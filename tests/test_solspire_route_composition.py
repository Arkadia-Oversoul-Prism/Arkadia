"""Regression coverage for nested and dynamically registered SolSpire routes."""
import base64
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.planner as planner_mod
import solspire.project_manager as project_manager
import solspire.project_store as project_store
from solspire.console_router import router as solspire_router


EXPECTED_COMPOSED_ROUTES = {
    ("POST", "/solspire/enterprise/workspaces/{enterprise_id}/members"),
    ("DELETE", "/solspire/enterprise/workspaces/{enterprise_id}/members/{handle}/desks/{desk}"),
    ("GET", "/solspire/enterprise/workspaces/{enterprise_id}/tasks"),
    ("PATCH", "/solspire/enterprise/workspaces/{enterprise_id}/tasks/{task_id}"),
    ("GET", "/solspire/enterprise/workspaces/{enterprise_id}/control-room"),
}


def test_dynamic_eden_ops_routes_are_present_at_composed_solspire_paths():
    """The generated OpenAPI schema must include every route after parent prefixes."""
    app = FastAPI()
    app.include_router(solspire_router)

    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, path_item in schema.get("paths", {}).items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}
    }

    missing = EXPECTED_COMPOSED_ROUTES - actual
    assert not missing, f"EDEN-OPS-02 routes missing from composed OpenAPI paths: {sorted(missing)}"


# ── The run pipeline must refuse a mutation plan as a governed 403 ─────────────
#
# `ExecutionRuntime.execute` refuses an engineering mutation plan by raising
# `PermissionError` before a worker thread exists (solspire/execution_runtime.py).
# `_execute_run` did not catch it, so `POST /solspire/run` answered an opaque
# `500 Internal Server Error` for any plan the planner produced with `fs_write`,
# `git_commit`, `git_push` or `github_commit`. The boundary held — nothing ran —
# but the caller could not tell a refused plan from a broken backend. The planner
# prompt asks the model not to emit those tools and `validate_plan` only checks
# structure, so the refusal is reachable from ordinary model output.

MUTATION_TOOL = "fs_write"
READ_ONLY_TOOL = "fs_list"


def _token(uid: str) -> str:
    def b64(payload: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    return f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'user_id': uid, 'email': f'{uid}@test.dev'})}.sig"


def _headers(uid: str = "route-composition-user") -> dict:
    return {"Authorization": f"Bearer {_token(uid)}"}


class _FixedPlanner:
    """Planner stub that yields one step for a chosen tool."""

    def __init__(self, tool: str) -> None:
        self._tool = tool

    def classify(self, request):
        from solspire.intent_router import IntentType

        return IntentType.Question

    def create_plan(self, request, intent):
        from solspire.execution_runtime import Plan

        return Plan(
            id=f"plan-{self._tool}",
            request=request,
            intent=intent.value,
            steps=[{"tool": self._tool, "payload": {"path": "note.md", "content": "x"}}],
            created_at=0.0,
        )

    def validate_plan(self, plan) -> bool:
        return True


@pytest.fixture()
def run_client(tmp_path, monkeypatch):
    """A client on the composed router, isolated from the shared SolSpire store."""
    db = tmp_path / "route-composition.db"
    monkeypatch.setattr(project_manager, "_DB_PATH", str(db), raising=False)
    monkeypatch.setattr(project_store, "_DB_PATH", str(db), raising=False)
    app = FastAPI()
    app.include_router(solspire_router)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _post_run(client, tool: str, monkeypatch):
    monkeypatch.setattr(planner_mod, "get_planner", lambda: _FixedPlanner(tool))
    return client.post("/solspire/run", json={"request": "write a note"}, headers=_headers())


def test_a_mutation_plan_is_refused_with_a_governed_403(run_client, monkeypatch):
    response = _post_run(run_client, MUTATION_TOOL, monkeypatch)

    assert response.status_code == 403, (
        f"a mutation plan must be refused as 403, not {response.status_code}: {response.text[:200]}"
    )
    detail = response.json()["detail"]
    assert detail.startswith("MUTATION_DISABLED:"), detail
    assert "K15" in detail and "K3" in detail, "the refusal must name the governed path"
    assert MUTATION_TOOL in detail, "the refusal must name the blocked tool"


def test_negative_control_a_read_only_plan_is_not_refused(run_client, monkeypatch):
    """Proves the 403 is caused by the mutation tool, not by the route wrapper."""
    response = _post_run(run_client, READ_ONLY_TOOL, monkeypatch)

    assert response.status_code != 403, (
        f"a read-only plan must not be refused as a mutation, got {response.status_code}"
    )
    assert "MUTATION_DISABLED" not in response.text


def test_a_refused_plan_creates_no_execution(run_client, monkeypatch):
    """The boundary still holds: the refusal happens before any execution is recorded."""
    from solspire.execution_runtime import get_runtime

    _post_run(run_client, MUTATION_TOOL, monkeypatch)

    refused_plan_id = f"plan-{MUTATION_TOOL}"
    recorded = get_runtime().list_executions(owner_uid="route-composition-user")
    assert all(e.get("plan_id") != refused_plan_id for e in recorded), (
        "the refused plan must not have created an execution"
    )
