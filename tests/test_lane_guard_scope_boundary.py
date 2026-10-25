"""Guard the scope probe: its control must pass, and it must bite on a bad resolver.

`scripts/lane_scope_probe.py` encodes the invariant that the lanes a guard enforces
against must not be altered by the live PR activity being evaluated. It is the
acceptance test for any repair of that defect, so the probe itself needs a guard --
otherwise a later edit could make its checks vacuous and the "repair" would pass by
examining nothing.

Deliberately **not** asserted here: that the shipped implementation passes the probe.
It does not (three of four checks fail at `3a1088c5`), and asserting that would
manufacture a permanently failing node that goes green only when the guard is repaired
-- a strict-xfail-shaped trap. The probe is run directly to judge a candidate; this
file only proves the probe can still tell a conforming design from a non-conforming one.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "lane_scope_probe.py"


def _load():
    spec = importlib.util.spec_from_file_location("lane_scope_probe", PROBE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lane_scope_probe"] = module
    spec.loader.exec_module(module)
    return module


def test_probe_control_passes_on_a_conforming_design():
    """The checks must be satisfiable, or a failure on the shipped design proves nothing."""
    probe = _load()
    results = probe.run(probe.conforming_scope)
    failed = [r["name"] for r in results if not r["passed"]]
    assert not failed, f"checks unsatisfiable on a conforming design: {failed}"


def test_probe_bites_on_a_nonconforming_resolver():
    """A resolver that lets PR activity remove a lane must be reported as failing."""
    probe = _load()

    def leaky_scope(state):
        # Mirrors the shipped shape: a lane that defers leaves the enforced set.
        return sorted(
            n for n, lane in state.get("lanes", {}).items()
            if lane.get("doc_guard") == "current"
        )

    results = probe.run(leaky_scope)
    failed = [r["name"] for r in results if not r["passed"]]
    assert failed, "the probe did not report a non-conforming resolver -- it is disarmed"
    assert any("exempt its own lane" in name for name in failed), (
        f"the lane-exemption check did not bite; failures were: {failed}"
    )


def test_probe_is_wired_to_the_shipped_implementation():
    """`shipped_scope` must delegate to the real guard, not a stub.

    This is the anti-disarm property. Without it, swapping `shipped_scope` for a
    conforming stub would make the probe pass while examining nothing -- the exact
    failure mode the probe exists to detect. Asserting *identity with the shipped
    function's behaviour* (rather than asserting the defect is present) keeps this
    test valid after a repair: once the guard is fixed, both sides still agree.
    """
    probe = _load()
    sys.path.insert(0, str(ROOT / "scripts"))
    import lane_state  # noqa: E402

    state = {"lanes": {"1": {"doc": "a.md", "doc_guard": "current"},
                       "2": {"doc": "b.md", "doc_guard": "deferred"}}}
    assert probe.shipped_scope(state) == sorted(lane_state.current_lanes(state)), (
        "shipped_scope no longer matches lane_state.current_lanes -- the probe is no "
        "longer judging the shipped implementation"
    )


def test_cli_exit_code_agrees_with_the_shipped_verdict():
    """The CLI's exit code must reflect what the checks found, in either state.

    Deliberately not pinned to exit 1. Pinning it would manufacture a node that only
    goes green when the guard is repaired -- a trap for the repair PR. The invariant
    asserted is the *agreement* between the CLI verdict and the checks, which holds
    before and after a repair.
    """
    import subprocess

    probe = _load()
    failed = [r for r in probe.run(probe.shipped_scope) if not r["passed"]]

    proc = subprocess.run([sys.executable, str(PROBE)], capture_output=True, text=True,
                          cwd=ROOT)
    assert proc.returncode == (1 if failed else 0), (
        f"CLI exit {proc.returncode} disagrees with {len(failed)} failing check(s)\n"
        + proc.stdout
    )


def test_probe_cli_selftest_exits_zero():
    import subprocess

    proc = subprocess.run([sys.executable, str(PROBE), "--selftest"],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stdout + proc.stderr
