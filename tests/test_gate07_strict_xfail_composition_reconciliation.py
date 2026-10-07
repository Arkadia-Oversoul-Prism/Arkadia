"""A strict xfail is a serialization constraint on the batch, not a preference.

PR #329 pins the worker -> attention seam and records the clean-stop defect as a
`strict=True` xfail: the healthy end of the hourly loop was composed into a pushed
HIGH `WEAVER_BLOCKED`. PR #342 repairs that defect — which is precisely the event
the strict xfail declares will flip it to a failure.

Neither PR is wrong in isolation. Each is green alone:

    #329 alone            -> 5 passed, 1 xfailed
    #342 alone            -> 11 passed

Composed (measured in a worktree at #329's tree with #342's `weaver/` patch applied):

    #329 + #342's router  -> 1 failed (strict XPASS), 5 passed

A batch merge therefore cannot take both in either order. This guard makes that
constraint executable and pins the reconciliation rule: the strict xfail is
*succeeded* by the repair, and the node must be re-materialized as a strict
assertion that the clean stop stays quiet. It is a decision record, not a gate
promotion and not an authority change.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTER_SOURCE = REPO_ROOT / "weaver" / "engineering_router.py"
COMPOSITION_GUARD = REPO_ROOT / "tests" / "test_worker_attention_composition.py"
EVIDENCE = (
    REPO_ROOT
    / "docs"
    / "control-plane"
    / "evidence"
    / "gate07-strict-xfail-composition-reconciliation-01"
    / "EVIDENCE.md"
)

# The router-side marker PR #342 introduces. It exists nowhere on `main`.
REPAIR_MARKER = "CLEAN_STOP_BLOCKER"

# The guard-side shape PR #329 introduces: a strict xfail.
STRICT_XFAIL_MARKER = "@pytest.mark.xfail(\n    strict=True,"

# The load-bearing clause of #329's recorded reason: it *declares* the flip. It is a
# single source line in the guard, so it is matched as one contiguous string.
FLIP_CLAUSE = "workstream; a strict xfail flips to a failure when it lands."

# The exact pre-repair guard block PR #329 records (file sha256 ebf81a50...). Held as
# a literal so the detector's negative control runs even before #329 is merged.
PRE_REPAIR_GUARD_TEXT = (
    "@pytest.mark.xfail(\n"
    "    strict=True,\n"
    "    reason=(\n"
    '        "RECORDED DEFECT (gate07/worker-attention-composition-guard-01): a trajectory "\n'
    '        "with no routable move is a clean stop \u2014 the scheduler treats NO_LEGAL_MOVE as "\n'
    '        "success \u2014 but select_next_move() always emits a blocker, so the worker composes "\n'
    '        "it into a pushed HIGH WEAVER_BLOCKED. Every idle hourly session would alert. "\n'
    '        "Repairing this changes the router\'s blockers contract and is a separate bounded "\n'
    '        "workstream; a strict xfail flips to a failure when it lands."\n'
    "    ),\n"
    ")\n"
)


def _read(path: Path) -> str:
    """Read a repository source file, or "" when it is absent at this revision."""
    return path.read_text(encoding="utf-8") if path.exists() else ""


def strict_xfail_repair_conflict(router_source: str, guard_source: str) -> str | None:
    """Return the conflict description when a repair coexists with its strict xfail.

    `None` means the pair is serializable: either the repair is absent, or the
    guard no longer records the defect as a strict xfail.
    """
    if REPAIR_MARKER not in router_source:
        return None
    if STRICT_XFAIL_MARKER not in guard_source:
        return None
    return (
        "weaver/engineering_router.py carries the clean-stop repair while "
        "tests/test_worker_attention_composition.py still records the clean-stop "
        "defect as a strict xfail; the guard will fail as a strict XPASS. "
        "Re-materialize the node as a strict quiet-stop assertion, or drop the repair."
    )


def test_a_strict_xfail_and_its_repair_cannot_coexist() -> None:
    """The live invariant: this repository revision must not hold both."""
    conflict = strict_xfail_repair_conflict(
        _read(ROUTER_SOURCE), _read(COMPOSITION_GUARD)
    )
    assert conflict is None, conflict


def test_detector_flags_the_known_pre_repair_pair() -> None:
    """Negative control: the detector reports the measured pre-repair combination.

    Without this, a detector that always returns `None` would look like a clean
    bill of health on every revision.
    """
    conflict = strict_xfail_repair_conflict(
        f"from weaver.engineering_router import {REPAIR_MARKER}\n",
        PRE_REPAIR_GUARD_TEXT,
    )
    assert conflict is not None
    assert "strict XPASS" in conflict


def test_detector_is_silent_when_the_repair_is_absent() -> None:
    """Positive control: the pre-repair router is not a conflict."""
    assert (
        strict_xfail_repair_conflict("def select_next_move():\n    ...\n", PRE_REPAIR_GUARD_TEXT)
        is None
    )


def test_recorded_xfail_reason_declares_the_flip() -> None:
    """#329's own reason text is what makes the two PRs non-serializable.

    If the reason no longer declares the flip, this guard's premise is stale and
    the reconciliation rule must be re-derived rather than assumed.
    """
    assert FLIP_CLAUSE in PRE_REPAIR_GUARD_TEXT


def test_reconciliation_decision_is_recorded() -> None:
    """The rule lives in-repo so the next heartbeat reconstructs it from evidence."""
    text = _read(EVIDENCE)
    assert text, f"missing decision record: {EVIDENCE}"
    for needle in ("#329", "#342", "strict xfail", "1 failed"):
        assert needle in text, f"decision record does not name {needle!r}"


def test_embedded_pre_repair_literal_matches_the_recorded_guard() -> None:
    """Self-check: the negative control's literal is the guard #329 actually wrote.

    Runs once #329's file is present at this revision; the extraction is anchored on
    the strict-xfail marker so it does not depend on surrounding file layout.
    """
    guard = _read(COMPOSITION_GUARD)
    if STRICT_XFAIL_MARKER not in guard:
        pytest.skip("pre-repair guard not present at this revision (PR #329 unmerged)")
    start = guard.index(STRICT_XFAIL_MARKER)
    end = guard.index(")\n", guard.index("    ),\n", start)) + 2
    assert guard[start:end] == PRE_REPAIR_GUARD_TEXT

