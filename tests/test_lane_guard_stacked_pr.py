"""A lane PR based on another branch is a composition hazard, not a lane PR.

Defect repaired here: ``scripts/lane_state.py`` judged a claimed-open lane PR by
its *state* (open / merged / closed) and never by its *base*. A PR whose base is
another branch is stacked: merging it lands the base branch's commits as well,
and the review of the child covers only the child. Measured 2026-10-25: lane
repair PR #568 targets #567's branch, and #567's own body records that merging it
"would itself require authorization" -- so merging the child lands an
unauthorized parent through the ordinary green-check path.

The liveness oracle cannot see this. It proves merged-ness from local ancestry
(``git merge-base --is-ancestor``), and a stacked PR and an unstacked one have
identical ancestry from the lane's point of view. The base branch is a separate
fact and needs a separate check.

The fixture is built in the test rather than read from the live snapshot: a live
fixture would make the outcome depend on which lane PR happens to be stacked,
which is not the property under test. The property is that a stacked base is
reported and an unstacked one is not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import lane_state as guard  # noqa: E402
import lane_state_refresh as refresh  # noqa: E402

LANE_STATE = REPO / "docs" / "control-plane" / "parallel-ui" / "lane-state.json"


def _state_with(number: int, claimants: list[str] | None = None) -> dict:
    """A minimal snapshot claiming ``number`` open, plus a real lane doc entry."""
    return {
        "lanes": {
            "1": {
                "doc": "AGENT-01-SHELL.md",
                "open_prs": [{"number": number, "branch": "feat/x", "head_sha": "a" * 40}],
            }
        },
        "closed_unmerged": [],
    }


def _record(number: int, base: str | None, state: str = "open", merged: bool = False) -> dict:
    rec: dict = {"number": number, "state": state, "merged": merged}
    if base is not None:
        rec["base"] = {"ref": base}
    return rec


# ------------------------------------------------------- the detector, directly


def test_a_stacked_pr_is_reported_as_stacked():
    """The load-bearing assertion: a non-default base must produce a finding."""
    state = _state_with(568)
    findings = guard._base_branch_findings(
        state, {568: _record(568, "gate-hygiene/lane-guard-authority-boundary-01")}
    )
    assert any("STACKED" in f and "#568" in f for f in findings), findings
    assert any("main" in f for f in findings), (
        "the finding must name the branch the PR should target: " + str(findings)
    )


def test_an_unstacked_pr_produces_no_finding():
    """Negative control: the detector must be silent on the safe shape.

    A detector that reddens on every PR reports nothing. This is the control that
    keeps the assertion above from being trivially true.
    """
    assert guard._base_branch_findings(_state_with(562), {562: _record(562, "main")}) == []


def test_an_unreadable_base_is_unknown_not_a_pass():
    """Fail closed: a record with no `base` cannot be assumed unstacked."""
    findings = guard._base_branch_findings(_state_with(562), {562: _record(562, None)})
    assert any("UNKNOWN" in f for f in findings), findings


def test_an_absent_record_is_left_to_the_state_check():
    """One fact, one finding: a missing record is reported by `_pr_state_findings`.

    Restating it here would double-count absence as two findings and make the
    output read as two independent defects.
    """
    assert guard._base_branch_findings(_state_with(999), {}) == []


# --------------------------------------------- the snapshot records the base


def test_the_refresh_records_each_pr_base_branch():
    """Without the field the guard above has nothing to read.

    The guard cannot re-derive the base from the snapshot, so the refresh must
    carry it. This pins the producer to the consumer.
    """
    open_prs = [
        {
            "number": 568,
            "title": "t",
            "draft": True,
            "updated_at": "2026-10-25T00:00:00Z",
            "head": {"ref": "gate-hygiene/lane-guard-fixed-scope-01", "sha": "b" * 40},
            "base": {"ref": "gate-hygiene/lane-guard-authority-boundary-01"},
        }
    ]
    state = refresh.build(
        open_prs, {568: ["web/arkadia_console/src/App.tsx"]}, "c" * 40, "owner/repo"
    )
    entry = state["lanes"]["1"]["open_prs"][0]
    assert entry["base_ref"] == "gate-hygiene/lane-guard-authority-boundary-01", entry


def test_the_shipped_snapshot_records_a_base_for_every_open_pr():
    """The live snapshot must carry the field the guard reads, or the guard is blind."""
    state = json.loads(LANE_STATE.read_text(encoding="utf-8"))
    missing = [
        (lane_no, pr["number"])
        for lane_no, lane in state["lanes"].items()
        for pr in lane.get("open_prs", [])
        if "base_ref" not in pr
    ]
    assert missing == [], (
        "snapshot entries with no recorded base branch (re-measure with "
        f"lane_state_refresh.py --write): {missing}"
    )
