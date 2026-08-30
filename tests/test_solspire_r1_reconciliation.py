"""R1 — SolSpire project-execution reconciliation invariants."""
from __future__ import annotations

import inspect
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_patch(repo_root: str) -> dict:
    from weaver.pass_spec import current_head, current_origin_main

    return {
        "patch_id": "r1-patch",
        "plan_id": "r1-plan",
        "plan_content_hash": "r1-plan-hash",
        "base_head_sha": current_head(repo_root),
        "base_origin_sha": current_origin_main(repo_root),
        "status": "VALID",
        "files": [
            {
                "path": "weaver/pass_spec.py",
                "operation": "MODIFY",
                "patch_text": "--- a/weaver/pass_spec.py\n+++ b/weaver/pass_spec.py\n@@\n+# R1 fixture\n",
            }
        ],
        "review": {"objective": "R1 reconciliation fixture"},
        "tests": {},
    }


def test_r1_canonical_builders_match_solspire_wrappers():
    from solspire.project_execution import (
        build_pass_spec_for_patch as solspire_build_spec,
        build_patch_approval as solspire_build_approval,
    )
    from weaver.project_execution import (
        build_pass_spec_for_patch as weaver_build_spec,
        build_patch_approval as weaver_build_approval,
    )

    patch = _sample_patch(str(REPO_ROOT))
    project = {"id": "r1-project", "name": "R1 project"}

    sol_spec = solspire_build_spec(project, patch, repo_root=str(REPO_ROOT))
    canonical_spec = weaver_build_spec(patch, repo_root=str(REPO_ROOT))

    for key in ("pass_id", "objective", "base_sha", "allowed_paths", "required_tests", "pass_spec_hash"):
        assert sol_spec[key] == canonical_spec[key]
    assert sol_spec["bound_patch_hash"] == canonical_spec["bound_patch_hash"]
    assert sol_spec["project_id"] == "r1-project"

    sol_approval = solspire_build_approval(patch, sol_spec, approved=True)
    canonical_approval = weaver_build_approval(patch, canonical_spec, approved=True)
    assert sol_approval == canonical_approval


def test_r1_readiness_wrapper_delegates_to_weaver():
    import solspire.project_execution as solspire_execution
    import weaver.project_execution as weaver_execution

    source = inspect.getsource(solspire_execution)
    assert "PassSpec(" not in source
    assert "PatchApproval(" not in source
    assert "path_in_allowlist" not in source
    assert "current_head(" not in source
    assert "current_origin_main(" not in source
    assert "weaver.project_execution" in source
    assert inspect.getsource(weaver_execution.evaluate_execution_state).find("path_in_allowlist") >= 0


def test_r1_existing_execution_seam_remains_canonical():
    import solspire.project_execution as solspire_execution

    source = inspect.getsource(solspire_execution)
    assert "from weaver.execution import" in source
    assert "execute_patch" in source
    assert "run_transaction" not in source
