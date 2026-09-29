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
    """Line-local unified diff (not applied). MVP: never emit redesign-region hunks."""
    import difflib
    if operation == "ADD":
        lines = [f"--- /dev/null", f"+++ b/{path}"]
        for ln in after.splitlines() or [""]:
            lines.append(f"+{ln}")
        return "\n".join(lines) + "\n"
    if operation == "DELETE":
        lines = [f"--- a/{path}", f"+++ /dev/null"]
        for ln in before.splitlines():
            lines.append(f"-{ln}")
        return "\n".join(lines) + "\n"
    bl = before.splitlines(keepends=True)
    al = after.splitlines(keepends=True)
    diff = list(difflib.unified_diff(bl, al, fromfile=f"a/{path}", tofile=f"b/{path}", n=3, lineterm=""))
    if not diff:
        return f"--- a/{path}\n+++ b/{path}\n# no textual delta\n"
    return "\n".join(line.rstrip("\n") for line in diff) + "\n"



def _count_diff_lines(patch_text: str) -> dict[str, int]:
    added = removed = 0
    for ln in (patch_text or "").splitlines():
        if ln.startswith("+++") or ln.startswith("---") or ln.startswith("@@"):
            continue
        if ln.startswith("+"):
            added += 1
        elif ln.startswith("-"):
            removed += 1
    return {"added": added, "removed": removed, "changed": added + removed}


def _extract_docstring_text(objective: str) -> str | None:
    """Pull quoted replacement text from a concrete docstring objective, if present."""
    import re
    o = objective or ""
    m = re.search(
        r"(?:to\s+say|to\s*:|as)\s+[\"']([^\"']{3,200})[\"']",
        o,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    m = re.search(r"[\"']([^\"']{8,200})[\"']", o)
    if m and "docstring" in o.lower():
        return m.group(1).strip()
    return None


def _objective_docstring_intent(objective: str) -> bool:
    o = (objective or "").lower()
    return "docstring" in o and any(
        k in o for k in ("update", "clarify", "change", "set", "replace", "rewrite", "module")
    )


def _surgical_module_docstring(before: str, new_text: str) -> tuple[str, str]:
    """Replace module docstring only. Returns (after, strategy)."""
    import re
    m = re.match(r'(?s)^(\s*)([ruRU]{0,2})("""|\'\'\')(.*?)(\3)(\s*)', before)
    if not m:
        after = f'"""{new_text}"""\n' + before
        return after, "MODULE_DOCSTRING_INSERT"
    prefix, flags, quote, _old, _q2, trail = (
        m.group(1), m.group(2) or "", m.group(3), m.group(4), m.group(5), m.group(6)
    )
    replacement = f"{prefix}{flags}{quote}{new_text}{quote}{trail}"
    after = replacement + before[m.end():]
    return after, "MODULE_DOCSTRING_REPLACE"


def _surgical_modify(
    before: str,
    *,
    objective: str,
    symbols: list[str],
    impl: str,
) -> tuple[str, str, str]:
    """Attempt surgical after-state for MODIFY. Returns (after, strategy, fidelity)."""
    if _objective_docstring_intent(objective):
        new_text = _extract_docstring_text(objective)
        if not new_text:
            new_text = "Clarified module purpose for operator review."
        after, strategy = _surgical_module_docstring(before, new_text)
        return after, strategy, "HIGH"
    marker = (
        f"\n# [K14 PROPOSED] {impl[:200]}\n" if impl else "\n# [K14 PROPOSED] under-specified\n"
    )
    after = before + marker if before else marker
    return after, "ANNOTATIVE_MARKER", "LIMITED"


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
        fe_strategy = None
        fe_fidelity = None
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
            if not symbols and not impl and not _objective_docstring_intent(str(cs_d.get("objective") or "")):
                under_specified = True
            after, strategy, fidelity = _surgical_modify(
                before,
                objective=str(cs_d.get("objective") or ""),
                symbols=symbols,
                impl=impl,
            )
            fe_strategy = strategy
            fe_fidelity = fidelity
        elif op == "DELETE":
            after = ""

        if under_specified and status == PatchStatus.PROPOSED.value:
            status = PatchStatus.PATCH_UNDER_SPECIFIED.value
        if base_mismatch and status in (PatchStatus.PROPOSED.value, PatchStatus.VALID.value):
            status = PatchStatus.PATCH_BASE_MISMATCH.value

        patch_text = _unified_diff(path, before, after, op)
        line_stats = _count_diff_lines(patch_text)
        entry = {
                "path": path,
                "operation": op,
                "symbols_or_regions": sorted(symbols),
                "before": before[:4000],
                "after": after[:4000],
                "patch_text": patch_text,
                "evidence_refs": list(fe.get("evidence_refs") or [])[:5],
                "plan_step": fe.get("plan_step") or "",
                "claim_kinds": list(fe.get("claim_kinds") or []),
                "line_stats": line_stats,
            }
        if op == "MODIFY":
            entry["synthesis_strategy"] = locals().get("fe_strategy") or "UNKNOWN"
            entry["fidelity"] = locals().get("fe_fidelity") or "LIMITED"
        patch_files.append(entry)

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
        "fidelity": (
            "HIGH"
            if patch_files and all((f.get("fidelity") == "HIGH") for f in patch_files if f.get("operation") == "MODIFY")
            and any(f.get("operation") == "MODIFY" for f in patch_files)
            else (
                "LIMITED"
                if any(f.get("fidelity") == "LIMITED" for f in patch_files)
                else "UNKNOWN"
            )
        ),
        "synthesis_strategies": {
            f["path"]: f.get("synthesis_strategy") for f in patch_files if f.get("synthesis_strategy")
        },
        "line_stats": {f["path"]: f.get("line_stats") for f in patch_files},
        "implementation_quality": (
            "HIGH"
            if patch_files and all((f.get("fidelity") == "HIGH") for f in patch_files if f.get("operation") == "MODIFY")
            and any(f.get("operation") == "MODIFY" for f in patch_files)
            else "LIMITED"
        ),
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
