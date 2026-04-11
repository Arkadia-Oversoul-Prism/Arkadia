"""
Arkadia — github_corpus.py (backward-compatibility shim)

This module previously held the hardcoded corpus.
The corpus is now dynamically managed by the `corpus` package.
This file delegates to it so any existing imports keep working.
"""

from corpus import (
    get_full_corpus,
    refresh_corpus,
    get_doc,
    get_by_category,
    total_chars,
    sources_status,
)

__all__ = [
    "get_full_corpus",
    "refresh_corpus",
    "get_doc",
    "get_by_category",
    "total_chars",
    "sources_status",
]
