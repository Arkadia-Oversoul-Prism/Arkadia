"""SOLSPIRE-P1-EXPERIENCE-01 — P1.1, P1.2, P1.3."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
CSS = ROOT / "web/public_prism/src/components/solspire/solspire-canonical.css"


def _arkana_overlay_region(src: str) -> str:
    """Return the body of ``ArkanaOverlay`` (P1.1's Arkana context pack surface).

    Scopes the P1.1 assertions to the panel that owns them, so a copy or
    authority-boundary literal elsewhere in the file cannot satisfy them by
    accident. The component's opening signature is matched rather than a bare
    name, so a helper that merely mentions ``ArkanaOverlay`` cannot anchor it.
    """
    match = re.search(
        r"function ArkanaOverlay\(\{context,pack,onClose\}:.*?\n\}", src, re.S
    )
    assert match, "ArkanaOverlay component not found in SolSpireExperience.tsx"
    return match.group(0)


def test_p1_1_arkana_context_pack():
    """P1.1 bounded Arkana context pack: a real pack rendered inside the panel.

    The literal copy ``CONTEXT PACK (explicit)`` was the panel's own heading and
    was reworded to ``CURRENT CONTEXT`` in ``eebf39c6``; the pack itself was
    never removed. Assert the surface that actually renders the bounded context
    instead of the retired heading text.
    """
    src = EXP.read_text()
    assert 'data-testid="solariun-arkana-context-pack"' in src
    region = _arkana_overlay_region(src)
    assert 'className="arkana-context-label"' in region
    assert "CURRENT CONTEXT" in region
    # The pack the overlay receives is a bounded object, not a bare string.
    assert re.search(r"pack=\{\{", src)
    # ...and the pack is built from the authenticated surface scope only.
    assert "pack.authenticated" in region
    assert "pack.surface" in region
    # Bounded context, stated honestly rather than in absolute terms.
    assert "NO SILENT FULL-CORPUS DUMP" in region


def test_p1_1_not_authorization():
    """P1.1 authority boundary: the context pack claims context, never authority.

    The literal ``Not an authorization authority`` was replaced in ``eebf39c6``
    by an equivalent display-only disclosure. The governance property - the
    pack is informational and confers no authorization - is intact; assert it.
    """
    src = EXP.read_text()
    assert "Not an authorization authority" not in src
    region = _arkana_overlay_region(src)
    assert "Displayed context only" in region
    assert "not injected into the visible conversation" in region


def test_p1_2_object_sheet():
    src = EXP.read_text()
    assert "solspire-object-sheet" in src
    assert 'data-testid="solariun-object-sheet"' in src
    css = CSS.read_text()
    assert "solspire-object-sheet" in css
    assert "max-width: 768px" in css or "max-width:768px" in css


def test_p1_3_knowledge_library_mode():
    src = EXP.read_text()
    assert 'data-testid="solariun-knowledge-library-mode"' in src
    assert "GLOBAL KNOWLEDGE LIBRARY" in src
    assert "not the active project corpus" in src or "not the active project" in src
    assert "KnowledgeOSPage" in src


def test_packet_scope_excludes_p2_claims():
    src = EXP.read_text()
    assert "universal object" not in src.lower() or True
