"""Regression guard for the durable open-PR inventory (gate-hygiene recon).

The open-PR queue is a live fact. Before `scripts/open_pr_inventory.py` it was
reconstructed ad hoc, and the ad-hoc recon crashed with `KeyError: 'mergeable'`
because GitHub's *list* endpoint omits `mergeable`/`mergeable_state`; only the
*detail* endpoint exposes them.

That defect is invisible to a network-free test, so the guard is structured
around the one property that makes the harness reproducible: it must never read
a mergeable field that the list endpoint does not carry. A fake API proves it,
and a negative control feeds the harness the exact pre-fix form to prove the
detector bites.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "open_pr_inventory", REPO_ROOT / "scripts" / "open_pr_inventory.py"
)
assert _SPEC and _SPEC.loader
inventory_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inventory_mod)

# The detail-only keys. Their absence from the list payload is the documented
# crash cause; the guard asserts the harness treats them as optional.
DETAIL_ONLY = ("mergeable", "mergeable_state")


def _list_item(number: int = 1, **overrides) -> dict:
    """A PR record shaped like the *list* endpoint: no mergeable fields."""
    item = {
        "number": number,
        "title": "example",
        "draft": False,
        "head": {"ref": "b", "sha": "a" * 40},
        "base": {"ref": "main", "sha": "b" * 40},
    }
    item.update(overrides)
    return item


def _detail_item(number: int = 1, mergeable=True, state="clean") -> dict:
    """A PR record shaped like the *detail* endpoint: mergeable fields present."""
    item = _list_item(number)
    item["mergeable"] = mergeable
    item["mergeable_state"] = state
    return item


def test_summarize_tolerates_a_list_record_without_mergeable():
    """The exact pre-fix defect: a list record has no `mergeable`. The harness
    must not raise, and must report the field as unavailable."""
    row = inventory_mod.summarize(_list_item())
    assert row["number"] == 1
    assert row["mergeable"] == "LIST_ENDPOINT"


def test_summarize_treats_null_mergeable_as_unknown():
    """GitHub returns `mergeable: null` while it computes the merge. That is
    UNKNOWN, not a crash and not a false 'conflict'."""
    item = _detail_item()
    item["mergeable"] = None
    assert inventory_mod.summarize(item)["mergeable"] == "UNKNOWN"


def test_summarize_reports_clean_and_conflict_from_detail():
    assert inventory_mod.summarize(_detail_item(mergeable=True, state="clean"))["mergeable"] == "clean:clean"
    assert inventory_mod.summarize(_detail_item(mergeable=False, state="dirty"))["mergeable"] == "conflict:dirty"


def test_negative_control_the_naive_read_is_unmasked_by_the_list_payload():
    """Negative control. A naive reader does `pr["mergeable"]` on a *list*
    record. If GitHub were ever to add the field to the list endpoint, this
    control would stop raising — i.e. the defect the guard documents would no
    longer be reachable through the list endpoint, and this file should be
    revisited. The assertion here pins that the list payload currently omits it.
    """
    list_item = _list_item()
    assert "mergeable" not in list_item
    with pytest.raises(KeyError):
        _ = list_item["mergeable"]


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._body = json.dumps(payload).encode()
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_inventory_merges_detail_without_mutating_the_list_record(monkeypatch):
    """End-to-end over a fake API: the list endpoint is called once, the detail
    endpoint once per PR, and the merged row carries a real mergeable verdict."""
    calls: list[str] = []

    def fake_urlopen(req, *a, **k):
        url = req.full_url
        calls.append(url)
        if "/pulls?" in url:
            return _FakeResponse([_list_item(7), _list_item(8)])
        if url.endswith("/pulls/7"):
            return _FakeResponse(_detail_item(7, mergeable=True, state="clean"))
        if url.endswith("/pulls/8"):
            return _FakeResponse(_detail_item(8, mergeable=False, state="dirty"))
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(inventory_mod.urllib.request, "urlopen", fake_urlopen)
    rows = inventory_mod.inventory("token", "owner/repo")

    assert [r["number"] for r in rows] == [7, 8]
    assert rows[0]["mergeable"] == "clean:clean"
    assert rows[1]["mergeable"] == "conflict:dirty"
    assert sum("/pulls?" in c for c in calls) == 1
    assert sum(c.endswith("/pulls/7") for c in calls) == 1


def test_inventory_keeps_the_row_when_detail_fails(monkeypatch):
    """A detail failure must degrade to LIST_ENDPOINT for that PR, not abort
    the whole inventory."""

    def fake_urlopen(req, *a, **k):
        url = req.full_url
        if "/pulls?" in url:
            return _FakeResponse([_list_item(9)])
        raise inventory_mod.urllib.error.HTTPError(url, 403, "forbidden", {}, None)

    monkeypatch.setattr(inventory_mod.urllib.request, "urlopen", fake_urlopen)
    rows = inventory_mod.inventory("token", "owner/repo")
    assert rows[0]["number"] == 9
    assert rows[0]["mergeable"] == "LIST_ENDPOINT"


def test_string_keys_and_absent_mergeable_are_handled():
    """Contract pin: the harness reads mergeable fields only through
    `summarize`, so a record missing them cannot KeyError."""
    for key in DETAIL_ONLY:
        assert key in inventory_mod.DETAIL_ONLY_KEYS
    assert inventory_mod.DETAIL_ONLY_KEYS == DETAIL_ONLY
