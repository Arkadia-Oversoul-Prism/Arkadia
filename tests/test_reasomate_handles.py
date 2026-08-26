"""Pass 09R: ReasoMate handle discovery, uniqueness, and handle-based send."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.auth import (
    normalize_handle,
    resolve_uid_by_handle,
    public_profile_by_handle,
    save_user_profile_store,
    load_user_profile_store,
)


def test_normalize_handle_accepts_at_and_case():
    assert normalize_handle("@Alice") == "alice"
    assert normalize_handle("Alice") == "alice"
    assert normalize_handle("@alice.dev") == "alice.dev"
    assert normalize_handle("user-name") == "user-name"


def test_normalize_handle_rejects_invalid():
    with pytest.raises(ValueError):
        normalize_handle("")
    with pytest.raises(ValueError):
        normalize_handle("@")
    with pytest.raises(ValueError):
        normalize_handle("a")
    with pytest.raises(ValueError):
        normalize_handle("-bad")
    with pytest.raises(ValueError):
        normalize_handle("x" * 33)


def test_handle_uniqueness_and_discovery(tmp_path, monkeypatch):
    monkeypatch.setattr("api.auth._profiles_dir", lambda: str(tmp_path))
    save_user_profile_store("uid-a", {"username": "@Alpha", "display_name": "Alpha User"})
    assert load_user_profile_store("uid-a")["username"] == "alpha"
    assert resolve_uid_by_handle("@ALPHA") == "uid-a"
    pub = public_profile_by_handle("Alpha")
    assert pub is not None
    assert pub["handle"] == "alpha"
    assert pub["display_name"] == "Alpha User"
    assert "uid" not in pub
    assert "uid-a" not in str(pub)
    with pytest.raises(ValueError, match="taken"):
        save_user_profile_store("uid-b", {"username": "alpha"})


def _client_factory(tmp_path, monkeypatch):
    monkeypatch.setattr("api.auth._profiles_dir", lambda: str(tmp_path / "profiles"))
    monkeypatch.setattr("api.messages._MSG_DIR", str(tmp_path / "messages"))
    os.makedirs(tmp_path / "profiles", exist_ok=True)
    os.makedirs(tmp_path / "messages", exist_ok=True)

    from api.main import app
    from api.auth import require_auth

    def make(uid: str) -> TestClient:
        async def _auth():
            return {"uid": uid, "email": f"{uid}@test.local", "display_name": uid}

        app.dependency_overrides[require_auth] = _auth
        return TestClient(app)

    return make


def test_public_discovery_endpoint_no_uid(tmp_path, monkeypatch):
    make = _client_factory(tmp_path, monkeypatch)
    save_user_profile_store("uid-a", {"username": "solariun", "display_name": "Sol"})
    c = make("uid-a")
    r = c.get("/api/users/by-handle/solariun")
    assert r.status_code == 200
    body = r.json()["user"]
    assert body["handle"] == "solariun"
    assert "uid" not in body
    assert c.get("/api/users/by-handle/nope").status_code == 404
    assert c.get("/api/users/by-handle/-bad").status_code == 400


def test_send_by_handle_auth_sender_and_self_reject(tmp_path, monkeypatch):
    make = _client_factory(tmp_path, monkeypatch)
    save_user_profile_store("uid-a", {"username": "alice"})
    save_user_profile_store("uid-b", {"username": "bob"})

    ca = make("uid-a")
    r = ca.post("/api/messages", json={"recipient_handle": "@bob", "content": "hello bob"})
    assert r.status_code == 200, r.text
    msg = r.json()["message"]
    assert msg["sender_uid"] == "uid-a"
    assert msg["recipient_uid"] == "uid-b"
    assert msg["content"] == "hello bob"

    r2 = ca.post(
        "/api/messages",
        json={"recipient_handle": "bob", "content": "again", "sender_uid": "uid-b"},
    )
    assert r2.status_code == 200
    assert r2.json()["message"]["sender_uid"] == "uid-a"

    r3 = ca.post("/api/messages", json={"recipient_handle": "alice", "content": "to self"})
    assert r3.status_code == 400

    r4 = ca.post("/api/messages", json={"recipient_handle": "nobody", "content": "x"})
    assert r4.status_code == 404


def test_inbox_surfaces_peer_handle(tmp_path, monkeypatch):
    make = _client_factory(tmp_path, monkeypatch)
    save_user_profile_store("uid-a", {"username": "alice"})
    save_user_profile_store("uid-b", {"username": "bob"})
    ca = make("uid-a")
    assert ca.post("/api/messages", json={"recipient_handle": "bob", "content": "hi"}).status_code == 200
    inbox = ca.get("/api/messages/inbox")
    assert inbox.status_code == 200
    convs = inbox.json()["conversations"]
    assert len(convs) >= 1
    peer = next(c for c in convs if c.get("peer_uid") == "uid-b")
    assert peer.get("peer_handle") == "bob"

    th = ca.get("/api/messages/thread/uid-b")
    assert th.status_code == 200
    assert th.json().get("peer_handle") == "bob"
