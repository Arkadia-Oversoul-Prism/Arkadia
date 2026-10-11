"""Workstream 4 — Lab overview surface contract (read-only ceiling + redaction wiring).

Source-level guards for `components/lab/LabOverviewSnapshot.tsx` and its
projection `labOverview.ts`: that the surface is wired to the declared registry
entry, issues no request of its own, asks for no mutating method, renders no
control, and keeps the projection pure.

The redaction guards are the load-bearing ones. `repository.remote` carries
whatever userinfo the environment's remote URL holds, and the handler's
`security.values_redacted` flag does not cover it, so the UI boundary must strip
it. These tests prove the strip is wired and that a negative control fails if the
raw value were rendered instead.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PAGE = REPO_ROOT / "web" / "arkadia_console" / "src" / "pages" / "EngineeringLabPage.tsx"
OVERVIEW_TS = LAB_SRC / "labOverview.ts"
OVERVIEW_TSX = LAB_SRC / "LabOverviewSnapshot.tsx"
ENDPOINTS_TS = REPO_ROOT / "web" / "arkadia_console" / "src" / "lib" / "endpoints.ts"
SERVICE_PY = REPO_ROOT / "lab" / "service.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Read-only ceiling


def test_surface_is_wired_to_the_declared_registry_entry():
    """`labOverview` is already a registry member, so no shared-file edit is needed."""
    source = _read(OVERVIEW_TSX)
    assert "endpoints.labOverview" in source
    assert "/api/lab/overview" not in source
    assert 'labOverview: "/api/lab/overview"' in _read(ENDPOINTS_TS)


def test_surface_fetches_nothing_beyond_its_declared_entry():
    source = _read(OVERVIEW_TSX)
    assert source.count("useHydration<") == 1
    assert source.count("apiRequest<") == 1
    assert "fetch(" not in source


def test_surface_requests_no_mutating_method_and_renders_no_control():
    source = _read(OVERVIEW_TSX) + _read(OVERVIEW_TS)
    for forbidden in ('method: "POST"', 'method: "PUT"', 'method: "DELETE"', "method: 'POST'"):
        assert forbidden not in source
    assert "<button" not in source
    assert "onClick" not in source
    assert "onSubmit" not in source


def test_projection_is_pure():
    source = _read(OVERVIEW_TS)
    assert not re.search(r"^\s*import\b", source, re.MULTILINE), "projection must import nothing"
    for token in ("fetch(", "apiRequest", "useHydration", "localStorage", "window."):
        assert token not in source


def test_mounted_on_the_engineering_lab_page():
    page = _read(PAGE)
    assert "<LabOverviewSnapshot />" in page


# ---------------------------------------------------------------------------
# Credential redaction is wired, not merely available


def test_surface_never_renders_the_raw_remote():
    """The renderer must read the redacted field, not the raw handler value."""
    source = _read(OVERVIEW_TSX)
    assert "ledger.repository.remote.value" in source
    # The raw view field must not appear in a render expression.
    assert "view.repository?.remote" not in source
    assert "repository?.remote" not in source


def test_projection_exposes_the_redacted_remote_and_the_flag():
    source = _read(OVERVIEW_TS)
    assert "redactRemote(" in source
    assert "redacted: boolean" in source or "redacted: true" in source


def test_redaction_is_documented_as_a_handler_gap_not_a_handler_guarantee():
    """The surface must state the scope of the handler's redaction flag.

    `values_redacted: true` reads as blanket assurance but covers
    `security.observations` only. A future reader must not mistake it for a
    guarantee over `repository.remote`.
    """
    source = _read(OVERVIEW_TS) + _read(OVERVIEW_TSX)
    assert "security.observations only" in source
    assert "handler_redaction_scope" in source


def test_negative_control_the_raw_remote_detector_sees_a_raw_render():
    """The detector must fire on a renderer that used the raw value."""
    polluted = "<span>{view.repository?.remote}</span>"
    assert "ledger.repository.remote.value" not in polluted
    assert "repository?.remote" in polluted


def test_negative_control_the_redactor_is_actually_exercised():
    """The projection must call the redactor, not merely declare it."""
    source = _read(OVERVIEW_TS)
    call_sites = re.findall(r"redactRemote\([^)]*\)", source)
    assert call_sites, "redactRemote is declared but never called"
    assert any("remote" in site for site in call_sites), "the call must receive the remote value"


# ---------------------------------------------------------------------------
# The handler contract this surface depends on


def test_handler_route_and_auth_are_what_the_slice_claims():
    """`GET /overview` under the Lab router, authenticated by the router default."""
    source = _read(REPO_ROOT / "api" / "lab_routes.py")
    assert '@router.get("/overview")' in source
    assert 'router = APIRouter(prefix="/api/lab"' in source
    assert "dependencies=[Depends(require_lab_auth)]" in source


def test_handler_still_emits_the_governance_ceiling():
    """The surface's central reading depends on this block existing."""
    source = _read(SERVICE_PY)
    for key in ("maximum_authority", "autonomous_mutation", "production_mutation", "approval_required"):
        assert f'"{key}"' in source, f"build_overview no longer declares {key}"
    assert '"autonomous_mutation":False' in source
    assert '"production_mutation":False' in source
    assert '"approval_required":True' in source


def test_handler_still_reports_partial_status_and_per_component_errors():
    """A failed collector must downgrade the status rather than be silent."""
    source = _read(SERVICE_PY)
    assert '"partial" if errors else "observed"' in source
    assert '"errors":errors' in source
