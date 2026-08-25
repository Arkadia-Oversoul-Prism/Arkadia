"""
P1-1 — NovaNet/Transmissions ownership semantics.

Verifies the product acceptance criteria "create a post / see it / delete own post"
while enforcing P1 security invariants:

1. Verified Firebase identity determines ownership (client identity advisory only).
2. Client-supplied author id is never authoritative.
3. Public posts are intentionally public (GET list remains open).
4. Only the owner can delete; anonymous posts are not deletable via API.

Auth resolution is stubbed by replacing the module's injected
``_get_current_user`` callable directly (no mock library): the module defines a
fallback stub at import time, and tests swap the injected function the same way
the production fallback mechanism does.
"""
import os
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import api.transmissions as tx

UID_A = "uid-user-a"
UID_B = "uid-user-b"


def _uid_callable(uid):
    async def _get_current_user(request: Request):  # type: ignore
        return {"uid": uid}
    return _get_current_user


async def _anon_callable(request: Request):  # type: ignore
    return None


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(tx, "DATA_FILE", str(tmp_path / "transmissions.json"))
    tx._get_current_user = _anon_callable
    app = FastAPI()
    app.include_router(tx.router)
    yield TestClient(app)
    tx._get_current_user = _anon_callable


def _as_a(content="post A"):
    return {"content": content, "author": {"name": "User A", "avatar": "◆", "role": "Node"}}


def test_authenticated_create_binds_owner_uid(client):
    tx._get_current_user = _uid_callable(UID_A)
    r = client.post("/api/transmissions", json=_as_a())
    assert r.status_code == 200
    post = r.json()["transmission"]
    assert post["owner_uid"] == UID_A
    # client-supplied author id is overridden by the verified uid
    assert post["author"]["id"] == UID_A
    assert post["author"]["name"] == "User A"


def test_anonymous_create_carries_no_owner(client):
    r = client.post("/api/transmissions", json=_as_a())
    assert r.status_code == 200
    post = r.json()["transmission"]
    assert post["owner_uid"] is None
    assert post["author"]["id"] == "anon"


def test_delete_requires_authentication(client):
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    d = client.delete(f"/api/transmissions/{post_id}")
    assert d.status_code == 401


def test_non_owner_cannot_delete(client):
    tx._get_current_user = _uid_callable(UID_A)
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    tx._get_current_user = _uid_callable(UID_B)
    d = client.delete(f"/api/transmissions/{post_id}")
    assert d.status_code == 403
    # post still visible publicly (intentionally public)
    assert any(p["id"] == post_id for p in client.get("/api/transmissions").json()["transmissions"])


def test_owner_can_delete_and_is_gone(client):
    tx._get_current_user = _uid_callable(UID_A)
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    d = client.delete(f"/api/transmissions/{post_id}")
    assert d.status_code == 200
    assert not any(p["id"] == post_id for p in client.get("/api/transmissions").json()["transmissions"])


def test_anonymous_posts_are_not_deletable_via_api(client):
    # created anonymously
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    # even an authenticated caller cannot delete it
    tx._get_current_user = _uid_callable(UID_A)
    d = client.delete(f"/api/transmissions/{post_id}")
    assert d.status_code == 403


def test_comment_binds_verified_uid(client):
    tx._get_current_user = _uid_callable(UID_A)
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    c = client.post(
        f"/api/transmissions/{post_id}/comment",
        json={"content": "hello", "author": {"id": "spoofed", "name": "User A"}},
    )
    assert c.status_code == 200
    comment = c.json()["comment"]
    assert comment["owner_uid"] == UID_A
    assert comment["author"]["id"] == UID_A


def test_react_and_list_stay_public(client):
    r = client.post("/api/transmissions", json=_as_a())
    post_id = r.json()["transmission"]["id"]
    react = client.post(f"/api/transmissions/{post_id}/react", json={"type": "star"})
    assert react.status_code == 200
    assert react.json()["reactions"]["star"] == 1
    listed = client.get("/api/transmissions")
    assert listed.status_code == 200
