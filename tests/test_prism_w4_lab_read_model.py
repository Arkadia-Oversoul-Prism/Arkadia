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
    """The view path the component builds must be the declared sub-resource.

    The path is built inline at the ``useHydration`` call so its first argument
    is literally the registry member (the registry-contract guard requires
    ``endpoints.*``). ``endpoints.labSessions`` is the collection the backend
    declares.
    """
    component = _read(COMPONENT)
    assert 'endpoints.labSessions + "/" + encodeURIComponent(sessionId)' in component
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


# ---------------------------------------------------------------------------
# Run / work-event / evidence ledger, surfaced on the Weaver page
# ---------------------------------------------------------------------------

WEAVER_PAGE = CONSOLE / "src" / "pages" / "WeaverPage.tsx"
LAB_RUNTIME = ROOT / "lab" / "engineering_lab" / "runtime.py"


def test_weaver_page_renders_the_session_ledger():
    """The Weaver page names runs/events/evidence from a real contract rather
    than advertising an unbuilt execute view."""
    page = _read(WEAVER_PAGE)
    assert 'import { LabSessionList }' in page
    assert "<LabSessionList />" in page


def test_weaver_page_lists_the_three_record_classes():
    """Each governance record class is rendered distinctly and labelled as what
    it is, not as a later stage."""
    component = _read(COMPONENT)
    for testid in ("lab-runs", "lab-events", "lab-evidence"):
        assert f'data-testid="{testid}"' in component
    # Each class carries a distinct empty state (an empty ledger is not a failure).
    for testid in ("lab-runs-empty", "lab-events-empty", "lab-evidence-empty"):
        assert f'data-testid="{testid}"' in component
    # Evidence is explicitly not a verdict; a run is an execution record.
    assert "not a verdict" in component
    assert "is not an executed run" in component


def test_weaver_page_advertises_only_a_served_contract():
    """The advertised `contract=` string must be a served path (its parameter
    name may differ), so a page cannot advertise execution it does not perform.
    """
    import re

    from api.main import app

    advertised = re.findall(r'contract="([^"]+)"', _read(WEAVER_PAGE))
    assert advertised, "the Weaver page advertises no blocked state -- the check would be vacuous"
    served = {re.sub(r"\{[^}]*\}", "{}", p) for p in app.openapi()["paths"].keys()}
    for value in advertised:
        normalized = re.sub(r"\{[^}]*\}", "{}", value)
        assert normalized in served, f"advertised contract {value!r} is not a served path"


def test_weaver_ledger_does_not_assert_acceptance():
    """The record ledger must not render an earlier stage as acceptance."""
    component = _read(COMPONENT)
    assert "review boundary" in component
    assert "acceptance is a separate human act" in component


def test_session_view_backend_supplies_the_three_record_arrays():
    """The ledger reads `runs`/`events`/`evidence` from the session view; those
    keys must be the ones `session_view` returns."""
    view = _read(LAB_RUNTIME)
    block = view.split("def session_view", 1)[1].split("def overview", 1)[0]
    for key in ('"runs": runs', '"events": events', '"evidence": evidence'):
        assert key in block, f"session_view does not return {key!r}"



# ---------------------------------------------------------------------------
# Artifact canvas (slice 03), surfaced on the Engineering Lab page
# ---------------------------------------------------------------------------

CANVAS = CONSOLE / "src" / "components" / "lab" / "LabArtifactCanvas.tsx"


def test_lab_page_renders_the_artifact_canvas():
    page = _read(PAGE)
    assert 'import { LabArtifactCanvas }' in page
    assert "<LabArtifactCanvas />" in page


def test_canvas_reads_the_declared_artifacts_endpoint():
    component = _read(CANVAS)
    assert "endpoints.labArtifacts" in component, "the canvas must use the canonical endpoint map"


def test_canvas_issues_no_mutating_request():
    assert mutating_calls(_read(CANVAS)) == []


def test_canvas_does_not_reference_the_mutating_lab_endpoints():
    component = _read(CANVAS)
    for path in MUTATING_LAB_PATHS:
        assert path not in component, f"canvas reaches for the mutating Lab path '{path}'"


def test_canvas_renders_unavailable_content_honestly():
    """The truthfulness rule: an artifact with no captured content must render
    the backend's reason, never a fabricated placeholder."""
    component = _read(CANVAS)
    assert "unavailable_reason" in component
    assert 'data-testid="lab-canvas-unavailable"' in component
    # It must not present a false success from an empty response.
    assert "No artifacts captured" in component


def test_canvas_declares_actions_but_does_not_wire_them():
    """Declared actions are affordances, not authority; a non-interactive label
    is the honest rendering."""
    component = _read(CANVAS)
    assert "actions.join" in component
    assert "not wired" in component

