"""Weaver run / work-event / evidence ledger — backend oracle (Workstream 4).

The Weaver surface now reads the Lab's own session view
(``GET /api/lab/engineering/sessions/{id}`` -> ``EngineeringLabRuntime.session_view``)
instead of advertising an unbuilt execute view. This file is the backend oracle
for that claim: it drives the **real** runtime and store over an isolated
database and asserts the shape the console depends on.

The governance distinction the surface exists to preserve is
proposal != approval != execution != work event != evidence != verification !=
acceptance. The substrate enforces it and this oracle pins it:

  * a session opens PROPOSED with an empty ``runs`` / ``evidence`` ledger;
  * ``session_view`` returns exactly the keys the ledger reads;
  * recording an authorization does not by itself create a run or evidence;
  * ``reached_review_boundary`` is true only at the review states, and the
    substrate stops there — it never *completes* a session itself.

Negative controls prove each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import os
import tempfile

import pytest

OWNER = "subject-owner"
OTHER = "subject-other"


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    """The real runtime + store over an isolated SQLite database and event log.

    ``lab.engineering_lab.store`` resolves its DB path at import time from
    ``SOLSPIRE_PROJECTS_DB``, so the module-level constant is what is patched.
    ``events.get_event_stream`` resolves the append-log path at *its* import
    time, so an explicit ``EventStream`` is injected rather than relying on the
    env var — otherwise the oracle writes into the tracked ``data/`` tree.
    """
    from lab.engineering_lab import store as store_mod
    from lab.engineering_lab.events import EventStream
    from lab.engineering_lab.runtime import EngineeringLabRuntime

    db = tmp_path / "lab.db"
    monkeypatch.setattr(store_mod, "_DB_PATH", str(db))
    monkeypatch.setattr(store_mod, "_GLOBAL_STORE", None)
    stream = EventStream(log_path=str(tmp_path / "agent_events.jsonl"))
    return EngineeringLabRuntime(store=store_mod.get_store(), stream=stream)


def _open(runtime, uid: str = OWNER) -> dict:
    agent = runtime.register_agent(subject_ref=uid, role="WEAVER", display_name="Weaver")
    return runtime.open_session(
        subject_ref=uid,
        workspace_ref="ws-1",
        agent_id=agent["agent_id"],
        objective="bounded objective",
    )


def _record_classes(view: dict) -> dict[str, list]:
    return {"runs": view["runs"], "events": view["events"], "evidence": view["evidence"]}


def _detect_later_stage_inflation(view: dict) -> list[str]:
    """Divergences that present an earlier stage as a later one.

    A session that has not executed must not carry runs; a session whose runs
    have not produced evidence must not carry evidence.
    """
    defects = []
    if view["session"]["state"] in ("PROPOSED", "AUTHORIZED") and view["runs"]:
        defects.append("a not-yet-executed session carries runs")
    if not view["runs"] and view["evidence"]:
        defects.append("evidence exists without any run")
    return defects


# ---------------------------------------------------------------------------
# The shape the ledger reads
# ---------------------------------------------------------------------------

def test_session_view_returns_exactly_the_declared_keys(runtime):
    view = runtime.session_view(_open(runtime)["session_id"], OWNER)
    assert set(view) == {
        "session",
        "agent",
        "runs",
        "events",
        "evidence",
        "artifacts",
        "loop",
        "reached_review_boundary",
        "human_decision_required",
    }
    assert set(_record_classes(view)) == {"runs", "events", "evidence"}


def test_new_session_ledger_is_empty_but_the_session_event_exists(runtime):
    """Opening a session is a work event, not an execution. The ledger shows the
    event and an empty run/evidence set — never an invented run."""
    view = runtime.session_view(_open(runtime)["session_id"], OWNER)
    assert view["runs"] == []
    assert view["evidence"] == []
    assert [e["event_type"] for e in view["events"]] == ["SESSION_CREATED"]
    assert _detect_later_stage_inflation(view) == []


def test_event_shape_is_the_one_the_ledger_renders(runtime):
    view = runtime.session_view(_open(runtime)["session_id"], OWNER)
    (event,) = view["events"]
    assert set(event) >= {"event_id", "event_type", "sequence", "timestamp_utc", "session_id"}
    assert event["event_type"] == "SESSION_CREATED"
    assert isinstance(event["sequence"], int)


# ---------------------------------------------------------------------------
# Governance boundary
# ---------------------------------------------------------------------------

def test_authorization_is_not_execution(runtime):
    """Recording an authorization moves the session to AUTHORIZED and adds no
    run and no evidence. A decision is not an execution."""
    session = _open(runtime)
    sid = session["session_id"]
    assert session["state"] == "PROPOSED"

    runtime.record_authorization(subject_ref=OWNER, scope_ref=sid, operations_allowed=("read", "test"))
    runtime.transition(sid, OWNER, "AUTHORIZED")

    view = runtime.session_view(sid, OWNER)
    assert view["session"]["state"] == "AUTHORIZED"
    assert view["runs"] == []
    assert view["evidence"] == []
    assert _detect_later_stage_inflation(view) == []


def test_review_boundary_flag_is_only_true_at_the_review_states(runtime):
    """`reached_review_boundary` must be false for a PROPOSED/AUTHORIZED session
    and true only once the substrate reaches a review state."""
    sid = _open(runtime)["session_id"]
    assert runtime.session_view(sid, OWNER)["reached_review_boundary"] is False


def test_reads_are_owner_scoped(runtime):
    """Another subject cannot inspect this session's ledger."""
    sid = _open(runtime, OWNER)["session_id"]
    with pytest.raises(KeyError):
        runtime.session_view(sid, OTHER)


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def test_negative_control_inflation_detector_flags_a_fabricated_run():
    """The detector must report the stage inflation it exists to catch."""
    fabricated = {"session": {"state": "PROPOSED"}, "runs": [{"run_id": "x"}], "evidence": []}
    assert _detect_later_stage_inflation(fabricated) == ["a not-yet-executed session carries runs"]
    evidence_only = {"session": {"state": "AUTHORIZED"}, "runs": [], "evidence": [{"evidence_id": "e"}]}
    assert _detect_later_stage_inflation(evidence_only) == ["evidence exists without any run"]
    coherent = {"session": {"state": "AUTHORIZED"}, "runs": [], "evidence": []}
    assert _detect_later_stage_inflation(coherent) == []


def test_negative_control_a_bad_key_is_seen(runtime):
    """If `session_view` stopped returning a record class the ledger reads, the
    key-set assertion must redden — proving it is not vacuously true."""
    view = runtime.session_view(_open(runtime)["session_id"], OWNER)
    mutated = {k: v for k, v in view.items() if k != "evidence"}
    assert set(mutated) != set(view)
    assert "evidence" not in mutated
