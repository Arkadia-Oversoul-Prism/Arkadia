"""M02A — CI gate integrity: positive product paths + negative forbidden paths."""
from scripts.cp10_mutation_boundary_policy import evaluate_changed_paths


def test_legitimate_frontend_mutation_passes():
    ok, _ = evaluate_changed_paths(
        [
            "web/public_prism/src/components/solspire/SolSpireExperience.tsx",
            "web/public_prism/src/pages/ProjectDashboard.tsx",
        ]
    )
    assert ok is True


def test_legitimate_control_plane_mutation_passes():
    ok, _ = evaluate_changed_paths(
        [
            "docs/control-plane/moves/M02A-ci-gate-integrity.md",
            "docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml",
            ".github/workflows/sg-02-fe-2-v.yml",
        ]
    )
    assert ok is True


def test_lab_harness_still_passes():
    ok, _ = evaluate_changed_paths(["lab/council/evaluators.py", "tests/test_phase3_council.py"])
    assert ok is True


def test_unknown_top_level_path_fails():
    ok, msg = evaluate_changed_paths(["secret-backdoor/bin/x"])
    assert ok is False
    assert "legitimate" in msg.lower() or "Unexpected" in msg


def test_v3_dual_shell_forbidden():
    ok, msg = evaluate_changed_paths(
        ["web/public_prism/src/components/solspire/SolSpireExperienceV3.tsx"]
    )
    assert ok is False
    assert "V3" in msg


def test_v2_active_implementation_forbidden():
    ok, msg = evaluate_changed_paths(
        ["web/public_prism/src/components/solspire/SolSpireExperienceV2.tsx"],
        v2_diff_adds_function=True,
    )
    assert ok is False


def test_v2_stub_only_allowed():
    ok, _ = evaluate_changed_paths(
        ["web/public_prism/src/components/solspire/SolSpireExperienceV2.tsx"],
        v2_diff_adds_function=False,
    )
    assert ok is True


def test_trajectory_next_move_is_m02a():
    from weaver.engineering_router import select_next_move
    import yaml
    from pathlib import Path

    data = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml").read_text()
    )
    move, _ = select_next_move(data)
    assert move is not None
    assert move["id"] == "M02A"
