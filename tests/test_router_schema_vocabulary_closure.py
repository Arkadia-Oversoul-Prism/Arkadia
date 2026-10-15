"""Every schema-legal move status must be active, terminal, or explicitly gated.

`tests/test_trajectory_schema_conformance.py` guards the seam in one direction only:
`router ⊆ schema` (the statuses the router acts on are schema-legal). The reverse
direction — `schema ⊆ router` — was asserted nowhere, so the frozen contract could
admit a status the router has no behaviour for and nothing failed.

That gap is live. Schema-legal states `aborted`, `blocked`, `failed`, `merged`, and
`merged_acceptance_pending` require explicit non-routable treatment. The last marks a live
frontier (`G12-A`, `G12-C` on `TRAJECTORY-CONSOLE-COMPLETION-01.yaml`).
Before the truthfulness repair (PR #322) the skip was silent: the session reported the
generic "no legal pending move (all complete or dependencies unresolved)" fallback for
a trajectory that still carried active work. After #322 it is named — the frontier is
still unroutable, but the session can say why.

This guard pins a complete status disposition: active statuses may route; completed/accepted
statuses may terminate; merged-but-unaccepted and blocked/failure states are explicitly gated;
statuses outside the schema are named as malformed. No gate status may satisfy a dependency.

The guard is stdlib-only (plus `pytest`): it reads the JSON schema with `json`, the
trajectory with a small line reader, and drives the router through its public
`select_next_move()`. A guard that can be skipped for a missing install is decoration.
"""
from __future__ import annotations

import json

from pathlib import Path

import pytest

from weaver.engineering_router import (
    ACTIVE_STATUSES,
    NON_ROUTABLE_STATUSES,
    TERMINAL_DONE,
    _load_yaml,
    select_next_move,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/control-plane/trajectory.schema.json"
CONTROL_PLANE = ROOT / "docs/control-plane"
LIVE_TRAJECTORY = CONTROL_PLANE / "TRAJECTORY-CONSOLE-COMPLETION-01.yaml"

_ROUTER_VOCABULARY = frozenset(ACTIVE_STATUSES) | frozenset(TERMINAL_DONE) | frozenset(NON_ROUTABLE_STATUSES)

# The pre-#322 fallback. Kept here as the control it is: the generic message the
# router emitted for *any* unroutable frontier, including a live one.
_PREFIX_GENERIC_FALLBACK = "no legal pending move"
_UNRECOGNIZED_MARKER = "unrecognized move status"


def _schema_move_enum() -> set[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"]["moves"]["items"]["properties"]["status"]["enum"])


def _live_moves() -> list[dict]:
    """The live trajectory's moves, via the router's own loader.

    `moves` sits at the top level (PR #319 lifted it); fall back to the nested
    position so a future move back does not read as "no moves".
    """
    data = _load_yaml(LIVE_TRAJECTORY)
    moves = data.get("moves") or data["trajectory"].get("moves") or []
    assert moves, f"{LIVE_TRAJECTORY.name}: no moves parsed"
    return moves


def _trajectory(status: str, move_id: str = "M") -> dict:
    """A minimal trajectory whose single move carries `status`."""
    return {
        "trajectory": {
            "id": "T",
            "status": "authorized-for-review-gated-execution",
        },
        "moves": [{"id": move_id, "status": status, "spec": "s.md"}],
    }


def _route(status: str) -> tuple[dict | None, list[str]]:
    return select_next_move(_trajectory(status))


def _is_named_unroutable(move: dict | None, blockers: list[str], status: str) -> bool:
    """True when the router declined *and* named `status` as the reason."""
    if move is not None:
        return False
    joined = " ".join(blockers)
    return _UNRECOGNIZED_MARKER in joined and f"({status!r})" in joined


# ---------------------------------------------------------------------------
# The invariant: the schema cannot admit a status the router skips silently
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", sorted(_schema_move_enum()))
def test_every_schema_legal_status_is_routable_or_named_unroutable(status: str):
    """A schema-legal status must never be dropped without being reported.

    A status the router knows is an honest answer either way: selected when active,
    or the generic fallback when terminal (nothing left to route). A status outside
    the vocabulary has no honest fallback — it must be *named*, or the session
    reports "all complete or dependencies unresolved" for live work.
    """
    move, blockers = _route(status)
    if status in ACTIVE_STATUSES:
        assert move is not None, f"active status {status!r} was not selected: {blockers}"
        return
    if status in TERMINAL_DONE:
        assert move is None
        assert any(_PREFIX_GENERIC_FALLBACK in b for b in blockers)
        return
    if status in NON_ROUTABLE_STATUSES:
        assert move is None, f"gated status {status!r} was selected"
        joined = " ".join(blockers)
        assert status in joined and "human review/acceptance evidence required" in joined
        assert "unrecognized move status" not in joined
        assert not any(_PREFIX_GENERIC_FALLBACK in b for b in blockers)
        return
    assert move is None, f"unknown status {status!r} was silently selected"
    assert _is_named_unroutable(move, blockers, status), (
        f"status {status!r} is outside the schema but the router skipped it silently; "
        f"blockers={blockers}"
    )


def test_schema_statuses_have_explicit_active_terminal_or_gate_dispositions():
    """Pin the live vocabulary gap so a change to it is deliberate.

    `merged_acceptance_pending` encodes "the PR merged but repository acceptance
    evidence is not yet recorded"; `aborted`/`blocked`/`failed` are failure states the
    router models only as *blockers*, not as move statuses. The set is asserted
    exactly, so widening the router vocabulary or closing the gap in the trajectory
    data fails here and is re-decided rather than drifting.

    This is a *record*, not a requirement: the guard above is what must keep
    holding. Closing the gap is a sovereign decision (see
    `docs/control-plane/evidence/gate07-trajectory-status-vocabulary-decision-01/`).
    """
    assert _schema_move_enum() == (
        set(ACTIVE_STATUSES) | set(TERMINAL_DONE) | set(NON_ROUTABLE_STATUSES)
    )
    assert NON_ROUTABLE_STATUSES == {
        "aborted",
        "blocked",
        "failed",
        "merged",
        "merged_acceptance_pending",
    }


def test_router_vocabulary_is_a_subset_of_the_schema_enum():
    """The sibling direction, restated here so the seam reads in one file.

    `tests/test_trajectory_schema_conformance.py` owns this assertion; keeping it
    local means a reader of either half sees both directions of the same seam.
    """
    assert _ROUTER_VOCABULARY <= _schema_move_enum()


# ---------------------------------------------------------------------------
# The defect is live, not hypothetical
# ---------------------------------------------------------------------------


def test_live_trajectory_frontier_is_unroutable_and_named():
    """The live trajectory carries a frontier the router cannot route.

    Not a failure of the router: it is the data that is outside the vocabulary.
    The router's obligation is to name it, which this pins.
    """
    gated = sorted(
        {str(m.get("status")) for m in _live_moves()}
        & set(NON_ROUTABLE_STATUSES)
    )
    assert gated == ["merged_acceptance_pending"], (
        f"live trajectory gated statuses changed: {gated}"
    )

    move, blockers = select_next_move(_load_yaml(LIVE_TRAJECTORY))
    assert move is None, "live trajectory unexpectedly selected a move"
    joined = " ".join(blockers)
    assert "merged_acceptance_pending" in joined
    assert "human review/acceptance evidence required" in joined
    assert "dependency-blocked frontier" in joined
    assert "unrecognized move status" not in joined


# ---------------------------------------------------------------------------
# Negative controls — the guard must fail on the behaviour it replaces
# ---------------------------------------------------------------------------


def test_negative_control_pre_fix_router_would_have_skipped_silently():
    """The pre-#322 router reported the generic fallback for the live frontier.

    This reproduces the silent-skip shape directly: when the only move is
    unroutable and the router emits the generic fallback, the reason is absent.
    If `_is_named_unroutable` ever returns True for that shape the guard has stopped
    discriminating between "named" and "skipped".
    """
    generic = [f"{_PREFIX_GENERIC_FALLBACK} (all complete or dependencies unresolved)"]
    assert not _is_named_unroutable(None, generic, "merged_acceptance_pending")

    # Unknown statuses remain explicitly named; schema-valid gated statuses use a
    # separate human-acceptance blocker and are never treated as completion.
    move, blockers = _route("quantum_pending")
    assert move is None
    assert _is_named_unroutable(move, blockers, "quantum_pending")


def test_negative_control_future_status_outside_the_schema_is_still_named():
    """The classification is not a hard-coded list of known statuses.

    A status nobody has added to the schema yet must still be named, or the next
    vocabulary slip repeats the original defect.
    """
    move, blockers = _route("quantum_pending")
    assert move is None
    assert _is_named_unroutable(move, blockers, "quantum_pending")


def test_negative_control_active_status_is_routed_not_named():
    """A routable status must be selected, not reported as unroutable.

    Guards against a rewrite that reports every status as unroutable and satisfies
    the invariant vacuously.
    """
    move, blockers = _route("pending")
    assert move is not None
    assert blockers == []


def test_guard_is_selected_and_executed_by_a_workflow():
    """A guard no workflow executes is decoration.

    `weaver/engineering_router.py` is path-filtered out of every other workflow, so
    the weaver-mvp2 gate is the only surface that can judge this seam. The file must
    appear in both filters — a guard absent from the `pull_request` filter is judged
    by nothing until after the merge — and be named in a `run:` step, not merely
    triggered.
    """
    import yaml

    root = Path(__file__).resolve().parents[1]
    text = (root / ".github/workflows/weaver-mvp2-validation.yml").read_text(
        encoding="utf-8"
    )
    workflow = yaml.safe_load(text)
    trigger = workflow.get(True, workflow.get("on"))  # PyYAML parses `on` as True
    assert isinstance(trigger, dict)

    name = "tests/test_router_schema_vocabulary_closure.py"
    for event in ("push", "pull_request"):
        paths = (trigger.get(event) or {}).get("paths") or []
        assert name in paths, f"{event} filter does not select this guard"

    push_paths = (trigger.get("push") or {}).get("paths") or []
    pr_paths = (trigger.get("pull_request") or {}).get("paths") or []
    assert set(push_paths) == set(pr_paths), (
        "push and pull_request filters must be identical, or a PR can introduce a "
        "surface the boundary only judges after merge"
    )

    assert "Engineering-router status truthfulness guard" in text
    step = text.split("Engineering-router status truthfulness guard", 1)[1]
    assert name in step, "the guard step does not execute this file"
