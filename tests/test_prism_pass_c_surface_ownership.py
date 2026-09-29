"""PRISM-PASS-C — canonical surface ownership / view wiring (source-level)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
SOLARIUN = ROOT / "web/public_prism/src/pages/SolariunConsole.tsx"


def _app() -> str:
    return APP.read_text(encoding="utf-8")


def _block(view: str) -> str:
    """Extract the mount block for `view === 'view'`.

    App.tsx mounts every view inline as a single JSX element —
    `{view === 'spiral-codex' && <motion.div ...>...</motion.div>}` — with no
    parenthesised expression, so match through to the closing `</motion.div>}`.

    The boundary guard matters: a non-greedy `.*?` that never finds its closing
    token will happily swallow the following blocks and return a *different*
    view's markup, which would make every content assertion pass vacuously. A
    block that contains another `{view === ` marker was not extracted correctly.
    """
    text = _app()
    m = re.search(
        rf"\{{view === '{re.escape(view)}' && \(?(.*?)</motion\.div>\)?\}}",
        text,
        re.S,
    )
    assert m, f"view block not found for {view}"
    block = m.group(1)
    assert "{view === " not in block, f"block extraction crossed a view boundary for {view}"
    return block


def _redirect(view: str) -> str:
    """Extract the `handleNavigate` rule(s) that mention `view`.

    A legacy view id may own a mount block, a redirect to a canonical view plus
    section, or both. Rules can group ids —
    `if (requested === 'a' || requested === 'b') next = {...}` — so return every
    matching line rather than a single one.
    """
    lines = [
        line
        for line in _app().splitlines()
        if f"requested === '{view}'" in line
    ]
    assert lines, f"no handleNavigate redirect for {view}"
    return "\n".join(lines)


def test_spiral_codex_not_solspire_field():
    """Spiral Codex is its own surface, never the personal solariun field.

    The legacy `field` lens id is retained in SolariunConsole's compat map (field
    -> overview). What must not recur is passing it to SolariunConsole, which
    accepts only SolSpireLens (there is no `field` lens).
    """
    assert "SpiralCodexFeed" in _block("spiral-codex")
    assert 'initialSection="field"' not in _app()
    assert re.search(r"field:'overview'", SOLARIUN.read_text(encoding="utf-8"))


def test_spiral_codex_uses_feed_component():
    assert "import SpiralCodexFeed" in _app()
    assert "SpiralCodexFeed" in _block("spiral-codex")


def test_echo_field_aliases_resolve_to_solariun_observatory():
    """Echo Field / Echofeild Matrix are personal surfaces.

    Pre-consolidation these aliased SolSpire "field"; consolidation moved the
    personal workspace to Solariun's `observatory` lens, which renders the
    workspace event collection. Assert the two mechanisms — a live mount and a
    redirect rule — rather than the retired SolSpire field alias.
    """
    for view in ("personal-echofeild", "echofeild-matrix"):
        assert "UniversalEchofeildMatrix" in _block(view)
        flat = _redirect(view).replace(" ", "")
        assert "view:'solariun'" in flat
        assert "section:'observatory'" in flat


def test_nav_echo_field_opens_personal_echofeild():
    nav = NAV.read_text(encoding="utf-8")
    assert "Echo Field" in nav
    assert "view: 'personal-echofeild'" in nav


def test_knowledge_os_resolves_to_solariun_knowledge():
    """`knowledge-os` is both a live mount and a redirect alias onto Solariun.

    It shares one grouped `handleNavigate` rule with `codex`
    (`requested === 'knowledge-os' || requested === 'codex'`), and additionally has a
    `'/knowledge-os'` entry in the path table. Asserting the mount alone under-describes
    the route — an earlier revision of this file claimed no redirect rule existed at all.
    """
    block = _block("knowledge-os")
    assert "SolariunConsole" in block
    assert 'initialSection="knowledge"' in block
    assert "SolSpireConsole" not in block  # enterprise console is not the personal lens
    assert "KnowledgeOSPage" not in _app()  # not an independent mount
    flat = re.sub(r"\s+", "", _redirect("knowledge-os"))
    assert "view:'solariun'" in flat
    assert "section:'knowledge'" in flat


def test_codex_resolves_to_knowledge_lens():
    """Legacy `codex` is rewritten onto Solariun's **knowledge** lens.

    `handleNavigate` maps `codex` -> `{view:'solariun', section:'knowledge'}`, and the
    `codex` mount passes `initialSection="knowledge"`. `SolariunConsole` resolves that
    through `LEGACY_MAP`, where `knowledge` is **not** a legacy key, so the value passes
    through unchanged: codex lands on `knowledge`, never on `memory`.

    `LEGACY_MAP` does carry a `codex:'memory'` row (pre-consolidation fallback). Asserting
    that row exists is a declaration-inventory check — it does **not** describe codex's
    route, and an earlier revision of this test wrongly claimed it did.
    """
    block = _block("codex")
    assert "SolariunConsole" in block
    assert 'initialSection="knowledge"' in block
    flat = re.sub(r"\s+", "", _redirect("codex"))
    assert "view:'solariun'" in flat
    assert "section:'knowledge'" in flat
    assert "codex:'memory'" in SOLARIUN.read_text(encoding="utf-8")


def test_loops_resolves_to_solariun_tasks():
    rule = _redirect("loops")
    assert "view: 'solariun'" in rule or "view:'solariun'" in rule
    assert "section: 'tasks'" in rule or "section:'tasks'" in rule
    assert re.search(r"loops:'tasks'", SOLARIUN.read_text(encoding="utf-8"))


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
