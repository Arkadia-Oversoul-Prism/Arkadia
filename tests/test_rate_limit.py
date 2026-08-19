"""Phase 1 — rate limit unit tests (in-process, no network)."""
from __future__ import annotations

from api.rate_limit import (
    check_rate_limit,
    reset_rate_limit_state,
    load_limits,
    _match_limit,
    _is_exempt,
)


def setup_function():
    reset_rate_limit_state()


def test_allows_under_limit():
    for _ in range(5):
        ok, retry = check_rate_limit("t1", max_requests=5, window=60)
        assert ok and retry == 0


def test_blocks_over_limit():
    for _ in range(3):
        check_rate_limit("t2", max_requests=3, window=60)
    ok, retry = check_rate_limit("t2", max_requests=3, window=60)
    assert not ok
    assert retry >= 1


def test_separate_keys_independent():
    for _ in range(3):
        check_rate_limit("user-a", max_requests=3, window=60)
    ok, _ = check_rate_limit("user-b", max_requests=3, window=60)
    assert ok


def test_match_longest_prefix():
    limits = load_limits()
    m = _match_limit("/api/commune/resonance", limits)
    assert m and m[0] == "/api/commune/resonance"
    m2 = _match_limit("/api/knowledge/search", limits)
    assert m2 and m2[0] == "/api/knowledge/search"
    m3 = _match_limit("/api/knowledge/notes/xyz", limits)
    assert m3 and m3[0] == "/api/knowledge/"


def test_exempt_paths():
    assert _is_exempt("/api/knowledge/status")
    assert _is_exempt("/health")
    assert not _is_exempt("/api/commune/resonance")
