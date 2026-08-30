"""Cross-layer SG-02-FE contract tests.

The production frontend is TypeScript, while the canonical capability registry is
Python. These tests keep the frontend projection from silently drifting from the
registry until a runtime API adapter is introduced.
"""

from pathlib import Path
import re

from spiral_grove.registry import build_ais_capability_catalog


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public_prism" / "src"
FRONTEND = SRC / "data" / "spiralGroveCatalog.ts"
PAGE = SRC / "pages" / "SpiralGrovePage.tsx"
GATEWAY = SRC / "components" / "spiral-grove" / "CrystalGateway.tsx"
ARCHIVE = ROOT / "archive" / "frontend" / "spiral_grove" / "SpiralGrovePage.placeholder.tsx"


def read_projected_ids() -> set[str]:
    text = FRONTEND.read_text(encoding="utf-8")
    return set(re.findall(r"'cap-[a-z0-9-]+'", text))


def test_frontend_projection_exists_and_is_explicitly_registry_sourced() -> None:
    text = FRONTEND.read_text(encoding="utf-8")
    assert "spiral_grove.registry.build_ais_capability_catalog()" in text
    assert "export const AIS_CAPABILITIES" in text


def test_every_registry_capability_is_present_in_frontend_projection() -> None:
    registry = build_ais_capability_catalog()
    projected_ids = {value.strip("'") for value in read_projected_ids()}
    registry_ids = {item.id for item in registry.active()}
    assert projected_ids == registry_ids


def test_frontend_projection_has_exactly_the_registry_capability_count() -> None:
    registry_ids = {item.id for item in build_ais_capability_catalog().active()}
    projected_ids = {value.strip("'") for value in read_projected_ids()}
    assert len(projected_ids) == len(registry_ids)
    assert projected_ids == registry_ids


def test_current_page_no_longer_uses_placeholder_ais_university() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "AISUniversity" not in page
    assert "AIS_CAPABILITIES" in page
    assert "LearnerCapabilityState" in page


def test_placeholder_is_archived_not_deleted() -> None:
    assert ARCHIVE.exists()
    archived = ARCHIVE.read_text(encoding="utf-8")
    assert "Archived SG-02-FE placeholder" in archived


def test_gateway_projects_the_same_domain_registry_used_by_grove() -> None:
    gateway = GATEWAY.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert "GROVE_DOMAINS" in gateway
    assert "GROVE_DOMAINS" in page
    assert "onSelectDomain" in gateway
    assert "onSelectDomain={selectDomain}" in page


def test_gateway_domains_are_the_five_ais_domains() -> None:
    text = FRONTEND.read_text(encoding="utf-8")
    for domain in (
        "digital_intelligence",
        "creative_technology",
        "systems_thinking",
        "human_development",
        "ecological_agricultural",
    ):
        assert domain in text


def test_gateway_persistence_is_exploration_only() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "arkadia.spiral-grove.domain-state.v1" in page
    assert "localStorage" in page
    assert "GroveGatewayState" in page


def test_learning_path_exercises_and_evidence_remain_downstream() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "Learning Path Engine" in page
    assert "Exercises and evidence are not generated" in page
