"""B1.2 — SQLiteJobStore tests.

Covers:
- Full job lifecycle (create → running → completed / failed)
- Retry logic and MAX_RETRIES boundary
- Atomic claim: two workers cannot claim the same job
- Crash recovery: RUNNING jobs reset to PENDING on store init
- stats() correctness
- list() filtering and ordering
- task_done() is a no-op (API parity)
- reset() clears all jobs
"""
from __future__ import annotations

import threading
import time
import pytest

from kernel.storage.sqlite_job_store import (
    SQLiteJobStore,
    PENDING, RUNNING, COMPLETED, FAILED, MAX_RETRIES,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_jobs.db")


@pytest.fixture()
def store(db_path):
    return SQLiteJobStore(db_path=db_path)


# ── lifecycle ─────────────────────────────────────────────────────────────────

def test_create_returns_job(store):
    job = store.create({"type": "test"})
    assert job["job_id"].startswith("job_")
    assert job["status"] == PENDING
    assert job["intent"] == {"type": "test"}
    assert job["retries"] == 0
    assert job["source"] == "api"
    assert job["result"] is None
    assert job["error"] is None


def test_get_returns_copy(store):
    job = store.create({"type": "x"})
    fetched = store.get(job["job_id"])
    assert fetched is not None
    assert fetched["job_id"] == job["job_id"]


def test_get_missing_returns_none(store):
    assert store.get("job_nonexistent") is None


def test_mark_running(store):
    job = store.create({"type": "x"})
    updated = store.mark_running(job["job_id"])
    assert updated["status"] == RUNNING
    assert updated["started_at"] is not None


def test_mark_completed(store):
    job = store.create({"type": "x"})
    store.mark_running(job["job_id"])
    done = store.mark_completed(job["job_id"], result={"answer": 42})
    assert done["status"] == COMPLETED
    assert done["result"] == {"answer": 42}
    assert done["ended_at"] is not None


def test_mark_failed(store):
    job = store.create({"type": "x"})
    store.mark_running(job["job_id"])
    failed = store.mark_failed(job["job_id"], error="timeout")
    assert failed["status"] == FAILED
    assert failed["error"] == "timeout"
    assert failed["ended_at"] is not None


# ── retry logic ───────────────────────────────────────────────────────────────

def test_requeue_bumps_retry_count(store):
    job = store.create({"type": "x"})
    store.mark_running(job["job_id"])
    requeued = store.requeue_for_retry(job["job_id"], error="transient")
    assert requeued["status"] == PENDING
    assert requeued["retries"] == 1
    assert requeued["error"] == "transient"


def test_requeue_three_times(store):
    job = store.create({"type": "x"})
    jid = job["job_id"]
    for i in range(MAX_RETRIES):
        store.mark_running(jid)
        store.requeue_for_retry(jid, error=f"attempt {i + 1}")
    final = store.get(jid)
    assert final["retries"] == MAX_RETRIES


# ── list / filter ─────────────────────────────────────────────────────────────

def test_list_all(store):
    store.create({"type": "a"})
    store.create({"type": "b"})
    jobs = store.list()
    assert len(jobs) == 2


def test_list_by_status(store):
    j1 = store.create({"type": "a"})
    store.create({"type": "b"})
    store.mark_running(j1["job_id"])
    pending = store.list(status=PENDING)
    running = store.list(status=RUNNING)
    assert len(pending) == 1
    assert len(running) == 1


def test_list_limit(store):
    for i in range(5):
        store.create({"i": i})
    assert len(store.list(limit=3)) == 3


def test_list_ordered_newest_first(store):
    j1 = store.create({"seq": 1})
    time.sleep(0.01)
    j2 = store.create({"seq": 2})
    jobs = store.list()
    assert jobs[0]["job_id"] == j2["job_id"]
    assert jobs[1]["job_id"] == j1["job_id"]


# ── stats ─────────────────────────────────────────────────────────────────────

def test_stats_empty(store):
    s = store.stats()
    assert s["total"] == 0
    assert s["pending"] == 0


def test_stats_counts(store):
    j1 = store.create({"t": 1})
    j2 = store.create({"t": 2})
    store.mark_running(j1["job_id"])
    store.mark_completed(j1["job_id"], result=None)
    s = store.stats()
    assert s["completed"] == 1
    assert s["pending"] == 1
    assert s["total"] == 2


# ── next_job_id (queue behaviour) ─────────────────────────────────────────────

def test_next_job_id_returns_pending_job(store):
    job = store.create({"type": "claim_me"})
    # The store init calls _recover_running_jobs; re-create as pending
    job_id = store.next_job_id(timeout=1.0)
    assert job_id == job["job_id"]
    # Claimed job is now RUNNING
    claimed = store.get(job_id)
    assert claimed["status"] == RUNNING


def test_next_job_id_returns_none_when_empty(store):
    result = store.next_job_id(timeout=0.1)
    assert result is None


def test_task_done_is_noop(store):
    store.task_done()   # must not raise


# ── atomic claim: two workers, one job ───────────────────────────────────────

def test_atomic_claim_no_double_claim(db_path):
    """Two threads racing on next_job_id must each claim a different job."""
    store = SQLiteJobStore(db_path=db_path)
    store.create({"t": 1})
    store.create({"t": 2})

    claimed: list[str | None] = []
    lock = threading.Lock()

    def worker():
        jid = store.next_job_id(timeout=2.0)
        with lock:
            claimed.append(jid)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Both jobs claimed, each by exactly one worker
    assert len(claimed) == 2
    assert None not in claimed
    assert claimed[0] != claimed[1]


def test_no_double_claim_with_one_job(db_path):
    """With one job and two racing workers, exactly one claims it."""
    store = SQLiteJobStore(db_path=db_path)
    store.create({"t": 1})

    claimed: list[str | None] = []
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()   # start simultaneously
        jid = store.next_job_id(timeout=1.0)
        with threading.Lock():
            claimed.append(jid)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    non_null = [j for j in claimed if j is not None]
    assert len(non_null) == 1


# ── crash recovery ────────────────────────────────────────────────────────────

def test_running_jobs_reset_to_pending_on_restart(db_path):
    """Simulate a crash: create store, mark a job running, then open a new
    store instance against the same DB — the RUNNING job must become PENDING."""
    store1 = SQLiteJobStore(db_path=db_path)
    job = store1.create({"type": "crash_test"})
    # Directly update to RUNNING without going through next_job_id
    store1.update(job["job_id"], status=RUNNING, started_at=time.time())
    assert store1.get(job["job_id"])["status"] == RUNNING

    # Simulated restart: new store instance
    store2 = SQLiteJobStore(db_path=db_path)
    recovered = store2.get(job["job_id"])
    assert recovered["status"] == PENDING


# ── reset (test-only) ─────────────────────────────────────────────────────────

def test_reset_clears_all_jobs(store):
    store.create({"t": 1})
    store.create({"t": 2})
    store.reset()
    assert store.list() == []
    assert store.stats()["total"] == 0
