"""Engineering Lab — operational authority reading (Workstream 4, Lane 4).

Guards the read-only authority reading added for the Lane-4 reconciliation over
`web/arkadia_console`:

  * the projection is executed for real (node imports the `.ts` and runs it), so
    its behaviour — not a source substring — is what is judged;
  * the fields it reads are pinned to the serving handler
    (`lab/engineering_lab/runtime.py::EngineeringLabRuntime.overview`), so a
    handler rename reddens the guard rather than letting the surface read a
    healthy-looking `unknown`;
  * the load-bearing boundary is proven with **negative controls**: a boolean
    mutation flag that is absent must read `unknown` (never `false`, which would
    imply a closed door), and the mutation path is only "closed" when the handler
    explicitly reports both autonomous merge *and* deploy disabled.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSOLE = REPO_ROOT / "web" / "arkadia_console"
LAB_TREE = CONSOLE / "src" / "components" / "lab"
PROJECTION = LAB_TREE / "labGovernance.ts"
SURFACE = LAB_TREE / "LabAuthorityReadings.tsx"
LAB_PAGE = CONSOLE / "src" / "pages" / "EngineeringLabPage.tsx"
HANDLER = REPO_ROOT / "lab" / "engineering_lab" / "runtime.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(payload: dict) -> dict:
    """Execute the real ``labGovernance.ts`` over *payload* and return the reading."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const view = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify(m.readLabGovernance(view)));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# The shape is the handler's own
# ---------------------------------------------------------------------------


def test_handler_returns_the_authority_block_the_projection_reads():
    """`runtime.overview` must return an `authority` block carrying the keys the
    projection reads. A rename would make the surface read `unknown` (an absence)
    rather than failing loudly."""
    source = _read(HANDLER)
    assert '"authority": {' in source, "runtime.overview no longer returns an authority block"
    for field in (
        "lab_authority_ceiling",
        "autonomous_merge",
        "autonomous_deploy",
        "human_authorization_required",
    ):
        assert f'"{field}"' in source, f"handler no longer declares {field!r}"


def test_handler_returns_the_counts_block_the_projection_reads():
    """The session ladder the projection reads must be the handler's own keys."""
    source = _read(HANDLER)
    assert '"counts": {' in source, "runtime.overview no longer returns a counts block"
    for field in ("sessions", "active", "awaiting_human"):
        assert f'"{field}"' in source, f"handler no longer reports counts.{field!r}"


def test_surface_consumes_the_projection_rather_than_recomputing():
    """The surface is a projection of the reading, not a second implementation."""
    surface = _read(SURFACE)
    assert "readLabGovernance" in surface
    assert "LabGovernanceSource" in surface


def test_lab_page_mounts_the_authority_reading():
    """The reading is actually rendered on the Lab surface, fed the overview it holds."""
    page = _read(LAB_PAGE)
    assert "LabAuthorityReadings" in page
    assert "<LabAuthorityReadings source={" in page


# ---------------------------------------------------------------------------
# Behaviour — the projection is executed, not read
# ---------------------------------------------------------------------------


def test_a_declared_ceiling_reads_as_a_ceiling_not_a_grant():
    """The load-bearing property: the substrate's declared ceiling is reported,
    and the reading does not promote it to a granted authority."""
    reading = run_projection(
        {
            "authority": {
                "lab_authority_ceiling": 2,
                "autonomous_merge": False,
                "autonomous_deploy": False,
                "human_authorization_required": True,
            },
            "counts": {"sessions": 3, "active": 1, "awaiting_human": 2},
        }
    )
    assert reading["ceiling"] == 2
    assert reading["ceiling_reported"] is True
    assert reading["authority_reported"] is True
    assert reading["mutation_closed"] is True
    assert reading["human_gate_declared"] is True
    assert "not a granted authority" in reading["note"]


def test_awaiting_human_is_reported_and_not_accepted():
    """A run at the review boundary is counted as awaiting a human, not as done."""
    reading = run_projection(
        {
            "authority": {
                "lab_authority_ceiling": 2,
                "autonomous_merge": False,
                "autonomous_deploy": False,
                "human_authorization_required": True,
            },
            "counts": {"sessions": 3, "active": 1, "awaiting_human": 2},
        }
    )
    assert reading["awaiting_human"] == 2
    assert reading["active"] == 1


def test_negative_control_absent_flag_is_unknown_not_false():
    """A negative control for the executed behaviour above.

    If the projection coerced a missing boolean to `false`, an unreported
    `autonomous_merge` would read as a *closed* door — the dangerous direction.
    The control asserts an absent flag is `unknown`, and that the mutation path is
    not called closed when only one of the two flags is declared.
    """
    reading = run_projection(
        {
            "authority": {
                "lab_authority_ceiling": 2,
                "autonomous_deploy": False,
                # autonomous_merge deliberately omitted
                "human_authorization_required": True,
            },
            "counts": {},
        }
    )
    assert reading["autonomous_merge"] is None, "an absent flag must not read as false"
    assert reading["authority_reported"] is False
    assert reading["mutation_closed"] is False, "one declared flag is not a closed path"


def test_negative_control_missing_block_reads_unknown():
    """An absent authority block must read as unknown, never as a healthy ceiling."""
    reading = run_projection({})
    assert reading["ceiling"] is None
    assert reading["authority_reported"] is False
    assert reading["mutation_closed"] is False
    assert reading["sessions"] is None
    assert "unknown" in reading["note"]
