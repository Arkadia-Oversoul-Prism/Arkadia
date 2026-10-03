"""Live, owner-scoped capability probes. Configuration is not proof of operation."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any


def _probe(name: str, fn) -> dict[str, Any]:
    try:
        detail = fn()
        state = detail.get("binding_state") if isinstance(detail, dict) else None
        return {"capability": name, "state": state if state == "UNBOUND" else "AVAILABLE", "detail": detail}
    except Exception as exc:
        return {"capability": name, "state": "UNAVAILABLE",
                "detail": f"{type(exc).__name__}: {exc}"}


def project_integration_health(*, subject_uid: str, project: dict[str, Any]) -> dict[str, Any]:
    """Exercise real local capability paths and report unknown/unbound seams honestly."""
    project_id = str(project.get("id") or "")
    results: dict[str, dict[str, Any]] = {}

    def probe_weaver():
        from lab.engineering_lab.runtime import get_runtime
        overview = get_runtime().overview(subject_uid)
        from solspire.project_knowledge import build_project_context_for_weaver
        context = build_project_context_for_weaver(project)
        if not isinstance(overview, dict) or context.get("project_id") != project_id:
            raise RuntimeError("Weaver runtime/context binding did not resolve this project")
        return {"runtime_overview": "resolved", "project_context": "resolved",
                "authorization": context.get("authorization")}

    def probe_arkana():
        from solspire.project_knowledge import build_project_context_for_weaver
        context = build_project_context_for_weaver(project)
        if context.get("project_id") != project_id or context.get("owner") != subject_uid:
            raise RuntimeError("Arkana context is not bound to the authenticated owner/project")
        return {"project_id": project_id, "owner_scope": "verified",
                "conversation_interface": "project_context_resolved"}

    def probe_knowledge():
        from solspire.project_knowledge import build_knowledge_summary, build_derived_graph
        summary = build_knowledge_summary(project_id)
        graph = build_derived_graph(project_id)
        if summary.get("project_id") != project_id or graph.get("project_id") != project_id:
            raise RuntimeError("Knowledge OS returned a mismatched project")
        if (summary.get("source_health") or {}).get("state") == "PARTIAL":
            raise RuntimeError(f"Knowledge OS sources unavailable: {(summary.get('source_health') or {}).get('errors')}")
        return {"sources": summary.get("sources", {}),
                "source_health": summary.get("source_health", {"state": "UNKNOWN"}),
                "graph_counts": graph.get("counts", {}),
                "graph_kind": graph.get("kind")}

    def probe_larder():
        from solspire.project_store import list_events
        from solspire.workspace_manager import get_workspace_manager
        from solspire.workevent_manager import get_workevent_manager
        import json
        events = list_events(project_id, limit=500)
        workspace = get_workspace_manager().get_for_subject(subject_uid)
        if workspace is None:
            return {"binding_state": "UNBOUND", "bound_order_count": 0,
                    "detail": "Canonical workspace is missing; WorkEvent evidence cannot be verified."}
        work_events = get_workevent_manager().list(subject_uid, workspace.id, 500)
        witnessed = {
            str(ref).removeprefix("living-larder-order:")
            for work_event in work_events
            if work_event.event_type == "LIVING_LARDER_ORDER_BOUND"
            and (work_event.scope_ref == project_id or work_event.work_ref == project_id)
            for ref in work_event.artifact_refs
            if str(ref).startswith("living-larder-order:")
        }
        bindings = []
        missing_witnesses = []
        for event in events:
            if str(event.get("event_type") or "") != "living_larder_order_bound":
                continue
            raw = event.get("data") or {}
            data = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(data, dict) or not data.get("order_id"):
                continue
            order_id = str(data["order_id"])
            if order_id not in witnessed:
                missing_witnesses.append(order_id)
                continue
            bindings.append({"order_id": order_id, "status": data.get("status"),
                             "total": data.get("total"), "currency": "NGN",
                             "source": data.get("source", "living_larder_orders"),
                             "workevent_evidence": "VERIFIED"})
        if not bindings:
            return {"binding_state": "UNBOUND", "bound_order_count": 0,
                    "missing_workevent_evidence": missing_witnesses,
                    "detail": "No Living Larder order has both a project binding and matching WorkEvent evidence."}
        return {"binding_state": "PROJECT_BOUND", "bound_order_count": len(bindings),
                "orders": bindings[:100], "missing_workevent_evidence": missing_witnesses}

    results["weaver"] = _probe("weaver", probe_weaver)
    results["arkana"] = _probe("arkana", probe_arkana)
    results["knowledge_os"] = _probe("knowledge_os", probe_knowledge)
    results["living_larder"] = _probe("living_larder", probe_larder)
    image = os.environ.get("SOLSPIRE_AGENT_IMAGE", "")
    runtime_name = os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker")
    runtime = shutil.which(runtime_name)
    image_digest = image.rsplit("@sha256:", 1)[-1] if "@sha256:" in image else ""
    image_pinned = len(image_digest) == 64 and all(ch in "0123456789abcdef" for ch in image_digest.lower())
    runtime_live = False
    image_present = False
    runtime_error = None
    if runtime and image_pinned:
        try:
            info = subprocess.run([runtime, "info"], shell=False, capture_output=True,
                                  text=True, timeout=5, check=False)
            runtime_live = info.returncode == 0
            if not runtime_live:
                runtime_error = (info.stderr or info.stdout or "runtime info failed")[:500]
            else:
                inspected = subprocess.run([runtime, "image", "inspect", image],
                                           shell=False, capture_output=True, text=True,
                                           timeout=5, check=False)
                image_present = inspected.returncode == 0
                if not image_present:
                    runtime_error = (inspected.stderr or inspected.stdout or "configured image not present")[:500]
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
    ready = bool(runtime and image_pinned and runtime_live and image_present)
    results["isolated_execution"] = {
        "capability": "isolated_execution",
        "state": "AVAILABLE" if ready else "UNAVAILABLE",
        "detail": {"runtime_found": bool(runtime), "runtime_live": runtime_live,
                   "image_digest_pinned": image_pinned, "image_present": image_present,
                   "runtime_name": runtime_name,
                   "reason": None if ready else runtime_error or
                   "container runtime, live daemon, immutable image digest, or local image is missing"},
    }
    larder_detail = results["living_larder"].get("detail")
    larder_bound = isinstance(larder_detail, dict) and larder_detail.get("binding_state") == "PROJECT_BOUND"
    return {
        "contract": "solspire.integration-health.v1",
        "project_id": project_id,
        "owner_uid": subject_uid,
        "capabilities": results,
        "all_required_available": all(results[k]["state"] == "AVAILABLE"
                                      for k in ("weaver", "arkana", "knowledge_os", "isolated_execution"))
                                      and larder_bound,
        "semantics": {
            "AVAILABLE": "the probe exercised the capability path successfully",
            "UNAVAILABLE": "the probe failed or required runtime/configuration is missing",
            "UNBOUND": "no explicit project binding exists; no relationship is inferred",
            "authorization": "capability health never grants execution or patch approval",
        },
    }


__all__ = ["project_integration_health"]
