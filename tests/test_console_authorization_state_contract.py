"""Boundary guard: a 403 authorization refusal is not a missing identity.

``AUTHORITY`` and ``AUTHORIZATION`` are separate properties, and the console must
not collapse them. The backend pins the distinction:
``tests/test_authority_boundary.py`` asserts that an *authenticated* principal
without the ``Govern`` authority is refused with ``403`` (forbidden), not ``401``
(unauthenticated); the two layers are distinct server-side.

The console historically violated that server-side boundary. ``useHydration.stateFor``
mapped both ``AUTH_REQUIRED`` (401) and ``FORBIDDEN`` (403) to a single
``auth-required`` hydration state, and the shared ``ContractState`` panel rendered
it as "Authentication required — Sign in to load it." For a viewer who *is* signed
in, the 403 message is false and its retry advice cannot succeed: the backend refused
the identity, it did not fail to recognize one.

Measured on ``main`` @ ``3ca8582a``, ``stateFor`` was::

    if (error.kind === "AUTH_REQUIRED") return "auth-required";
    if (error.kind === "FORBIDDEN")     return "auth-required";   # <-- the defect

This module pins the repair and carries a **negative control**: the pre-repair shape
is fed to the same detector and must be reported, so the guard cannot be disarmed by
rewriting the source back without also reddening this test.

Source-level (like the other console contract guards in this repo); no DOM, no bundler.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Spell the surface with its joined path so `scripts/console_contract_domain.py`
# selects this guard into the console-contract domain (it derives the domain from
# the surface spelling in a guard's source). Without the joined spelling the gate
# would not execute this file -- a guard no workflow runs is decoration.
CONSOLE = ROOT / "web/arkadia_console" / "src"
HOOK = CONSOLE / "lib" / "useHydration.ts"
UI = CONSOLE / "components" / "ui.tsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# A pure detector over the hook source, so both the live file and a synthetic
# pre-repair sample are judged by the same rule.
# ---------------------------------------------------------------------------

def forbidden_is_conflated_with_auth_required(source: str) -> bool:
    """True when a `FORBIDDEN` classification is routed to `auth-required`.

    The defect is specifically a line that tests ``FORBIDDEN`` and returns the
    ``auth-required`` state. A correct repair routes ``FORBIDDEN`` to its own
    state, so no such line exists.
    """
    for raw in source.splitlines():
        line = raw.split("//", 1)[0]
        if "FORBIDDEN" in line and "auth-required" in line:
            return True
    return False


# ---------------------------------------------------------------------------
# Positive: the live source must not conflate the two.
# ---------------------------------------------------------------------------

def test_forbidden_is_a_distinct_hydration_state():
    source = _read(HOOK)
    assert '| "forbidden"' in source, "HydrationState must declare a distinct `forbidden` state"
    assert not forbidden_is_conflated_with_auth_required(source), (
        "stateFor routes FORBIDDEN to auth-required; a signed-in viewer is told to sign in"
    )


def test_state_classifier_covers_the_repair():
    source = _read(HOOK)
    assert 'if (error.kind === "FORBIDDEN") return "forbidden";' in source
    assert 'if (error.kind === "AUTH_REQUIRED") return "auth-required";' in source


def test_classifier_is_exported_for_direct_testing():
    # `stateFor` must be exported so a future DOM-level test can call it without a
    # render harness; a private classifier is only reachable through the hook.
    assert "export function stateFor(" in _read(HOOK)


# ---------------------------------------------------------------------------
# The shared panel must render the distinct state, and its copy must not tell an
# already-signed-in viewer to sign in.
# ---------------------------------------------------------------------------

def test_contract_panel_renders_the_forbidden_state():
    source = _read(UI)
    assert "forbidden: {" in source, "ContractState must carry a copy entry for `forbidden`"
    assert "Not authorized for this identity" in source


def test_forbidden_copy_does_not_advise_signing_in():
    source = _read(UI)
    start = source.index("forbidden: {")
    end = source.index("unavailable: {", start)
    block = source[start:end]
    assert "sign in" not in block.lower(), (
        "the forbidden copy tells a signed-in viewer to sign in; that is the conflation"
    )
    assert "signing in again will not change the answer" in block.lower()


# ---------------------------------------------------------------------------
# Negative control: the detector flags the measured pre-repair shape, so it
# cannot be satisfied by a source that reintroduces the defect.
# ---------------------------------------------------------------------------

_PRE_REPAIR_HOOK = '''function stateFor(error: ApiError): HydrationState {
  if (error.kind === "AUTH_REQUIRED") return "auth-required";
  if (error.kind === "FORBIDDEN") return "auth-required";
  if (error.kind === "NETWORK_ERROR" || error.kind === "SERVER_ERROR") return "unavailable";
  return "error";
}'''


def test_detector_reports_the_pre_repair_shape():
    assert forbidden_is_conflated_with_auth_required(_PRE_REPAIR_HOOK) is True


def test_detector_is_silent_on_the_repair_shape():
    assert forbidden_is_conflated_with_auth_required(_read(HOOK)) is False
