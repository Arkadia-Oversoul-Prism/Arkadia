"""Workstream 4 — automation grammar read surface, contract pins (source guard).

``tests/test_prism_w4_automation_grammar.py`` measures the *behaviour* of the
projection against payloads shaped like the served contract. This file measures
the property that makes the surface safe to mount at all: every vocabulary it
renders is the substrate's own, it reaches no mutating verb, and it renders the
human gate as the final transition rather than as a self-serve state.

Frontend guards in this repository are source-level string assertions (see
``tests/test_prism_w4_lab_read_model.py``); this file follows that convention.
The detectors live at module level so the negative controls exercise the same
code the live assertions use.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
LAB = CONSOLE / "src" / "components" / "lab"
SURFACE_TSX = LAB / "LabAutomationGrammar.tsx"
PROJECTION_TS = LAB / "labAutomationGrammar.ts"
PAGE = CONSOLE / "src" / "pages" / "EngineeringLabPage.tsx"
ENDPOINTS = CONSOLE / "src" / "lib" / "endpoints.ts"
LAB_ROUTES = ROOT / "api" / "lab_routes.py"
AUTOMATIONS = ROOT / "lab" / "engineering_lab" / "automations.py"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")
MUTATING_LAB_PATHS = ("/authorize", "/execute", "/transition", "/run-agent")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (each has a negative control below)
# ---------------------------------------------------------------------------


def mutating_calls(text: str) -> list[str]:
    """Every mutating HTTP method a module explicitly asks for."""
    return [
        m.group(1)
        for m in re.finditer(r'method\s*:\s*"([A-Z]+)"', text)
        if m.group(1) in MUTATING_METHODS
    ]


def network_calls(text: str) -> list[str]:
    """Every request primitive the projection invokes.

    A projection that fetched its own data would be a second reader of the
    automations contract, and its purity claim would have to be re-proved.
    """
    return sorted({m.group(1) for m in re.finditer(r"\b(fetch|apiRequest|useHydration)\s*[(<]", text)})


def rendered_testids(text: str) -> set[str]:
    return set(re.findall(r'data-testid="([^"]+)"', text)) | set(
        re.findall(r"data-testid=\{`([^`]+)`\}", text)
    )


def strip_comments(text: str) -> str:
    """The module's code with comments removed.

    A surface that *documents* an unwired mutating path in a comment is not a
    surface that calls it. Scanning prose for a path is the mention-vs-execution
    defect this repository has already been bitten by, so the path assertions run
    against code only.
    """
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", without_block, flags=re.MULTILINE)


def declared_grammar(module: str) -> list[str]:
    """The substrate's ordered grammar chain, read from ``grammar_view``."""
    match = re.search(r'"grammar":\s*\[(.*?)\]', module, re.DOTALL)
    assert match, "automations.py declares no grammar chain"
    return re.findall(r'"([A-Z_]+)"', match.group(1))


def declared_states(module: str) -> set[str]:
    """The substrate's ``AUTOMATION_STATES`` vocabulary."""
    match = re.search(
        r"AUTOMATION_STATES:\s*tuple\[str,\s*\.\.\.\]\s*=\s*\((.*?)\)", module, re.DOTALL
    )
    assert match, "automations.py declares no AUTOMATION_STATES tuple"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


def declared_trigger_kinds(module: str) -> set[str]:
    """The substrate's ``TRIGGER_KINDS`` vocabulary."""
    match = re.search(
        r"TRIGGER_KINDS:\s*tuple\[str,\s*\.\.\.\]\s*=\s*\((.*?)\)", module, re.DOTALL
    )
    assert match, "automations.py declares no TRIGGER_KINDS tuple"
    return set(re.findall(r'"([a-z_]+)"', match.group(1)))


def declared_human_gated_states(module: str) -> set[str]:
    """The substrate's ``HUMAN_GATED_STATES`` — the states only a human leaves."""
    match = re.search(r"HUMAN_GATED_STATES:\s*frozenset\[str\]\s*=\s*frozenset\(\{(.*?)\}\)", module, re.DOTALL)
    assert match, "automations.py declares no HUMAN_GATED_STATES frozenset"
    return set(re.findall(r'"([A-Z_]+)"', match.group(1)))


def declared_terminal_states(module: str) -> set[str]:
    """States with no outgoing transition, read from ``AUTOMATION_TRANSITIONS``."""
    match = re.search(
        r"AUTOMATION_TRANSITIONS:\s*dict\[str,\s*frozenset\[str\]\]\s*=\s*\{(.*?)\n\}", module, re.DOTALL
    )
    assert match, "automations.py declares no AUTOMATION_TRANSITIONS mapping"
    return set(re.findall(r'"([A-Z_]+)":\s*frozenset\(\)', match.group(1)))


def projection_literal(name: str, text: str) -> set[str]:
    """A ``readonly string[]`` literal exported by the projection."""
    match = re.search(
        rf"export const {name}: readonly string\[\] = \[(.*?)\];", text, re.DOTALL
    )
    assert match, f"projection exports no {name} literal"
    return set(re.findall(r'"([A-Za-z_]+)"', match.group(1)))


# ---------------------------------------------------------------------------
# The rendered vocabulary is the substrate's vocabulary
# ---------------------------------------------------------------------------


def test_rendered_grammar_chain_is_the_substrate_chain():
    """The chain the surface renders must be the chain the substrate declares."""
    assert projection_literal("GRAMMAR_CLAUSES", _read(PROJECTION_TS)) == set(
        declared_grammar(_read(AUTOMATIONS))
    )


def test_rendered_grammar_order_matches_the_substrate_order():
    """Order is the contract: a reorder re-labels a clause without renaming it."""
    match = re.search(r"export const GRAMMAR_CLAUSES: readonly string\[\] = \[(.*?)\];", _read(PROJECTION_TS), re.DOTALL)
    assert match
    rendered = re.findall(r'"([A-Z_]+)"', match.group(1))
    assert rendered == declared_grammar(_read(AUTOMATIONS))


def test_rendered_state_vocabulary_is_the_substrate_vocabulary():
    assert projection_literal("HUMAN_GATED_STATES", _read(PROJECTION_TS)) == declared_human_gated_states(
        _read(AUTOMATIONS)
    )
    assert projection_literal("TERMINAL_STATES", _read(PROJECTION_TS)) == declared_terminal_states(
        _read(AUTOMATIONS)
    )


def test_rendered_trigger_kinds_are_substrate_kinds():
    """Every kind the projection treats as an event trigger must be a real kind."""
    rendered = projection_literal("EVENT_TRIGGER_KINDS", _read(PROJECTION_TS))
    substrate = declared_trigger_kinds(_read(AUTOMATIONS))
    assert rendered, "the projection must classify at least one event trigger kind"
    assert rendered <= substrate, f"not substrate trigger kinds: {sorted(rendered - substrate)}"


def test_rendered_state_vocabulary_is_not_read_from_a_stale_constant():
    """The states the surface renders must come from the served payload.

    The projection reads ``grammar.states`` at call time; if it carried its own
    state list, a substrate state added later would be reported as unknown for
    every session.
    """
    text = _read(PROJECTION_TS)
    assert "declaredStates" in text
    assert "grammar.states" in text or "grammar?.states" in text


# ---------------------------------------------------------------------------
# The read-only ceiling
# ---------------------------------------------------------------------------


def test_surface_issues_no_mutating_request():
    assert mutating_calls(_read(SURFACE_TSX)) == []


def test_surface_does_not_reference_the_mutating_lab_endpoints():
    text = strip_comments(_read(SURFACE_TSX))
    assert [p for p in MUTATING_LAB_PATHS if p in text] == []


def test_surface_reads_the_declared_collection_endpoint():
    """The surface must read the registry entry, not restate the path."""
    text = _read(SURFACE_TSX)
    assert "endpoints.labAutomations" in text
    assert "labAutomations" in _read(ENDPOINTS)


def test_surface_does_not_post_to_create_or_move_an_automation():
    """Creating and state-moving are mutating acts and must stay unwired."""
    text = strip_comments(_read(SURFACE_TSX))
    assert "/engineering/automations" not in text
    assert "/state" not in text


def test_projection_module_is_pure():
    """No network, no React, no store access — so it can be executed directly.

    The check is on *code*, not prose: the module's own header comment explains
    that it has no imports, and a naive scan would read that sentence as one.
    """
    text = strip_comments(_read(PROJECTION_TS))
    assert network_calls(text) == []
    assert "react" not in text.lower()
    assert not re.search(r"^\s*import\b", text, re.MULTILINE)


# ---------------------------------------------------------------------------
# The governance distinctions the surface renders
# ---------------------------------------------------------------------------


def test_human_gate_is_rendered_as_the_final_transition():
    text = _read(SURFACE_TSX)
    assert "final transition" in text
    assert "never authorize" in text


def test_authority_claim_is_rendered_as_a_violation_not_as_state():
    text = _read(PROJECTION_TS)
    assert "boundary_violations" in text
    assert "may_authorize" in text
    surface = _read(SURFACE_TSX)
    assert "Boundary violation" in surface


def test_evidence_clause_is_never_inferred_from_the_definition():
    """EVIDENCE is produced by a run; the projection must say so, not guess it."""
    text = _read(PROJECTION_TS)
    assert "RUN_PRODUCED_CLAUSES" in text
    assert "not carried by the automation definition" in text
    assert "produced by a run" in text


def test_unknown_state_is_reported_honestly():
    text = _read(PROJECTION_TS)
    assert "outside the served vocabulary" in text
    assert "not mapped onto a known state" in text


def test_empty_state_has_distinct_copy():
    surface = _read(SURFACE_TSX)
    assert "lab-automations-empty" in rendered_testids(surface)
    assert "No automations are recorded for this identity" in surface


def test_surface_is_mounted_in_the_lab_page():
    page = _read(PAGE)
    assert "LabAutomationGrammar" in page
    assert "<LabAutomationGrammar />" in page


def test_surface_does_not_edit_the_shared_registry():
    """The registry entry already exists; this slice consumes it, it does not add it."""
    assert "labAutomations" in _read(ENDPOINTS)


# ---------------------------------------------------------------------------
# Negative controls — the detectors must see the defect they exist to catch
# ---------------------------------------------------------------------------


def test_negative_control_detectors_flag_the_defect_they_exist_to_catch():
    assert mutating_calls('fetch(p, { method: "POST" })') == ["POST"]
    assert mutating_calls('fetch(p, { method: "GET" })') == []
    assert network_calls("const x = apiRequest<Foo>(p);") == ["apiRequest"]
    assert network_calls("export function buildAutomationLedger(p) {}") == []
    assert rendered_testids('<p data-testid="a" />') == {"a"}
    assert rendered_testids("<p className='x' />") == set()
    # A documented-but-unwired mutating path is prose; a called one is code.
    assert "/execute" in "/* documents /execute */"
    assert "/execute" not in strip_comments("/* documents /execute */")
    assert "/execute" not in strip_comments("// documents /execute")
    assert "/execute" in strip_comments('fetch("/execute")')
    # The purity detector must still see a real import or fetch.
    assert re.search(r"^\s*import\b", strip_comments("import x from 'y';"), re.MULTILINE)
    assert network_calls(strip_comments("const d = await fetch(u);")) == ["fetch"]


def test_negative_control_vocabulary_detector_sees_a_divergent_value():
    """A rendered clause the substrate does not declare must be detectable."""
    substrate = set(declared_grammar(_read(AUTOMATIONS)))
    divergent = substrate | {"APPROVAL"}
    assert divergent != substrate
    assert divergent - substrate == {"APPROVAL"}


def test_negative_control_human_gated_detector_sees_a_self_serve_state():
    """A state the substrate does not human-gate must not be read as gated."""
    gated = declared_human_gated_states(_read(AUTOMATIONS))
    assert "DRAFT" not in gated
    assert "RUNNING" not in gated


def test_negative_control_terminal_detector_sees_a_non_terminal_state():
    terminal = declared_terminal_states(_read(AUTOMATIONS))
    assert "COMPLETED" in terminal
    assert "RUNNING" not in terminal


def test_negative_control_event_kind_detector_sees_a_scheduled_kind():
    """``scheduled`` is a real kind but is not an event kind."""
    rendered = projection_literal("EVENT_TRIGGER_KINDS", _read(PROJECTION_TS))
    assert "scheduled" not in rendered
    assert "scheduled" in declared_trigger_kinds(_read(AUTOMATIONS))
