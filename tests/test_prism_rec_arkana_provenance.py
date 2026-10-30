"""Arkana response provenance — frontend source contract (prism-recursive-recovery-01).

The console's Arkana surface now renders the provenance a reply already carried.
`POST /api/commune/resonance` returns three retrieval channels beside `reply`:
`rag_refs` (corpus scrolls scored by `_rag_context`), `sources` (Knowledge OS
notes actually injected, from `oracle_spine.build_sources`), and `memory` (turn
metadata). The console previously dropped all three, so a reader could not tell
what informed a reply.

This guard binds the slice to the things that make the claim real, at the source
level (this repository's frontend test convention):

  * the **backend contract** the slice reads: the three channel names and their
    element shapes are the ones `api/main.py` / `api/oracle_spine.py` emit;
  * the **provenance is normalised, not invented**: the surface renders the
    normalized channels from `askArkana`, which derives them from the response
    (`buildProvenance`), not from a constant;
  * the **read-only ceiling**: neither new module issues a mutating request;
  * an **honest no-retrieval state** that is distinct from an empty channel.

Negative controls prove each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"

PAGE = CONSOLE / "pages" / "ArkanaPage.tsx"
LIB = CONSOLE / "lib" / "arkana.ts"
CONTRACT = CONSOLE / "components" / "arkana" / "arkanaProvenanceContract.ts"
PANEL = CONSOLE / "components" / "arkana" / "ArkanaProvenancePanel.tsx"
RESONANCE_HANDLER = ROOT / "api" / "main.py"
SPINE = ROOT / "api" / "oracle_spine.py"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (each has a negative control below)
# ---------------------------------------------------------------------------


def mutating_calls(text: str) -> list[str]:
    """Every mutating HTTP method a module explicitly asks for."""
    return [m.group(1) for m in re.finditer(r'method\s*:\s*"([A-Z]+)"', text) if m.group(1) in MUTATING_METHODS]


def renders_provenance_from_a_constant(text: str) -> bool:
    """A page that renders a provenance object the reply did not supply.

    The defect is a panel fed by a literal rather than the normalised response,
    e.g. ``provenance={{ rag_refs: [], sources: [] }}`` or a hardcoded object.
    """
    return bool(re.search(r"provenance=\{\{", text)) or bool(
        re.search(r"const\s+\w*[Pp]rovenance\w*\s*=\s*\{", text)
    )


def _panel_renders_field(source: str, marker: str) -> bool:
    """Whether the panel body actually reads a provenance field name."""
    return marker in source


# ---------------------------------------------------------------------------
# The backend emits the channels the contract names
# ---------------------------------------------------------------------------


def test_resonance_handler_returns_the_three_channels():
    handler = _read(RESONANCE_HANDLER)
    for channel in ('"rag_refs"', '"sources"', '"memory"'):
        assert channel in handler, f"resonance handler no longer returns {channel}"


def test_rag_context_emits_label_and_category():
    handler = _read(RESONANCE_HANDLER)
    assert '"label": s[' in handler
    assert '"category": s[' in handler


def test_build_sources_emits_title_type_via():
    spine = _read(SPINE)
    for field in ('"title"', '"type"', '"via"', '"excerpt"'):
        assert field in spine, f"build_sources no longer emits {field}"


# ---------------------------------------------------------------------------
# The contract names the channels (feature-local, not a shared registry)
# ---------------------------------------------------------------------------


def test_contract_declares_the_three_channels():
    contract = _read(CONTRACT)
    for channel in ("rag_refs", "sources", "memory"):
        assert channel in contract
    assert '"note" | "graph"' in contract


def test_negative_control_detector_flags_a_hardcoded_provenance():
    assert renders_provenance_from_a_constant("<ArkanaProvenancePanel provenance={{ rag_refs: [] }} />") is True
    assert renders_provenance_from_a_constant("const fakeProvenance = { ragRefs: [] };") is True
    assert renders_provenance_from_a_constant(
        "{turn.provenance && <ArkanaProvenancePanel provenance={turn.provenance} />}"
    ) is False


# ---------------------------------------------------------------------------
# The library normalises provenance from the response
# ---------------------------------------------------------------------------


def test_library_builds_provenance_from_the_response():
    lib = _read(LIB)
    assert "buildProvenance" in lib
    assert "reply.rag_refs" in lib
    assert "reply.sources" in lib
    assert "reply.memory" in lib


def test_library_returns_the_turn_with_provenance():
    lib = _read(LIB)
    assert "Promise<ArkanaTurn>" in lib
    assert "provenance:" in lib


# ---------------------------------------------------------------------------
# The page renders the panel, fed by the reply
# ---------------------------------------------------------------------------


def test_arkana_page_renders_the_provenance_panel():
    page = _read(PAGE)
    assert 'import { ArkanaProvenancePanel }' in page
    assert "<ArkanaProvenancePanel provenance={turn.provenance} />" in page


def test_page_holds_provenance_from_the_reply():
    page = _read(PAGE)
    assert "result.provenance" in page
    assert "ArkanaProvenance" in page


def test_negative_control_page_shape_is_flagged_as_constant_fed():
    """A page render bounded to a literal is the defect; the real form is not."""
    assert renders_provenance_from_a_constant(
        "<ArkanaProvenancePanel provenance={{ rag_refs: reply.rag_refs }} />"
    ) is True


# ---------------------------------------------------------------------------
# Read-only ceiling
# ---------------------------------------------------------------------------


def test_new_modules_issue_no_mutating_request():
    assert mutating_calls(_read(CONTRACT)) == []
    assert mutating_calls(_read(PANEL)) == []
    lib = _read(LIB)
    # The JSON fallback and SSE stream are both conversational POSTs. No other
    # write surface is introduced by the Arkana page or provenance modules.
    assert mutating_calls(lib) == ["POST", "POST"]
    assert re.search(r"apiRequest<ArkanaReply>\\(endpoints\\.arkanaResonance,", lib)
    assert re.search(r"const path = endpoints\\.arkanaResonanceStream;", lib)


def test_negative_control_detector_flags_a_mutating_module():
    assert mutating_calls('apiRequest(p, { method: "PATCH", body: "{}" })') == ["PATCH"]
    assert mutating_calls("apiRequest(p)") == []


# ---------------------------------------------------------------------------
# Honest no-retrieval state vs empty channel
# ---------------------------------------------------------------------------


def test_panel_distinguishes_no_retrieval_from_empty_channel():
    panel = _read(PANEL)
    assert "hasRetrieval" in panel
    assert "arkana-provenance-none" in panel
    assert "arkana-provenance" in panel


def test_panel_renders_each_channel_field():
    panel = _read(PANEL)
    assert _panel_renders_field(panel, "notes_retrieved")
    assert _panel_renders_field(panel, "ragRefs")
    assert _panel_renders_field(panel, "sources")


def test_contract_retrieval_flag_ignores_bare_injection():
    """A memory object is present on every call; `injected` alone is not evidence."""
    contract = _read(CONTRACT)
    assert "notes_retrieved" in contract
    assert "ragRefs.length > 0" in contract
    assert "sources.length > 0" in contract
