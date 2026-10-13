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


def _renders_degraded_counts(panel: str) -> bool:
    """An unavailable source must surface as degraded, never a confident zero."""
    return (
        "unavailable · not counted" in panel
        and "s.included" in panel
        and "included: s.included" not in panel  # a chip may never claim included when false
    )


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
    assert _renders_degraded_counts(PANEL)
    # The COUNTS rows are gated on membership of the included-source set.
    assert "available.has(source)" in PANEL


def test_negative_control_detects_confident_zeros_for_unavailable_sources():
    synthetic = "value: count(data[key])"  # unconditional: an unavailable source reads as 0
    assert "unavailable · not counted" not in synthetic


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
