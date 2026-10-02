"""Verified boundary — AUTHORITY ≠ AUTHORIZATION (Arkadia-native).

The dedicated test the boundary map flagged as missing. ``AUTHORITY`` and
``AUTHORIZATION`` are separate properties and neither substitutes for the other:

  * **AUTHORIZATION** is a property of the *route* — ``Depends(require_auth)``
    decides whether a principal may reach an operation at all.
  * **AUTHORITY** is a property of the *principal* — the ``Govern`` permission
    (Flamekeeper role, or ``access_level >= 3``) decides whether it may make a
    governance decision.

Consequences this file pins:

  1. An authenticated principal is *authorized* to reach ``/api/approvals``
     surfaces while *lacking authority* to decide — and the denial is ``403``
     (forbidden), not ``401`` (unauthenticated). The two layers are distinct.
  2. Authority does **not** confer reach: an unauthenticated caller cannot decide
     merely by claiming a governing role — it is still ``401``.
  3. Authority is computed from the principal (``_has_govern_authority``),
     independent of any route, and is not derived from authentication.

Anonymous-denial cases exercise the *real* dependency (no override). Authority
cases override ``require_auth`` so the identity under test is deterministic.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from api.approval_routes import (
    APPROVAL_LOCK,
    PENDING_APPROVALS,
    _has_govern_authority,
    _require_govern_authority,
)
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
    """Override auth with a mutable identity. Default: an ordinary
    authenticated principal (Guest, access_level 0) — authorized to reach
    routes, without authority to decide."""
    current = {"uid": "authz-subject", "role": "Guest", "access_level": 0}
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


def _request_approval(client, tool_name="execute_shell", payload=None):
    r = client.post(
        "/api/approvals/request",
        json={"tool_name": tool_name, "payload": payload or {"command": "whoami"}, "description": "t"},
    )
    assert r.status_code == 200, r.text
    return r.json()["approval_id"]


def _decide_as_reviewer(client, as_user, aid, *, verb="approve", authorized=False):
    """Decide *aid* as a principal DISTINCT from the requester.

    The reviewer identity differs from the requester so that a 403 can only be
    the authority gate — never the self-approval prohibition. This is what makes
    the AUTHORITY ≠ AUTHORIZATION assertion isolate the authority layer.
    """
    prev = (as_user["uid"], as_user["role"], as_user["access_level"])
    as_user["uid"] = "reviewer"
    as_user["role"] = "Flamekeeper" if authorized else "Guest"
    as_user["access_level"] = 3 if authorized else 0
    try:
        return client.post(f"/api/approvals/{aid}/{verb}")
    finally:
        as_user["uid"], as_user["role"], as_user["access_level"] = prev


# ── 1. Authorized to reach ≠ authoritative to decide ──────────────────────────

def test_authenticated_principal_reaches_approval_surface(client, as_user):
    """A Guest is AUTHORIZED to reach the approval surfaces (auth-gated)."""
    assert client.get("/api/approvals").status_code == 200
    assert client.post(
        "/api/approvals/request",
        json={"tool_name": "execute_shell", "payload": {"command": "whoami"}},
    ).status_code == 200


def test_distinct_unauthoritative_reviewer_cannot_decide(client, as_user):
    """An authenticated principal with no Govern authority cannot decide — even
    when it is NOT the requester, so the denial is the authority gate alone."""
    aid = _request_approval(client)
    assert _decide_as_reviewer(client, as_user, aid, verb="approve").status_code == 403
    assert _decide_as_reviewer(client, as_user, aid, verb="reject").status_code == 403


def test_authority_denial_is_forbidden_not_unauthenticated(client, as_user):
    """The distinction is legible in the status code: reaching the route is
    authorization (would be 401 if denied); failing the authority check is
    authorization's *separate* layer and is 403."""
    aid = _request_approval(client)
    r = _decide_as_reviewer(client, as_user, aid, verb="approve")
    assert r.status_code == 403
    assert r.status_code != 401


def test_authority_denial_names_the_govern_permission(client, as_user):
    """The 403 states *why*: it is the missing Govern authority, not some other
    forbidden condition."""
    aid = _request_approval(client)
    detail = _decide_as_reviewer(client, as_user, aid, verb="approve").json()["detail"]
    assert "Govern" in detail or "authority" in detail.lower()


def test_authoritative_reviewer_can_decide(client, as_user):
    """Control: the same distinct reviewer, once authoritative, is allowed."""
    aid = _request_approval(client)
    assert _decide_as_reviewer(client, as_user, aid, authorized=True).status_code == 200


# ── 2. Authority does not confer reach (no substitute for authorization) ──────

def test_authority_claim_without_authentication_cannot_reach(client):
    """An anonymous caller cannot decide merely by being authoritative in
    principle: authority does not grant route reach."""
    assert client.post("/api/approvals/anything/approve").status_code == 401


def test_authority_does_not_bypass_tool_run_authorization(client, as_user):
    """A principal holding no approval authority can still reach a non-gated
    tool — authorization is independent of authority — and remains unable to
    decide approvals."""
    # authorized to run a non-gated tool
    assert client.post(
        "/api/tools/read_file/run", json={"payload": {"path": "README.md"}}
    ).status_code == 200
    # ...but still not authoritative over approvals
    aid = _request_approval(client)
    assert client.post(f"/api/approvals/{aid}/approve").status_code == 403


# ── 3. Authority is a principal property, computed independently ──────────────

@pytest.mark.parametrize("principal,expected", [
    ({"role": "Flamekeeper", "access_level": 0}, True),
    ({"role": "Flamekeeper"}, True),
    ({"role": "Guest", "access_level": 3}, True),
    ({"role": "Weaver", "access_level": 2}, False),
    ({"role": "Guest", "access_level": 0}, False),
    ({}, False),
])
def test_authority_is_computed_from_the_principal(principal, expected):
    """AUTHORITY is a function of the principal (role / access level), not of
    route reachability and not of authentication."""
    assert _has_govern_authority(principal) is expected


def test_authentication_alone_does_not_confer_authority():
    """An identity with no governing role and no sovereign access level has no
    authority, however authenticated it is."""
    assert _has_govern_authority({"uid": "someone", "role": "Guest", "access_level": 0}) is False


def test_authority_predicate_ignores_unrelated_claims():
    """Authority is not inferred from unrelated identity attributes."""
    assert _has_govern_authority({"uid": "x", "email": "x@example.com", "role": "Witness"}) is False


def test_require_govern_authority_raises_forbidden():
    """The authority gate is an authorization-layer failure (403), not an
    authentication failure (401)."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        _require_govern_authority({"role": "Guest", "access_level": 0})
    assert exc.value.status_code == 403
    # an authoritative principal passes without raising
    _require_govern_authority({"role": "Flamekeeper", "access_level": 0})


# ── 4. The declaration itself ─────────────────────────────────────────────────

def test_decision_routes_declare_the_authority_gate():
    """Pin the boundary at the source level: both decision routes must call the
    authority gate, so a future edit cannot silently drop it."""
    import api.approval_routes as _a
    for fn in (_a.api_approve, _a.api_reject):
        src = inspect.getsource(fn)
        assert "_require_govern_authority(user)" in src, (
            f"{fn.__name__} no longer declares the authority gate"
        )
    # and the listing route distinguishes reviewer from ordinary caller
    assert "_has_govern_authority(user)" in inspect.getsource(_a.api_list_approvals)
