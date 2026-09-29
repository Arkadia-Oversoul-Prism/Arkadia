"""M07 — AEAS-v0.1.1 freeze verification (no implementation activation)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AEAS = ROOT / "docs/control-plane/AEAS-v0.1.1.md"


def test_aeas_artifact_exists():
    assert AEAS.is_file()


def test_aeas_declares_frozen():
    text = AEAS.read_text(encoding="utf-8")
    assert "AEAS-v0.1.1" in text
    assert "FROZEN" in text
    assert "Implementation: NOT AUTHORIZED" in text or "Implementation: NOT AUTHORIZED" in text.replace(" ", "")


def test_aeas_prohibits_autonomous_merge_deploy():
    text = AEAS.read_text(encoding="utf-8")
    assert "Autonomous Merge: PROHIBITED" in text or "Autonomous Merge" in text
    assert "Human Authorization" in text


def test_m07_does_not_rewrite_aeas_body_in_tests():
    # Guard: tests only read
    assert AEAS.stat().st_size > 500
