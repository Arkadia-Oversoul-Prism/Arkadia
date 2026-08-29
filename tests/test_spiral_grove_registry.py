"""Wave 02 registry tests."""

import pytest

from spiral_grove.models import Capability, CapabilityStatus
from spiral_grove.registry import (
    CapabilityCycleError,
    CapabilityRegistry,
    DuplicateCapabilityError,
    UnknownCapabilityError,
    build_ais_capability_catalog,
)


def capability(capability_id: str, *, prerequisites: list[str] | None = None) -> Capability:
    return Capability(
        id=capability_id,
        slug=capability_id,
        name=capability_id,
        description=f"{capability_id} capability",
        domain="test",
        level=1,
        prerequisites=prerequisites or [],
        status=CapabilityStatus.ACTIVE,
    )


def test_registry_rejects_duplicate_id() -> None:
    registry = CapabilityRegistry([capability("cap-a")])
    with pytest.raises(DuplicateCapabilityError):
        registry.register(capability("cap-a"))


def test_registry_rejects_duplicate_slug() -> None:
    first = capability("cap-a")
    second = Capability(
        id="cap-b",
        slug="cap-a",
        name="cap-b",
        description="cap-b capability",
        domain="test",
        level=1,
    )
    with pytest.raises(DuplicateCapabilityError):
        CapabilityRegistry([first, second])


def test_registry_rejects_unknown_prerequisite() -> None:
    with pytest.raises(UnknownCapabilityError):
        CapabilityRegistry([capability("cap-b", prerequisites=["cap-missing"])])


def test_prerequisites_are_resolved_dependency_first() -> None:
    registry = CapabilityRegistry(
        [
            capability("cap-a"),
            capability("cap-b", prerequisites=["cap-a"]),
            capability("cap-c", prerequisites=["cap-b"]),
        ]
    )

    result = registry.graph().prerequisites_for("cap-c")
    assert [item.id for item in result] == ["cap-a", "cap-b"]


def test_registry_rejects_prerequisite_cycle() -> None:
    with pytest.raises(CapabilityCycleError):
        CapabilityRegistry(
            [
                capability("cap-a", prerequisites=["cap-b"]),
                capability("cap-b", prerequisites=["cap-a"]),
            ]
        )


def test_ready_prerequisites_returns_only_missing_direct_dependencies() -> None:
    registry = CapabilityRegistry(
        [
            capability("cap-a"),
            capability("cap-b"),
            capability("cap-c", prerequisites=["cap-a", "cap-b"]),
        ]
    )

    missing = registry.graph().ready_prerequisites("cap-c", {"cap-a"})
    assert [item.id for item in missing] == ["cap-b"]


def test_ais_catalog_contains_all_five_learning_domains() -> None:
    registry = build_ais_capability_catalog()
    domains = {item.domain for item in registry.active()}
    assert domains == {
        "digital_intelligence",
        "creative_technology",
        "systems_thinking",
        "human_development",
        "ecological_agricultural",
    }


def test_ais_catalog_resolves_no_missing_prerequisites_or_cycles() -> None:
    registry = build_ais_capability_catalog()
    graph = registry.graph()

    for item in registry.active():
        graph.prerequisites_for(item.id)


def test_ais_catalog_has_ai_prompt_engineering_dependency() -> None:
    registry = build_ais_capability_catalog()
    capability = registry.by_slug("ai-prompt-engineering")

    assert capability.prerequisites == ["cap-digital-intelligence"]


def test_ais_catalog_supports_progressive_creative_workflow() -> None:
    registry = build_ais_capability_catalog()
    prerequisites = registry.graph().prerequisites_for("cap-ai-creative-workflows")

    assert [item.id for item in prerequisites] == [
        "cap-ai-prompt-engineering",
        "cap-digital-intelligence",
        "cap-content-systems",
    ]
