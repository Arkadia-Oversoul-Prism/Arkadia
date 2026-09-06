from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "web/public_prism/src/components/PrismInteriorShell.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def test_authenticated_interior_uses_one_prism_shell():
    shell = SHELL.read_text()
    nav = NAV.read_text()
    assert 'data-testid="prism-interior-shell"' in shell
    assert "useAuth" in shell
    assert "Same identity · same context · same backend" in shell
    assert "PrismInteriorShell" in nav


def test_shell_exposes_canonical_primary_surfaces():
    shell = SHELL.read_text()
    for view in ("novanet", "sci", "solspire", "commune", "knowledge-os"):
        assert f"key: '{view}'" in shell or f'key: "{view}"' in shell or f"'{view}'" in shell
    assert "PRIMARY" in shell
    assert 'data-testid="prism-primary-rail"' in shell


def test_shell_exposes_secondary_nexus_lenses():
    shell = SHELL.read_text()
    assert "SECONDARY" in shell
    assert 'data-testid="prism-secondary-toggle"' in shell
    assert 'data-testid="prism-secondary-lenses"' in shell
    for label in ("ReasoMate", "Echo Field", "Encyclopedia", "Spiral Grove", "Living Larder", "Offerings", "Weaver"):
        assert label in shell


def test_shell_does_not_create_authority_or_backend_paths():
    shell = SHELL.read_text()
    forbidden = ("write_file", "apply_patch", "commit_and_push", "run_transaction", "execute_patch")
    assert not any(token in shell for token in forbidden)


def test_novanet_view_mounts_content_not_nested_hub():
    """W3: authenticated interior must not re-enter NexusPage tab hierarchy."""
    app = APP.read_text()
    # Find novanet view block
    assert "view === 'novanet'" in app
    assert "NovaNetPage" in app
    # Nested hub must not be the novanet mount
    idx = app.find("view === 'novanet'")
    block = app[idx : idx + 400]
    assert "NovaNetPage" in block
    assert "NexusPage" not in block
