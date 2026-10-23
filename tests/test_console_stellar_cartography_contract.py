"""Stellar Cartography contract guard (PRISM-REC-STELLAR-01).

`GET /api/stellar-cartography` is a verified anonymous open read on the canonical
deployment (`200`, no identity) that the console referenced **nowhere**, while the
archived Prism mounted its readout as the header of `NexusSpiralCodex`
(`archive/frontend/arkadia-prism/web/public_prism/src/pages/NexusSpiralCodex.tsx:953`)
— the surface the console now expresses as the NovaNet `codex` lens.

This guard pins the properties that a later edit could silently break. It is a
**source-level** guard, which is this repository's convention for console
contracts; every detector here is paired with a control that runs against the
**real** files, because a detector that is only tested against a synthetic
fixture proves nothing about the code that ships.

The three properties, and why each is worth a test:

1.  **The path is registered once and read through the registry.** The directive
    requires one endpoint registry (§3.1). A literal `/api/stellar-cartography`
    in a component would be a second source of truth, and the console-contract
    wiring gate derives its domain from the tree — a stray literal escapes it.
2.  **The panel is mounted on the lens it indexes.** The archive mounted the
    readout *above* the corpus on one surface. A panel that exists but is
    unreachable is the exact `UNSURFACED` state this slice closes, so the mount is
    asserted, not merely the file's presence.
3.  **A failed read is shown, not swallowed.** The archived component caught
    fetch errors into an empty handler and guarded `setData` on a non-null
    result, so an outage rendered "Calibrating the star date…" **forever**. That
    is the defect a faithful port would have carried, so it gets a detector.

Disjoint from `test_console_spiral_codex_contract.py` (the corpus read on the same
lens) and `test_console_legacy_route_coverage.py` (legacy path dispositions).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONSOLE = REPO / "web" / "arkadia_console" / "src"
PANEL = CONSOLE / "components" / "novaNet" / "StellarCartographyPanel.tsx"
CONTRACT = CONSOLE / "components" / "novaNet" / "stellarCartographyContract.ts"
ENDPOINTS = CONSOLE / "lib" / "endpoints.ts"
NOVANET = CONSOLE / "pages" / "NovaNetPage.tsx"

PATH = "/api/stellar-cartography"

# The archive is source evidence, never code to edit or serve.
ARCHIVE = (
    REPO
    / "archive"
    / "frontend"
    / "arkadia-prism"
    / "web"
    / "public_prism"
    / "src"
)


def _strip_comments(source: str) -> str:
    """Remove `//` and `/* */` comments so prose cannot satisfy a detector.

    A doc comment naming a path is not a request for it. Without this, a comment
    that *mentions* a literal reads as a use of it — the defect already
    measured in this repository on a sibling guard.
    """
    source = re.sub(r"/\*[\s\S]*?\*/", "", source)
    source = re.sub(r"(?m)//.*$", "", source)
    return source


def _code(path: Path) -> str:
    return _strip_comments(path.read_text(encoding="utf-8"))


def _normalise(source: str) -> str:
    """Collapse whitespace so a line-wrapped literal still matches.

    JSX copy is wrapped by the formatter; an exact-substring pin over prose fails
    on correct code once it re-wraps.
    """
    return re.sub(r"\s+", " ", source)


# ── 1. one registry entry, read through it ──────────────────────────────────


def test_path_is_registered_exactly_once() -> None:
    source = _code(ENDPOINTS)
    assert f'"{PATH}"' in source, (
        f"{PATH} must be registered in lib/endpoints.ts; the panel reads it through "
        "the registry rather than a literal"
    )
    assert source.count(f'"{PATH}"') == 1, (
        f"{PATH} appears more than once in the registry — a duplicate entry is a "
        "second source of truth"
    )


def test_no_component_holds_a_literal_copy_of_the_path() -> None:
    """The path is a registry entry, never a component literal."""
    offenders: list[str] = []
    for path in CONSOLE.rglob("*.ts*"):
        if path == ENDPOINTS:
            continue
        if PATH in _code(path):
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == [], (
        f"{PATH} is hard-coded outside the registry in: {offenders}. Read it via "
        "`endpoints.stellarCartography` so the registry stays the single source of truth."
    )


def test_panel_reads_through_the_registry_key() -> None:
    source = _code(PANEL)
    assert "endpoints.stellarCartography" in source, (
        "the panel must read `endpoints.stellarCartography`"
    )


# ── 2. the readout is mounted on the lens it heads ──────────────────────────


def test_panel_is_mounted_on_the_codex_lens() -> None:
    source = _normalise(_code(NOVANET))
    assert "StellarCartographyPanel" in source, "the panel is imported but never mounted"
    assert 'section === "codex"' in source, "the codex lens must still be declared"
    # The mount must be inside the codex branch, not merely present in the file.
    codex_branch = source.split('section === "codex"', 1)[1]
    branch_body = codex_branch[: codex_branch.find(")}") + 1] if ")}" in codex_branch else codex_branch
    assert "StellarCartographyPanel" in branch_body, (
        "StellarCartographyPanel must render inside the `codex` lens branch"
    )


def test_readout_heads_the_corpus_as_in_the_archive() -> None:
    """The archive placed the readout *above* the corpus on one surface."""
    source = _normalise(_code(NOVANET))
    codex_branch = source.split('section === "codex"', 1)[1]
    head = codex_branch.find("StellarCartographyPanel")
    corpus = codex_branch.find("SpiralCodexPanel")
    assert head != -1 and corpus != -1, "both panels must be mounted on the codex lens"
    assert head < corpus, (
        "the readout heads the lens; the corpus follows it (archive order)"
    )


def test_archive_mount_is_evidence_for_this_placement() -> None:
    """Control: the placement claim is grounded in the archive, not asserted."""
    archive_page = ARCHIVE / "pages" / "NexusSpiralCodex.tsx"
    assert archive_page.exists(), "archive evidence must remain readable"
    assert "<StellarCartography />" in archive_page.read_text(encoding="utf-8"), (
        "the archive mounted the readout on NexusSpiralCodex; if this changes, the "
        "placement rationale must be re-derived"
    )


# ── 3. failures are surfaced, not swallowed ─────────────────────────────────


def test_panel_surfaces_read_failures() -> None:
    source = _code(PANEL)
    assert ".catch(" in source, "the read must handle failure"
    # An empty handler is the archive's defect: `catch(() => {})`.
    assert not re.search(r"\.catch\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)", source), (
        "an empty catch swallows the failure — the archive did this and rendered "
        "'Calibrating the star date…' forever"
    )
    assert "ContractState" in source, (
        "failures must be presented through ContractState so an outage is not "
        "rendered as a permanent loading state"
    )
    assert "setState(\"unavailable\")" in source, (
        "a failed read must move the panel out of `loading`"
    )


def test_panel_does_not_recompute_the_readout_client_side() -> None:
    """The Ark Date epoch is not a UTC derivation; a client copy would disagree."""
    source = _code(PANEL)
    assert "Date.now()" not in source and "new Date(" not in source, (
        "the readout is server-derived; computing it client-side would silently "
        "disagree with the kernel's own value"
    )


def test_panel_offers_no_mutation_control() -> None:
    """This slice wires a read. A submit control would imply a contract that is not wired."""
    source = _code(PANEL)
    for verb in ("POST", "PUT", "PATCH", "DELETE"):
        assert verb not in source, f"the read-only panel must not reference {verb}"
    assert "apiRequest" in source, "the read goes through the shared client"


# ── contract module ─────────────────────────────────────────────────────────


def test_shape_guard_rejects_a_truncated_payload() -> None:
    """`isStellarReadout` must reject, so a bad payload is not rendered as undefined."""
    source = _code(CONTRACT)
    assert "export function isStellarReadout" in source, "the shape guard must exist"
    # Every section the panel reads must be part of the shape check.
    for section in (
        "ark_date",
        "schumann",
        "lunar",
        "planetary",
        "cosmic_weather",
        "oversoul_blind_pull",
        "galactica",
    ):
        assert section in source, f"the shape guard must check `{section}`"


def test_shape_guard_is_actually_used_by_the_panel() -> None:
    source = _code(PANEL)
    assert "isStellarReadout(" in source, (
        "the shape guard must be invoked; defining it without calling it is dead code"
    )


def test_sky_order_is_fixed() -> None:
    """A map iteration order would make two renders of one readout disagree."""
    source = _code(CONTRACT)
    assert "SKY_ORDER" in source and "orderedBodies" in source, (
        "the planetary sky must be ordered explicitly"
    )
    assert _code(PANEL).count("orderedBodies(") >= 1, "the panel must use the ordering helper"


def test_refresh_interval_is_bounded() -> None:
    """A poll tighter than the kernel's resolution is load for no new information."""
    source = _code(CONTRACT)
    match = re.search(r"STELLAR_REFRESH_MS\s*=\s*([0-9_]+)", source)
    assert match, "the refresh interval must be a named constant"
    value = int(match.group(1).replace("_", ""))
    assert value >= 60_000, (
        f"STELLAR_REFRESH_MS={value} polls faster than the readout changes "
        "(the finest subdivision is the 48/day breath)"
    )
