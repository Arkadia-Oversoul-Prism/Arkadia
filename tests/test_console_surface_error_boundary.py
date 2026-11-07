"""Surface render-failure error boundary — PRR-06.

Before this work item a render exception inside any surface tore down the whole
tree: a blank canonical application with no recovery control. The boundary
catches a failed *surface* render and replaces only that surface with an honest
failure state while the shell stays usable.

Domain: the Arkadia Console (`web/arkadia_console`), the primary application.
This is a resilience seam of the shared application shell (Lane A), not a new
runtime: no data path, auth path, or backend contract changes.

What is asserted:

  * the boundary is mounted exactly once, in the composition root, wrapping the
    surface body for *every* surface — including the declared `standalone` one,
    which returns before the shell (same convention as the `<Shell>` mount
    guard);
  * it is keyed by surface, so a caught failure cannot outlive the surface that
    produced it;
  * it implements both React error-boundary lifecycle methods;
  * the fallback shows the *real* caught error and offers two real recovery
    actions — a full reload, and navigation home bound to the shared router;
  * the failure copy claims nothing about backend work (no "saved", no
    "sent … successfully").

Each load-bearing detector carries a negative control.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
APP_PATH = SRC / "App.tsx"
BOUNDARY_PATH = SRC / "components" / "ErrorBoundary.tsx"

APP = APP_PATH.read_text(encoding="utf-8")
BOUNDARY = BOUNDARY_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def _mount_count(app_source: str) -> int:
    # `Component<ErrorBoundaryProps` contains the substring `<ErrorBoundary` but
    # is a type argument, not a mount — require JSX tag boundaries.
    return len(re.findall(r"<ErrorBoundary(?=[\s>])", app_source))


def _is_keyed_by_surface(app_source: str) -> bool:
    return bool(re.search(r"<ErrorBoundary\s+key=\{route\.surface\}", app_source))


def _implements_lifecycle(boundary_source: str) -> bool:
    return (
        "static getDerivedStateFromError" in boundary_source
        and "componentDidCatch" in boundary_source
    )


def _guards_every_surface(app_source: str) -> bool:
    """True when no render path reaches the surface body without the boundary.

    The standalone surface returns before the shell, so a boundary mounted only
    inside the shell block leaves it unguarded. Require a single hoisted wrapper
    and that both return paths go through it.
    """
    shell_block = re.search(r"<Shell[^>]*>.*?</Shell>", app_source, re.DOTALL)
    if not shell_block:
        return False
    if not re.search(
        r"const surfaceBody = \(\s*<ErrorBoundary[\s\S]*?\{body\}\s*</ErrorBoundary>\s*\);",
        app_source,
    ):
        return False
    if "if (def.standalone) return surfaceBody;" not in app_source:
        return False
    return "{surfaceBody}" in shell_block.group(0)


# ---------------------------------------------------------------------------
# Mounting contract
# ---------------------------------------------------------------------------


def _boundary_mount_owners(sources: dict[str, str]) -> list[str]:
    """Modules that mount the error boundary — the second-mount detector.

    Module level, so the negative control exercises the *same* code the live
    assertion does. The control below used to compare a hand-written list against
    itself, which made it vacuous: renaming the live detector's marker left the
    control passing, so the mount guard could be disarmed with no red test.
    """
    return sorted(
        name for name, src in sources.items() if re.search(r"<ErrorBoundary(?=[\s>])", src)
    )


def test_boundary_is_mounted_exactly_once_in_the_composition_root():
    sources = {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in sorted(SRC.rglob("*.ts*"))
    }
    importers = _boundary_mount_owners(sources)
    assert importers == ["web/arkadia_console/src/App.tsx"], (
        f"the boundary must be mounted only in the composition root; found {importers}"
    )
    assert _mount_count(APP) == 1, "exactly one boundary mount — a second would nest failure states"
    assert 'from "./components/ErrorBoundary"' in APP


def test_boundary_is_keyed_by_surface_so_failure_cannot_outlive_it():
    assert _is_keyed_by_surface(APP), (
        "the boundary must be keyed by route.surface — unkeyed, a caught failure "
        "would persist across navigation"
    )


def test_boundary_wraps_the_surface_body_for_every_surface():
    """The boundary is hoisted, so the shell is what varies, not the boundary.

    Asserting the boundary sits *inside* the shell block would encode the defect
    this guard exists to catch: a standalone surface returns before the shell, so
    a boundary mounted only inside the shell leaves that surface unguarded.
    """
    shell_block = re.search(r"<Shell[^>]*>.*?</Shell>", APP, re.DOTALL)
    assert shell_block, "the composition root renders no Shell"
    assert _guards_every_surface(APP)


# ---------------------------------------------------------------------------
# Fallback contract
# ---------------------------------------------------------------------------


def test_boundary_implements_both_lifecycle_methods():
    assert _implements_lifecycle(BOUNDARY), (
        "an error boundary needs getDerivedStateFromError and componentDidCatch"
    )


def test_fallback_shows_the_real_error_and_real_recovery_actions():
    assert "{error.message}" in BOUNDARY, "the caught error message must be shown, verbatim"
    assert "window.location.reload()" in BOUNDARY, "Reload must be a real full reload"
    assert "onClick={this.props.onHome}" in BOUNDARY, "Go-to-home must use the bound router action"
    assert re.search(r"<ErrorBoundary[^>]*onHome=\{\(\) => navigate\(\"home\"\)\}", APP, re.DOTALL), (
        "the composition root must bind onHome to the shared router"
    )


def test_failure_copy_claims_nothing_about_backend_work():
    # A render failure changes nothing on the backend; the copy must not imply
    # otherwise (no fabricated save/send outcomes in either direction).
    copy = re.search(r"This surface failed while rendering\.(.*?)</p>", BOUNDARY, re.DOTALL)
    assert copy, "the failure copy is missing"
    text = copy.group(1)
    assert "changes nothing on the backend" in text
    for forbidden in ("saved", "submitted", "sent successfully", "restored"):
        assert forbidden not in text.lower(), f"failure copy must not claim {forbidden!r}"


def test_the_boundary_state_is_module_local_not_shared():
    assert "state: ErrorBoundaryState = { error: null };" in BOUNDARY
    assert "context" not in BOUNDARY.lower() or "no context" in BOUNDARY.lower()


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------


def test_negative_control_detects_a_mount_outside_the_composition_root():
    """A second mount is the defect, and the detector must report it.

    The control calls :func:`_boundary_mount_owners` — the same function the live
    assertion uses — on a synthetic second mount. The previous version compared a
    hand-written list to a literal, so it stayed green while the live detector's
    marker was renamed (measured), i.e. it could not fail for any input.
    """
    synthetic = {
        "web/arkadia_console/src/App.tsx": "<ErrorBoundary key={route.surface}>{body}</ErrorBoundary>",
        "web/arkadia_console/src/pages/HomePage.tsx": "<ErrorBoundary>{body}</ErrorBoundary>",
    }
    assert _boundary_mount_owners(synthetic) == [
        "web/arkadia_console/src/App.tsx",
        "web/arkadia_console/src/pages/HomePage.tsx",
    ], _boundary_mount_owners(synthetic)
    # A type argument is not a mount, and must not be reported.
    assert _boundary_mount_owners({"src/x.tsx": "type P = Component<ErrorBoundaryProps>"}) == []


def test_negative_control_detects_a_boundary_missing_lifecycle():
    synthetic = "class B extends Component { render() { return this.props.children; } }"
    assert not _implements_lifecycle(synthetic)
    assert _implements_lifecycle(BOUNDARY)


def test_negative_control_detects_an_unkeyed_mount():
    unkeyed = '<ErrorBoundary surface="X" onHome={() => navigate("home")}>{body}</ErrorBoundary>'
    assert not _is_keyed_by_surface(unkeyed)
    assert _is_keyed_by_surface(APP)


def test_negative_control_detects_the_standalone_surface_escaping_the_boundary():
    """Feed the detector the pre-repair shape: the boundary lives only inside the
    shell and the standalone surface returns the raw body before reaching it."""
    pre_repair = (
        "if (def.standalone) return body;\n"
        "return (\n"
        "  <Shell current={route.surface} onNavigate={handleNavigate}>\n"
        '    <ErrorBoundary key={route.surface} surface="X" onHome={onHome}>{body}</ErrorBoundary>\n'
        "  </Shell>\n"
        ");\n"
    )
    assert not _guards_every_surface(pre_repair)
    assert _guards_every_surface(APP)
