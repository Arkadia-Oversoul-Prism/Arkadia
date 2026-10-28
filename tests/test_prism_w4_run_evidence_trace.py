"""Workstream 4 — run → work-event → evidence trace (backend + projection oracle).

The trace surface (`components/lab/LabRunTrace.tsx` + `labRunTrace.ts`) is a
pure projection of the Lab session view
(``GET /api/lab/engineering/sessions/{id}`` → ``EngineeringLabRuntime.session_view``).
Two things make that claim real, and both are measured here rather than asserted:

1. **The references it joins on are the ones the substrate records.** This file
   drives the *real* runtime over an isolated SQLite database and event log, then
   asserts that the ids the projection joins on (``event.run_id``,
   ``evidence.run_ref``, ``run.evidence_refs``) are exactly the values the
   runtime writes — so the projection cannot be joining on a guessed field.

2. **The projection behaves as claimed.** ``labRunTrace.ts`` is pure and
   dependency-free, so it is *executed* (not read) by the Node runtime and given
   the real session view. Every governance claim — execution != evidence !=
   verification != review != acceptance — is then an observed output, not a
   source-level string match.

Node executes the module directly; if Node is unavailable the projection tests
skip with a stated reason rather than silently passing.

Negative controls prove each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

OWNER = "subject-owner"
OTHER = "subject-other"

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PROJECTION = LAB_SRC / "labRunTrace.ts"


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    """The real runtime + store over an isolated SQLite database and event log."""
    from lab.engineering_lab import store as store_mod
    from lab.engineering_lab.events import EventStream
    from lab.engineering_lab.runtime import EngineeringLabRuntime

    monkeypatch.setattr(store_mod, "_DB_PATH", str(tmp_path / "lab.db"))
    monkeypatch.setattr(store_mod, "_GLOBAL_STORE", None)
    stream = EventStream(log_path=str(tmp_path / "agent_events.jsonl"))
    return EngineeringLabRuntime(store=store_mod.get_store(), stream=stream)


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("# hi\n")
    return root


def _authorized_session(runtime, uid: str = OWNER, role: str = "BUILDER", write: bool = False):
    from lab.engineering_lab.sandbox import SandboxPolicy  # noqa: F401  (documents the contract)

    agent = runtime.register_agent(subject_ref=uid, role=role, write_allowed=write)
    session = runtime.open_session(
        subject_ref=uid, workspace_ref="ws-1", agent_id=agent["agent_id"], objective="trace probe"
    )
    runtime.record_authorization(
        subject_ref=uid, scope_ref=session["session_id"], operations_allowed=("read", "run")
    )
    runtime.transition(session["session_id"], uid, "AUTHORIZED")
    return session


def _execute_read(runtime, session, workspace, uid: str = OWNER) -> dict:
    from lab.engineering_lab.runtime import BoundedOperation, BoundedTask
    from lab.engineering_lab.sandbox import SandboxPolicy

    return runtime.execute_bounded_task(
        subject_ref=uid,
        session_id=session["session_id"],
        task=BoundedTask(
            objective="read the readme",
            operations=(BoundedOperation(kind="read", target="README.md"),),
            acceptance=("reads",),
        ),
        sandbox_policy=SandboxPolicy(root=str(workspace)),
    )


# ---------------------------------------------------------------------------
# The projection is executed, not read
# ---------------------------------------------------------------------------


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(view: dict) -> dict:
    """Execute the real ``labRunTrace.ts`` over *view* and return the ledger.

    Node strips TypeScript types natively, so the module executed here is the
    one that ships to the browser — not a re-implementation of it. The module is
    imported by absolute URL from a ``node -e`` program rather than through a
    generated driver file, so nothing is written into the source tree.
    """
    node = _node()
    url = PROJECTION.as_uri()
    program = (
        f"const m = await import({json.dumps(url)});\n"
        "const view = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify(m.buildRunTrace(view)));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(view)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# The references are the ones the substrate records
# ---------------------------------------------------------------------------

def test_run_id_is_the_field_events_and_evidence_reference(runtime, workspace):
    """The joins the projection performs must be on fields the substrate writes.

    A new session carries one ``SESSION_CREATED`` event with ``run_id`` unset; an
    executed run's events carry its ``run_id`` and its evidence carries
    ``run_ref == run_id``. If any of these changed, the projection would silently
    report zero links for a session that has them.
    """
    session = _authorized_session(runtime)
    sid = session["session_id"]
    result = _execute_read(runtime, session, workspace)
    run_id = result["run_id"]

    view = runtime.session_view(sid, OWNER)
    (run,) = view["runs"]
    assert run["run_id"] == run_id

    # Events: session-scoped ones carry no run_id; the run's own carry it exactly.
    session_events = [e for e in view["events"] if not e.get("run_id")]
    run_events = [e for e in view["events"] if e.get("run_id") == run_id]
    assert "SESSION_CREATED" in [e["event_type"] for e in session_events]
    assert {e["event_type"] for e in session_events} <= {"SESSION_CREATED", "SESSION_TRANSITION"}
    assert run_events, "the run's own work events must carry its run_id"
    assert {e["run_id"] for e in run_events} == {run_id}

    # Evidence: joined by run_ref, and named by the run's own evidence_refs.
    (evidence,) = view["evidence"]
    assert evidence["run_ref"] == run_id
    assert evidence["evidence_id"] in run["evidence_refs"]


def test_projection_joins_a_real_session_view(runtime, workspace):
    """Executed end to end: the ledger must show the run, its events, its
    evidence, and the reference sets the substrate actually recorded."""
    session = _authorized_session(runtime)
    sid = session["session_id"]
    result = _execute_read(runtime, session, workspace)
    run_id = result["run_id"]

    ledger = run_projection(runtime.session_view(sid, OWNER))

    (trace,) = ledger["runs"]
    assert trace["run_id"] == run_id
    assert trace["events"], "the run's work events must be linked"
    assert [e["evidence_id"] for e in trace["evidence"]] == [result["evidence_refs"][0]]
    assert trace["dangling_evidence_refs"] == []
    assert trace["unreferenced_evidence_ids"] == []
    # The session's own creation event is recorded work, not a run's work.
    session_event_types = [e["event_type"] for e in ledger["session_events"]]
    assert "SESSION_CREATED" in session_event_types
    assert all(e["run_id"] in (None, "") for e in ledger["session_events"])
    assert ledger["unlinked_events"] == []
    assert ledger["unlinked_evidence"] == []


def test_proposed_session_has_an_empty_trace(runtime):
    """An authorized-but-unexecuted session has no runs, so there is nothing to
    trace. The projection must not invent a run from the session event."""
    session = _authorized_session(runtime)
    ledger = run_projection(runtime.session_view(session["session_id"], OWNER))
    assert ledger["runs"] == []
    # The session's own creation/transition events are recorded work with no run.
    types = [e["event_type"] for e in ledger["session_events"]]
    assert "SESSION_CREATED" in types
    assert all(e["run_id"] in (None, "") for e in ledger["session_events"])


# ---------------------------------------------------------------------------
# The state boundaries the trace exists to preserve
# ---------------------------------------------------------------------------

def test_evidence_without_verification_is_reported(runtime, workspace):
    """A successful bounded run records ``VERIFYING`` while its evidence state
    stays ``IMPLEMENTED``. The projection must report the stage as entered and
    the verification as *not asserted* — the substrate's own
    ``IMPLEMENTED != VERIFIED`` boundary."""
    session = _authorized_session(runtime)
    result = _execute_read(runtime, session, workspace)
    view = runtime.session_view(session["session_id"], OWNER)
    (evidence,) = view["evidence"]
    assert evidence["state"] == "IMPLEMENTED", "control premise: the run did not assert VERIFIED"

    ledger = run_projection(view)
    (trace,) = ledger["runs"]
    assert trace["verification"]["stage_entered"] is True
    assert trace["verification"]["asserted"] is False
    assert ledger["evidence_without_verification"] == [result["run_id"]]
    assert ledger["evidence_with_verification"] == []


def test_review_boundary_is_not_acceptance(runtime, workspace):
    """The run stops at the review boundary; the session never self-completes.
    The projection must read acceptance as NOT_RECORDED."""
    session = _authorized_session(runtime)
    _execute_read(runtime, session, workspace)
    view = runtime.session_view(session["session_id"], OWNER)
    assert view["session"]["state"] == "READY_FOR_REVIEW"

    ledger = run_projection(view)
    assert ledger["review_boundary"] is True
    assert ledger["acceptance"]["state"] == "NOT_RECORDED"
    assert ledger["acceptance"]["basis"] == []
    assert ledger["runs"][0]["review"]["at_boundary"] is True


def test_authorization_alone_produces_no_run_and_no_evidence(runtime):
    """A recorded authorization is not an execution: the trace stays empty and
    acceptance stays NOT_RECORDED."""
    session = _authorized_session(runtime)
    view = runtime.session_view(session["session_id"], OWNER)
    assert view["session"]["state"] == "AUTHORIZED"
    ledger = run_projection(view)
    assert ledger["runs"] == []
    assert ledger["acceptance"]["state"] == "NOT_RECORDED"


# ---------------------------------------------------------------------------
# Missing / partial links, owner isolation, duplicates
# ---------------------------------------------------------------------------

def test_owner_isolation_the_projection_never_sees_another_subject(runtime, workspace):
    """Owner scoping is enforced by the runtime; the projection receives only
    what the handler returns. Another subject's view must not be reachable."""
    session = _authorized_session(runtime, OWNER)
    _execute_read(runtime, session, workspace, OWNER)
    with pytest.raises(KeyError):
        runtime.session_view(session["session_id"], OTHER)


def test_missing_run_link_is_reported_not_dropped():
    """A declared ``evidence_ref`` with no matching record, an event naming an
    absent run, and evidence naming an absent run must all be reported."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [
                {
                    "run_id": "RUN-1",
                    "state": "VERIFYING",
                    "result_state": "IMPLEMENTED",
                    "evidence_refs": ["EVD-missing", "EVD-1"],
                }
            ],
            "events": [
                {"event_id": "AEV-1", "run_id": "RUN-1", "event_type": "RUN_STARTED", "sequence": 1},
                {"event_id": "AEV-2", "run_id": "RUN-ghost", "event_type": "RUN_FINISHED", "sequence": 2},
                {"event_id": "AEV-3", "event_type": "SESSION_CREATED", "sequence": 3},
            ],
            "evidence": [
                {"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"},
                {"evidence_id": "EVD-2", "run_ref": "RUN-ghost", "state": "IMPLEMENTED"},
            ],
        }
    )
    (trace,) = ledger["runs"]
    assert trace["dangling_evidence_refs"] == ["EVD-missing"]
    assert [e["event_id"] for e in ledger["unlinked_events"]] == ["AEV-2"]
    assert [e["evidence_id"] for e in ledger["unlinked_evidence"]] == ["EVD-2"]
    assert [e["event_id"] for e in ledger["session_events"]] == ["AEV-3"]
    assert any("do not resolve" in line for line in ledger["unresolved"])


def test_partial_link_run_ref_and_evidence_refs_disagree():
    """The two ways a run and its evidence can be linked are independent fields.
    Evidence present under ``run_ref`` but absent from ``evidence_refs`` must be
    reported as a partial link, not silently accepted as agreement."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": []}],
            "events": [],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"}],
        }
    )
    (trace,) = ledger["runs"]
    assert trace["unreferenced_evidence_ids"] == ["EVD-1"]
    assert trace["dangling_evidence_refs"] == []
    assert trace["evidence"][0]["evidence_id"] == "EVD-1"


def test_unattributed_evidence_is_reported():
    """Evidence with no ``run_ref`` cannot be traced to a run at all."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": []}],
            "events": [],
            "evidence": [{"evidence_id": "EVD-orphan", "state": "IMPLEMENTED"}],
        }
    )
    assert [e["evidence_id"] for e in ledger["unattributed_evidence"]] == ["EVD-orphan"]
    assert ledger["runs"][0]["evidence"] == []
    assert any("no run reference" in line for line in ledger["unresolved"])


def test_the_handler_filters_orphan_evidence_before_the_projection_sees_it(runtime):
    """The evidence doc claims orphan evidence "cannot normally appear" because
    ``session_view`` filters it. That claim is measured here against the real
    handler rather than restated.

    An evidence record whose ``run_ref`` names no run is written straight to the
    store. The handler must not return it — which is exactly why the projection's
    ``unlinked_evidence`` classification is only reachable from a view the
    handler did not produce. If the filter is ever removed, this test reddens and
    the projection's classification stops being hypothetical.
    """
    from lab.engineering_lab.contracts import EvidenceRecord

    session = _authorized_session(runtime)
    store = runtime._store
    store.save_evidence(
        EvidenceRecord(
            evidence_id="EVD-orphan",
            subject_ref=OWNER,
            workspace_ref="ws-1",
            run_ref="RUN-does-not-exist",
            state="IMPLEMENTED",
            summary="evidence naming no run in this session",
            detail={},
            timestamp_utc="2026-01-01T00:00:00+00:00",
            provenance={},
        )
    )

    view = runtime.session_view(session["session_id"], OWNER)
    assert [e["evidence_id"] for e in view["evidence"]] == []

    # The record exists in the store — it was dropped by the filter, not absent.
    assert any(
        e["evidence_id"] == "EVD-orphan"
        for e in runtime._store.list_evidence(OWNER)
    )

    # And the projection, given that real view, reports nothing unresolved: it
    # cannot see what the handler withheld. The classification is therefore a
    # forward guard, not a live reading — stated rather than implied.
    ledger = run_projection(view)
    assert ledger["unlinked_evidence"] == []
    assert ledger["unattributed_evidence"] == []


def test_duplicate_evidence_is_deduplicated_and_reported():
    """A repeated evidence id must not be counted twice as two records, and the
    duplication must be visible rather than absorbed."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": ["EVD-1"]}],
            "events": [],
            "evidence": [
                {"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"},
                {"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"},
            ],
        }
    )
    assert ledger["duplicate_evidence_ids"] == ["EVD-1"]
    assert len(ledger["runs"][0]["evidence"]) == 1
    assert any("duplicate evidence id" in line for line in ledger["unresolved"])


def test_a_view_missing_record_classes_does_not_throw():
    """A partial view degrades to an empty ledger with a stated reason rather
    than raising into the render path."""
    ledger = run_projection({"session": {"session_id": "SES-1", "state": "PROPOSED"}})
    assert ledger["runs"] == []
    assert ledger["acceptance"]["state"] == "NOT_RECORDED"


# ---------------------------------------------------------------------------
# Acceptance is read only from the human terminal state
# ---------------------------------------------------------------------------

def test_acceptance_is_read_only_from_the_human_terminal_state():
    """Only the human terminal state produces HUMAN_ACCEPTED; every other
    recorded state, including the review boundary, reads NOT_RECORDED."""
    for state in ("PROPOSED", "AUTHORIZED", "RUNNING", "CHECKPOINTED", "VERIFYING", "READY_FOR_REVIEW"):
        ledger = run_projection({"session": {"session_id": "SES-1", "state": state}, "runs": [], "events": [], "evidence": []})
        assert ledger["acceptance"]["state"] == "NOT_RECORDED", state
        assert ledger["acceptance"]["basis"] == [], state

    accepted = run_projection({"session": {"session_id": "SES-1", "state": "COMPLETED"}, "runs": [], "events": [], "evidence": []})
    assert accepted["acceptance"]["state"] == "HUMAN_ACCEPTED"
    assert accepted["acceptance"]["basis"] == ["session.state=COMPLETED"]


def test_the_human_terminal_state_is_the_substrate_s_vocabulary():
    """The state the projection reads as acceptance must be the Lab's own
    ``HUMAN_TERMINAL_STATES`` member, not a value invented by the console."""
    from lab.engineering_lab import contracts

    assert contracts.HUMAN_TERMINAL_STATES == frozenset({"COMPLETED"})
    source = PROJECTION.read_text(encoding="utf-8")
    assert 'HUMAN_ACCEPTED_SESSION_STATES: readonly string[] = ["COMPLETED"]' in source


def test_verified_evidence_state_is_the_substrate_s_result_state():
    """``VERIFIED`` must be one of the Lab's own ``RESULT_STATES``."""
    from lab.engineering_lab import contracts

    assert "VERIFIED" in contracts.RESULT_STATES
    assert "IMPLEMENTED" in contracts.RESULT_STATES


# ---------------------------------------------------------------------------
# Negative controls — each detector must flag the defect it exists to catch
# ---------------------------------------------------------------------------

def test_negative_control_acceptance_detector_flags_a_fabricated_acceptance():
    """The detector must report acceptance it should not infer. A run at the
    review boundary, and evidence marked VERIFIED, must not become acceptance."""
    fabricated = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "READY_FOR_REVIEW"},
            "runs": [{"run_id": "RUN-1", "state": "READY_FOR_REVIEW", "evidence_refs": ["EVD-1"]}],
            "events": [],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "VERIFIED"}],
        }
    )
    assert fabricated["acceptance"]["state"] == "NOT_RECORDED"
    assert fabricated["acceptance"]["basis"] == []
    assert fabricated["evidence_with_verification"] == ["RUN-1"]
    assert fabricated["evidence_without_verification"] == []


def test_negative_control_link_detector_sees_a_clean_view_as_clean():
    """A fully-resolving view must not be reported as unresolved — otherwise the
    detector is trivially true and proves nothing."""
    clean = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "READY_FOR_REVIEW", "reached_review_boundary": True},
            "runs": [{"run_id": "RUN-1", "state": "READY_FOR_REVIEW", "evidence_refs": ["EVD-1"]}],
            "events": [{"event_id": "AEV-1", "run_id": "RUN-1", "event_type": "RUN_STARTED", "sequence": 1}],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"}],
        }
    )
    assert clean["unresolved"] == ["Every recorded reference in this view resolves."]
    assert clean["runs"][0]["dangling_evidence_refs"] == []


def test_negative_control_verification_detector_flags_an_inflated_verification():
    """If a view records evidence as VERIFIED, the detector must say so — proving
    the ``asserted`` reading is not hardcoded false."""
    inflated = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": ["EVD-1"]}],
            "events": [],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "VERIFIED"}],
        }
    )
    (trace,) = inflated["runs"]
    assert trace["verification"]["asserted"] is True
    assert trace["verification"]["asserted_basis"] == ["evidence.state=VERIFIED (EVD-1)"]


# ---------------------------------------------------------------------------
# run → artifact: the captured proposal is joined, and is not evidence
# ---------------------------------------------------------------------------


def _execute_write(runtime, session, workspace, uid: str = OWNER) -> dict:
    """A bounded write run — the only run kind that captures an artifact."""
    from lab.engineering_lab.runtime import BoundedOperation, BoundedTask
    from lab.engineering_lab.sandbox import SandboxPolicy

    return runtime.execute_bounded_task(
        subject_ref=uid,
        session_id=session["session_id"],
        task=BoundedTask(
            objective="prepare a change set",
            operations=(BoundedOperation(kind="write", target="out.txt", content="hi"),),
            acceptance=("prepared",),
            requires_write=True,
        ),
        sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
    )


def test_run_id_is_the_field_artifacts_reference(runtime, workspace):
    """The artifact join must be on a field the substrate writes.

    ``_capture_artifact`` records ``run_id`` on the artifact and the run records
    the artifact id in its own ``artifact_refs``. If either changed, the
    projection would report zero artifact links for a run that has one.
    """
    session = _authorized_session(runtime, role="BUILDER", write=True)
    sid = session["session_id"]
    result = _execute_write(runtime, session, workspace)
    run_id = result["run_id"]

    view = runtime.session_view(sid, OWNER)
    (run,) = view["runs"]
    (artifact,) = view["artifacts"]
    assert artifact["run_id"] == run_id
    assert artifact["artifact_id"] in run["artifact_refs"]


def test_projection_joins_a_real_artifact(runtime, workspace):
    """Executed end to end: a write run's artifact appears under its run, with
    the reference sets the substrate actually recorded."""
    session = _authorized_session(runtime, role="BUILDER", write=True)
    sid = session["session_id"]
    result = _execute_write(runtime, session, workspace)
    run_id = result["run_id"]

    ledger = run_projection(runtime.session_view(sid, OWNER))

    (trace,) = ledger["runs"]
    assert trace["run_id"] == run_id
    assert [a["artifact_id"] for a in trace["artifacts"]] == result["artifact_refs"]
    assert trace["dangling_artifact_refs"] == []
    assert trace["unreferenced_artifact_ids"] == []
    assert ledger["unlinked_artifacts"] == []
    assert ledger["unattributed_artifacts"] == []
    assert ledger["unresolved"] == ["Every recorded reference in this view resolves."]


def test_artifact_is_a_captured_proposal_not_evidence_or_verification(runtime, workspace):
    """The non-collapse the artifact join must preserve: an artifact is not an
    evidence record, and its presence asserts nothing about verification."""
    session = _authorized_session(runtime, role="BUILDER", write=True)
    result = _execute_write(runtime, session, workspace)
    ledger = run_projection(runtime.session_view(session["session_id"], OWNER))

    (trace,) = ledger["runs"]
    assert trace["artifacts"], "control premise: the write run captured an artifact"
    assert trace["artifacts"][0]["artifact_id"] not in [
        e["evidence_id"] for e in trace["evidence"]
    ]
    assert trace["verification"]["asserted"] is False
    assert ledger["acceptance"]["state"] == "NOT_RECORDED"


def test_read_run_captures_no_artifact(runtime, workspace):
    """A read run prepares nothing, so it captures no artifact. The projection
    must report an empty artifact list rather than infer one from the run."""
    session = _authorized_session(runtime)
    result = _execute_read(runtime, session, workspace)
    assert result["artifact_refs"] == [], "control premise: a read run captures nothing"

    ledger = run_projection(runtime.session_view(session["session_id"], OWNER))
    (trace,) = ledger["runs"]
    assert trace["artifacts"] == []
    assert trace["dangling_artifact_refs"] == []


def test_authorization_alone_produces_no_artifact(runtime):
    """Negative control: a recorded authorization is not a capture. No run means
    no artifact, and the trace stays empty."""
    session = _authorized_session(runtime, role="BUILDER", write=True)
    view = runtime.session_view(session["session_id"], OWNER)
    assert view["artifacts"] == [], "control premise: authorization alone captures nothing"
    ledger = run_projection(view)
    assert ledger["runs"] == []
    assert ledger["unlinked_artifacts"] == []
    assert ledger["unattributed_artifacts"] == []


def test_missing_artifact_link_is_reported_not_dropped():
    """A declared ``artifact_ref`` with no matching artifact, an artifact naming
    an absent run, and an artifact with no ``run_id`` must all be reported."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [
                {
                    "run_id": "RUN-1",
                    "state": "VERIFYING",
                    "evidence_refs": [],
                    "artifact_refs": ["ART-missing", "ART-1"],
                }
            ],
            "events": [],
            "evidence": [],
            "artifacts": [
                {"artifact_id": "ART-1", "run_id": "RUN-1", "kind": "diff"},
                {"artifact_id": "ART-2", "run_id": "RUN-ghost", "kind": "diff"},
                {"artifact_id": "ART-3", "kind": "diff"},
            ],
        }
    )
    (trace,) = ledger["runs"]
    assert trace["dangling_artifact_refs"] == ["ART-missing"]
    assert [a["artifact_id"] for a in ledger["unlinked_artifacts"]] == ["ART-2"]
    assert [a["artifact_id"] for a in ledger["unattributed_artifacts"]] == ["ART-3"]
    assert any("artifact reference(s) do not resolve" in line for line in ledger["unresolved"])


def test_partial_link_artifact_run_id_and_artifact_refs_disagree():
    """The two ways a run and its artifact can be linked are independent fields.
    An artifact present under ``run_id`` but absent from ``artifact_refs`` must be
    reported as a partial link, not silently accepted as agreement."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": [], "artifact_refs": []}],
            "events": [],
            "evidence": [],
            "artifacts": [{"artifact_id": "ART-1", "run_id": "RUN-1", "kind": "diff"}],
        }
    )
    (trace,) = ledger["runs"]
    assert trace["unreferenced_artifact_ids"] == ["ART-1"]
    assert trace["dangling_artifact_refs"] == []
    assert trace["artifacts"][0]["artifact_id"] == "ART-1"


def test_negative_control_artifact_detector_flags_a_ghost_artifact():
    """The artifact detector must fire on an artifact naming an absent run, or it
    is trivially true. This is the same view the evidence detector is proved on,
    with the artifact analogue."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": [], "artifact_refs": []}],
            "events": [],
            "evidence": [],
            "artifacts": [{"artifact_id": "ART-ghost", "run_id": "RUN-absent", "kind": "diff"}],
        }
    )
    assert [a["artifact_id"] for a in ledger["unlinked_artifacts"]] == ["ART-ghost"]
    assert any("name a run not in this view" in line for line in ledger["unresolved"])


def test_negative_control_artifact_link_detector_sees_a_clean_view_as_clean():
    """A fully-resolving view that includes an artifact must not be reported as
    unresolved — otherwise adding the join would make every view look broken."""
    clean = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "READY_FOR_REVIEW"},
            "runs": [
                {
                    "run_id": "RUN-1",
                    "state": "READY_FOR_REVIEW",
                    "evidence_refs": ["EVD-1"],
                    "artifact_refs": ["ART-1"],
                }
            ],
            "events": [],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"}],
            "artifacts": [{"artifact_id": "ART-1", "run_id": "RUN-1", "kind": "diff"}],
        }
    )
    assert clean["unresolved"] == ["Every recorded reference in this view resolves."]
    assert clean["runs"][0]["artifacts"][0]["artifact_id"] == "ART-1"


def test_a_view_without_artifacts_is_unchanged_by_the_artifact_join():
    """Backward compatibility: a view that carries no ``artifacts`` key (the shape
    every pre-existing caller sends) must project exactly as before — empty
    artifact lists and no new unresolved line."""
    ledger = run_projection(
        {
            "session": {"session_id": "SES-1", "state": "VERIFYING"},
            "runs": [{"run_id": "RUN-1", "state": "VERIFYING", "evidence_refs": ["EVD-1"]}],
            "events": [],
            "evidence": [{"evidence_id": "EVD-1", "run_ref": "RUN-1", "state": "IMPLEMENTED"}],
        }
    )
    (trace,) = ledger["runs"]
    assert trace["artifacts"] == []
    assert trace["dangling_artifact_refs"] == []
    assert trace["unreferenced_artifact_ids"] == []
    assert ledger["unlinked_artifacts"] == []
    assert ledger["unattributed_artifacts"] == []
    assert ledger["unresolved"] == ["Every recorded reference in this view resolves."]

