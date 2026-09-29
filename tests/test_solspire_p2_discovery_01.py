from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/architecture/SOLSPIRE_P2_DISCOVERY_v1.md"

def test_discovery_doc_exists():
    assert DOC.is_file()
    text = DOC.read_text()
    assert "SOLSPIRE-P2-DISCOVERY-01" in text
    assert "not implementation" in text.lower() or "NOT AUTHORIZED" in text
    for p in ("Universal Search", "Intent Objects", "Provenance Inspector", "Automation Ontology"):
        assert p in text
    assert "WorkEvent ≠ provenance" in text or "WorkEvent" in text and "provenance" in text
    assert "AEAS" in text and "FROZEN" in text
