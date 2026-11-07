"""Solariun `memory` lens — personal Echofeild read model — PRR-08.

The `memory` lens previously stated, honestly, that it had no verified read
contract. That claim was too strong: `GET /api/me/field`
(`api/echofeild.py::get_my_field`, `require_auth`) is a served, registry-listed
contract — the personal Echofeild read model the archived Prism surfaced as its
Personal Echofeild / observatory lens. This work item wires the read.

The contract's distinguishing property is **per-source provenance**:
`meta.sources` reports, for every source, whether it was actually included or
came back unavailable. The panel must render that truthfully — a degraded
source shows "unavailable · not counted", never a confident zero.

Domain: the Arkadia Console (`web/arkadia_console`) over the canonical FastAPI
app. Read-only; counts only, no record contents. The backend contract itself
is regression-covered by `tests/test_echofeild_aggregator.py` (auth, isolation,
composition) — executed here as part of this slice's verification, not
re-implemented.

Frontend half is the repository's source-contract convention with negative
controls.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
PANEL_PATH = SRC / "components" / "solariun" / "PersonalFieldPanel.tsx"
SOLARIUN_PATH = SRC / "pages" / "SolariunPage.tsx"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"

PANEL = PANEL_PATH.read_text(encoding="utf-8")
SOLARIUN = SOLARIUN_PATH.read_text(encoding="utf-8")
ENDPOINTS = ENDPOINTS_PATH.read_text(encoding="utf-8")


def _degraded_reading_defects(panel: str) -> list[str]:
    """Why an unavailable source could read as a confident zero.

    Module level, so the live assertion and its negative control call the *same*
    code. The control previously restated the ``unavailable · not counted``
    literal inline and never ran a detector, so the live predicate could be
    replaced by a constant with no red test (measured at `main` `03220c95`:
    forcing it to `True` left the whole file green).
    """
    defects: list[str] = []
    if "unavailable · not counted" not in panel:
        defects.append("a degraded source does not state 'unavailable · not counted'")
    if "s.included" not in panel:
        defects.append("the panel does not read the contract's own `included` flag")
    if "included: s.included" in panel:
        defects.append("a chip claims `included` when the contract says it was not")
    if "available.has(source)" not in panel:
        defects.append("the counts rows are not gated on the included-source set")
    return defects


def test_memory_lens_mounts_the_panel():
    assert 'section === "memory" && <PersonalFieldPanel />' in SOLARIUN
    assert 'import { PersonalFieldPanel } from "../components/solariun/PersonalFieldPanel"' in SOLARIUN


def test_panel_reads_the_registry_member_not_an_inline_path():
    assert "useHydration<PersonalField>(endpoints.field," in PANEL
    assert '"/api/me/field"' not in PANEL, "the path must come from the one registry"
    assert 'field: "/api/me/field"' in ENDPOINTS, "the registry entry it relies on"


def test_panel_renders_the_contract_provenance_verbatim():
    assert "meta?.sources" in PANEL
    assert 'data-testid={`field-source-${s.source}`}' in PANEL
    assert "s.detail || \"unavailable\"" in PANEL, "the contract's own detail must be shown"


def test_degraded_sources_are_shown_as_degraded_not_zero():
    """The load-bearing assertion: an unavailable source is never a confident zero."""
    assert _degraded_reading_defects(PANEL) == [], _degraded_reading_defects(PANEL)


def test_negative_control_detects_confident_zeros_for_unavailable_sources():
    """Prove the detector bites, by calling it on the pre-repair shape.

    Calls :func:`_degraded_reading_defects` — the same function the live assertion
    uses — so the control can actually fail when that detector is disarmed. The
    previous version asserted a literal was absent from a hand-written string and
    ran no detector at all.
    """
    naive = "value: count(data[key])"  # unconditional: an unavailable source reads as 0
    defects = _degraded_reading_defects(naive)
    assert any("unavailable · not counted" in d for d in defects), defects
    assert any("included-source set" in d for d in defects), defects
    # A chip that claims inclusion for a source the contract excluded is its own defect.
    claiming = (
        "unavailable · not counted s.included available.has(source) included: s.included"
    )
    assert any("claims `included`" in d for d in _degraded_reading_defects(claiming))
    # And the detector must stay silent on the real panel, or it is trivially true.
    assert _degraded_reading_defects(PANEL) == []


def test_panel_is_counts_only():
    # No record content is rendered: the panel never maps record items to JSX.
    assert "Counts only" in PANEL
    assert not re.search(
        r"\.map\(\(\s*(note|notes|message|messages|event|events|entry|item|project)\b",
        PANEL,
        re.IGNORECASE,
    ), "the panel must not render record contents — counts and provenance only"


def test_states_use_the_shared_contract_state():
    # The shared component owns loading/auth/unavailable/error; the panel must
    # pass its hydration state straight through and not roll its own machine.
    assert "ContractState" in PANEL
    assert "state={field.state}" in PANEL
    assert "field.state === " not in PANEL, "the panel pre-empts a shared state"
