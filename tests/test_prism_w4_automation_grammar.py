"""Workstream 4 — automation grammar projection, executed behaviour.

``tests/test_lab_automation_grammar_contract.py`` pins the *vocabulary* the
surface renders against the substrate. This file executes the real
``labAutomationGrammar.ts`` — not a re-implementation of it — over payloads
shaped like the served contract, so the projection's behaviour is measured
rather than read.

The governance distinctions under test are the ones the substrate declares in
``automations.grammar_view()``: an automation *prepares* consequential actions
(``may_prepare_consequential_action: true``) and may **never** authorize them
(``may_authorize_consequential_action: false``, ``final_transition: "HUMAN_GATE"``).
The projection must render that truthfully and report any contrary claim as a
boundary violation rather than as ordinary state.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = (
    ROOT / "web" / "arkadia_console" / "src" / "components" / "lab" / "labAutomationGrammar.ts"
)

GRAMMAR = [
    "TRIGGER",
    "AGENT",
    "TOOLS",
    "SANDBOX",
    "OUTPUT",
    "EVIDENCE",
    "NOTIFICATION",
    "HUMAN_GATE",
]

STATES = [
    "DRAFT",
    "ENABLED",
    "RUNNING",
    "OBSERVED",
    "COMPLETED",
    "FAILED",
    "AWAITING_HUMAN_ACTION",
]


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(payload: dict) -> dict:
    """Execute the real projection over *payload* and return the ledger.

    Node strips TypeScript types natively, so the module executed here is the one
    that ships to the browser. It is imported by absolute URL from a ``node -e``
    program rather than through a generated driver file, so nothing is written
    into the source tree.
    """
    node = _node()
    url = PROJECTION.as_uri()
    program = (
        f"const m = await import({json.dumps(url)});\n"
        "const payload = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify(m.buildAutomationLedger(payload)));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


def served_grammar() -> dict:
    return {
        "grammar": GRAMMAR,
        "states": STATES,
        "trigger_kinds": [
            "scheduled",
            "repository_event",
            "pr_event",
            "runtime_health",
            "manual",
            "external_event",
        ],
        "may_prepare_consequential_action": True,
        "may_authorize_consequential_action": False,
        "final_transition": "HUMAN_GATE",
    }


def record(**overrides) -> dict:
    base = {
        "automation_id": "AUT-abc123",
        "subject_ref": "owner-uid",
        "name": "Nightly reconciliation",
        "state": "DRAFT",
        "trigger": {"kind": "scheduled", "detail": "", "schedule": "0 2 * * *", "event": None},
        "agent_role": "weaver",
        "objective": "reconcile repository truth with runtime state",
        "tools": ["git", "pytest"],
        "sandbox_write_allowed": False,
        "notification_target": "glance",
        "created_at": "2026-10-12T00:00:00+00:00",
        "updated_at": "2026-10-12T00:00:00+00:00",
        "schema_version": "1",
        "grammar": GRAMMAR,
        "may_authorize": False,
        "human_gate_required": True,
    }
    base.update(overrides)
    return base


def payload(*records: dict, grammar: dict | None = None) -> dict:
    return {"automations": list(records), "grammar": grammar or served_grammar()}


# ---------------------------------------------------------------------------
# The chain is read from the payload, not restated
# ---------------------------------------------------------------------------


def test_declared_grammar_is_the_served_chain():
    ledger = run_projection(payload(record()))
    assert ledger["declared_grammar"] == GRAMMAR
    assert ledger["grammar_matches"] is True
    assert ledger["boundary_violations"] == []


def test_rendered_chain_matches_every_served_clause():
    ledger = run_projection(payload(record()))
    rendered = [c["clause"] for c in ledger["automations"][0]["clauses"]]
    assert rendered == GRAMMAR


def test_served_state_vocabulary_is_carried_through():
    ledger = run_projection(payload(record()))
    assert ledger["declared_states"] == STATES


# ---------------------------------------------------------------------------
# Clause filling is read from the record, never assumed
# ---------------------------------------------------------------------------


def test_a_fully_declared_record_fills_every_clause_it_can_carry():
    ledger = run_projection(payload(record()))
    (reading,) = ledger["automations"]
    filled = {c["clause"] for c in reading["clauses"] if c["filled"]}
    assert filled == set(GRAMMAR) - {"EVIDENCE"}


def test_evidence_clause_is_unfilled_because_a_run_produces_it():
    ledger = run_projection(payload(record()))
    (reading,) = ledger["automations"]
    evidence = next(c for c in reading["clauses"] if c["clause"] == "EVIDENCE")
    assert evidence["filled"] is False
    assert "produced by a run" in evidence["note"]
    assert "EVIDENCE" in reading["unfilled_clauses"]


def test_a_completed_state_does_not_fill_the_evidence_clause():
    """A definition in a terminal state still declares no evidence.

    This is the collapse the substrate forbids: a completed-looking state is not
    an evidence record, and the projection must not infer one from it.
    """
    ledger = run_projection(payload(record(state="COMPLETED")))
    (reading,) = ledger["automations"]
    evidence = next(c for c in reading["clauses"] if c["clause"] == "EVIDENCE")
    assert evidence["filled"] is False
    assert reading["state"]["terminal"] is True
    assert "EVIDENCE" in reading["unfilled_clauses"]


def test_a_scheduled_trigger_without_a_schedule_stays_unfilled():
    ledger = run_projection(
        payload(record(trigger={"kind": "scheduled", "detail": "", "schedule": None, "event": None}))
    )
    (reading,) = ledger["automations"]
    trigger = next(c for c in reading["clauses"] if c["clause"] == "TRIGGER")
    assert trigger["filled"] is False
    assert "TRIGGER" in reading["unfilled_clauses"]


def test_an_event_trigger_without_an_event_key_stays_unfilled():
    ledger = run_projection(
        payload(record(trigger={"kind": "pr_event", "detail": "", "schedule": None, "event": None}))
    )
    (reading,) = ledger["automations"]
    trigger = next(c for c in reading["clauses"] if c["clause"] == "TRIGGER")
    assert trigger["filled"] is False


def test_an_event_trigger_with_an_event_key_is_filled():
    ledger = run_projection(
        payload(record(trigger={"kind": "pr_event", "detail": "", "schedule": None, "event": "pull_request.opened"}))
    )
    (reading,) = ledger["automations"]
    trigger = next(c for c in reading["clauses"] if c["clause"] == "TRIGGER")
    assert trigger["filled"] is True


def test_a_manual_trigger_needs_neither_schedule_nor_event():
    ledger = run_projection(
        payload(record(trigger={"kind": "manual", "detail": "human initiated", "schedule": None, "event": None}))
    )
    (reading,) = ledger["automations"]
    trigger = next(c for c in reading["clauses"] if c["clause"] == "TRIGGER")
    assert trigger["filled"] is True


def test_a_record_missing_the_human_gate_does_not_assert_it():
    """The gate clause is filled only when the record asserts it."""
    ledger = run_projection(payload(record(human_gate_required=False)))
    (reading,) = ledger["automations"]
    gate = next(c for c in reading["clauses"] if c["clause"] == "HUMAN_GATE")
    assert gate["filled"] is False
    assert "HUMAN_GATE" in reading["unfilled_clauses"]


# ---------------------------------------------------------------------------
# The authority boundary
# ---------------------------------------------------------------------------


def test_a_record_claiming_authority_is_a_boundary_violation():
    """The substrate forbids ``may_authorize``; a claim of it is not state."""
    ledger = run_projection(payload(record(may_authorize=True)))
    assert ledger["automations"][0]["authorization"]["violation"] is True
    assert any("may_authorize=true" in v for v in ledger["boundary_violations"])


def test_a_record_claiming_no_authority_is_not_a_violation():
    ledger = run_projection(payload(record(may_authorize=False)))
    assert ledger["automations"][0]["authorization"]["violation"] is False
    assert ledger["boundary_violations"] == []


def test_a_grammar_declaring_a_non_human_final_transition_is_a_violation():
    grammar = served_grammar()
    grammar["final_transition"] = "AUTO_MERGE"
    ledger = run_projection(payload(record(), grammar=grammar))
    assert ledger["final_transition"] == "AUTO_MERGE"
    assert any("not the human gate" in v for v in ledger["boundary_violations"])


def test_a_grammar_claiming_authority_is_a_violation():
    grammar = served_grammar()
    grammar["may_authorize_consequential_action"] = True
    ledger = run_projection(payload(record(), grammar=grammar))
    assert any("authorize a consequential action" in v for v in ledger["boundary_violations"])


def test_a_reordered_grammar_chain_is_reported_not_reconciled():
    grammar = served_grammar()
    grammar["grammar"] = ["AGENT", "TRIGGER"] + GRAMMAR[2:]
    ledger = run_projection(payload(record(), grammar=grammar))
    assert ledger["grammar_matches"] is False
    assert any("not the rendered chain" in v for v in ledger["boundary_violations"])


# ---------------------------------------------------------------------------
# State readings
# ---------------------------------------------------------------------------


def test_the_human_gated_states_are_read_as_human_gated():
    for state in ("AWAITING_HUMAN_ACTION", "COMPLETED"):
        ledger = run_projection(payload(record(state=state)))
        reading = ledger["automations"][0]["state"]
        assert reading["human_gated"] is True, state


def test_a_working_state_is_not_read_as_human_gated():
    ledger = run_projection(payload(record(state="RUNNING")))
    reading = ledger["automations"][0]["state"]
    assert reading["human_gated"] is False
    assert reading["terminal"] is False
    assert "not evidence, verification, or acceptance" in reading["note"]


def test_only_the_terminal_state_is_read_as_terminal():
    for state in STATES:
        ledger = run_projection(payload(record(state=state)))
        assert ledger["automations"][0]["state"]["terminal"] is (state == "COMPLETED"), state


def test_an_unknown_state_is_reported_and_not_mapped():
    ledger = run_projection(payload(record(state="SELF_APPROVED")))
    reading = ledger["automations"][0]["state"]
    assert reading["state"] == "SELF_APPROVED"
    assert reading["known"] is False
    assert ledger["unknown_states"] == ["SELF_APPROVED"]
    assert any("outside the served vocabulary" in u for u in ledger["unresolved"])


def test_a_state_added_to_the_payload_vocabulary_is_known():
    """The vocabulary is read from the payload, so a new substrate state is known."""
    grammar = served_grammar()
    grammar["states"] = STATES + ["PAUSED"]
    ledger = run_projection(payload(record(state="PAUSED"), grammar=grammar))
    assert ledger["automations"][0]["state"]["known"] is True
    assert ledger["unknown_states"] == []


# ---------------------------------------------------------------------------
# Empty and defensive readings
# ---------------------------------------------------------------------------


def test_an_empty_payload_yields_an_empty_ledger():
    ledger = run_projection({"automations": [], "grammar": served_grammar()})
    assert ledger["automations"] == []
    assert ledger["state_counts"] == {}
    assert any("No automations are recorded" in u for u in ledger["unresolved"])


def test_a_missing_payload_does_not_throw():
    ledger = run_projection({})
    assert ledger["automations"] == []
    assert ledger["declared_grammar"] == []


def test_a_null_payload_does_not_throw():
    ledger = run_projection(None)
    assert ledger["automations"] == []
    assert ledger["grammar_matches"] is False


def test_state_counts_summarise_the_served_records():
    ledger = run_projection(
        payload(
            record(automation_id="A", state="DRAFT"),
            record(automation_id="B", state="DRAFT"),
            record(automation_id="C", state="AWAITING_HUMAN_ACTION"),
        )
    )
    assert ledger["state_counts"] == {"DRAFT": 2, "AWAITING_HUMAN_ACTION": 1}


def test_a_fully_declared_record_reports_only_the_run_produced_gap():
    """A complete definition has exactly one unfilled clause — the run's."""
    ledger = run_projection(payload(record()))
    assert ledger["unresolved"] == [
        "Every grammar clause a definition can carry is filled. "
        "The run-produced clause(s) remain unfilled by design."
    ]
    assert ledger["automations"][0]["run_produced_clauses"] == ["EVIDENCE"]


def test_an_incomplete_definition_is_distinguished_from_the_run_produced_gap():
    """A missing schedule is a real gap; EVIDENCE alone is not."""
    ledger = run_projection(
        payload(record(trigger={"kind": "scheduled", "detail": "", "schedule": None, "event": None}))
    )
    assert any("unfilled grammar clause(s): TRIGGER." in u for u in ledger["unresolved"])
    assert ledger["automations"][0]["run_produced_clauses"] == ["EVIDENCE"]
