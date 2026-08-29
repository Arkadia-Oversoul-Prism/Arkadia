"""WEAVER-W4 — Explicit operator validation scenarios (read-only)."""
from __future__ import annotations

from typing import Any

from .workbench_view import run_read_only_pipeline


SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "repo_understanding",
        "title": "Repository understanding",
        "objective": "Map the Weaver transaction architecture.",
        "affected_paths": [],
        "expect": {"execution": "LOCKED", "min_facts": 1},
    },
    {
        "id": "scoped_investigation",
        "title": "Scoped investigation",
        "objective": "Investigate the K15 execution path.",
        "affected_paths": [
            "weaver/execution.py",
            "weaver/transaction.py",
            "weaver/session_kernel.py",
        ],
        "expect": {"execution": "LOCKED", "scope_not": "UNSCOPED"},
    },
    {
        "id": "plan_generation",
        "title": "Plan generation",
        "objective": "Improve observability around transaction stages.",
        "affected_paths": ["weaver/transaction.py", "weaver/execution.py"],
        "expect": {"execution": "LOCKED", "has_plan": True},
    },
    {
        "id": "patch_review",
        "title": "Patch review",
        "objective": "Review a narrow documentation improvement for workbench_view.",
        "affected_paths": ["weaver/workbench_view.py"],
        "expect": {"execution": "LOCKED", "executed": False},
    },
    {
        "id": "governance_boundary",
        "title": "Governance boundary",
        "objective": "Attempt to imply execution without approval.",
        "affected_paths": ["weaver/execution.py"],
        "expect": {"execution": "LOCKED", "executed": False, "approval": False},
    },
]


def run_scenario(scenario_id: str, repo_root: str = ".") -> dict[str, Any]:
    sc = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not sc:
        return {"ok": False, "error": f"unknown scenario: {scenario_id}"}
    result = run_read_only_pipeline(
        sc["objective"],
        repo_root=repo_root,
        affected_paths=sc.get("affected_paths") or None,
    )
    expect = sc.get("expect") or {}
    checks: list[dict[str, Any]] = []
    auth = result.get("authorization") or {}
    scope = result.get("scope") or {}
    if "execution" in expect:
        ok = auth.get("Execution") == expect["execution"]
        checks.append({"check": "execution", "ok": ok, "actual": auth.get("Execution")})
    if expect.get("scope_not"):
        ok = scope.get("status") != expect["scope_not"]
        checks.append({"check": "scope_not_unscoped", "ok": ok, "actual": scope.get("status")})
    if expect.get("has_plan"):
        ok = bool((result.get("plan") or {}).get("plan_id"))
        checks.append({"check": "has_plan", "ok": ok})
    if "executed" in expect:
        ok = result.get("executed") is expect["executed"]
        checks.append({"check": "executed", "ok": ok, "actual": result.get("executed")})
    if "approval" in expect:
        ok = (result.get("governance") or {}).get("APPROVAL") is expect["approval"]
        checks.append({"check": "approval", "ok": ok})
    if "min_facts" in expect:
        n = len((result.get("analysis") or {}).get("facts") or [])
        checks.append({"check": "min_facts", "ok": n >= int(expect["min_facts"]), "actual": n})
    return {
        "ok": all(c["ok"] for c in checks) if checks else True,
        "scenario": sc["id"],
        "title": sc["title"],
        "checks": checks,
        "scope": scope,
        "authorization": auth,
        "executed": result.get("executed"),
        "plan_id": (result.get("plan") or {}).get("plan_id"),
        "note": "Validation is read-only. PASS on checks ≠ repository mutation.",
    }


def run_all_scenarios(repo_root: str = ".") -> dict[str, Any]:
    results = [run_scenario(s["id"], repo_root=repo_root) for s in SCENARIOS]
    return {
        "ok": all(r["ok"] for r in results),
        "count": len(results),
        "results": results,
        "mutation": False,
        "authority": "NONE",
    }
