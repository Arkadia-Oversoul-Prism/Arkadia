"""Shared document text extraction for uploads.

Pulls readable text out of PDF, DOCX, TXT and Markdown files so the same
extraction logic serves both the public Spiral Codex upload and personal
Knowledge OS / SolSpire project file ingestion. Returns plain text; binary
formats that cannot be parsed fall back to a placeholder marker so the
upload still succeeds and the file is indexed.
"""
from __future__ import annotations

import io
from typing import Tuple


def extract_text(file_name: str, raw: bytes) -> Tuple[str, str]:
    """Return (extracted_text, mime_type) for an uploaded file."""
    name = (file_name or "").lower()
    if name.endswith(".md"):
        return raw.decode("utf-8", errors="ignore"), "text/markdown"
    if name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore"), "text/plain"

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw))
            text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if text:
                return text, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except Exception:
            pass
        return (f"[DOCX FILE: {file_name} - {len(raw)} bytes]\n[Install python-docx for full text extraction.]",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    if name.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
            if text:
                return text, "application/pdf"
        except Exception:
            pass
        return (f"[PDF FILE: {file_name} - {len(raw)} bytes]\n[Install PyPDF2 for full text extraction.]",
                "application/pdf")

    if name.endswith(".html") or name.endswith(".htm"):
        return raw.decode("utf-8", errors="ignore"), "text/html"

    if name.endswith(".json"):
        return raw.decode("utf-8", errors="ignore"), "application/json"

    # Last resort: try as plain text.
    return raw.decode("utf-8", errors="ignore"), "application/octet-stream"


def make_label(file_name: str) -> str:
    """Turn a filename into a human-readable scroll label."""
    base = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
    return base.replace("_", " ").replace("-", " ").strip().title() or file_name
