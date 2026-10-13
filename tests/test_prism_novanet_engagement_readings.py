"""Lane 2 — NovaNet public-field engagement (interactive reactions / comments).

The public transmissions feed (`GET /api/transmissions`, `api/transmissions.py`)
returns four reaction counters (``heart`` / ``fire`` / ``star`` / ``mind``), a
``reposts`` count and a ``comments`` array on every post. The archived Prism field
card made the reaction and comment readings **interactive**; the console first
rendered them read-only, so the interaction was missing even though both write
handlers are live and verified.

This guard now pins the **interactive** contract:

  * ``POST /api/transmissions/{id}/react``   — ``{type}`` over the backend's four
    declared keys; the server refuses anything else with 400.
  * ``POST /api/transmissions/{id}/comment`` — ``{content}``; the server refuses
    blank content with 400.

and the boundaries that keep it honest:

  * **exactly these two** write paths are composed — no third, unverified route;
  * ``reposts`` carries **no** control, because the router declares no repost
    write handler (a grep of `api/transmissions.py`);
  * the paths are registry-derived, never inline literals;
  * no count is invented — a value the server did not return reads its own ``0``.

These are **source-level** assertions against the active console, matching the
established convention for console contract guards
(`tests/test_prism_novanet_author_controls.py`,
`tests/test_prism_opportunity_entry_flow.py`). Each behavioural claim carries a
**negative control** — a synthetic source that violates it must be reported by
the same detector that judges the live tree.
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
    """The readings and their write handlers are only legitimate because they exist."""
    src = _read(BACKEND)
    assert '"reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0}' in src
    assert '"comments": [], "reposts": 0' in src
    assert 'valid = {"heart", "fire", "star", "mind"}' in src
    # The two wired write routes are the backend's own.
    assert '@router.post("/api/transmissions/{post_id}/react")' in src
    assert '@router.post("/api/transmissions/{post_id}/comment")' in src


def test_reposts_has_no_write_handler_on_the_router():
    """`reposts` stays a reading: the backend serves no repost mutation."""
    src = _read(BACKEND)
    assert not re.search(r"@router\.(post|patch|put)\([^)]*repost", src), (
        "a repost write handler would make the read-only repost reading a lie"
    )


def test_engagement_component_exists_and_wires_exactly_the_two_routes():
    assert ENGAGEMENT.is_file(), "the NovaNet engagement component is missing"
    src = _read(ENGAGEMENT)
    assert "export function EngagementBar" in src
    assert 'data-testid="novanet-engagement"' in src
    # Both declared write routes are reachable from this component.
    assert re.search(r"`\$\{endpoints\.transmissions\}/\$\{encodeURIComponent\([^)]*\)\}/react`", src), (
        "the reaction path must be composed from the registry"
    )
    assert re.search(r"`\$\{endpoints\.transmissions\}/\$\{encodeURIComponent\([^)]*\)\}/comment`", src), (
        "the comment path must be composed from the registry"
    )


def test_only_two_write_paths_are_wired():
    """No third mutation path: exactly react + comment call `apiRequest`."""
    src = _read(ENGAGEMENT)
    calls = re.findall(r"apiRequest[^\n]*?\(([^,]+),", src)
    assert len(calls) == 2, f"expected exactly two write calls, found {len(calls)}: {calls}"


def test_mutation_paths_are_registry_derived_not_literals():
    """No inline path: the base must come from ``endpoints.transmissions``."""
    src = _read(ENGAGEMENT)
    assert "endpoints.transmissions" in src, "the path base must be the registry collection"
    assert not re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', src), (
        "the mutation path must not be an inline literal"
    )
    assert "encodeURIComponent" in src


def test_reaction_vocabulary_is_the_backends_own():
    """The four keys and their order come from the backend, not a local guess."""
    src = _read(ENGAGEMENT)
    assert re.search(
        r'REACTION_TYPES\s*=\s*\[\s*"heart"\s*,\s*"fire"\s*,\s*"star"\s*,\s*"mind"\s*\]',
        src,
    ), "the reaction vocabulary must be the backend's four declared keys, in order"


def test_no_invented_counts():
    """A count the server did not return reads the server's own zero."""
    src = _read(ENGAGEMENT)
    assert "reactions?.[type] ?? 0" in src, "a missing reaction count must read 0, not be invented"
    assert "typeof transmission.reposts" in src, "reposts must be the server value when present"


def test_reposts_carries_no_control():
    """The repost reading is shown without a button — no unverified capture path."""
    src = _read(ENGAGEMENT)
    block = re.search(r'data-testid="novanet-reposts"(.*?)</span>\s*</div>', src, re.S)
    assert block, "the reposts reading must render"
    assert "<button" not in block.group(1), "reposts must not carry a control (no write handler exists)"


def test_page_mounts_the_engagement_surface_with_reload():
    """The page renders the readings and re-reads the feed after a write."""
    src = _read(PAGE)
    assert "EngagementBar" in src, "the NovaNet field must render the declared readings"
    assert "<EngagementBar transmission={t} onChanged={field.reload} />" in src, (
        "a write must re-read the feed so the server's counts are shown"
    )


# ---------------------------------------------------------------------------
# Detectors — the same predicate applied to the live tree and to a defect
# ---------------------------------------------------------------------------

_REACTION_VOCAB = re.compile(
    r'REACTION_TYPES\s*=\s*\[\s*"heart"\s*,\s*"fire"\s*,\s*"star"\s*,\s*"mind"\s*\]'
)
_ZERO_FALLBACK = re.compile(r"reactions\?\.\[type\]\s*\?\?\s*0")


def _third_path_defect(source: str) -> bool:
    """True when the surface wires a write path beyond react + comment."""
    calls = re.findall(r"apiRequest[^\n]*?\(([^,]+),", source)
    return "export function EngagementBar" in source and len(calls) != 2


def _inline_path_defect(source: str) -> bool:
    """True when a mutation path is an inline literal rather than registry-derived."""
    return "export function EngagementBar" in source and (
        re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', source) is not None
        or "endpoints.transmissions" not in source
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
    assert not _third_path_defect(_read(ENGAGEMENT))
    assert not _inline_path_defect(_read(ENGAGEMENT))
    assert not _invented_count_defect(_read(ENGAGEMENT))
    assert not _vocabulary_defect(_read(ENGAGEMENT))
    assert not _unmounted_defect(_read(PAGE))


def test_detector_flags_a_third_write_path():
    """Negative control: a repost path invented with no backend handler."""
    defect = (
        "export function EngagementBar({ transmission }) {\n"
        '  apiRequest(`${endpoints.transmissions}/${transmission.id}/react`, { method: "POST" });\n'
        '  apiRequest(`${endpoints.transmissions}/${transmission.id}/comment`, { method: "POST" });\n'
        '  apiRequest(`${endpoints.transmissions}/${transmission.id}/repost`, { method: "POST" });\n'
        "  return null;\n"
        "}\n"
    )
    assert _third_path_defect(defect), "the third-path detector missed an unwired route"


def test_detector_flags_an_inline_path():
    """Negative control: a mutation path that bypasses the registry."""
    defect = (
        "export function EngagementBar({ transmission }) {\n"
        '  apiRequest("/api/transmissions/x/react", { method: "POST" });\n'
        "  apiRequest(`${endpoints.transmissions}/${transmission.id}/comment`, { method: \"POST\" });\n"
        "  return null;\n"
        "}\n"
    )
    assert _inline_path_defect(defect), "the inline-path detector missed a literal route"


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
        '  return <SurfaceLenses surface="novanet" lenses={LENSES} />;\n'
        "}\n"
    )
    assert _unmounted_defect(defect), "the mount detector missed a dropped engagement surface"
