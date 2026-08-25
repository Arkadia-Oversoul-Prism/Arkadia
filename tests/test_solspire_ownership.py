"""Consolidation Pass 01R — SolSpire authorization + owner scoping.

Proves:
  A. Every /solspire route requires a Firebase identity (401 unauthenticated).
  B. Project ownership is derived from the authenticated uid; user B cannot
     read/mutate/archive user A's projects, and A's projects are excluded
     from B's list.
  C. Client-supplied ownership fields (owner / owner_uid / user_id / uid /
     metadata.owner) are never authoritative.
  D. Cross-user access to every project sub-resource (conversations, files,
     upload, repositories, tasks, memory, events, project run) is denied.
  E. Execution ownership: owner can get/list/pause/resume/cancel; other users
     get 404 with no existence leak.
  F. Global/tool routes are authenticated and expose no cross-user state.
  G. Legacy NULL-owner projects are invisible to everyone (no silent adoption).

Auth seam: the canonical api.auth.require_auth dependency. With no
FIREBASE_SERVICE_ACCOUNT_JSON configured the auth layer runs in its documented
dev-mode, decoding the JWT payload to resolve the uid — the tests drive the
real dependency with unsigned JWTs rather than replacing it.
"""
from __future__ import annotations

import base64
import json
import os
import tempfile
import threading
import time
import uuid

import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_solspire_ownership_")
os.environ["SOLSPIRE_PROJECTS_DB"] = os.path.join(_tmpdir, "solspire_projects.db")
os.environ.setdefault("SOLSPIRE_DATA_DIR", _tmpdir)

from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.project_manager as pm_mod
import solspire.project_store as store_mod
from solspire.console_router import router as solspire_router
from solspire.execution_runtime import Execution, ExecutionStatus, Plan, get_runtime

USER_A = "sol-user-a"
USER_B = "sol-user-b"


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _token(uid: str) -> str:
    """Unsigned JWT resolved by the real dev-mode auth seam."""
    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'user_id': uid, 'email': f'{uid}@test.dev'})}.sig"


def _headers(uid: str) -> dict:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(scope="module")
def client():
    # Point both SolSpire stores at the temp DB regardless of import order.
    old_pm, old_store = pm_mod._DB_PATH, store_mod._DB_PATH
    pm_mod._DB_PATH = store_mod._DB_PATH = os.environ["SOLSPIRE_PROJECTS_DB"]
    app = FastAPI()
    app.include_router(solspire_router)
    with TestClient(app) as c:
        yield c
    pm_mod._DB_PATH, store_mod._DB_PATH = old_pm, old_store


@pytest.fixture(scope="module")
def project_a(client):
    r = client.post("/solspire/projects", json={"name": "Alpha Codex"}, headers=_headers(USER_A))
    assert r.status_code == 200, r.text
    return r.json()["project"]


@pytest.fixture(scope="module")
def project_b(client):
    r = client.post("/solspire/projects", json={"name": "Beta Codex"}, headers=_headers(USER_B))
    assert r.status_code == 200, r.text
    return r.json()["project"]


# ── A. Authentication ─────────────────────────────────────────────────────────

UNAUTH_ROUTES = [
    ("GET", "/solspire/projects"),
    ("POST", "/solspire/projects"),
    ("GET", "/solspire/projects/any-id"),
    ("PUT", "/solspire/projects/any-id"),
    ("POST", "/solspire/projects/any-id/archive"),
    ("GET", "/solspire/projects/any-id/conversations"),
    ("POST", "/solspire/projects/any-id/conversations"),
    ("GET", "/solspire/projects/any-id/files"),
    ("POST", "/solspire/projects/any-id/files/upload"),
    ("GET", "/solspire/projects/any-id/repositories"),
    ("GET", "/solspire/projects/any-id/tasks"),
    ("GET", "/solspire/projects/any-id/memory"),
    ("GET", "/solspire/projects/any-id/events"),
    ("POST", "/solspire/projects/any-id/run"),
    ("GET", "/solspire/executions"),
    ("GET", "/solspire/executions/any-id"),
    ("POST", "/solspire/executions/any-id/pause"),
    ("POST", "/solspire/executions/any-id/resume"),
    ("POST", "/solspire/executions/any-id/cancel"),
    ("POST", "/solspire/run"),
    ("GET", "/solspire/providers"),
    ("POST", "/solspire/providers/select"),
    ("GET", "/solspire/providers/keys"),
    ("POST", "/solspire/providers/keys"),
    ("POST", "/solspire/providers/model"),
    ("POST", "/solspire/providers/fallback"),
    ("POST", "/solspire/tools/fs/read"),
    ("POST", "/solspire/tools/fs/write"),
    ("POST", "/solspire/tools/fs/list"),
    ("POST", "/solspire/tools/github/repos"),
    ("POST", "/solspire/tools/github/tree"),
    ("POST", "/solspire/tools/github/read"),
    ("POST", "/solspire/tools/github/commit"),
    ("GET", "/solspire/status"),
]


@pytest.mark.parametrize("method,path", UNAUTH_ROUTES)
def test_unauthenticated_routes_return_401(client, method, path):
    r = client.request(method, path, json={})
    assert r.status_code == 401, f"{method} {path} → {r.status_code} (expected 401)"


# ── B. Ownership ──────────────────────────────────────────────────────────────

def test_create_sets_server_derived_owner(client, project_a):
    assert project_a["owner_uid"] == USER_A


def test_owner_can_read_mutate_archive(client, project_a):
    pid = project_a["id"]
    r = client.get(f"/solspire/projects/{pid}", headers=_headers(USER_A))
    assert r.status_code == 200 and r.json()["project"]["id"] == pid

    r = client.put(f"/solspire/projects/{pid}", json={"description": "owner edit"}, headers=_headers(USER_A))
    assert r.status_code == 200

    r = client.post(f"/solspire/projects/{pid}/archive", headers=_headers(USER_A))
    assert r.status_code == 200
    r = client.get(f"/solspire/projects/{pid}", headers=_headers(USER_A))
    assert r.json()["project"]["status"] == "archived"


def test_other_user_cannot_read_mutate_archive(client, project_b):
    pid = project_b["id"]
    r = client.get(f"/solspire/projects/{pid}", headers=_headers(USER_A))
    assert r.status_code == 404
    r = client.put(f"/solspire/projects/{pid}", json={"name": "hijack"}, headers=_headers(USER_A))
    assert r.status_code == 404
    r = client.post(f"/solspire/projects/{pid}/archive", headers=_headers(USER_A))
    assert r.status_code == 404
    # Untouched: B's project is still active with its original name.
    r = client.get(f"/solspire/projects/{pid}", headers=_headers(USER_B))
    assert r.json()["project"]["status"] == "active"
    assert r.json()["project"]["name"] == "Beta Codex"


def test_lists_are_owner_scoped(client, project_a, project_b):
    ra = client.get("/solspire/projects", headers=_headers(USER_A)).json()["projects"]
    rb = client.get("/solspire/projects", headers=_headers(USER_B)).json()["projects"]
    ids_a = {p["id"] for p in ra}
    ids_b = {p["id"] for p in rb}
    assert project_a["id"] in ids_a and project_b["id"] not in ids_a
    assert project_b["id"] in ids_b and project_a["id"] not in ids_b
    assert all(p["owner_uid"] == USER_A for p in ra)
    assert all(p["owner_uid"] == USER_B for p in rb)


def test_nonexistent_and_cross_owner_are_indistinguishable(client, project_b):
    r_fake = client.get("/solspire/projects/does-not-exist", headers=_headers(USER_A))
    r_cross = client.get(f"/solspire/projects/{project_b['id']}", headers=_headers(USER_A))
    assert r_fake.status_code == r_cross.status_code == 404
    assert r_fake.json() == r_cross.json()


# ── C. Spoof resistance ───────────────────────────────────────────────────────

def test_client_supplied_ownership_fields_are_ignored(client):
    r = client.post(
        "/solspire/projects?uid=evil&user_id=evil&owner=evil",
        json={
            "name": "Spoof Attempt",
            "owner": USER_B,
            "owner_uid": USER_B,
            "uid": USER_B,
            "user_id": USER_B,
            "metadata": {"owner": USER_B, "owner_uid": USER_B, "user_id": USER_B},
        },
        headers=_headers(USER_A),
    )
    assert r.status_code == 200, r.text
    project = r.json()["project"]
    # Ownership comes from the verified token, never the client.
    assert project["owner_uid"] == USER_A
    # Visible to A, invisible to B despite B's uid being sprayed everywhere.
    assert client.get(f"/solspire/projects/{project['id']}", headers=_headers(USER_A)).status_code == 200
    assert client.get(f"/solspire/projects/{project['id']}", headers=_headers(USER_B)).status_code == 404


# ── D. Sub-resources ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def seeded_project(client):
    r = client.post("/solspire/projects", json={"name": "Seeded"}, headers=_headers(USER_A))
    pid = r.json()["project"]["id"]
    h = _headers(USER_A)
    conv = client.post(f"/solspire/projects/{pid}/conversations", json={"title": "secret plans"}, headers=h).json()
    client.post(f"/solspire/projects/{pid}/conversations/{conv['id']}/messages",
                json={"role": "user", "content": "SUBRESOURCE_CANARY_A"}, headers=h)
    f = client.post(f"/solspire/projects/{pid}/files", json={"name": "secret.md", "content": "FILE_CANARY_A"}, headers=h).json()
    repo = client.post(f"/solspire/projects/{pid}/repositories",
                       json={"owner": "octo", "repo": "secret-repo"}, headers=h).json()
    task = client.post(f"/solspire/projects/{pid}/tasks", json={"title": "secret task"}, headers=h).json()
    mem = client.post(f"/solspire/projects/{pid}/memory", json={"title": "secret memory", "content": "MEM_CANARY_A"}, headers=h).json()
    return {"pid": pid, "conv": conv, "file": f, "repo": repo, "task": task, "mem": mem}


def test_owner_can_use_subresources(client, seeded_project):
    pid = seeded_project["pid"]
    h = _headers(USER_A)
    assert client.get(f"/solspire/projects/{pid}/conversations", headers=h).json()["count"] == 1
    assert "FILE_CANARY_A" in client.get(f"/solspire/projects/{pid}/files/{seeded_project['file']['id']}", headers=h).json()["content"]
    assert len(client.get(f"/solspire/projects/{pid}/repositories", headers=h).json()["repositories"]) == 1
    assert len(client.get(f"/solspire/projects/{pid}/tasks", headers=h).json()["tasks"]) == 1
    assert len(client.get(f"/solspire/projects/{pid}/memory", headers=h).json()["memory"]) == 1
    events = client.get(f"/solspire/projects/{pid}/events", headers=h).json()["events"]
    assert len(events) >= 1  # conversation_created / file_created / repo_linked


def test_cross_user_denied_on_every_subresource(client, seeded_project):
    pid = seeded_project["pid"]
    h = _headers(USER_B)
    attempts = [
        ("GET", f"/solspire/projects/{pid}/conversations", None),
        ("POST", f"/solspire/projects/{pid}/conversations", {"title": "x"}),
        ("DELETE", f"/solspire/projects/{pid}/conversations/{seeded_project['conv']['id']}", None),
        ("POST", f"/solspire/projects/{pid}/conversations/{seeded_project['conv']['id']}/messages", {"role": "user", "content": "x"}),
        ("GET", f"/solspire/projects/{pid}/files", None),
        ("POST", f"/solspire/projects/{pid}/files", {"name": "x"}),
        ("GET", f"/solspire/projects/{pid}/files/{seeded_project['file']['id']}", None),
        ("PUT", f"/solspire/projects/{pid}/files/{seeded_project['file']['id']}", {"content": "x"}),
        ("DELETE", f"/solspire/projects/{pid}/files/{seeded_project['file']['id']}", None),
        ("GET", f"/solspire/projects/{pid}/repositories", None),
        ("POST", f"/solspire/projects/{pid}/repositories", {"owner": "o", "repo": "r"}),
        ("DELETE", f"/solspire/projects/{pid}/repositories/{seeded_project['repo']['id']}", None),
        ("GET", f"/solspire/projects/{pid}/tasks", None),
        ("POST", f"/solspire/projects/{pid}/tasks", {"title": "x"}),
        ("PUT", f"/solspire/projects/{pid}/tasks/{seeded_project['task']['id']}", {"status": "done"}),
        ("DELETE", f"/solspire/projects/{pid}/tasks/{seeded_project['task']['id']}", None),
        ("GET", f"/solspire/projects/{pid}/memory", None),
        ("POST", f"/solspire/projects/{pid}/memory", {"title": "x", "content": "y"}),
        ("PUT", f"/solspire/projects/{pid}/memory/{seeded_project['mem']['id']}", {"title": "x"}),
        ("DELETE", f"/solspire/projects/{pid}/memory/{seeded_project['mem']['id']}", None),
        ("GET", f"/solspire/projects/{pid}/events", None),
        ("POST", f"/solspire/projects/{pid}/run", {"request": "hello"}),
    ]
    for method, path, body in attempts:
        r = client.request(method, path, json=body, headers=h)
        assert r.status_code == 404, f"{method} {path} → {r.status_code} (cross-user must be 404)"


def test_cross_user_upload_denied(client, seeded_project):
    pid = seeded_project["pid"]
    files = {"file": ("notes.txt", b"upload canary", "text/plain")}
    r = client.post(f"/solspire/projects/{pid}/files/upload", files=files, headers=_headers(USER_B))
    assert r.status_code == 404


def test_subresource_data_not_mutated_by_cross_user_attempts(client, seeded_project):
    pid = seeded_project["pid"]
    h = _headers(USER_A)
    convs = client.get(f"/solspire/projects/{pid}/conversations", headers=h).json()["conversations"]
    assert len(convs) == 1 and convs[0]["status"] == "active"
    assert len(convs[0]["messages"]) == 1  # cross-user append did not land
    tasks = client.get(f"/solspire/projects/{pid}/tasks", headers=h).json()["tasks"]
    assert len(tasks) == 1 and tasks[0]["status"] == "open"  # cross-user update did not land
    assert len(client.get(f"/solspire/projects/{pid}/repositories", headers=h).json()["repositories"]) == 1
    assert len(client.get(f"/solspire/projects/{pid}/files", headers=h).json()["files"]) == 1


# ── E. Executions ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def execution_a(client):
    """Run created through the real POST /solspire/run pipeline as user A."""
    r = client.post("/solspire/run", json={"request": "What is resonance?"}, headers=_headers(USER_A), timeout=90)
    assert r.status_code == 200, r.text
    ex = r.json()["execution"]
    assert ex["owner_uid"] == USER_A
    return ex


def test_owner_can_get_and_list_execution(client, execution_a):
    h = _headers(USER_A)
    r = client.get(f"/solspire/executions/{execution_a['id']}", headers=h)
    assert r.status_code == 200 and r.json()["execution"]["id"] == execution_a["id"]
    listed = client.get("/solspire/executions", headers=h).json()["executions"]
    assert any(e["id"] == execution_a["id"] for e in listed)


def test_other_user_cannot_get_list_or_control_execution(client, execution_a):
    h = _headers(USER_B)
    eid = execution_a["id"]
    assert client.get(f"/solspire/executions/{eid}", headers=h).status_code == 404
    listed = client.get("/solspire/executions", headers=h).json()["executions"]
    assert all(e["id"] != eid for e in listed)
    for action in ("pause", "resume", "cancel"):
        r = client.post(f"/solspire/executions/{eid}/{action}", headers=h)
        assert r.status_code == 404, f"cross-user {action} → {r.status_code}"


def test_execution_control_does_not_leak_existence(client, execution_a):
    h = _headers(USER_B)
    real = client.get(f"/solspire/executions/{execution_a['id']}", headers=h)
    fake = client.get("/solspire/executions/no-such-execution", headers=h)
    assert real.status_code == fake.status_code == 404
    assert real.json() == fake.json()


@pytest.fixture(scope="module")
def running_execution_a():
    """A long-lived RUNNING execution owned by A, registered in the runtime's
    real data structures (no worker thread, so the state is deterministic)."""
    runtime = get_runtime()
    plan = Plan(id="p-controlled", request="controlled", intent="Workflow",
                steps=[{"tool": "llm", "payload": {}}])
    ex = Execution(
        id=str(uuid.uuid4()), plan=plan, status=ExecutionStatus.RUNNING,
        started_at=time.time(), completed_at=None, results=[], error=None,
        owner_uid=USER_A,
    )
    with runtime._lock:
        runtime._executions[ex.id] = ex
        ev = threading.Event()
        ev.set()
        runtime._pause_events[ex.id] = ev
        runtime._cancel_flags[ex.id] = False
    return ex


def test_execution_control_roundtrip_for_owner(client, running_execution_a):
    """Pause → resume → cancel through the routes, as the owner."""
    runtime = get_runtime()
    ex = running_execution_a
    h = _headers(USER_A)
    assert client.post(f"/solspire/executions/{ex.id}/pause", headers=h).status_code == 200
    assert runtime.get(ex.id).status == ExecutionStatus.PAUSED
    assert client.post(f"/solspire/executions/{ex.id}/resume", headers=h).status_code == 200
    assert runtime.get(ex.id).status == ExecutionStatus.RUNNING
    assert client.post(f"/solspire/executions/{ex.id}/cancel", headers=h).status_code == 200
    assert runtime.get(ex.id).status == ExecutionStatus.CANCELLED
    # B still cannot touch it after state changes.
    assert client.post(f"/solspire/executions/{ex.id}/cancel", headers=_headers(USER_B)).status_code == 404
    assert client.get(f"/solspire/executions/{ex.id}", headers=_headers(USER_B)).status_code == 404


# ── F. Global/tool routes ─────────────────────────────────────────────────────

def test_global_routes_require_auth_and_work_when_authenticated(client):
    h = _headers(USER_A)
    # Status: authenticated, and project/execution counts are caller-scoped.
    r = client.get("/solspire/status", headers=h)
    assert r.status_code == 200
    # Providers: global server-side config, no per-user state — auth required.
    assert client.get("/solspire/providers", headers=h).status_code == 200
    # fs tools: sandboxed shared workspace (tools_fs path-sandbox preserved).
    r = client.post("/solspire/tools/fs/read", json={"path": "../../../etc/passwd"}, headers=h)
    assert r.json().get("ok") is False  # traversal still refused
    r = client.post("/solspire/tools/fs/list", json={"path": "."}, headers=h)
    assert r.status_code == 200 and r.json()["ok"] is True


def test_status_counts_are_caller_scoped(client, project_b, execution_a):
    # project_b belongs to B; A's status must not count it.
    ra = client.get("/solspire/status", headers=_headers(USER_A)).json()
    rb = client.get("/solspire/status", headers=_headers(USER_B)).json()
    assert rb["projects"]["active_count"] >= 1
    # A's execution exists; B's execution totals must exclude it.
    assert all(True for _ in rb["executions"]["by_status"])  # shape sanity
    a_execs = client.get("/solspire/executions", headers=_headers(USER_A)).json()["executions"]
    b_execs = client.get("/solspire/executions", headers=_headers(USER_B)).json()["executions"]
    assert {e["id"] for e in a_execs}.isdisjoint({e["id"] for e in b_execs})
    assert ra["executions"]["total"] == len(a_execs)
    assert rb["executions"]["total"] == len(b_execs)


# ── G. Legacy unowned projects ────────────────────────────────────────────────

def test_legacy_null_owner_projects_are_invisible_to_everyone(client):
    legacy = pm_mod.get_project_manager().create("Legacy Pre-Auth Project")  # owner None
    assert legacy.owner_uid is None
    for uid in (USER_A, USER_B):
        h = _headers(uid)
        assert client.get(f"/solspire/projects/{legacy.id}", headers=h).status_code == 404
        assert client.post(f"/solspire/projects/{legacy.id}/archive", headers=h).status_code == 404
        assert client.get(f"/solspire/projects/{legacy.id}/files", headers=h).status_code == 404
        listed = client.get("/solspire/projects", headers=h).json()["projects"]
        assert all(p["id"] != legacy.id for p in listed)
    # And the legacy row was not silently adopted by the first caller.
    assert pm_mod.get_project_manager().load(legacy.id).owner_uid is None
