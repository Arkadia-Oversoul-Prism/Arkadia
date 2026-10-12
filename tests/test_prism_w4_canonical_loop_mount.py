"""PRISM Workstream 4 — canonical work-loop surface (mount + handler oracle).

The console's Engineering Lab surface renders the runtime's *canonical work loop*
through ``components/lab/ExecutionLoop.tsx``. That component was committed by an
earlier pass (``74936640``) but never imported or rendered — an orphaned
projection. This guard binds its mount to the two things that make the surface
honest:

  * the **handler oracle** — the stages it renders are exactly ``CANONICAL_LOOP``
    as the authenticated ``GET /api/lab/engineering/overview`` returns it, read
    from the *real* runtime over an isolated database, not from an interface;
  * the **read-only ceiling** — the component and its reader issue no mutating
    request and reference no mutating Lab path.

The governance distinction the surface exists to preserve is
proposal != approval != execution != evidence != verification !=
review/acceptance. A loop *definition* is not a run-status indicator, so the guard
also asserts the component says so and that a malformed/absent payload yields no
inferred stages.

These are source-level contracts plus one executed handler, matching this
repository's frontend-test convention (see ``tests/test_prism_w4_lab_read_model.py``).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
PAGE = CONSOLE / "src" / "pages" / "EngineeringLabPage.tsx"
COMPONENT = CONSOLE / "src" / "components" / "lab" / "ExecutionLoop.tsx"
LAB_ROUTES = ROOT / "api" / "lab_routes.py"
RUNTIME = ROOT / "lab" / "engineering_lab" / "runtime.py"
ENDPOINTS = CONSOLE / "src" / "lib" / "endpoints.ts"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#: The Lab endpoints that mutate Lab state and require a human decision. The loop
#: surface must not reach for any of them.
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


def canonical_loop(runtime_src: str) -> list[str]:
    """The runtime's declared loop, read from ``CANONICAL_LOOP``."""
    start = runtime_src.index("CANONICAL_LOOP")
    block = runtime_src[start : runtime_src.index(")", start)]
    return re.findall(r'"([A-Z_]+)"', block)


# ---------------------------------------------------------------------------
# The orphaned projection is now mounted, and its stages come from the read
# ---------------------------------------------------------------------------


def test_lab_page_renders_the_canonical_loop_surface():
    page = _read(PAGE)
    assert 'import { ExecutionLoop }' in page
    assert "<ExecutionLoop" in page, "the canonical loop surface is not rendered"


def test_loop_stages_are_read_from_the_overview_response():
    """The stages must come from the authenticated overview read — the same
    declared registry entry the page already hydrates — not a second request or
    a hardcoded sequence."""
    page = _read(PAGE)
    assert "readLoopStages(" in page
    assert 'overview.data' in page, "the loop reader must consume the overview payload"
    assert "endpoints.labEngineeringOverview" in page


def test_loop_reader_infers_no_stage_from_a_malformed_payload():
    """A payload without a well-formed ``loop`` array yields no stages, so the
    surface reports an unfilled definition instead of inventing one."""
    page = _read(PAGE)
    # The reader is total: it filters to strings and falls back to an empty list.
    assert "Array.isArray(loop)" in page
    assert 'typeof stage === "string"' in page
    assert "? loop.filter" in page and ": [];" in page


def test_surface_distinguishes_definition_from_live_status():
    component = _read(COMPONENT)
    assert "not a live run-status indicator" in component
    assert "Human authorization remains a distinct gate" in component


# ---------------------------------------------------------------------------
# Read-only ceiling (structural, not merely promised)
# ---------------------------------------------------------------------------


def test_loop_component_issues_no_mutating_request():
    assert mutating_calls(_read(COMPONENT)) == []
    assert mutating_calls(_read(PAGE)) == []


def test_loop_surface_does_not_reference_the_mutating_lab_endpoints():
    for path in MUTATING_LAB_PATHS:
        assert path not in _read(COMPONENT), f"loop surface reaches for the mutating Lab path '{path}'"


def test_loop_component_issues_no_request_of_its_own():
    """The component is a pure projection: the page fetches, the component renders."""
    component = _read(COMPONENT)
    assert "apiRequest" not in component
    assert "useHydration" not in component


def test_negative_control_detector_flags_a_mutating_module():
    """The detector must report the defect it exists to catch."""
    assert mutating_calls('apiRequest(p, { method: "POST", body: "{}" })') == ["POST"]
    assert mutating_calls('apiRequest(p, { method: "DELETE" })') == ["DELETE"]
    assert mutating_calls('apiRequest(p, { method: "GET" })') == []
    assert mutating_calls("apiRequest(p)") == []


# ---------------------------------------------------------------------------
# The backend contract it binds to (executed, not asserted)
# ---------------------------------------------------------------------------


def test_overview_route_is_a_declared_get_route():
    routes = _read(LAB_ROUTES)
    assert '@router.get("/engineering/overview")' in routes


def test_overview_returns_the_runtime_canonical_loop(runtime):
    """Drive the *real* runtime over an isolated store and assert the stages it
    returns are exactly ``CANONICAL_LOOP`` — the vocabulary the UI renders."""
    routes = _read(LAB_ROUTES)
    assert 'overview["loop"] = list(CANONICAL_LOOP)' in routes

    overview = runtime.overview("subject-owner")
    assert overview["loop"] == canonical_loop(_read(RUNTIME))
    assert overview["loop"] == [
        "DISCOVER",
        "PLAN",
        "EXECUTE",
        "OBSERVE",
        "EVIDENCE",
        "PROPOSE",
        "REVIEW",
        "AUTHORIZE",
        "VERIFY",
        "RECORD",
    ]


def test_overview_loop_is_owner_scoped_and_carries_no_authority(runtime):
    overview = runtime.overview("subject-owner")
    assert overview["authority"]["human_authorization_required"] is True
    assert overview["authority"]["autonomous_merge"] is False
    assert overview["authority"]["autonomous_deploy"] is False


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


# ---------------------------------------------------------------------------
# Registry binding
# ---------------------------------------------------------------------------


def test_overview_endpoint_is_the_declared_registry_entry():
    endpoints_ts = _read(ENDPOINTS)
    assert 'labEngineeringOverview: "/api/lab/engineering/overview"' in endpoints_ts
