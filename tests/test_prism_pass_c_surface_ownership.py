"""PRISM-PASS-C — canonical surface ownership / view wiring (source-level)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"


def _app() -> str:
    return APP.read_text(encoding="utf-8")


def _block(view: str) -> str:
    """Extract JSX block for view === 'view' (best-effort)."""
    text = _app()
    m = re.search(
        rf"\{{view === '{re.escape(view)}' && \((.*?)\n\s*\)\}}",
        text,
        re.S,
    )
    assert m, f"view block not found for {view}"
    return m.group(1)


def test_spiral_codex_not_solspire_field():
    block = _block("spiral-codex")
    assert "SolSpireConsole" not in block or 'initialSection="field"' not in block
    assert "SpiralCodexFeed" in block
    assert 'initialSection="field"' not in block


def test_spiral_codex_uses_feed_component():
    assert "import SpiralCodexFeed" in _app()
    assert "SpiralCodexFeed" in _block("spiral-codex")


def test_echo_field_aliases_resolve_to_solspire_field():
    for view in ("personal-echofeild", "echofeild-matrix"):
        block = _block(view)
        assert "SolSpireConsole" in block
        assert 'initialSection="field"' in block


def test_nav_echo_field_opens_solspire():
    nav = NAV.read_text(encoding="utf-8")
    assert "Echo Field" in nav
    assert "view: 'solspire'" in nav


def test_knowledge_os_resolves_to_solspire_knowledge():
    block = _block("knowledge-os")
    assert "SolSpireConsole" in block
    assert 'initialSection="knowledge"' in block
    assert "KnowledgeOSPage" not in block  # not independent mount


def test_codex_resolves_to_solspire_codex():
    block = _block("codex")
    assert "SolSpireConsole" in block
    assert 'initialSection="codex"' in block


def test_loops_resolves_to_solspire_loops():
    block = _block("loops")
    assert "SolSpireConsole" in block
    assert 'initialSection="loops"' in block


def test_no_new_top_level_views_introduced():
    """Pass C must not expand the View union with new product shells."""
    text = _app()
    m = re.search(r"type View\s*=\s*((?:.|\n)*?);", text)
    assert m
    union = m.group(1)
    # known views from pre-pass baseline — no weaver/shell inventions required
    assert "spiral-codex" in union
    assert "solspire" in union
    assert "'weaver'" not in union  # no new View id for Weaver shell


def test_frontend_no_k3_transaction_in_app():
    text = _app()
    assert "run_transaction" not in text
    assert "execute_patch" not in text
