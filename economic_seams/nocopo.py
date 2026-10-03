from __future__ import annotations

"""NOCOPO/BPP OCDS bulk-data adapter.

The feed is a periodically refreshed snapshot, not a real-time tender API.
Malformed records and implausible dates are retained as diagnostics, never
silently converted into actionable opportunities.
"""
from datetime import datetime, timedelta, timezone
import gzip
import json
import os
from typing import Any
from urllib.parse import urlparse

import requests

DEFAULT_URL = "https://data.open-contracting.org/en/publication/64/download?name=2026.jsonl.gz"
SOURCE_ID = "nocopo"
MAX_COMPRESSED_BYTES = 20 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_RECORDS = 100_000
MAX_FUTURE_DAYS = 365


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(value.get("name") or value.get("id") or "")
    if isinstance(value, list):
        return "; ".join(filter(None, (_text(item) for item in value)))
    return str(value).strip()


def _amount(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    amount = value.get("amount")
    currency = _text(value.get("currency"))
    if amount is None:
        return ""
    return f"{amount} {currency}".strip()


def normalize_record(record: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Normalize one OCDS compiled release without inferring missing facts."""
    now = now or datetime.now(timezone.utc)
    tender = record.get("tender") if isinstance(record.get("tender"), dict) else {}
    buyer = record.get("buyer") if isinstance(record.get("buyer"), dict) else {}
    planning = record.get("planning") if isinstance(record.get("planning"), dict) else {}
    contracts = record.get("contracts") if isinstance(record.get("contracts"), list) else []
    awards = record.get("awards") if isinstance(record.get("awards"), list) else []
    title = _text(tender.get("title") or planning.get("rationale") or record.get("title"))
    tender_status = _text(tender.get("status")).lower()
    end_date = _text(tender.get("tenderPeriod", {}).get("endDate") if isinstance(tender.get("tenderPeriod"), dict) else "")
    parsed_end = None
    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if parsed_end.tzinfo is None:
                parsed_end = parsed_end.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            parsed_end = None
    plausible_future_deadline = bool(
        parsed_end and now < parsed_end <= now + timedelta(days=MAX_FUTURE_DAYS)
    )
    active = tender_status in {"active", "planned"} and plausible_future_deadline
    award_values = [_amount(a.get("value")) for a in awards if isinstance(a, dict)]
    contract_values = [_amount(c.get("value")) for c in contracts if isinstance(c, dict)]
    return {
        "ocid": _text(record.get("ocid")),
        "title": title,
        "buyer": _text(buyer),
        "tender_status": tender_status,
        "tender_end_date": end_date,
        "tender_value": _amount(tender.get("value")),
        "award_values": [v for v in award_values if v],
        "contract_values": [v for v in contract_values if v],
        "active_tender_lead": active and bool(title) and bool(_text(record.get("ocid"))),
        "source_url": DEFAULT_URL,
        "source_snapshot": "2026 OCDS bulk snapshot; registry refresh cadence is not guaranteed",
        "quality_flags": [
            flag for flag, condition in (
                ("missing_ocid", not _text(record.get("ocid"))),
                ("missing_tender_title", not title),
                ("missing_tender_end_date", not bool(end_date)),
                ("unparseable_tender_end_date", bool(end_date) and parsed_end is None),
                ("implausible_or_out_of_window_tender_end_date", bool(parsed_end) and not plausible_future_deadline),
            ) if condition
        ],
    }


def parse_jsonl_gzip(payload: bytes, *, now: datetime | None = None) -> list[dict[str, Any]]:
    if not isinstance(payload, (bytes, bytearray)) or len(payload) > MAX_COMPRESSED_BYTES:
        raise ValueError("NOCOPO compressed payload is invalid or exceeds the size limit")
    try:
        decoded = gzip.decompress(payload)
    except (OSError, EOFError) as exc:
        raise ValueError("NOCOPO payload is not a valid gzip stream") from exc
    if len(decoded) > MAX_DECOMPRESSED_BYTES:
        raise ValueError("NOCOPO decompressed payload exceeds the size limit")
    records = []
    for line_number, line in enumerate(decoded.splitlines(), start=1):
        if not line.strip():
            continue
        if len(records) >= MAX_RECORDS:
            raise ValueError("NOCOPO record limit exceeded")
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed NOCOPO JSONL at line {line_number}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"NOCOPO record at line {line_number} is not an object")
        records.append(normalize_record(item, now=now))
    return records


def fetch_records(session=requests, url: str | None = None, timeout: int = 30) -> list[dict[str, Any]]:
    """Fetch configured OCDS snapshot with bounded response size and strict host."""
    target = url or os.environ.get("NOCOPO_OCDS_URL", DEFAULT_URL)
    parsed = urlparse(target)
    if parsed.scheme != "https" or parsed.hostname not in {
        "data.open-contracting.org", "fastly.data.open-contracting.org"
    }:
        raise ValueError("NOCOPO_OCDS_URL must use an approved HTTPS data host")
    response = session.get(
        target, timeout=timeout,
        headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0", "Accept": "application/gzip"},
        stream=True,
    )
    response.raise_for_status()
    chunks = []
    size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_COMPRESSED_BYTES:
            raise ValueError("NOCOPO download exceeds the compressed size limit")
        chunks.append(chunk)
    return parse_jsonl_gzip(b"".join(chunks))
