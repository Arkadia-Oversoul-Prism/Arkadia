"""WEAVER-K15 — Governed patch execution via K3 (orchestration only).

PATCH ≠ AUTHORIZATION. K3 remains the sole mutation path.
No second write/commit/push engine.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any

from .pass_spec import PassSpec, PassSpecError, current_head, current_origin_main, path_in_allowlist
from .patch import ProposedPatch
from .plan import Plan, PlanError, approve_plan, validate_plan_against_spec
from .transaction import TransactionResult, run_transaction
from .verification import verify_implementation, plan_content_hash


@dataclass
class PatchApproval:
    """Human approval bound to exact patch + plan + base SHAs + PassSpec."""

    patch_id: str
    patch_hash: str
    plan_id: str
    plan_hash: str
    base_head_sha: str
    base_origin_sha: str | None
    pass_spec_hash: str
    approved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    execution_id: str
    patch_id: str
    patch_hash: str
    plan_id: str
    plan_hash: str
    pass_spec_hash: str
    base_head_sha: str
    base_origin_sha: str | None
    preflight: dict[str, Any] = field(default_factory=dict)
    mutation: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    publication: dict[str, Any] = field(default_factory=dict)
    final_status: str = "BLOCKED"
    authorization: dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def patch_content_hash(patch: ProposedPatch | dict[str, Any]) -> str:
    if isinstance(patch, ProposedPatch):
        data = {
            "patch_id": patch.patch_id,
            "plan_id": patch.plan_id,
            "plan_content_hash": patch.plan_content_hash,
            "files": [
                {"path": f.get("path"), "operation": f.get("operation"), "patch_text": f.get("patch_text")}
                for f in (patch.files or [])
            ],
        }
    else:
        data = {
            "patch_id": patch.get("patch_id"),
            "plan_id": patch.get("plan_id"),
            "plan_content_hash": patch.get("plan_content_hash"),
            "files": [
                {"path": f.get("path"), "operation": f.get("operation"), "patch_text": f.get("patch_text")}
                for f in (patch.get("files") or [])
            ],
        }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def pass_spec_hash(spec: PassSpec) -> str:
    blob = json.dumps(
        {
            "pass_id": spec.pass_id,
            "objective": spec.objective,
            "base_sha": spec.base_sha,
            "allowed_paths": list(spec.allowed_paths),
            "forbidden_paths": list(spec.forbidden_paths),
            "required_tests": list(spec.required_tests),
            "publication_required": bool(getattr(spec, "publication_required", True)),
        },
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _eid(*parts: str) -> str:
    return "ex-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _working_tree_clean(repo_root: str) -> bool:
    r = subprocess.run(["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True)
    return r.returncode == 0 and not (r.stdout or "").strip()


def _blocked(
    *,
    patch: ProposedPatch | dict[str, Any],
    spec: PassSpec | None,
    message: str,
    preflight: dict[str, Any],
    status: str = "BLOCKED",
) -> ExecutionResult:
    if isinstance(patch, ProposedPatch):
        pid, ph, plid, plh = patch.patch_id, patch_content_hash(patch), patch.plan_id, patch.plan_content_hash
        bh, bo = patch.base_head_sha, patch.base_origin_sha
    else:
        pid = str(patch.get("patch_id") or "")
        ph = patch_content_hash(patch)
        plid = str(patch.get("plan_id") or "")
        plh = str(patch.get("plan_content_hash") or "")
        bh = str(patch.get("base_head_sha") or "")
        bo = patch.get("base_origin_sha")
    psh = pass_spec_hash(spec) if spec else ""
    return ExecutionResult(
        execution_id=_eid(pid, status, message[:40]),
        patch_id=pid,
        patch_hash=ph,
        plan_id=plid,
        plan_hash=plh,
        pass_spec_hash=psh,
        base_head_sha=bh,
        base_origin_sha=bo if isinstance(bo, str) or bo is None else str(bo),
        preflight=preflight,
        mutation={"attempted": False, "changed_files": [], "result": status},
        verification={"status": "NOT_RUN"},
        publication={"required": bool(spec and getattr(spec, "publication_required", True)), "status": "NOT_ATTEMPTED"},
        final_status=status,
        authorization={
            "current_pass_authorized": False,
            "note": "Execution blocked or finished; future sessions still require a new PassSpec.",
        },
        message=message,
    )


def patch_to_k3_plan(patch: ProposedPatch, spec: PassSpec) -> Plan:
    paths = sorted({f.get("path", "") for f in (patch.files or []) if f.get("path")})
    steps = [
        f"{f.get('operation')}: {f.get('path')} — {f.get('plan_step') or ''}"
        for f in sorted(patch.files or [], key=lambda x: x.get("path") or "")
    ]
    plan = Plan(
        pass_id=spec.pass_id,
        objective=spec.objective,
        rationale=f"K15 execution of patch {patch.patch_id}",
        proposed_files=paths,
        implementation_steps=steps or ["apply approved patch via K3"],
        required_tests=list(spec.required_tests or (patch.tests or {}).get("required") or []),
        required_builds=list(spec.required_builds),
        architectural_impact=["Weaver control-plane"],
        risks=["K15 orchestrates only; K3 performs mutation"],
        expected_outcome="Governed mutation under PassSpec",
        approved=False,
    )
    validate_plan_against_spec(plan, spec)
    return plan


def execute_patch(
    patch: ProposedPatch | dict[str, Any],
    pass_spec: PassSpec | None,
    approval: PatchApproval | dict[str, Any] | None,
    *,
    repo_root: str = ".",
    run_k3: bool = True,
) -> ExecutionResult:
    """
    Orchestrate approved patch through K3. Does not write/commit itself.
    """
    preflight: dict[str, Any] = {
        "repository": True,
        "authorization": False,
        "scope": False,
        "binding": False,
        "clean_tree": False,
    }

    if pass_spec is None:
        return _blocked(patch=patch, spec=None, message="PassSpec required", preflight=preflight)

    if approval is None:
        return _blocked(patch=patch, spec=pass_spec, message="explicit patch approval required", preflight=preflight)

    if isinstance(patch, dict):
        # normalize minimal
        from .patch import ProposedPatch as PP

        patch = PP(
            patch_id=str(patch.get("patch_id") or ""),
            base_head_sha=str(patch.get("base_head_sha") or ""),
            base_origin_sha=patch.get("base_origin_sha"),
            plan_id=str(patch.get("plan_id") or ""),
            plan_content_hash=str(patch.get("plan_content_hash") or ""),
            changeset_id=str(patch.get("changeset_id") or ""),
            status=str(patch.get("status") or "PROPOSED"),
            files=list(patch.get("files") or []),
            tests=dict(patch.get("tests") or {}),
            impact=dict(patch.get("impact") or {}),
            validation=dict(patch.get("validation") or {}),
            review=dict(patch.get("review") or {}),
            authorization=dict(patch.get("authorization") or {}),
            execution=dict(patch.get("execution") or {}),
        )

    if isinstance(approval, dict):
        approval = PatchApproval(
            patch_id=str(approval.get("patch_id") or ""),
            patch_hash=str(approval.get("patch_hash") or ""),
            plan_id=str(approval.get("plan_id") or ""),
            plan_hash=str(approval.get("plan_hash") or ""),
            base_head_sha=str(approval.get("base_head_sha") or ""),
            base_origin_sha=approval.get("base_origin_sha"),
            pass_spec_hash=str(approval.get("pass_spec_hash") or ""),
            approved=bool(approval.get("approved", True)),
        )

    if not approval.approved:
        return _blocked(patch=patch, spec=pass_spec, message="approval.approved is false", preflight=preflight)

    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    clean = _working_tree_clean(repo_root)
    preflight["clean_tree"] = clean

    # SHA drift
    if patch.base_head_sha != head:
        preflight["binding"] = False
        return _blocked(
            patch=patch,
            spec=pass_spec,
            message=f"HEAD drift: patch base {patch.base_head_sha} != {head}",
            preflight=preflight,
        )
    if patch.base_origin_sha is not None and origin is not None and patch.base_origin_sha != origin:
        return _blocked(
            patch=patch,
            spec=pass_spec,
            message=f"origin drift: patch base {patch.base_origin_sha} != {origin}",
            preflight=preflight,
        )
    if not clean:
        return _blocked(patch=patch, spec=pass_spec, message="working tree not clean", preflight=preflight)

    # Approval binding
    ph = patch_content_hash(patch)
    psh = pass_spec_hash(pass_spec)
    if approval.patch_id != patch.patch_id or approval.patch_hash != ph:
        return _blocked(patch=patch, spec=pass_spec, message="approval patch binding mismatch", preflight=preflight)
    if approval.plan_id != patch.plan_id or approval.plan_hash != patch.plan_content_hash:
        return _blocked(patch=patch, spec=pass_spec, message="approval plan binding mismatch", preflight=preflight)
    if approval.base_head_sha != patch.base_head_sha:
        return _blocked(patch=patch, spec=pass_spec, message="approval base_head binding mismatch", preflight=preflight)
    if approval.pass_spec_hash != psh:
        return _blocked(patch=patch, spec=pass_spec, message="approval PassSpec binding mismatch", preflight=preflight)

    preflight["binding"] = True
    preflight["authorization"] = True

    # Scope
    paths = sorted({f.get("path", "") for f in (patch.files or []) if f.get("path")})
    for path in paths:
        if not path_in_allowlist(path, pass_spec.allowed_paths):
            return _blocked(patch=patch, spec=pass_spec, message=f"OUT_OF_SCOPE: {path}", preflight=preflight)
        for f in pass_spec.forbidden_paths:
            ff = f.replace("\\", "/").lstrip("./")
            if ff and (path == ff or path.startswith(ff.rstrip("/") + "/")):
                return _blocked(patch=patch, spec=pass_spec, message=f"forbidden path: {path}", preflight=preflight)
    preflight["scope"] = True

    if patch.status in ("STALE", "PLAN_BINDING_MISMATCH", "OUT_OF_SCOPE", "INVALID", "PATCH_BASE_MISMATCH"):
        return _blocked(
            patch=patch,
            spec=pass_spec,
            message=f"patch status not executable: {patch.status}",
            preflight=preflight,
        )

    # Build K3 plan and require explicit approval on plan (PassSpec is auth; plan still marked approved for K3)
    try:
        plan = patch_to_k3_plan(patch, pass_spec)
        approve_plan(plan)  # human already approved via PatchApproval bound to this patch
    except PlanError as e:
        return _blocked(patch=patch, spec=pass_spec, message=str(e), preflight=preflight)

    if not run_k3:
        # Test/orchestration dry mode: all gates passed, mutation not attempted
        return ExecutionResult(
            execution_id=_eid(patch.patch_id, "PRECHECKED"),
            patch_id=patch.patch_id,
            patch_hash=ph,
            plan_id=patch.plan_id,
            plan_hash=patch.plan_content_hash,
            pass_spec_hash=psh,
            base_head_sha=patch.base_head_sha,
            base_origin_sha=patch.base_origin_sha,
            preflight=preflight,
            mutation={"attempted": False, "changed_files": [], "result": "PRECHECKED"},
            verification={"status": "NOT_RUN"},
            publication={"required": bool(getattr(pass_spec, "publication_required", True)), "status": "NOT_ATTEMPTED"},
            final_status="BLOCKED",  # no mutation without K3
            authorization={
                "current_pass_authorized": False,
                "note": "Preflight OK but run_k3=False; no mutation. Future session still needs PassSpec.",
            },
            message="preflight passed; K3 not invoked",
        )

    # Sole mutation path
    try:
        tx: TransactionResult = run_transaction(
            pass_spec,
            task=pass_spec.objective,
            plan=plan,
            require_plan_approval=True,
            auto_approve_if_spec_is_authorization=False,
            repo_root=repo_root,
        )
    except Exception as e:
        return _blocked(patch=patch, spec=pass_spec, message=f"K3 transaction error: {e}", preflight=preflight, status="FAILED")

    changed = []
    if tx.session and getattr(tx.session, "changed_files", None):
        changed = list(tx.session.changed_files or [])
    # K12 verification input
    test_results = {}
    if tx.session and getattr(tx.session, "test_results", None):
        test_results = dict(tx.session.test_results or {})

    vreport = verify_implementation(
        {
            "plan_id": patch.plan_id,
            "objective": pass_spec.objective,
            "affected_paths": paths,
            "implementation_steps": plan.implementation_steps,
            "proposed_changes": paths,
            "test_strategy": {"required_tests": list(pass_spec.required_tests)},
            "risk_register": [],
        },
        actual_paths=changed or paths,
        test_results=test_results,
        result_sha=current_head(repo_root),
        remote_sha=current_origin_main(repo_root),
        publication_required=bool(getattr(pass_spec, "publication_required", True)),
        pass_spec=pass_spec,
        repo_root=repo_root,
    )

    final = tx.status
    if final == "PASS" and vreport.verdict.get("status") == "FAILED":
        final = "FAILED"
    if final == "PASS" and vreport.verdict.get("status") == "INSUFFICIENT_EVIDENCE":
        # keep PASS if K3 published; verification notes insufficiency
        pass

    pub_status = "UNKNOWN"
    if tx.status == "PASS":
        h = current_head(repo_root)
        o = current_origin_main(repo_root)
        pub_status = "PUBLISHED" if h == o else "PENDING_PUBLICATION"
        if pub_status == "PENDING_PUBLICATION":
            final = "PENDING_PUBLICATION"
    elif tx.status == "NO_CHANGE":
        pub_status = "NOT_REQUIRED"
        final = "NO_CHANGE"

    return ExecutionResult(
        execution_id=_eid(patch.patch_id, final),
        patch_id=patch.patch_id,
        patch_hash=ph,
        plan_id=patch.plan_id,
        plan_hash=patch.plan_content_hash,
        pass_spec_hash=psh,
        base_head_sha=patch.base_head_sha,
        base_origin_sha=patch.base_origin_sha,
        preflight=preflight,
        mutation={
            "attempted": True,
            "changed_files": changed,
            "result": tx.status,
            "k3_stage": tx.stage,
            "k3_message": tx.message,
        },
        verification={
            "status": vreport.verdict.get("status"),
            "report_id": vreport.verification_id,
            "reasons": vreport.verdict.get("reasons"),
        },
        publication={
            "required": bool(getattr(pass_spec, "publication_required", True)),
            "status": pub_status,
            "commit_sha": current_head(repo_root),
            "remote_sha": current_origin_main(repo_root),
        },
        final_status=final,
        authorization={
            "current_pass_authorized": False,
            "note": "Execution complete. Fresh sessions require a new PassSpec. MEMORY ≠ AUTHORIZATION.",
        },
        message=tx.message,
    )
