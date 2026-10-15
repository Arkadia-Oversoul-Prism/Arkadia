"""Arkana thread-history contract — measured against the live handler.

Workstream 4's Arkana thread-history slice reads two routes. This file is the
backend oracle for that slice: it composes the real ``api.commune_threads``
router and drives it with a real identity override, so the shape, the auth
boundary, the owner scoping and the failure behaviour are *measured*, not
inferred from the archive UI or from a source constant.

Verified contract (``api/commune_threads.py``):

  | method | path                                    | auth | success                  |
  |--------|-----------------------------------------|------|--------------------------|
  | GET    | /api/commune/threads                    | 401  | ``{"threads": [...]}``   |
  | POST   | /api/commune/threads                    | 401  | thread (not read here)   |
  | GET    | /api/commune/threads/{uuid}             | 401  | ``{"thread": {...}}``    |
  | PATCH  | /api/commune/threads/{uuid}             | 401  | thread (not read here)   |
  | GET    | /api/commune/threads/{uuid}/messages    | 401  | ``{"messages": [...]}``  |

``_public_thread`` deliberately omits ``user_id``: ownership is enforced
server-side, so the client never receives it. ``list_threads`` returns ``[]``
(never an error) when the identity owns nothing, which is why the UI must render
an *empty* state distinctly from a failed read.

Recorded failure states (this revision):

  * no identity -> ``401 {"detail": "Authentication required"}`` on every route.
  * unknown / other owner's uuid -> ``404 {"detail": "Thread not found"}``.
  * a non-integer ``project_id`` -> ``422`` on list (FastAPI query typing) and
    ``400`` on create (manual body validation); a non-existent project -> ``404``
    on create.
  * an empty request body on create -> ``500`` (the handler calls
    ``request.json()`` without guarding a body-less request). Recorded, not
    repaired: it is a backend defect outside this workstream's owned paths, and
    the read-only slice never issues a create.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import knowledge
from knowledge import db as kdb
from knowledge import vault
from api import auth
from api.commune_threads import router as commune_threads_router

ROOT = Path(__file__).resolve().parents[1]

OWNER = "subject-owner"
OTHER = "subject-other"

READ_ROUTES = [
    ("GET", "/api/commune/threads"),
    ("GET", "/api/commune/threads/{uuid}"),
    ("GET", "/api/commune/threads/{uuid}/messages"),
]
ALL_ROUTES = READ_ROUTES + [
    ("POST", "/api/commune/threads"),
    ("PATCH", "/api/commune/threads/{uuid}"),
]


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """The real router, composed over an isolated Knowledge OS database."""
    monkeypatch.setattr(kdb, "_DB_PATH", tmp_path / "knowledge.db")
    monkeypatch.setattr(knowledge, "_DB_PATH", kdb._DB_PATH)
    monkeypatch.setattr(vault, "VAULT_ROOT", tmp_path / "vault")
    monkeypatch.setattr(knowledge, "VAULT_ROOT", vault.VAULT_ROOT)
    # `knowledge.db` caches a per-thread connection; drop it so the temp DB is used.
    kdb._local.conn = None
    application = FastAPI()
    application.include_router(commune_threads_router)
    yield application
    kdb._local.conn = None


@pytest.fixture()
def auth_as(app, monkeypatch):
    """A client factory whose ``get_current_user`` is the measured identity.

    ``api.commune_threads._user_id`` calls ``get_current_user`` **directly** (not
    through ``Depends``), importing it lazily from ``api.auth``. A FastAPI
    ``dependency_overrides`` entry therefore does not reach it; the seam is the
    module attribute, which is what is patched here.
    """

    def _factory(uid: str | None) -> TestClient:
        async def _identify(request):  # noqa: ANN001 - signature mirrors the real dep
            return {"uid": uid} if uid else None

        monkeypatch.setattr(auth, "get_current_user", _identify)
        return TestClient(app, raise_server_exceptions=False)

    return _factory


def _seed_thread(uid: str, title: str, project_id: int | None = None) -> dict:
    return vault.create_thread(title, user_id=uid, project_id=project_id)


def _seed_turn(thread_id: int, uid: str, prompt: str, answer: str, note_type: str = "conversation") -> None:
    kdb.execute(
        "INSERT INTO notes (uuid, title, content, vault_path, note_type, thread_id, user_id) VALUES (?,?,?,?,?,?,?)",
        (f"note-{prompt[:8]}", "turn", f"## Prompt\n\n{prompt}\n\n## Response\n\n{answer}", "Projects/n.md", note_type, thread_id, uid),
    )


# ---------------------------------------------------------------------------
# Route + method matrix
# ---------------------------------------------------------------------------

def test_declared_routes_and_methods(app):
    paths = app.openapi()["paths"]
    assert set(paths) == {
        "/api/commune/threads",
        "/api/commune/threads/{thread_uuid}",
        "/api/commune/threads/{thread_uuid}/messages",
    }
    assert set(paths["/api/commune/threads"]) == {"get", "post"}
    assert set(paths["/api/commune/threads/{thread_uuid}"]) == {"get", "patch"}
    assert set(paths["/api/commune/threads/{thread_uuid}/messages"]) == {"get"}


def test_every_route_requires_an_identity(auth_as):
    unauthenticated = auth_as(None)
    for method, path in ALL_ROUTES:
        url = path.replace("{uuid}", "any")
        response = unauthenticated.request(method, url, json={"title": "x"})
        assert response.status_code == 401, f"{method} {url} reached a handler without identity"
        assert response.json()["detail"] == "Authentication required"


def test_negative_control_the_identity_is_what_admits_the_read(app, auth_as):
    """Same request, identity present -> 200. The delta is the identity."""
    thread = _seed_thread(OWNER, "My convo")
    assert auth_as(None).get("/api/commune/threads").status_code == 401
    response = auth_as(OWNER).get("/api/commune/threads")
    assert response.status_code == 200
    assert [t["uuid"] for t in response.json()["threads"]] == [thread["uuid"]]


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

def test_list_shape_is_exact_and_owner_scoped(app, auth_as):
    thread = _seed_thread(OWNER, "My convo")
    body = auth_as(OWNER).get("/api/commune/threads").json()
    assert set(body) == {"threads"}
    (row,) = body["threads"]
    assert set(row) == {"id", "uuid", "title", "project_id", "created_at", "updated_at"}
    # `_public_thread` omits the owner: it must not leak through this projection.
    assert "user_id" not in row
    assert row["uuid"] == thread["uuid"]
    assert row["title"] == "My convo"
    assert row["project_id"] is None


def test_detail_shape_is_the_same_projection_wrapped(app, auth_as):
    thread = _seed_thread(OWNER, "My convo")
    body = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}").json()
    assert set(body) == {"thread"}
    assert set(body["thread"]) == {"id", "uuid", "title", "project_id", "created_at", "updated_at"}
    assert "user_id" not in body["thread"]


def test_reads_are_owner_scoped(app, auth_as):
    """Another identity cannot see or fetch this thread — 404, not a leak."""
    thread = _seed_thread(OWNER, "Private convo")
    other = auth_as(OTHER)
    assert other.get("/api/commune/threads").json() == {"threads": []}
    assert other.get(f"/api/commune/threads/{thread['uuid']}").status_code == 404
    assert other.get(f"/api/commune/threads/{thread['uuid']}/messages").status_code == 404


def test_empty_list_is_a_success_not_an_error(auth_as):
    """The empty state the UI must render distinctly from failure."""
    response = auth_as(OWNER).get("/api/commune/threads")
    assert response.status_code == 200
    assert response.json() == {"threads": []}


def test_unknown_thread_is_404_on_both_sub_resources(auth_as):
    client = auth_as(OWNER)
    assert client.get("/api/commune/threads/does-not-exist").status_code == 404
    assert client.get("/api/commune/threads/does-not-exist/messages").status_code == 404
    assert client.get("/api/commune/threads/does-not-exist").json()["detail"] == "Thread not found"


def test_non_integer_project_filter_is_rejected(auth_as):
    """Two different rejection paths, both measured:
      * the list route types ``project_id`` as ``int | None``, so FastAPI itself
        rejects a non-integer query with ``422``;
      * the create route reads the body and validates ``project_id`` manually,
        so a non-integer body value is a ``400``.
    A UI must not present either as an empty list.
    """
    assert auth_as(OWNER).get("/api/commune/threads?project_id=abc").status_code == 422
    assert (
        auth_as(OWNER).post("/api/commune/threads", json={"title": "x", "project_id": "abc"}).status_code == 400
    )


# ---------------------------------------------------------------------------
# Messages sub-resource
# ---------------------------------------------------------------------------

def _messages_detector(payload: dict) -> list[str]:
    """Divergences between the payload and the contract the slice relies on."""
    defects = []
    if set(payload) != {"messages"}:
        defects.append(f"envelope keys {sorted(payload)}")
    for message in payload.get("messages", []):
        if set(message) != {"role", "content", "created_at"}:
            defects.append(f"message keys {sorted(message)}")
        if message.get("role") not in {"user", "arkana"}:
            defects.append(f"role {message.get('role')!r}")
    return defects


def test_message_roles_are_user_and_arkana_only(app, auth_as):
    """The handler emits `arkana`, not `assistant` — the UI must not assume the
    resonance vocabulary."""
    thread = _seed_thread(OWNER, "Convo")
    _seed_turn(thread["id"], OWNER, "What is resonance?", "The field answers.")
    payload = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages").json()
    assert _messages_detector(payload) == []
    assert [m["role"] for m in payload["messages"]] == ["user", "arkana"]
    assert payload["messages"][0]["content"] == "What is resonance?"
    assert payload["messages"][1]["content"] == "The field answers."


def test_markerless_and_non_conversation_notes_are_not_fabricated(app, auth_as):
    """A note without the prompt/response markers, a note with only a prompt, and
    a non-`conversation` note must not become a message — no invented answer."""
    thread = _seed_thread(OWNER, "Convo")
    kdb.execute(
        "INSERT INTO notes (uuid, title, content, vault_path, note_type, thread_id, user_id) VALUES (?,?,?,?,?,?,?)",
        ("n-blank", "blank", "just prose", "Ideas/n.md", "conversation", thread["id"], OWNER),
    )
    kdb.execute(
        "INSERT INTO notes (uuid, title, content, vault_path, note_type, thread_id, user_id) VALUES (?,?,?,?,?,?,?)",
        ("n-half", "half", "## Prompt\n\nonly a question", "Projects/n.md", "conversation", thread["id"], OWNER),
    )
    _seed_turn(thread["id"], OWNER, "unused", "unused", note_type="idea")
    payload = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages").json()
    assert payload == {"messages": []}


def test_empty_thread_messages_is_a_success(app, auth_as):
    thread = _seed_thread(OWNER, "Convo")
    response = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages")
    assert response.status_code == 200
    assert response.json() == {"messages": []}


def test_negative_control_message_detector_flags_a_divergent_payload():
    """The detector must report the defect it exists to catch."""
    assert _messages_detector({"messages": []}) == []
    divergent = {"messages": [{"role": "assistant", "content": "x", "created_at": None}]}
    assert _messages_detector(divergent) == ["role 'assistant'"]
    assert _messages_detector({"items": []}) == ["envelope keys ['items']"]


# ---------------------------------------------------------------------------
# Recorded backend defect (not repaired here)
# ---------------------------------------------------------------------------

def test_recorded_defect_bodyless_create_is_a_server_error(auth_as):
    """`create_arkana_thread` calls ``await request.json()`` unguarded, so a
    body-less POST is a 500. Recorded, not repaired: mutation is outside this
    read-only slice and `api/commune_threads.py` is not owned by workstream 4.
    When it is repaired this pin must be re-pointed (a 400 is the expected fix).
    """
    response = auth_as(OWNER).post("/api/commune/threads", content=b"", headers={"Content-Type": "application/json"})
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# The second conversation producer (project conversations)
# ---------------------------------------------------------------------------

def _project_turn(thread_id: int, uid: str, role: str, content: str) -> None:
    """A note in the shape ``solspire.conversation_bridge`` actually writes."""
    kdb.execute(
        "INSERT INTO notes (uuid, title, content, vault_path, note_type, thread_id, user_id) VALUES (?,?,?,?,?,?,?)",
        (
            f"proj-{role}-{content[:8]}",
            f"Project conversation · {role}",
            f"Project: p-1\nConversation: conv-1\nRole: {role}\n\n{content}",
            "Projects/n.md",
            "conversation",
            thread_id,
            uid,
        ),
    )


def test_project_conversation_turns_are_visible(app, auth_as):
    """The project producer's notes are conversation turns, not invisible rows.

    Measured defect: `solspire/conversation_bridge.py` writes one
    ``note_type='conversation'`` note per turn headed ``Role: <role>``, while the
    handler only understood the Oracle spine's ``## Prompt``/``## Response`` pair
    — so a thread with recorded project turns answered ``messages: []``, which a
    UI cannot distinguish from an empty thread.
    """
    thread = _seed_thread(OWNER, "Project convo")
    _project_turn(thread["id"], OWNER, "user", "What is the plan?")
    _project_turn(thread["id"], OWNER, "assistant", "Ship the bounded slice.")
    payload = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages").json()
    assert _messages_detector(payload) == []
    assert [(m["role"], m["content"]) for m in payload["messages"]] == [
        ("user", "What is the plan?"),
        ("arkana", "Ship the bounded slice."),
    ]


def test_both_producers_compose_in_one_thread(app, auth_as):
    """A thread written by both producers keeps every turn, in note order."""
    thread = _seed_thread(OWNER, "Mixed convo")
    _project_turn(thread["id"], OWNER, "user", "first")
    _seed_turn(thread["id"], OWNER, "second", "second answer")
    payload = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages").json()
    assert [m["role"] for m in payload["messages"]] == ["user", "user", "arkana"]
    assert [m["content"] for m in payload["messages"]] == ["first", "second", "second answer"]


def test_unknown_role_heading_is_a_user_turn_not_a_fabricated_answer(app, auth_as):
    """Only known answer roles become `arkana`; anything else is a user turn."""
    thread = _seed_thread(OWNER, "Roles")
    _project_turn(thread["id"], OWNER, "system", "a preamble")
    payload = auth_as(OWNER).get(f"/api/commune/threads/{thread['uuid']}/messages").json()
    assert [(m["role"], m["content"]) for m in payload["messages"]] == [("user", "a preamble")]


def test_negative_control_the_turn_reader_flags_the_unparsed_shape():
    """The reader must return nothing for the shapes it exists to reject, and a
    turn for each shape it claims to understand — otherwise the guard above could
    pass against a reader that returns a turn for *any* note."""
    from api.commune_threads import _turn_messages

    assert _turn_messages("## Prompt\n\nq\n\n## Response\n\na") == [("user", "q"), ("arkana", "a")]
    assert _turn_messages("Conversation: c\nRole: assistant\n\nhi") == [("arkana", "hi")]
    # The pre-repair defect: the project shape was unparsed, so this returned [].
    assert _turn_messages("just prose") == []
    assert _turn_messages("## Prompt\n\nonly a question") == []
    assert _turn_messages("Role: user\n\n") == []
    assert _turn_messages("Project: p\nConversation: c\nRole: user") == []
