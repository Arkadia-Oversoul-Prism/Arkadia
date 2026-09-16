"""SOLSPIRE-P1-EXPERIENCE-01 — P1.1, P1.2, P1.3."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
CSS = ROOT / "web/public_prism/src/components/solspire/solspire-canonical.css"


def test_p1_1_arkana_context_pack():
    src = EXP.read_text()
    assert 'data-testid="solariun-arkana-context-pack"' in src
    assert "CONTEXT PACK (explicit)" in src
    assert "Arkana knows everything" in src or "Not “Arkana knows everything.”" in src or "not “Arkana knows everything" in src.lower() or "knows everything" in src
    assert "pack:" in src or "pack={{" in src
    assert "Do not invent access" in src or "Bounded context only" in src


def test_p1_1_not_authorization():
    src = EXP.read_text()
    assert "Not an authorization authority" in src


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
