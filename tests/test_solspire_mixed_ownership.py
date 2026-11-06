"""AO4-02 — cross-tenant sub-resource mutation (mixed ownership).

The existing suite in `test_solspire_ownership.py` proves that a caller who does
not own the project in the URL is refused. It does **not** prove the converse,
which is the actual vulnerability:

    the caller owns project B, the row belongs to project A, and the request
    names project B in the URL with project A's row id.

`require_project_owner` authorizes the *project in the URL*. If the store then
mutates by primary key alone (`WHERE id = ?`), the ownership check passes and
the write lands on a row in a project the caller has no authority over. That is
a cross-tenant write, and it is invisible to a test that only ever uses the
victim's project id in the URL.

Every test here therefore:
  1. creates a victim row in project A (owned by USER_A),
  2. issues the mutation as USER_B against **project B** (which USER_B owns)
     using project A's row id,
  3. asserts the response is the same existence-hiding 404 an unknown id gets,
  4. asserts the victim row is byte-for-byte unchanged.

Auth seam: identical to `test_solspire_ownership.py` — the real
`api.auth.require_auth` dependency in its documented dev-mode, driven with
unsigned JWTs. No production credential, no weakened verification.
"""
from __future__ import annotations

import base64
import json
import os
import tempfile

import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_solspire_mixed_ownership_")
_SOL_DB = os.path.join(_tmpdir, "solspire_projects.db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.project_manager as pm_mod
import solspire.project_store as store_mod
from solspire.console_router import router as solspire_router

OWNER = "mixed-owner-a"
ATTACKER = "mixed-owner-b"


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _token(uid: str) -> str:
    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'user_id': uid, 'email': f'{uid}@test.dev'})}.sig"


def _headers(uid: str) -> dict:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(scope="module")
def client():
    old_pm, old_store = pm_mod._DB_PATH, store_mod._DB_PATH
    pm_mod._DB_PATH = store_mod._DB_PATH = _SOL_DB
    app = FastAPI()
    app.include_router(solspire_router)
    with TestClient(app) as c:
        yield c
    pm_mod._DB_PATH, store_mod._DB_PATH = old_pm, old_store


@pytest.fixture(scope="module")
def tenants(client):
    """Project A (victim, owned by OWNER) and project B (attacker's own)."""
    a = client.post("/solspire/projects", json={"name": "Victim A"}, headers=_headers(OWNER)).json()["project"]
    b = client.post("/solspire/projects", json={"name": "Attacker B"}, headers=_headers(ATTACKER)).json()["project"]
    return {"a": a["id"], "b": b["id"]}


@pytest.fixture(scope="module")
def victim_rows(client, tenants):
    """One row of every mutable sub-resource, created in project A."""
    pid = tenants["a"]
    h = _headers(OWNER)
    task = client.post(f"/solspire/projects/{pid}/tasks",
                       json={"title": "victim task", "description": "ORIGINAL"}, headers=h).json()
    mem = client.post(f"/solspire/projects/{pid}/memory",
                      json={"title": "victim memory", "content": "ORIGINAL"}, headers=h).json()
    fil = client.post(f"/solspire/projects/{pid}/files",
                      json={"name": "victim.md", "content": "ORIGINAL"}, headers=h).json()
    repo = client.post(f"/solspire/projects/{pid}/repositories",
                       json={"owner": "octo", "repo": "victim-repo"}, headers=h).json()
    return {"task": task, "mem": mem, "file": fil, "repo": repo}


# ── The core vulnerability: URL project B + project A's row id ────────────────

def test_cross_tenant_task_update_is_denied_and_does_not_mutate(client, tenants, victim_rows):
    """AO4-02: the reported finding, exactly as described."""
    task_id = victim_rows["task"]["id"]
    r = client.put(
        f"/solspire/projects/{tenants['b']}/tasks/{task_id}",
        json={"title": "PWNED", "status": "done"},
        headers=_headers(ATTACKER),
    )
    # Same 404 an unknown id gets — no existence leak, no "forbidden" oracle.
    assert r.status_code == 404, f"cross-tenant task update returned {r.status_code}"

    # The victim row is untouched.
    tasks = client.get(f"/solspire/projects/{tenants['a']}/tasks", headers=_headers(OWNER)).json()["tasks"]
    row = next(t for t in tasks if t["id"] == task_id)
    assert row["title"] == "victim task"
    assert row["status"] == "open"


def test_cross_tenant_task_delete_is_denied_and_does_not_mutate(client, tenants, victim_rows):
    task_id = victim_rows["task"]["id"]
    r = client.delete(
        f"/solspire/projects/{tenants['b']}/tasks/{task_id}",
        headers=_headers(ATTACKER),
    )
    assert r.status_code == 404, f"cross-tenant task delete returned {r.status_code}"

    tasks = client.get(f"/solspire/projects/{tenants['a']}/tasks", headers=_headers(OWNER)).json()["tasks"]
    assert any(t["id"] == task_id for t in tasks), "victim task was deleted across tenants"


def test_cross_tenant_memory_update_and_delete_are_denied(client, tenants, victim_rows):
    mem_id = victim_rows["mem"]["id"]
    h = _headers(ATTACKER)

    r = client.put(f"/solspire/projects/{tenants['b']}/memory/{mem_id}",
                   json={"title": "PWNED", "content": "PWNED"}, headers=h)
    assert r.status_code == 404, f"cross-tenant memory update returned {r.status_code}"

    r = client.delete(f"/solspire/projects/{tenants['b']}/memory/{mem_id}", headers=h)
    assert r.status_code == 404, f"cross-tenant memory delete returned {r.status_code}"

    mem = client.get(f"/solspire/projects/{tenants['a']}/memory", headers=_headers(OWNER)).json()["memory"]
    row = next(m for m in mem if m["id"] == mem_id)
    assert row["title"] == "victim memory"
    assert row["content"] == "ORIGINAL"


def test_cross_tenant_file_update_and_delete_are_denied(client, tenants, victim_rows):
    file_id = victim_rows["file"]["id"]
    h = _headers(ATTACKER)

    r = client.put(f"/solspire/projects/{tenants['b']}/files/{file_id}",
                   json={"content": "PWNED"}, headers=h)
    assert r.status_code == 404, f"cross-tenant file update returned {r.status_code}"

    r = client.delete(f"/solspire/projects/{tenants['b']}/files/{file_id}", headers=h)
    assert r.status_code == 404, f"cross-tenant file delete returned {r.status_code}"

    f = client.get(f"/solspire/projects/{tenants['a']}/files/{file_id}", headers=_headers(OWNER)).json()
    assert f["content"] == "ORIGINAL"


def test_cross_tenant_repository_unlink_is_denied(client, tenants, victim_rows):
    repo_id = victim_rows["repo"]["id"]
    r = client.delete(
        f"/solspire/projects/{tenants['b']}/repositories/{repo_id}",
        headers=_headers(ATTACKER),
    )
    assert r.status_code == 404, f"cross-tenant repo unlink returned {r.status_code}"

    repos = client.get(f"/solspire/projects/{tenants['a']}/repositories",
                       headers=_headers(OWNER)).json()["repositories"]
    assert any(x["id"] == repo_id for x in repos), "victim repository was unlinked across tenants"


# ── The owner must still be able to do all of it (no over-correction) ─────────

def test_owner_can_still_update_and_delete_own_rows(client, tenants):
    """The scoping fix must not break the legitimate path."""
    pid = tenants["a"]
    h = _headers(OWNER)

    task = client.post(f"/solspire/projects/{pid}/tasks", json={"title": "mine"}, headers=h).json()
    r = client.put(f"/solspire/projects/{pid}/tasks/{task['id']}", json={"status": "done"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert client.delete(f"/solspire/projects/{pid}/tasks/{task['id']}", headers=h).status_code == 200

    mem = client.post(f"/solspire/projects/{pid}/memory", json={"title": "m", "content": "c"}, headers=h).json()
    assert client.put(f"/solspire/projects/{pid}/memory/{mem['id']}", json={"title": "m2"}, headers=h).status_code == 200
    assert client.delete(f"/solspire/projects/{pid}/memory/{mem['id']}", headers=h).status_code == 200

    fil = client.post(f"/solspire/projects/{pid}/files", json={"name": "f.md", "content": "c"}, headers=h).json()
    assert client.put(f"/solspire/projects/{pid}/files/{fil['id']}", json={"content": "c2"}, headers=h).status_code == 200
    assert client.delete(f"/solspire/projects/{pid}/files/{fil['id']}", headers=h).status_code == 200

    repo = client.post(f"/solspire/projects/{pid}/repositories",
                       json={"owner": "o", "repo": "r"}, headers=h).json()
    assert client.delete(f"/solspire/projects/{pid}/repositories/{repo['id']}", headers=h).status_code == 200


def test_unknown_row_id_is_indistinguishable_from_cross_tenant(client, tenants):
    """A nonexistent id and another tenant's id must produce the same response."""
    h = _headers(ATTACKER)
    bogus = "00000000-0000-0000-0000-000000000000"
    for path in (
        f"/solspire/projects/{tenants['b']}/tasks/{bogus}",
        f"/solspire/projects/{tenants['b']}/memory/{bogus}",
        f"/solspire/projects/{tenants['b']}/files/{bogus}",
        f"/solspire/projects/{tenants['b']}/repositories/{bogus}",
    ):
        r = client.delete(path, headers=h)
        assert r.status_code == 404
        assert r.json()["detail"] in {
            "Task not found", "Memory entry not found", "File not found", "Repository not found"
        }
