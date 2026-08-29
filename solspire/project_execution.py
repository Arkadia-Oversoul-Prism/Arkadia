"""WEAVER-MVP1 — Governed project execution surface.

PROJECT ACCESS ≠ PASSSPEC ≠ PATCHAPPROVAL ≠ EXECUTION
Mutation route: project → weaver.execution.execute_patch (K15) → K3 only.
"""
from __future__ import annotations

import hashlib
from typing import Any

from weaver.execution import (
    PatchApproval,
    execute_patch,
    patch_content_hash,
    pass_spec_hash,
)
from weaver.pass_spec import PassSpec, current_head, current_origin_main


def evaluate_execution_state(
    *,
    patch: dict[str, Any] | None,
    pass_spec: dict[str, Any] | None = None,
    approval: dict[str, Any] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    auth = {
        "project_access": "OWNER_VERIFIED_BY_CALLER",
        "PassSpec": "NONE",
        "PatchApproval": "NONE",
        "Execution": "LOCKED",
        "Mutation path": "K15 → K3 ONLY",
        "note": "Project ownership is not authorization.",
    }
    if not patch:
        return {
            "state": "NO_PROPOSAL",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["No proposed patch"],
            "authorization": auth,
        }
    ph = patch_content_hash(patch)
    if patch.get("status") in (
        "STALE", "OUT_OF_SCOPE", "INVALID", "PATCH_BASE_MISMATCH", "PLAN_BINDING_MISMATCH",
    ):
        return {
            "state": "BLOCKED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": [f"Patch status not executable: {patch.get('status')}"],
            "authorization": auth,
            "patch_hash": ph,
            "patch_id": patch.get("patch_id"),
        }
    if not pass_spec:
        return {
            "state": "PASSSPEC_REQUIRED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["PassSpec missing"],
            "authorization": auth,
            "patch_hash": ph,
            "patch_id": patch.get("patch_id"),
        }
    try:
        spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
        spec.validate_structure()
    except Exception as e:
        return {
            "state": "PASSSPEC_REQUIRED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": [f"PassSpec invalid: {e}"],
            "authorization": auth,
            "patch_hash": ph,
        }
    auth = {**auth, "PassSpec": "BOUND"}
    psh = pass_spec_hash(spec)
    if not approval:
        return {
            "state": "PATCH_APPROVAL_REQUIRED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["PatchApproval missing"],
            "authorization": {**auth, "PatchApproval": "NONE"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
            "patch_id": patch.get("patch_id"),
        }
    if str(approval.get("patch_hash") or "") != ph:
        return {
            "state": "BLOCKED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["Patch hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
        }
    if str(approval.get("pass_spec_hash") or "") != psh:
        return {
            "state": "BLOCKED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["PassSpec hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
        }
    if not bool(approval.get("approved", False)):
        return {
            "state": "PATCH_APPROVAL_REQUIRED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["PatchApproval.approved is false"],
            "authorization": {**auth, "PatchApproval": "NONE"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
        }
    auth = {**auth, "PatchApproval": "BOUND", "Execution": "K15_READY"}
    try:
        head = current_head(repo_root)
        if patch.get("base_head_sha") and patch.get("base_head_sha") != head:
            return {
                "state": "BLOCKED",
                "execution": "LOCKED",
                "k15_ready": False,
                "lock_reasons": [f"HEAD drift: patch base {patch.get('base_head_sha')} != {head}"],
                "authorization": auth,
                "patch_hash": ph,
                "pass_spec_hash": psh,
            }
    except Exception:
        pass
    return {
        "state": "K15_READY",
        "execution": "K15_READY",
        "k15_ready": True,
        "lock_reasons": [],
        "authorization": auth,
        "patch_hash": ph,
        "pass_spec_hash": psh,
        "patch_id": patch.get("patch_id"),
        "plan_id": patch.get("plan_id"),
        "plan_hash": patch.get("plan_content_hash"),
    }


def build_pass_spec_for_patch(
    project: dict[str, Any],
    patch: dict[str, Any],
    *,
    pass_id: str | None = None,
    objective: str | None = None,
    allowed_paths: list[str] | None = None,
    required_tests: list[str] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    head = current_head(repo_root)
    paths = sorted(
        {
            (f.get("path") or "").replace("\\", "/").lstrip("./")
            for f in (patch.get("files") or [])
            if f.get("path")
        }
    )
    if allowed_paths is not None:
        paths = [p.replace("\\", "/").lstrip("./") for p in allowed_paths]
    spec = PassSpec(
        pass_id=pass_id
        or f"mvp1-{hashlib.sha256((patch.get('patch_id') or 'x').encode()).hexdigest()[:10]}",
        objective=objective
        or str((patch.get("review") or {}).get("objective") or project.get("name") or "MVP governed execution"),
        base_sha=str(patch.get("base_head_sha") or head),
        allowed_paths=paths,
        forbidden_paths=[],
        required_tests=list(required_tests or []),
        required_builds=[],
        non_goals=["autonomous execution", "second mutation path", "UI-as-authority"],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
        human_approval_required=True,
        checkpoint_required=True,
        pass_type="engineering",
    )
    spec.validate_structure()
    d = spec.to_dict()
    d["pass_spec_hash"] = pass_spec_hash(spec)
    d["bound_patch_id"] = patch.get("patch_id")
    d["bound_patch_hash"] = patch_content_hash(patch)
    d["project_id"] = project.get("id")
    d["authorization_note"] = "PassSpec bound. PatchApproval still required. Execution LOCKED."
    d["origin_sha"] = current_origin_main(repo_root)
    return d


def build_patch_approval(
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    *,
    approved: bool = True,
) -> dict[str, Any]:
    spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
    psh = pass_spec_hash(spec)
    ph = patch_content_hash(patch)
    approval = PatchApproval(
        patch_id=str(patch.get("patch_id") or ""),
        patch_hash=ph,
        plan_id=str(patch.get("plan_id") or ""),
        plan_hash=str(patch.get("plan_content_hash") or ""),
        base_head_sha=str(patch.get("base_head_sha") or ""),
        base_origin_sha=patch.get("base_origin_sha"),
        pass_spec_hash=psh,
        approved=bool(approved),
    )
    d = approval.to_dict()
    d["project_note"] = "Explicit human bind. Not ownership. Not knowledge. Not UI alone."
    return d


def execute_project_patch(
    project: dict[str, Any],
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    approval: dict[str, Any],
    *,
    repo_root: str = ".",
    run_k3: bool = False,
) -> dict[str, Any]:
    readiness = evaluate_execution_state(
        patch=patch, pass_spec=pass_spec, approval=approval, repo_root=repo_root
    )
    if not readiness.get("k15_ready"):
        return {
            "state": readiness.get("state"),
            "execution": {
                "status": "NOT_RUN",
                "final_status": "BLOCKED",
                "message": "; ".join(readiness.get("lock_reasons") or ["not ready"]),
            },
            "verification": {"status": "NOT_RUN"},
            "authorization": readiness.get("authorization"),
            "k15_ready": False,
            "project_id": project.get("id"),
            "mutation_path": "NONE — K15 not invoked",
        }
    spec = PassSpec.from_dict(pass_spec) if not isinstance(pass_spec, PassSpec) else pass_spec
    result = execute_patch(patch, spec, approval, repo_root=repo_root, run_k3=run_k3)
    rd = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    final = rd.get("final_status") or "BLOCKED"
    ver = rd.get("verification") or {}
    return {
        "state": "K15_READY" if (not run_k3 and final == "BLOCKED") else (
            "BLOCKED" if final == "BLOCKED" else "VERIFICATION_PENDING"
        ),
        "execution": {
            "status": "NOT_RUN" if not run_k3 else ("SUCCESS" if final != "BLOCKED" else "FAILED"),
            "final_status": final,
            "message": rd.get("message"),
            "k15": "PRECHECKED" if (not run_k3 and "preflight" in str(rd.get("message") or "").lower()) else (
                "REJECTED" if final == "BLOCKED" else "ACCEPTED"
            ),
            "k3": "NOT_INVOKED" if not run_k3 else ((rd.get("mutation") or {}).get("result") or "UNKNOWN"),
            "mutation": rd.get("mutation"),
            "preflight": rd.get("preflight"),
        },
        "verification": {
            "status": ver.get("status") or "NOT_RUN",
            "note": "EXECUTED ≠ VERIFIED until verification evidence exists",
        },
        "authorization": {
            "PassSpec": "BOUND",
            "PatchApproval": "BOUND",
            "Execution": final,
            "project_access": "OWNER_VERIFIED_BY_CALLER",
            "Mutation path": "K15 → K3 ONLY",
        },
        "k15_ready": True,
        "project_id": project.get("id"),
        "patch_id": patch.get("patch_id"),
        "patch_hash": patch_content_hash(patch),
        "execution_id": rd.get("execution_id"),
    }
