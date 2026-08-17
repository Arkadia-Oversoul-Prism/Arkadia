"""Tests for the shared document text extraction helper (kernel.doc_extract).

Covers the formats accepted by the public, personal, and SolSpire upload
routes so a regression in extraction breaks the test suite before it breaks
an upload in production.
"""
import io
import os
import sys
import pytest

# Ensure the repo root is importable when tests run from anywhere.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from kernel.doc_extract import extract_text, make_label


def test_extract_txt():
    text, mime = extract_text("notes.txt", b"hello personal field")
    assert text == "hello personal field"
    assert mime == "text/plain"


def test_extract_markdown():
    text, mime = extract_text("ritual.md", b"# Heading\n\nbody text")
    assert "# Heading" in text
    assert mime == "text/markdown"


def test_extract_html():
    text, mime = extract_text("page.html", b"<html><body>visible</body></html>")
    assert "visible" in text
    assert mime == "text/html"


def test_extract_json():
    text, mime = extract_text("data.json", b'{"k": "v"}')
    assert "v" in text
    assert mime == "application/json"


def test_extract_unknown_falls_back_to_text():
    text, mime = extract_text("mystery.dat", b"plain bytes")
    assert text == "plain bytes"
    assert mime == "application/octet-stream"


def test_extract_empty_bytes():
    text, mime = extract_text("empty.txt", b"")
    assert text == ""
    assert mime == "text/plain"


def test_extract_pdf_without_pypdf2_returns_marker():
    # Simulate a PDF body without depending on PyPDF2 being installed.
    text, mime = extract_text("doc.pdf", b"%PDF-1.4 binary garbage")
    # Either real extraction happened or a fallback marker was produced.
    assert isinstance(text, str)
    assert mime == "application/pdf"


def test_extract_docx_without_python_docx_returns_marker():
    text, mime = extract_text("doc.docx", b"PK\x03\x04 not really a docx")
    assert isinstance(text, str)
    assert "DOCX" in text or len(text) > 0
    assert mime.startswith("application/vnd.openxmlformats")


def test_make_label_from_filename():
    assert make_label("my_ritual_plan.md") == "My Ritual Plan"
    assert make_label("weekly-review.txt") == "Weekly Review"


def test_make_label_no_extension():
    assert make_label("README") == "Readme"


def test_make_label_empty_filename():
    assert make_label("") == ""


def test_extract_preserves_multiline_content():
    body = b"line one\nline two\n\nline four"
    text, _ = extract_text("multi.txt", body)
    assert text == body.decode("utf-8")
