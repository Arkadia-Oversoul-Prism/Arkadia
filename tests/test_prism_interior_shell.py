import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "web/public_prism/src/components/PrismInteriorShell.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def _rail(shell: str, name: str) -> list[tuple[str, str]]:
    """Parse a nav rail out of the shell source.

    Asserts the array exists so a renamed or removed rail fails loudly instead of
    letting a substring assertion pass by accident.
    """
    match = re.search(rf"const {name} = \[(.*?)\] as const;", shell, re.S)
    assert match, f"{name} rail not found in PrismInteriorShell.tsx"
    entries = re.findall(r"\{ key: '([^']+)', label: '([^']+)'", match.group(1))
    assert entries, f"{name} rail is empty"
    return entries


def test_authenticated_interior_uses_one_prism_shell():
    """One shell per authenticated interior: same identity, same context, same backend.

    The invariant prose ("Same identity · same context · same backend") was never a
    literal in the component. Assert the structure that actually delivers it.
    """
    shell = SHELL.read_text()
    nav = NAV.read_text()
    assert 'data-testid="prism-interior-shell"' in shell
    assert "useAuth" in shell
    assert 'data-testid="identity-persistence"' in shell
    assert "PrismInteriorShell" in nav


def test_shell_exposes_canonical_primary_surfaces():
    shell = SHELL.read_text()
    primary = _rail(shell, "PRIMARY")
    keys = [key for key, _ in primary]
    # Canonical anchors the rail must keep reachable.
    for anchor in ("novanet", "solspire", "commune"):
        assert anchor in keys, f"primary rail lost anchor surface {anchor!r}"
    # Every primary surface must be resolvable by activeSurfaceFor, or it can never
    # render as the active surface.
    resolver = shell.split("function activeSurfaceFor", 1)[1].split("\n}", 1)[0]
    for key, label in primary:
        assert label, f"primary surface {key!r} has no label"
        assert f"'{key}'" in resolver, f"primary surface {key!r} is not resolved by activeSurfaceFor"
    assert 'data-testid="novanet-primary-rail"' in shell


def test_shell_exposes_secondary_nexus_lenses():
    shell = SHELL.read_text()
    secondary = _rail(shell, "SECONDARY")
    assert len(secondary) >= 4, "secondary lens rail collapsed"
    assert "SECONDARY.map(" in shell, "secondary lenses are not rendered from the SECONDARY rail"
    # The lens expander is a real disclosure control, not a decorative string.
    assert "aria-expanded={lensesOpen}" in shell
    assert "setLensesOpen" in shell
    for key, label in secondary:
        assert label in shell, f"secondary lens {key!r} label {label!r} missing from shell"


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
