"""SolSpire project adapter for Weaver governed execution.

PROJECT ACCESS ≠ PASSSPEC ≠ PATCHAPPROVAL ≠ EXECUTION

This module intentionally contains no Weaver governance rules. It adapts
project/workspace context to the canonical Weaver governance primitives and
preserves the historical SolSpire API for callers.
"""
from __future__ import annotations

import hashlib
from typing import Any

from weaver.execution import execute_patch, pass_spec_hash, patch_content_hash
from weaver.governance import (
    build_patch_approval as _weaver_build_patch_approval,
    build_pass_spec_for_patch as _weaver_build_pass_spec_for_patch,
    evaluate_patch_readiness as _weaver_evaluate_patch_readiness,
)
from weaver.pass_spec import PassSpec, current_head, current_origin_main


def evaluate_execution_state(
    *,
    patch: dict[str, Any] | None,
    pass_spec: dict[str, Any] | None = None,
    approval: dict[str, Any] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Compatibility adapter; readiness semantics belong to Weaver."""
    return _weaver_evaluate_patch_readiness(
        patch=patch or {}, pass_spec=pass_spec, approval=approval, repo_root=repo_root
    )


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
    """Compatibility adapter; PassSpec construction semantics belong to Weaver."""
    resolved_pass_id = pass_id or f"mvp1-{hashlib.sha256((patch.get('patch_id') or 'x').encode()).hexdigest()[:10]}"
    resolved_objective = objective or str(
        (patch.get("review") or {}).get("objective")
        or project.get("name")
        or "MVP governed execution"
    )
    spec = _weaver_build_pass_spec_for_patch(
        patch,
        pass_id=resolved_pass_id,
        objective=resolved_objective,
        allowed_paths=allowed_paths,
        required_tests=required_tests,
        repo_root=repo_root,
    )
    data = spec.to_dict()
    data["pass_spec_hash"] = pass_spec_hash(spec)
    data["bound_patch_id"] = patch.get("patch_id")
    data["bound_patch_hash"] = patch_content_hash(patch)
    data["project_id"] = project.get("id")
    data["authorization_note"] = "PassSpec bound. PatchApproval still required. Execution LOCKED."
    data["origin_sha"] = current_origin_main(repo_root)
    return data


def build_patch_approval(
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    *,
    approved: bool = True,
) -> dict[str, Any]:
    """Compatibility adapter; PatchApproval binding semantics belong to Weaver."""
    approval = _weaver_build_patch_approval(patch, pass_spec, approved=approved)
    data = approval.to_dict()
    data["project_note"] = "Explicit human bind. Not ownership. Not knowledge. Not UI alone."
    return data


def execute_project_patch(
    project: dict[str, Any],
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    approval: dict[str, Any],
    *,
    repo_root: str = ".",
    run_k3: bool = False,
) -> dict[str, Any]:
    """Project adapter around the canonical Weaver K15 → K3 execution seam."""
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

    spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
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
