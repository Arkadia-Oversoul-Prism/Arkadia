"""SolSpire ↔ Weaver bridge (W4).

Project context + owner access ≠ Weaver authorization.
Read-only analyze path only. No K15/K3 invocation from this module.
"""
from __future__ import annotations

from typing import Any

from weaver.capabilities import capability_summary
from weaver.operator_validation import run_all_scenarios, run_scenario
from weaver.workbench_view import run_read_only_pipeline
from solspire.project_knowledge import build_project_context_for_weaver, build_knowledge_summary


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
    rich = build_project_context_for_weaver(project)
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
    pipeline["project_context"] = {**ctx, **{k: rich.get(k) for k in ("knowledge", "repositories", "memory_note", "embeddings")}}
    return pipeline


def project_capabilities() -> dict[str, Any]:
    return capability_summary()


def project_validation(scenario_id: str | None = None, repo_root: str = ".") -> dict[str, Any]:
    if scenario_id:
        return run_scenario(scenario_id, repo_root=repo_root)
    return run_all_scenarios(repo_root=repo_root)


# --- WEAVER-MVP1 governed execution surface ---

def project_execution_readiness(
    project: dict[str, Any],
    patch: dict[str, Any] | None,
    *,
    pass_spec: dict[str, Any] | None = None,
    approval: dict[str, Any] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    from solspire.project_execution import evaluate_execution_state

    state = evaluate_execution_state(
        patch=patch, pass_spec=pass_spec, approval=approval, repo_root=repo_root
    )
    state["project_id"] = project.get("id")
    return state


def project_bind_pass_spec(
    project: dict[str, Any],
    patch: dict[str, Any],
    *,
    pass_id: str | None = None,
    objective: str | None = None,
    allowed_paths: list[str] | None = None,
    required_tests: list[str] | None = None,
    repo_root: str = ".",
) -> dict[str, Any]:
    from solspire.project_execution import build_pass_spec_for_patch, evaluate_execution_state

    spec = build_pass_spec_for_patch(
        project,
        patch,
        pass_id=pass_id,
        objective=objective,
        allowed_paths=allowed_paths,
        required_tests=required_tests,
        repo_root=repo_root,
    )
    readiness = evaluate_execution_state(patch=patch, pass_spec=spec, approval=None, repo_root=repo_root)
    return {"pass_spec": spec, "readiness": readiness, "execution": "LOCKED"}


def project_bind_patch_approval(
    project: dict[str, Any],
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    *,
    approved: bool = True,
    repo_root: str = ".",
) -> dict[str, Any]:
    from solspire.project_execution import build_patch_approval, evaluate_execution_state

    approval = build_patch_approval(patch, pass_spec, approved=approved)
    readiness = evaluate_execution_state(
        patch=patch, pass_spec=pass_spec, approval=approval, repo_root=repo_root
    )
    return {"patch_approval": approval, "readiness": readiness}


def project_execute_governed(
    project: dict[str, Any],
    patch: dict[str, Any],
    pass_spec: dict[str, Any],
    approval: dict[str, Any],
    *,
    repo_root: str = ".",
    run_k3: bool = False,
) -> dict[str, Any]:
    from solspire.project_execution import execute_project_patch

    return execute_project_patch(
        project, patch, pass_spec, approval, repo_root=repo_root, run_k3=run_k3
    )
