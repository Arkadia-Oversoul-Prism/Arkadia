"""Phase 6 — persistent execution gate.

The test deliberately kills a worker process after its first durable
checkpoint, reconstructs the store, and resumes the same task from that
checkpoint. No second queue implementation is involved.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import time
from pathlib import Path

from kernel.jobs import JobStore


def _bind_store(store):
    import kernel.jobs as jobs
    jobs._store = store


def _crash_worker(snapshot: str, ready: mp.Queue) -> None:
    import kernel.worker as worker

    store = JobStore(snapshot)
    _bind_store(store)
    job = store.create({"type": "phase6_probe", "task_id": "EV-PHASE6-001"}, source="phase6-test")

    def slow_execute(_intent):
        ready.put("entered")
        time.sleep(30)
        return {"success": True, "handled": True, "summary": "should not finish"}

    worker.execute_intent = slow_execute
    worker._process_job(job, "phase6-crash-worker")


def test_kill_worker_resume_from_last_checkpoint(tmp_path: Path):
    snapshot = str(tmp_path / "jobs.json")
    ready: mp.Queue = mp.Queue()
    process = mp.Process(target=_crash_worker, args=(snapshot, ready))
    process.start()
    try:
        assert ready.get(timeout=10) == "entered"

        deadline = time.time() + 10
        while time.time() < deadline:
            if os.path.exists(snapshot):
                recovered = JobStore(snapshot)
                jobs = recovered.list()
                if jobs and jobs[0]["execution"]["checkpoints"]:
                    break
            time.sleep(0.1)
        else:
            raise AssertionError("first durable checkpoint was not written")

        process.terminate()
        process.join(timeout=10)
        assert process.exitcode is not None

        recovered = JobStore(snapshot)
        jobs = recovered.list()
        assert len(jobs) == 1
        job = jobs[0]
        assert job["status"] == "pending"
        assert job["execution"]["lease"] is None
        assert job["execution"]["state"] == "RESUMING"
        assert job["execution"]["checkpoints"][-1]["name"] == "execution.started"
        assert job["execution"]["checkpoints"][-1]["data"]["resume_from"] is None

        import kernel.worker as worker
        observed: dict = {}
        _bind_store(recovered)

        def resumed_execute(intent):
            observed["resume_from"] = intent["payload"]["_execution"]["resume_from"]
            return {"success": True, "handled": True, "summary": "resumed"}

        worker.execute_intent = resumed_execute
        worker._process_job(job, "phase6-resume-worker")

        final = recovered.get(job["job_id"])
        assert final is not None
        assert final["status"] == "completed"
        assert observed["resume_from"] == "execution.started"
        assert final["execution"]["state"] == "COMPLETE"
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


def test_lease_recovery_is_bounded(tmp_path: Path):
    store = JobStore(str(tmp_path / "jobs.json"))
    job = store.create({"type": "phase6_probe"})
    assert store.acquire_lease(job["job_id"], "worker-a", lease_seconds=0.01)
    time.sleep(0.03)
    assert store.recover_expired_leases() == 1
    recovered = store.get(job["job_id"])
    assert recovered["status"] == "pending"
    assert recovered["execution"]["lease"] is None
