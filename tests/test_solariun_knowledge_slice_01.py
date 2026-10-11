"""Workstream 3 — Solariun / Knowledge OS first bounded slice (source contract).

The slice wires the declared ``GET /api/knowledge/graph`` contract into the
Knowledge OS surface as a feature-local panel. This module is a source-level
contract over that slice, matching the repository convention for frontend
guards (see ``tests/test_prism_pass_c_surface_ownership.py`` and
``tests/test_frontend_arkadia_console_rebuild_01.py``).

It also records the ownership boundary the shared contract imposes: the slice
touches only feature-owned files and does not edit ``App.tsx``, ``lib/router.ts``,
``lib/surfaces.ts``, the shared shell or the endpoint registry.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
FEATURE = CONSOLE / "pages" / "knowledge"
ARCHIVE = ROOT / "archive" / "frontend" / "arkadia-prism" / "web" / "public_prism" / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── discovered paths (recorded, not guessed from product names) ──────────────

def test_current_solariun_and_knowledge_paths_are_where_the_slice_expects():
    assert (CONSOLE / "pages" / "SolariunPage.tsx").is_file()
    assert (CONSOLE / "pages" / "KnowledgePage.tsx").is_file()
    assert (FEATURE / "KnowledgeGraphPanel.tsx").is_file()
    assert (FEATURE / "knowledgeContracts.ts").is_file()


def test_archived_sources_remain_available_as_evidence():
    # The retired Prism UI is evidence for reconciliation, not code to restore.
    assert (ARCHIVE / "pages" / "SolariunConsole.tsx").is_file()
    assert (ARCHIVE / "pages" / "knowledge" / "KnowledgeOSPage.tsx").is_file()


# ── the slice is mounted through the page it owns ────────────────────────────

def test_knowledge_page_mounts_the_graph_panel():
    page = _read(CONSOLE / "pages" / "KnowledgePage.tsx")
    assert 'from "./knowledge/KnowledgeGraphPanel"' in page
    assert "<KnowledgeGraphPanel />" in page


def test_slice_does_not_edit_the_shared_composition_seam():
    # The panel is reached through KnowledgePage; App.tsx stays untouched.
    app = _read(CONSOLE / "App.tsx")
    assert "KnowledgeGraphPanel" not in app
    assert "knowledge/" not in app


# ── the panel consumes the declared contract, not an invented one ────────────

def test_panel_consumes_the_declared_endpoint_through_the_shared_client():
    panel = _read(FEATURE / "KnowledgeGraphPanel.tsx")
    assert "endpoints.knowledgeGraph" in panel
    assert 'from "../../lib/apiClient"' in panel
    assert 'from "../../lib/useHydration"' in panel


def test_panel_declares_no_hardcoded_host_or_second_api_base():
    panel = _read(FEATURE / "KnowledgeGraphPanel.tsx")
    assert not _violations(panel), "panel must not hardcode a host or bypass the canonical client"


def test_panel_does_not_reimplement_the_ownership_boundary_client_side():
    # The server applies the ownership predicate. A client-side `user_id` filter
    # could only *look* like a boundary while the response still carried the data.
    panel = _read(FEATURE / "KnowledgeGraphPanel.tsx")
    assert "user_id" not in panel
    assert "summarizeGraph" in panel  # scope is *reported*, not enforced, here


def test_contracts_module_classifies_public_versus_scoped():
    contracts = _read(FEATURE / "knowledgeContracts.ts")
    assert "classifyGraphScope" in contracts
    assert '"empty"' in contracts
    assert '"public"' in contracts
    assert '"scoped"' in contracts
    assert "user_id" in contracts


# ── negative control: the detector bites ─────────────────────────────────────

_HARDCODED = re.compile(r"https?://|VITE_API_URL|import\.meta\.env\.VITE_API_BASE_URL")
_SHAPE_GUARD = re.compile(r"Array\.isArray\(candidate\.nodes\)\s*&&\s*Array\.isArray\(candidate\.edges\)")


def _violations(source: str) -> list[str]:
    """Flag host literals and non-canonical API bases in a feature module."""
    return _HARDCODED.findall(source)


def test_detector_flags_a_hardcoded_host():
    offending = 'const r = await fetch("https://arkadia-qzu4.onrender.com/api/knowledge/graph");'
    assert _violations(offending), "the detector must report a hardcoded production origin"


def test_detector_is_silent_on_the_shipped_panel():
    assert _violations(_read(FEATURE / "KnowledgeGraphPanel.tsx")) == []


# ── an unrecognised payload must not read as a legitimate empty scope ────────

def test_panel_rejects_an_unrecognised_payload():
    panel = _read(FEATURE / "KnowledgeGraphPanel.tsx")
    assert "isKnowledgeGraphData" in panel
    assert "ApiError" in panel
    assert "isKnowledgeGraphData" in _read(FEATURE / "knowledgeContracts.ts")


def test_shape_guard_checks_both_collections():
    assert _SHAPE_GUARD.search(_read(FEATURE / "knowledgeContracts.ts"))


def test_shape_guard_detector_flags_a_weakened_guard():
    weakened = "return Array.isArray(candidate.nodes);"
    assert not _SHAPE_GUARD.search(weakened), "a guard that checks only `nodes` must not satisfy the detector"
