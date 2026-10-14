"""Arkana thread timestamps — the reading is zone-independent (Workstream 4).

The thread contract's timestamps come off the Knowledge OS columns, whose default
is SQLite's `datetime('now')`: `YYYY-MM-DD HH:MM:SS` in **UTC**, with no zone
designator, passed through unchanged by `api/commune_threads.py`. Per ECMA-262 a
zoneless date-time is read as *local* time, so the obvious
`new Date(value.replace(" ", "T"))` places the same stored instant at a different
moment in every zone — and is accidentally correct on a UTC host, which is why a
green build never notices.

This guard **executes the shipped module** through Node (this repository's
frontend convention — see `tests/test_prism_w4_run_evidence_trace.py`), so the
thing judged is the module that reaches the browser, not a re-implementation of
it. It asserts:

  * the stored value resolves to the **same instant** under four different `TZ`
    values — the property the defect violates;
  * the rendered reading **names the reader's zone**, so a displayed time is
    never ambiguous about which clock it is on;
  * an unreadable value is surfaced verbatim rather than dropped or guessed;
  * the premise itself: SQLite's `datetime('now')` really is UTC, and the schema
    really does use it for these columns.

A negative control runs the **pre-repair** body through the same probe and
asserts it *does* move across zones — so the detector is proven to detect the
defect it exists to catch, rather than passing on any implementation at all.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
ARKANA = CONSOLE / "src" / "components" / "arkana"
MODULE = ARKANA / "arkanaThreadTime.ts"
COMPONENT = ARKANA / "ArkanaThreadHistory.tsx"
SCHEMA = ROOT / "knowledge" / "schema.sql"

#: The same stored instant, read from four zones that span the offsets.
ZONES = ("UTC", "America/New_York", "Europe/London", "Asia/Kolkata")

STORED = "2026-10-14 06:06:12"

#: The body this slice replaced, kept verbatim so the control measures the real defect.
PRE_REPAIR_BODY = """export function readableTime(value) {
  if (!value) return "-";
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}
"""

_PROBE = (
    "const m = await import(process.argv[1]);\n"
    "const values = JSON.parse(process.argv[2]);\n"
    "process.stdout.write(JSON.stringify(values.map((v) => {\n"
    "  const text = m.readableTime(v);\n"
    "  const n = m.normalizeTimestamp(v);\n"
    "  return { text, ms: new Date(n).getTime() };\n"
    "})));\n"
)


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the reading cannot be executed here")
    return found


def run_readings(module_path: Path, values: list[str], zone: str) -> list[dict]:
    """Execute *module_path* under *zone* and return each reading's text + instant."""
    completed = subprocess.run(
        [_node(), "--input-type=module", "-e", _PROBE, module_path.as_uri(), json.dumps(values)],
        capture_output=True,
        text=True,
        timeout=60,
        env={**_clean_env(), "TZ": zone},
    )
    if completed.returncode != 0:
        pytest.fail(f"reading execution failed under TZ={zone}: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


def _clean_env() -> dict:
    import os

    return dict(os.environ)


@pytest.fixture(scope="module")
def readings_by_zone() -> dict[str, list[dict]]:
    """The shipped module's reading of the stored value, per zone."""
    return {zone: run_readings(MODULE, [STORED], zone) for zone in ZONES}


# ---------------------------------------------------------------------------
# The property the defect violates
# ---------------------------------------------------------------------------


def test_the_stored_instant_is_identical_in_every_zone(readings_by_zone):
    instants = {zone: readings[0]["ms"] for zone, readings in readings_by_zone.items()}
    assert len(set(instants.values())) == 1, f"the reading moved across zones: {instants}"
    # And it is the instant the column actually holds: 06:06:12 UTC.
    expected = int(datetime(2026, 10, 14, 6, 6, 12, tzinfo=timezone.utc).timestamp() * 1000)
    assert instants["UTC"] == expected


def test_the_reading_names_the_readers_zone(readings_by_zone):
    for zone, readings in readings_by_zone.items():
        text = readings[0]["text"]
        assert text and text != STORED, f"{zone}: the value was not rendered"
        # A short-offset zone label (`GMT-4`, `GMT+5:30`) must be present, so the
        # reader can tell which clock the shown time is on.
        assert "GMT" in text, f"{zone}: the reading carries no zone label: {text!r}"


def test_each_zone_renders_its_own_clock(readings_by_zone):
    """The label is not decoration: the rendered wall-clock really is the local one."""
    assert readings_by_zone["America/New_York"][0]["text"].startswith("10/14/2026, 2:06:12")
    assert readings_by_zone["Asia/Kolkata"][0]["text"].startswith("10/14/2026, 11:36:12")


def test_an_unreadable_value_is_surfaced_not_dropped():
    readings = run_readings(MODULE, ["", "not-a-timestamp"], "UTC")
    assert readings[0]["text"] == "—"
    assert "not-a-timestamp" in readings[1]["text"]


def test_a_value_that_already_states_its_zone_is_left_alone():
    """Guessing a zone for a value that states one would move the instant."""
    readings = run_readings(MODULE, ["2026-10-14T06:06:12Z", "2026-10-14T06:06:12+02:00"], "UTC")
    assert readings[0]["ms"] == int(datetime(2026, 10, 14, 6, 6, 12, tzinfo=timezone.utc).timestamp() * 1000)
    assert readings[1]["ms"] == int(datetime(2026, 10, 14, 6, 6, 12, tzinfo=timezone.utc).timestamp() * 1000) - 7200000


# ---------------------------------------------------------------------------
# Negative control — the detector fires on the defect it exists to catch
# ---------------------------------------------------------------------------


def test_negative_control_the_pre_repair_body_moves_across_zones(tmp_path):
    """The replaced body must fail the property, or the guard proves nothing."""
    pre_repair = tmp_path / "preRepair.ts"
    pre_repair.write_text(PRE_REPAIR_BODY, encoding="utf-8")

    # `normalizeTimestamp` does not exist on the control, so read the raw text only.
    program = (
        "const m = await import(process.argv[1]);\n"
        "process.stdout.write(m.readableTime(process.argv[2]));\n"
    )
    rendered = {}
    for zone in ("America/New_York", "Asia/Kolkata"):
        completed = subprocess.run(
            [_node(), "--input-type=module", "-e", program, pre_repair.as_uri(), STORED],
            capture_output=True,
            text=True,
            timeout=60,
            env={**_clean_env(), "TZ": zone},
        )
        assert completed.returncode == 0, completed.stderr
        rendered[zone] = completed.stdout.strip()

    # Both zones print the same wall-clock, i.e. the same stored UTC value read as
    # if it were local — the defect, reproduced.
    assert rendered["America/New_York"] == rendered["Asia/Kolkata"], (
        f"the control did not reproduce the defect: {rendered}"
    )
    # And the shipped module disagrees with the control, so the repair is load-bearing.
    assert run_readings(MODULE, [STORED], "Asia/Kolkata")[0]["text"] != rendered["Asia/Kolkata"]


# ---------------------------------------------------------------------------
# The premise: the column really is zoneless UTC
# ---------------------------------------------------------------------------


def test_sqlite_datetime_now_is_utc():
    connection = sqlite3.connect(":memory:")
    stored = connection.execute("SELECT datetime('now')").fetchone()[0]
    connection.close()

    # `datetime('now')` is UTC; a naive parse of the stored string must land within
    # a minute of the true UTC instant and hours away from a UTC+5:30 misreading.
    parsed = datetime.strptime(stored, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    drift = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert drift < 60, f"datetime('now') is not UTC: {stored!r} drifted {drift}s"


def test_the_thread_columns_default_to_that_form():
    schema = SCHEMA.read_text(encoding="utf-8")
    threads = schema.split("CREATE TABLE IF NOT EXISTS threads", 1)[1].split(");", 1)[0]
    for column in ("created_at", "updated_at"):
        line = next(l for l in threads.splitlines() if column in l)
        assert "datetime('now')" in line, f"{column} no longer defaults to UTC: {line.strip()}"


# ---------------------------------------------------------------------------
# The surface reads through the one module (source level)
# ---------------------------------------------------------------------------


def test_the_surface_reads_through_the_canonical_module():
    component = COMPONENT.read_text(encoding="utf-8")
    assert 'from "./arkanaThreadTime"' in component
    assert "readableTime(" in component
    # The local definition must be gone: two readings would drift apart.
    assert "function readableTime" not in component
    assert "new Date(normalized)" not in component


def test_the_guard_is_selected_by_the_console_contract_domain():
    """A guard no gate executes is decoration."""
    sys_path = ROOT / "scripts" / "console_contract_domain.py"
    completed = subprocess.run(
        ["python", str(sys_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    domain = completed.stdout.split()
    assert "tests/test_prism_w4_arkana_thread_time_truth.py" in domain
