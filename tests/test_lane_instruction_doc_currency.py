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
    assert state["schema"] == "arkadia.lane-state/1.0"
    assert len(state["base_main"]) == 40, "base_main must be a full 40-char SHA"
    assert sorted(state["lanes"]) == ["1", "2", "3", "4"]


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
    assert declared not in lane["merged_prs"], (
        f"AGENT-01-SHELL.md declares merged PR #{declared}"
    )


def test_every_deferral_is_owned_by_an_open_pr():
    state = live_state()
    open_prs = guard._pr_index(state)
    for lane_no, lane in state["lanes"].items():
        if lane["doc_guard"] == "deferred":
            owner = lane["deferred_to_pr"]
            assert owner in open_prs, (
                f"lane {lane_no} defers to PR #{owner}, which is not open"
            )


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
    state["lanes"]["2"]["deferred_to_pr"] = 99999999  # not in the snapshot
    findings = guard._disposition_findings(state)
    assert any("#99999999" in f for f in findings), findings


def test_disposition_check_flags_an_unknown_disposition():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["doc_guard"] = "ignored"
    findings = guard._disposition_findings(state)
    assert any("must be 'current' or 'deferred'" in f for f in findings), findings


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
