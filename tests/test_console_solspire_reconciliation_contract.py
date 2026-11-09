"""Solariun / SolSpire experience reconciliation — ARK-UI-UNIFICATION-002.

The archived Prism expressed one experience across two surfaces: `Solariun`
(`SolSpireExperience`, lenses `overview`/`projects`/`knowledge`/`memory`/`weaver`/
`engineering-lab`/`opportunity-radar`/…) and `SolSpire` (the team/enterprise
surface, whose `opportunity-radar` lens was labelled "Field"). The console had
reconciled only part of that vocabulary: `Solariun` declared four lenses and had
no "what matters now" cockpit, and `SolSpire` was a single flat page with no
addressable sections at all.

This work item reconciles the rest **into the same navigation and interaction
system** the product already uses — the shared `SurfaceLenses` strip — without a
new store, a second read model, or a forked radar:

* `Solariun` gains `overview` (the archived Home cockpit), `engineering-lab` and
  `field` (the archived `opportunity-radar` lens, expressed on SolSpire).
* `SolSpire` becomes section-addressed (`/enterprise/<lens>`) with the same strip,
  and its sections carry truthful states.

Domain: the Arkadia Console (`web/arkadia_console`). Read-only: nothing here
mutates project, field, lab, weaver or enterprise state.

The frontend half is the repository's source-contract convention with negative
controls; the lens sets are read from the pages' own `LENSES` arrays so the oracle
is a function of the source, not a second hand-written list.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
SOLARIUN_PATH = SRC / "pages" / "SolariunPage.tsx"
SOLSPIRE_PATH = SRC / "pages" / "SolSpirePage.tsx"
OVERVIEW_PATH = SRC / "components" / "solariun" / "SolariunOverview.tsx"
APP_PATH = SRC / "App.tsx"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"

SOLARIUN = SOLARIUN_PATH.read_text(encoding="utf-8")
SOLSPIRE = SOLSPIRE_PATH.read_text(encoding="utf-8")
OVERVIEW = OVERVIEW_PATH.read_text(encoding="utf-8")
APP = APP_PATH.read_text(encoding="utf-8")
ENDPOINTS = ENDPOINTS_PATH.read_text(encoding="utf-8")

#: The archived `SolSpireExperience` lens vocabulary this reconciliation restores
#: (transcribed from `archive/.../solspire/SolSpireExperience.tsx` `NAV`/`LensContent`).
ARCHIVED_LENSES = (
    "overview",
    "projects",
    "knowledge",
    "memory",
    "weaver",
    "engineering-lab",
    "opportunity-radar",
)


def _declared_lens_ids(page_text: str) -> set[str]:
    """The lens ids a page declares, read from its own `LENSES` array.

    A page with no `LENSES` array declares no lens: it returns the empty set
    rather than raising, so the negative control can feed a page that has none.
    """
    block = re.search(r"const\s+LENSES\s*=\s*\[(.*?)\];", page_text, re.DOTALL)
    return set(re.findall(r'id:\s*"([^"]+)"', block.group(1))) if block else set()


def _code_only(text: str) -> str:
    """Comments may name a route freely; only code composes paths."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return text


def _composes_an_inline_solspire_path(text: str) -> bool:
    """A raw `/solspire/...` composition outside the registry = second contract."""
    return bool(re.search(r"[`\"']/?solspire/", _code_only(text)))


# ---------------------------------------------------------------------------
# Solariun — the reconciled lens set
# ---------------------------------------------------------------------------


def test_solariun_declares_the_reconciled_lens_set():
    """The archived vocabulary is reconciled, not dropped.

    `overview` (Home cockpit), `engineering-lab` and `field` (the archived
    `opportunity-radar` lens) join the four the console already declared. The
    archived `opportunity-radar` id is expressed as `field` — the label the
    archive itself gave that lens — so the console's vocabulary matches the
    archived navigation rather than inventing a new name.
    """
    declared = _declared_lens_ids(SOLARIUN)
    assert declared == {
        "overview",
        "projects",
        "knowledge",
        "memory",
        "weaver",
        "engineering-lab",
        "field",
    }, declared


def test_solariun_overview_lens_mounts_the_cockpit():
    assert 'section === "overview" && (' in SOLARIUN
    assert "SolariunOverview" in SOLARIUN
    assert 'import { SolariunOverview } from "../components/solariun/SolariunOverview"' in SOLARIUN


def test_overview_composes_existing_reads_only():
    """The cockpit reuses the page's project read and the personal field read.

    It must not issue a second read of the project list (the page already holds
    it) and must not invent a new endpoint: the only contract it reads is the
    registry's `field` entry.
    """
    assert "endpoints.field" in OVERVIEW, "the cockpit reads the personal field through the registry"
    assert "solspireProjects" not in OVERVIEW, "the cockpit must reuse the page's project read, not re-read it"
    assert not _composes_an_inline_solspire_path(OVERVIEW)
    assert 'field: "/api/me/field"' in ENDPOINTS, "the registry entry it relies on"


def test_overview_reports_a_degraded_source_as_degraded_not_zero():
    """The personal field's per-source provenance is honoured, not flattened."""
    assert "unavailable · not counted" in OVERVIEW
    assert "available.has(source)" in OVERVIEW


def test_owning_surface_lenses_point_do_not_fork():
    """`knowledge`, `weaver`, `engineering-lab` and `field` name their authority.

    One intelligence, many interfaces: each of these lenses names the canonical
    surface that owns the read and offers real navigation to it, rather than
    re-reading the same contract here.
    """
    for lens in ("knowledge", "weaver", "engineering-lab", "field"):
        assert f"{lens}:" in SOLARIUN or f'"{lens}":' in SOLARIUN, lens
    assert 'surface: "engineering-lab"' in SOLARIUN
    assert 'surface: "solspire"' in SOLARIUN, "the field lens points at the SolSpire surface"


# ---------------------------------------------------------------------------
# SolSpire — section-addressed, same navigation system
# ---------------------------------------------------------------------------


def test_solspire_is_section_addressed_with_the_shared_strip():
    assert "SurfaceLenses" in SOLSPIRE, "the surface must use the one shared lens strip"
    assert 'surface="solspire"' in SOLSPIRE
    assert "section" in SOLSPIRE and "onNavigate" in SOLSPIRE


def test_solspire_declares_the_field_lens_and_its_siblings():
    declared = _declared_lens_ids(SOLSPIRE)
    assert declared == {"field", "enterprise", "voice", "proposals"}, declared


def test_solspire_field_lens_mounts_the_radar_and_control_plane():
    """The archived `opportunity-radar` lens is the `field` lens here."""
    assert 'section === "field" && (' in SOLSPIRE
    assert "<OpportunityRadarSection" in SOLSPIRE
    assert "<SolSpireControlPlane" in SOLSPIRE


def test_solspire_renders_an_honest_not_a_lens_state():
    """A section outside the declared set is stated, not silently shown as field."""
    assert "!LENS_IDS.has(section)" in SOLSPIRE
    assert "is not a lens of this surface" in SOLSPIRE


def test_solspire_advertises_only_served_paths():
    """Every advertised contract is on the `/solspire` router, never the wrong `/api` prefix."""
    advertised = re.findall(r'contract="([^"]+)"', SOLSPIRE)
    assert advertised, "the surface must still declare its not-yet-wired contracts"
    for value in advertised:
        assert not value.startswith("/api/solspire/"), f"{value!r} carries the wrong /api prefix"
        assert value.startswith("/solspire/"), f"{value!r} is not on the /solspire router"


def test_app_composes_solspire_with_its_section_and_navigator():
    """The composition root must pass the route's section and the navigator through."""
    assert "<SolSpirePage section={route.section} onNavigate={navigate} />" in APP


# ---------------------------------------------------------------------------
# Negative controls — each detector must bite on the pre-repair shape
# ---------------------------------------------------------------------------


def test_negative_control_the_lens_reader_is_not_vacuous():
    """The reader must return the declared ids and nothing for a page without one."""
    assert _declared_lens_ids(SOLARIUN) == {
        "overview",
        "projects",
        "knowledge",
        "memory",
        "weaver",
        "engineering-lab",
        "field",
    }
    assert _declared_lens_ids("export function X() { return null; }") == set()


def test_negative_control_detects_inline_path_composition():
    synthetic = "useHydration(`/solspire/projects`, fetchIt)"
    assert _composes_an_inline_solspire_path(synthetic)
    assert not _composes_an_inline_solspire_path("useHydration(endpoints.solspireProjects, read)")


def test_negative_control_the_archived_vocabulary_is_actually_covered():
    """Every archived lens id is either declared or explicitly reconciled to one.

    `opportunity-radar` is the one archived id the console renames (`field`); the
    rest are declared verbatim. A reconciliation that dropped one would fail here.
    """
    declared = _declared_lens_ids(SOLARIUN) | _declared_lens_ids(SOLSPIRE)
    renamed = {"opportunity-radar": "field"}
    for lens in ARCHIVED_LENSES:
        target = renamed.get(lens, lens)
        assert target in declared, f"archived lens {lens!r} is not reconciled (expected {target!r})"
