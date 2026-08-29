"""WEAVER-K14 — Deterministic patch synthesis + dry-run impact analysis.

PATCH ≠ AUTHORIZATION. DRY RUN ≠ EXECUTION. Never applies patches.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .evidence import collect_evidence, query_evidence
from .implementation import ProposedChangeSet, synthesize_changeset
from .pass_spec import PassSpec, current_head, current_origin_main, path_in_allowlist
from .verification import plan_content_hash


class PatchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    VALID = "VALID"
    STALE = "STALE"
    PLAN_BINDING_MISMATCH = "PLAN_BINDING_MISMATCH"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    PATCH_UNDER_SPECIFIED = "PATCH_UNDER_SPECIFIED"
    PATCH_BASE_MISMATCH = "PATCH_BASE_MISMATCH"
    INVALID = "INVALID"


@dataclass
class ProposedPatch:
    patch_id: str
    base_head_sha: str
    base_origin_sha: str | None
    plan_id: str
    plan_content_hash: str
    changeset_id: str
    status: str
    files: list[dict[str, Any]] = field(default_factory=list)
    tests: dict[str, Any] = field(default_factory=dict)
    impact: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    authorization: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pid(base: str, cs_id: str, files: list[dict[str, Any]]) -> str:
    norm = json.dumps(
        [
            {
                "path": f.get("path"),
                "operation": f.get("operation"),
                "patch_text": f.get("patch_text"),
            }
            for f in files
        ],
        sort_keys=True,
    )
    return "patch-" + hashlib.sha256(f"{base}|{cs_id}|{norm}".encode()).hexdigest()[:12]


def _unified_diff(path: str, before: str, after: str, operation: str) -> str:
    """Minimal unified-diff style text (not applied)."""
    if operation == "ADD":
        lines = [f"--- /dev/null", f"+++ b/{path}"]
        for i, ln in enumerate(after.splitlines() or [""], 1):
            lines.append(f"+{ln}")
        return "\n".join(lines) + "\n"
    if operation == "DELETE":
        lines = [f"--- a/{path}", f"+++ /dev/null"]
        for ln in before.splitlines():
            lines.append(f"-{ln}")
        return "\n".join(lines) + "\n"
    # MODIFY
    bl = before.splitlines()
    al = after.splitlines()
    lines = [f"--- a/{path}", f"+++ b/{path}", f"@@ redesign region @@"]
    for ln in bl[:40]:
        lines.append(f"-{ln}")
    for ln in al[:40]:
        lines.append(f"+{ln}")
    if len(bl) > 40 or len(al) > 40:
        lines.append("# ... truncated for review ...")
    return "\n".join(lines) + "\n"


def synthesize_patch(
    changeset: ProposedChangeSet | dict[str, Any],
    *,
    pass_spec: PassSpec | None = None,
    expected_plan_hash: str | None = None,
    bound_head_sha: str | None = None,
    bound_origin_sha: str | None = None,
    repo_root: str = ".",
) -> ProposedPatch:
    """Build reviewable patch artifact. Never applies to disk."""
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)

    if isinstance(changeset, ProposedChangeSet):
        cs = changeset
        cs_d = cs.to_dict()
    else:
        cs_d = dict(changeset)
        cs = None

    plan_id = str(cs_d.get("plan_id") or "")
    ph = str(cs_d.get("plan_content_hash") or "")
    cs_id = str(cs_d.get("changeset_id") or "")
    base_head = bound_head_sha or str(cs_d.get("base_head_sha") or head)
    base_origin = bound_origin_sha if bound_origin_sha is not None else cs_d.get("base_origin_sha", origin)
    file_entries = list(cs_d.get("files") or [])

    status = PatchStatus.PROPOSED.value
    validation: dict[str, Any] = {
        "syntax": "n/a",
        "patch_applicability": "dry-run-only",
        "scope": "pending",
        "plan_binding": "valid",
        "sha_binding": "valid",
        "base_match": "valid",
    }

    if base_head != head or (base_origin is not None and origin is not None and base_origin != origin):
        status = PatchStatus.STALE.value
        validation["sha_binding"] = "STALE"

    if expected_plan_hash and expected_plan_hash != ph:
        status = PatchStatus.PLAN_BINDING_MISMATCH.value
        validation["plan_binding"] = "PLAN_BINDING_MISMATCH"

    if cs_d.get("status") == "OUT_OF_SCOPE" or (cs_d.get("scope") or {}).get("out_of_scope"):
        if status == PatchStatus.PROPOSED.value:
            status = PatchStatus.OUT_OF_SCOPE.value
        validation["scope"] = "OUT_OF_SCOPE"

    patch_files: list[dict[str, Any]] = []
    under_specified = False
    base_mismatch = False

    for fe in sorted(file_entries, key=lambda x: x.get("path") or ""):
        path = (fe.get("path") or "").replace("\\", "/").lstrip("./")
        op = fe.get("operation") or "MODIFY"
        symbols = list(fe.get("symbols_or_regions") or [])
        impl = (fe.get("implementation") or "").strip()
        reason = fe.get("reason") or ""

        if pass_spec and status not in (PatchStatus.STALE.value, PatchStatus.PLAN_BINDING_MISMATCH.value):
            forbidden = False
            for f in pass_spec.forbidden_paths:
                ff = f.replace("\\", "/").lstrip("./")
                if ff and (path == ff or path.startswith(ff.rstrip("/") + "/")):
                    forbidden = True
                    break
            if forbidden or not path_in_allowlist(path, pass_spec.allowed_paths):
                status = PatchStatus.OUT_OF_SCOPE.value
                validation["scope"] = "OUT_OF_SCOPE"

        p = Path(repo_root) / path
        before = ""
        if p.is_file():
            before = p.read_text(encoding="utf-8", errors="replace")
        elif op == "MODIFY":
            base_mismatch = True
            validation["base_match"] = "PATCH_BASE_MISMATCH"

        # after: only synthesize concrete content when ADD + enough design text
        after = before
        if op == "ADD":
            if impl and len(impl) > 20:
                # Design placeholder content — explicit that this is proposed, not applied
                after = (
                    f'"""Proposed module: {path}\n\n'
                    f"Design (NOT APPLIED):\n{impl}\n"
                    f'Reason: {reason}\n"""\n'
                    f"# TODO: implement under authorized K3 transaction\n"
                )
            else:
                under_specified = True
                after = ""
        elif op == "MODIFY":
            if not symbols and not impl:
                under_specified = True
            # Annotative after-state for review (not applied): append design marker comment
            marker = f"\n# [K14 PROPOSED] {impl[:200]}\n" if impl else "\n# [K14 PROPOSED] under-specified\n"
            after = before + marker if before else marker
        elif op == "DELETE":
            after = ""

        if under_specified and status == PatchStatus.PROPOSED.value:
            status = PatchStatus.PATCH_UNDER_SPECIFIED.value
        if base_mismatch and status in (PatchStatus.PROPOSED.value, PatchStatus.VALID.value):
            status = PatchStatus.PATCH_BASE_MISMATCH.value

        patch_text = _unified_diff(path, before, after, op)
        patch_files.append(
            {
                "path": path,
                "operation": op,
                "symbols_or_regions": sorted(symbols),
                "before": before[:4000],
                "after": after[:4000],
                "patch_text": patch_text,
                "evidence_refs": list(fe.get("evidence_refs") or [])[:5],
                "plan_step": fe.get("plan_step") or "",
                "claim_kinds": list(fe.get("claim_kinds") or []),
            }
        )

    if status == PatchStatus.PROPOSED.value and patch_files and not under_specified and not base_mismatch:
        status = PatchStatus.VALID.value
        validation["scope"] = validation.get("scope") if validation.get("scope") != "pending" else "ok"

    # Impact analysis via K10
    impact_files = sorted({f["path"] for f in patch_files})
    impact_symbols: list[str] = []
    for f in patch_files:
        impact_symbols.extend(f.get("symbols_or_regions") or [])
    impact_symbols = sorted(set(impact_symbols))

    deps: list[str] = []
    layers: list[str] = []
    test_refs: list[str] = []
    try:
        idx = collect_evidence(repo_root, roots=["weaver", "tests"])
        for path in impact_files:
            q = query_evidence(idx, path)
            for r in q.get("dependents") or []:
                s = r.get("source")
                if s and s not in deps:
                    deps.append(s)
            for r in q.get("architecture") or []:
                t = r.get("target")
                if t and t not in layers:
                    layers.append(t)
            for r in q.get("tests") or []:
                s = r.get("source")
                if s and s not in test_refs:
                    test_refs.append(s)
    except Exception:
        pass

    tests_block = {
        "existing": sorted(test_refs),
        "required": sorted((cs_d.get("tests") or {}).get("required_tests") or []),
        "affected": sorted(test_refs),
        "note": "DIRECT_TEST_REFERENCE is static; runtime coverage UNKNOWN",
        "runtime_coverage": "UNKNOWN",
    }

    impact = {
        "files": impact_files,
        "symbols": impact_symbols,
        "architecture_layers": sorted(layers),
        "dependencies": sorted(deps)[:40],
        "tests": sorted(test_refs),
    }

    auth = {
        "current_pass_authorized": bool(pass_spec is not None),
        "state": "PASS_SPEC" if pass_spec else "NONE",
        "note": "PATCH ≠ AUTHORIZATION",
    }
    execution = {"applied": False, "EXECUTED": False}

    review = {
        "summary": f"Patch {status} for {len(patch_files)} file(s)",
        "objective": cs_d.get("objective"),
        "files": [f["path"] for f in patch_files],
        "operations": {f["path"]: f["operation"] for f in patch_files},
        "symbols": {f["path"]: f["symbols_or_regions"] for f in patch_files},
        "impact": impact,
        "tests": tests_block,
        "risks": list(cs_d.get("risks") or []),
        "assumptions": list(cs_d.get("assumptions") or []),
        "unknowns": list(cs_d.get("unknowns") or []),
        "scope_status": validation.get("scope"),
        "sha_status": validation.get("sha_binding"),
        "plan_binding_status": validation.get("plan_binding"),
        "authorization": auth,
        "execution": execution,
        "EXECUTED": False,
    }

    pid = _pid(base_head, cs_id, patch_files)
    return ProposedPatch(
        patch_id=pid,
        base_head_sha=base_head,
        base_origin_sha=base_origin if isinstance(base_origin, str) or base_origin is None else str(base_origin),
        plan_id=plan_id,
        plan_content_hash=ph,
        changeset_id=cs_id,
        status=status,
        files=patch_files,
        tests=tests_block,
        impact=impact,
        validation=validation,
        review=review,
        authorization=auth,
        execution=execution,
    )


def review_patch(patch: ProposedPatch) -> dict[str, Any]:
    return dict(patch.review or patch.to_dict())
