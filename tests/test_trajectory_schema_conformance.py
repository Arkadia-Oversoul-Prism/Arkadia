"""Every trajectory move status must be one the schema and router both recognise.

The sibling guard `tests/test_scheduler_trajectory_conformance.py` proves a
scheduled trajectory is *structurally* loadable. This guard proves the move
*status vocabulary* is coherent across the three surfaces that must agree:

* `docs/control-plane/trajectory.schema.json` — the frozen contract,
* `weaver/engineering_router.py` — `ACTIVE_STATUSES` / `TERMINAL_DONE`, and
* every live `docs/control-plane/TRAJECTORY-*.yaml` instance.

Measured on `main` @ `451e41a`, the live scheduler target
(`TRAJECTORY-CONSOLE-COMPLETION-01.yaml`) carried `in_progress` and
`merged_acceptance_pending`, neither of which the schema enum admitted, while the
router used `in_progress` and `merged`. A trajectory can therefore be
structurally valid and still contradict the frozen contract.

The guard is deliberately **stdlib-only**: it reads the JSON schema with `json`
and extracts move statuses with a small YAML reader rather than `jsonschema` or
`pyyaml`. The only test that previously validated against the schema
(`tests/test_m08_trajectory_schema.py`) skips when `jsonschema` is absent, which
is why the divergence reached `main` unjudged. A guard that can be skipped for a
missing install is decoration; this one runs under `pip install pytest` alone.

Negative controls prove the reader detects the defect it claims to detect: an
out-of-enum status is surfaced, multiple moves are read, and a `moves` list
nested under `trajectory:` is not mistaken for the canonical top-level list.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/control-plane/trajectory.schema.json"
CONTROL_PLANE = ROOT / "docs/control-plane"

_ITEM_START_RE = re.compile(r"^(\s*)-\s+(\w[\w-]*):\s*(.*)$")
_ITEM_KEY_RE = re.compile(r"^(\s*)([\w-]+):\s*(.*)$")


def _schema_move_enum() -> set[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"]["moves"]["items"]["properties"]["status"]["enum"])


def _router_vocabulary() -> set[str]:
    from weaver.engineering_router import ACTIVE_STATUSES, TERMINAL_DONE

    return set(ACTIVE_STATUSES) | set(TERMINAL_DONE)


def _trajectory_files() -> list[Path]:
    return sorted(CONTROL_PLANE.glob("TRAJECTORY-*.yaml"))


def _unquote(value: str) -> str:
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    return value


def _moves_block_lines(text: str) -> list[str] | None:
    """Lines of the canonical top-level `moves:` sequence, or None if absent.

    Only an unindented `moves:` key is the canonical list; a `moves` nested under
    `trajectory:` (the structural slip the sibling guard rejects) is not.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("moves:"):
            start = i + 1
            break
    if start is None:
        return None
    block: list[str] = []
    for line in lines[start:]:
        if not line:
            block.append(line)
            continue
        # A top-level mapping key ends the sequence. Sequence items may sit at
        # column 0 (`- id:`) or be indented, so a leading `-` is content, not a
        # terminator.
        if not line[0].isspace() and not line.lstrip().startswith(("-", "#")):
            break
        block.append(line)
    return block


def _extract_move_statuses(text: str) -> list[dict[str, str | None]] | None:
    """Read `id`/`status` for each move in the canonical top-level list."""
    block = _moves_block_lines(text)
    if block is None:
        return None
    moves: list[dict[str, str | None]] = []
    current: dict[str, str | None] | None = None
    for line in block:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        start = _ITEM_START_RE.match(line)
        if start:
            current = {"id": None, "status": None}
            moves.append(current)
            key, value = start.group(2), start.group(3)
            if key in ("id", "status"):
                current[key] = _unquote(value)
            continue
        key_match = _ITEM_KEY_RE.match(line)
        if key_match and current is not None:
            key, value = key_match.group(2), key_match.group(3)
            if key in ("id", "status"):
                current[key] = _unquote(value)
    return moves


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_negative_control_reader_flags_an_out_of_enum_status():
    text = "trajectory:\n  id: T\nmoves:\n  - id: X\n    status: not_a_real_status\n"
    moves = _extract_move_statuses(text)
    assert moves == [{"id": "X", "status": "not_a_real_status"}]
    assert "not_a_real_status" not in _schema_move_enum()


def test_negative_control_reader_reads_every_move():
    text = (
        "moves:\n"
        "  - id: A\n    status: pending\n"
        "  - id: B\n    status: in_progress\n"
    )
    assert _extract_move_statuses(text) == [
        {"id": "A", "status": "pending"},
        {"id": "B", "status": "in_progress"},
    ]


def test_negative_control_reader_ignores_a_nested_moves_list():
    text = "trajectory:\n  moves:\n    - id: X\n      status: bogus\n"
    assert _extract_move_statuses(text) is None


# ---------------------------------------------------------------------------
# The invariants
# ---------------------------------------------------------------------------


def test_schema_move_enum_covers_the_router_vocabulary():
    """The router's own statuses must be schema-legal.

    A status the router can emit or act on but the schema rejects makes the
    frozen contract and the executed behaviour disagree.
    """
    enum = _schema_move_enum()
    vocabulary = _router_vocabulary()
    assert vocabulary <= enum, (
        f"router statuses absent from the schema enum: {sorted(vocabulary - enum)}"
    )


@pytest.mark.parametrize("path", _trajectory_files(), ids=lambda p: p.name)
def test_trajectory_move_statuses_are_in_the_schema_enum(path: Path):
    moves = _extract_move_statuses(path.read_text(encoding="utf-8"))
    assert moves, f"{path.name}: no moves parsed from the canonical list"
    enum = _schema_move_enum()
    for move in moves:
        assert move["id"], f"{path.name}: a move is missing its id"
        assert move["status"], f"{path.name}: move {move['id']} is missing its status"
        assert move["status"] in enum, (
            f"{path.name}: move {move['id']} status {move['status']!r} is not in "
            f"the schema enum {sorted(enum)}"
        )
