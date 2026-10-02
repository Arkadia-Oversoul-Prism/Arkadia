"""Verified boundary — the tool execution perimeter (Arkadia-native).

Acceptance tests for the boundary established on
``reconciliation/verified-boundary-01``. Before this change, ``api/main.py``
served ``POST /api/tools/{tool_name}/run`` with no authentication and ignored
``requires_approval``; ``api/approval_routes.py`` let anyone list every approval
and *executed the tool inside the approve handler*.

The perimeter composes checks that do not substitute for one another:

  * **authentication** — ``Depends(require_auth)`` establishes *who* is calling;
  * **authorization**  — the tool must exist, and the caller must present a valid
    approval reference for approval-gated tools;
  * **approval**       — a tool declaring ``requires_approval`` is denied until a
    recorded, unconsumed, same-subject approval exists;
  * **separation**     — approving records a decision and does **not** execute;
    execution is a distinct act at the tool-run boundary;
  * **governance**     — only a ``Govern`` principal (Flamekeeper / access_level
    >= 3) may decide, and self-approval is prohibited.

Anonymous-denial cases exercise the *real* dependency (no override) so the
assertion is about the boundary itself. Authenticated cases override
``require_auth`` so the authorization/approval logic is tested deterministically
without Firebase credentials — the override is the identity under test, not a
stand-in for the boundary being verified.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from api.approval_routes import APPROVAL_LOCK, PENDING_APPROVALS
from api.auth import require_auth
from api.main import app
from kernel.tools_real import register_real_tools


@pytest.fixture(scope="module", autouse=True)
def _tools_registered():
    register_real_tools()


@pytest.fixture(scope="module", autouse=True)
def _isolate_dependency_overrides():
    app.dependency_overrides.pop(require_auth, None)
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def as_user():
    """Override the auth dependency with a mutable identity.

    Default identity is an ordinary authenticated principal (Guest) with no
    approval authority — approving is a separate, governed act.
    """
    current = {"uid": "test-subject", "role": "Guest", "access_level": 0}
    app.dependency_overrides[require_auth] = lambda: {
        "uid": current["uid"],
        "email": f"{current['uid']}@example.com",
        "access_level": current["access_level"],
        "role": current["role"],
    }
    yield current
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture(autouse=True)
def _clean_approvals():
    with APPROVAL_LOCK:
        PENDING_APPROVALS.clear()
    yield
    with APPROVAL_LOCK:
        PENDING_APPROVALS.clear()


def _request_approval(client, tool_name, payload=None):
    r = client.post(
        "/api/approvals/request",
        json={"tool_name": tool_name, "payload": payload or {}, "description": "t"},
    )
    assert r.status_code == 200, r.text
    return r.json()["approval_id"]


def _approve(client, as_user, approval_id, *, authorized=True):
    """Decide an approval as an authorized Flamekeeper, then drop back to the
    ordinary caller. Requester and approver are deliberately distinct: the
    approver identity differs from the requester, so self-approval is never
    exercised by this helper."""
    prev = (as_user["uid"], as_user["role"], as_user["access_level"])
    as_user["uid"] = "flamekeeper"
    if authorized:
        as_user["role"] = "Flamekeeper"
        as_user["access_level"] = 3
    try:
        return client.post(f"/api/approvals/{approval_id}/approve")
    finally:
        as_user["uid"], as_user["role"], as_user["access_level"] = prev


# ── 1. Authentication: anonymous is denied ────────────────────────────────────

def test_anonymous_cannot_list_tools(client):
    assert client.get("/api/tools").status_code == 401


def test_anonymous_cannot_run_approval_gated_tool(client):
    r = client.post("/api/tools/execute_shell/run", json={"payload": {"command": "whoami"}})
    assert r.status_code == 401


def test_anonymous_cannot_run_readonly_tool(client):
    r = client.post("/api/tools/read_file/run", json={"payload": {"path": "README.md"}})
    assert r.status_code == 401


@pytest.mark.parametrize("method,path", [
    ("get", "/api/approvals"),
    ("post", "/api/approvals/request"),
    ("post", "/api/approvals/x/approve"),
    ("post", "/api/approvals/x/reject"),
])
def test_approval_routes_require_auth(client, method, path):
    assert getattr(client, method)(path).status_code == 401


@pytest.mark.parametrize("path", ["/api/jobs", "/api/goals"])
def test_kernel_loop_read_surfaces_require_auth(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", [
    "/api/job/create",
    "/api/goals",
    "/api/plan/run",
    "/api/agent/spawn",
    "/api/ceo/chat",
])
def test_kernel_loop_write_surfaces_require_auth(client, path):
    assert client.post(path, json={}).status_code == 401


# ── 2. Authorization / approval gating ────────────────────────────────────────

def test_authenticated_but_unapproved_gated_tool_is_denied(client, as_user):
    r = client.post("/api/tools/execute_shell/run", json={"payload": {"command": "whoami"}})
    assert r.status_code == 403


def test_bogus_approval_id_is_denied(client, as_user):
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": "does-not-exist"},
    )
    assert r.status_code == 403


def test_pending_approval_is_not_yet_spendable(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert r.status_code == 403


def test_approval_for_other_tool_is_denied(client, as_user):
    aid = _request_approval(client, "read_file", {"path": "README.md"})
    _approve(client, as_user, aid)
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert r.status_code == 403


def test_approved_gated_tool_runs_once(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    assert _approve(client, as_user, aid).status_code == 200
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert r.status_code == 200
    # single-use: the consumed approval cannot authorize a second run
    r2 = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert r2.status_code == 403


def test_non_gated_tool_needs_no_approval(client, as_user):
    r = client.post("/api/tools/read_file/run", json={"payload": {"path": "README.md"}})
    assert r.status_code == 200


# ── 3. Decision ≠ execution (the separation boundary) ─────────────────────────

def test_approve_decision_does_not_execute(client, as_user):
    """Approving records a decision; it must not run the tool."""
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    body = _approve(client, as_user, aid).json()
    assert body["status"] == "approved"
    assert "result" not in body  # no execution output leaked from the decision


# ── 4. Governance: authority + self-approval ──────────────────────────────────

def test_ordinary_principal_cannot_approve(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    assert client.post(f"/api/approvals/{aid}/approve").status_code == 403


def test_ordinary_principal_cannot_reject(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    assert client.post(f"/api/approvals/{aid}/reject").status_code == 403


def test_sovereign_access_level_may_approve(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    as_user["uid"] = "sovereign-reviewer"
    as_user["access_level"] = 3
    try:
        assert client.post(f"/api/approvals/{aid}/approve").status_code == 200
    finally:
        as_user["uid"] = "test-subject"
        as_user["access_level"] = 0


def test_self_approval_is_prohibited(client, as_user):
    """The requester cannot decide its own request, even holding Govern."""
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    as_user["role"] = "Flamekeeper"
    as_user["access_level"] = 3
    try:
        assert client.post(f"/api/approvals/{aid}/approve").status_code == 403
    finally:
        as_user["role"] = "Guest"
        as_user["access_level"] = 0


# ── 5. Subject scoping ────────────────────────────────────────────────────────

def test_approval_listing_is_subject_scoped(client, as_user):
    _request_approval(client, "execute_shell", {"command": "whoami"})
    as_user["uid"] = "other-subject"
    r = client.get("/api/approvals")
    assert r.status_code == 200
    assert r.json()["approvals"] == []


def test_flamekeeper_reviewer_sees_all_pending_approvals(client, as_user):
    _request_approval(client, "execute_shell", {"command": "whoami"})
    as_user["uid"] = "another-requester"
    _request_approval(client, "execute_shell", {"command": "whoami"})
    # ordinary caller sees only its own
    assert len(client.get("/api/approvals").json()["approvals"]) == 1
    as_user["role"] = "Flamekeeper"
    as_user["access_level"] = 3
    try:
        assert len(client.get("/api/approvals").json()["approvals"]) == 2
    finally:
        as_user["role"] = "Guest"
        as_user["access_level"] = 0


def test_approval_is_not_spendable_by_another_subject(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "whoami"})
    _approve(client, as_user, aid)
    as_user["uid"] = "other-subject"
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert r.status_code == 403


# ── 6. Containment survives the boundary ──────────────────────────────────────

def test_shell_allowlist_still_holds_after_approval(client, as_user):
    aid = _request_approval(client, "execute_shell", {"command": "rm -rf /"})
    _approve(client, as_user, aid)
    r = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "rm -rf /"}, "approval_id": aid},
    )
    assert r.status_code == 200
    assert r.json()["success"] is False  # approval does not bypass the allowlist


def test_read_containment_still_holds(client, as_user):
    r = client.post("/api/tools/read_file/run", json={"payload": {"path": "/etc/passwd"}})
    assert r.status_code == 200
    assert r.json()["success"] is False


# ── 7. The declaration itself ─────────────────────────────────────────────────

def test_tool_and_approval_routes_declare_require_auth():
    """Pin the boundary at the source level so a future edit cannot silently
    drop the dependency."""
    import api.main as _m
    for fn in (_m.list_tools_endpoint, _m.run_tool_endpoint,
               _m.agent_spawn, _m.ceo_chat):
        params = inspect.signature(fn).parameters
        assert "user" in params, f"{fn.__name__} does not declare an auth dependency"
    import api.plan_routes as _p
    assert "user" in inspect.signature(_p.run_plan).parameters
