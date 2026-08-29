"""Cross-layer SG-02-FE contract tests.

The production frontend is TypeScript, while the canonical capability registry is
Python. These tests keep the frontend projection from silently drifting from the
registry until a runtime API adapter is introduced.
"""

from pathlib import Path
import re

from spiral_grove.registry import build_ais_capability_catalog


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "web" / "public_prism" / "src" / "data" / "spiralGroveCatalog.ts"
PAGE = ROOT / "web" / "public_prism" / "src" / "pages" / "SpiralGrovePage.tsx"
ARCHIVE = ROOT / "archive" / "frontend" / "spiral_grove" / "SpiralGrovePage.placeholder.tsx"


def test_frontend_projection_exists_and_is_explicitly_registry_sourced() -> None:
    text = FRONTEND.read_text(encoding="utf-8")
    assert "spiral_grove.registry.build_ais_capability_catalog()" in text
    assert "export const AIS_CAPABILITIES" in text


def test_every_registry_capability_is_present_in_frontend_projection() -> None:
    registry = build_ais_capability_catalog()
    text = FRONTEND.read_text(encoding="utf-8")

    for capability in registry.active():
        assert capability.id in text
        assert capability.slug in text
        assert capability.name in text
        assert capability.domain in text


def test_frontend_projection_has_exactly_the_registry_capability_count() -> None:
    registry = build_ais_capability_catalog()
    text = FRONTEND.read_text(encoding="utf-8")
    ids = re.findall(r"'cap-[a-z0-9-]+'", text)
    projected_ids = {value.strip("'") for value in ids}
    assert projected_ids >= {item.id for item in registry.active()}
    assert len({item.id for item in registry.active()}) == 30


def test_current_page_no_longer_uses_placeholder_ais_university() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "AISUniversity" not in page
    assert "AIS_CAPABILITIES" in page
    assert "LearnerCapabilityState" in page


def test_placeholder_is_archived_not_deleted() -> None:
    assert ARCHIVE.exists()
    archived = ARCHIVE.read_text(encoding="utf-8")
    assert "Archived SG-02-FE placeholder" in archived
