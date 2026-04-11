"""
Arkadia Corpus — Base Source Interface

Every corpus source (GitHub, Google Drive, Joplin, Obsidian, etc.)
implements this interface. The manager aggregates them all.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CorpusDoc:
    """
    A single document in the living corpus.
    """
    id: str                          # Unique ID (e.g. "docs/DOC1_MASTER_WEIGHTS.md")
    source: str                      # Source name ("github", "gdrive", "joplin", "obsidian")
    label: str                       # Human-readable label
    description: str = ""            # Short description
    category: str = "UNCATEGORIZED"  # Category for grouping
    priority: int = 3                # 1=always inject, 2=high, 3=semantic match
    content: str = ""
    fetched_at: Optional[str] = None
    error: Optional[str] = None
    meta: dict = field(default_factory=dict)  # Source-specific metadata

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "label": self.label,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "content": self.content,
            "chars": len(self.content),
            "preview": self.content[:320].strip() if self.content else "",
            "fetched_at": self.fetched_at,
            "error": self.error,
        }


class BaseCorpusSource(ABC):
    """
    Abstract corpus source. Implement `discover` and `fetch_content`.
    """
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if this source has the required config/credentials."""
        ...

    @abstractmethod
    def discover(self) -> list[CorpusDoc]:
        """
        Discover all documents available from this source.
        Returns list of CorpusDoc with metadata but NOT content (content="" ).
        Content is fetched separately by the manager.
        """
        ...

    @abstractmethod
    def fetch_content(self, doc: CorpusDoc) -> str:
        """
        Fetch full content for a single document. Returns text.
        Raises on error so the manager can catch and mark doc.error.
        """
        ...

    def now_iso(self) -> str:
        return datetime.now().isoformat()
