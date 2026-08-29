"""SolSpire ↔ Weaver bridge (W4).

Project context + owner access ≠ Weaver authorization.
Read-only analyze path only. No K15/K3 invocation from this module.
"""
from __future__ import annotations

from typing import Any

from weaver.capabilities import capability_summary
from weaver.operator_validation import run_all_scenarios, run_scenario
from weaver.workbench_view import run_read_only_pipeline


def project_weaver_context(project: dict[str, Any]) -> dict[str, Any]:
    """Non-authoritative context envelope for UI/display."""
    return {
        "project_id": project.get("id"),
        "project_name": project.get("name"),
        "owner": project.get("owner"),
        "status": project.get("status"),
        "authorization": {
            "project_access": "OWNER_VERIFIED_BY_CALLER",
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "Mutation path": "K3 ONLY",
            "note": (
                "Project ownership grants access to this workspace. "
                "It does not authorize repository mutation."
            ),
        },
    }


def project_analyze(
    project: dict[str, Any],
    objective: str,
    *,
    affected_paths: list[str] | None = None,
    symbols: list[str] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    """Run read-only Weaver pipeline inside explicit project context."""
    ctx = project_weaver_context(project)
    pipeline = run_read_only_pipeline(
        objective,
        repo_root=repo_root,
        affected_paths=affected_paths,
        symbols=symbols,
    )
    # Re-assert governance: project context never upgrades authority
    pipeline["authorization"] = {
        **(pipeline.get("authorization") or {}),
        "PassSpec": (pipeline.get("authorization") or {}).get("PassSpec") or "NONE",
        "PatchApproval": "NONE",
        "Execution": "LOCKED",
        "Mutation path": "K3 ONLY",
        "project_access": "OWNER_VERIFIED_BY_CALLER",
        "note": "Project access ≠ PassSpec ≠ PatchApproval ≠ execution.",
    }
    pipeline["executed"] = False
    pipeline["project_context"] = ctx
    return pipeline


def project_capabilities() -> dict[str, Any]:
    return capability_summary()


def project_validation(scenario_id: str | None = None, repo_root: str = ".") -> dict[str, Any]:
    if scenario_id:
        return run_scenario(scenario_id, repo_root=repo_root)
    return run_all_scenarios(repo_root=repo_root)
