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
