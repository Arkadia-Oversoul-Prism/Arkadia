"""M02A — CI gate integrity: positive product paths + negative forbidden paths."""
import re
from pathlib import Path

import yaml

from scripts.cp10_mutation_boundary_policy import evaluate_changed_paths

_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _ROOT / ".github/workflows/sg-02-fe-2-v.yml"


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


def test_m02a_is_completed_and_never_re_offered():
    """M02A (ci-gate-integrity) is closed; the router must not re-offer it.

    The router is deterministic and never invents or reorders moves, so once every
    trajectory move is terminal the only truthful outcome is NO legal move.
    The previous `assert move["id"] == "M02A"` was unsatisfiable and hid the real
    contract: M02A's status/spec stay coherent in the trajectory.
    """
    from weaver.engineering_router import ACTIVE_STATUSES, select_next_move

    data = yaml.safe_load(
        (_ROOT / "docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml").read_text()
    )
    m02a = next(m for m in data["moves"] if m["id"] == "M02A")
    assert m02a["status"] == "completed"
    assert m02a["spec"] == "docs/control-plane/moves/M02A-ci-gate-integrity.md"

    move, blockers = select_next_move(data)
    if move is not None:
        assert move["id"] != "M02A"
        assert move["status"] in ACTIVE_STATUSES
    else:
        assert any("no legal pending move" in b for b in blockers)


# ---------------------------------------------------------------------------
# Gate-integrity regression: the CI mutation boundary must accept the product
# the repository actually ships. On main it rejected EDEN-OPS-02 because the
# allowlist omitted `enterprises/` (a seed-data surface), and the workflow's
# diagnostic printed every changed file, masking the single true offender.
# ---------------------------------------------------------------------------
# Exact change set of the EDEN-OPS-02 product work that was wrongly rejected.
_EDEN_OPS_02_CHANGESET = [
    "docs/architecture/EDEN-OPS-02_IMPLEMENTATION.md",
    "enterprises/eden-food-systems/tasks.seed.json",
    "solspire/eden_ops_02.py",
    "solspire/eden_ops_02_routes.py",
    "solspire/enterprise_router.py",
    "tests/test_eden_ops_02.py",
    "web/public_prism/src/components/EdenControlRoom.tsx",
    "web/public_prism/src/pages/EnterpriseConsole.tsx",
]


def _workflow_legit_regex() -> str:
    text = _WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"^\s*legit='([^']+)'", text, re.MULTILINE)
    assert match, "mutation-boundary allowlist (legit=...) not found in workflow"
    return match.group(1)


def test_shipped_product_changeset_passes_policy():
    ok, msg = evaluate_changed_paths(_EDEN_OPS_02_CHANGESET)
    assert ok is True, msg


def test_enterprise_seed_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["enterprises/eden-food-systems/enterprise.json"])
    assert ok is True, msg


def test_personal_vault_surface_is_still_rejected():
    ok, _ = evaluate_changed_paths(["vault/Ideas/x.md"])
    assert ok is False


def test_workflow_allowlist_agrees_with_policy_on_product_surfaces():
    """The workflow's inline copy and the policy script must not drift apart."""
    expr = _workflow_legit_regex()
    for path in _EDEN_OPS_02_CHANGESET:
        policy_ok, _ = evaluate_changed_paths([path])
        workflow_ok = bool(re.match(expr, path))
        assert policy_ok == workflow_ok, f"allowlist drift on {path}"


def test_ci_does_not_assert_retired_private_workspace_marker():
    """The frontend no longer renders that marker, so a gate asserting it can never
    pass. Comment lines that reference the history are fine."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("//", "#"))
    )
    assert "'PRIVATE WORKSPACE'" not in code, "CI still asserts the retired marker"
    assert "Enter the enterprise layer." in code


def test_continue_on_error_gates_are_still_enforced_by_outcome():
    """A `continue-on-error` step reports conclusion=success but outcome=failure.

    The browser gate is continue-on-error, so the only thing that fails CI is the
    later `test "${{ steps.<id>.outcome }}" = success` enforcement. If that line is
    dropped, a broken browser gate silently reports green.

    Steps that only provision or tear down harness infrastructure are intentionally
    unenforced; their failure surfaces downstream (the browser gate cannot pass).
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    steps = workflow["jobs"]["validate"]["steps"]
    enforced = set(re.findall(r"steps\.([A-Za-z0-9_-]+)\.outcome\s*}}'\s*=\s*success", text))

    infra_only = {
        "fb_user",  # provisions the disposable Firebase identity
        "fb_cleanup",  # tears down the disposable Firebase identity
    }

    soft = [s for s in steps if s.get("continue-on-error") is True]
    assert soft, "expected at least one continue-on-error step in the CP10 workflow"

    unenforced = [
        s.get("id") or s.get("name")
        for s in soft
        if s.get("id") and s["id"] not in enforced and s["id"] not in infra_only
    ]
    assert not unenforced, (
        f"continue-on-error verdict steps not enforced by steps.<id>.outcome: {unenforced}"
    )
    assert "browser" in enforced, "the CP10 browser gate must be enforced by outcome"

    enforce_steps = [s for s in steps if str(s.get("name", "")).startswith("Enforce")]
    assert enforce_steps, "expected a terminal 'Enforce ...' gate step"
    for s in enforce_steps:
        assert s.get("continue-on-error") is not True, (
            f"enforcement step '{s.get('name')}' must be able to fail the job"
        )

