import gzip
import json
from datetime import datetime, timezone

import pytest

from economic_seams.nocopo import normalize_record, parse_jsonl_gzip


NOW = datetime(2026, 10, 2, tzinfo=timezone.utc)


def test_normalizes_open_tender_with_plausible_deadline():
    item = normalize_record({
        "ocid": "ocds-gyl66f-example",
        "buyer": {"name": "Test MDA"},
        "tender": {
            "title": "Supply of solar inverters",
            "status": "active",
            "tenderPeriod": {"endDate": "2026-10-30T12:00:00Z"},
            "value": {"amount": 12000000, "currency": "NGN"},
        },
    }, now=NOW)
    assert item["active_tender_lead"] is True
    assert item["buyer"] == "Test MDA"
    assert item["tender_value"] == "12000000 NGN"
    assert item["quality_flags"] == []


def test_bad_historical_or_far_future_date_is_not_actionable():
    item = normalize_record({
        "ocid": "ocds-gyl66f-example",
        "tender": {
            "title": "Old tender",
            "status": "active",
            "tenderPeriod": {"endDate": "2919-11-25T00:00:00Z"},
        },
    }, now=NOW)
    assert item["active_tender_lead"] is False
    assert "implausible_or_out_of_window_tender_end_date" in item["quality_flags"]


def test_awarded_record_is_not_promoted_to_active_tender():
    item = normalize_record({
        "ocid": "ocds-gyl66f-awarded",
        "tender": {"title": "Past supply", "status": "complete"},
        "awards": [{"value": {"amount": 50, "currency": "NGN"}}],
    }, now=NOW)
    assert item["active_tender_lead"] is False
    assert item["award_values"] == ["50 NGN"]


def test_parses_gzip_jsonl():
    raw = b'\n'.join([
        json.dumps({"ocid": "ocds-1", "tender": {"title": "A", "status": "complete"}}).encode(),
        json.dumps({"ocid": "ocds-2", "tender": {"title": "B", "status": "complete"}}).encode(),
    ])
    assert len(parse_jsonl_gzip(gzip.compress(raw), now=NOW)) == 2


def test_rejects_malformed_jsonl():
    with pytest.raises(ValueError, match="Malformed NOCOPO JSONL"):
        parse_jsonl_gzip(gzip.compress(b"{bad json"), now=NOW)
