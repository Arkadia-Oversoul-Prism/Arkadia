"""PRISM Workstream 4 — Engineering Lab read-only session read model (source-level).

The console's Engineering Lab surface is allowed to *observe* the Lab substrate.
It is not allowed to acquire execution or authorization authority. This guard
binds the feature-local read model to the two things that make that claim real:

  * the **backend contract** — the collection path and the session view path it
    reads must exist as ``GET`` routes on the Lab router, and the state
    vocabulary it renders must be exactly the Lab's own ``LEGAL_TRANSITIONS``
    set (a UI that invents a state is a UI that can invent a stage);
  * the **read-only ceiling** — the module must issue no mutating request, and
    must not reference the Lab's mutating endpoints at all.

The governance distinction the surface exists to preserve is
proposal != approval != execution != work event != evidence != verification !=
review/acceptance. The guard therefore also asserts that reaching the review
boundary is not rendered as acceptance.

These are source-level contracts, matching this repository's frontend-test
convention (see ``tests/test_aeas05_canonical_frontend_acceptance.py``).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
PAGE = CONSOLE / "src" / "pages" / "EngineeringLabPage.tsx"
COMPONENT = CONSOLE / "src" / "components" / "lab" / "LabSessionList.tsx"
LAB_ROUTES = ROOT / "api" / "lab_routes.py"
CONTRACTS = ROOT / "lab" / "engineering_lab" / "contracts.py"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#: The Lab endpoints that mutate Lab state and require a human decision. The
#: read model must not reach for any of them.
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


def _block(text: str, opener: str) -> str:
    """Extract the object-literal block that follows *opener*.

    Anchors on ``= {`` rather than the first ``{``, because the declaration's
    type annotation (``Record<string, { ... }>``) contains a balanced brace pair
    that a naive scan would return instead of the value.
    """
    start = text.index(opener)
    start = text.index("= {", start) + 2
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise AssertionError(f"unbalanced block for {opener!r}")


def rendered_states(component: str) -> set[str]:
    """The state keys the read model maps to a governance stage."""
    block = _block(component, "const STATE_STAGE")
    return set(re.findall(r"^\s{2}([A-Z_]+):\s*\{", block, re.M))


def backend_states(contracts: str) -> set[str]:
    """The Lab's own governed session states, read from ``LEGAL_TRANSITIONS``."""
    block = _block(contracts, "LEGAL_TRANSITIONS")
    return set(re.findall(r'^\s{4}"([A-Z_]+)":', block, re.M))


# ---------------------------------------------------------------------------
# The surface is wired to the read model
# ---------------------------------------------------------------------------


def test_lab_page_renders_the_session_read_model():
    page = _read(PAGE)
    assert 'import { LabSessionList }' in page
    assert "<LabSessionList />" in page


def test_lab_page_keeps_the_mutating_acts_as_an_explicit_blocked_state():
    """Authorize/execute/transition are not silently absent -- the page names
    them as unwired rather than implying the surface can perform them."""
    page = _read(PAGE)
    assert "not wired" in page
    for verb in ("authorize", "execute", "transition"):
        assert verb in page


# ---------------------------------------------------------------------------
# Read-only ceiling
# ---------------------------------------------------------------------------


def test_read_model_issues_no_mutating_request():
    assert mutating_calls(_read(COMPONENT)) == []


def test_read_model_does_not_reference_the_mutating_lab_endpoints():
    component = _read(COMPONENT)
    for path in MUTATING_LAB_PATHS:
        assert path not in component, f"read model reaches for the mutating Lab path '{path}'"


def test_read_model_reads_the_declared_collection_endpoint():
    component = _read(COMPONENT)
    assert "endpoints.labSessions" in component, "the read model must use the canonical endpoint map"


def test_negative_control_detector_flags_a_mutating_read_model():
    """The detector must report the defect it exists to catch."""
    assert mutating_calls('apiRequest(p, { method: "POST", body: "{}" })') == ["POST"]
    assert mutating_calls('apiRequest(p, { method: "GET" })') == []
    assert mutating_calls("apiRequest(p)") == []


# ---------------------------------------------------------------------------
# The backend contract it binds to
# ---------------------------------------------------------------------------


def test_session_collection_and_view_are_declared_get_routes():
    routes = _read(LAB_ROUTES)
    assert '@router.get("/engineering/sessions")' in routes
    assert '@router.get("/engineering/sessions/{session_id}")' in routes


def test_read_model_view_path_is_the_backend_sub_resource():
    """The view path the component builds must be the declared sub-resource."""
    component = _read(COMPONENT)
    assert "${endpoints.labSessions}/${encodeURIComponent(sessionId)}" in component
    # endpoints.labSessions is the collection the backend declares.
    endpoints_ts = _read(CONSOLE / "src" / "lib" / "endpoints.ts")
    assert 'labSessions: "/api/lab/engineering/sessions"' in endpoints_ts


def test_rendered_state_vocabulary_is_the_backend_vocabulary():
    """A UI state that the substrate cannot enter would let the surface imply a
    stage the backend never granted. The sets must be identical."""
    assert rendered_states(_read(COMPONENT)) == backend_states(_read(CONTRACTS))


# ---------------------------------------------------------------------------
# Stage distinction and the review boundary
# ---------------------------------------------------------------------------


def test_governance_stages_are_visibly_distinct():
    component = _read(COMPONENT)
    for stage in ("PROPOSAL", "AUTHORIZATION", "EXECUTION", "VERIFICATION", "REVIEW", "ACCEPTANCE"):
        assert f'stage: "{stage}"' in component, f"stage '{stage}' is not distinguished"


def test_review_boundary_is_not_rendered_as_acceptance():
    component = _read(COMPONENT)
    assert "reached_review_boundary" in component
    assert "acceptance is a separate human act" in component
    # Only a human-accepted terminal maps to ACCEPTANCE.
    assert 'COMPLETED: { stage: "ACCEPTANCE"' in component


def test_unknown_state_is_reported_honestly():
    """An unrecognised state must render as unknown, not be coerced into a
    known stage."""
    component = _read(COMPONENT)
    assert 'stage: "UNKNOWN"' in component
    assert "Unrecognised state" in component


def test_negative_control_state_vocabulary_detector():
    """The vocabulary detector must see a divergent set, not always agree."""
    divergent = 'const STATE_STAGE: Record<string, unknown> = {\n  PROPOSED: { stage: "PROPOSAL" },\n};'
    assert rendered_states(divergent) == {"PROPOSED"}
    assert rendered_states(divergent) != backend_states(_read(CONTRACTS))
