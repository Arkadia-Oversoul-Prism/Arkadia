"""WEAVER governance primitives for project-scoped patch lifecycle.

This module owns PassSpec / PatchApproval binding and K15 readiness semantics.
SolSpire may adapt project context to these primitives, but must not reimplement
these rules.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .execution import PatchApproval, execute_patch, pass_spec_hash, patch_content_hash
from .pass_spec import PassSpec, current_head, current_origin_main, path_in_allowlist


def evaluate_patch_readiness(
    *,
    patch: dict[str, Any],
    pass_spec: dict[str, Any] | PassSpec | None = None,
    approval: dict[str, Any] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Return the canonical K15 readiness state without invoking K3."""
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
            "state": "NO_PROPOSAL", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["No proposed patch"], "authorization": auth,
        }

    ph = patch_content_hash(patch)
    if patch.get("status") in ("STALE", "OUT_OF_SCOPE", "INVALID", "PATCH_BASE_MISMATCH", "PLAN_BINDING_MISMATCH"):
        return {
            "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": [f"Patch status not executable: {patch.get('status')}"],
            "authorization": auth, "patch_hash": ph, "patch_id": patch.get("patch_id"),
        }

    if not pass_spec:
        return {
            "state": "PASSSPEC_REQUIRED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["PassSpec missing"], "authorization": auth,
            "patch_hash": ph, "patch_id": patch.get("patch_id"),
        }

    try:
        spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
        spec.validate_structure()
    except Exception as exc:
        return {
            "state": "PASSSPEC_REQUIRED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": [f"PassSpec invalid: {exc}"], "authorization": auth,
            "patch_hash": ph,
        }

    auth = {**auth, "PassSpec": "BOUND"}
    psh = pass_spec_hash(spec)
    if not approval:
        return {
            "state": "PATCH_APPROVAL_REQUIRED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["PatchApproval missing"],
            "authorization": {**auth, "PatchApproval": "NONE"},
            "patch_hash": ph, "pass_spec_hash": psh, "patch_id": patch.get("patch_id"),
        }

    if str(approval.get("patch_hash") or "") != ph:
        return {
            "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["Patch hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph, "pass_spec_hash": psh,
        }
    if str(approval.get("pass_spec_hash") or "") != psh:
        return {
            "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["PassSpec hash no longer matches approval"],
            "authorization": {**auth, "PatchApproval": "INVALIDATED"},
            "patch_hash": ph, "pass_spec_hash": psh,
        }
    if not bool(approval.get("approved", False)):
        return {
            "state": "PATCH_APPROVAL_REQUIRED", "execution": "LOCKED", "k15_ready": False,
            "lock_reasons": ["PatchApproval.approved is false"],
            "authorization": {**auth, "PatchApproval": "NONE"},
            "patch_hash": ph, "pass_spec_hash": psh,
        }

    auth = {**auth, "PatchApproval": "BOUND", "Execution": "K15_READY"}
    paths = sorted({f.get("path", "") for f in (patch.get("files") or []) if f.get("path")})
    for path in paths:
        if not path_in_allowlist(path, list(spec.allowed_paths or [])):
            return {
                "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
                "lock_reasons": [f"OUT_OF_SCOPE: {path}"], "authorization": auth,
                "patch_hash": ph, "pass_spec_hash": psh,
            }
        for forbidden in (spec.forbidden_paths or []):
            ff = str(forbidden).replace("\\", "/").lstrip("./")
            norm = path.replace("\\", "/").lstrip("./")
            if ff and (norm == ff or norm.startswith(ff.rstrip("/") + "/")):
                return {
                    "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
                    "lock_reasons": [f"forbidden path: {path}"], "authorization": auth,
                    "patch_hash": ph, "pass_spec_hash": psh,
                }

    try:
        head = current_head(repo_root)
        if patch.get("base_head_sha") and patch.get("base_head_sha") != head:
            return {
                "state": "BLOCKED", "execution": "LOCKED", "k15_ready": False,
                "lock_reasons": [f"HEAD drift: patch base {patch.get('base_head_sha')} != {head}"],
                "authorization": auth, "patch_hash": ph, "pass_spec_hash": psh,
            }
    except Exception:
        pass

    return {
        "state": "K15_READY", "execution": "K15_READY", "k15_ready": True,
        "lock_reasons": [], "authorization": auth, "patch_hash": ph,
        "pass_spec_hash": psh, "patch_id": patch.get("patch_id"),
        "plan_id": patch.get("plan_id"), "plan_hash": patch.get("plan_content_hash"),
    }


def build_pass_spec_for_patch(
    patch: dict[str, Any],
    *,
    pass_id: str,
    objective: str,
    allowed_paths: list[str] | None = None,
    required_tests: list[str] | None = None,
    repo_root: str = ".",
    non_goals: list[str] | None = None,
) -> PassSpec:
    """Construct the canonical PassSpec. Project metadata stays outside the spec."""
    head = current_head(repo_root)
    paths = sorted({
        (f.get("path") or "").replace("\\", "/").lstrip("./")
        for f in (patch.get("files") or []) if f.get("path")
    })
    if allowed_paths is not None:
        paths = [p.replace("\\", "/").lstrip("./") for p in allowed_paths]
    spec = PassSpec(
        pass_id=pass_id,
        objective=objective,
        base_sha=str(patch.get("base_head_sha") or head),
        allowed_paths=paths,
        forbidden_paths=[],
        required_tests=list(required_tests or []),
        required_builds=[],
        non_goals=list(non_goals or ["autonomous execution", "second mutation path", "UI-as-authority"]),
        commit_required=False,
        push_allowed=False,
        publication_required=False,
        human_approval_required=True,
        checkpoint_required=True,
        pass_type="engineering",
    )
    spec.validate_structure()
    return spec


def build_patch_approval(
    patch: dict[str, Any],
    pass_spec: PassSpec | dict[str, Any],
    *,
    approved: bool = True,
) -> PatchApproval:
    """Bind explicit human approval to the canonical patch and PassSpec hashes."""
    spec = pass_spec if isinstance(pass_spec, PassSpec) else PassSpec.from_dict(pass_spec)
    return PatchApproval(
        patch_id=str(patch.get("patch_id") or ""),
        patch_hash=patch_content_hash(patch),
        plan_id=str(patch.get("plan_id") or ""),
        plan_hash=str(patch.get("plan_content_hash") or ""),
        base_head_sha=str(patch.get("base_head_sha") or ""),
        base_origin_sha=patch.get("base_origin_sha"),
        pass_spec_hash=pass_spec_hash(spec),
        approved=bool(approved),
    )


__all__ = [
    "PatchApproval",
    "build_patch_approval",
    "build_pass_spec_for_patch",
    "evaluate_patch_readiness",
    "execute_patch",
    "pass_spec_hash",
    "patch_content_hash",
]
