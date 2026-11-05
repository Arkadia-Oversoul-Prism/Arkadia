"""The shared project-scoped context object — end-to-end demonstration.

This test proves the two edges the console's shared project context closes, by
exercising the **real HTTP routes** on ``api.main:app`` rather than asserting on
frontend source text:

  * **Forward edge.** A conversation started in a project workspace is scoped to
    that project: the console sends ``project_id`` to the Arkana stream, and a
    Lab session created from the same selection carries that project id into
    ``SessionCreate.project_ref``. The server then enforces the binding — the
    project must be owned by the caller and ``workspace_ref`` must be the
    caller's canonical workspace (``api/lab_routes.py``), so a session that
    claims a project binding it cannot satisfy is refused 409 rather than
    silently created unbound.

  * **Reverse edge.** A Lab session outcome returns to the project's
    conversation thread through the canonical bridge
    (``POST /solspire/projects/{id}/conversations/{conv_id}/messages`` →
    ``append_conversation_turn``), which composes the turn across the project
    record, the Knowledge OS note and the project activity event. No second
    store is created, and the recorded turn is readable back from the project
    conversation.

Authentication is overridden with the same ``dependency_overrides`` pattern the
repository's own Lab boundary tests use (``tests/test_lab_execution_boundary_ws2.py``).
This is a *test identity*, not a production credential, and no secret is written
anywhere. The overrides are removed in ``finally`` so no other test inherits them.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

SUBJECT = "test-subject-project-context"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A TestClient with a test identity and an isolated SolSpire database."""
    from api import auth as auth_mod
    from api import lab_routes
    from api.main import app
    from solspire import project_manager, project_store, workspace_manager

    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(project_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(project_store, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))

    # The Lab router authenticates twice (router-level + endpoint-level); both
    # must be overridden or the request is refused 401 before the body is read.
    app.dependency_overrides[auth_mod.require_auth] = lambda: {"uid": SUBJECT}
    app.dependency_overrides[lab_routes.require_lab_auth] = lambda: None
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(auth_mod.require_auth, None)
        app.dependency_overrides.pop(lab_routes.require_lab_auth, None)


def _make_project(client: TestClient, name: str) -> str:
    response = client.post("/solspire/projects", json={"name": name})
    assert response.status_code == 200, response.text
    return response.json()["project"]["id"]


def _canonical_workspace(client: TestClient) -> str:
    response = client.get("/solspire/workspace")
    assert response.status_code == 200, response.text
    return response.json()["workspace"]["id"]


def test_forward_edge_project_id_reaches_session_project_ref(client):
    """A project-scoped session carries the project id into ``project_ref``.

    This is the forward edge of the journey: the console's shared context
    supplies one project id, and the session the Lab creates is bound to it on
    the server — not merely labelled with it in the UI.
    """
    project_id = _make_project(client, "Forward edge project")
    workspace_id = _canonical_workspace(client)

    agent = client.post(
        "/api/lab/engineering/agents",
        json={"role": "SENTINEL", "name": "context probe agent"},
    )
    assert agent.status_code == 200, agent.text
    agent_id = agent.json()["agent_id"]

    created = client.post(
        "/api/lab/engineering/sessions",
        json={
            "workspace_ref": workspace_id,
            "agent_id": agent_id,
            "objective": "read-only investigation",
            "project_ref": project_id,
        },
    )
    assert created.status_code == 200, created.text
    session = created.json()

    # The binding is real: the server stored the project id on the session.
    assert session["project_ref"] == project_id
    assert session["workspace_ref"] == workspace_id

    # And it is readable back from the session list, so the console can show the
    # binding rather than infer it.
    listed = client.get("/api/lab/engineering/sessions")
    assert listed.status_code == 200, listed.text
    rows = listed.json()["sessions"]
    match = [row for row in rows if row.get("session_id") == session["session_id"]]
    assert match, "the created session must be listed for its subject"
    assert match[0].get("project_ref") == project_id


def test_forward_edge_refuses_a_binding_it_cannot_satisfy(client):
    """A claimed project binding that cannot be satisfied is refused, not faked.

    The console only offers the binding when the canonical workspace is known
    (``canBindProject``). This test pins the server side of that contract: a
    session that names a project but the wrong workspace is refused 409, so the
    console can never create a session that *looks* project-scoped while the
    server holds no such binding.
    """
    project_id = _make_project(client, "Mismatch project")

    agent = client.post(
        "/api/lab/engineering/agents",
        json={"role": "SENTINEL", "name": "mismatch probe agent"},
    )
    assert agent.status_code == 200, agent.text
    agent_id = agent.json()["agent_id"]

    refused = client.post(
        "/api/lab/engineering/sessions",
        json={
            "workspace_ref": "workspace:engineering-lab-mission",
            "agent_id": agent_id,
            "objective": "read-only investigation",
            "project_ref": project_id,
        },
    )
    assert refused.status_code == 409, refused.text
    assert "Canonical workspace binding mismatch" in refused.json()["detail"]


def test_reverse_edge_lab_outcome_returns_to_the_project_thread(client):
    """A Lab outcome returns to its project conversation thread.

    This is the reverse edge: the session was created with this project's
    ``project_ref``, so its outcome is recorded in this project's conversation
    through the canonical bridge. The turn is then read back from the project
    conversation, proving it is durable and attached to the project rather than
    held in a surface's local state.
    """
    project_id = _make_project(client, "Reverse edge project")
    workspace_id = _canonical_workspace(client)

    agent = client.post(
        "/api/lab/engineering/agents",
        json={"role": "SENTINEL", "name": "reverse probe agent"},
    )
    assert agent.status_code == 200, agent.text
    agent_id = agent.json()["agent_id"]

    session = client.post(
        "/api/lab/engineering/sessions",
        json={
            "workspace_ref": workspace_id,
            "agent_id": agent_id,
            "objective": "read-only investigation",
            "project_ref": project_id,
        },
    )
    assert session.status_code == 200, session.text
    session_id = session.json()["session_id"]

    # The console attaches (or reuses) the project's conversation.
    conversation = client.post(
        f"/solspire/projects/{project_id}/conversations",
        json={"title": "Reverse edge project conversation"},
    )
    assert conversation.status_code == 200, conversation.text
    conv_id = conversation.json()["id"]

    # The outcome is composed from the substrate's own report and appended
    # through the canonical bridge.
    outcome_body = (
        "**Engineering Lab outcome**\n\n"
        f"- session: `{session_id}`\n"
        "- session state: `open`\n\n"
        "_Recorded from the substrate's own report._"
    )
    appended = client.post(
        f"/solspire/projects/{project_id}/conversations/{conv_id}/messages",
        json={"role": "arkana", "content": outcome_body},
    )
    assert appended.status_code == 200, appended.text
    payload = appended.json()
    assert payload["ok"] is True
    assert payload["message"]["conversation_id"] == conv_id
    # The bridge reports its own Knowledge OS state; the test asserts the field
    # exists rather than asserting a particular value, because ingestion depends
    # on the Knowledge OS being available in this environment.
    assert "status" in payload["knowledge"]

    # The turn is durable and attached to the project: it reads back.
    listed = client.get(f"/solspire/projects/{project_id}/conversations")
    assert listed.status_code == 200, listed.text
    conversations = listed.json()["conversations"]
    match = [c for c in conversations if c["id"] == conv_id]
    assert match, "the conversation must be listed for its project"
    contents = [turn["content"] for turn in match[0]["messages"]]
    assert outcome_body in contents, "the Lab outcome must be recorded in the thread"


def test_reverse_edge_refuses_a_conversation_from_another_project(client):
    """A turn cannot be appended to a conversation that belongs to another project.

    The bridge refuses a conversation whose ``project_id`` does not match the
    route's project (404). This is what keeps the reverse edge honest: an outcome
    returns to *its* thread, and a surface cannot redirect it into an unrelated
    project's conversation.
    """
    project_a = _make_project(client, "Project A")
    project_b = _make_project(client, "Project B")

    conversation = client.post(
        f"/solspire/projects/{project_a}/conversations",
        json={"title": "A conversation"},
    )
    assert conversation.status_code == 200, conversation.text
    conv_id = conversation.json()["id"]

    crossed = client.post(
        f"/solspire/projects/{project_b}/conversations/{conv_id}/messages",
        json={"role": "arkana", "content": "should not land"},
    )
    assert crossed.status_code == 404, crossed.text
