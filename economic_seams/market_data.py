from __future__ import annotations

"""Fail-closed table extraction for public market reference pages.

Extracted rows are observations only. They are not live executable quotes.
"""
from html.parser import HTMLParser
import re
from typing import Any


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table = False
        self._row = False
        self._cell = False
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table = True
            self._current_table = []
        elif self._table and tag == "tr":
            self._row = True
            self._current_row = []
        elif self._table and self._row and tag in {"td", "th"}:
            self._cell = True
            self._current_cell = []

    def handle_data(self, data):
        if self._cell:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell:
            value = re.sub(r"\s+", " ", "".join(self._current_cell)).strip()
            self._current_row.append(value)
            self._cell = False
        elif tag == "tr" and self._row:
            if any(self._current_row):
                self._current_table.append(self._current_row)
            self._row = False
        elif tag == "table" and self._table:
            if self._current_table:
                self.tables.append(self._current_table)
            self._table = False


def parse_html_tables(html: str) -> list[list[list[str]]]:
    parser = _TableParser()
    parser.feed(html or "")
    parser.close()
    return parser.tables


def _number(value: str) -> bool:
    candidate = (value or "").strip().replace(",", "").replace("₦", "").replace("$", "")
    candidate = candidate.replace("NGN", "").replace("USD", "").strip()
    return bool(re.fullmatch(r"\(?-?\d+(?:\.\d+)?\)?", candidate))


def normalize_market_tables(html: str, *, source_id: str, source_url: str) -> list[dict[str, Any]]:
    """Return conservative raw table observations for CBN FX or NEPC prices."""
    if source_id not in {"cbn_fx", "nepc_prices"}:
        raise ValueError("unsupported structured market source")
    observations = []
    for table_index, table in enumerate(parse_html_tables(html)):
        for row_index, row in enumerate(table):
            cells = [re.sub(r"\s+", " ", cell).strip() for cell in row]
            nonempty = [cell for cell in cells if cell]
            if len(nonempty) < 2:
                continue
            numeric_cells = [cell for cell in nonempty if _number(cell)]
            if not numeric_cells:
                continue
            label_cells = [cell for cell in nonempty if not _number(cell)]
            if not label_cells:
                continue
            # Keep rows raw and transparent; downstream logic must interpret units,
            # dates and quote conventions rather than guessing from column position.
            observations.append({
                "source_id": source_id,
                "source_url": source_url,
                "table_index": table_index,
                "row_index": row_index,
                "labels": label_cells,
                "numeric_values": numeric_cells,
                "raw_cells": nonempty,
                "interpretation": "UNCLASSIFIED_REFERENCE_ROW",
            })
    return observations


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, re.sub(r"\\s+", " ", "".join(self._text)).strip()))
            self._href = None
            self._text = []


_NIGERIAN_STATES = {
    "ABIA", "ADAMAWA", "AKWA IBOM", "ANAMBRA", "BAUCHI", "BAYELSA", "BENUE",
    "BORNO", "CROSS RIVER", "DELTA", "EBONYI", "EDO", "EKITI", "ENUGU", "FCT",
    "GOMBE", "IMO", "JIGAWA", "KADUNA", "KANO", "KATSINA", "KEBBI", "KOGI",
    "KWARA", "LAGOS", "NASARAWA", "NIGER", "OGUN", "ONDO", "OSUN", "OYO",
    "PLATEAU", "RIVERS", "SOKOTO", "TARABA", "YOBE", "ZAMFARA",
}


def parse_nepc_pdf_text(text: str, *, source_url: str) -> list[dict[str, Any]]:
    """Extract auditable state/commodity price lines without guessing columns."""
    rows = []
    commodity = ""
    for line_number, raw_line in enumerate((text or "").splitlines(), start=1):
        line = re.sub(r"\\s+", " ", raw_line).strip()
        if not line:
            continue
        upper = line.upper()
        if ("UNIT:" in upper or "UNIT :" in upper) and len(line) < 180:
            commodity = line
            continue
        if upper in _NIGERIAN_STATES and not re.search(r"₦|\\d", line):
            continue
        state_match = re.match(r"^([A-Z][A-Z ]{1,24})\\s+(?=₦|N/A)", upper)
        values = re.findall(r"₦\\s*[\\d,]+(?:\\.\\d{1,2})?|\\bN/A\\b", line, flags=re.I)
        if state_match and values:
            state = state_match.group(1).strip()
            if state in _NIGERIAN_STATES and not state.startswith("%"):
                rows.append({
                    "source_id": "nepc_prices",
                    "source_url": source_url,
                    "line_number": line_number,
                    "commodity_unit_heading": commodity,
                    "state": state,
                    "reported_values": [re.sub(r"\\s+", " ", value).strip() for value in values],
                    "raw_line": line[:1200],
                    "interpretation": "INDICATIVE_LOCAL_PRICE_ROW",
                })
    return rows


def fetch_nepc_price_rows(session, page_url: str, timeout: int = 25) -> list[dict[str, Any]]:
    """Resolve the latest official NEPC local-price PDF and extract its text."""
    from io import BytesIO
    from urllib.parse import urljoin, urlparse
    from pdfminer.high_level import extract_text

    page = session.get(page_url, timeout=timeout, headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
    page.raise_for_status()
    parser = _LinkParser()
    parser.feed(page.text)
    parser.close()
    candidates = []
    for href, label in parser.links:
        target = urljoin(page.url, href or "")
        parsed = urlparse(target)
        if (parsed.scheme == "https" and parsed.hostname == "nepc.gov.ng"
                and parsed.path.lower().endswith(".pdf")
                and "local commodity price" in label.lower()):
            candidates.append(target)
    if not candidates:
        raise ValueError("No official NEPC local commodity price PDF link found")
    # Page order is newest first. Do not invent a date from the URL.
    pdf_url = candidates[0]
    response = session.get(pdf_url, timeout=timeout, headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
    response.raise_for_status()
    payload = response.content
    if not payload.startswith(b"%PDF-") or len(payload) > 20 * 1024 * 1024:
        raise ValueError("NEPC price document is not a valid bounded PDF")
    extracted = extract_text(BytesIO(payload))
    rows = parse_nepc_pdf_text(extracted, source_url=response.url)
    if not rows:
        raise ValueError("NEPC PDF yielded no recognizable state price rows")
    return rows
