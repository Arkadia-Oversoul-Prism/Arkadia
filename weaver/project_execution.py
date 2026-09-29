"""Canonical Weaver project-execution semantics.

This module owns engineering PassSpec / PatchApproval binding and readiness
semantics used by project-facing adapters. SolSpire may add project context,
but does not redefine Weaver governance rules.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .execution import PatchApproval, patch_content_hash, pass_spec_hash
from .pass_spec import PassSpec, current_head, current_origin_main, path_in_allowlist


_NON_EXECUTABLE_STATUSES = {
    "STALE",
    "OUT_OF_SCOPE",
    "INVALID",
    "PATCH_BASE_MISMATCH",
    "PLAN_BINDING_MISMATCH",
}


def evaluate_execution_state(
    *,
    patch: dict[str, Any] | None,
    pass_spec: dict[str, Any] | PassSpec | None = None,
    approval: dict[str, Any] | PatchApproval | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Evaluate governed execution readiness without mutating the repository."""
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
    if patch.get("status") in _NON_EXECUTABLE_STATUSES:
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

    if isinstance(approval, PatchApproval):
        approval_dict = approval.to_dict()
    else:
        approval_dict = approval

    if str(approval_dict.get("patch_hash") or "") != ph:
        return {
            "state": "BLOCKED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["Patch hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
        }
    if str(approval_dict.get("pass_spec_hash") or "") != psh:
        return {
            "state": "BLOCKED",
            "execution": "LOCKED",
            "k15_ready": False,
            "lock_reasons": ["PassSpec hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph,
            "pass_spec_hash": psh,
        }
    if not bool(approval_dict.get("approved", False)):
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
    for path in sorted({f.get("path", "") for f in (patch.get("files") or []) if f.get("path")}):
        if not path_in_allowlist(path, list(spec.allowed_paths or [])):
            return {
                "state": "BLOCKED",
                "execution": "LOCKED",
                "k15_ready": False,
                "lock_reasons": [f"OUT_OF_SCOPE: {path}"],
                "authorization": auth,
                "patch_hash": ph,
                "pass_spec_hash": psh,
            }
        for forbidden in (spec.forbidden_paths or []):
            ff = str(forbidden).replace("\\", "/").lstrip("./")
            norm = path.replace("\\", "/").lstrip("./")
            if ff and (norm == ff or norm.startswith(ff.rstrip("/") + "/")):
                return {
                    "state": "BLOCKED",
                    "execution": "LOCKED",
                    "k15_ready": False,
                    "lock_reasons": [f"forbidden path: {path}"],
                    "authorization": auth,
                    "patch_hash": ph,
                    "pass_spec_hash": psh,
                }

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
    patch: dict[str, Any],
    *,
    pass_id: str | None = None,
    objective: str | None = None,
    allowed_paths: list[str] | None = None,
    required_tests: list[str] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Build the canonical engineering PassSpec for a proposed patch."""
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
        objective=objective or str((patch.get("review") or {}).get("objective") or "MVP governed execution"),
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
    d["origin_sha"] = current_origin_main(repo_root)
    return d


def build_patch_approval(
    patch: dict[str, Any],
    pass_spec: dict[str, Any] | PassSpec,
    *,
    approved: bool = True,
) -> dict[str, Any]:
    """Build the canonical human approval binding for a proposed patch."""
    spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
    approval = PatchApproval(
        patch_id=str(patch.get("patch_id") or ""),
        patch_hash=patch_content_hash(patch),
        plan_id=str(patch.get("plan_id") or ""),
        plan_hash=str(patch.get("plan_content_hash") or ""),
        base_head_sha=str(patch.get("base_head_sha") or ""),
        base_origin_sha=patch.get("base_origin_sha"),
        pass_spec_hash=pass_spec_hash(spec),
        approved=bool(approved),
    )
    return approval.to_dict()
