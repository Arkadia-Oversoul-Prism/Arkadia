"""WEAVER-K13 — Governed implementation synthesis (DESIGN only).

PROPOSED CHANGESET ≠ EXECUTION ≠ AUTHORIZATION.
Does not write, commit, push, or apply patches.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .engineering_plan import EngineeringPlan
from .pass_spec import PassSpec, current_head, current_origin_main, path_in_allowlist
from .verification import plan_content_hash


class FileOp(str, Enum):
    ADD = "ADD"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    RENAME = "RENAME"


class ClaimKind(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    ASSUMPTION = "ASSUMPTION"
    UNKNOWN = "UNKNOWN"


class ChangesetStatus(str, Enum):
    PROPOSED = "PROPOSED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    STALE = "STALE"
    PLAN_BINDING_MISMATCH = "PLAN_BINDING_MISMATCH"
    BLOCKED = "BLOCKED"


@dataclass
class ProposedFileChange:
    path: str
    operation: str
    symbols_or_regions: list[str] = field(default_factory=list)
    reason: str = ""
    implementation: str = ""  # concrete design instruction / pseudo-diff, not applied
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    plan_step: str = ""
    risk: str = ""
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    claim_kinds: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedChangeSet:
    changeset_id: str
    plan_id: str
    plan_content_hash: str
    objective: str
    base_head_sha: str
    base_origin_sha: str | None
    scope: dict[str, Any] = field(default_factory=dict)
    files: list[dict[str, Any]] = field(default_factory=list)
    tests: dict[str, Any] = field(default_factory=dict)
    verification_requirements: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    status: str = ChangesetStatus.PROPOSED.value
    authorization: dict[str, Any] = field(default_factory=dict)
    review_bundle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cid(base: str, plan_hash: str, files: list[dict[str, Any]]) -> str:
    norm = json.dumps(
        [{"path": f.get("path"), "operation": f.get("operation"), "symbols": f.get("symbols_or_regions")} for f in files],
        sort_keys=True,
    )
    return "cs-" + hashlib.sha256(f"{base}|{plan_hash}|{norm}".encode()).hexdigest()[:12]


def _read_symbols(repo_root: str, rel: str) -> list[str]:
    path = Path(repo_root) / rel
    if not path.is_file() or path.suffix != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
    return names


def _file_exists(repo_root: str, rel: str) -> bool:
    return (Path(repo_root) / rel).is_file()


def synthesize_changeset(
    plan: EngineeringPlan | dict[str, Any],
    *,
    pass_spec: PassSpec | None = None,
    expected_plan_hash: str | None = None,
    bound_head_sha: str | None = None,
    bound_origin_sha: str | None = None,
    repo_root: str = ".",
) -> ProposedChangeSet:
    """Design-only synthesis. Never mutates the repository."""
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    base_head = bound_head_sha or head
    base_origin = bound_origin_sha if bound_origin_sha is not None else origin

    if isinstance(plan, EngineeringPlan):
        plan_id = plan.plan_id
        objective = plan.objective
        paths = list(plan.affected_paths)
        steps = list(plan.implementation_steps)
        required_tests = list((plan.test_strategy or {}).get("required_tests") or [])
        missing_test_paths = list((plan.test_strategy or {}).get("paths_without_discoverable_tests") or [])
        verif = list(plan.verification_strategy or [])
        risks = [r.get("description", str(r)) if isinstance(r, dict) else str(r) for r in (plan.risk_register or [])]
        unknowns = [u.get("statement", str(u)) if isinstance(u, dict) else str(u) for u in (plan.unknowns or [])]
        proposed = list(plan.proposed_changes or [])
        ph = plan_content_hash(plan)
        evidence_refs = list(plan.evidence_refs or [])
    else:
        plan_id = str(plan.get("plan_id") or "")
        objective = str(plan.get("objective") or "")
        paths = list(plan.get("affected_paths") or [])
        steps = list(plan.get("implementation_steps") or [])
        required_tests = list((plan.get("test_strategy") or {}).get("required_tests") or [])
        missing_test_paths = list((plan.get("test_strategy") or {}).get("paths_without_discoverable_tests") or [])
        verif = list(plan.get("verification_strategy") or [])
        risks = [str(r) for r in (plan.get("risk_register") or [])]
        unknowns = [str(u) for u in (plan.get("unknowns") or [])]
        proposed = list(plan.get("proposed_changes") or [])
        ph = plan_content_hash(plan)
        evidence_refs = list(plan.get("evidence_refs") or [])

    status = ChangesetStatus.PROPOSED.value
    unresolved: list[str] = []

    if base_head != head or (base_origin is not None and origin is not None and base_origin != origin):
        status = ChangesetStatus.STALE.value
        unresolved.append("repository advanced since synthesis base")

    if expected_plan_hash and expected_plan_hash != ph:
        status = ChangesetStatus.PLAN_BINDING_MISMATCH.value
        unresolved.append("plan content hash mismatch")

    # Scope
    in_scope: list[str] = []
    out: list[str] = []
    for p in sorted(set(paths)):
        n = p.replace("\\", "/").lstrip("./")
        if pass_spec:
            forbidden = False
            for f in pass_spec.forbidden_paths:
                ff = f.replace("\\", "/").lstrip("./")
                if ff and (n == ff or n.startswith(ff.rstrip("/") + "/") or n.startswith(ff)):
                    forbidden = True
                    break
            if forbidden or not path_in_allowlist(n, pass_spec.allowed_paths):
                out.append(n)
            else:
                in_scope.append(n)
        else:
            in_scope.append(n)
    if out and status == ChangesetStatus.PROPOSED.value:
        status = ChangesetStatus.OUT_OF_SCOPE.value
        unresolved.append(f"out of scope: {out}")

    # File-level synthesis
    file_changes: list[dict[str, Any]] = []
    assumptions: list[str] = [
        "Existing public interfaces remain stable unless a change explicitly targets them.",
    ]
    for i, path in enumerate(in_scope):
        exists = _file_exists(repo_root, path)
        op = FileOp.MODIFY.value if exists else FileOp.ADD.value
        symbols = _read_symbols(repo_root, path) if exists else []
        step = steps[i] if i < len(steps) else (steps[-1] if steps else "Implement planned change")
        reason = proposed[i] if i < len(proposed) else (proposed[0] if proposed else f"Address objective at {path}")
        # Implementation design text (not applied)
        if exists and symbols:
            impl = (
                f"MODIFY {path}: review symbols {symbols[:12]}; "
                f"apply plan step «{step}»; keep unrelated symbols unchanged."
            )
            kinds = [ClaimKind.FACT.value, ClaimKind.INFERENCE.value]
        elif exists:
            impl = f"MODIFY {path}: file exists but no top-level symbols parsed; apply «{step}» carefully."
            kinds = [ClaimKind.FACT.value, ClaimKind.UNKNOWN.value]
            unknowns.append(f"symbol map incomplete for {path}")
        else:
            impl = f"ADD {path}: create module implementing «{step}»; export minimal public API."
            kinds = [ClaimKind.INFERENCE.value]
            assumptions.append(f"New path {path} is the correct location for this capability.")

        # Test synthesis hint
        test_note = ""
        if path in missing_test_paths:
            test_note = "NEW_TEST_REQUIRED"
            unknowns.append(f"No discoverable test for {path}")
        elif required_tests:
            test_note = "EXISTING_TEST"
        else:
            test_note = "UNKNOWN"

        fc = ProposedFileChange(
            path=path,
            operation=op,
            symbols_or_regions=symbols[:20],
            reason=str(reason),
            implementation=impl,
            evidence_refs=evidence_refs[:5],
            plan_step=step,
            risk=risks[0] if risks else "",
            assumptions=list(assumptions[-2:]),
            unknowns=[u for u in unknowns if path in u][:3],
            claim_kinds=kinds,
        )
        d = fc.to_dict()
        d["test_mapping"] = test_note
        file_changes.append(d)

    # Optional test file proposals (design only)
    test_block = {
        "required_tests": sorted(required_tests),
        "file_test_mapping": {f["path"]: f.get("test_mapping") for f in file_changes},
        "note": "EXISTING_TEST is static discoverability, not runtime coverage",
    }

    files_sorted = sorted(file_changes, key=lambda x: x["path"])
    cid = _cid(base_head, ph, files_sorted)

    auth = {
        "current_pass_authorized": bool(pass_spec is not None),
        "state": "PASS_SPEC" if pass_spec else "NONE",
        "note": "PROPOSED CHANGESET ≠ AUTHORIZATION ≠ EXECUTION",
    }

    review = {
        "objective": objective,
        "plan_id": plan_id,
        "plan_content_hash": ph,
        "evidence_refs": evidence_refs[:10],
        "changes": files_sorted,
        "affected_files": [f["path"] for f in files_sorted],
        "operations": {f["path"]: f["operation"] for f in files_sorted},
        "symbols": {f["path"]: f["symbols_or_regions"] for f in files_sorted},
        "tests": test_block,
        "verification": verif,
        "risks": risks,
        "assumptions": assumptions,
        "unknowns": unknowns,
        "scope": {"in_scope": in_scope, "out_of_scope": out},
        "authorization": auth,
        "status": status,
        "next_action": "awaiting human authorization",
    }

    return ProposedChangeSet(
        changeset_id=cid,
        plan_id=plan_id,
        plan_content_hash=ph,
        objective=objective,
        base_head_sha=base_head,
        base_origin_sha=base_origin,
        scope={"in_scope": in_scope, "out_of_scope": out, "pass_spec_bound": bool(pass_spec)},
        files=files_sorted,
        tests=test_block,
        verification_requirements=verif,
        risks=risks,
        assumptions=assumptions,
        unknowns=unknowns,
        unresolved=unresolved,
        status=status,
        authorization=auth,
        review_bundle=review,
    )


def review_changeset(cs: ProposedChangeSet) -> dict[str, Any]:
    return dict(cs.review_bundle or cs.to_dict())
