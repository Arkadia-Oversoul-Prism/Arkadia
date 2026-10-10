"""M02A — CI gate integrity: positive product paths + negative forbidden paths."""
import re
from pathlib import Path

import yaml

from scripts.cp10_mutation_boundary_policy import evaluate_changed_paths, resolve_range_endpoint

_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _ROOT / ".github/workflows/sg-02-fe-2-v.yml"

# Matches the enforcement form `test "${{ steps.<id>.outcome }}" = success`.
_ENFORCED_BY_OUTCOME = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outcome\s*}}'\s*=\s*success")
# The self-satisfying form the enforcement step must never use: a
# `continue-on-error` step's conclusion is always `success`, so an assertion
# built on it can never fail.
_ENFORCED_BY_CONCLUSION = re.compile(r"steps\.([A-Za-z0-9_-]+)\.conclusion\s*}}'\s*=\s*success")


def enforced_by_outcome(text: str) -> set:
    """Step ids asserted through `steps.<id>.outcome`."""
    return set(_ENFORCED_BY_OUTCOME.findall(text))


def enforced_by_conclusion(text: str) -> set:
    """Step ids asserted through `steps.<id>.conclusion` (self-satisfying)."""
    return set(_ENFORCED_BY_CONCLUSION.findall(text))


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


def _mutation_step_code() -> str:
    """The CP10 mutation step's shell with comment lines stripped."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("//", "#"))
    )


def _run_judge(feed: str) -> tuple[int, str]:
    """Run the policy CLI the workflow runs, over `feed` on stdin."""
    import contextlib
    import io

    from scripts.cp10_mutation_boundary_policy import main

    buf = io.StringIO()
    import sys

    real_stdin = sys.stdin
    sys.stdin = io.StringIO(feed)
    try:
        with contextlib.redirect_stdout(buf):
            rc = main(["--judge"])
    finally:
        sys.stdin = real_stdin
    return rc, buf.getvalue()


def test_mutation_boundary_delegates_the_allowlist_decision():
    """The gate must decide through the tested module, not a regex beside it.

    The workflow and the policy each carried a hand-maintained allowlist, and they
    drifted: a surface admitted in the module was absent from the shell copy. The
    gate then judged the shell's copy while the fitness tests proved the module's —
    the proof and the executed decision could disagree.
    """
    code = _mutation_step_code()
    assert "cp10_mutation_boundary_policy.py --judge" in code, (
        "the CP10 step must delegate the allowlist verdict to the tested module"
    )
    assert "printf '%s\\n' \"$changed\"" in code, (
        "the changed range must be the input to the delegated verdict"
    )


def test_workflow_carries_no_second_allowlist_copy():
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert not re.search(r"^\s*legit='", text, re.MULTILINE), (
        "the hand-maintained `legit=` regex is the drift defect; the policy module "
        "is the single source of the boundary decision"
    )
    assert "offenders" not in _mutation_step_code(), (
        "offender reporting must come from the policy module's verdict"
    )


def test_judge_cli_decision_matches_the_module_the_tests_import():
    """The CLI the workflow runs must render the same verdict as the public API."""
    for corpus, expected in (
        (_EDEN_OPS_02_CHANGESET, True),
        (_SOLARIUN_THREAD_NAV_CHANGESET, True),
        (["vault/Ideas/x.md"], False),
        (["secret-backdoor/bin/x"], False),
    ):
        policy_ok, _ = evaluate_changed_paths(corpus)
        assert policy_ok is expected
        rc, out = _run_judge("\n".join(corpus))
        assert (rc == 0) is expected, out
        if not expected:
            assert "Unexpected path outside legitimate repository surfaces" in out


def test_judge_cli_passes_an_empty_change_set():
    rc, out = _run_judge("")
    assert rc == 0, out


# ---------------------------------------------------------------------------
# Regression: root-level narrative docs are shipped product surfaces.


def test_shipped_product_changeset_passes_policy():
    ok, msg = evaluate_changed_paths(_EDEN_OPS_02_CHANGESET)
    assert ok is True, msg


def test_enterprise_seed_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["enterprises/eden-food-systems/enterprise.json"])
    assert ok is True, msg


def test_personal_vault_surface_is_still_rejected():
    ok, _ = evaluate_changed_paths(["vault/Ideas/x.md"])
    assert ok is False


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


def test_workflow_delegation_admits_root_docs_and_still_rejects_unknown_roots():
    corpus = (
        _ROOT_DOCS
        + _SOLARIUN_THREAD_NAV_CHANGESET
        + _OPPORTUNITY_RADAR_CHANGESET
    )
    rc, out = _run_judge("\n".join(corpus))
    assert rc == 0, out
    for rejected in ("vault/Ideas/x.md", "secret-backdoor/bin/x"):
        rc, out = _run_judge(rejected)
        assert rc != 0, f"{rejected} must stay outside the boundary"


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
# merge without the surface being admitted: it diffed HEAD against HEAD^, and a
# merge commit whose first parent already contains the path reports no change, so
# the offender could never reappear to fail. Masking is not resolution — a future
# `opportunity_radar/` commit under a non-merge parent would redden `main` again.
# The range itself is now judged correctly (base..HEAD, see resolve_range_endpoint),
# so the surface must stay enumerated rather than relying on that masking.
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


# ---------------------------------------------------------------------------
# Regression: `reconciliation/` — the upstream causal-continuity forensic record.
# PR #180 merged `reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md` while the
# allowlist was still incomplete, so the surface was rejected by the very gate that
# judged the merge. The completeness invariant above caught it on main: the tracked
# path is the only one of 1579 the module rejects, and three fitness tests were red
# (`test_allowlist_admits_every_tracked_top_level_prefix`,
# `test_allowlist_covers_every_tracked_surface`,
# `test_delegated_verdict_admits_every_tracked_surface`). A later non-merge commit
# touching `reconciliation/` would redden the CP10 gate on main for the same reason,
# so the surface is enumerated rather than left to be inherited by masking.
# ---------------------------------------------------------------------------
_RECONCILIATION_CHANGESET = [
    "reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md",
]


def test_reconciliation_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md"])
    assert ok is True, msg


def test_shipped_reconciliation_changeset_passes_policy():
    """The exact change set that left the CP10 fitness tests red on the #180 merge."""
    ok, msg = evaluate_changed_paths(_RECONCILIATION_CHANGESET)
    assert ok is True, msg


# ---------------------------------------------------------------------------
# Regression: `economic_seams/` — the provider-neutral economic seam engine.
# Merged to main while the allowlist omitted the tree, so the CP10 gate rejected
# the merge that introduced it: commit 39cd05e touches only
# `economic_seams/correlation.py` and is judged FAIL by the policy CLI the
# workflow runs. The completeness invariant above caught it on main (three
# fitness tests red); a later non-merge commit touching the tree reddens the gate
# for the same reason, so the surface is enumerated rather than left to be
# inherited by masking.
# ---------------------------------------------------------------------------
_ECONOMIC_SEAMS_CHANGESET = [
    "economic_seams/__init__.py",
    "economic_seams/correlation.py",
    "economic_seams/engine.py",
    "economic_seams/market_data.py",
    "economic_seams/nocopo.py",
]


def test_economic_seams_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["economic_seams/correlation.py"])
    assert ok is True, msg


def test_shipped_economic_seams_changeset_passes_policy():
    """The exact change set that reddened the CP10 gate on the 39cd05e commit."""
    ok, msg = evaluate_changed_paths(_ECONOMIC_SEAMS_CHANGESET)
    assert ok is True, msg


# ---------------------------------------------------------------------------
# Regression: `musical-intention-engine/` — the MIE control-plane corpus
# (constitution, field recon, interaction canvas, musical-object spec, prototype
# loop, decisions, experiments, research) that issue #209's MVP build reads from.
# Same omission class as `economic_seams/`: tracked, omitted, three fitness tests
# red on main.
# ---------------------------------------------------------------------------
_MUSICAL_INTENTION_ENGINE_CHANGESET = [
    "musical-intention-engine/00-CONSTITUTION.md",
    "musical-intention-engine/03-MUSICAL-OBJECT-SPEC.md",
    "musical-intention-engine/OPENHANDS-MVP-01.md",
    "musical-intention-engine/06-EXPERIMENTS/EXP-001.md",
]


def test_musical_intention_engine_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["musical-intention-engine/00-CONSTITUTION.md"])
    assert ok is True, msg


def test_shipped_musical_intention_engine_changeset_passes_policy():
    """The corpus surface issue #209's bounded build commits against."""
    ok, msg = evaluate_changed_paths(_MUSICAL_INTENTION_ENGINE_CHANGESET)
    assert ok is True, msg


# ---------------------------------------------------------------------------
# Regression: `research/` — the Oversoul Prism control-plane research corpus
# (lattice reconstruction, node transformation, convergence, conflict,
# verification, resolution, acceptance), merged via PRs #277-#288; and
# `schemas/` — the versioned public wire contracts, merged via PR #286
# ("ARCH-01: define Arkana Signal Fabric v1"). Same omission class as
# `economic_seams/` and `musical-intention-engine/`: tracked on main, omitted
# from the allowlist, so three fitness tests were red and the CP10 gate would
# reject the next ordinary commit touching either tree. Measured at ebe09a6:
# 15 offenders under `research/` plus 1 under `schemas/`.
# ---------------------------------------------------------------------------
_RESEARCH_AND_SCHEMAS_CHANGESET = [
    "research/oversoul_prism_3x3/validate.py",
    "research/oversoul_prism_verification/probe.py",
    "research/oversoul_prism_acceptance/README.md",
    "schemas/arkana/signal/1.0/arkana-signal.schema.json",
]


def test_research_corpus_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["research/oversoul_prism_3x3/validate.py"])
    assert ok is True, msg


def test_schemas_contract_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(
        ["schemas/arkana/signal/1.0/arkana-signal.schema.json"]
    )
    assert ok is True, msg


def test_shipped_research_and_schemas_changeset_passes_policy():
    """The exact change set the CP10 gate rejected on main at ebe09a6."""
    ok, msg = evaluate_changed_paths(_RESEARCH_AND_SCHEMAS_CHANGESET)
    assert ok is True, msg


def test_research_and_schemas_admission_is_not_overbroad():
    """Admitting those trees must not weaken the boundary elsewhere.

    Negative control: admitting `research/` and `schemas/` must not admit their
    prefix lookalikes, nor any unknown root.
    """
    for path in (
        "research_evil/x.py",
        "schemas_evil/x.json",
        "research2/x.py",
        "schema/x.json",
        "researches/x.py",
    ):
        ok, msg = evaluate_changed_paths([path])
        assert ok is False, f"{path} should be rejected ({msg})"


def test_delegated_verdict_admits_research_and_schemas_and_rejects_lookalikes():
    """The CLI the workflow executes must agree with the imported API."""
    rc, out = _run_judge("\n".join(_RESEARCH_AND_SCHEMAS_CHANGESET))
    assert rc == 0, out
    for path in ("research_evil/x.py", "schemas_evil/x.json", "schema/x.json"):
        rc, out = _run_judge(path)
        assert rc != 0, f"{path} must stay outside the boundary"



# ---------------------------------------------------------------------------
# Regression: `google_workspace/` — the Weaver Google Workspace Attention Bus
# Apps Script surface introduced by PR #311.
# ---------------------------------------------------------------------------
_GOOGLE_WORKSPACE_CHANGESET = [
    "google_workspace/Code.gs",
    "google_workspace/appsscript.json",
]


def test_google_workspace_surface_is_legitimate():
    ok, msg = evaluate_changed_paths(["google_workspace/appsscript.json"])
    assert ok is True, msg


def test_shipped_google_workspace_changeset_passes_policy():
    """The exact two-path change set PR #311 adds under `google_workspace/`."""
    ok, msg = evaluate_changed_paths(_GOOGLE_WORKSPACE_CHANGESET)
    assert ok is True, msg


def test_google_workspace_admission_is_not_overbroad():
    """Admitting the tree must not admit its prefix lookalikes or unknown roots."""
    for path in (
        "google_workspace_evil/x.gs",
        "google_workspace2/x.json",
        "googleworkspace/x.gs",
        "google_workspaces/x.json",
    ):
        ok, msg = evaluate_changed_paths([path])
        assert ok is False, f"{path} should be rejected ({msg})"


def test_delegated_verdict_admits_google_workspace_and_rejects_lookalikes():
    """The CLI the workflow executes must agree with the imported API."""
    rc, out = _run_judge("\n".join(_GOOGLE_WORKSPACE_CHANGESET))
    assert rc == 0, out
    for path in ("google_workspace_evil/x.gs", "google_workspace2/x.json"):
        rc, out = _run_judge(path)
        assert rc != 0, f"{path} must stay outside the boundary"


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
        "reconciliation_evil/x.md",
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


def test_delegated_verdict_admits_omitted_surfaces_and_rejects_lookalikes():
    corpus = _OMITTED_SURFACE_CHANGESET + [
        "knowledge/static_ingestion.py",
        "spiral_grove/learning_path.py",
        "reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md",
    ]
    rc, out = _run_judge("\n".join(corpus))
    assert rc == 0, out
    # Prefix lookalikes and nested conftest.py are not admitted by the module.
    for path in (
        "knowledge_evil/x.py",
        "spiral_grove_evil/x.py",
        "conftest_evil.py",
        ".knowledge/x.py",
        "somewhere/conftest.py",
        "reconciliation_evil/x.md",
    ):
        rc, out = _run_judge(path)
        assert rc != 0, f"{path} must stay outside the boundary"


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
    enforced = enforced_by_outcome(text)

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


def test_enforcement_never_reads_step_conclusion():
    """The enforcement step must read `.outcome`, never `.conclusion`.

    `continue-on-error: true` separates the two: `conclusion` is `success` for
    every soft step whatever happened, `outcome` is the real result. An
    assertion built on `.conclusion` collapses to the constant
    `test 'success' = success` and cannot fail, so the gate it claims to be is
    decorative. Measured evidence that the live form works (it is substituted,
    not constant): at `main` `f9ced6b6` (run `37954341298`) and on PR #354's
    head `ebb4077b` (run `37967556608`) the enforcement step runs 16
    assertions; 15 print `test 'success' = success` and one -- the 15th --
    prints `test 'failure' = success`, the real `outcome` of the soft `browser`
    step, and the step exits 1.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    offenders = enforced_by_conclusion(text)
    assert not offenders, (
        "the CP10 enforcement step asserts steps.<id>.conclusion, which is "
        f"always 'success' for a continue-on-error step: {sorted(offenders)}"
    )


def test_outcome_detector_is_not_blind():
    """Negative control: the detector must flag the `.conclusion` form.

    Without this, `test_enforcement_never_reads_step_conclusion` could pass
    because the regex matches nothing, not because the workflow is correct.
    """
    vulnerable = (
        "test '${{ steps.browser.conclusion }}' = success\n"
        "test '${{ steps.backend.conclusion }}' = success\n"
    )
    assert enforced_by_conclusion(vulnerable) == {"browser", "backend"}
    assert enforced_by_outcome(vulnerable) == set()


def test_outcome_detector_matches_the_live_form():
    """Positive control: the live `.outcome` form must be matched."""
    correct = "test '${{ steps.browser.outcome }}' = success\n"
    assert enforced_by_outcome(correct) == {"browser"}
    assert enforced_by_conclusion(correct) == set()


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


def test_delegated_verdict_admits_every_tracked_surface():
    """The gate runs on main; a tracked surface the module omits turns it red.

    This is the same invariant as test_allowlist_covers_every_tracked_surface, but
    through the CLI the workflow actually executes rather than the imported API, so
    the delegated decision cannot diverge from the proven one.
    """
    rejected = []
    for path in _tracked_paths():
        rc, out = _run_judge(path)
        if rc != 0:
            rejected.append(f"{path}: {out.strip()}")
    assert not rejected, (
        "the delegated boundary omits surfaces this repository tracks, so the next "
        "merge that touches them reddens the CP10 gate:\n" + "\n".join(rejected[:20])
    )


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
        # lookalikes of the surfaces admitted by this change
        "economic_seams_evil/x.py",
        "musical-intention-engine_evil/x.md",
        "musical_intention_engine/x.md",
        "research_evil/x.py",
        "schemas_evil/x.json",
        "schema/x.json",
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


# ---------------------------------------------------------------------------
# Range evaluation: the boundary must judge the whole guarded change set.
# Diffing `HEAD^ HEAD` inspects only the tip commit, so a multi-commit PR's
# earlier commits are never judged — an offender added in the first commit and
# followed by any unrelated commit reports no change and can never fail
# (masking, not resolution; PR #110 -> opportunity_radar/SAPZ_CAPTURE_STATE.md).
# The range endpoint is now chosen by the tested policy module and the workflow
# diffs `base..HEAD`.
# ---------------------------------------------------------------------------
def test_range_endpoint_uses_pull_request_base():
    base, reason = resolve_range_endpoint({"pull_request": {"base": {"sha": "b" * 40}}})
    assert base == "b" * 40
    assert "pull_request" in reason


def test_range_endpoint_prefers_pull_request_over_push_before():
    """A PR event carries no usable `before`; the base SHA is the true range."""
    base, _ = resolve_range_endpoint(
        {"pull_request": {"base": {"sha": "b" * 40}}, "before": "c" * 40}
    )
    assert base == "b" * 40


def test_range_endpoint_uses_push_before():
    base, reason = resolve_range_endpoint({"before": "a" * 40})
    assert base == "a" * 40
    assert "push" in reason


def test_range_endpoint_rejects_all_zero_push_before():
    """A branch-creation push reports an all-zero `before`; HEAD^ is the fallback."""
    base, reason = resolve_range_endpoint({"before": "0" * 40}, ref_exists=True)
    assert base == "HEAD^"
    assert "fallback" in reason


def test_range_endpoint_falls_back_to_head_parent():
    base, _ = resolve_range_endpoint({}, ref_exists=True)
    assert base == "HEAD^"


def test_range_endpoint_is_undeterminable_without_parent():
    """No event range and no parent must NOT silently pass — the caller fails."""
    base, reason = resolve_range_endpoint({}, ref_exists=False)
    assert base is None
    assert "cannot determine" in reason


def test_single_tip_diff_masks_a_multi_commit_pr_offender():
    """The masking defect, reproduced with real git objects.

    A PR run executes on the head commit, so `HEAD^ HEAD` inspects only the PR's
    *last* commit. A path admitted nowhere — added in an earlier PR commit — shows
    no change there and can never fail, however many commits follow it. That is
    exactly how PR #110 would have landed `opportunity_radar/SAPZ_CAPTURE_STATE.md`
    on an allowlist that rejected it. The range base..HEAD sees the offender.
    """
    import os
    import subprocess
    import tempfile

    offender = "opportunity_radar/SAPZ_CAPTURE_STATE.md"
    with tempfile.TemporaryDirectory() as tmp:
        def git(*args: str) -> str:
            return subprocess.run(
                ["git", *args], cwd=tmp, capture_output=True, text=True, check=True,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "GIT_AUTHOR_NAME": "cp10",
                    "GIT_AUTHOR_EMAIL": "cp10@example.invalid",
                    "GIT_COMMITTER_NAME": "cp10",
                    "GIT_COMMITTER_EMAIL": "cp10@example.invalid",
                },
            ).stdout

        git("init", "-q", "-b", "main")
        with open(os.path.join(tmp, "base.txt"), "w", encoding="utf-8") as fh:
            fh.write("base\n")
        git("add", "-A")
        git("commit", "-qm", "base commit")
        base = git("rev-parse", "HEAD").strip()

        git("checkout", "-qb", "pr")
        os.makedirs(os.path.join(tmp, "opportunity_radar"))
        with open(os.path.join(tmp, offender), "w", encoding="utf-8") as fh:
            fh.write("offender\n")
        git("add", "-A")
        git("commit", "-qm", "PR commit 1: adds a surface admitted nowhere")
        with open(os.path.join(tmp, "followup.txt"), "w", encoding="utf-8") as fh:
            fh.write("follow-up\n")
        git("add", "-A")
        git("commit", "-qm", "PR commit 2: unrelated change")

        tip_only = [
            p for p in git("diff", "--name-only", "HEAD^", "HEAD").splitlines() if p.strip()
        ]
        full_range = [
            p for p in git("diff", "--name-only", base, "HEAD").splitlines() if p.strip()
        ]
        assert offender not in tip_only, "the single-tip range is expected to mask the offender"
        assert offender in full_range, "base..HEAD must expose the offender"

        # And the gate's own policy rejects it, so exposure is not cosmetic.
        ok, msg = evaluate_changed_paths(full_range)
        assert ok is False, f"the exposed offender must be rejected ({msg})"


def test_workflow_diffs_the_resolved_range_not_head_parent():
    """The workflow must diff the resolved base, and must fail closed if it cannot."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("//", "#"))
    )
    assert 'changed="$(git diff --name-only "$base" HEAD)"' in code, (
        "the mutation boundary must diff the resolved range base..HEAD"
    )
    assert 'changed="$(git diff --name-only HEAD^ HEAD)"' not in code, (
        "the boundary must not diff only the tip commit's first parent"
    )
    # Fail closed when no range can be determined.
    assert "Mutation boundary FAIL" in code
    # The range endpoint comes from the tested policy module, not a hand-rolled copy.
    assert "cp10_mutation_boundary_policy.py --resolve-range" in code


def test_workflow_forbid_diffs_use_the_resolved_range():
    text = _WORKFLOW.read_text(encoding="utf-8")
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("//", "#"))
    )
    assert 'git diff "$base" HEAD --' in code
    assert "git diff HEAD^ HEAD --" not in code, (
        "the V2/V3 and workflow-automation forbid diffs must use the guarded range"
    )


def test_checkout_fetches_the_full_history_for_range_resolution():
    """depth=1 only reaches HEAD^; the resolved base can be arbitrarily far back."""
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["fetch-depth"] == 0, (
        "a shallow checkout cannot resolve pull_request.base.sha, so the boundary "
        "would fail closed on every PR instead of judging the range"
    )




# ---------------------------------------------------------------------------
# Trigger coverage: the boundary's own contract surfaces must invoke the boundary.
# The `mutation` step is unconditional, so a path absent from the trigger filter is
# a path never judged — a PR that rewrites
# `scripts/cp10_mutation_boundary_policy.py` or its fitness tests previously
# produced no CP10 check-run at all.
# ---------------------------------------------------------------------------
_BOUNDARY_CONTRACT_SURFACES = [
    "scripts/cp10_mutation_boundary_policy.py",
    "tests/test_m02a_ci_gate_integrity.py",
]


def _workflow_triggers() -> dict:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    return workflow[True] if True in workflow else workflow["on"]


def test_boundary_contract_surfaces_trigger_the_boundary():
    triggers = _workflow_triggers()
    for trigger in ("push", "pull_request"):
        paths = triggers[trigger]["paths"]
        for surface in _BOUNDARY_CONTRACT_SURFACES:
            assert surface in paths, (
                f"{trigger} must run CP10 when {surface} changes; otherwise the "
                "boundary can be rewritten without being judged"
            )


def test_push_and_pull_request_filters_are_identical():
    """Both filters must name the same surfaces.

    The asymmetry is a masking hole, not a convenience: a surface the gate judges on
    push but not on pull_request lets a PR introduce it unjudged, and CP10 then goes
    red on main at the merge. That is exactly how PR #112 landed
    tests/test_phase5_governed_execution.py against an already-red gate. Keeping the
    two lists identical means a widening of one is always a widening of both.
    """
    triggers = _workflow_triggers()
    push = set(triggers["push"]["paths"])
    pull = set(triggers["pull_request"]["paths"])
    assert push == pull, (
        "push and pull_request trigger filters diverge; surfaces present in only "
        f"one: {sorted(push ^ pull)}"
    )


def test_phase5_fixture_surface_triggers_the_boundary():
    """Every dry-run fixture step the gate executes must also select the gate.

    The workflow runs Phase 5 Governed Execution fixtures; if that test file is not
    a trigger path, a change to the very fixture the step validates can reach main
    without the boundary executing it.
    """
    triggers = _workflow_triggers()
    for trigger in ("push", "pull_request"):
        assert "tests/test_phase5_governed_execution.py" in triggers[trigger]["paths"], (
            f"{trigger} runs the Phase 5 fixture step but does not trigger on its file"
        )


def test_every_trigger_path_is_admitted_by_the_policy():
    """A trigger path the allowlist rejects would make the gate structurally red.

    The filter is written twice (push + pull_request); both must stay admissible so
    that widening the trigger set cannot introduce a permanent failure.
    """
    triggers = _workflow_triggers()
    for trigger in ("push", "pull_request"):
        for pattern in triggers[trigger]["paths"]:
            probe = pattern.replace("**", "x").replace("*", "x")
            if probe.endswith("/"):
                probe += "x"
            ok, msg = evaluate_changed_paths([probe])
            assert ok is True, (
                f"trigger pattern {pattern!r} ({trigger}) resolves to {probe!r}, "
                f"which the boundary rejects: {msg}"
            )

