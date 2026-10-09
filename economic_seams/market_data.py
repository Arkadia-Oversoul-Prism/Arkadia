from __future__ import annotations

"""Fail-closed market reference extraction and comparability gates."""

from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from typing import Any
from urllib.parse import urljoin, urlparse


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table = self._row = self._cell = False
        self._current_table, self._current_row, self._current_cell = [], [], []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table, self._current_table = True, []
        elif self._table and tag == "tr":
            self._row, self._current_row = True, []
        elif self._table and self._row and tag in {"td", "th"}:
            self._cell, self._current_cell = True, []

    def handle_data(self, data):
        if self._cell:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell:
            self._current_row.append(re.sub(r"\s+", " ", "".join(self._current_cell)).strip())
            self._cell = False
        elif tag == "tr" and self._row:
            if any(self._current_row):
                self._current_table.append(self._current_row)
            self._row = False
        elif tag == "table" and self._table:
            if self._current_table:
                self.tables.append(self._current_table)
            self._table = False


def parse_html_tables(html: str):
    parser = _TableParser()
    parser.feed(html or "")
    parser.close()
    return parser.tables


def _number(value: str) -> bool:
    candidate = (value or "").strip().replace(",", "").replace("₦", "").replace("$", "")
    candidate = candidate.replace("NGN", "").replace("USD", "").strip()
    return bool(re.fullmatch(r"\(?-?\d+(?:\.\d+)?\)?", candidate))


def normalize_market_tables(html: str, *, source_id: str, source_url: str):
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
            label_cells = [cell for cell in nonempty if not _number(cell)]
            if not numeric_cells or not label_cells:
                continue
            observations.append({
                "source_id": source_id, "source_url": source_url,
                "table_index": table_index, "row_index": row_index,
                "labels": label_cells, "numeric_values": numeric_cells,
                "raw_cells": nonempty, "interpretation": "UNCLASSIFIED_REFERENCE_ROW",
            })
    return observations


def parse_cbn_nfem_rows(html: str, *, source_url: str):
    """Extract only the CBN NFEM published rate, never adjacent high/low/closing columns."""
    rows = []
    for table_index, table in enumerate(parse_html_tables(html)):
        for header_index, header in enumerate(table):
            normalized = [re.sub(r"\s+", " ", cell).strip().casefold() for cell in header]
            date_columns = [i for i, value in enumerate(normalized) if value == "date"]
            rate_columns = [
                i for i, value in enumerate(normalized)
                if "nfem rate" in value and not any(term in value for term in
                    ("highest", "lowest", "closing", "average", "turnover", "deals"))
            ]
            if not date_columns or not rate_columns:
                continue
            date_column, rate_column = date_columns[0], rate_columns[0]
            for row_index, raw_cells in enumerate(table[header_index + 1:], start=header_index + 1):
                cells = [re.sub(r"\s+", " ", cell).strip() for cell in raw_cells]
                if max(date_column, rate_column) >= len(cells):
                    continue
                published_date, rate = cells[date_column], cells[rate_column]
                try:
                    parsed_date = datetime.strptime(published_date, "%B-%d-%Y").date().isoformat()
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(published_date, "%Y-%m-%d").date().isoformat()
                    except ValueError:
                        continue
                if not _number(rate):
                    continue
                rows.append({
                    "source_id": "cbn_fx",
                    "source_url": source_url,
                    "table_index": table_index,
                    "row_index": row_index,
                    "labels": [parsed_date, "NFEM Rate (₦/US$)"],
                    "numeric_values": [rate.replace(",", "").replace("₦", "").strip()],
                    "raw_cells": cells,
                    "observed_date": parsed_date,
                    "currency": "USD",
                    "unit": "₦ per US$1",
                    "quote_basis": "CBN NFEM volume-weighted average official rate",
                    "interpretation": "CBN_REFERENCE_FX_RATE",
                })
    return rows


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href, self._text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, re.sub(r"\s+", " ", "".join(self._text)).strip()))
            self._href, self._text = None, []


_NIGERIAN_STATES = {
    "ABIA", "ADAMAWA", "AKWA IBOM", "ANAMBRA", "BAUCHI", "BAYELSA", "BENUE",
    "BORNO", "CROSS RIVER", "DELTA", "EBONYI", "EDO", "EKITI", "ENUGU", "FCT",
    "GOMBE", "IMO", "JIGAWA", "KADUNA", "KANO", "KATSINA", "KEBBI", "KOGI",
    "KWARA", "LAGOS", "NASARAWA", "NIGER", "OGUN", "ONDO", "OSUN", "OYO",
    "PLATEAU", "RIVERS", "SOKOTO", "TARABA", "YOBE", "ZAMFARA",
}


def parse_afdb_rss_items(xml_text: str, *, feed_url: str):
    """Parse official AfDB RSS items; reject malformed feeds and non-AfDB item links."""
    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError as exc:
        raise ValueError("AfDB procurement RSS is not valid XML") from exc

    def local_name(tag):
        return tag.rsplit("}", 1)[-1].casefold()

    items = []
    for element in root.iter():
        if local_name(element.tag) not in {"item", "entry"}:
            continue
        fields = {}
        for child in list(element):
            key = local_name(child.tag)
            value = (child.text or "").strip()
            if key == "link" and not value:
                value = (child.attrib.get("href") or "").strip()
            if value:
                fields.setdefault(key, value)
        title = fields.get("title", "").strip()
        link = fields.get("link", "").strip()
        target = urljoin(feed_url, link) if link else ""
        parsed = urlparse(target)
        if (not title or parsed.scheme != "https" or not parsed.hostname
                or not (parsed.hostname == "afdb.org" or parsed.hostname.endswith(".afdb.org"))):
            continue
        description = fields.get("description") or fields.get("summary") or fields.get("content") or ""
        from html import unescape
        description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(description))).strip()
        items.append({
            "source_id": "afdb_procurement",
            "source_url": target,
            "title": title[:500],
            "published_at": fields.get("pubdate") or fields.get("published") or fields.get("updated"),
            "excerpt": description[:1800],
        })
    if not items:
        raise ValueError("AfDB procurement RSS contained no valid official items")
    return items


def fetch_afdb_procurement_items(session, feed_url: str, timeout: int = 25):
    response = session.get(
        feed_url, timeout=timeout,
        headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0",
                 "Accept": "application/rss+xml, application/xml, text/xml"},
    )
    response.raise_for_status()
    payload = response.content
    if len(payload) > 10 * 1024 * 1024:
        raise ValueError("AfDB procurement RSS exceeds the 10 MiB response limit")
    encoding = getattr(response, "encoding", None) or "utf-8"
    return parse_afdb_rss_items(payload.decode(encoding, errors="replace"), feed_url=feed_url)


def parse_nepc_pdf_text(text: str, *, source_url: str):
    rows, commodity = [], ""
    for line_number, raw_line in enumerate((text or "").splitlines(), start=1):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        upper = line.upper()
        if ("UNIT:" in upper or "UNIT :" in upper) and len(line) < 180:
            commodity = line
            continue
        state_match = re.match(r"^([A-Z][A-Z ]{1,24})\s+(?=₦|N/A)", upper)
        values = re.findall(r"₦\s*[\d,]+(?:\.\d{1,2})?|\bN/A\b", line, flags=re.I)
        if state_match and values:
            state = state_match.group(1).strip()
            if state in _NIGERIAN_STATES:
                rows.append({
                    "source_id": "nepc_prices", "source_url": source_url,
                    "line_number": line_number, "commodity_unit_heading": commodity,
                    "state": state,
                    "reported_values": [re.sub(r"\s+", " ", value).strip() for value in values],
                    "raw_line": line[:1200],
                    "interpretation": "INDICATIVE_LOCAL_PRICE_ROW",
                })
    return rows


def normalize_cbn_fx_row(row: dict, *, observed_date: str, quote_basis: str,
                         currency: str, unit: str = "1 USD") -> dict:
    if not all(str(x).strip() for x in (observed_date, quote_basis, currency, unit)):
        raise ValueError("CBN FX normalization requires date, quote basis, currency and unit")
    values = row.get("numeric_values") or []
    if len(values) != 1:
        raise ValueError("CBN FX normalization requires exactly one explicit numeric rate")
    return {
        "source_id": "cbn_fx", "source_url": row.get("source_url", ""),
        "observed_date": observed_date.strip(), "period": observed_date.strip(),
        "currency": currency.strip().upper(), "unit": unit.strip(), "location": "NG",
        "price": str(values[0]).strip(), "quote_basis": quote_basis.strip(),
        "interpretation": "CBN_REFERENCE_FX_RATE",
    }


def normalize_nepc_price_row(row: dict, *, period: str, unit: str,
                             quote_basis: str = "INDICATIVE_LOCAL_PRICE") -> dict:
    commodity = str(row.get("commodity_unit_heading") or "").strip()
    state = str(row.get("state") or "").strip().upper()
    values = row.get("reported_values") or []
    if not commodity or not state or not period.strip() or not unit.strip() or not values:
        raise ValueError("NEPC normalization requires commodity, geography, period, unit and price")
    if len(values) != 1:
        raise ValueError("NEPC row has multiple period columns; map the period explicitly before normalization")
    return {
        "source_id": "nepc_prices", "source_url": row.get("source_url", ""),
        "period": period.strip(), "commodity": commodity, "unit": unit.strip(),
        "location": state, "price": values[0].strip(), "currency": "NGN",
        "quote_basis": quote_basis.strip(), "interpretation": "INDICATIVE_LOCAL_PRICE",
    }


def comparable_market_observations(left: dict, right: dict) -> bool:
    """No spread calculation unless commodity, unit, geography, period and quote basis all align."""
    required = ("commodity", "unit", "location", "period", "quote_basis")
    for item in (left, right):
        if any(not str(item.get(key, "")).strip() for key in required):
            return False
    return all(str(left[key]).strip().casefold() == str(right[key]).strip().casefold()
               for key in required)


def fetch_nepc_price_rows(session, page_url: str, timeout: int = 25):
    from io import BytesIO
    from pdfminer.high_level import extract_text
    page = session.get(page_url, timeout=timeout,
                       headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
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
    response = session.get(candidates[0], timeout=timeout,
                           headers={"User-Agent": "Arkadia-Economic-Seam-Engine/1.0"})
    response.raise_for_status()
    payload = response.content
    if not payload.startswith(b"%PDF-") or len(payload) > 20 * 1024 * 1024:
        raise ValueError("NEPC price document is not a valid bounded PDF")
    rows = parse_nepc_pdf_text(extract_text(BytesIO(payload)), source_url=response.url)
    if not rows:
        raise ValueError("NEPC PDF yielded no recognizable state price rows")
    return rows
