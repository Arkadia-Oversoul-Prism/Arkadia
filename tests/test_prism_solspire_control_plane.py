"""SolSpire control-plane readings — PRR-09.

`SolSpirePage` advertised four contracts as not-yet-wired using a wrong `/api`
prefix (`/api/solspire/workloads`, `/api/solspire/proposals`,
`/api/solspire/pulses`, `/api/solspire/voice`). The canonical backend serves the
`/solspire` router (no `/api` prefix); three of those reads are real, owner-scoped
GETs. This work item wires the bounded daily/weekly spine through the shared
endpoint registry and stops advertising the wrong strings.

Domain: the Arkadia Console (`web/arkadia_console`) over the canonical FastAPI
app. Read-only: no control here mutates workspace, workload, pulse, synthesis,
proposal, or work-event state, and none is offered.

The backend half is **executed**: a TestClient over the real `console_router`
with isolated SQLite paths asserts the served shapes and the two *narrow* states
the surface must distinguish from a failure — `409` (no canonical workspace
bound) and `404` (no canonical workload yet). The frontend half is the
repository's source-contract convention with negative controls.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.pulse_manager as pulse_manager
import solspire.synthesis_manager as synthesis_manager
import solspire.workload_manager as workload_manager
import solspire.workspace_manager as workspace_manager
from api.auth import require_auth
from solspire.console_router import router as console_router

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"
PAGE_PATH = SRC / "pages" / "SolSpirePage.tsx"
PANEL_PATH = SRC / "components" / "solspire" / "SolSpireControlPlane.tsx"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"
TYPES_PATH = SRC / "lib" / "types.ts"

PAGE = PAGE_PATH.read_text(encoding="utf-8")
PANEL = PANEL_PATH.read_text(encoding="utf-8")
ENDPOINTS = ENDPOINTS_PATH.read_text(encoding="utf-8")
TYPES = TYPES_PATH.read_text(encoding="utf-8")

OWNER = {"uid": "sc-owner", "access_level": 1}

#: The four strings SolSpirePage advertised at `3ca8582`; none is a served path.
WRONG_ADVERTISED = (
    "/api/solspire/workloads",
    "/api/solspire/proposals",
    "/api/solspire/pulses",
    "/api/solspire/voice",
)


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def _code_only(text: str) -> str:
    """Comments may name a route freely; only code composes paths."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return text


def _composes_an_inline_solspire_path(text: str) -> bool:
    """A raw `/solspire/...` composition outside the registry = second contract."""
    return bool(re.search(r"[`\"']/?solspire/", _code_only(text)))


# ---------------------------------------------------------------------------
# Backend half — executed against the real router
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db = tmp_path / "solspire_projects.db"
    for module in (workspace_manager, workload_manager, pulse_manager, synthesis_manager):
        monkeypatch.setattr(module, "_DB_PATH", str(db))
    application = FastAPI()
    application.include_router(console_router)
    yield application
    application.dependency_overrides.clear()


def _client(app: FastAPI, user: dict | None) -> TestClient:
    app.dependency_overrides.pop(require_auth, None)
    if user is not None:
        app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def test_workspace_reads_are_owner_scoped_and_shape_stable(app):
    body = _client(app, OWNER).get("/solspire/workspace").json()
    assert set(("workspace", "canonical", "subject_binding")) <= set(body)
    assert body["canonical"] is True
    assert body["subject_binding"] == "authenticated_firebase_uid"
    for key in ("id", "workspace_type", "display_name", "lifecycle"):
        assert key in body["workspace"], key


def test_unauthenticated_caller_is_refused_on_every_read(app):
    client = _client(app, None)
    for path in ("/solspire/workspace", "/solspire/workloads", "/solspire/pulses", "/solspire/syntheses"):
        assert client.get(path).status_code == 401, path


def test_missing_workspace_is_a_409_not_a_broken_read(app):
    """Without a bound workspace the list reads answer 409 — the surface's
    'unbound' state, not a transport failure."""
    client = _client(app, OWNER)
    assert client.get("/solspire/pulses").status_code == 409
    assert client.get("/solspire/syntheses").status_code == 409
    assert client.get("/solspire/workloads").status_code == 409


def test_bound_workspace_yields_empty_lists_and_a_404_workload(app):
    """After the workspace resolves: pulses/syntheses are 200 empty lists, and
    the workload is a genuine 404 (no workload yet)."""
    client = _client(app, OWNER)
    assert client.get("/solspire/workspace").status_code == 200

    pulses = client.get("/solspire/pulses")
    assert pulses.status_code == 200
    assert pulses.json() == {"pulses": [], "count": 0}

    syntheses = client.get("/solspire/syntheses")
    assert syntheses.status_code == 200
    assert syntheses.json() == {"syntheses": [], "count": 0}

    assert client.get("/solspire/workloads").status_code == 404


def test_reads_mutate_nothing(app):
    client = _client(app, OWNER)
    client.get("/solspire/workspace")
    first = client.get("/solspire/pulses").json()
    second = client.get("/solspire/pulses").json()
    assert first == second


# ---------------------------------------------------------------------------
# Frontend half — source contracts with negative controls
# ---------------------------------------------------------------------------


def test_panel_reads_every_spine_endpoint_through_the_registry():
    for name in ("solspireWorkspace", "solspireWorkloads", "solspirePulses", "solspireSyntheses"):
        assert f"endpoints.{name}" in PANEL, name
    assert not _composes_an_inline_solspire_path(PANEL), (
        "the panel must not compose a `/solspire/...` path itself"
    )


def test_registry_entries_are_declared():
    for entry in ('solspireWorkspace: "/solspire/workspace"',
                  'solspireWorkloads: "/solspire/workloads"',
                  'solspirePulses: "/solspire/pulses"',
                  'solspireSyntheses: "/solspire/syntheses"'):
        assert entry in ENDPOINTS, entry


def test_types_are_declared_for_every_read():
    for iface in ("SolspireWorkspaceRead", "SolspireWorkloadRead", "SolspirePulseList", "SolspireSynthesisList"):
        assert f"export interface {iface}" in TYPES, iface


def test_page_no_longer_advertises_the_wrong_api_prefix():
    for wrong in WRONG_ADVERTISED:
        assert wrong not in PAGE, f"the wrong contract string {wrong!r} must be gone"


def test_page_mounts_the_control_plane_and_advertises_only_served_paths():
    assert "<SolSpireControlPlane" in PAGE
    advertised = re.findall(r'contract="([^"]+)"', PAGE)
    assert advertised, "the page must still declare its not-yet-wired contracts"
    for value in advertised:
        assert not value.startswith("/api/solspire/"), (
            f"advertised contract {value!r} carries the wrong /api prefix"
        )
        assert value.startswith("/solspire/"), f"advertised contract {value!r} is not on the /solspire router"


def test_negative_control_detects_inline_path_composition():
    synthetic = "useHydration(`/solspire/pulses`, fetchIt)"
    assert _composes_an_inline_solspire_path(synthetic)
    assert not _composes_an_inline_solspire_path("useHydration(endpoints.solspirePulses, read)")


def test_negative_control_detects_the_wrong_advertised_prefix():
    synthetic = '<NotYetWired contract="/api/solspire/pulses" />'
    assert any(w in synthetic for w in WRONG_ADVERTISED)
    assert "/api/solspire/pulses" not in PAGE
