"""Lane 2 — NovaNet public-field author controls (edit / delete own post).

The archived Prism field offered author-only Edit / Delete controls over the
public transmissions feed. The console field was read-only, so the product
capability was missing even though the backend contract is live and verified.

These are **source-level** assertions against the active console, matching the
established convention for console contract guards
(`tests/test_prism_opportunity_entry_flow.py`, `tests/test_console_endpoint_registry_contract.py`).

The backend contract this surface mirrors (`api/transmissions.py`):
  * ``PATCH  /api/transmissions/{id}`` — 401 anonymous, 403 non-owner, 200 owner
  * ``DELETE /api/transmissions/{id}`` — 401 anonymous, 403 non-owner, 200 owner
Ownership is derived from the verified Firebase uid, never the client.

Each behavioural claim carries a **negative control**: a synthetic source that
violates it must be reported by the same detector that judges the live tree, so
the guard cannot be disarmed by rewriting the component.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
PAGE = CONSOLE / "pages" / "NovaNetPage.tsx"
CONTROLS = CONSOLE / "components" / "novaNet" / "AuthorControls.tsx"
BACKEND = ROOT / "api" / "transmissions.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The backend contract the surface mirrors is the one that is served
# ---------------------------------------------------------------------------


def test_backend_serves_the_author_only_mutation_routes():
    """The controls are only legitimate because these handlers exist."""
    src = _read(BACKEND)
    assert '@router.patch("/api/transmissions/{post_id}")' in src
    assert '@router.delete("/api/transmissions/{post_id}")' in src
    # The boundary is identity-derived, not client-supplied.
    assert "only the author can edit this post" in src
    assert "only the author can delete this post" in src


# ---------------------------------------------------------------------------
# The component exists and composes its path from the one registry
# ---------------------------------------------------------------------------


def test_author_controls_component_exists():
    assert CONTROLS.is_file(), "the NovaNet author controls component is missing"
    src = _read(CONTROLS)
    assert "export function AuthorControls" in src
    assert 'data-testid="novanet-author-controls"' in src
    assert 'data-testid="novanet-author-edit"' in src


def test_mutation_path_is_registry_derived_not_a_literal():
    """No inline path: the base must come from ``endpoints.transmissions``."""
    src = _read(CONTROLS)
    assert "endpoints.transmissions" in src, "the path base must be the registry collection"
    # A raw literal in a request path would be a second, unreviewed contract.
    assert not re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', src), (
        "the mutation path must not be an inline literal"
    )
    # The id must be encoded so it cannot address a different route.
    assert "encodeURIComponent" in src


# ---------------------------------------------------------------------------
# Ownership mirrors the backend boundary; the client never decides it
# ---------------------------------------------------------------------------


def test_page_gates_controls_on_verified_uid_ownership():
    src = _read(PAGE)
    assert "AuthorControls" in src, "the page must mount the author controls"
    # The gate compares the verified uid to the post's owner_uid.
    assert re.search(r"myUid\s*===\s*t\.owner_uid", src), (
        "ownership must compare the verified uid to owner_uid"
    )
    assert "useAuth" in src, "the verified identity must come from the auth context"
    assert "field.reload" in src, "a mutation must re-read the field it changed"


def test_component_renders_nothing_for_a_non_owner():
    """A control that could only 403 is a decorative control (directive §6)."""
    src = _read(CONTROLS)
    assert re.search(r"if\s*\(\s*!isOwn\s*\)\s*return\s+null", src), (
        "AuthorControls must render nothing when the reader is not the owner"
    )


# ---------------------------------------------------------------------------
# Detectors — the same predicate applied to the live tree and to a defect
# ---------------------------------------------------------------------------

_OWNERSHIP_GATE = re.compile(r"myUid\s*===\s*t\.owner_uid")
_NON_OWNER_RETURN = re.compile(r"if\s*\(\s*!isOwn\s*\)\s*return\s+null")
_REGISTRY_BASE = "endpoints.transmissions"


def _ownership_defect(source: str) -> bool:
    """True when a page offers the controls without a verified-uid gate."""
    return "AuthorControls" in source and not _OWNERSHIP_GATE.search(source)


def _non_owner_defect(source: str) -> bool:
    """True when a component can render controls for a non-owner."""
    return "export function AuthorControls" in source and not _NON_OWNER_RETURN.search(source)


def _literal_path_defect(source: str) -> bool:
    """True when the mutation path is inlined rather than registry-derived."""
    inlined = re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', source)
    return bool(inlined) or _REGISTRY_BASE not in source


def test_detectors_are_silent_on_the_live_tree():
    assert not _ownership_defect(_read(PAGE))
    assert not _non_owner_defect(_read(CONTROLS))
    assert not _literal_path_defect(_read(CONTROLS))


def test_detector_flags_an_ungated_control():
    """Negative control: a page that mounts the controls for everyone."""
    defect = "export function NovaNetPage() {\n  return <AuthorControls transmission={t} />;\n}\n"
    assert _ownership_defect(defect), "the ownership detector missed an ungated control"


def test_detector_flags_a_control_offered_to_a_non_owner():
    """Negative control: a component with no owner check."""
    defect = "export function AuthorControls({ transmission }) {\n  return <button>Delete</button>;\n}\n"
    assert _non_owner_defect(defect), "the non-owner detector missed an unguarded control"


def test_detector_flags_an_inlined_mutation_path():
    """Negative control: the plausible-but-unreviewed inline contract."""
    defect = 'const r = await apiRequest("/api/transmissions/" + id, { method: "DELETE" });'
    assert _literal_path_defect(defect), "the inline-path detector missed a literal contract"
