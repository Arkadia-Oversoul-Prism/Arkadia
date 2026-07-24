"""B1.2 — SQLiteGoalStore tests.

Covers:
- Full goal lifecycle (create → record_run → delete)
- due_goals: status filter, next_run gate, hourly cap
- update() with validation (status, cadence, max_runs_per_hour)
- list() filtering and ordering
- record_run: counter, next_run advance, history cap
- reset() clears all goals
"""
from __future__ import annotations

import time
import pytest

from kernel.storage.sqlite_goal_store import (
    SQLiteGoalStore,
    ACTIVE, PAUSED, COMPLETED,
    MIN_CADENCE_SECONDS, MAX_RUNS_PER_HOUR_HARD, HISTORY_CAP,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_goals.db")


@pytest.fixture()
def store(db_path):
    return SQLiteGoalStore(db_path=db_path)


# ── create ────────────────────────────────────────────────────────────────────

def test_create_returns_goal(store):
    goal = store.create("Do the thing")
    assert goal["goal_id"].startswith("goal_")
    assert goal["description"] == "Do the thing"
    assert goal["status"] == ACTIVE
    assert goal["run_count"] == 0
    assert goal["history"] == []


def test_create_clamps_cadence(store):
    goal = store.create("test", cadence_seconds=5)  # below MIN
    assert goal["cadence_seconds"] >= MIN_CADENCE_SECONDS


def test_create_clamps_max_runs(store):
    goal = store.create("test", max_runs_per_hour=999)  # above hard cap
    assert goal["max_runs_per_hour"] <= MAX_RUNS_PER_HOUR_HARD


def test_create_start_now_true(store):
    before = time.time()
    goal = store.create("now", start_now=True)
    assert goal["next_run"] <= time.time()
    assert goal["next_run"] >= before - 1


def test_create_start_now_false(store):
    goal = store.create("later", cadence_seconds=300, start_now=False)
    assert goal["next_run"] > time.time()


def test_create_requires_description(store):
    with pytest.raises(ValueError):
        store.create("")
    with pytest.raises(ValueError):
        store.create("   ")


# ── get ───────────────────────────────────────────────────────────────────────

def test_get_existing(store):
    goal = store.create("x")
    fetched = store.get(goal["goal_id"])
    assert fetched["goal_id"] == goal["goal_id"]


def test_get_missing_returns_none(store):
    assert store.get("goal_nope") is None


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_all(store):
    store.create("a")
    store.create("b")
    assert len(store.list()) == 2


def test_list_by_status(store):
    g = store.create("x")
    store.create("y")
    store.update(g["goal_id"], status=PAUSED)
    assert len(store.list(status=PAUSED)) == 1
    assert len(store.list(status=ACTIVE)) == 1


# ── update ────────────────────────────────────────────────────────────────────

def test_update_status(store):
    g = store.create("x")
    updated = store.update(g["goal_id"], status=PAUSED)
    assert updated["status"] == PAUSED


def test_update_invalid_status(store):
    g = store.create("x")
    with pytest.raises(ValueError):
        store.update(g["goal_id"], status="invalid")


def test_update_clamps_cadence(store):
    g = store.create("x")
    updated = store.update(g["goal_id"], cadence_seconds=1)
    assert updated["cadence_seconds"] >= MIN_CADENCE_SECONDS


def test_update_clamps_max_runs(store):
    g = store.create("x")
    updated = store.update(g["goal_id"], max_runs_per_hour=9999)
    assert updated["max_runs_per_hour"] <= MAX_RUNS_PER_HOUR_HARD


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_existing(store):
    g = store.create("x")
    assert store.delete(g["goal_id"]) is True
    assert store.get(g["goal_id"]) is None


def test_delete_missing(store):
    assert store.delete("goal_nope") is False


# ── record_run ────────────────────────────────────────────────────────────────

def test_record_run_bumps_counters(store):
    g = store.create("x", cadence_seconds=60, start_now=True)
    ts = time.time()
    updated = store.record_run(g["goal_id"], job_id="job_abc", ts=ts)
    assert updated["run_count"] == 1
    assert updated["last_run"] == ts
    assert updated["next_run"] == pytest.approx(ts + 60, abs=0.01)
    assert "job_abc" in updated["history"]


def test_record_run_history_capped(store):
    g = store.create("x", cadence_seconds=60, start_now=True)
    for i in range(HISTORY_CAP + 10):
        store.record_run(g["goal_id"], job_id=f"job_{i:03d}")
    final = store.get(g["goal_id"])
    assert len(final["history"]) == HISTORY_CAP


def test_record_run_missing_goal(store):
    result = store.record_run("goal_nope", job_id="j")
    assert result is None


def test_record_run_without_job_id(store):
    g = store.create("x")
    updated = store.record_run(g["goal_id"], job_id=None)
    assert updated["run_count"] == 1
    assert updated["history"] == []


# ── due_goals ─────────────────────────────────────────────────────────────────

def test_due_goals_returns_past_next_run(store):
    past  = time.time() - 10
    future = time.time() + 300

    g_due = store.create("due",  cadence_seconds=60, start_now=True)
    store.update(g_due["goal_id"], next_run=past)

    g_not = store.create("soon", cadence_seconds=60, start_now=False)
    store.update(g_not["goal_id"], next_run=future)

    due = store.due_goals()
    ids = [g["goal_id"] for g in due]
    assert g_due["goal_id"] in ids
    assert g_not["goal_id"] not in ids


def test_due_goals_excludes_paused(store):
    g = store.create("x", start_now=True)
    store.update(g["goal_id"], next_run=time.time() - 1, status=PAUSED)
    assert store.due_goals() == []


def test_due_goals_excludes_completed(store):
    g = store.create("x", start_now=True)
    store.update(g["goal_id"], next_run=time.time() - 1, status=COMPLETED)
    assert store.due_goals() == []


def test_due_goals_hourly_cap_enforced(store):
    """A goal that ran less than 3600/max_runs_per_hour seconds ago should
    be excluded by the hourly cap."""
    g = store.create("x", cadence_seconds=30, max_runs_per_hour=2)
    # Simulate: last_run was 5 seconds ago (gap < 3600/2=1800s)
    now = time.time()
    store.update(g["goal_id"], next_run=now - 1, last_run=now - 5)
    assert store.due_goals() == []


def test_due_goals_no_cap_when_cadence_covers_it(store):
    """cadence × max_runs_per_hour ≥ 3600 → cap always passes."""
    # cadence=600, cap=6 → 3600 ≥ 3600 → always under cap
    g = store.create("x", cadence_seconds=600, max_runs_per_hour=6)
    now = time.time()
    store.update(g["goal_id"], next_run=now - 1, last_run=now - 1)
    due = store.due_goals()
    assert any(d["goal_id"] == g["goal_id"] for d in due)


# ── reset ─────────────────────────────────────────────────────────────────────

def test_reset_clears_all_goals(store):
    store.create("a")
    store.create("b")
    store.reset()
    assert store.list() == []
