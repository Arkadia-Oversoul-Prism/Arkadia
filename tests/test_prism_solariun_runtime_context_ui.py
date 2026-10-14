"""Solariun project runtime-context canvas — PRR-03.

The Solariun `projects` lens advertised `runtime-context` as not-yet-wired while
the canonical backend serves a bounded, owner-scoped projection of exactly that
(`solspire/console_router.py::project_runtime_context`, mounted under the
`/solspire` router). This work item wires the read: a per-project control in
the projects lens opens a canvas that renders the projection's actual binding
states — UNKNOWN stays UNKNOWN — and repeats the endpoint's own epistemic
boundary instead of inferring one.

Domain: the Arkadia Console (`web/arkadia_console`) over the canonical FastAPI
app. Read-only: no control here mutates project, pulse, workload, or weaver
state, and none is offered.

The backend half is **executed**: a TestClient over the real `console_router`
with isolated SQLite paths asserts the served shape, the deliberate 404
ambiguity (`require_project_owner` answers identically for a missing project
and a foreign one — existence is never leaked), and the 401 without identity.
The frontend half is the repository's source-contract convention with negative
controls; the path builder is executed in Node.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.project_manager as project_manager
import solspire.project_store as project_store
import solspire.workspace_manager as workspace_manager
from api.auth import require_auth
from solspire.console_router import router as console_router

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"
CANVAS_PATH = SRC / "components" / "solariun" / "ProjectRuntimeCanvas.tsx"
SOLARIUN_PATH = SRC / "pages" / "SolariunPage.tsx"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"

CANVAS = CANVAS_PATH.read_text(encoding="utf-8")
SOLARIUN = SOLARIUN_PATH.read_text(encoding="utf-8")
ENDPOINTS = ENDPOINTS_PATH.read_text(encoding="utf-8")

OWNER = {"uid": "rc-owner", "access_level": 1}
OTHER = {"uid": "rc-other", "access_level": 1}


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def _wires_the_canvas(text: str) -> bool:
    """The projects lens offers a per-project control and mounts the canvas."""
    return "solariun-runtime-" in text and "ProjectRuntimeCanvas" in text


def _code_only(text: str) -> str:
    """Comments may name the route freely; only code composes paths."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return text


def _composes_an_inline_path(text: str) -> bool:
    """A raw `/solspire/...` composition outside the registry = second contract."""
    return bool(re.search(r"[`\"']/?solspire/", _code_only(text)))


# ---------------------------------------------------------------------------
# Backend half — executed against the real router
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(project_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(project_store, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))
    application = FastAPI()
    application.include_router(console_router)
    yield application
    application.dependency_overrides.clear()


def _client(app: FastAPI, user: dict | None) -> TestClient:
    app.dependency_overrides.pop(require_auth, None)
    if user is not None:
        app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _project(owner_uid: str, name: str = "Runtime project") -> str:
    return project_manager.get_project_manager().create(name=name, owner_uid=owner_uid).id


def test_owner_reads_the_bounded_projection(app):
    pid = _project(OWNER["uid"])
    response = _client(app, OWNER).get(f"/solspire/projects/{pid}/runtime-context")
    assert response.status_code == 200
    body = response.json()
    for key in ("project", "project_store", "knowledge_graph", "control_plane", "binding_state"):
        assert key in body, key
    assert body["project"]["id"] == pid
    assert body["project"]["name"] == "Runtime project"
    # Nothing is inferred: with no workspace, the spines report UNKNOWN.
    assert body["control_plane"]["workspace"] is None
    assert body["binding_state"]["daily_pulse"] == "UNKNOWN"
    assert body["binding_state"]["workload"].startswith("UNKNOWN") or "BOUND" in body["binding_state"]["workload"]
    # The endpoint carries its own epistemic boundary; the canvas repeats it.
    assert "not authority" in body["epistemic_boundary"]
    for store_key in ("tasks", "files", "memory", "events", "repositories"):
        assert isinstance(body["project_store"][store_key], list), store_key


def test_unauthenticated_caller_is_refused(app):
    pid = _project(OWNER["uid"])
    response = _client(app, None).get(f"/solspire/projects/{pid}/runtime-context")
    assert response.status_code == 401


def test_missing_and_foreign_projects_are_indistinguishable(app):
    pid = _project(OWNER["uid"])
    client = _client(app, OTHER)
    missing = client.get("/solspire/projects/does-not-exist/runtime-context")
    foreign = client.get(f"/solspire/projects/{pid}/runtime-context")
    assert missing.status_code == 404
    assert foreign.status_code == 404
    assert missing.json() == foreign.json(), (
        "the contract must not leak which of the two refusals occurred"
    )


def test_the_read_mutates_nothing(app):
    pid = _project(OWNER["uid"])
    client = _client(app, OWNER)
    first = client.get(f"/solspire/projects/{pid}/runtime-context").json()
    second = client.get(f"/solspire/projects/{pid}/runtime-context").json()
    # retrieved_at may differ; the state must not.
    for key in ("project", "project_store", "control_plane", "binding_state"):
        assert first[key] == second[key], key


# ---------------------------------------------------------------------------
# Frontend half — source contracts with negative controls
# ---------------------------------------------------------------------------


def test_canvas_reads_through_the_registry_derived_builder():
    assert "solspireProjectRuntime(projectId)" in CANVAS, (
        "the canvas must read through the registry-derived builder"
    )
    assert "solspireProjects" not in CANVAS, (
        "the canvas must not compose the collection path itself"
    )
    assert not _composes_an_inline_path(CANVAS)


def test_builder_is_declared_in_the_registry_module_and_serves_the_handler_path():
    builder = re.search(r"export function solspireProjectRuntime.*?\n\}", ENDPOINTS, re.DOTALL)
    assert builder, "endpoints.ts declares no solspireProjectRuntime builder"
    assert "endpoints.solspireProjects" in builder.group(0), "the builder must derive from the registry"
    assert "encodeURIComponent" in builder.group(0), "the id must be percent-encoded"


def test_builder_executed_in_node_serves_and_encodes():
    node = shutil.which("node")
    assert node, "node is required to evaluate the path builder"
    script = (
        ENDPOINTS.replace("export ", "")
        + "\nconsole.log(JSON.stringify(["
        + 'solspireProjectRuntime("abc"),'
        + 'solspireProjectRuntime("a/b?c#d")'
        + "]));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr.strip()
    plain, hostile = json.loads(result.stdout)
    assert plain == "/solspire/projects/abc/runtime-context"
    assert hostile == "/solspire/projects/a%2Fb%3Fc%23d/runtime-context", (
        "an id containing / ? or # must not address a different route"
    )


def test_projects_lens_wires_a_real_control_and_mounts_the_canvas():
    assert _wires_the_canvas(SOLARIUN)
    assert "aria-pressed" in SOLARIUN, "the per-project toggle must expose its state"
    assert "/api/solspire/projects/{id}/runtime-context" not in SOLARIUN, (
        "the not-yet-wired placeholder this replaces must be gone"
    )


def test_negative_control_detects_an_unwired_projects_lens():
    synthetic = "<ul>{projects.map((p) => <li key={p.id}>{p.name}</li>)}</ul>"
    assert not _wires_the_canvas(synthetic)


def test_negative_control_detects_inline_path_composition():
    synthetic = "useHydration(`/solspire/projects/${id}/runtime-context`, fetchIt)"
    assert _composes_an_inline_path(synthetic)
    assert not _composes_an_inline_path(CANVAS)


def test_canvas_states_are_honest():
    # The deliberate 404 ambiguity is explained, not guessed at.
    assert "NOT_FOUND" in CANVAS
    assert "does not exist" in CANVAS and "does not own" in CANVAS
    # UNKNOWN bindings are visually distinct and never rewritten.
    assert 'value === "UNKNOWN"' in CANVAS
    assert "epistemic_boundary" in CANVAS
    # Every hydration state is routed through the shared ContractState.
    assert "ContractState" in CANVAS
