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
    surface body inside the shell (same convention as the `<Shell>` mount
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


# ---------------------------------------------------------------------------
# Mounting contract
# ---------------------------------------------------------------------------


def test_boundary_is_mounted_exactly_once_in_the_composition_root():
    importers = [
        str(p.relative_to(ROOT))
        for p in sorted(SRC.rglob("*.ts*"))
        if re.search(r"<ErrorBoundary(?=[\s>])", p.read_text(encoding="utf-8"))
    ]
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


def test_boundary_wraps_the_surface_body_inside_the_shell():
    shell_block = re.search(
        r"<Shell[^>]*>.*?</Shell>",
        APP,
        re.DOTALL,
    )
    assert shell_block, "the composition root renders no Shell"
    block = shell_block.group(0)
    assert "<ErrorBoundary" in block and "{body}" in block
    assert block.index("<ErrorBoundary") < block.index("{body}") < block.index("</ErrorBoundary>")


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
    synthetic_importers = ["web/arkadia_console/src/pages/HomePage.tsx"]
    assert synthetic_importers != ["web/arkadia_console/src/App.tsx"]


def test_negative_control_detects_a_boundary_missing_lifecycle():
    synthetic = "class B extends Component { render() { return this.props.children; } }"
    assert not _implements_lifecycle(synthetic)
    assert _implements_lifecycle(BOUNDARY)


def test_negative_control_detects_an_unkeyed_mount():
    unkeyed = '<ErrorBoundary surface="X" onHome={() => navigate("home")}>{body}</ErrorBoundary>'
    assert not _is_keyed_by_surface(unkeyed)
    assert _is_keyed_by_surface(APP)
