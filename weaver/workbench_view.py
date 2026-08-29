"""WEAVER-W1 — Operator view model over existing Weaver APIs (no mutation).

UI/adapter only. Does not write files, commit, push, or apply patches.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any

from .analysis import analyze_objective
from .continuation import load_continuation
from .engineering_plan import build_engineering_plan
from .evidence import evidence_for_analysis
from .implementation import synthesize_changeset
from .pass_spec import current_head, current_origin_main
from .patch import synthesize_patch
from .recon import build_context_packet
from .verification import VerificationVerdict


LIFECYCLE = [
    "RECON",
    "EVIDENCE",
    "ANALYSIS",
    "PLAN",
    "CHANGESET",
    "PATCH",
    "REVIEW",
    "APPROVAL",
    "EXECUTION",
    "VERIFICATION",
]


@dataclass
class ObservatoryState:
    repository: dict[str, Any]
    system: dict[str, Any]
    authority: dict[str, Any]
    lifecycle: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git_status_short(repo_root: str) -> str:
    r = subprocess.run(["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True)
    return (r.stdout or "").strip()


def _ahead_behind(repo_root: str) -> tuple[int, int]:
    r = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return (0, 0)
    parts = (r.stdout or "0\t0").strip().split()
    try:
        return int(parts[0]), int(parts[1] if len(parts) > 1 else 0)
    except ValueError:
        return (0, 0)


def repository_state(repo_root: str = ".") -> dict[str, Any]:
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    dirty = bool(_git_status_short(repo_root))
    ahead, behind = _ahead_behind(repo_root)
    cont_status, _, cont_msg = load_continuation(repo_root)
    return {
        "identity": "Arkadia-Oversoul-Prism/Arkadia",
        "branch": "main",
        "head_sha": head,
        "origin_sha": origin,
        "clean": not dirty,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "continuation_status": cont_status.value if hasattr(cont_status, "value") else str(cont_status),
        "continuation_message": cont_msg,
        "stale_hint": cont_status.value == "STALE" if hasattr(cont_status, "value") else False,
    }


def observatory(repo_root: str = ".", pipeline: dict[str, Any] | None = None) -> ObservatoryState:
    """Surface 1 — What is Weaver right now?"""
    repo = repository_state(repo_root)
    pipe = pipeline or {}
    stages = []
    for name in LIFECYCLE:
        info = pipe.get(name) or {}
        stages.append(
            {
                "stage": name,
                "status": info.get("status", "AVAILABLE" if name in ("RECON", "EVIDENCE") else "PENDING"),
                "detail": info.get("detail", ""),
            }
        )
    auth = {
        "PassSpec": "PRESENT" if pipe.get("pass_spec") else "NONE",
        "PatchApproval": "PRESENT" if pipe.get("patch_approval") else "NONE",
        "Execution": "READY" if pipe.get("pass_spec") and pipe.get("patch_approval") else "LOCKED",
        "Mutation path": "K3 ONLY",
        "note": "PROPOSED ≠ APPROVAL ≠ EXECUTION ≠ VERIFICATION",
    }
    system = {
        "lifecycle": " → ".join(LIFECYCLE),
        "engine": "Weaver K0.1–K15 control plane",
        "workbench": "W1 operator cockpit (read-only default)",
    }
    return ObservatoryState(repository=repo, system=system, authority=auth, lifecycle=stages)


def run_read_only_pipeline(objective: str, repo_root: str = ".") -> dict[str, Any]:
    """
    Surfaces 2–3: objective → analysis → plan → changeset → patch.
    Never mutates. Never creates PassSpec or approval.
    """
    objective = (objective or "").strip()
    out: dict[str, Any] = {
        "objective": objective,
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "Mutation path": "K3 ONLY",
            "note": "Read-only pipeline. ANALYSIS ≠ AUTHORIZATION.",
        },
        "executed": False,
    }
    if not objective:
        out["status"] = "BLOCKED"
        out["message"] = "empty objective"
        return out

    # Recon / context
    try:
        ctx = build_context_packet(repo_root)
    except Exception as e:
        ctx = {"error": str(e)}
    out["recon"] = {"status": "COMPLETED", "context_keys": sorted(ctx.keys()) if isinstance(ctx, dict) else []}

    # Evidence
    try:
        ev = evidence_for_analysis(repo_root, subject_hints=["weaver/workbench_view.py", "weaver/execution.py"])
    except Exception as e:
        ev = {"error": str(e)}
    out["evidence"] = {
        "status": "COMPLETED",
        "summary": (ev.get("index_summary") if isinstance(ev, dict) else {}),
        "authorization": (ev.get("authorization") if isinstance(ev, dict) else {}),
    }

    # Analysis
    analysis = analyze_objective(objective, pass_spec=None, repo_root=repo_root)
    out["analysis"] = {
        "status": "COMPLETED",
        "result_kind": analysis.result_kind,
        "facts": analysis.evidence.get("facts") if analysis.evidence else [],
        "inferences": analysis.evidence.get("inferences") if analysis.evidence else [],
        "unknowns": analysis.evidence.get("unknowns") if analysis.evidence else [],
        "risks": analysis.risks,
        "alternatives": analysis.alternatives,
        "authorization": analysis.authorization,
        "continuation_state": analysis.continuation_state,
    }

    # Plan (no PassSpec → unscoped / candidate)
    plan = build_engineering_plan(objective, pass_spec=None, repo_root=repo_root)
    out["plan"] = {
        "status": "COMPLETED",
        "plan_id": plan.plan_id,
        "objective": plan.objective,
        "scope_status": plan.scope_status,
        "affected_paths": plan.affected_paths,
        "implementation_steps": plan.implementation_steps,
        "test_strategy": plan.test_strategy,
        "risk_register": plan.risk_register,
        "authorization": plan.authorization,
        "approval": plan.approval,
        "review_bundle": plan.review_bundle,
    }

    # Changeset
    cs = synthesize_changeset(plan, pass_spec=None, repo_root=repo_root)
    out["changeset"] = {
        "status": cs.status,
        "changeset_id": cs.changeset_id,
        "plan_id": cs.plan_id,
        "plan_content_hash": cs.plan_content_hash,
        "base_head_sha": cs.base_head_sha,
        "files": cs.files,
        "tests": cs.tests,
        "authorization": cs.authorization,
        "review_bundle": cs.review_bundle,
    }

    # Patch
    patch = synthesize_patch(cs, pass_spec=None, repo_root=repo_root)
    out["patch"] = {
        "status": patch.status,
        "patch_id": patch.patch_id,
        "base_head_sha": patch.base_head_sha,
        "plan_content_hash": patch.plan_content_hash,
        "files": [
            {
                "path": f.get("path"),
                "operation": f.get("operation"),
                "symbols": f.get("symbols_or_regions"),
                "patch_text": (f.get("patch_text") or "")[:2000],
            }
            for f in (patch.files or [])
        ],
        "validation": patch.validation,
        "impact": patch.impact,
        "execution": patch.execution,
        "review": patch.review,
        "EXECUTED": False,
    }

    out["governance"] = {
        "PROPOSED_PATCH": True,
        "APPROVAL": False,
        "EXECUTION": False,
        "VERIFICATION": False,
        "states": [
            "PROPOSED",
            "AWAITING REVIEW",
            "APPROVED=false",
            "EXECUTABLE=false (no PassSpec/PatchApproval)",
            "EXECUTED=false",
            "VERIFIED=false",
        ],
        "note": "PROPOSED PATCH ≠ APPROVAL ≠ EXECUTION ≠ VERIFICATION",
    }

    # Pipeline stage map for observatory
    out["pipeline"] = {
        "RECON": {"status": "COMPLETED"},
        "EVIDENCE": {"status": "COMPLETED"},
        "ANALYSIS": {"status": "COMPLETED"},
        "PLAN": {"status": "COMPLETED"},
        "CHANGESET": {"status": cs.status},
        "PATCH": {"status": patch.status},
        "REVIEW": {"status": "AWAITING REVIEW"},
        "APPROVAL": {"status": "NONE"},
        "EXECUTION": {"status": "LOCKED"},
        "VERIFICATION": {"status": "PENDING"},
        "pass_spec": False,
        "patch_approval": False,
    }
    out["status"] = "ANALYSIS_READY"
    return out


def render_verification_matrix(report: dict[str, Any] | None) -> list[dict[str, str]]:
    """Surface 5 helper — never invent PASS from UNKNOWN."""
    if not report:
        return [
            {"claim": "No verification report", "evidence": "missing", "status": "UNKNOWN"},
        ]
    matrix = report.get("proof_matrix") or []
    if matrix:
        return [
            {
                "claim": str(row.get("claim", "")),
                "evidence": str(row.get("evidence", "")),
                "status": str(row.get("status", "UNKNOWN")),
            }
            for row in matrix
        ]
    verdict = (report.get("verdict") or {}).get("status") or "UNKNOWN"
    return [{"claim": "Overall verdict", "evidence": "report", "status": str(verdict)}]


def render_text_observatory(state: ObservatoryState) -> str:
    lines = [
        "=== WEAVER OBSERVATORY ===",
        f"HEAD:    {state.repository.get('head_sha')}",
        f"origin:  {state.repository.get('origin_sha')}",
        f"clean:   {state.repository.get('clean')}",
        f"ahead/behind: {state.repository.get('ahead')}/{state.repository.get('behind')}",
        f"continuation: {state.repository.get('continuation_status')}",
        "",
        "AUTHORITY",
        f"  PassSpec:      {state.authority.get('PassSpec')}",
        f"  PatchApproval: {state.authority.get('PatchApproval')}",
        f"  Execution:     {state.authority.get('Execution')}",
        f"  Mutation:      {state.authority.get('Mutation path')}",
        "",
        "LIFECYCLE",
    ]
    for s in state.lifecycle:
        lines.append(f"  {s['stage']:14} {s['status']}")
    return "\n".join(lines)


def render_text_pipeline(result: dict[str, Any]) -> str:
    """Human-readable multi-surface dump."""
    chunks = [
        "=== OBJECTIVE ===",
        result.get("objective") or "(none)",
        "",
        "=== AUTHORITY ===",
        json.dumps(result.get("authorization"), indent=2),
        "",
        "=== ANALYSIS (facts/inferences/unknowns) ===",
    ]
    an = result.get("analysis") or {}
    for label in ("facts", "inferences", "unknowns"):
        chunks.append(f"-- {label.upper()} --")
        for item in (an.get(label) or [])[:12]:
            if isinstance(item, dict):
                chunks.append(f"  [{item.get('kind')}] {item.get('statement')}")
            else:
                chunks.append(f"  {item}")
    plan = result.get("plan") or {}
    chunks += [
        "",
        "=== ENGINEERING PLAN ===",
        f"plan_id: {plan.get('plan_id')}",
        f"scope:   {plan.get('scope_status')}",
        f"paths:   {plan.get('affected_paths')}",
        f"steps:   {plan.get('implementation_steps')}",
        f"auth:    {plan.get('authorization')}",
        "",
        "=== CHANGESET ===",
    ]
    cs = result.get("changeset") or {}
    for f in (cs.get("files") or [])[:20]:
        chunks.append(
            f"  {f.get('operation')} {f.get('path')} symbols={f.get('symbols_or_regions')} kind={f.get('claim_kinds')}"
        )
    patch = result.get("patch") or {}
    chunks += [
        "",
        "=== PATCH ===",
        f"patch_id: {patch.get('patch_id')}",
        f"status:   {patch.get('status')}",
        f"base:     {patch.get('base_head_sha')}",
        f"EXECUTED: {patch.get('EXECUTED')}",
        f"impact:   {patch.get('impact')}",
        "",
        "=== GOVERNANCE ===",
        json.dumps(result.get("governance"), indent=2),
    ]
    return "\n".join(chunks)
