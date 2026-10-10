"""Regression tests for non-blocking corpus reads and coordinated refreshes."""
from __future__ import annotations

import asyncio
import time

import pytest

import api.main as corpus_api


@pytest.fixture(autouse=True)
def reset_corpus_state():
    corpus_api._cache.update(
        scrolls=None, at=0.0, attempt_at=0.0, last_error=None
    )
    corpus_api._refresh_task = None
    yield
    # asyncio.run() closes each test loop and cancels any task left pending.
    corpus_api._refresh_task = None
    corpus_api._cache.update(
        scrolls=None, at=0.0, attempt_at=0.0, last_error=None
    )


def test_cold_read_returns_local_fallback_without_waiting_for_remote(monkeypatch):
    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()

        monkeypatch.setattr(corpus_api, "_build_local_scrolls", lambda: {
            "local": {"id": "local", "chars": 4, "content": "warm"}
        })

        async def slow_tree():
            entered.set()
            await release.wait()
            return [{"path": "docs/remote.md", "type": "blob"}]

        async def build(_tree):
            return {"remote": {"id": "remote", "chars": 6, "content": "remote"}}

        monkeypatch.setattr(corpus_api, "_fetch_github_tree", slow_tree)
        monkeypatch.setattr(corpus_api, "_build_scrolls", build)
        monkeypatch.setattr(corpus_api, "_load_direct_scrolls", lambda: [])

        started = time.monotonic()
        result = await corpus_api._get_scrolls()
        elapsed = time.monotonic() - started
        assert "local" in result
        assert elapsed < 0.2

        task = corpus_api._refresh_task
        assert task is not None and not task.done()
        await entered.wait()
        release.set()
        await task
        assert "remote" in corpus_api._cache["scrolls"]

    asyncio.run(scenario())


def test_stale_read_serves_snapshot_and_schedules_only_one_refresh(monkeypatch):
    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()
        old = {"old": {"id": "old", "chars": 3, "content": "old"}}
        corpus_api._cache.update(scrolls=old, at=time.time() - corpus_api.CACHE_TTL - 1)

        async def slow_tree():
            entered.set()
            await release.wait()
            return [{"path": "docs/new.md", "type": "blob"}]

        async def build(_tree):
            return {"new": {"id": "new", "chars": 3, "content": "new"}}

        monkeypatch.setattr(corpus_api, "_fetch_github_tree", slow_tree)
        monkeypatch.setattr(corpus_api, "_build_scrolls", build)
        monkeypatch.setattr(corpus_api, "_load_direct_scrolls", lambda: [])

        first = await corpus_api._get_scrolls()
        task = corpus_api._refresh_task
        second = await corpus_api._get_scrolls()
        assert "old" in first and "old" in second
        assert corpus_api._refresh_task is task
        await entered.wait()
        release.set()
        await task
        assert "new" in corpus_api._cache["scrolls"]

    asyncio.run(scenario())


def test_build_scrolls_uses_bounded_parallel_fetches(monkeypatch):
    async def scenario():
        active = 0
        peak = 0

        async def fake_fetch(path):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.005)
            active -= 1
            return path, None

        monkeypatch.setattr(corpus_api, "_fetch_raw", fake_fetch)
        monkeypatch.setattr(corpus_api, "_infer_category", lambda _path: ("TEST", 1))
        monkeypatch.setattr(corpus_api, "_is_readable", lambda _path: True)
        monkeypatch.setattr(corpus_api, "_make_label", lambda path: path)

        tree = [{"path": f"docs/item-{i}.md", "type": "blob"} for i in range(24)]
        result = await corpus_api._build_scrolls(tree)
        assert len(result) == 24
        assert 1 < peak <= 8

    asyncio.run(scenario())


def test_failed_refresh_preserves_last_good_snapshot(monkeypatch):
    async def scenario():
        old = {"good": {"id": "good", "chars": 4, "content": "good"}}
        corpus_api._cache.update(scrolls=old, at=time.time() - 1000)

        async def fail_tree():
            raise TimeoutError("simulated GitHub timeout")

        monkeypatch.setattr(corpus_api, "_fetch_github_tree", fail_tree)
        result = await corpus_api._refresh_scrolls()
        assert result == old
        assert corpus_api._cache["scrolls"] == old
        assert "TimeoutError" in corpus_api._cache["last_error"]

    asyncio.run(scenario())
