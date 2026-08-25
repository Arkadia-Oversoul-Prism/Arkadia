"""Consolidation Pass 02 — Echofeild aggregator (GET /api/me/field).

Proves the composed personal-field read model is:
  A. authenticated (401 without a token)
  B. owner-isolated (derived exclusively from the verified uid; client-supplied
     uid/user_id/owner/node_key parameters are never authoritative)
  C/D/E/F. scoped per source (notes, graph, projects, messages)
  G. read-only (no writes to any store)
  H. a stable, secret-free response contract

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

import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_echofeild_")
os.environ["ARKADIA_DB_PATH"] = os.path.join(_tmpdir, "test.db")

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.echofeild as echofeild
import api.messages as messages_mod
import knowledge.vault as vault
from knowledge import timeline as tl
from knowledge.db import get_connection
from knowledge.graph import add_edge

USER_A = "echofeild-user-a"
USER_B = "echofeild-user-b"
USER_C = "echofeild-user-c"

CANARY_A = "ECHOFEILD_CANARY_A_20260825"
CANARY_B = "ECHOFEILD_CANARY_B_20260825"
CANARY_BC = "ECHOFEILD_CANARY_PRIVATE_PAIR_BC_20260825"

EXPECTED_KEYS = {
    "identity", "notes", "graph", "timeline", "projects",
    "conversations", "messages", "executions", "meta",
}


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _token(uid: str) -> str:
    """Unsigned JWT resolved by the real dev-mode auth seam."""
    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'user_id': uid, 'email': f'{uid}@test.dev'})}.sig"


def _auth(uid: str) -> dict:
    return {"Authorization": f"Bearer {_token(uid)}"}


def _seed_knowledge() -> dict:
    note_a = vault.create_note(title=f"A note {CANARY_A}", content=f"private {CANARY_A}", user_id=USER_A)
    note_b = vault.create_note(title=f"B note {CANARY_B}", content=f"private {CANARY_B}", user_id=USER_B)
    note_pub = vault.create_note(title="Public corpus entry", content="shared public corpus", user_id=None)
    add_edge(note_a["id"], note_pub["id"], "references")
    proj_a = vault.create_project("A project", user_id=USER_A)
    vault.create_project("B project", user_id=USER_B)
    tl.record(event_type="note_created", payload={"mark": CANARY_A}, note_id=note_a["id"], user_id=USER_A)
    tl.record(event_type="note_created", payload={"mark": CANARY_B}, note_id=note_b["id"], user_id=USER_B)
    return {"note_a": note_a, "note_b": note_b, "note_pub": note_pub, "proj_a": proj_a}


def _seed_messages() -> None:
    os.makedirs(messages_mod._MSG_DIR, exist_ok=True)
    messages_mod._append(USER_A, USER_B, {
        "id": "m-ab", "sender_uid": USER_A, "recipient_uid": USER_B,
        "content": f"hello {CANARY_A}", "timestamp": 1000,
    })
    messages_mod._append(USER_B, USER_C, {
        "id": "m-bc", "sender_uid": USER_B, "recipient_uid": USER_C,
        "content": f"secret {CANARY_BC}", "timestamp": 2000,
    })


def _counts() -> dict:
    conn = get_connection()
    out = {}
    for table in ("notes", "projects", "timeline", "graph_edges", "threads"):
        out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return out


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "VAULT_ROOT", tmp_path / "vault")
    monkeypatch.setattr(messages_mod, "_MSG_DIR", str(tmp_path / "messages"))
    conn = get_connection()
    for table in ("graph_edges", "timeline", "chunks", "embeddings", "note_tags", "notes", "threads", "projects"):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    app = FastAPI()
    app.include_router(echofeild.router)
    yield TestClient(app)


# ── A. Authentication ─────────────────────────────────────────────────────────

def test_unauthenticated_requires_auth(client):
    r = client.get("/api/me/field")
    assert r.status_code == 401


def test_authenticated_request_succeeds(client):
    r = client.get("/api/me/field", headers=_auth(USER_A))
    assert r.status_code == 200
    assert r.json()["meta"]["owner_uid"] == USER_A


# ── B. Owner isolation ────────────────────────────────────────────────────────

def test_owner_isolation(client):
    seed = _seed_knowledge()
    field_a = client.get("/api/me/field", headers=_auth(USER_A)).json()
    field_b = client.get("/api/me/field", headers=_auth(USER_B)).json()

    assert field_a["meta"]["owner_uid"] == USER_A
    assert field_b["meta"]["owner_uid"] == USER_B
    assert field_a["identity"]["uid"] == USER_A
    assert field_b["identity"]["uid"] == USER_B

    body_a = json.dumps(field_a)
    body_b = json.dumps(field_b)
    assert CANARY_A in body_a and CANARY_A not in body_b
    assert CANARY_B in body_b and CANARY_B not in body_a

    ids_a = {n["id"] for n in field_a["notes"]}
    ids_b = {n["id"] for n in field_b["notes"]}
    assert seed["note_a"]["id"] in ids_a and seed["note_b"]["id"] not in ids_a
    assert seed["note_b"]["id"] in ids_b and seed["note_a"]["id"] not in ids_b


def test_client_supplied_identity_params_are_ignored(client):
    _seed_knowledge()
    r = client.get(
        "/api/me/field",
        headers=_auth(USER_A),
        params={"uid": USER_B, "user_id": USER_B, "owner": USER_B, "node_key": USER_B},
    )
    assert r.status_code == 200
    field = r.json()
    assert field["meta"]["owner_uid"] == USER_A
    body = json.dumps(field)
    assert CANARY_A in body
    assert CANARY_B not in body


# ── C. Notes ──────────────────────────────────────────────────────────────────

def test_notes_are_owner_scoped(client):
    seed = _seed_knowledge()
    field_a = client.get("/api/me/field", headers=_auth(USER_A)).json()
    titles_a = {n["title"] for n in field_a["notes"]}
    assert f"A note {CANARY_A}" in titles_a
    assert f"B note {CANARY_B}" not in titles_a
    # public corpus remains visible to an authenticated user (existing semantic)
    assert seed["note_pub"]["id"] in {n["id"] for n in field_a["notes"]}


# ── D. Graph ──────────────────────────────────────────────────────────────────

def test_graph_is_owner_scoped(client):
    seed = _seed_knowledge()
    field_a = client.get("/api/me/field", headers=_auth(USER_A)).json()
    field_b = client.get("/api/me/field", headers=_auth(USER_B)).json()

    nodes_a = {n["id"] for n in field_a["graph"]["nodes"]}
    nodes_b = {n["id"] for n in field_b["graph"]["nodes"]}
    assert seed["note_a"]["id"] in nodes_a
    assert seed["note_pub"]["id"] in nodes_a
    assert seed["note_b"]["id"] not in nodes_a
    assert seed["note_b"]["id"] in nodes_b
    assert seed["note_a"]["id"] not in nodes_b

    edge_pairs_a = {(e["source_note_id"], e["target_note_id"]) for e in field_a["graph"]["edges"]}
    assert (seed["note_a"]["id"], seed["note_pub"]["id"]) in edge_pairs_a
    for e in field_a["graph"]["edges"]:
        assert e["source_note_id"] in nodes_a and e["target_note_id"] in nodes_a


# ── E. Projects ───────────────────────────────────────────────────────────────

def test_projects_are_owner_scoped(client):
    seed = _seed_knowledge()
    field_a = client.get("/api/me/field", headers=_auth(USER_A)).json()
    field_b = client.get("/api/me/field", headers=_auth(USER_B)).json()
    names_a = {p["name"] for p in field_a["projects"]}
    names_b = {p["name"] for p in field_b["projects"]}
    assert "A project" in names_a and "B project" not in names_a
    assert "B project" in names_b and "A project" not in names_b
    # SolSpire is not owner-scoped in this repo state — excluded, never leaked
    assert field_a["executions"] == []
    solspire_source = next(s for s in field_a["meta"]["sources"] if s["source"] == "solspire")
    assert solspire_source["included"] is False


# ── F. Messages ───────────────────────────────────────────────────────────────

def test_messages_are_participant_scoped(client):
    _seed_messages()
    field_a = client.get("/api/me/field", headers=_auth(USER_A)).json()

    peers = {c["peer_uid"] for c in field_a["conversations"]}
    assert peers == {USER_B}

    msgs_a = json.dumps(field_a["messages"])
    assert CANARY_A in msgs_a
    assert CANARY_BC not in msgs_a  # private B↔C pair never leaks to A

    field_b = client.get("/api/me/field", headers=_auth(USER_B)).json()
    peers_b = {c["peer_uid"] for c in field_b["conversations"]}
    assert peers_b == {USER_A, USER_C}


# ── G. Read-only ──────────────────────────────────────────────────────────────

def test_field_is_read_only(client):
    _seed_knowledge()
    _seed_messages()
    before = _counts()
    msg_dir = messages_mod._MSG_DIR
    files_before = {n: open(os.path.join(msg_dir, n)).read() for n in os.listdir(msg_dir)}

    r = client.get("/api/me/field", headers=_auth(USER_A))
    assert r.status_code == 200

    assert _counts() == before
    files_after = {n: open(os.path.join(msg_dir, n)).read() for n in os.listdir(msg_dir)}
    assert files_after == files_before


def test_field_does_not_create_message_store(client):
    # No seeding — the messages directory must not be created by a read.
    r = client.get("/api/me/field", headers=_auth(USER_A))
    assert r.status_code == 200
    assert not os.path.exists(messages_mod._MSG_DIR)


# ── H. Response contract ──────────────────────────────────────────────────────

def test_response_contract(client):
    _seed_knowledge()
    r = client.get("/api/me/field", headers=_auth(USER_A))
    assert r.status_code == 200
    field = r.json()  # valid JSON

    assert EXPECTED_KEYS.issubset(set(field.keys()))
    assert isinstance(field["notes"], list)
    assert isinstance(field["graph"], dict) and "nodes" in field["graph"] and "edges" in field["graph"]
    assert isinstance(field["timeline"], list)
    assert isinstance(field["projects"], list)
    assert isinstance(field["conversations"], list)
    assert isinstance(field["messages"], list)
    assert isinstance(field["executions"], list)

    meta = field["meta"]
    assert meta["owner_uid"] == USER_A
    assert meta["generated_at"]
    assert isinstance(meta["sources"], list) and meta["sources"]

    # no secrets, tokens, or provider credentials in the payload
    raw = r.text.lower()
    for forbidden in ('"token"', "api_key", "apikey", "service_account", "private_key", "idtoken"):
        assert forbidden not in raw
