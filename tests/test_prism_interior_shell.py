from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "web/public_prism/src/components/PrismInteriorShell.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"


def test_authenticated_interior_uses_one_prism_shell():
    shell = SHELL.read_text()
    nav = NAV.read_text()
    assert 'data-testid="prism-interior-shell"' in shell
    assert "useAuth" in shell
    assert "Same identity · same context · same backend" in shell
    assert "PrismInteriorShell" in nav


def test_shell_exposes_canonical_surfaces():
    shell = SHELL.read_text()
    for view in ("sci", "solspire", "commune", "knowledge-os"):
        assert f"key: '{view}'" in shell


def test_shell_does_not_create_authority_or_backend_paths():
    shell = SHELL.read_text()
    forbidden = ("write_file", "apply_patch", "commit_and_push", "run_transaction", "execute_patch")
    assert not any(token in shell for token in forbidden)
