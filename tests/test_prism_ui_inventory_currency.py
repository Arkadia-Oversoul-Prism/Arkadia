"""The reconciliation inventory must describe the console that actually exists.

`docs/control-plane/overnight/PRISM-UI-INVENTORY.md` is the roadmap the
reconciliation workstream is chosen from, so a row that says a capability is
`MISSING` while the console already routes to it is not a cosmetic doc defect:
it sends the next pulse to rebuild something that exists.

Measured at `main` `bb19aabd`: five rows carried that defect (`/encyclopedia`,
`/spiral-codex`, `/settings`+`/account`, `/personal-echofeild`, `/dashboard` were
`MISSING` with an empty surface cell while `surfaces.ts` / `router.ts` resolved
them) and three declared surfaces (`/workspace`, `/operator`, `/n-atlas-lab`)
appeared nowhere in the document. Nothing detected either direction.

This module derives its domain from the live declarations rather than restating
them, so a surface added to `surfaces.ts` is judged by the same rule as the ones
present today. It is source-only on purpose: the backend-contract column is
verified against the real route table by other guards, and measuring that table
requires importing `api.main` (see the inventory's §3.1 `PYTHONPATH` caveat).

The controls at the end are the point of the file. A detector that reports the
same verdict for the pre-repair document and the repaired one has not been shown
to detect anything, so the pre-repair rows are fed to it verbatim and the
finding is asserted by name.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SURFACES_TS = REPO_ROOT / "web" / "arkadia_console" / "src" / "lib" / "surfaces.ts"
ROUTER_TS = REPO_ROOT / "web" / "arkadia_console" / "src" / "lib" / "router.ts"
INVENTORY = REPO_ROOT / "docs" / "control-plane" / "overnight" / "PRISM-UI-INVENTORY.md"

MISSING = "MISSING"
IMPLEMENTED_STATES = {"IMPLEMENTED", "PARTIAL"}
ROW_STATUSES = IMPLEMENTED_STATES | {"MISSING", "DEFERRED"}


# ---------------------------------------------------------------------------
# Parsing — every oracle below is read from source, never restated
# ---------------------------------------------------------------------------


def _strip_comment_lines(text: str) -> str:
    """Drop `//` and block-comment lines so a prose example cannot be parsed as a declaration."""
    kept = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if in_block:
            if "*/" in stripped:
                in_block = False
            continue
        if stripped.startswith("/*"):
            in_block = "*/" not in stripped
            continue
        if stripped.startswith("//"):
            continue
        kept.append(line)
    return "\n".join(kept)


def declared_surfaces(surfaces_ts: str) -> dict[str, str]:
    """`SurfaceId -> canonical path`, read from the `SURFACES` declaration."""
    region = _strip_comment_lines(surfaces_ts)
    start = region.index("export const SURFACES")
    region = region[start:]
    surfaces: dict[str, str] = {}
    pending: str | None = None
    for line in region.splitlines():
        id_match = re.match(r'\s*id:\s*"([^"]+)",\s*$', line)
        if id_match:
            pending = id_match.group(1)
            continue
        path_match = re.match(r'\s*path:\s*"([^"]+)",\s*$', line)
        if path_match and pending:
            surfaces[pending] = path_match.group(1)
            pending = None
    if len(surfaces) < 10:
        raise AssertionError(f"parsed only {len(surfaces)} surfaces — the parser has drifted from surfaces.ts")
    return surfaces


def _object_literal(text: str, header: str) -> str:
    stripped = _strip_comment_lines(text)
    start = stripped.index(header)
    end = stripped.index("\n};", start)
    return stripped[start:end]


def path_aliases(router_ts: str) -> dict[str, str]:
    """Legacy inbound path -> surface id, read from `PATH_ALIASES`."""
    body = _object_literal(router_ts, "export const PATH_ALIASES")
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', body))


def lens_aliases(router_ts: str) -> dict[str, str]:
    """Legacy inbound path -> surface id, read from `LENS_ALIASES` (the section is irrelevant here)."""
    body = _object_literal(router_ts, "export const LENS_ALIASES")
    return {
        path: surface
        for path, surface in re.findall(r'"([^"]+)":\s*\{\s*surface:\s*"([^"]+)"', body)
    }


def matrix_rows(inventory: str) -> list[dict[str, object]]:
    """The §2 reconciliation matrix, as structured rows."""
    start = inventory.index("## 2. Route reconciliation matrix")
    end = inventory.index("## 3.", start)
    rows = []
    for line in inventory[start:end].splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            continue
        legacy_routes = [token for token in re.findall(r"`([^`]*)`", cells[0]) if token.startswith("/")]
        surface_tokens = re.findall(r"`([^`]*)`", cells[3])
        named_id = surface_tokens[0] if surface_tokens else None
        named_path = surface_tokens[1] if len(surface_tokens) > 1 else None
        rows.append(
            {
                "legacy": legacy_routes,
                "surface_id": named_id,
                "surface_path": named_path,
                "status": cells[6],
            }
        )
    if len(rows) < 20:
        raise AssertionError(f"parsed only {len(rows)} matrix rows — the parser has drifted from the inventory")
    return rows


def surface_table(inventory: str) -> list[tuple[str, str]]:
    """The `no legacy counterpart` accounting: (surface id, canonical path).

    Both shapes are read so the control can be fed the earlier prose form of this
    section: a table row (`| `id` | `/path` |`) or an inline pair (`id` → `/path`).
    """
    start = inventory.index("no legacy counterpart")
    end = inventory.index("### 2.1", start)
    section = inventory[start:end]
    pairs: list[tuple[str, str]] = []
    for line in section.splitlines():
        match = re.match(r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line)
        if match:
            pairs.append((match.group(1), match.group(2)))
    if not pairs:
        pairs = re.findall(r"`([a-z][a-z0-9-]*)`\s*→\s*`(/[^`]+)`", section)
    return pairs


# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------


def findings(
    surfaces: dict[str, str],
    aliases: dict[str, str],
    lenses: dict[str, str],
    rows: list[dict[str, object]],
    table: list[tuple[str, str]],
) -> list[str]:
    """Every way the inventory can disagree with the console's route declaration."""
    problems: list[str] = []
    path_to_id = {path: surface_id for surface_id, path in surfaces.items()}

    accounted = {str(row["surface_path"]) for row in rows if row["surface_path"]}
    accounted |= {path for _, path in table}
    for surface_id, path in surfaces.items():
        if path not in accounted:
            problems.append(f"surface {surface_id!r} at {path} is not accounted for in the inventory")

    for surface_id, path in table:
        if surface_id not in surfaces:
            problems.append(f"inventory table names undeclared surface {surface_id!r}")
        elif surfaces[surface_id] != path:
            problems.append(
                f"inventory table names {surface_id!r} at {path}, but surfaces.ts declares {surfaces[surface_id]}"
            )

    for row in rows:
        status = str(row["status"])
        surface_id = row["surface_id"]
        surface_path = row["surface_path"]
        label = " ".join(str(route) for route in row["legacy"]) or "<no route>"

        if status not in ROW_STATUSES:
            problems.append(f"row {label} carries an unrecognised status {status!r}")
            continue

        if surface_id and surface_id not in surfaces:
            problems.append(f"row {label} names undeclared surface {surface_id!r}")
        if surface_id and surface_path and surface_id in surfaces and surfaces[surface_id] != surface_path:
            problems.append(
                f"row {label} names {surface_id!r} at {surface_path}, but surfaces.ts declares {surfaces[surface_id]}"
            )

        if status == MISSING and surface_id:
            problems.append(f"row {label} is MISSING but names surface {surface_id!r}")
        if status in IMPLEMENTED_STATES and not surface_id:
            problems.append(f"row {label} is {status} but names no console surface")

        if status != MISSING:
            continue
        for route in row["legacy"]:
            resolved = path_to_id.get(route) or aliases.get(route) or lenses.get(route)
            if resolved is None:
                continue
            problems.append(
                f"row {label} is MISSING, but the console router resolves {route} to {resolved!r}"
            )
            if surface_id and surface_id != resolved:
                problems.append(
                    f"row {label} names {surface_id!r} but {route} resolves to {resolved!r}"
                )
    return problems


# ---------------------------------------------------------------------------
# The live document
# ---------------------------------------------------------------------------


def test_every_declared_surface_is_accounted_for_and_every_claim_is_resolvable():
    surfaces = declared_surfaces(SURFACES_TS.read_text(encoding="utf-8"))
    aliases = path_aliases(ROUTER_TS.read_text(encoding="utf-8"))
    lenses = lens_aliases(ROUTER_TS.read_text(encoding="utf-8"))
    inventory = INVENTORY.read_text(encoding="utf-8")
    problems = findings(surfaces, aliases, lenses, matrix_rows(inventory), surface_table(inventory))
    assert problems == [], "inventory disagrees with the console route declaration:\n" + "\n".join(problems)


def test_the_parser_reads_the_declarations_it_claims_to_read():
    """A parser that returns nothing makes every assertion above vacuous."""
    surfaces = declared_surfaces(SURFACES_TS.read_text(encoding="utf-8"))
    aliases = path_aliases(ROUTER_TS.read_text(encoding="utf-8"))
    lenses = lens_aliases(ROUTER_TS.read_text(encoding="utf-8"))
    assert surfaces["settings"] == "/settings"
    assert surfaces["n-atlas"] == "/n-atlas-lab"
    assert aliases["/account"] == "settings"
    assert aliases["/nexus"] == "novanet"
    assert lenses["/encyclopedia"] == "novanet"
    assert lenses["/spiral-codex"] == "novanet"


# ---------------------------------------------------------------------------
# Controls — the detector must be shown to detect
# ---------------------------------------------------------------------------

PRE_REPAIR_ROWS = [
    {
        "legacy": ["/encyclopedia"],
        "surface_id": None,
        "surface_path": None,
        "status": MISSING,
    },
    {
        "legacy": ["/settings", "/account"],
        "surface_id": None,
        "surface_path": None,
        "status": MISSING,
    },
    {
        # A MISSING row whose route the router does not resolve: the control that
        # proves the detector is not simply reporting every MISSING row.
        "legacy": ["/offerings"],
        "surface_id": None,
        "surface_path": None,
        "status": MISSING,
    },
]


def _live_inputs():
    return (
        declared_surfaces(SURFACES_TS.read_text(encoding="utf-8")),
        path_aliases(ROUTER_TS.read_text(encoding="utf-8")),
        lens_aliases(ROUTER_TS.read_text(encoding="utf-8")),
        matrix_rows(INVENTORY.read_text(encoding="utf-8")),
        surface_table(INVENTORY.read_text(encoding="utf-8")),
    )


def test_negative_control_the_pre_repair_rows_are_reported_and_an_unresolved_row_is_not():
    surfaces, aliases, lenses, rows, table = _live_inputs()
    reported = findings(surfaces, aliases, lenses, PRE_REPAIR_ROWS, table)
    assert any("/encyclopedia" in problem for problem in reported), reported
    assert any("/settings" in problem for problem in reported), reported
    assert not any("/offerings" in problem for problem in reported), reported


def test_planted_defect_reverting_one_repaired_row_is_reported():
    surfaces, aliases, lenses, rows, table = _live_inputs()
    planted = [dict(row) for row in rows]
    for row in planted:
        if "/settings" in [str(route) for route in row["legacy"]]:
            row["surface_id"] = None
            row["surface_path"] = None
            row["status"] = MISSING
    reported = findings(surfaces, aliases, lenses, planted, table)
    assert any("/settings" in problem for problem in reported), reported
    # The same row, unplanted, must be silent.
    assert findings(surfaces, aliases, lenses, rows, table) == []


def test_invented_surface_and_missing_accounting_are_both_reported():
    surfaces, aliases, lenses, rows, table = _live_inputs()
    invented = list(table) + [("dashboard", "/dashboard")]
    reported = findings(surfaces, aliases, lenses, rows, invented)
    assert any("undeclared surface 'dashboard'" in problem for problem in reported), reported

    dropped = [pair for pair in table if pair[0] != "operator"]
    reported = findings(surfaces, aliases, lenses, rows, dropped)
    assert any("'operator'" in problem and "not accounted for" in problem for problem in reported), reported
