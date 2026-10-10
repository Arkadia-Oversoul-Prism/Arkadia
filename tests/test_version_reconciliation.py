"""Tests for the source-to-runtime revision reconciliation (ADR-016).

Pure-function and fail-closed: a missing or placeholder revision must yield
``UNKNOWN``, never a spurious ``MATCH``. An unreadable endpoint must yield
``BLOCKED``. No network is performed.
"""
import urllib.error

from scripts.version_reconciliation import BLOCKED, MATCH, MISMATCH, UNKNOWN, compare
from scripts import version_reconciliation as vc


def test_compare_matches_identical_revision():
    assert compare("f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8", "f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8") == MATCH


def test_compare_reports_mismatch_for_different_revisions():
    assert compare("aaaaaaa", "bbbbbbb") == MISMATCH


def test_compare_is_fail_closed_on_absent_values():
    assert compare(None, "bbbbbbb") == UNKNOWN
    assert compare("aaaaaaa", None) == UNKNOWN
    assert compare("unknown", "aaaaaaa") == UNKNOWN
    assert compare("aaaaaaa", "unknown") == UNKNOWN
    assert compare("", "") == UNKNOWN


def test_fetch_reports_blocked_when_endpoint_unreadable(monkeypatch):
    def _boom(*args, **kwargs):
        raise urllib.error.URLError("unreachable")

    monkeypatch.setattr(vc.urllib.request, "urlopen", _boom)
    hint, revision = vc.fetch_reported_revision("https://example.invalid", 0.1)
    assert hint == BLOCKED
    assert revision is None
