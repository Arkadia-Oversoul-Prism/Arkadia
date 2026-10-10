"""Tests for the source-to-runtime revision reconciliation (ADR-016).

Pure-function and fail-closed: a missing, placeholder, or invalid revision must
yield ``UNKNOWN``, never a spurious ``MATCH``. Two disagreeing valid revision
sources reported by the deployment must yield ``CONFLICT``, never ``MATCH``. An
unreadable endpoint - including an HTML body served with ``200`` - must yield
``BLOCKED``. No network is performed.
"""
import json

import pytest

from kernel.revision_identity import PLACEHOLDER_TOKENS
from scripts import version_reconciliation as vc
from scripts.version_reconciliation import (
    BLOCKED,
    CONFLICT,
    MATCH,
    MISMATCH,
    UNKNOWN,
    compare,
)

_HEAD = "ba3c7b574e704f6cc73393fa63e867ee2a9aa719"
_OTHER = "f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8"


class _FakeResponse:
    """Minimal stand-in for the object returned by ``urllib.request.urlopen``."""

    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch_body(monkeypatch, body: bytes, status: int = 200) -> None:
    monkeypatch.setattr(vc.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(body, status))


def _payload(revision, *, conflict=False, sources=None) -> bytes:
    return json.dumps(
        {
            "schema": "arkadia.version/v1",
            "source_revision": revision,
            "revision_conflict": conflict,
            "revision_sources": sources if sources is not None else {},
        }
    ).encode("utf-8")


# ── compare(): the fail-closed core ──────────────────────────────────────────

def test_compare_matches_identical_revision():
    assert compare(_HEAD, _HEAD) == MATCH


def test_compare_reports_mismatch_for_different_valid_revisions():
    assert compare(_HEAD, _OTHER) == MISMATCH


def test_compare_normalizes_case_and_whitespace_for_valid_revisions():
    assert compare(f"  {_HEAD.upper()}  ", _HEAD) == MATCH


def test_compare_is_fail_closed_on_absent_values():
    assert compare(None, _OTHER) == UNKNOWN
    assert compare(_HEAD, None) == UNKNOWN
    assert compare("unknown", _HEAD) == UNKNOWN
    assert compare(_HEAD, "unknown") == UNKNOWN
    assert compare("", "") == UNKNOWN
    assert compare("", _HEAD) == UNKNOWN


@pytest.mark.parametrize("placeholder", sorted(PLACEHOLDER_TOKENS))
def test_compare_never_matches_placeholders_even_when_both_sides_agree(placeholder):
    """The headline guarantee: identical placeholders are not a match."""
    assert compare(placeholder, placeholder) == UNKNOWN
    assert compare(placeholder.upper(), placeholder.upper()) == UNKNOWN
    assert compare(f"  {placeholder}  ", placeholder.upper()) == UNKNOWN


def test_compare_is_fail_closed_on_invalid_and_non_sha_values():
    assert compare("main", _HEAD) == UNKNOWN
    assert compare(_HEAD, "v1.2.3") == UNKNOWN
    assert compare("main", "main") == UNKNOWN
    assert compare("abc123", "abc123") == UNKNOWN
    assert compare("g" * 40, "g" * 40) == UNKNOWN
    assert compare("a" * 41, "a" * 41) == UNKNOWN


def test_compare_fails_closed_on_conflict():
    assert compare(_HEAD, _HEAD, conflict=True) == CONFLICT
    assert compare(_HEAD, _OTHER, conflict=True) == CONFLICT
    assert compare("unknown", "unknown", conflict=True) == CONFLICT


# ── fetch_reported_evidence(): evidence classification ──────────────────────

def test_fetch_reports_blocked_when_endpoint_unreadable(monkeypatch):
    def _boom(*args, **kwargs):
        raise vc.urllib.error.URLError("unreachable")

    monkeypatch.setattr(vc.urllib.request, "urlopen", _boom)
    evidence = vc.fetch_reported_evidence("https://example.invalid", 0.1)
    assert evidence["verdict_hint"] == BLOCKED
    assert evidence["revision"] is None
    assert evidence["conflict"] is False


def test_fetch_reports_blocked_for_html_body_served_with_200(monkeypatch):
    """A static host rewriting unknown paths to index.html must not read as revision evidence."""
    _patch_body(monkeypatch, b"<!doctype html><html><body>Arkadia</body></html>")

    evidence = vc.fetch_reported_evidence("https://example.invalid", 0.1)

    assert evidence["verdict_hint"] == BLOCKED
    assert evidence["revision"] is None


def test_fetch_reports_blocked_for_non_object_json(monkeypatch):
    _patch_body(monkeypatch, b"[]")
    assert vc.fetch_reported_evidence("https://example.invalid", 0.1)["verdict_hint"] == BLOCKED


def test_fetch_reports_blocked_for_non_200(monkeypatch):
    _patch_body(monkeypatch, _payload(_HEAD), status=503)
    assert vc.fetch_reported_evidence("https://example.invalid", 0.1)["verdict_hint"] == BLOCKED


def test_fetch_reads_conflict_and_sources(monkeypatch):
    _patch_body(
        monkeypatch,
        _payload(
            _HEAD,
            conflict=True,
            sources={
                "ARKADIA_SOURCE_REVISION": {"status": "revision", "value": _HEAD},
                "RENDER_GIT_COMMIT": {"status": "revision", "value": _OTHER},
            },
        ),
    )

    evidence = vc.fetch_reported_evidence("https://example.invalid", 0.1)

    assert evidence["verdict_hint"] == "OK"
    assert evidence["revision"] == _HEAD
    assert evidence["conflict"] is True


# ── invalid reported sources ────────────────────────────────────────────────

def test_invalid_reported_sources_flags_only_invalid_entries():
    sources = {
        "ARKADIA_SOURCE_REVISION": {"status": "invalid", "value": None},
        "RENDER_GIT_COMMIT": {"status": "revision", "value": _HEAD},
    }
    assert vc.invalid_reported_sources(sources) == ["ARKADIA_SOURCE_REVISION"]


def test_invalid_reported_sources_ignores_absent_and_placeholder():
    """The Dockerfile's empty default is expected, not a misconfiguration."""
    sources = {
        "ARKADIA_SOURCE_REVISION": {"status": "absent", "value": None},
        "RENDER_GIT_COMMIT": {"status": "placeholder", "value": None},
    }
    assert vc.invalid_reported_sources(sources) == []
    assert vc.invalid_reported_sources({}) == []


# ── main(): end-to-end verdict and exit codes ───────────────────────────────

def _run(monkeypatch, body, expected):
    _patch_body(monkeypatch, body)
    return vc.main(["--base-url", "https://example.invalid", "--expected", expected])


def test_main_matches_reported_revision(monkeypatch, capsys):
    assert _run(monkeypatch, _payload(_HEAD), _HEAD) == 0
    assert "verdict:          MATCH" in capsys.readouterr().out


def test_main_reports_mismatch_for_genuine_drift(monkeypatch, capsys):
    assert _run(monkeypatch, _payload(_OTHER), _HEAD) == 1
    assert "verdict:          MISMATCH" in capsys.readouterr().out


def test_main_reports_conflict_and_fails_closed(monkeypatch, capsys):
    body = _payload(
        _HEAD,
        conflict=True,
        sources={
            "ARKADIA_SOURCE_REVISION": {"status": "revision", "value": _HEAD},
            "RENDER_GIT_COMMIT": {"status": "revision", "value": _OTHER},
        },
    )

    code = _run(monkeypatch, body, _HEAD)

    output = capsys.readouterr().out
    assert code == 4
    assert "verdict:          CONFLICT" in output
    assert "revision_conflict: True" in output
    assert "verdict:          MATCH" not in output


def test_main_reports_unknown_when_reported_metadata_is_absent(monkeypatch, capsys):
    assert _run(monkeypatch, _payload("unknown"), _HEAD) == 2
    assert "verdict:          UNKNOWN" in capsys.readouterr().out


def test_main_fails_closed_when_reported_source_is_invalid(monkeypatch, capsys):
    """A valid reported revision with a misconfigured source must not read as correspondence."""
    body = _payload(
        _HEAD,
        sources={
            "ARKADIA_SOURCE_REVISION": {"status": "invalid", "value": None},
            "RENDER_GIT_COMMIT": {"status": "revision", "value": _HEAD},
        },
    )

    code = _run(monkeypatch, body, _HEAD)

    output = capsys.readouterr().out
    assert code == 2
    assert "verdict:          UNKNOWN" in output
    assert "ARKADIA_SOURCE_REVISION" in output


def test_main_reports_blocked_for_html_body(monkeypatch, capsys):
    assert _run(monkeypatch, b"<html></html>", _HEAD) == 3
    assert "verdict:          BLOCKED" in capsys.readouterr().out


def test_main_reports_unknown_for_placeholder_expected(monkeypatch, capsys):
    assert _run(monkeypatch, _payload(_HEAD), "UNKNOWN") == 2
    assert "verdict:          UNKNOWN" in capsys.readouterr().out
