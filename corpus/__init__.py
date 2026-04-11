"""
Arkadia Corpus — Public API

Import from this module. The manager is a singleton initialized once.
"""

from .manager import CorpusManager

_manager: CorpusManager | None = None


def _get() -> CorpusManager:
    global _manager
    if _manager is None:
        _manager = CorpusManager()
    return _manager


def get_full_corpus() -> dict:
    return _get().get_full_corpus()


def refresh_corpus() -> dict:
    return _get().refresh()


def get_doc(doc_id: str) -> str:
    return _get().get_doc(doc_id)


def get_by_category(category: str) -> dict:
    return _get().get_by_category(category)


def total_chars() -> int:
    return _get().total_chars()


def sources_status() -> list[dict]:
    return _get().sources_status()
