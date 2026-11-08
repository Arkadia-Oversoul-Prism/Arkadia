"""AO-006 — the Arkadia One canvas contract.

The console renders Engineering Lab, Arkana and Weaver as three product
boundaries over one backend. This guard binds the unified canvas to the
properties that make it safe to serve, and to the orchestration dimensions
Weaver's surface previously had to declare *unavailable*.

What is asserted, and why each one is load-bearing:

1.  **One read, three surfaces.** ``GET /api/canvas`` returns all three sections
    in one response, and the declared surface set is exactly the three the
    console renders. A canvas that silently dropped a surface would leave the
    workspace shell hydrating a partial picture.

2.  **Identity is the only scope.** No canvas route accepts a subject, owner or
    uid parameter. Cross-subject reads are impossible by construction rather
    than by a check that could be forgotten — the strongest form of the
    isolation requirement.

3.  **Isolation is real, not declared.** Two subjects with real Lab state each
    see only their own sessions, runs and threads, and a session id belonging to
    one subject returns 404 for the other (existence is never leaked).

4.  **The canvas is read-only.** Every canvas route is GET. Consequential acts
    stay on the routes that own their human-authorization boundary.

5.  **The orchestration dimensions are published.** The run record carries
    ``depends_on``, ``subtasks``, ``attempt`` and ``retryable``, and the canvas
    projects them. This is the contract change Weaver's surface named as the
    smallest thing that would close its gap.

6.  **Retryability is a state-machine fact.** ``retryable`` is derived from
    whether an executable session state is reachable, so the payload cannot
    promise a retry the API would refuse. Measured on this revision no run is
    retryable, and the policy string says why.

7.  **Absence is reported, not invented.** A subject with no state gets empty
    collections and a real count of zero — never a fabricated session.
"""
from __future__ import annotations

import base64
import json
import os
import tempfile

import pytest

# The Lab and SolSpire stores snapshot their DB path at import time, so the
# redirect must happen before any of them is imported.
_STATE = tempfile.mkdtemp(prefix="ao006_canvas_")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SOLSPIRE_DATA_DIR", _STATE)
os.environ.setdefault("ARKADIA_DB_PATH", os.path.join(_STATE, "knowledge.db"))


def _token(uid: str) -> str:
    """A dev-mode bearer payload (signature is not verified outside production)."""
    payload = base64.urlsafe_b64encode(
        json.dumps({"uid": uid, "user_id": uid, "email": f"{uid}@example.test"}).encode()
    ).decode().rstrip("=")
    return f"header.{payload}.signature"


def _headers(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


# A caller-supplied scope parameter would let a request choose whose data is
# read. Identity is the only scope, so no canvas route may accept one of these.
_CALLER_SUPPLIED_SCOPE_PARAMETERS = frozenset(
    {"subject", "subject_ref", "uid", "user_id", "owner", "owner_uid"}
)


def _caller_supplied_scope_offenders(routes) -> list[str]:
    """Name every route that accepts a caller-supplied subject/owner parameter.

    The live isolation assertion and its negative control both call this, so
    neutering the detector reddens the control as well as the live node.
    """
    return [
        f"{route.path} accepts {param.name!r}"
        for route in routes
        for param in (getattr(route, "dependant", None).query_params if route.dependant else [])
        if param.name in _CALLER_SUPPLIED_SCOPE_PARAMETERS
    ]


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


@pytest.fixture(scope="module")
def alice_state(client):
    """Real Lab state for one subject: an agent, a session, and one executed run."""
    headers = _headers("ao006-alice")
    agent = client.post(
        "/api/lab/engineering/agents", headers=headers, json={"role": "WEAVER"}
    ).json()
    workspace = client.get("/solspire/workspace", headers=headers).json()["workspace"]["id"]
    session = client.post(
        "/api/lab/engineering/sessions",
        headers=headers,
        json={
            "workspace_ref": workspace,
            "agent_id": agent["agent_id"],
            "objective": "ao006 canvas probe",
        },
    ).json()
    session_id = session["session_id"]
    client.post(
        f"/api/lab/engineering/sessions/{session_id}/authorize",
        headers=headers,
        json={"operations_allowed": ["read", "list"]},
    )
    executed = client.post(
        f"/api/lab/engineering/sessions/{session_id}/execute",
        headers=headers,
        json={
            "objective": "ao006 canvas probe",
            "operations": [
                {"kind": "list", "target": "."},
                {"kind": "read", "target": "README.md"},
            ],
        },
    )
    assert executed.status_code == 200, executed.text
    return {"session_id": session_id, "run": executed.json()}


# ---------------------------------------------------------------------------
# 1. One read, three surfaces
# ---------------------------------------------------------------------------


def test_canvas_serves_all_three_surfaces_in_one_read(client):
    response = client.get("/api/canvas", headers=_headers("ao006-alice"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["surfaces"] == ["engineering-lab", "arkana", "weaver"]
    assert set(body["sections"]) == {"engineering-lab", "arkana", "weaver"}
    for section in body["sections"].values():
        assert section["contract"].startswith("/"), "a section must name its owning contract"


def test_canvas_surface_discovery_matches_the_served_sections(client):
    headers = _headers("ao006-alice")
    declared = client.get("/api/canvas/surfaces", headers=headers).json()
    served = client.get("/api/canvas", headers=headers).json()
    assert [s["id"] for s in declared["surfaces"]] == served["surfaces"]


# ---------------------------------------------------------------------------
# 2. Identity is the only scope
# ---------------------------------------------------------------------------


def test_no_canvas_route_accepts_a_subject_parameter():
    """Cross-subject reads must be impossible by construction, not by a check."""
    from api.canvas_routes import router

    offenders = _caller_supplied_scope_offenders(router.routes)
    assert offenders == [], f"canvas route(s) accept a caller-supplied subject: {offenders}"


def test_canvas_requires_authentication(client):
    assert client.get("/api/canvas").status_code == 401
    assert client.get("/api/canvas/surfaces").status_code == 401


# ---------------------------------------------------------------------------
# 3. Isolation is real
# ---------------------------------------------------------------------------


def test_another_subject_sees_none_of_the_first_subjects_state(client, alice_state):
    bob = _headers("ao006-bob")
    canvas = client.get("/api/canvas", headers=bob).json()
    assert canvas["sections"]["engineering-lab"]["sessions"] == []
    assert canvas["sections"]["weaver"]["runs"] == []
    assert canvas["sections"]["arkana"]["count"] == 0


def test_a_session_id_from_another_subject_is_not_found(client, alice_state):
    """404, not 403: existence is never leaked across subjects."""
    response = client.get(
        f"/api/canvas/sessions/{alice_state['session_id']}", headers=_headers("ao006-bob")
    )
    assert response.status_code == 404


def test_the_owner_can_read_their_own_session_canvas(client, alice_state):
    response = client.get(
        f"/api/canvas/sessions/{alice_state['session_id']}", headers=_headers("ao006-alice")
    )
    assert response.status_code == 200
    assert response.json()["session"]["session_id"] == alice_state["session_id"]


# ---------------------------------------------------------------------------
# 4. The canvas is read-only
# ---------------------------------------------------------------------------


def test_every_canvas_route_is_a_get():
    from api.canvas_routes import router

    mutating = [r.path for r in router.routes if not (r.methods <= {"GET"})]
    assert mutating == [], f"the canvas exposes a mutating route: {mutating}"


# ---------------------------------------------------------------------------
# 5. The orchestration dimensions are published
# ---------------------------------------------------------------------------


def test_the_run_record_publishes_the_four_orchestration_dimensions(client, alice_state):
    """The four dimensions are asserted on the *persisted* record, not the response.

    The execute response is the run's own summary; the record is read back
    through the canvas so the assertion is on what the store actually holds.
    """
    view = client.get(
        f"/api/canvas/sessions/{alice_state['session_id']}", headers=_headers("ao006-alice")
    ).json()
    run = view["runs"][0]
    for field in ("depends_on", "subtasks", "attempt", "retryable", "retry_policy"):
        assert field in run, f"the persisted run record does not publish {field!r}"
    assert run["attempt"] == 1
    assert run["depends_on"] == []


def test_a_blocked_run_persists_the_retryable_value_the_state_machine_decides(
    client, alice_state
):
    """S1 — the persisted `retryable` for a BLOCKED run is the real decision.

    The vacuous direction (`retryable is False` on a run that could never be
    retryable) proves nothing. This drives a run to BLOCKED and asserts the
    value the store holds *and* the policy string that decided it, so the
    pre/post-advance ordering cannot silently regress: reading the session
    before `_advance` would persist a decision taken on the wrong side of the
    transition.
    """
    from lab.engineering_lab.runtime import _retry_decision

    headers = _headers("ao006-alice")
    agent = client.post(
        "/api/lab/engineering/agents", headers=headers, json={"role": "WEAVER"}
    ).json()
    workspace = client.get("/solspire/workspace", headers=headers).json()["workspace"]["id"]
    session = client.post(
        "/api/lab/engineering/sessions",
        headers=headers,
        json={
            "workspace_ref": workspace,
            "agent_id": agent["agent_id"],
            "objective": "ao006 blocked retry probe",
        },
    ).json()
    session_id = session["session_id"]
    client.post(
        f"/api/lab/engineering/sessions/{session_id}/authorize",
        headers=headers,
        json={"operations_allowed": ["read"]},
    )
    # A read of a target that does not exist produces an observation carrying an
    # error, which is the substrate's own route to a BLOCKED result state.
    blocked = client.post(
        f"/api/lab/engineering/sessions/{session_id}/execute",
        headers=headers,
        json={
            "objective": "ao006 blocked retry probe",
            "operations": [{"kind": "read", "target": "does-not-exist-ao006.txt"}],
        },
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["result_state"] == "BLOCKED", blocked.text

    view = client.get(f"/api/canvas/sessions/{session_id}", headers=headers).json()
    run = view["runs"][-1]
    assert run["result_state"] == "BLOCKED", f"the probe did not reach BLOCKED: {run['result_state']}"

    # The persisted value must equal the decision the state machine makes from
    # the run state, result state and the session state the run actually left
    # behind. Recomputing it here is the point: reading the session *before*
    # `_advance` would persist a decision taken on the wrong side of the
    # transition, and this assertion is what catches that.
    session_state = view["session"]["state"]
    expected, expected_policy = _retry_decision(
        run["state"], run["result_state"], session_state
    )
    assert run["retryable"] is expected, (
        f"persisted retryable={run['retryable']} disagrees with the state machine "
        f"(run {run['state']!r}/{run['result_state']!r}, session {session_state!r} "
        f"-> expected {expected})"
    )
    # And the policy string names the rule that decided it, so the value is
    # traceable rather than a bare boolean.
    assert run["retry_policy"] == expected_policy
    assert run["retry_policy"].startswith("AEAS-5/REVISION_REQUIRED")
    # A BLOCKED result state is never retryable while the run sits in a
    # non-retryable run state, which is the honest answer on this revision.
    assert run["retryable"] is False
    assert run["retry_policy"].endswith(":terminal")


def test_the_canvas_projects_dependencies_subtasks_and_retries(client, alice_state):
    view = client.get(
        f"/api/canvas/sessions/{alice_state['session_id']}", headers=_headers("ao006-alice")
    ).json()
    orchestration = view["orchestration"]
    assert set(orchestration) == {"dependencies", "subtasks", "retries"}

    run = view["runs"][0]
    for field in ("depends_on", "subtasks", "attempt", "retryable", "retry_policy"):
        assert field in run, f"the run record does not publish {field!r}"

    # The decomposition is the task's own operation set, with observed states.
    assert [s["kind"] for s in run["subtasks"]] == ["list", "read"]
    assert [s["state"] for s in run["subtasks"]] == ["SUCCEEDED", "SUCCEEDED"]
    assert run["attempt"] == 1


def test_the_canvas_publishes_a_poll_contract_instead_of_implying_a_stream(client):
    weaver = client.get("/api/canvas", headers=_headers("ao006-alice")).json()["sections"]["weaver"]
    poll = weaver["orchestration"]["poll"]
    assert poll["mode"] == "poll"
    assert poll["cursor_field"] == "updated_at"
    assert "No SSE/WebSocket" in poll["note"]


# ---------------------------------------------------------------------------
# 6. Retryability is a state-machine fact
# ---------------------------------------------------------------------------


def test_retryability_is_derived_from_reachable_session_states():
    from lab.engineering_lab.runtime import _retry_decision

    # A boundary refusal is never retryable, whatever the session can reach.
    assert _retry_decision("BLOCKED", "BOUNDARY_REFUSED", "AUTHORIZED")[0] is False
    # A terminal run state is never retryable.
    assert _retry_decision("VERIFYING", None, "VERIFYING")[0] is False
    # A retry is possible only when an executable state is reachable.
    assert _retry_decision("BLOCKED", None, "AUTHORIZED")[0] is True
    retryable, policy = _retry_decision("BLOCKED", None, "REVISION_REQUIRED")
    assert retryable is False
    assert policy.endswith("no-reauthorization-path")


def test_the_retry_policy_does_not_promise_an_unreachable_retry():
    """Measured on this revision: REVISION_REQUIRED cannot reach AUTHORIZED/QUEUED.

    If a re-authorization edge is added to the state machine this assertion
    flips, which is the signal to re-measure the policy — not a defect.
    """
    from lab.engineering_lab.runtime import EXECUTABLE_SESSION_STATES, _reachable_states

    reachable = _reachable_states("REVISION_REQUIRED")
    assert not (reachable & EXECUTABLE_SESSION_STATES), (
        "the state machine now permits re-authorization; re-measure the retry policy"
    )


# ---------------------------------------------------------------------------
# 7. Absence is reported, not invented
# ---------------------------------------------------------------------------


def test_an_empty_subject_gets_empty_collections_and_a_real_zero(client):
    canvas = client.get("/api/canvas", headers=_headers("ao006-empty")).json()
    assert canvas["sections"]["arkana"]["threads"] == []
    assert canvas["sections"]["arkana"]["count"] == 0
    assert canvas["sections"]["weaver"]["orchestration"]["dependencies"] == []
    assert canvas["sections"]["weaver"]["orchestration"]["subtasks"] == []
    assert canvas["sections"]["weaver"]["orchestration"]["poll"]["updated_at"] is None


# ---------------------------------------------------------------------------
# Negative controls — the detectors must be able to fail
# ---------------------------------------------------------------------------


def test_negative_control_a_subject_parameter_would_be_detected():
    """The isolation detector is proven against the shape it exists to catch.

    Calls :func:`_caller_supplied_scope_offenders` — the same detector the live
    assertion uses — so neutering the detector reddens this control too. It also
    asserts a clean route is *not* reported, so a detector that flags everything
    cannot pass either.
    """
    from fastapi import APIRouter, Depends, Query

    from api.auth import require_auth

    probe = APIRouter()

    @probe.get("/probe")
    async def _probe(subject: str = Query(default=""), user: dict = Depends(require_auth)):
        return {}

    @probe.get("/clean")
    async def _clean(user: dict = Depends(require_auth)):
        return {}

    assert _caller_supplied_scope_offenders(probe.routes) == [
        "/probe accepts 'subject'"
    ], "the detector did not report a caller-supplied subject"
    clean = [r for r in probe.routes if r.path == "/clean"]
    assert _caller_supplied_scope_offenders(clean) == [], (
        "the detector must not report a route that takes no scope parameter"
    )
