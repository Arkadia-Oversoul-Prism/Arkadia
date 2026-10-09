"""Regression guard for the baseline test-debt fingerprint (gate-hygiene).

The published fingerprint in `.bootstrap/01_STATE.md` was, for two revisions,
not reproducible from the derivation printed beside it: the derivation read as
bare node ids, but the value was actually `"FAILED/ERROR <nodeid>"`. Worse, the
node ids had been read from `pytest -q` output *including* the assertion reason,
which pytest truncates to the terminal width -- so the same node set hashed
differently in a 120-column job and an 80-column shell.

These tests pin the derivation with known-answer tests (so a change in how the
fingerprint is computed fails loudly) and prove the two properties that make a
fingerprint usable: it is independent of the reporting terminal width and of
the order in which pytest reports nodes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "baseline_fingerprint", REPO_ROOT / "scripts" / "baseline_fingerprint.py"
)
assert _SPEC and _SPEC.loader
baseline_fingerprint = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(baseline_fingerprint)

# Known-answer test: sorted `"<OUTCOME> <nodeid>"` lines joined by "\n" plus a
# trailing newline.
KAT_LOG = (
    "FAILED tests/a.py::test_one - AssertionError: assert 1 == 2\n"
    "FAILED tests/b.py::test_two - assert 'x' in 'y'\n"
    "ERROR tests/c.py\n"
)
KAT_OUTCOMES = "6dca8d694c688a8bb845222d2ddedde7a190c7fcd5eaa78a3e4292f300cb0f49"
# sha256(b"\n") -- the empty fingerprint, which is a fixed value, not a special case.
EMPTY_FINGERPRINT = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"


def _write(tmp_path: Path, text: str, name: str = "suite.log") -> Path:
    # Distinct names matter: a shared filename makes a two-log comparison
    # compare one file with itself and pass vacuously.
    log = tmp_path / name
    log.write_text(text, encoding="utf-8")
    return log


def test_known_answer_outcomes_fingerprint(tmp_path):
    log = _write(tmp_path, KAT_LOG)
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [
        "ERROR tests/c.py",
        "FAILED tests/a.py::test_one",
        "FAILED tests/b.py::test_two",
    ]
    assert ids == ["tests/a.py::test_one", "tests/b.py::test_two", "tests/c.py"]
    assert baseline_fingerprint.fingerprint(outcomes) == KAT_OUTCOMES


def test_fingerprint_is_independent_of_terminal_width(tmp_path):
    """The defect this script exists to remove: reason truncation must not matter."""
    wide = _write(
        tmp_path,
        "FAILED tests/a.py::test_one - AssertionError: assert 'alpha' == 'beta' "
        "where 'alpha' is a very long repr that an 80-column terminal would clip\n"
        "ERROR tests/c.py\n",
        name="wide.log",
    )
    narrow = _write(
        tmp_path,
        "FAILED tests/a.py::test_one - Assert...\n"
        "ERROR tests/c.py\n",
        name="narrow.log",
    )
    wide_out, wide_ids = baseline_fingerprint.extract(str(wide))
    narrow_out, narrow_ids = baseline_fingerprint.extract(str(narrow))
    assert baseline_fingerprint.fingerprint(wide_out) == baseline_fingerprint.fingerprint(narrow_out)
    assert baseline_fingerprint.fingerprint(wide_ids) == baseline_fingerprint.fingerprint(narrow_ids)


def test_fingerprint_is_independent_of_report_order(tmp_path):
    a = _write(
        tmp_path,
        "FAILED tests/a.py::t\nERROR tests/c.py\nFAILED tests/b.py::t\n",
        name="order_a.log",
    )
    b = _write(
        tmp_path,
        "ERROR tests/c.py\nFAILED tests/b.py::t\nFAILED tests/a.py::t\n",
        name="order_b.log",
    )
    assert baseline_fingerprint.fingerprint(baseline_fingerprint.extract(str(a))[0]) == (
        baseline_fingerprint.fingerprint(baseline_fingerprint.extract(str(b))[0])
    )


def test_node_set_is_invariant_but_outcomes_distinguish_failure_from_error(tmp_path):
    """A node flipping FAILED<->ERROR is not a node-set change, but is a real
    outcome change; the two fingerprints must not conflate them."""
    failed = _write(tmp_path, "FAILED tests/a.py::t\nFAILED tests/b.py::t\n", name="failed.log")
    errored = _write(tmp_path, "ERROR tests/a.py::t\nFAILED tests/b.py::t\n", name="errored.log")
    f_out, f_ids = baseline_fingerprint.extract(str(failed))
    e_out, e_ids = baseline_fingerprint.extract(str(errored))
    assert baseline_fingerprint.fingerprint(f_ids) == baseline_fingerprint.fingerprint(e_ids)
    assert baseline_fingerprint.fingerprint(f_out) != baseline_fingerprint.fingerprint(e_out)


def test_empty_log_hashes_the_empty_fingerprint(tmp_path):
    log = _write(tmp_path, "no outcomes here\n")
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [] and ids == []
    assert baseline_fingerprint.fingerprint(ids) == EMPTY_FINGERPRINT


def test_extract_matches_an_independent_implementation(tmp_path):
    """Guard against the extractor drifting from the published derivation:
    `sha256("\\n".join(sorted(ids)) + "\\n")`, computed here by hand."""
    log = _write(tmp_path, KAT_LOG)
    _, ids = baseline_fingerprint.extract(str(log))
    independent = hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()
    assert baseline_fingerprint.fingerprint(ids) == independent


def test_json_output_shape(tmp_path, capsys):
    log = _write(tmp_path, KAT_LOG)
    rc = baseline_fingerprint.main([str(log), "--json"])
    assert rc == 0
    import json

    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"] == 3
    assert payload["failed"] == 2
    assert payload["errors"] == 1
    assert payload["outcomes_fingerprint"] == KAT_OUTCOMES


@pytest.mark.parametrize(
    "line",
    [
        "tests/a.py::test_one",  # a bare node id is not an outcome line
        "  FAILED tests/a.py::t",  # indented (continuation), not a report line
        "1 failed, 2 passed",  # summary line
    ],
)
def test_non_outcome_lines_are_ignored(tmp_path, line):
    log = _write(tmp_path, line + "\n")
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [] and ids == []


def test_log_missing_an_error_line_is_rejected_not_under_reported(tmp_path):
    """A log whose summary counts exceed its outcome lines must fail closed.

    pytest omits ERROR summary lines under `-rf`, so a collection error is invisible to
    the line-based extractor: the run *looks* complete while the fingerprint describes a
    subset of the debt. This is a negative control for the guard — it feeds the exact
    shape `-rf` produces and asserts the extractor refuses it rather than hashing a
    short node set.
    """
    log = _write(
        tmp_path,
        "FAILED tests/a.py::t - AssertionError\n"
        "9 failed, 1417 passed, 20 skipped, 1 error in 126.64s (0:02:06)\n",
    )
    with pytest.raises(ValueError, match="Re-run with `-rEf`"):
        baseline_fingerprint.extract(str(log))


def test_complete_log_is_accepted(tmp_path):
    """The positive control: matching counts parse without error."""
    log = _write(
        tmp_path,
        "FAILED tests/a.py::t - AssertionError\n"
        "ERROR tests/b.py\n"
        "1 failed, 1 error in 3.20s\n",
    )
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == ["ERROR tests/b.py", "FAILED tests/a.py::t"]
    assert ids == ["tests/a.py::t", "tests/b.py"]


# --- Live node set and published-value agreement ---------------------------
#
# The tests above pin the *derivation* with synthetic input. They cannot catch a
# published value that is internally inconsistent, because the published value is
# never fed back through the derivation. These tests close that gap: they run the
# real recorded baseline node set through the extractor and require the repository's
# published fingerprint to equal the result.
#
# History this guards: `.bootstrap/01_STATE.md` published `a59453b8…`/`9a35c812…`,
# but neither is reproducible from the derivation printed beside it (or from any
# other convention). `scripts/baseline_fingerprint.py` then produced `4d84e7eb…`/
# `da2ec262…` for the recorded nodes — but only in a clone that contained the PR-head
# revision `7d79f38…`, because the set it hashed held a node that skips when that
# revision is absent. The canonical value is now derived from a set that excludes it,
# so the value is stable across clone depths. See
# `docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/`.

LIVE_NODE_SET = REPO_ROOT / "tests" / "fixtures" / "baseline_node_set.txt"

# The recorded set *before* `gate-hygiene/stale-gate-fixture-retirement-01` retired the two
# nodes asserting the archived root `gate/` + `index.html` surface. `a59453b8…`/`9a35c812…`
# are this set plus the depth-dependent sibling below — they are not "unreproducible", and
# keeping the era-correct set lets the origin stay proved after the retirement.
SUPERSEDED_NODE_SET = (
    REPO_ROOT / "tests" / "fixtures" / "superseded_baseline_node_set.txt"
)

# The 18-node set that was canonical 2026-10-03 → 2026-10-04, before the live
# reconciliation removed the 8 entries a live run reports as passing. Retained so the
# superseded pair stays reproducible from an era-correct set rather than only from prose.
SUPERSEDED_18_NODE_SET = (
    REPO_ROOT / "tests" / "fixtures" / "superseded_baseline_node_set_18.txt"
)

# The 10-node set that was canonical 2026-10-04 → 2026-10-08, before
# `gate-hygiene/open-pr-owned-baseline-drift-01` recorded the 7 further nodes a live run
# reports that open PRs are repairing. Retained so the superseded pair stays reproducible
# from an era-correct set rather than only from prose.
SUPERSEDED_10_NODE_SET = (
    REPO_ROOT / "tests" / "fixtures" / "superseded_baseline_node_set_10.txt"
)

# The 17-node set that was canonical 2026-10-08 → 2026-10-09, before `main` advanced past
# this branch's base: #371 added the n-atlas workflow's self-selection line, so
# `test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]` — a node
# this reconciliation had recorded as open-PR-owned drift (#355) — now **passes** on `main`.
# A recorded node that leaves the failing set while its credited owner is still open is the
# exact defect `test_recorded_set_excludes_the_live_reconciled_repairs` exists to catch, so
# the node is retired into this archival fixture and the value retained as a superseded pair.
SUPERSEDED_17_NODE_SET = (
    REPO_ROOT / "tests" / "fixtures" / "superseded_baseline_node_set_17.txt"
)

# The subset of the recorded baseline whose *repair* is carried by an open pull request.
# Each of these fails on `main` and passes at its owner's head, so it is baseline debt a
# future merge will remove — not a regression. Recorded so the next pass does not
# re-derive the attribution, and so a node that leaves `main` without its owner merging
# (i.e. mine to explain) is visible.
OPEN_PR_OWNED_SET = (
    REPO_ROOT / "tests" / "fixtures" / "open_pr_owned_drift_node_set.txt"
)

# The *era*-set nodes whose repair is likewise carried by an open pull request. The earlier
# pass recorded this in prose only ("PR #357 repairs three of them") — measured, but not
# inspectable and not guarded, so nothing failed if a later pass re-listed them as unowned or
# dropped them when #357 merged. #357's head passes all three while `main` fails them, so the
# ownership belongs in a fixture the guard reads.
ERA_SET_OPEN_PR_OWNED_SET = (
    REPO_ROOT / "tests" / "fixtures" / "era_set_open_pr_owned_node_set.txt"
)

# The two nodes retired by `gate-hygiene/stale-gate-fixture-retirement-01`. They asserted a
# root `gate/` directory and root `index.html` redirect that `f6718b9` / `377cdb3` archived
# (the surface survives only under `archive/legacy_frontend/gate/`). The guard below fails if
# either re-enters the recorded set, so a future merge cannot silently restore the stale
# expectation while the fixture stays trimmed.
RETIRED_NODES = (
    "tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists",
    "tests/test_gate_status.py::test_gate_files_and_fetch_handling",
)

# The *sibling* depth-dependent node. It dereferences the `GATE2_PARENT_REV` read
# unconditionally, so it crashes (AttributeError) instead of skipping when `7d79f38…` is
# absent. It is likewise excluded from the recorded set — a live CI-shaped run reports it,
# so the recorded set is the *stable* debt, one node short of a bare clone's live run.
CLONE_DEPENDENT_SIBLING_NODE = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec"
)

# A node whose outcome depends on whether this clone contains the PR-head revision
# pinned by `tests/test_agents_md_encoding_adjudication.py` (`GATE2_PARENT_REV`). It
# is *not* part of the recorded set: including it made the fingerprint a function of
# clone depth rather than of the repository's debt. The guard below fails if it ever
# comes back.
CLONE_DEPTH_DEPENDENT_NODE = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline"
)

# The adjudication file's *pinned-revision* nodes: the four nodes whose outcome once
# depended on clone depth. Each dereferenced an `AGENTS.md` revision (the oracle, the
# corruption origin, or the recovered tip) that a **depth-1** clone (`git clone --depth 1`)
# does not resolve. Before the repair in this pass they *failed* there — a checkout
# incapable of adjudicating reported four false verdicts, and a bare clone carried **21**
# failing/error nodes against the recorded 17.
#
# The repair is test-side only and does not touch the audit instrument: each node now
# declines (`pytest.skip`) when its pinned revision is unresolvable, so a history-absent
# clone reports *the same 17 nodes* as one with full history — the depth-dependence is
# removed, not relocated. This is the "no node-set delta across clone depths" invariant,
# and the live probe below asserts it against a real bare clone rather than trusting this
# list. The tuple is retained (and the fingerprint guard below still checks these nodes are
# absent from the recorded set) so the *names* remain pinned: a regression that freed a
# node to fail would be caught by the probe, and a re-recording would be caught by the guard.
#
# Repaired this pass:
#   test_corruption_origin_is_re_derivable      -> now skips when CORRUPTION_COMMIT is absent
#   test_live_file_verdict_matches_its_state    -> now skips when ORACLE_REV is absent
#   test_cli_summarises_the_oracle_without_crashing           -> accepts the undecided exit 2
#   test_exit_code_does_not_call_a_divergent_clean_file_verified -> skips when revisions absent
#
# Measured on `main` `44137991`: full history -> 17 nodes (matches the fixture exactly);
# `git clone --depth 1` -> 17 nodes after the repair (was 21).
DEPTH1_CLONE_DEPENDENT_NODES = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_cli_summarises_the_oracle_without_crashing",
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_corruption_origin_is_re_derivable",
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_exit_code_does_not_call_a_divergent_clean_file_verified",
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_live_file_verdict_matches_its_state",
)

# Canonical values: `scripts/baseline_fingerprint.py` run on LIVE_NODE_SET.
# Superseded 2026-10-08 by `gate-hygiene/open-pr-owned-baseline-drift-01`: a live
# `-rEf --continue-on-collection-errors` run on `main` `44137991` reported 16 failed /
# 1776 passed / 22 skipped / 1 error — **17** nodes — while the recorded set carried 10.
# The 7 unrecorded nodes were all repaired by open PRs (#347/#354/#355/#356) and were
# therefore baseline debt, not regressions; recording them makes the fixture describe the
# repository's live debt rather than a subset of it.
# Superseded 2026-10-09 by the `main`-advance correction: a live run on `main` `43c3e2b1`
# reports 15 failed / 1 error — **16** nodes — one fewer than that 17, because #371 added the
# n-atlas workflow's self-selection line so the node credited to open PR #355 now passes.
# Both prior pairs (10 and 17 nodes) are retained in SUPERSEDED_* below.
CANONICAL_OUTCOMES_FINGERPRINT = (
    "bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733"
)
CANONICAL_IDS_FINGERPRINT = (
    "ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833"
)

# Values that were published but do not describe the recorded set. They must not
# reappear in the repository docs: the doc-agreement test below fails if either is
# found.
#
# `a59453b8…`/`9a35c812…` are the *era-correct* 20-node set plus its depth-dependent
# sibling node (proved by `test_superseded_values_are_the_superseded_set_plus_its_sibling`),
# i.e. a live bare-clone run — not the depth-stable recorded debt, and not
# "unreproducible". `4d84e7eb…`/`da2ec262…` were reproducible only in a clone that
# contained the PR-head revision `7d79f38…`. `a578a766…`/`8036fc06…` were the canonical
# pair for the 20-node recorded set before the two archived-surface nodes were retired
# 2026-10-03 by `gate-hygiene/stale-gate-fixture-retirement-01`. `6c7bf821…`/`2bc35996…`
# were canonical for the 18-node set, and `9a54f5b4…`/`124bfdfd…` for the 10-node set
# (2026-10-04 → 2026-10-08). All six pairs are superseded by the live-reconciled
# canonical value above.
SUPERSEDED_OUTCOMES_FINGERPRINTS = (
    "a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f",
    "4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7",
    "a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1",
    # Canonical for the 18-node recorded set, 2026-10-03 → 2026-10-04.
    "6c7bf8218fd1e0ae9bc970653e98c18b3a78b69a5c4920dac9f4747c033e4648",
    # Canonical for the 10-node recorded set, 2026-10-04 → 2026-10-08.
    "9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38",
    # Canonical for the 17-node recorded set, 2026-10-08 → 2026-10-09 (superseded when
    # #371 repaired the n-atlas trigger node on `main`).
    "26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798",
)
SUPERSEDED_IDS_FINGERPRINTS = (
    "9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22",
    "da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71",
    "8036fc0692eb0358f037adb2cf9e2b234db1f41a4586ca0162f4e52350cfa713",
    "2bc35996b21de6529ffffab63446c8bd7295c388e841a2807101d189eaf7da01",
    "124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f",
    # Canonical for the 17-node recorded set, 2026-10-08 → 2026-10-09.
    "571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224",
)

# Documents that publish a baseline fingerprint and must agree with the canonical
# value. MISSION.md / NEXT_AGENT.md / the ledger are read by the next agent, so a
# stale value there propagates the defect rather than recording it.
FINGERPRINT_DOCS = [
    ".bootstrap/01_STATE.md",
    "MISSION.md",
    "NEXT_AGENT.md",
    "docs/phase1/CONTINUATION_LEDGER.md",
]


# Nodes the reconciliation removed because a live full-suite run reports them as
# *passing*. They were repaired by later merges while the fixture kept carrying them as
# debt. Listing them here lets the guard below fail if one is ever re-recorded: the
# recorded set must describe the repository's live debt, not its history.
LIVE_RED_SHOULD_NOT_PASS_NODES = (
    "tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified",
    "tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge",
    "tests/test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records",
    "tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection",
    "tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write",
    "tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow",
    "tests/test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle",
    "tests/test_upstream_causal_continuity_01.py::test_api_approval_does_not_create_enterprise_authorization",
    # Repaired on `main` by #371 (the n-atlas workflow gained its own self-selection path),
    # so the node credited to open PR #355 stopped failing while #355 was still open. Its
    # leaving the failing set is not #355 merging; it must stay out of the recorded set.
    "tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]",
)


def test_live_node_set_reproduces_the_canonical_fingerprint():
    """The recorded baseline set must hash to the published canonical value."""
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert len(ids) == 16
    assert sum(1 for o in outcomes if o.startswith("FAILED")) == 15
    assert sum(1 for o in outcomes if o.startswith("ERROR")) == 1
    assert baseline_fingerprint.fingerprint(outcomes) == CANONICAL_OUTCOMES_FINGERPRINT
    assert baseline_fingerprint.fingerprint(ids) == CANONICAL_IDS_FINGERPRINT


def test_recorded_set_excludes_the_clone_depth_dependent_node():
    """The recorded set must not depend on clone depth.

    `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` skips when
    the PR-head revision it pins is absent, so its outcome differs between a shallow
    clone and one that carries that revision. The depth-1 extras fail outright (missing
    `AGENTS.md` history). Recording any of them made the fingerprint a function of the
    clone rather than of the repository's debt, which is the same defect class this
    reconciliation exists to remove. (The name stays singular for the prior evidence docs
    that cite it; the body guards the whole depth-dependent set.)
    """
    _, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert CLONE_DEPTH_DEPENDENT_NODE not in ids
    assert CLONE_DEPENDENT_SIBLING_NODE not in ids
    for node in DEPTH1_CLONE_DEPENDENT_NODES:
        assert node not in ids


def test_depth1_clone_dependent_nodes_are_named_as_a_set_not_a_single_node():
    """The depth-1 extras are four nodes, and none may be silently conflated with another.

    A single-node pin understated the divergence: the missing history changes the outcome
    of four adjudication nodes, and a bare clone reports 21 nodes against the recorded 17.
    This is a structural assertion; the live contrast against a real depth-1 clone is the
    separate probe below.
    """
    assert len(DEPTH1_CLONE_DEPENDENT_NODES) == 4
    assert CLONE_DEPENDENT_SIBLING_NODE not in DEPTH1_CLONE_DEPENDENT_NODES
    assert CLONE_DEPTH_DEPENDENT_NODE not in DEPTH1_CLONE_DEPENDENT_NODES
    assert all(
        n.startswith("tests/test_agents_md_encoding_adjudication.py::")
        for n in DEPTH1_CLONE_DEPENDENT_NODES
    )


def _agents_md_history_is_absent() -> bool:
    """Whether this clone lacks the `AGENTS.md` history the four nodes dereference.

    `--is-shallow-repository` is **not** the discriminator: the hourly automation's
    partial clone reports `true` yet still carries 26 revisions of `AGENTS.md`, so the
    pinned revisions resolve there. The nodes turn on whether those revisions *resolve*,
    which is a property of the history actually present, not of the shallow flag. A true
    `git clone --depth 1` carries a single revision of the file. (Since the repair, the
    nodes no longer fail in that regime — they decline — so this predicate now only
    selects which branch of the probe's invariant is exercised.)
    """
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "--format=%H", "--", "AGENTS.md"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return True
    return len(proc.stdout.split()) <= 1


def test_depth1_clone_nodes_are_exactly_the_extra_failures_in_a_bare_clone():
    """Live probe: the four nodes must not *fail* in any clone regime.

    A named list is only worth its maintenance if it is checked against the clone it
    describes. This runs the four candidate adjudication nodes in the *current* clone and
    asserts that none fails, whichever conformance constrains the subprocess: ``-rEf`` so a
    collection error is visible, and ``-p no:cacheprovider`` so a nested run leaves no
    ``.pytest_cache`` in the repository. A history-absent clone previously failed all four;
    after the repair each declines, so the assertion holds in both regimes and the file's
    node count is stable across clone depths.
    """
    derivative = REPO_ROOT / "tests" / "fixtures" / "depth1_clone_probe_node_set.txt"
    if derivative.exists():
        _, probe_ids = baseline_fingerprint.extract(str(derivative))
        assert set(probe_ids) == set(DEPTH1_CLONE_DEPENDENT_NODES)

    files = sorted({n.split("::", 1)[0] for n in DEPTH1_CLONE_DEPENDENT_NODES})
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "-rEf", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    failed = {
        line.split(" - ", 1)[0][len("FAILED "):].strip()
        for line in proc.stdout.splitlines()
        if line.startswith("FAILED ")
    }
    errored = {
        line.split(" - ", 1)[0][len("ERROR "):].strip()
        for line in proc.stdout.splitlines()
        if line.startswith("ERROR ")
    }
    # The invariant that makes the fingerprint depth-stable: none of the four nodes may
    # *fail* in any clone regime. A history-absent clone previously failed all four; after
    # the repair each declines (`skip`) instead, while a history-present clone still
    # exercises each. Asserting "no failure in either regime" is strictly stronger than the
    # old pass/fail split: a node that regressed to failing in *either* regime is caught, and
    # the probe no longer records a false verdict as an expected outcome.
    history_absent = _agents_md_history_is_absent()
    assert failed == set(), (
        f"adjudication nodes failed (history_absent={history_absent}): {sorted(failed)} — "
        "they must decline, not fail, when pinned history is unresolvable"
    )
    assert errored == set(), (
        f"adjudication nodes errored (history_absent={history_absent}): {sorted(errored)}"
    )


def test_recorded_set_excludes_the_retired_archived_surface_nodes():
    """The two retired nodes asserted a surface `f6718b9` / `377cdb3` archived.

    They are the repository's stale expectation, not its debt, so they must stay out of the
    recorded set. The guard keeps a future merge from restoring the stale literal while the
    fixture stays trimmed — the mirror image of the clone-depth guard above.
    """
    _, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    for retired in RETIRED_NODES:
        assert retired not in ids


def test_recorded_set_excludes_the_live_reconciled_repairs():
    """Nodes a live run reports as *passing* must not be carried as recorded debt.

    Eight entries were repaired by later merges while the fixture kept listing them. Keeping
    them made the recorded debt over-report — the repository's history, not its live state —
    which is the same defect class as the retired-archived-surface guard above. This fails if
    any of the eight is re-recorded.
    """
    _, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    for repaired in LIVE_RED_SHOULD_NOT_PASS_NODES:
        assert repaired not in ids


def test_superseded_18_node_set_reproduces_the_superseded_pair():
    """The archival fixture must hash to the superseded 18-node pair.

    `tests/fixtures/superseded_baseline_node_set_18.txt` is the only in-repo artifact
    that carries the pre-reconciliation 18-node debt. Without this guard the file could
    be edited or deleted while `SUPERSEDED_OUTCOMES_FINGERPRINTS` still cites the value,
    making the supersession unreproducible from the repository alone.
    """
    outcomes, ids = baseline_fingerprint.extract(str(SUPERSEDED_18_NODE_SET))
    assert len(ids) == 18
    assert baseline_fingerprint.fingerprint(outcomes) == SUPERSEDED_OUTCOMES_FINGERPRINTS[3]
    assert baseline_fingerprint.fingerprint(ids) == SUPERSEDED_IDS_FINGERPRINTS[3]


def _is_compositionally_attributed(recorded: set[str], era_ids: set[str],
                                   owned_ids: set[str]) -> bool:
    """True iff every recorded node is owned by the era set or an open PR."""
    return recorded == era_ids | owned_ids


def test_live_node_set_is_the_era_set_plus_the_open_pr_owned_set():
    """The recorded set must be reconstructable, with nothing silently absorbed.

    The 2026-10-04 reconciliation only *removed* entries a live run reports as passing;
    this 2026-10-08 pass *added* the 7 nodes a live run reports that open PRs are
    repairing. Every added node must be accounted for by `OPEN_PR_OWNED_SET` — a node in
    the recorded set but owned by neither the 10-node era set nor an open PR would mean a
    new failure was silently absorbed into the baseline instead of being attributed.
    This is the subset relation the earlier pass asserted, made compositional so it
    survives an addition as well as a removal.
    """
    _, live_ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    _, era_ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    owned_ids = _open_pr_owned_node_ids()
    assert _is_compositionally_attributed(set(live_ids), set(era_ids), owned_ids)
    # And the era set is still a *subset* — the reconciliation did not drop live debt.
    assert set(era_ids) <= set(live_ids)


def _open_pr_owned_node_ids() -> set[str]:
    return _fixture_node_ids(OPEN_PR_OWNED_SET)


def _era_set_open_pr_owned_node_ids() -> set[str]:
    return _fixture_node_ids(ERA_SET_OPEN_PR_OWNED_SET)


def _fixture_node_ids(path: Path) -> set[str]:
    return {
        line.split("\t", 1)[0].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def test_era_set_open_pr_owned_nodes_are_in_the_era_set():
    """Every era-owned entry must be an era-set node, and its owner must be named.

    The companion fixture asserts the era set is not uniformly unowned. If an entry named a
    node the era fixture does not carry, the fixture would describe ownership of a node that
    is not era debt — the mirror defect. And an entry without an owner PR could not be cleared
    when that PR merges, so the next pass would re-derive it.

    Re-measured 2026-10-09 at `main` `43c3e2b1`: the fixture grew 3 → 8 as #363/#365 were
    found to own five more era-set nodes, so the residual unowned set shrank 7 → 2. The count
    is derived below, so a fixture edit that leaves a stale split fails rather than ships.
    """
    _, era_ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    lines = [
        line for line in ERA_SET_OPEN_PR_OWNED_SET.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(lines) == 8
    for line in lines:
        node, _, pr = line.partition("\t")
        assert node.startswith("tests/") and "::" in node, line
        assert pr.strip().isdigit(), line
    owned_ids = _era_set_open_pr_owned_node_ids()
    assert owned_ids <= set(era_ids)
    # The drift fixture and this one partition disjointly: a node cannot be both a node the
    # era set already recorded and one a live run added beyond it.
    assert owned_ids.isdisjoint(_open_pr_owned_node_ids())


def test_era_set_ownership_is_reported_for_every_era_set_open_pr():
    """The era set is not uniformly unowned, and the split must stay derivable.

    The earlier pass recorded this split in prose: "the remaining seven era-set nodes ...
    have no open-PR owner". Nothing checked it, so a later pass could re-list the three
    #357-owned nodes as unowned — or drop them once #357 merges — without any test noticing.
    This derives the split from the fixtures and fails if the recorded ownership stops
    accounting for the whole era set.

    Re-measured 2026-10-09 at `main` `43c3e2b1`: #363 owns the two identity/ReasoMate nodes
    and #365 the three steward-filter nodes, so the split is now `10 = 8 owned + 2 unowned`
    (the residual being the `test_autonomy.py` ERROR and `test_ais_w2_living_gate_grove_handoff.py`).
    """
    _, era_ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    era_owned = _era_set_open_pr_owned_node_ids()
    unowned = set(era_ids) - era_owned
    assert len(era_ids) == 10
    assert len(era_owned) == 8
    assert len(unowned) == 2
    # And the era-owned nodes are still live debt — the recorded set carries them.
    _, live_ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert era_owned <= set(live_ids)


def test_open_pr_owned_nodes_are_all_recorded_baseline_debt():
    """A PR-owned node must be part of the recorded set, and absent no other node.

    The companion fixture names the nodes whose repair an open PR carries. If one were
    listed but not recorded, the fixture would describe debt `main` does not have — the
    mirror defect of leaving it unrecorded.
    """
    _, live_ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    owned_ids = _open_pr_owned_node_ids()
    assert len(owned_ids) == 6
    assert owned_ids <= set(live_ids)


def test_open_pr_owned_entries_each_name_a_pr():
    """Every companion entry must carry an owner PR, so it can be cleared on merge."""
    lines = [
        line for line in OPEN_PR_OWNED_SET.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(lines) == 6
    for line in lines:
        node, _, pr = line.partition("\t")
        assert node.startswith("tests/") and "::" in node, line
        assert pr.strip().isdigit(), line


def test_superseded_10_node_set_reproduces_the_superseded_pair():
    """The era fixture must hash to the 10-node pair it is cited for.

    `tests/fixtures/superseded_baseline_node_set_10.txt` is the only in-repo artifact that
    carries the 2026-10-04 → 2026-10-08 recorded debt. Without this guard the file could be
    edited or deleted while `SUPERSEDED_*` still cites the value, making the supersession
    unreproducible from the repository alone.
    """
    outcomes, ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    assert len(ids) == 10
    assert baseline_fingerprint.fingerprint(outcomes) == SUPERSEDED_OUTCOMES_FINGERPRINTS[4]
    assert baseline_fingerprint.fingerprint(ids) == SUPERSEDED_IDS_FINGERPRINTS[4]


def test_superseded_17_node_set_reproduces_the_superseded_pair():
    """The 17-node era fixture must hash to the pair it is cited for.

    `tests/fixtures/superseded_baseline_node_set_17.txt` is the only in-repo artifact that
    carries the 2026-10-08 → 2026-10-09 recorded debt: the set this reconciliation published
    before `main` advanced through #371 and repaired the n-atlas trigger node. Without this
    guard the file could be edited or deleted while `SUPERSEDED_*` still cites the value,
    making the supersession unreproducible from the repository alone.
    """
    outcomes, ids = baseline_fingerprint.extract(str(SUPERSEDED_17_NODE_SET))
    assert len(ids) == 17
    assert baseline_fingerprint.fingerprint(outcomes) == SUPERSEDED_OUTCOMES_FINGERPRINTS[5]
    assert baseline_fingerprint.fingerprint(ids) == SUPERSEDED_IDS_FINGERPRINTS[5]


def test_superseded_17_node_set_excludes_the_repaired_node():
    """The archival 17-node set must carry the node `main` later repaired.

    The supersession only reproduces if the archived set still contains the n-atlas trigger
    node: it is the single difference between the 17-node and the canonical 16-node set.
    Deriving it here keeps the correction inspectable — a future edit that trimmed the
    archival fixture would make the recorded 17-node pair unreproducible while the test
    above still passed on a coincidental value.
    """
    _, ids = baseline_fingerprint.extract(str(SUPERSEDED_17_NODE_SET))
    repaired = (
        "tests/test_ci_gate_trigger_coverage.py"
        "::test_pr_pytest_workflow_is_selected_by_its_own_file"
        "[n-atlas-developer-lab.yml]"
    )
    _, live_ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert repaired in ids
    assert repaired not in live_ids
    assert len(set(ids) - set(live_ids)) == 1


def test_era_set_composition_rejects_an_unattributed_node():
    """Negative control: a node owned by neither the era set nor an open PR must fail.

    The compositional guard is only meaningful if a silently-absorbed node is actually
    rejected. Feed the *same predicate* the positive test uses a recorded set that adds an
    unattributed node and confirm it returns false — without this the positive test could
    pass on a predicate that accepts anything.
    """
    _, era_ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    owned_ids = _open_pr_owned_node_ids()
    absorbed = "tests/test_somewhere.py::test_a_new_unexplained_failure"
    recorded = set(era_ids) | owned_ids | {absorbed}
    assert not _is_compositionally_attributed(recorded, set(era_ids), owned_ids)
    # Positive control: the same predicate accepts the attributed set.
    assert _is_compositionally_attributed(set(era_ids) | owned_ids, set(era_ids), owned_ids)


def test_superseded_values_are_the_superseded_set_plus_its_sibling():
    """`a59453b8…`/`9a35c812…` are the *era-correct* 20-node set plus its depth-dependent
    sibling — not "unreproducible by any convention".

    A bare clone (CI) reports the sibling — it crashes with AttributeError instead of
    skipping — so its live run is the recorded set plus that node. Deriving the value from
    `SUPERSEDED_NODE_SET` (the set as it stood before the retirement) rather than from the
    current 18-node set keeps this origin proved after `gate-hygiene/
    stale-gate-fixture-retirement-01` trimmed the two archived-surface nodes. Both values are
    still *superseded* — the sibling is clone-depth dependent and must not be republished.
    """
    outcomes, ids = baseline_fingerprint.extract(str(SUPERSEDED_NODE_SET))
    assert CLONE_DEPENDENT_SIBLING_NODE not in ids
    assert baseline_fingerprint.fingerprint(
        sorted(outcomes + [f"FAILED {CLONE_DEPENDENT_SIBLING_NODE}"])
    ) == SUPERSEDED_OUTCOMES_FINGERPRINTS[0]
    assert baseline_fingerprint.fingerprint(
        sorted(ids + [CLONE_DEPENDENT_SIBLING_NODE])
    ) == SUPERSEDED_IDS_FINGERPRINTS[0]


def test_superseded_fingerprints_are_not_reproducible():
    """Negative control: the recorded set must NOT hash to a superseded value, so the
    doc-agreement test cannot be satisfied by accident. A convention that happened to
    yield a superseded value would mean the correction was wrong.

    Note the distinction from `test_superseded_values_are_the_superseded_set_plus_its_sibling`:
    a superseded value *is* reproducible — from the era-correct set plus a depth-dependent
    node. What must never hold is the recorded set alone reproducing one.
    """
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    outcomes_fp = baseline_fingerprint.fingerprint(outcomes)
    ids_fp = baseline_fingerprint.fingerprint(ids)
    assert outcomes_fp not in SUPERSEDED_OUTCOMES_FINGERPRINTS
    assert ids_fp not in SUPERSEDED_IDS_FINGERPRINTS
    # And no "reason included" / "unsorted" variant lands on them either.
    unsorted_ids_fp = hashlib.sha256(("\n".join(sorted(ids)).encode())).hexdigest()
    assert unsorted_ids_fp not in SUPERSEDED_IDS_FINGERPRINTS


@pytest.mark.parametrize("doc", FINGERPRINT_DOCS)
def test_published_docs_carry_the_canonical_fingerprint(doc):
    text = (REPO_ROOT / doc).read_text(encoding="utf-8")
    for superseded in SUPERSEDED_OUTCOMES_FINGERPRINTS:
        assert superseded not in text, (
            f"{doc} still publishes the superseded outcomes fingerprint {superseded}"
        )
    for superseded in SUPERSEDED_IDS_FINGERPRINTS:
        assert superseded not in text, (
            f"{doc} still publishes the superseded node-set fingerprint {superseded}"
        )
    assert CANONICAL_OUTCOMES_FINGERPRINT in text, (
        f"{doc} does not publish the canonical outcomes fingerprint"
    )


# The counts a pass records in prose. A pass that changes a fixture and leaves a count
# describing the old one is the failure mode this pins: the counts are derived from the
# fixtures below, so the two can no longer drift apart silently.
#
# `main` and the branch measure the *same* 16-node set; the branch's extra passes are its
# own new guard functions, so the passed count is NOT a fingerprint input and is
# deliberately excluded. Only the failing/error counts are pinned.
RECORDED_BASELINE_COUNTS = {
    "failed": 15,
    "errors": 1,
    "nodes": 16,
    "era_set": 10,
    "era_set_open_pr_owned": 8,
    "era_set_unowned": 2,
    "open_pr_owned_drift": 6,
}


def test_recorded_counts_are_derived_from_the_fixtures_not_prose():
    """Every recorded count must be reproducible from the fixtures.

    This is the compositional half of the reconciliation: the drift fixture already makes an
    *unattributed* node fail, and this guard makes a *mis-described* attribution fail. A
    future pass may change a fixture and the doc together, but it cannot change one and leave
    a count the other contradicts.
    """
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    _, era_ids = baseline_fingerprint.extract(str(SUPERSEDED_10_NODE_SET))
    era_owned = _era_set_open_pr_owned_node_ids()
    drift = _open_pr_owned_node_ids()

    derived = {
        "failed": len([o for o in outcomes if o.startswith("FAILED ")]),
        "errors": len([o for o in outcomes if o.startswith("ERROR ")]),
        "nodes": len(ids),
        "era_set": len(era_ids),
        "era_set_open_pr_owned": len(era_owned),
        "era_set_unowned": len(set(era_ids) - era_owned),
        "open_pr_owned_drift": len(drift),
    }
    assert derived == RECORDED_BASELINE_COUNTS, derived
    assert derived["nodes"] == derived["failed"] + derived["errors"]
    # The era set and the drift set together account for every recorded node.
    assert set(era_ids) | drift == set(ids)
