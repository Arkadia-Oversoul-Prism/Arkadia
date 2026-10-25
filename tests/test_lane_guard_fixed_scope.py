"""The lane guard's scope must not be a function of the activity it judges.

Defect repaired here: ``scripts/lane_state.py`` derived the set of lanes it
enforced against from the snapshot's ``doc_guard`` field, and
``scripts/lane_state_refresh.py`` computed that field from **live open PRs**. A
pull request touching a lane's owned code paths and that lane's doc therefore
removed the lane from judgement -- and one broad PR touching every lane's paths
and docs emptied the enforced set, leaving a guard that examined nothing and
reported success.

These tests pin the invariant, not the implementation. ``scripts/lane_scope_probe.py``
is the executable statement of it; the assertions here keep the probe and the
constant from being disarmed.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import lane_state as guard  # noqa: E402
import lane_state_refresh as refresh  # noqa: E402

LANE_STATE = REPO / "docs" / "control-plane" / "parallel-ui" / "lane-state.json"


def _probe():
    spec = importlib.util.spec_from_file_location(
        "lane_scope_probe", REPO / "scripts" / "lane_scope_probe.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["lane_scope_probe"] = module
    spec.loader.exec_module(module)
    return module


def _live_state() -> dict:
    return json.loads(LANE_STATE.read_text(encoding="utf-8"))


# --------------------------------------------------------------- the invariant


def test_probe_passes_against_the_shipped_guard():
    """The acceptance test for this repair: all four checks must pass.

    Before the repair this failed three of four. It is the load-bearing
    assertion -- everything below pins a specific way the repair could be
    undone.
    """
    probe = _probe()
    results = probe.run(probe.shipped_scope)
    failed = [r["name"] for r in results if not r["passed"]]
    assert not failed, f"scope invariant violated: {failed}"


def test_probe_control_still_passes():
    """A check that cannot pass on a conforming design proves nothing."""
    probe = _probe()
    failed = [r["name"] for r in probe.run(probe.conforming_scope) if not r["passed"]]
    assert not failed, f"checks unsatisfiable on a conforming design: {failed}"


def test_enforced_set_is_the_canonical_constant_not_the_snapshot():
    """An empty snapshot must not empty the enforced set."""
    assert guard.enforced_lanes({"lanes": {}}) == sorted(guard.CANONICAL_LANES)


def test_one_pr_cannot_remove_its_lane_from_judgement():
    """The exact defect: a lane marked deferred must still be judged."""
    state = _live_state()
    for lane_no in state["lanes"]:
        deferred = copy.deepcopy(state)
        deferred["lanes"][lane_no]["doc_guard"] = "deferred"
        assert lane_no in guard.enforced_lanes(deferred), (
            f"lane {lane_no} left the enforced set when marked deferred"
        )


def test_a_fully_deferred_snapshot_is_still_judged():
    state = _live_state()
    for lane in state["lanes"].values():
        lane["doc_guard"] = "deferred"
    assert guard.enforced_lanes(state) == sorted(guard.CANONICAL_LANES)


# ------------------------------------------------- fail-closed, not vacuous


def test_empty_enforced_set_is_a_finding_not_a_pass():
    findings = guard._enforced_set_findings([])
    assert findings, "an empty enforced set passed vacuously"
    assert "EMPTY" in findings[0]


def test_nonempty_enforced_set_produces_no_finding():
    """Positive control: the guard must be silent when the set is sound."""
    assert guard._enforced_set_findings(sorted(guard.CANONICAL_LANES)) == []


def test_a_lane_absent_from_the_constant_is_still_judged_and_reported():
    """The snapshot may add a lane before the constant catches up -- but say so."""
    state = {"lanes": {"1": {"doc": "a.md"}, "99": {"doc": "b.md"}}}
    enforced = guard.enforced_lanes(state)
    assert "99" in enforced, "a lane present only in the snapshot was dropped"
    assert guard._enforced_set_findings(enforced), (
        "a judged lane missing from CANONICAL_LANES was not reported"
    )


# ------------------------------------------------------- the pair cannot drift


def test_canonical_lanes_match_lane_ownership():
    """The constant and the ownership map are two copies of one fact.

    They must agree, or a lane could be owned-but-unjudged (silently exempt) or
    judged-but-unowned. This is the drift guard for the deliberate duplication
    that makes the enforced set independent of the snapshot.
    """
    assert set(guard.CANONICAL_LANES) == set(refresh.LANE_OWNERSHIP), (
        "CANONICAL_LANES and LANE_OWNERSHIP disagree; update both in the same "
        "change -- the duplication is deliberate, the drift is not"
    )


# ------------------------------------------------- the second inversion site


def test_every_lane_blocks_on_a_dead_pointer():
    """A deferral must not silence a dead-pointer finding either.

    The same inversion appeared a second time in ``--verify-live``: only lanes
    whose ``doc_guard`` was ``current`` blocked, so deferring a lane also hid the
    fact that its doc pointed at a closed thread. The call site now passes the
    enforced set; this pins that it is not reverted to a derived one.
    """
    source = (REPO / "scripts" / "lane_state.py").read_text(encoding="utf-8")
    assert "lanes=enforced" in source, (
        "the dead-pointer check no longer receives the enforced set"
    )
    assert "lanes=owned" not in source, (
        "the dead-pointer check is scoped by a derived variable again"
    )


@pytest.mark.parametrize("lane_no", ["1", "2", "3", "4"])
def test_a_deferral_cannot_hide_a_dead_pointer(lane_no, tmp_path):
    """Feed the dead-pointer check a deferred lane; it must still report.

    The fixture is built here rather than read from the live lane docs: a live
    fixture would make this test pass or fail according to whether a doc happens
    to carry a dead pointer, which is not the property under test. The property
    is that *deferral does not suppress the finding*.
    """
    state = _live_state()
    state["lanes"][lane_no]["doc_guard"] = "deferred"
    doc = tmp_path / state["lanes"][lane_no]["doc"]
    doc.write_text("**Active branch:** `feat/dead`\n**Active PR:** #99999999\n",
                   encoding="utf-8")
    records = {99999999: {"state": "closed", "merged": False}}
    findings = guard._declared_pointer_findings(
        state, records, None, lane_dir=tmp_path, lanes=guard.enforced_lanes(state)
    )
    assert any("#99999999" in f for f in findings), (
        f"lane {lane_no} is deferred and its dead pointer was not reported"
    )
