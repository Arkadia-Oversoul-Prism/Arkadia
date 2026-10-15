"""Lane 2 — NovaNet public-field composer (create a transmission).

The archived Prism field (`archive/frontend/arkadia-prism/web/public_prism/src/
pages/SocialFieldVerified.tsx`) opened with a composer gated on the verified
identity (``canTransmit = isAuthenticated && profile``) that ``POST``ed a new
public transmission. The console reconciled the field's *read* side (engagement
readings, author controls, live react / comment writes) but never rendered the
create path, so an authenticated reader could reply to a post yet not originate
one.

The contract is live and verified on `api/transmissions.py`:

  * ``POST /api/transmissions`` — body ``{content, author}``; blank content is
    refused with 400; the response is ``{"transmission": {...}}``.

This guard pins the **create** contract on the active console:

  * exactly **one** write path — the collection ``POST`` — is composed;
  * the path is registry-derived (`endpoints.transmissions`), never an inline
    literal;
  * the composer renders a control **only** when the caller is authenticated, and
    states the sign-in requirement otherwise (it does not offer a control the
    archived gate withheld);
  * on success the page re-reads the feed, so the server's own list and count are
    shown rather than a client-appended optimistic row.

These are **source-level** assertions against the active console, matching the
established convention for console contract guards
(`tests/test_prism_novanet_engagement_readings.py`,
`tests/test_prism_novanet_author_controls.py`). Each behavioural claim carries a
**negative control** — a synthetic source that violates it must be reported by
the same detector that judges the live tree.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
PAGE = CONSOLE / "pages" / "NovaNetPage.tsx"
COMPOSER = CONSOLE / "components" / "novaNet" / "TransmissionComposer.tsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_composer_exists_and_composes_one_write_path():
    """The create surface exists and calls ``apiRequest`` exactly once (the POST)."""
    src = _read(COMPOSER)
    assert "export function TransmissionComposer" in src
    calls = re.findall(r"apiRequest[^\n]*?\(([^,]+),", src)
    assert len(calls) == 1, f"expected exactly one write call, found {len(calls)}: {calls}"
    assert re.search(r'method:\s*"POST"', src), "the compose call must be a POST"


def test_compose_path_is_registry_derived_not_a_literal():
    """The path is the registry's collection, never an inline literal."""
    src = _read(COMPOSER)
    assert "endpoints.transmissions" in src, "the path base must be the registry collection"
    assert not re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', src), (
        "the create path must not be an inline literal"
    )


def test_composer_never_invents_ownership_client_side():
    """The client mirrors the archived gate; it does not fabricate the author id."""
    src = _read(COMPOSER)
    # The author block is projected from the verified profile, not a fabricated uid.
    assert "owner_uid" not in src, "the client must not send an owner_uid it decides"


def test_composer_is_gated_on_the_verified_identity():
    """An anonymous reader is told to sign in, not offered a decorative control."""
    src = _read(COMPOSER)
    assert "if (!isAuthenticated)" in src, "the composer must gate on the verified identity"
    assert re.search(r'data-testid="novanet-transmit-signin"', src), (
        "the anonymous state must be stated, not silently hidden"
    )
    assert re.search(r'data-testid="novanet-transmit-composer"', src), (
        "the authenticated composer must render"
    )


def test_compose_reports_refusal_honestly():
    """A rejected write is surfaced, and the blank submit is blocked client-side."""
    src = _read(COMPOSER)
    assert "AUTH_REQUIRED" in src, "an auth failure must be named, not shown as a fault"
    assert re.search(r'data-testid="novanet-transmit-error"', src), (
        "a refusal must render a visible error"
    )
    assert "!text.trim()" in src, "a blank transmission must not be submittable"


def test_page_mounts_the_composer_and_reloads_after_transmit():
    """The field renders the composer and re-reads the feed after a create."""
    src = _read(PAGE)
    assert "TransmissionComposer" in src, "the NovaNet field must render the composer"
    assert re.search(r"<TransmissionComposer[\s\S]*?onCreated=\{\(\) => field\.reload\(\)\}", src), (
        "a create must re-read the feed so the server's own list is shown"
    )
    assert re.search(r"isAuthenticated=\{isAuthenticated\}", src), (
        "the page must pass the verified-identity gate to the composer"
    )


# ---------------------------------------------------------------------------
# Detectors — the same predicate applied to the live tree and to a defect
# ---------------------------------------------------------------------------

_POST_METHOD = re.compile(r'method:\s*"POST"')
_SIGNIN = re.compile(r'data-testid="novanet-transmit-signin"')
_ERROR = re.compile(r'data-testid="novanet-transmit-error"')


def _multi_path_defect(source: str) -> bool:
    """True when the composer wires a write path beyond the one collection POST."""
    calls = re.findall(r"apiRequest[^\n]*?\(([^,]+),", source)
    return "export function TransmissionComposer" in source and len(calls) != 1


def _inline_path_defect(source: str) -> bool:
    """True when the create path is an inline literal rather than registry-derived."""
    return "export function TransmissionComposer" in source and (
        re.search(r'apiRequest[^\n]*\(\s*["\'`]/api/transmissions', source) is not None
        or "endpoints.transmissions" not in source
    )


def _ungated_defect(source: str) -> bool:
    """True when an anonymous reader is offered the composer instead of a sign-in note."""
    return "export function TransmissionComposer" in source and not _SIGNIN.search(source)


def _silent_refusal_defect(source: str) -> bool:
    """True when a refusal is swallowed and never rendered."""
    return "export function TransmissionComposer" in source and not _ERROR.search(source)


def _unmounted_defect(source: str) -> bool:
    """True when the NovaNet field no longer renders the composer."""
    return "SurfaceLenses" in source and "TransmissionComposer" not in source


def test_detectors_are_silent_on_the_live_tree():
    assert not _multi_path_defect(_read(COMPOSER))
    assert not _inline_path_defect(_read(COMPOSER))
    assert not _ungated_defect(_read(COMPOSER))
    assert not _silent_refusal_defect(_read(COMPOSER))
    assert not _unmounted_defect(_read(PAGE))


def test_detector_flags_a_second_write_path():
    """Negative control: an invented delete path alongside the create POST."""
    defect = (
        "export function TransmissionComposer({ isAuthenticated }) {\n"
        '  if (!isAuthenticated) return "sign in";\n'
        '  apiRequest(`${endpoints.transmissions}`, { method: "POST" });\n'
        '  apiRequest(`${endpoints.transmissions}/x`, { method: "DELETE" });\n'
        '  return <p data-testid="novanet-transmit-signin" />;\n'
        "}\n"
    )
    # Give it the honest-refusal marker so only the multi-path detector fires.
    defect += 'const x = <p data-testid="novanet-transmit-error" />;\n'
    assert _multi_path_defect(defect), "the multi-path detector missed a second write"


def test_detector_flags_an_inline_path():
    """Negative control: a create path that bypasses the registry."""
    defect = (
        "export function TransmissionComposer({ isAuthenticated }) {\n"
        '  apiRequest("/api/transmissions", { method: "POST" });\n'
        '  return <p data-testid="novanet-transmit-signin" />;\n'
        "}\n"
        'const x = <p data-testid="novanet-transmit-error" />;\n'
    )
    assert _inline_path_defect(defect), "the inline-path detector missed a literal route"


def test_detector_flags_an_ungated_composer():
    """Negative control: the composer renders for an anonymous reader."""
    defect = (
        "export function TransmissionComposer() {\n"
        '  apiRequest(endpoints.transmissions, { method: "POST" });\n'
        '  return <div data-testid="novanet-transmit-composer" />;\n'
        "}\n"
    )
    assert _ungated_defect(defect), "the gate detector missed an ungated composer"


def test_detector_flags_a_silent_refusal():
    """Negative control: a rejected write disappears without a message."""
    defect = (
        "export function TransmissionComposer({ isAuthenticated }) {\n"
        "  if (!isAuthenticated) return null;\n"
        '  apiRequest(endpoints.transmissions, { method: "POST" }).catch(() => {});\n'
        '  return <p data-testid="novanet-transmit-signin" />;\n'
        "}\n"
    )
    assert _silent_refusal_defect(defect), "the refusal detector missed a swallowed error"


def test_detector_flags_the_unmounted_composer():
    """Negative control: the field stops rendering the composer."""
    defect = "export function NovaNetPage() { return <SurfaceLenses />; }\n"
    assert _unmounted_defect(defect), "the mount detector missed a dropped composer"
