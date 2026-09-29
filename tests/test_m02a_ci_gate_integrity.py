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


# ---------------------------------------------------------------------------
# Regression: root-level narrative docs are shipped product surfaces.
# `AGENTS.md` is the repository's persistent agent memory and is committed by
# ordinary work, but the allowlist only admitted paths with a directory prefix.
# That rejected EL-01..10 (PR #97, merge d48ad0e) and Solariun thread-navigation
# (PR #104, merge a26af40) on `main`, leaving the canonical branch's CP10 gate red.
# ---------------------------------------------------------------------------
_ROOT_DOCS = [
    "AGENTS.md",
    "CURRENT_STATE.md",
    "NEXT_AGENT.md",
    "PARKING_LOT.md",
    "ROADMAP.md",
]

_SOLARIUN_THREAD_NAV_CHANGESET = [
    "AGENTS.md",
    "docs/control-plane/evidence/solariun-thread-calibration/EVIDENCE.md",
    "tests/test_solariun_thread_navigation_01.py",
    "web/public_prism/src/components/solspire/SolSpireExperience.tsx",
    "web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx",
]


def test_root_narrative_docs_are_legitimate():
    ok, msg = evaluate_changed_paths(_ROOT_DOCS)
    assert ok is True, msg


def test_shipped_solariun_thread_nav_changeset_passes_policy():
    """The exact change set that turned main's CP10 gate red."""
    ok, msg = evaluate_changed_paths(_SOLARIUN_THREAD_NAV_CHANGESET)
    assert ok is True, msg


def test_nested_doc_paths_still_resolve_through_their_directory():
    """Root-doc admission must not become a blanket `*.md` bypass."""
    ok, _ = evaluate_changed_paths(["docs/control-plane/WEAVER-RUN-PROTOCOL.md"])
    assert ok is True
    # No directory prefix and not a top-level doc → still an unknown surface.
    ok, msg = evaluate_changed_paths(["secret-backdoor/notes.md"])
    assert ok is False, msg


def test_workflow_allowlist_agrees_with_policy_on_root_docs():
    expr = _workflow_legit_regex()
    corpus = (
        _ROOT_DOCS
        + _SOLARIUN_THREAD_NAV_CHANGESET
        + _OPPORTUNITY_RADAR_CHANGESET
        + ["vault/Ideas/x.md", "secret-backdoor/bin/x"]
    )
    for path in corpus:
        policy_ok, _ = evaluate_changed_paths([path])
        workflow_ok = bool(re.match(expr, path))
        assert policy_ok == workflow_ok, f"allowlist drift on {path}"


# ---------------------------------------------------------------------------
# Regression: `knowledge/`, `spiral_grove/` and root `conftest.py`.
# These are merged, active surfaces (GATE-01 canonical authorship, GATE-05
# Knowledge OS, Spiral Grove SG-03) yet the allowlist only enumerated paths with
# a directory prefix, so committing any of them turned `main` red. The workflow
# is self-contradictory: it *triggers* on `spiral_grove/**` and `lab/**` while
# rejecting `spiral_grove/` in its own allowlist. Pending PR #109 changes
# `knowledge/static_ingestion.py`, which would have failed the same step.
# ---------------------------------------------------------------------------
# Regression: `opportunity_radar/` — the SAPZ capture MVP persisted state.
# PR #110 merged `opportunity_radar/SAPZ_CAPTURE_STATE.md` while the allowlist was
# still incomplete, so the CP10 step failed on that merge (run 36514924096, job
# 109234968163: "Unexpected path outside legitimate repository surfaces" ->
# opportunity_radar/SAPZ_CAPTURE_STATE.md). The gate then went green on the next
# merge without the surface being admitted: it diffs HEAD against HEAD^, and a
# merge commit whose first parent already contains the path reports no change, so
# the offender can never reappear to fail. Masking is not resolution — a future
# `opportunity_radar/` commit under a non-merge parent would redden `main` again.
# ---------------------------------------------------------------------------
_OPPORTUNITY_RADAR_CHANGESET = [
    "opportunity_radar/SAPZ_CAPTURE_STATE.md",
    "web/public_prism/src/pages/OpportunityRadarPage.tsx",
    "web/public_prism/src/data/opportunityRadar.ts",
]


def test_opportunity_radar_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["opportunity_radar/SAPZ_CAPTURE_STATE.md"])
    assert ok is True, msg


def test_shipped_opportunity_radar_changeset_passes_policy():
    """The exact change set that failed main's CP10 gate on the #110 merge."""
    ok, msg = evaluate_changed_paths(_OPPORTUNITY_RADAR_CHANGESET)
    assert ok is True, msg


def test_allowlist_admits_every_tracked_top_level_prefix():
    """A tracked prefix the allowlist omits reddens main on the next real commit."""
    # `vault/` is tracked only as scaffold and is deliberately outside the
    # boundary (see test_personal_vault_surface_is_still_rejected); its full
    # exclusion is asserted there, so it is not an omission this test flags.
    prefixes = {
        p.split("/", 1)[0]
        for p in _tracked_paths()
        if "/" in p and not p.startswith("vault/")
    }
    rejected = sorted(
        prefix for prefix in prefixes if not evaluate_changed_paths([prefix + "/probe"])[0]
    )
    assert not rejected, (
        "allowlist omits tracked top-level prefixes, so a non-merge commit "
        "touching them fails CP10: " + ", ".join(rejected)
    )


# ---------------------------------------------------------------------------
_OMITTED_SURFACE_CHANGESET = [
    "knowledge/static_ingestion.py",
    "knowledge/vault.py",
    "spiral_grove/learning_path.py",
    "conftest.py",
]


def test_omitted_merged_surfaces_are_legitimate():
    ok, msg = evaluate_changed_paths(_OMITTED_SURFACE_CHANGESET)
    assert ok is True, msg


def test_knowledge_os_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["knowledge/context_engine.py"])
    assert ok is True, msg


def test_spiral_grove_surface_is_legitimate():
    """The workflow triggers on spiral_grove/** so its allowlist must admit it."""
    ok, msg = evaluate_changed_paths(["spiral_grove/__init__.py"])
    assert ok is True, msg


def test_root_conftest_is_legitimate():
    ok, msg = evaluate_changed_paths(["conftest.py"])
    assert ok is True, msg


def test_content_surface_admission_is_not_overbroad():
    """Admitting those surfaces must not weaken the boundary elsewhere."""
    # Directory-prefix lookalikes are not content surfaces.
    for path in [
        "knowledge_evil/x.py",
        "spiral_grove_evil/x.py",
        "conftest_evil.py",
        ".knowledge/x.py",
    ]:
        ok, msg = evaluate_changed_paths([path])
        assert ok is False, f"{path} should still be rejected ({msg})"
    # Personal vault and unknown roots remain rejected.
    for path in ["vault/Ideas/x.md", "secret-backdoor/bin/x"]:
        ok, _ = evaluate_changed_paths([path])
        assert ok is False
    # A nested `conftest.py` is not covered by the root-level literal.
    ok, _ = evaluate_changed_paths(["somewhere/conftest.py"])
    assert ok is False


def test_workflow_allowlist_agrees_with_policy_on_omitted_surfaces():
    expr = _workflow_legit_regex()
    corpus = _OMITTED_SURFACE_CHANGESET + [
        "knowledge_evil/x.py",
        "spiral_grove_evil/x.py",
        "conftest_evil.py",
        ".knowledge/x.py",
        "somewhere/conftest.py",
    ]
    for path in corpus:
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



# ---------------------------------------------------------------------------
# Completeness: the allowlist must be an inventory of what the repository
# *actually* tracks — not a hand-picked subset. The defect above recurred three
# times (EDEN-OPS-02, EL-01..10 #97, Solariun #104) because each fix patched the
# current symptom instead of asserting the invariant. These tests close the bug
# class: every tracked path must be admitted, and the workflow mirror must agree.
# ---------------------------------------------------------------------------
def _tracked_paths() -> list[str]:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=_ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - no git
        import pytest

        pytest.skip("git unavailable to enumerate the tracked inventory")
    return [line for line in out.splitlines() if line.strip()]


def test_allowlist_covers_every_tracked_surface():
    """The gate runs on main; a tracked surface the allowlist omits turns it red."""
    rejected = []
    for path in _tracked_paths():
        ok, msg = evaluate_changed_paths([path])
        if not ok:
            rejected.append(f"{path}: {msg}")
    assert not rejected, (
        "the allowlist omits surfaces this repository tracks, so the next merge "
        "that touches them reddens the CP10 gate:\n" + "\n".join(rejected[:20])
    )


def test_workflow_allowlist_agrees_with_policy_on_every_tracked_surface():
    """The inline workflow mirror and the policy script must admit identically."""
    expr = _workflow_legit_regex()
    drift = [
        path
        for path in _tracked_paths()
        if evaluate_changed_paths([path])[0] != bool(re.match(expr, path))
    ]
    assert not drift, f"workflow/policy allowlist drift on tracked paths: {drift[:20]}"


def test_vault_scaffold_is_admitted_but_generated_notes_are_not():
    """vault/ is the private Knowledge OS runtime output; only its scaffold is tracked."""
    for path in [
        "vault/Index/README.md",
        "vault/Templates/conversation-template.md",
        "vault/Ideas/.gitkeep",
    ]:
        ok, msg = evaluate_changed_paths([path])
        assert ok is True, msg
    ok, msg = evaluate_changed_paths(["vault/Ideas/2026-01-01.md"])
    assert ok is False, "a generated vault note must stay outside the boundary"
    assert "vault" in msg.lower(), "the rejection must name the vault boundary"


def test_allowlist_rejects_unknown_lookalike_roots():
    """Admitting more real surfaces must not admit lookalikes of them."""
    for path in [
        "knowledge_evil/x.py",
        "spiral_grove_evil/x.py",
        "conftest_evil.py",
        ".knowledge/x.py",
        "somewhere/conftest.py",
        "EVIL/x.md",
        "terraform/main.tf",
        "deploy.sh",
    ]:
        ok, msg = evaluate_changed_paths([path])
        assert ok is False, f"{path} should be rejected ({msg})"


def test_workflow_still_forbids_constitutional_dual_shell():
    """Breadth in the admit-list must not have softened the `forbid` stage."""
    forbid = re.search(r"^\s*forbid='([^']+)'", _WORKFLOW.read_text(encoding="utf-8"), re.MULTILINE)
    assert forbid, "the V2/V3 forbid stage must still exist in the workflow"
    expr = forbid.group(1)
    assert re.search(expr, "web/public_prism/src/components/solspire/SolSpireExperienceV3.tsx"), (
        "the constitutional V3 dual shell must still be forbidden"
    )
    assert re.search(expr, "web/public_prism/src/components/solspire/SolSpireExperienceV2.tsx")

