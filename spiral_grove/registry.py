"""In-memory capability registry for Spiral Grove Wave 02.

The registry is a domain/catalog layer. It is not an authorization system and
it is not a Knowledge OS replacement. Knowledge remains source-backed and is
resolved through existing Knowledge OS interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import Capability, CapabilityStatus


class CapabilityRegistryError(ValueError):
    """Base error for invalid capability catalog operations."""


class DuplicateCapabilityError(CapabilityRegistryError):
    """Raised when a capability ID or slug already exists."""


class UnknownCapabilityError(CapabilityRegistryError):
    """Raised when a referenced capability does not exist."""


class CapabilityCycleError(CapabilityRegistryError):
    """Raised when prerequisite traversal encounters a cycle."""


@dataclass(frozen=True)
class CapabilityGraph:
    """Read-only snapshot of registered capabilities."""

    capabilities: dict[str, Capability]

    def get(self, capability_id: str) -> Capability:
        try:
            return self.capabilities[capability_id]
        except KeyError as exc:
            raise UnknownCapabilityError(capability_id) from exc

    def prerequisites_for(self, capability_id: str) -> tuple[Capability, ...]:
        """Return transitive prerequisites in dependency-first order."""
        self.get(capability_id)
        ordered: list[Capability] = []
        visited: set[str] = set()
        active: set[str] = set()

        def visit(current_id: str) -> None:
            if current_id in active:
                raise CapabilityCycleError(current_id)
            if current_id in visited:
                return
            active.add(current_id)
            current = self.get(current_id)
            for prerequisite_id in current.prerequisites:
                visit(prerequisite_id)
                if prerequisite_id not in {item.id for item in ordered}:
                    ordered.append(self.get(prerequisite_id))
            active.remove(current_id)
            visited.add(current_id)

        visit(capability_id)
        return tuple(ordered)

    def ready_prerequisites(self, capability_id: str, demonstrated: set[str]) -> tuple[Capability, ...]:
        """Return direct prerequisites not yet demonstrated by a learner."""
        capability = self.get(capability_id)
        missing = [self.get(item) for item in capability.prerequisites if item not in demonstrated]
        return tuple(missing)


class CapabilityRegistry:
    """Mutable catalog used to build validated capability graphs."""

    def __init__(self, capabilities: list[Capability] | None = None) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._slugs: dict[str, str] = {}
        for capability in capabilities or []:
            self.register(capability)
        self._validate_references()

    def register(self, capability: Capability) -> None:
        if capability.id in self._capabilities or capability.slug in self._slugs:
            raise DuplicateCapabilityError(capability.id)
        self._capabilities[capability.id] = capability
        self._slugs[capability.slug] = capability.id
        try:
            self._validate_references()
        except Exception:
            self._capabilities.pop(capability.id, None)
            self._slugs.pop(capability.slug, None)
            raise

    def get(self, capability_id: str) -> Capability:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise UnknownCapabilityError(capability_id) from exc

    def by_slug(self, slug: str) -> Capability:
        try:
            return self.get(self._slugs[slug])
        except KeyError as exc:
            raise UnknownCapabilityError(slug) from exc

    def active(self) -> tuple[Capability, ...]:
        return tuple(item for item in self._capabilities.values() if item.status == CapabilityStatus.ACTIVE)

    def graph(self) -> CapabilityGraph:
        self._validate_references()
        return CapabilityGraph(dict(self._capabilities))

    def _validate_references(self) -> None:
        for capability in self._capabilities.values():
            for prerequisite_id in capability.prerequisites:
                if prerequisite_id not in self._capabilities:
                    raise UnknownCapabilityError(prerequisite_id)
        for capability in self._capabilities.values():
            self.graph_validate_cycle(capability.id)

    def graph_validate_cycle(self, capability_id: str) -> None:
        graph = CapabilityGraph(dict(self._capabilities))
        graph.prerequisites_for(capability_id)


def build_ais_capability_catalog() -> CapabilityRegistry:
    """Return the initial A.I.S capability catalogue."""
    capabilities = [
        Capability(
            id="cap-digital-intelligence",
            slug="digital-intelligence",
            name="Digital Intelligence",
            description="Use digital systems critically, safely, and effectively.",
            domain="digital_intelligence",
            level=1,
            outcomes=["navigate-digital-systems", "evaluate-digital-information"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-ai-prompt-engineering",
            slug="ai-prompt-engineering",
            name="AI Prompt Engineering",
            description="Design bounded prompts and evaluate AI-assisted outputs.",
            domain="digital_intelligence",
            level=2,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["write-bounded-prompts", "evaluate-ai-output"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-research-systems",
            slug="research-systems",
            name="Research Systems",
            description="Find, verify, synthesize, and communicate evidence.",
            domain="digital_intelligence",
            level=2,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["source-information", "synthesize-evidence"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-digital-operations",
            slug="digital-operations",
            name="Digital Operations",
            description="Design repeatable digital workflows and operating routines.",
            domain="digital_intelligence",
            level=3,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["design-workflows", "document-operations"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-no-code-development",
            slug="no-code-development",
            name="No-Code Development",
            description="Build useful digital prototypes without traditional programming.",
            domain="digital_intelligence",
            level=3,
            prerequisites=["cap-digital-intelligence", "cap-digital-operations"],
            outcomes=["prototype-workflows", "ship-no-code-tools"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-content-systems",
            slug="content-systems",
            name="Content Systems",
            description="Plan, produce, organize, and distribute digital content.",
            domain="digital_intelligence",
            level=2,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["plan-content", "build-content-workflows"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-ai-creative-workflows",
            slug="ai-assisted-creative-workflows",
            name="AI-Assisted Creative Workflows",
            description="Use AI within accountable creative production workflows.",
            domain="digital_intelligence",
            level=3,
            prerequisites=["cap-ai-prompt-engineering", "cap-content-systems"],
            outcomes=["direct-ai-creative-work", "review-generated-assets"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-music-production-ai",
            slug="music-production-with-ai",
            name="Music Production with AI",
            description="Create and refine music using AI-assisted production workflows.",
            domain="creative_technology",
            level=2,
            prerequisites=["cap-ai-prompt-engineering"],
            outcomes=["produce-ai-assisted-music", "iterate-audio-assets"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-audio-engineering",
            slug="audio-engineering",
            name="Audio Engineering",
            description="Record, edit, mix, and evaluate audio.",
            domain="creative_technology",
            level=2,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["edit-audio", "evaluate-audio-quality"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-creative-writing",
            slug="creative-writing",
            name="Creative Writing",
            description="Develop original written work with structure, voice, and revision.",
            domain="creative_technology",
            level=1,
            outcomes=["write-original-work", "revise-writing"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-storytelling",
            slug="storytelling-systems",
            name="Storytelling Systems",
            description="Build coherent stories across written, audio, and visual media.",
            domain="creative_technology",
            level=2,
            prerequisites=["cap-creative-writing"],
            outcomes=["structure-stories", "adapt-stories-across-media"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-media-production",
            slug="media-production",
            name="Media Production",
            description="Plan and produce publishable media projects.",
            domain="creative_technology",
            level=2,
            prerequisites=["cap-content-systems"],
            outcomes=["produce-media", "manage-production-workflows"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-visual-design",
            slug="visual-design",
            name="Visual Design",
            description="Communicate ideas through effective visual composition and design.",
            domain="creative_technology",
            level=2,
            prerequisites=["cap-digital-intelligence"],
            outcomes=["compose-visual-assets", "apply-design-principles"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-problem-solving",
            slug="problem-solving",
            name="Problem Solving",
            description="Frame problems, generate options, test assumptions, and choose actions.",
            domain="systems_thinking",
            level=1,
            outcomes=["frame-problems", "evaluate-options"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-decision-architecture",
            slug="decision-architecture",
            name="Decision Architecture",
            description="Make explicit, evidence-aware decisions under constraints.",
            domain="systems_thinking",
            level=2,
            prerequisites=["cap-problem-solving"],
            outcomes=["map-decisions", "surface-tradeoffs"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-operational-thinking",
            slug="operational-thinking",
            name="Operational Thinking",
            description="Translate goals into repeatable systems and accountable actions.",
            domain="systems_thinking",
            level=2,
            prerequisites=["cap-problem-solving"],
            outcomes=["translate-goals-to-actions", "design-operating-systems"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-workflow-design",
            slug="workflow-design",
            name="Workflow Design",
            description="Model work as clear, measurable, improvable workflows.",
            domain="systems_thinking",
            level=2,
            prerequisites=["cap-operational-thinking"],
            outcomes=["map-workflows", "improve-processes"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-pattern-recognition",
            slug="pattern-recognition",
            name="Pattern Recognition",
            description="Identify meaningful structures across observations and evidence.",
            domain="systems_thinking",
            level=2,
            prerequisites=["cap-problem-solving"],
            outcomes=["identify-patterns", "test-patterns"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-structured-reasoning",
            slug="structured-reasoning",
            name="Structured Reasoning",
            description="Build clear arguments, inspect assumptions, and reason transparently.",
            domain="systems_thinking",
            level=2,
            prerequisites=["cap-problem-solving"],
            outcomes=["construct-arguments", "inspect-assumptions"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-communication",
            slug="communication",
            name="Communication",
            description="Communicate ideas clearly across audiences and formats.",
            domain="human_development",
            level=1,
            outcomes=["communicate-clearly", "adapt-message-to-audience"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-presentation",
            slug="presentation",
            name="Presentation",
            description="Present ideas with structure, confidence, evidence, and clarity.",
            domain="human_development",
            level=2,
            prerequisites=["cap-communication"],
            outcomes=["deliver-presentations", "defend-ideas"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-confidence-building",
            slug="confidence-building",
            name="Confidence Building",
            description="Develop confidence through practice, feedback, and demonstrated capability.",
            domain="human_development",
            level=1,
            outcomes=["receive-feedback", "act-with-agency"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-identity-mapping",
            slug="identity-mapping",
            name="Identity Mapping",
            description="Identify strengths, interests, values, and directions for development.",
            domain="human_development",
            level=1,
            outcomes=["map-strengths", "articulate-direction"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-discipline-systems",
            slug="discipline-systems",
            name="Discipline Systems",
            description="Build practical routines that support sustained work and learning.",
            domain="human_development",
            level=2,
            prerequisites=["cap-confidence-building"],
            outcomes=["design-routines", "maintain-practice"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-collaborative-intelligence",
            slug="collaborative-intelligence",
            name="Collaborative Intelligence",
            description="Work productively with peers through shared reasoning and responsibility.",
            domain="human_development",
            level=2,
            prerequisites=["cap-communication"],
            outcomes=["collaborate-effectively", "peer-review-work"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-soil-systems",
            slug="soil-systems",
            name="Soil Systems",
            description="Understand soil as a living production and ecological system.",
            domain="ecological_agricultural",
            level=1,
            outcomes=["observe-soil", "manage-basic-soil-health"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-farm-operations",
            slug="farm-operations",
            name="Farm Operations",
            description="Plan and execute basic agricultural production operations.",
            domain="ecological_agricultural",
            level=2,
            prerequisites=["cap-soil-systems"],
            outcomes=["plan-farm-tasks", "track-farm-operations"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-food-systems",
            slug="food-systems",
            name="Food Systems",
            description="Understand production, movement, access, and use of food resources.",
            domain="ecological_agricultural",
            level=2,
            prerequisites=["cap-farm-operations"],
            outcomes=["map-food-systems", "identify-food-system-bottlenecks"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-water-systems",
            slug="water-systems",
            name="Water Systems",
            description="Understand basic water resources, use, conservation, and management.",
            domain="ecological_agricultural",
            level=1,
            outcomes=["map-water-use", "identify-conservation-actions"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-resource-management",
            slug="resource-management",
            name="Resource Management",
            description="Allocate scarce resources responsibly against real constraints.",
            domain="ecological_agricultural",
            level=2,
            prerequisites=["cap-problem-solving"],
            outcomes=["allocate-resources", "track-resource-use"],
            status=CapabilityStatus.ACTIVE,
        ),
        Capability(
            id="cap-sustainable-agriculture",
            slug="sustainable-agriculture",
            name="Sustainable Agriculture",
            description="Design agricultural practices balancing productivity and ecological stewardship.",
            domain="ecological_agricultural",
            level=3,
            prerequisites=["cap-soil-systems", "cap-water-systems", "cap-resource-management"],
            outcomes=["design-sustainable-practices", "evaluate-agricultural-tradeoffs"],
            status=CapabilityStatus.ACTIVE,
        ),
    ]
    return CapabilityRegistry(capabilities)
