"""Lane 2 — NovaNet public-field engagement readings (reactions / comments /
reposts).

The public transmissions feed (`GET /api/transmissions`, `api/transmissions.py`)
returns four reaction counters (``heart`` / ``fire`` / ``star`` / ``mind``), a
``reposts`` count and a ``comments`` array on every post, and the archived Prism
field card rendered exactly those readings. The console rendered none of them,
so engagement a reader could already fetch was invisible.

These are **source-level** assertions against the active console, matching the
established convention for console contract guards
(`tests/test_prism_novanet_author_controls.py`,
`tests/test_prism_opportunity_entry_flow.py`).

The invariant is **read-only fidelity**: the surface mirrors the backend's
declared shape and invents no value, and it introduces no mutation it cannot
prove. Each behavioural claim carries a **negative control** — a synthetic
source that violates it must be reported by the same detector that judges the
live tree, so the guard cannot be disarmed by rewriting the component.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
PAGE = CONSOLE / "pages" / "NovaNetPage.tsx"
ENGAGEMENT = CONSOLE / "components" / "novaNet" / "EngagementBar.tsx"
BACKEND = ROOT / "api" / "transmissions.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The shape the surface mirrors is the one the backend declares
# ---------------------------------------------------------------------------


def test_backend_declares_the_engagement_shape_it_serves():
    """The readings are only legitimate because the feed carries them."""
    src = _read(BACKEND)
    assert '"reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0}' in src
    assert '"comments": [], "reposts": 0' in src
    assert 'valid = {"heart", "fire", "star", "mind"}' in src


def test_engagement_component_exists_and_is_display_only():
    assert ENGAGEMENT.is_file(), "the NovaNet engagement component is missing"
    src = _read(ENGAGEMENT)
    assert "export function EngagementBar" in src
    assert 'data-testid="novanet-engagement"' in src
    # A reading surface must not mutate: no request moves from this component.
    assert "apiRequest" not in src, "the engagement surface must be read-only"
    assert not re.search(r"\bmethod\s*:", src), "no HTTP method belongs on a reading surface"


def test_reaction_vocabulary_is_the_backends_own():
    """The four keys and their order come from the backend, not a local guess."""
    src = _read(ENGAGEMENT)
    assert re.search(
        r'REACTION_TYPES\s*=\s*\[\s*"heart"\s*,\s*"fire"\s*,\s*"star"\s*,\s*"mind"\s*\]',
        src,
    ), "the reaction vocabulary must be the backend's four declared keys, in order"
    for key in ("heart", "fire", "star", "mind"):
        assert f'data-testid={{`novanet-reaction-${{type}}`}}' in src or key in src


def test_no_invented_counts():
    """A count the server did not return reads the server's own zero."""
    src = _read(ENGAGEMENT)
    assert "reactions?.[type] ?? 0" in src, "a missing reaction count must read 0, not be invented"
    assert "typeof transmission.reposts" in src, "reposts must be the server value when present"


def test_page_mounts_the_engagement_surface_read_only():
    """The page renders the readings and adds no write path for them."""
    src = _read(PAGE)
    assert "EngagementBar" in src, "the NovaNet field must render the declared readings"
    assert "<EngagementBar transmission={t} />" in src, "the readings must render per transmission"


# ---------------------------------------------------------------------------
# Detectors — the same predicate applied to the live tree and to a defect
# ---------------------------------------------------------------------------

_REACTION_VOCAB = re.compile(
    r'REACTION_TYPES\s*=\s*\[\s*"heart"\s*,\s*"fire"\s*,\s*"star"\s*,\s*"mind"\s*\]'
)
_ZERO_FALLBACK = re.compile(r"reactions\?\.\[type\]\s*\?\?\s*0")


def _mutation_defect(source: str) -> bool:
    """True when a reading surface carries a request/method it cannot prove."""
    return "export function EngagementBar" in source and (
        "apiRequest" in source or re.search(r"\bmethod\s*:", source) is not None
    )


def _invented_count_defect(source: str) -> bool:
    """True when the surface fabricates a count instead of defaulting to zero."""
    return "export function EngagementBar" in source and not _ZERO_FALLBACK.search(source)


def _vocabulary_defect(source: str) -> bool:
    """True when the reaction vocabulary diverges from the backend's four keys."""
    return "export function EngagementBar" in source and not _REACTION_VOCAB.search(source)


def _unmounted_defect(source: str) -> bool:
    """True when the NovaNet field no longer renders the declared readings."""
    return "SurfaceLenses" in source and "EngagementBar" not in source


def test_detectors_are_silent_on_the_live_tree():
    assert not _mutation_defect(_read(ENGAGEMENT))
    assert not _invented_count_defect(_read(ENGAGEMENT))
    assert not _vocabulary_defect(_read(ENGAGEMENT))
    assert not _unmounted_defect(_read(PAGE))


def test_detector_flags_a_mutating_reading_surface():
    """Negative control: a reading bar that fires a request."""
    defect = (
        "export function EngagementBar({ transmission }) {\n"
        '  return <button onClick={() => apiRequest("/api/transmissions/x/react", { method: "POST" })}>♥</button>;\n'
        "}\n"
    )
    assert _mutation_defect(defect), "the read-only detector missed a mutating surface"


def test_detector_flags_an_invented_count():
    """Negative control: a bar that fabricates engagement."""
    defect = (
        "export function EngagementBar({ transmission }) {\n"
        "  return <span>{transmission.resonance || 7}</span>;\n"
        "}\n"
    )
    assert _invented_count_defect(defect), "the invented-count detector missed a fabricated value"


def test_detector_flags_a_divergent_vocabulary():
    """Negative control: a locally invented reaction key."""
    defect = (
        'export const REACTION_TYPES = ["like", "love"] as const;\n'
        "export function EngagementBar() {\n  return null;\n}\n"
    )
    assert _vocabulary_defect(defect), "the vocabulary detector missed a divergent key set"


def test_detector_flags_a_dropped_mount():
    """Negative control: the page stops rendering the readings."""
    defect = (
        "export function NovaNetPage() {\n"
        "  return <SurfaceLenses surface=\"novanet\" lenses={LENSES} />;\n"
        "}\n"
    )
    assert _unmounted_defect(defect), "the mount detector missed a dropped engagement surface"
