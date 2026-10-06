"""The hourly stop must reach the sovereign, or it is not a stop.

`EngineeringWorker.run()` records a downstream attention event for every terminal
outcome. `build_engineering_attention_event` decided salience from the status alone:
`FAILED`/`BLOCKED` were high-severity and pushed; everything else — including
`NO_LEGAL_MOVE` — was a plain `WEAVER_STATE_CHANGED` at INFO with `push_delivery`
false.

`NO_LEGAL_MOVE` is only a *clean* stop when it has nothing to report. When the router
returns it **with blockers** the trajectory still carried a frontier the session could
not route — a structural slip (`invalid trajectory structure`, the live hourly failure
`37379043890`), an unrecognized move status (the G12-A/G12-C `merged_acceptance_pending`
slip), or an unresolved dependency. Projecting that as an ordinary state change left the
hourly stop silent: no push, no action, `action_required` false.

These tests exercise only the public builder, so the negative control fails on a wrong
classification rather than on an import. A rewrite that reports every outcome as blocked
is caught by `test_clean_no_legal_move_stays_quiet`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from weaver.attention_bus import build_engineering_attention_event, classify_event


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# The pre-fix salience rule, kept here as the control it is: a status-only decision.
_PREFIX_STATUS_ONLY = {"FAILED", "BLOCKED"}


def _event(status: str, *, blockers: list[str] | None = None, **extra):
    return build_engineering_attention_event(
        {
            "session_id": "engineering-test",
            "status": status,
            "blockers": blockers or [],
            "next_move": None,
            **extra,
        }
    )


def test_failed_session_is_blocked_and_pushed():
    event = _event("FAILED", blockers=["invalid trajectory structure"])
    assert event.event_type == "WEAVER_BLOCKED"
    assert event.severity == "HIGH"
    assert event.action_required is True
    assert "push" in classify_event(event).channels


@pytest.mark.parametrize(
    "blocker",
    [
        "invalid trajectory structure",
        "unrecognized move status: G12-A ('merged_acceptance_pending')",
        "G12-B: missing dependency G12-X",
        "G12-B: scope/spec missing",
    ],
)
def test_no_legal_move_with_blockers_is_pushed(blocker: str):
    """An unroutable frontier must reach the sovereign, not be filed as INFO."""
    event = _event("NO_LEGAL_MOVE", blockers=[blocker])
    assert event.event_type == "WEAVER_BLOCKED"
    assert event.severity == "HIGH"
    assert event.action_required is True
    assert "push" in classify_event(event).channels


def test_clean_no_legal_move_stays_quiet():
    """With nothing to report, NO_LEGAL_MOVE remains an ordinary clean stop.

    Negative control for the repair: a detector that flagged every NO_LEGAL_MOVE would
    turn the loop's healthy end state into permanent noise.
    """
    event = _event("NO_LEGAL_MOVE")
    assert event.event_type == "WEAVER_STATE_CHANGED"
    assert event.severity == "INFO"
    assert event.action_required is False
    assert "push" not in classify_event(event).channels


def test_ready_for_review_still_requires_human_authority():
    """Regression: the review boundary keeps its authority and push delivery."""
    event = _event("READY_FOR_REVIEW", next_move={"id": "G12-B"})
    assert event.event_type == "WEAVER_STATE_CHANGED"
    assert event.human_authority_required is True
    assert event.action_required is True
    assert "push" in classify_event(event).channels


def test_negative_control_status_only_rule_would_miss_the_defect():
    """The pre-fix rule classifies the live defect as not-blocked.

    If the assertion below ever stops holding, the repair has been reverted to a
    status-only decision and the hourly stop goes silent again.
    """
    result = {
        "session_id": "engineering-test",
        "status": "NO_LEGAL_MOVE",
        "blockers": ["invalid trajectory structure"],
        "next_move": None,
    }
    assert (result["status"] in _PREFIX_STATUS_ONLY) is False
    event = build_engineering_attention_event(result)
    assert event.event_type == "WEAVER_BLOCKED"
    assert event.action_required is True


def test_guard_is_selected_by_a_workflow_that_runs_the_whole_suite():
    """A guard no workflow executes is decoration.

    The guard is auto-collected by any workflow running the whole suite, but only if
    that workflow is triggered by a change to `weaver/**`. This pins that wiring
    without naming a file list that would drift.
    """
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "pytest tests/ -q" not in text:
            continue
        workflow = yaml.safe_load(text)
        # PyYAML parses the bare key `on` as the boolean True.
        trigger = workflow.get(True, workflow.get("on")) or {}
        pr_paths = set((trigger.get("pull_request") or {}).get("paths") or [])
        if "weaver/**" in pr_paths:
            return
    pytest.fail(
        "no workflow runs the whole test suite and is selected by 'weaver/**'; a "
        "change to weaver/attention_bus.py would not execute this guard"
    )
