"""Fail-closed contracts for the read-only PR batch reconciliation packet."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pr_batch_reconcile", ROOT / "scripts" / "pr_batch_reconcile.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_dependency_parser_only_records_explicit_known_pr_dependencies():
    pr = {"number": 8, "title": "cleanup", "body": "Depends on #3; after PR #5"}
    assert mod._dependencies(pr, {3, 5, 8, 12}) == [3, 5]
    assert mod._dependencies({"number": 8, "body": "see #12"}, {12, 8}) == []


def test_check_runs_envelope_is_paginated_and_pending_fails_closed(monkeypatch):
    calls = []

    def fake_get(token, url):
        calls.append(url)
        if "page=1" in url:
            return 200, {"total_count": 2, "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "in_progress", "conclusion": None},
            ]}
        return 200, {"total_count": 2, "check_runs": []}

    monkeypatch.setattr(mod, "_get", fake_get)
    result = mod._checks("token", "https://api.test", "owner/repo", "abc")
    assert result["count"] == 2
    assert result["all_success"] is False
    assert result["unknown_or_non_success"] == ["IN_PROGRESS"]
    assert len(calls) == 1  # short page terminates; no phantom second page


def test_check_runs_empty_is_not_a_pass(monkeypatch):
    monkeypatch.setattr(mod, "_get", lambda *args: (200, {"total_count": 0, "check_runs": []}))
    result = mod._checks("token", "https://api.test", "owner/repo", "abc")
    assert result["count"] == 0
    assert result["all_success"] is False


def test_inventory_pagination_failure_is_fatal_and_incomplete(monkeypatch):
    monkeypatch.setattr(mod, "_get", lambda *args: (502, {"message": "upstream"}))
    try:
        mod.inventory("token", "owner/repo", "https://api.test")
    except mod.EvidenceError as exc:
        assert "page 1" in str(exc)
    else:
        raise AssertionError("partial inventory must not be emitted as complete")


def test_merge_authority_is_never_granted_by_packet_schema():
    # The public packet has an explicit no-mutation/no-authorization contract.
    source = (ROOT / "scripts" / "pr_batch_reconcile.py").read_text()
    assert '"ready_for_merge_authorized": False' in source
    assert '"merge_or_mutation_performed": False' in source
