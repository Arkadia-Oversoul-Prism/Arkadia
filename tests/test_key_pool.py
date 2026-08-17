"""Tests for the distributed Gemini key pool and TTS round-robin selection.

These cover the load-balancing guarantees the user asked for:
  * concurrent callers spread across all configured keys (not one)
  * a quota-hit key is cooled and skipped
  * TTS keys round-robin across parallel calls
"""
import os
import sys
import importlib
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def key_pool(tmp_path, monkeypatch):
    """Fresh key_pool with an isolated data dir + empty stores."""
    monkeypatch.setenv("SOLSPIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ARKADIA_KEY_COOLDOWN", "1")
    # Point provider/key stores at the temp dir so we don't read real keys.
    (tmp_path / "provider_keys.json").write_text('{}')
    (tmp_path / "api_keys.json").write_text('{"keys": {}, "active_id": null}')
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # The sub-stores cache their file path at import time; reload them so they
    # pick up the temp data dir before key_pool re-imports them.
    for mod in ("api.provider_key_store", "api.key_manager"):
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
    if "api.key_pool" in sys.modules:
        importlib.reload(sys.modules["api.key_pool"])
    from api import key_pool
    return key_pool


def _seed(key_pool, keys):
    """Inject keys directly into the pool's cooldown map for deterministic tests."""
    # Clear the multi-provider store so it doesn't leak keys from other seeds.
    Path(os.environ["SOLSPIRE_DATA_DIR"], "provider_keys.json").write_text('{}')
    data = {"keys": {f"k{i}": {"key": k} for i, k in enumerate(keys)}, "active_id": None}
    Path(os.environ["SOLSPIRE_DATA_DIR"], "api_keys.json").write_text(
        __import__("json").dumps(data)
    )
    importlib.reload(key_pool)


def test_acquire_distributes_across_keys(key_pool):
    _seed(key_pool, ["AAA", "BBB", "CCC"])
    picks = [key_pool.acquire_key() for _ in range(9)]
    # Every configured key should be used; no single key dominates.
    assert set(picks) == {"AAA", "BBB", "CCC"}
    # Round-robin: each key appears ~3 times in 9 picks.
    counts = {k: picks.count(k) for k in ("AAA", "BBB", "CCC")}
    assert max(counts.values()) - min(counts.values()) <= 1


def test_failed_key_is_cooled_and_skipped(key_pool):
    _seed(key_pool, ["AAA", "BBB", "CCC"])
    key_pool.report_failure("AAA")
    picks = [key_pool.acquire_key() for _ in range(6)]
    assert "AAA" not in picks
    assert set(picks) == {"BBB", "CCC"}


def test_report_success_clears_cooldown(key_pool):
    _seed(key_pool, ["AAA", "BBB", "CCC"])
    key_pool.report_failure("AAA")
    assert "AAA" not in [key_pool.acquire_key() for _ in range(3)]
    key_pool.report_success("AAA")
    picks = [key_pool.acquire_key() for _ in range(6)]
    assert "AAA" in picks


def test_pool_snapshot_counts(key_pool):
    _seed(key_pool, ["AAA", "BBB", "CCC"])
    snap = key_pool.pool_snapshot()
    assert snap["size"] == 3
    assert snap["available"] == 3
    assert snap["cooled"] == []
    key_pool.report_failure("BBB")
    snap = key_pool.pool_snapshot()
    assert snap["available"] == 2
    assert len(snap["cooled"]) == 1


def test_reset_all_clears_cooldowns(key_pool):
    _seed(key_pool, ["AAA", "BBB", "CCC"])
    key_pool.report_failure("AAA")
    key_pool.report_failure("BBB")
    key_pool.reset_all()
    snap = key_pool.pool_snapshot()
    assert snap["available"] == 3
    assert snap["cooled"] == []


def test_acquire_returns_none_when_empty(key_pool):
    _seed(key_pool, [])
    assert key_pool.acquire_key() == ""


# ── TTS round-robin ──────────────────────────────────────────────────────────


@pytest.fixture
def tts_km(tmp_path, monkeypatch):
    monkeypatch.setenv("SOLSPIRE_DATA_DIR", str(tmp_path))
    if "api.tts_key_manager" in sys.modules:
        importlib.reload(sys.modules["api.tts_key_manager"])
    from api import tts_key_manager
    importlib.reload(tts_key_manager)
    return tts_key_manager


def test_tts_round_robin_distributes(tts_km):
    tts_km.add_key("el-1", "Set 1")
    tts_km.add_key("el-2", "Set 2")
    tts_km.add_key("el-3", "Set 3")
    picks = [tts_km.get_active_key() for _ in range(6)]
    assert set(picks) == {"el-1", "el-2", "el-3"}
    counts = {k: picks.count(k) for k in ("el-1", "el-2", "el-3")}
    assert max(counts.values()) - min(counts.values()) <= 1


def test_tts_skips_quota_hit(tts_km):
    tts_km.add_key("el-1", "Set 1")
    tts_km.add_key("el-2", "Set 2")
    tts_km.add_key("el-3", "Set 3")
    # Mark el-2 exhausted via rotate_key
    nxt = tts_km.rotate_key("el-2")
    assert nxt != "el-2"
    picks = [tts_km.get_active_key() for _ in range(6)]
    assert "el-2" not in picks


def test_tts_count_keys(tts_km):
    tts_km.add_key("el-1", "Set 1")
    tts_km.add_key("el-2", "Set 2")
    counts = tts_km.count_keys()
    assert counts["total"] == 2
    assert counts["available"] == 2
    assert counts["quota_hit"] == 0
