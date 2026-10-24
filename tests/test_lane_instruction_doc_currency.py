"""Lane instruction-doc currency (Prism UI parallel lanes) — fitness test.

Guards the drift repaired in branch ``feat/prism-l1-lane-doc-currency-01``
(evidence: ``docs/control-plane/evidence/prism-l1-lane-doc-currency-01/``):
the four lane instruction documents under
``docs/control-plane/parallel-ui/AGENT-0N-*.md`` carried active-branch/PR
pointers to a **merged** wave (PRs #429/#430/#431/#428), so a successor agent
reading a lane doc would resume a closed thread.

The oracle is the machine-readable snapshot
``docs/control-plane/parallel-ui/lane-state.json``: the doc must agree with it,
and a lane may only be *deferred* while another open PR is repairing that doc.

Every check here reads the **real** snapshot and the **real** documents. Each
carries a negative control that proves the detector reports the shape it claims
to detect -- a guard that is silent on a planted defect is not a guard.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
LANE_STATE = LANE_DIR / "lane-state.json"


def _load_guard():
    spec = importlib.util.spec_from_file_location(
        "lane_state", REPO / "scripts" / "lane_state.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


def live_state() -> dict:
    return json.loads(LANE_STATE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- real corpus


def test_snapshot_exists_and_is_well_formed():
    state = live_state()
    assert state["schema"] == "arkadia.lane-state/1.1"
    assert len(state["base_main"]) == 40, "base_main must be a full 40-char SHA"
    assert sorted(state["lanes"]) == ["1", "2", "3", "4"]


def test_every_merged_pr_carries_its_merge_commit():
    # The liveness oracle decides "is this PR merged?" from ``merged_prs``. A
    # bare PR number makes that undecidable, so the guard would silently lose
    # the ability to catch a merged PR left under ``open_prs``. Each entry must
    # therefore be a {number, merge_commit_sha} object with a full-length SHA.
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        for entry in lane["merged_prs"]:
            assert isinstance(entry, dict), (
                f"lane {lane_no}: merged_prs entry {entry!r} is a bare PR number"
            )
            assert len(entry["merge_commit_sha"]) == 40, (
                f"lane {lane_no} merged PR #{entry['number']} merge_commit_sha "
                f"is not full length"
            )


def test_every_recorded_head_sha_is_full_length():
    # This repo has a recorded defect class: an abbreviated SHA makes an API
    # query silently return "no results". A snapshot is only re-verifiable if
    # its SHAs are full.
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        for pr in lane["open_prs"]:
            assert len(pr["head_sha"]) == 40, (
                f"lane {lane_no} PR #{pr['number']} head_sha is not full length"
            )


def test_live_guarded_docs_agree_with_the_snapshot():
    state = live_state()
    findings = guard._disposition_findings(state)
    findings += guard.check_lane_docs(state, lanes=guard.current_lanes(state))
    assert findings == [], findings


def test_lane_one_shell_doc_is_guarded_current():
    # Lane 1 owns the shell instruction (SHARED-CONTRACTS.md row 1). Its doc is
    # the one this workstream repairs, so it must not be deferred away.
    state = live_state()
    assert state["lanes"]["1"]["doc_guard"] == "current"


def test_lane_one_shell_doc_does_not_name_a_merged_pr():
    state = live_state()
    lane = state["lanes"]["1"]
    text = (LANE_DIR / lane["doc"]).read_text(encoding="utf-8")
    declared = guard.declared_pr(text)
    assert declared in guard._pr_index(state), (
        f"AGENT-01-SHELL.md declares PR #{declared}, not an open lane PR"
    )
    assert declared not in guard.merged_pr_numbers(state), (
        f"AGENT-01-SHELL.md declares merged PR #{declared}"
    )


def test_idle_lane_has_no_open_pr_and_is_not_guarded_as_active_work():
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        if lane["doc_guard"] == "idle":
            assert lane["open_prs"] == [], f"lane {lane_no}: idle lane has open PRs"
            assert lane_no not in guard.current_lanes(state)


def test_every_deferral_is_owned_by_an_open_pr():
    state = live_state()
    open_prs = guard._pr_index(state)
    for lane_no, lane in state["lanes"].items():
        if lane["doc_guard"] == "deferred":
            owner = lane["deferred_to_pr"]
            assert owner in open_prs, (
                f"lane {lane_no} defers to PR #{owner}, which is not open"
            )


def test_snapshot_freshness_is_asserted_not_merely_printed():
    """A snapshot measured against a superseded main must fail the check.

    The first cut of this guard printed ``base main: X (current: Y)`` and exited
    0 regardless -- a stale snapshot (the thing that makes every currency claim
    unsound) could not redden it. Fed a base_main that is not current main, the
    check must now report drift.
    """
    state = live_state()
    findings = guard._freshness_findings(state, "0" * 40)
    assert findings, "stale snapshot base_main was not reported"
    assert "re-measure" in findings[0]


def test_freshness_abstains_when_main_is_unresolvable():
    # An unprovable freshness is not a drift claim and not a pass. With no
    # resolvable main the check must produce no finding, and the caller prints
    # "unknown" rather than a comparison it did not make.
    state = live_state()
    assert guard._freshness_findings(state, None) == []
    assert "unknown" in guard.freshness_text(state, None)


def test_detector_flags_a_merged_pr_left_recorded_as_open():
    """Feed the liveness oracle the stale-snapshot shape and require a finding.

    Uses a real merge commit from the snapshot, so the control exercises the
    same git ancestry path the live check uses -- not a mock of it.
    """
    state = copy.deepcopy(live_state())
    merged_entry = state["lanes"]["1"]["merged_prs"][0]
    state["lanes"]["1"]["open_prs"].append(
        {
            "number": merged_entry["number"],
            "branch": "feat/prism-next2-01-shell-contract-map",
            "head_sha": "0" * 40,
        }
    )
    findings = guard._liveness_findings(state)
    assert any("already an ancestor of HEAD" in f for f in findings), findings


def test_liveness_reports_undecidable_when_the_clone_lacks_the_commit():
    # A shallow clone cannot see the merge commit. Scoring that as "not merged"
    # is a silent pass in the dangerous direction, so it must be reported as
    # UNKNOWN instead. Proven with a well-formed but absent object name.
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["open_prs"].append(
        {"number": 429, "branch": "x", "head_sha": "0" * 40}
    )
    for entry in state["lanes"]["1"]["merged_prs"]:
        if entry["number"] == 429:
            entry["merge_commit_sha"] = "a" * 40
    findings = guard._liveness_findings(state)
    assert any("UNKNOWN, not a pass" in f for f in findings), findings


def test_merge_commit_check_flags_a_bare_pr_number():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["merged_prs"] = [429]
    findings = guard._merge_commit_findings(state)
    assert any("bare PR number" in f for f in findings), findings


def test_merge_commit_check_flags_a_missing_sha():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["merged_prs"][0]["merge_commit_sha"] = ""
    findings = guard._merge_commit_findings(state)
    assert any("liveness cannot be decided" in f for f in findings), findings


def test_merged_pr_numbers_is_not_vacuous_against_dict_entries():
    # The pre-repair test asserted ``declared not in lane["merged_prs"]``. With
    # dict entries that compares an int against dicts and is *always* true --
    # a silently vacuous guard. The helper must extract numbers.
    state = live_state()
    numbers = guard.merged_pr_numbers(state)
    assert numbers, "merged_pr_numbers returned nothing"
    assert all(isinstance(n, int) for n in numbers)
    assert numbers == guard.merged_pr_commits(state).keys()


# ------------------------------------------------------------ negative controls


def test_detector_flags_a_doc_pointing_at_a_merged_pr(tmp_path):
    """Feed the detector the exact pre-repair shape and require it to report it."""
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active branch:** `feat/prism-next2-01-shell-contract-map`\n"
        "**Active PR:** [#429](https://example/429)\n",
        encoding="utf-8",
    )
    findings = guard.check_lane_docs(state, lane_dir=tmp_path, lanes=["1"])
    assert findings, "detector was silent on a doc naming a merged PR"
    assert any("#429" in f for f in findings)


def test_detector_flags_a_branch_that_does_not_match_its_pr(tmp_path):
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active branch:** `feat/wrong-branch`\n**Active PR:** #507\n",
        encoding="utf-8",
    )
    findings = guard.check_lane_docs(state, lane_dir=tmp_path, lanes=["1"])
    assert any("heads" in f for f in findings), findings


def test_disposition_check_flags_a_deferral_to_a_closed_pr():
    state = copy.deepcopy(live_state())
    state["lanes"]["2"]["doc_guard"] = "deferred"
    state["lanes"]["2"]["deferred_to_pr"] = 99999999  # not in the snapshot
    findings = guard._disposition_findings(state)
    assert any("#99999999" in f for f in findings), findings


def test_disposition_check_flags_an_unknown_disposition():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["doc_guard"] = "ignored"
    findings = guard._disposition_findings(state)
    assert any("must be 'current', 'deferred', or 'idle'" in f for f in findings), findings


@pytest.mark.parametrize("lane_no", ["1", "2", "3", "4"])
def test_last_declaration_wins_over_the_wave_header(lane_no):
    """A dated status block must supersede the earlier wave header.

    Lanes update by *appending* a status block; a first-wins scanner would
    read the stale wave header forever. This pins the last-wins convention.
    """
    text = (
        "**Active branch:** `feat/old-wave`\n"
        "**Active PR:** #429\n"
        "... later ...\n"
        "**Active branch:** `feat/new-wave`\n"
        "**Active PR:** #507\n"
    )
    assert guard.declared_branch(text) == "feat/new-wave"
    assert guard.declared_pr(text) == 507


# ------------------------------------------------------------------- wiring


def test_a_workflow_executes_the_lane_doc_guard():
    """The guard must have a continuous execution surface, and its trigger
    filter must name every input the guard reads.

    The guard reads the lane docs + snapshot, the policy script, and this test
    file. A filter that omits any of them lets a change to that input land
    without executing the guard -- the "guard no workflow runs is decoration"
    class recorded elsewhere in this repo.
    """
    workflow = (REPO / ".github/workflows/lane-doc-currency.yml").read_text(
        encoding="utf-8"
    )
    for needed in (
        "docs/control-plane/parallel-ui/**",
        "scripts/lane_state.py",
        "tests/test_lane_instruction_doc_currency.py",
        ".github/workflows/lane-doc-currency.yml",
    ):
        assert needed in workflow, f"lane-doc-currency.yml filter omits {needed}"
    # It must actually invoke pytest on the guard, not merely mention it.
    assert "pytest -q tests/test_lane_instruction_doc_currency.py" in workflow
    # The liveness oracle reads git ancestry, so the checkout must carry full
    # history. A depth-1 checkout makes the oracle undecidable (or, read
    # naively, silently permissive) -- pin the requirement to the workflow.
    assert "fetch-depth: 0" in workflow, (
        "lane-doc-currency.yml must check out full history (fetch-depth: 0) for "
        "the merge-ancestry liveness oracle"
    )
