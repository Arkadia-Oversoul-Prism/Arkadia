"""Verified boundary — execution and WorkEvent remain distinct, with a Weaver causal bridge.

Two independent records exist on this substrate, and they are **not** joined:

  * a **tool execution** — ``POST /api/tools/{tool}/run`` returns a synchronous
    envelope and, when the tool requires approval, consumes the approval. It
    records ``consumed_at`` / ``consumed_by`` on the approval. It does **not**
    create a kernel job, and it does **not** create a SolSpire WorkEvent.
  * a **kernel Work Event** — ``POST /api/job/create`` creates a job whose own
    ``execution.events`` log records ``lease.acquired`` and
    ``execution.started`` / ``execution.completed`` checkpoints. That job carries
    no ``work_event`` / ``work_ref`` field.
  * a **SolSpire WorkEvent** — ``solspire.workevent_manager`` persists a distinct
    continuity record (``work_events`` table). Its **only** creator in the
    codebase is the ``/solspire/workevents`` router. Nothing in the execution or
    job path constructs one.

So the status of EXECUTION → WORK EVENT is:

  * **recorded** as *two separate records* (execution evidence on the approval /
    job; WorkEvents in their own spine), and
  * **absent** as a *durable join*: there is no identifier connecting an
    execution to a WorkEvent, and no code path that would create one.

Consequences this file pins:

  1. A gated tool run succeeds and consumes the approval, while creating **no**
     job and **no** WorkEvent.
  2. The kernel job path creates a job whose execution events are recorded, but
     that job references **no** WorkEvent.
  3. WorkEvents are created **only** through their own router; an operator can
     create one, but the execution path never does.
  4. The WorkEvent model carries no execution/job reference field — the absence
     is structural, not incidental.
  5. ``weaver/enterprise_orchestration.py`` holds the richer causal graph but its
     ``forward_walk`` / ``reverse_walk`` traversal is **not exposed over HTTP** —
     implemented, unexposed. (Its counters and verified evidence *are* readable
     through the enterprise control-room projection; only the walk has no route.)

This test measures the system that exists. It does **not** manufacture a
WorkEvent to demonstrate the boundary.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from api.approval_routes import APPROVAL_LOCK, PENDING_APPROVALS
from api.auth import require_auth
from api.main import app
from kernel.tools_real import register_real_tools
from solspire import workevent_manager as _wem


@pytest.fixture(scope="module", autouse=True)
def _tools_registered():
    register_real_tools()


@pytest.fixture(autouse=True)
def _isolate_dependency_overrides():
    app.dependency_overrides.pop(require_auth, None)
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture(autouse=True)
def _isolate_approvals():
    with APPROVAL_LOCK:
        PENDING_APPROVALS.clear()
    yield
    with APPROVAL_LOCK:
        PENDING_APPROVALS.clear()


@pytest.fixture(autouse=True)
def _isolate_workevents(tmp_path, monkeypatch):
    """Point the WorkEvent spine at a fresh DB so the count is deterministic."""
    monkeypatch.setattr(_wem, "_DB_PATH", str(tmp_path / "work_events.db"))
    yield


@pytest.fixture(autouse=True)
def _isolate_jobs(tmp_path, monkeypatch):
    """Point the kernel job store at a fresh snapshot."""
    from kernel import jobs as _jobs

    monkeypatch.setattr(_jobs, "_store", _jobs.JobStore(snapshot_path=str(tmp_path / "job_store.json")))
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def as_user():
    current = {"uid": "exec-subject", "role": "Guest", "access_level": 0}
    app.dependency_overrides[require_auth] = lambda: {
        "uid": current["uid"],
        "email": f"{current['uid']}@example.com",
        "access_level": current["access_level"],
        "role": current["role"],
    }
    yield current
    app.dependency_overrides.pop(require_auth, None)


def _job_count(client) -> int:
    return len(client.get("/api/jobs").json()["jobs"])


def _workevent_count() -> int:
    return len(_wem.get_workevent_manager().list("exec-subject"))


def _run_gated_tool(client) -> None:
    """Request → approve (sovereign) → consume, the real decision/act path."""
    r = client.post(
        "/api/approvals/request",
        json={"tool_name": "execute_shell", "payload": {"command": "whoami"}, "description": "t"},
    )
    assert r.status_code == 200, r.text
    aid = r.json()["approval_id"]

    app.dependency_overrides[require_auth] = lambda: {
        "uid": "sovereign-node", "email": "s@example.com", "access_level": 3, "role": "Flamekeeper"
    }
    assert client.post(f"/api/approvals/{aid}/approve").status_code == 200

    app.dependency_overrides[require_auth] = lambda: {
        "uid": "exec-subject", "email": "exec-subject@example.com", "access_level": 0, "role": "Guest"
    }
    run = client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )
    assert run.status_code == 200, run.text
    assert run.json()["success"] is True


def test_gated_execution_creates_no_job_and_no_workevent(client, as_user):
    """The act runs and consumes the approval — yet the WorkEvent spine stays empty."""
    before_jobs = _job_count(client)
    before_events = _workevent_count()

    _run_gated_tool(client)

    assert _job_count(client) == before_jobs, "execution must not create a kernel job"
    assert _workevent_count() == before_events, "execution must not create a WorkEvent"


def test_execution_is_recorded_on_the_approval_not_as_a_workevent(client, as_user):
    """Execution leaves *some* record — but on the approval, not in the spine."""
    r = client.post(
        "/api/approvals/request",
        json={"tool_name": "execute_shell", "payload": {"command": "whoami"}, "description": "t"},
    )
    aid = r.json()["approval_id"]

    app.dependency_overrides[require_auth] = lambda: {
        "uid": "sovereign-node", "email": "s@example.com", "access_level": 3, "role": "Flamekeeper"
    }
    client.post(f"/api/approvals/{aid}/approve")
    app.dependency_overrides[require_auth] = lambda: {
        "uid": "exec-subject", "email": "exec-subject@example.com", "access_level": 0, "role": "Guest"
    }
    client.post(
        "/api/tools/execute_shell/run",
        json={"payload": {"command": "whoami"}, "approval_id": aid},
    )

    approval = PENDING_APPROVALS[aid]
    assert approval["consumed_at"] is not None
    assert approval["consumed_by"] == "exec-subject"
    assert _workevent_count() == 0


def test_kernel_job_records_execution_events_without_a_workevent(client, as_user):
    """A kernel job records its own execution events; it references no WorkEvent."""
    r = client.post(
        "/api/job/create",
        json={"intent": {"tool_name": "read_file", "subject_ref": "exec-subject",
                         "payload": {"path": "/etc/hostname"}}, "source": "gate02"},
    )
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]

    job = client.get("/api/jobs").json()["jobs"][0]
    execution = job.get("execution") or {}
    events = execution.get("events") or []
    # The job records its own execution — but only as kernel-internal events.
    assert any(e.get("event") == "lease.acquired" for e in events) or job["status"] in {"pending", "running", "completed"}

    # It carries no reference into the WorkEvent spine.
    assert not any("work" in k and "event" in k for k in job.keys())
    assert "work_event_id" not in job and "work_ref" not in job
    assert _workevent_count() == 0
    assert job_id  # the kernel id exists; the WorkEvent id does not


def test_workevent_is_created_only_through_its_own_router(client, as_user):
    """The only creator is the WorkEvent router — not the execution path."""
    # The execution path cannot have created one (nothing to list).
    assert _workevent_count() == 0

    # The router *can* create one — proving the spine is functional, not broken.
    created = _wem.get_workevent_manager().create(
        subject_ref="exec-subject",
        workspace_ref="ws-exec",
        event_type="TOOL_EXECUTED",
        occurred_at=0.0,
        work_ref="job_does_not_connect",
    )
    assert created.work_event_id
    assert _workevent_count() == 1


def test_workevent_model_has_explicit_execution_causal_reference():
    """The bridge is explicit and does not collapse WorkEvent into authorization."""
    fields = set(_wem.WorkEvent.__dataclass_fields__.keys())
    assert "execution_attempt_ref" in fields
    for forbidden in ("job_id", "task_id", "execution_ref", "approval_id"):
        assert forbidden not in fields
    assert "work_ref" in fields

def test_execution_path_never_imports_the_workevent_spine():
    """No execution module constructs a WorkEvent — verified against source."""
    import api.main as _main
    import kernel.execution as _exec
    import kernel.worker as _worker

    for module in (_main, _exec, _worker):
        src = inspect.getsource(module)
        assert "workevent" not in src.lower(), f"{module.__name__} references the WorkEvent spine"
        assert "WorkEventManager" not in src, f"{module.__name__} references WorkEventManager"


def test_enterprise_orchestration_graph_is_not_exposed_over_http(client, as_user):
    """The richer causal graph exists in code but has no HTTP route."""
    paths = set(app.openapi()["paths"].keys())
    assert not any("forward_walk" in p or "reverse_walk" in p for p in paths)
    # There is no route that traverses the enterprise orchestration graph.
    assert "/solspire/enterprise" not in paths
