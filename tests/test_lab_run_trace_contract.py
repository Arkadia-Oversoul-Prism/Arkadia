"""Workstream 4 — run → work-event → evidence trace, read-only ceiling (source guard).

``tests/test_prism_w4_run_evidence_trace.py`` measures the *behaviour* of the
projection against the real runtime. This file measures the property that makes
the surface safe to mount at all: it is read-only by construction, it reads only
the declared session contract, it does not reach for the Lab's mutating verbs,
and it renders the governance distinctions it claims to render.

Frontend guards in this repository are source-level string assertions (see
``tests/test_prism_w4_lab_read_model.py``); this file follows that convention and
does not duplicate its assertions. The detectors live at module level so the
negative controls exercise the same code the live assertions use.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
LAB = CONSOLE / "src" / "components" / "lab"
TRACE_TSX = LAB / "LabRunTrace.tsx"
TRACE_TS = LAB / "labRunTrace.ts"
SESSION_LIST = LAB / "LabSessionList.tsx"
CONTRACTS = ROOT / "lab" / "engineering_lab" / "contracts.py"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")
MUTATING_LAB_PATHS = ("/authorize", "/execute", "/transition", "/run-agent")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def mutating_calls(text: str) -> list[str]:
    """Every mutating HTTP method a module explicitly asks for."""
    return [
        m.group(1)
        for m in re.finditer(r'method\s*:\s*"([A-Z]+)"', text)
        if m.group(1) in MUTATING_METHODS
    ]


def network_calls(text: str) -> list[str]:
    """Every request primitive the module invokes.

    A trace surface that fetched its own data would be a second reader of the
    session contract, and its read-only claim would have to be re-proved. It must
    instead be a pure projection of the view its parent already holds.
    """
    return sorted({m.group(1) for m in re.finditer(r"\b(fetch|apiRequest|useHydration)\s*[(<]", text)})


def rendered_testids(text: str) -> set[str]:
    return set(re.findall(r'data-testid="([^"]+)"', text)) | set(
        re.findall(r"data-testid=\{`([^`]+)`\}", text)
    )


def declared_result_states(contracts: str) -> set[str]:
    """The Lab's own evidence ``RESULT_STATES`` vocabulary."""
    match = re.search(
        r"RESULT_STATES:\s*frozenset\[str\]\s*=\s*frozenset\(\s*\{(.*?)\}\s*\)", contracts, re.DOTALL
    )
    assert match, "contracts.py declares no RESULT_STATES frozenset"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


def declared_checkpoint_states(contracts: str) -> set[str]:
    """The Lab's own session/run ``CHECKPOINT_STATES`` vocabulary."""
    match = re.search(r"CHECKPOINT_STATES:\s*tuple\[str,\s*\.\.\.\]\s*=\s*\((.*?)\)", contracts, re.DOTALL)
    assert match, "contracts.py declares no CHECKPOINT_STATES tuple"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


def declared_human_terminal_states(contracts: str) -> set[str]:
    """The Lab's own human-only terminal states."""
    match = re.search(r"HUMAN_TERMINAL_STATES:\s*frozenset\[str\]\s*=\s*frozenset\(\s*\{(.*?)\}\s*\)", contracts, re.DOTALL)
    assert match, "contracts.py declares no HUMAN_TERMINAL_STATES frozenset"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


def projection_vocabulary(source: str, name: str) -> set[str]:
    """The string literals a projection constant declares, read from source."""
    match = re.search(rf"{name}:\s*readonly string\[\]\s*=\s*\[(.*?)\]", source, re.DOTALL)
    assert match, f"the projection declares no {name}"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


# ---------------------------------------------------------------------------
# Read-only ceiling
# ---------------------------------------------------------------------------


def test_trace_issues_no_mutating_request():
    for path in (TRACE_TSX, TRACE_TS):
        assert mutating_calls(_read(path)) == [], f"{path.name} asks for a mutating method"


def test_trace_does_not_reference_the_mutating_lab_endpoints():
    for path in (TRACE_TSX, TRACE_TS):
        source = _read(path)
        for verb in MUTATING_LAB_PATHS:
            assert verb not in source, f"{path.name} reaches for the mutating Lab path '{verb}'"


def test_trace_fetches_nothing_of_its_own():
    """The ledger is a projection of the view its parent holds. A fetch here
    would be a second, unreviewed read of the session contract."""
    for path in (TRACE_TSX, TRACE_TS):
        assert network_calls(_read(path)) == [], f"{path.name} performs its own network read"


def test_trace_projection_module_is_pure():
    """``labRunTrace.ts`` is executed directly by the oracle test, so it must
    import nothing at all — no React, no client, no registry."""
    source = _read(TRACE_TS)
    assert "import " not in source.replace("import type ", ""), "the projection imports a module"
    assert not re.search(r"^\s*import\b", source, re.M), "the projection has a runtime import"


def test_negative_control_detectors_flag_the_defect_they_exist_to_catch():
    assert mutating_calls('apiRequest(p, { method: "POST", body: "{}" })') == ["POST"]
    assert mutating_calls('apiRequest(p, { method: "GET" })') == []
    assert network_calls("const x = useHydration<View>(p, f);") == ["useHydration"]
    assert network_calls("apiRequest(path)") == ["apiRequest"]
    assert network_calls("function buildRunTrace(v) { return v; }") == []


# ---------------------------------------------------------------------------
# One registry, one reader
# ---------------------------------------------------------------------------


def test_trace_is_mounted_in_the_session_view_not_a_second_reader():
    """The trace renders inside the session detail, so the session contract has
    exactly one reader in this surface."""
    source = _read(SESSION_LIST)
    assert 'import { LabRunTrace }' in source
    assert "<LabRunTrace view={view.data} />" in source
    # The parent still reads the declared registry member, and only that.
    assert "endpoints.labSessions" in source
    assert len(re.findall(r"useHydration<", source)) == 2, (
        "the session list and the session detail are the only two reads"
    )


def test_trace_does_not_edit_the_shared_registry():
    """``lib/endpoints.ts`` is workstream 1's file. The trace adds no entry."""
    endpoints_ts = _read(CONSOLE / "src" / "lib" / "endpoints.ts")
    assert "labRunTrace" not in endpoints_ts
    assert "trace" not in endpoints_ts.lower()


# ---------------------------------------------------------------------------
# The governance distinctions the surface renders
# ---------------------------------------------------------------------------


def test_every_governance_stage_is_rendered_distinctly():
    source = _read(TRACE_TSX)
    for testid in (
        "lab-trace-runs",
        "lab-trace-empty",
        "lab-trace-acceptance",
        "lab-trace-unresolved",
    ):
        assert f'data-testid="{testid}"' in source, f"missing render surface '{testid}'"


def test_verification_is_not_inferred_from_an_evidence_record():
    """The projection must separate *entering* the verification stage from a
    recorded value *asserting* it. Collapsing them is the defect this exists to
    catch (the Lab's own ``IMPLEMENTED != VERIFIED`` boundary)."""
    source = _read(TRACE_TS)
    assert "stage_entered" in source and "asserted" in source
    assert "entered_basis" in source and "asserted_basis" in source
    # The asserted reading is derived only from the recorded VERIFIED state.
    assert 'VERIFIED_EVIDENCE_STATES: readonly string[] = ["VERIFIED"]' in source
    assert "indexOf(record.state)" in source


def test_verified_evidence_state_is_a_real_result_state():
    """A console-only vocabulary value would let the surface assert a state the
    substrate cannot record."""
    states = declared_result_states(_read(CONTRACTS))
    assert states, "control premise: RESULT_STATES must be non-empty"
    claimed = projection_vocabulary(_read(TRACE_TS), "VERIFIED_EVIDENCE_STATES")
    assert claimed, "the projection declares no verified-state vocabulary"
    assert claimed <= states, f"projection asserts state(s) outside RESULT_STATES: {claimed - states}"


def test_every_projection_state_vocabulary_is_a_substrate_vocabulary():
    """Each state list the projection reads must be drawn from the substrate.

    A console-invented state is worse than a missing one: it would let the
    surface report a boundary the Lab cannot record, or read a recorded state as
    acceptance that the Lab never granted.
    """
    contracts = _read(CONTRACTS)
    source = _read(TRACE_TS)
    checkpoint = declared_checkpoint_states(contracts)
    human_terminal = declared_human_terminal_states(contracts)

    assert checkpoint, "control premise: CHECKPOINT_STATES must be non-empty"
    assert human_terminal, "control premise: HUMAN_TERMINAL_STATES must be non-empty"

    for name, allowed in (
        ("VERIFICATION_STAGE_STATES", checkpoint),
        ("REVIEW_STATES", checkpoint),
        ("HUMAN_ACCEPTED_SESSION_STATES", human_terminal),
    ):
        claimed = projection_vocabulary(source, name)
        assert claimed, f"the projection declares no {name}"
        assert claimed <= allowed, f"{name} names state(s) outside the substrate: {claimed - allowed}"

    # The acceptance reading is the *whole* human terminal vocabulary, so a new
    # human-only terminal state cannot be silently read as not-accepted.
    assert projection_vocabulary(source, "HUMAN_ACCEPTED_SESSION_STATES") == human_terminal


def test_acceptance_is_read_only_from_the_human_terminal_state():
    """Only the human terminal state may read as acceptance; every other value,
    including the review boundary, must read NOT_RECORDED."""
    source = _read(TRACE_TS)
    assert 'HUMAN_ACCEPTED_SESSION_STATES: readonly string[] = ["COMPLETED"]' in source
    assert "NOT_RECORDED" in source
    assert "never inferred" in source
    # The review boundary is rendered as a boundary, never as an accepted result.
    assert "not an accepted result" in source
    # ...and the component renders that note rather than restating it.
    assert "trace.review.note" in _read(TRACE_TSX)


def test_review_boundary_does_not_imply_human_decision_was_made():
    """``human_decision_required`` is the backend's flag that a decision is
    *outstanding*. The surface must carry it as a distinct field so it can never
    be read as the decision having been made."""
    source = _read(TRACE_TS)
    assert "human_decision_required" in source
    tsx = _read(TRACE_TSX)
    assert "human decision required:" in tsx


def test_unresolved_links_are_rendered_not_hidden():
    """A reference that does not resolve must have a visible surface, and a clean
    view must say so rather than render an empty panel."""
    source = _read(TRACE_TSX)
    assert "ledger.unresolved" in source
    assert "do not resolve" in source
    assert "absent from the run's own evidence_refs" in source
    ts = _read(TRACE_TS)
    assert "dangling_evidence_refs" in ts
    assert "unreferenced_evidence_ids" in ts
    assert "unattributed_evidence" in ts
    assert "duplicate_evidence_ids" in ts


def test_partial_and_empty_states_have_distinct_copy():
    """An empty ledger is not a failure, and a partial link is not an error."""
    source = _read(TRACE_TSX)
    assert "lab-trace-partial-" in source
    assert "lab-trace-evidence-without-verification" in source
    assert "not an executed run" in source
    assert "Evidence is a record, not a verdict" in source


def test_negative_control_vocabulary_detector_sees_a_divergent_value():
    """The vocabulary detector must report a value the substrate cannot record."""
    states = declared_result_states(_read(CONTRACTS))
    assert "APPROVED" not in states
    assert {"APPROVED"} - states == {"APPROVED"}


def test_the_non_collapse_the_trace_renders_is_the_substrate_s_own():
    """``IMPLEMENTED != VERIFIED`` is the pair this slice exists to render. It
    must be the substrate's declared non-collapse, and the projection must not
    treat the left value as satisfying the right."""
    contracts = _read(CONTRACTS)
    assert '("IMPLEMENTED", "VERIFIED")' in contracts
    assert '("RUNNING", "COMPLETED")' in contracts
    source = _read(TRACE_TS)
    assert "IMPLEMENTED" not in projection_vocabulary(source, "VERIFIED_EVIDENCE_STATES")
    assert "VERIFIED" not in projection_vocabulary(source, "HUMAN_ACCEPTED_SESSION_STATES")


# ---------------------------------------------------------------------------
# The projection reads only handler-recorded reference fields
# ---------------------------------------------------------------------------


def test_joined_fields_are_declared_on_the_interface():
    """The fields the ledger joins on must be declared, so a rename in the
    handler surfaces as a type error rather than a silent zero-link reading."""
    source = _read(TRACE_TS)
    for field in ("run_id", "run_ref", "evidence_refs", "evidence_id", "event_id", "sequence"):
        assert field in source, f"the projection does not declare '{field}'"


def test_projection_does_not_invent_a_reference_field():
    """Every field the projection reads must exist on the runtime's own records.

    This is the "never join on a guessed identifier" rule: a fabricated field
    would join nothing and report a healthy session as empty.
    """
    runtime = _read(ROOT / "lab" / "engineering_lab" / "runtime.py")
    store = _read(ROOT / "lab" / "engineering_lab" / "store.py")
    for field in ("run_id", "run_ref", "evidence_refs", "evidence_id", "event_id"):
        assert field in runtime or field in store, f"the substrate records no '{field}'"
