"""WEAVER-W5 — Project Knowledge OS (composition over existing store).

Derived views only. Not a second memory/graph/vector authority.
"""
from __future__ import annotations

from typing import Any


def _safe_list(fn, *args, default=None, errors=None, source=None):
    try:
        return fn(*args)
    except Exception as exc:
        if errors is not None and source:
            errors[source] = f"{type(exc).__name__}: {exc}"
        return default if default is not None else []


def build_knowledge_summary(project_id: str, embedding_provider=None) -> dict[str, Any]:
    from solspire.project_store import (
        list_memory,
        list_files,
        list_repositories,
        list_tasks,
        list_events,
        list_conversations,
    )
    from solspire.embedding_provider import get_embedding_provider

    source_errors: dict[str, str] = {}
    mem = _safe_list(list_memory, project_id, errors=source_errors, source="memory")
    files = _safe_list(list_files, project_id, errors=source_errors, source="files")
    repos = _safe_list(list_repositories, project_id, errors=source_errors, source="repositories")
    tasks = _safe_list(list_tasks, project_id, errors=source_errors, source="tasks")
    events = _safe_list(list_events, project_id, errors=source_errors, source="events")
    convs = _safe_list(list_conversations, project_id, errors=source_errors, source="conversations")
    provider = embedding_provider or get_embedding_provider()

    return {
        "project_id": project_id,
        "source_health": {
            "state": "PARTIAL" if source_errors else "AVAILABLE",
            "errors": source_errors,
            "empty_means": "zero returned rows only when state is AVAILABLE",
        },
        "sources": {
            "memory": len(mem),
            "files": len(files),
            "repositories": len(repos),
            "tasks": len(tasks),
            "events": len(events),
            "conversations": len(convs),
        },
        "items": {
            "repositories": [
                {
                    "id": r.get("id"),
                    "owner": r.get("owner"),
                    "repo": r.get("repo"),
                    "branch": r.get("branch"),
                    "label": r.get("label"),
                    "provenance": "SOURCE-BACKED",
                }
                for r in (repos or [])[:50]
            ],
            "files": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "mime_type": f.get("mime_type"),
                    "provenance": "SOURCE-BACKED",
                }
                for f in (files or [])[:50]
            ],
            "memory": [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "tags": m.get("tags"),
                    "provenance": "SOURCE-BACKED",
                    "epistemic": "OPERATOR_CONTEXT",
                    "note": "Memory is contextual. Not FACT. Not authorization.",
                }
                for m in (mem or [])[:50]
            ],
            "tasks": [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "status": t.get("status"),
                    "provenance": "SOURCE-BACKED",
                }
                for t in (tasks or [])[:50]
            ],
        },
        "embeddings": provider.describe(project_id=project_id),
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "note": "Knowledge summary is read-only. Not authorization.",
        },
    }


def build_derived_graph(project_id: str) -> dict[str, Any]:
    """Compatibility wrapper for the bounded semantic graph projection."""
    from solspire.semantic_graph import build_bounded_semantic_graph
    return build_bounded_semantic_graph(project_id)


def build_project_context_for_weaver(project: dict[str, Any]) -> dict[str, Any]:
    """Read-only context envelope. Never authorization."""
    pid = project.get("id")
    try:
        summary = build_knowledge_summary(pid) if pid else {}
    except Exception as exc:
        summary = {
            "project_id": pid, "sources": {}, "items": {},
            "embeddings": {"state": "UNAVAILABLE"},
            "source_health": {
                "state": "UNAVAILABLE",
                "errors": {"summary": f"{type(exc).__name__}: {exc}"},
            },
        }
    owner_uid = project.get("owner_uid") or project.get("owner")
    continuity: dict[str, Any] = {"workspace": None, "daily_pulse": None, "work_events": None,
                                  "binding_state": {"daily_pulse": "UNKNOWN", "workevents": "UNKNOWN"}}
    graph = {}
    project_event_context: list[dict[str, Any]] | None = None
    project_event_state = "UNKNOWN"
    larder_orders: list[dict[str, Any]] = []
    if pid:
        try:
            import json
            from solspire.project_store import list_events
            source_events = list_events(pid, limit=100)
            project_event_state = "AVAILABLE"
            project_event_context = []
            for event in source_events:
                project_event_context.append({
                    "id": event.get("id"), "event_type": event.get("event_type"),
                    "summary": event.get("summary"), "created_at": event.get("created_at"),
                    "provenance": "SOURCE-BACKED",
                })
                if event.get("event_type") == "living_larder_order_bound":
                    raw = event.get("data") or {}
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(data, dict) and data.get("order_id"):
                        larder_orders.append({
                            "order_id": data.get("order_id"), "status": data.get("status", "UNKNOWN"),
                            "created_at": data.get("created_at"), "subtotal": data.get("subtotal"),
                            "delivery_fee": data.get("delivery_fee"), "total": data.get("total"),
                            "item_count": data.get("item_count"), "currency": "NGN",
                            "snapshot_digest": data.get("snapshot_digest"),
                            "provenance": "SOURCE-BACKED",
                        })
        except Exception as exc:
            project_event_state = "UNAVAILABLE"
            project_event_context = None
            larder_orders = []
        try:
            from datetime import datetime, timezone
            from solspire.workspace_manager import get_workspace_manager
            from solspire.pulse_manager import get_pulse_manager
            from solspire.workevent_manager import get_workevent_manager
            workspace = get_workspace_manager().get_for_subject(str(owner_uid or ""))
            continuity["workspace"] = workspace.to_dict() if workspace else None
            if workspace:
                pulse = get_pulse_manager().get_for_subject_date(
                    str(owner_uid), workspace.id, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                events = [e.to_dict() for e in get_workevent_manager().list(str(owner_uid), workspace.id, 100)
                          if e.scope_ref == pid or e.work_ref == pid]
                continuity["daily_pulse"] = pulse.to_dict() if pulse else None
                continuity["work_events"] = events[:50]
                continuity["work_events"] = events[:50]
                continuity["binding_state"] = {
                    "daily_pulse": "AVAILABLE" if pulse else "EMPTY",
                    "workevents": "AVAILABLE" if events else "EMPTY",
                }
        except Exception as exc:
            continuity["daily_pulse"] = None
            continuity["work_events"] = None
            continuity["binding_state"] = {"daily_pulse": "UNAVAILABLE",
                                           "workevents": "UNAVAILABLE",
                                           "detail": f"{type(exc).__name__}: {exc}"}
        try:
            graph = build_derived_graph(pid)
        except Exception as exc:
            graph = {"state": "UNAVAILABLE", "detail": f"{type(exc).__name__}: {exc}"}
    witnessed_larder_ids = {
        str(ref).removeprefix("living-larder-order:")
        for event in (continuity.get("work_events") or [])
        if event.get("event_type") == "LIVING_LARDER_ORDER_BOUND"
        for ref in event.get("artifact_refs", [])
        if str(ref).startswith("living-larder-order:")
    }
    unwitnessed_larder_ids = [str(order["order_id"]) for order in larder_orders
                              if str(order["order_id"]) not in witnessed_larder_ids]
    larder_orders = [order for order in larder_orders
                     if str(order["order_id"]) in witnessed_larder_ids]
    larder_state = (
        "UNAVAILABLE"
        if project_event_state == "UNAVAILABLE"
        or continuity.get("binding_state", {}).get("workevents") == "UNAVAILABLE"
        else "PROJECT_BOUND" if larder_orders else "UNKNOWN"
    )
    return {
        "project_id": pid,
        "project_name": project.get("name"),
        "owner": owner_uid,
        "status": project.get("status"),
        "knowledge": (summary.get("sources")
                      if (summary.get("source_health") or {}).get("state") == "AVAILABLE"
                      else None),
        "knowledge_source_health": summary.get("source_health", {"state": "UNKNOWN"}),
        "repositories": ((summary.get("items") or {}).get("repositories")
                         if (summary.get("source_health") or {}).get("state") == "AVAILABLE"
                         else None),
        "knowledge_graph": graph,
        "project_events": (project_event_context[:100]
                           if project_event_context is not None else None),
        "project_events_state": project_event_state,
        "living_larder": {
            "binding_state": larder_state,
            "orders": larder_orders[:100] if project_event_state != "UNAVAILABLE" else None,
            "unwitnessed_order_ids": unwitnessed_larder_ids,
            "note": "Only explicitly bound source records with matching WorkEvent evidence are shown; no transaction is inferred.",
        },
        "continuity": continuity,
        "memory_note": "Memory listed in knowledge OS is OPERATOR_CONTEXT, not FACT.",
        "embeddings": summary.get("embeddings"),
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "Mutation path": "K3 ONLY",
            "note": "ProjectContext is context only. Not PassSpec. Not PatchApproval.",
        },
    }
