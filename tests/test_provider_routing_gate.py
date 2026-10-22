"""Controls for the provider-routing regression attribution gate.

These are the gate's own tests. They exist so the gate cannot be disarmed by
editing it: each control feeds it the exact evidence shape it must handle, and
asserts the verdict *and* the exit code, because the exit code is what a workflow
reads.

Every "false-pass" control below is a shape that could otherwise be read as
"no failures". A gate that answers PASS for any of them is worse than no gate.

Run: python -m pytest tests/test_provider_routing_gate.py -q
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from provider_routing_gate import (  # noqa: E402
    EXIT, FAIL, INCONCLUSIVE, PASS, compare, executed_count, merge_base,
)

BASE_SHA = "04e1b83b89e51a994af68b529a1076665f9b3ae5"
COMMAND = "python -m pytest tests/ -q -rEf --continue-on-collection-errors"
ENVIRONMENT = {"python": "3.11", "command": COMMAND,
               "dependency_source": "requirements.txt"}

# A representative baseline: three failing nodes and one collection error.
BASELINE_LOG = """\
tests/test_a.py ..F
tests/test_b.py .E
FAILED tests/test_a.py::test_alpha
FAILED tests/test_a.py::test_beta
FAILED tests/test_c.py::test_gamma
ERROR tests/test_autonomy.py
3 failed, 40 passed, 2 skipped, 1 error in 12.34s
"""

CANDIDATE_LOG = BASELINE_LOG


@pytest.fixture
def baseline(tmp_path):
    log = tmp_path / "baseline.log"
    log.write_text(BASELINE_LOG)
    from baseline_fingerprint import extract, fingerprint
    _, ids = extract(str(log))
    record = {
        "schema": "arkadia.provider-routing-baseline/1",
        "source_sha": BASE_SHA,
        "environment": dict(ENVIRONMENT),
        "log": str(log),
        "nodes": len(ids),
        "ids_fingerprint": fingerprint(ids),
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(record))
    return json.loads(path.read_text())


def run(candidate_text, tmp_path, *, record=None, env=None, base_sha=BASE_SHA,
        name="candidate.log"):
    log = tmp_path / name
    log.write_text(candidate_text)
    return compare(baseline=record, candidate_log=str(log),
                   candidate_env=env or ENVIRONMENT,
                   candidate_base_sha=base_sha)


def record_for(tmp_path, log_text, name="base.log"):
    log = tmp_path / name
    log.write_text(log_text)
    from baseline_fingerprint import extract, fingerprint
    _, ids = extract(str(log))
    return {"schema": "arkadia.provider-routing-baseline/1",
            "source_sha": BASE_SHA, "environment": dict(ENVIRONMENT),
            "log": str(log), "nodes": len(ids),
            "ids_fingerprint": fingerprint(ids)}


# ---------------------------------------------------------------------------
# the core distinction: pre-existing debt vs an introduced regression
# ---------------------------------------------------------------------------

def test_identical_run_passes_and_reports_debt_unchanged(baseline, tmp_path):
    r = run(CANDIDATE_LOG, tmp_path, record=baseline)
    assert r["verdict"] == PASS
    assert EXIT[r["verdict"]] == 0
    assert len(r["unchanged"]) == 4
    assert r["newly_failing"] == []


def test_introduced_regression_fails_and_keeps_debt_unchanged(baseline, tmp_path):
    """The deliverable's whole purpose."""
    r = run(CANDIDATE_LOG + "FAILED tests/test_new.py::test_regression\n",
            tmp_path, record=baseline)
    assert r["verdict"] == FAIL
    assert EXIT[r["verdict"]] == 1
    assert r["newly_failing"] == ["tests/test_new.py::test_regression"]
    assert len(r["unchanged"]) == 4      # debt retained, not reported as regression


def test_resolved_failure_is_not_a_regression(baseline, tmp_path):
    text = (CANDIDATE_LOG
            .replace("FAILED tests/test_a.py::test_beta\n", "")
            .replace("3 failed, 40 passed", "2 failed, 41 passed"))
    r = run(text, tmp_path, record=baseline)
    assert r["verdict"] == PASS
    assert r["newly_failing"] == []
    assert r["resolved"] == ["tests/test_a.py::test_beta"]
    assert len(r["unchanged"]) == 3


def test_failure_to_error_class_shift_is_reported_not_a_regression(baseline, tmp_path):
    """A node that flips FAILED<->ERROR is a diagnostic, not a new failure."""
    # The summary must stay consistent with the outcome lines, otherwise the log
    # is the internally-inconsistent shape the gate refuses. A FAILED->ERROR flip
    # moves one node from `failed` to `errors`.
    text = (CANDIDATE_LOG
            .replace("FAILED tests/test_a.py::test_alpha\n",
                     "ERROR tests/test_a.py::test_alpha\n")
            .replace("3 failed, 40 passed, 2 skipped, 1 error",
                     "2 failed, 40 passed, 2 skipped, 2 errors"))
    r = run(text, tmp_path, record=baseline)
    assert r["verdict"] == PASS
    assert r["newly_failing"] == []
    assert r["class_shift"] == ["tests/test_a.py::test_alpha"]


# ---------------------------------------------------------------------------
# fail-closed: absent, stale, incomparable
# ---------------------------------------------------------------------------

def test_absent_baseline_is_inconclusive_not_pass(tmp_path):
    r = run(CANDIDATE_LOG, tmp_path, record=None)
    assert r["verdict"] == INCONCLUSIVE
    assert EXIT[r["verdict"]] == 2


def test_stale_baseline_sha_is_inconclusive(baseline, tmp_path):
    r = run(CANDIDATE_LOG, tmp_path, record=baseline, base_sha="b" * 40)
    assert r["verdict"] == INCONCLUSIVE
    assert any("STALE" in x for x in r["reasons"])


def test_baseline_without_source_sha_is_inconclusive(tmp_path):
    rec = record_for(tmp_path, BASELINE_LOG)
    del rec["source_sha"]
    assert run(CANDIDATE_LOG, tmp_path, record=rec)["verdict"] == INCONCLUSIVE


@pytest.mark.parametrize("key,value", [
    ("python", "3.13"),
    ("command", "pytest tests/ -q"),
    ("dependency_source", "pyproject.toml"),
])
def test_environment_mismatch_is_inconclusive(baseline, tmp_path, key, value):
    r = run(CANDIDATE_LOG, tmp_path, record=baseline, env={**ENVIRONMENT, key: value})
    assert r["verdict"] == INCONCLUSIVE
    assert any(key in x for x in r["reasons"])


# ---------------------------------------------------------------------------
# false-pass guards: a run that executed nothing must never read as clean
# ---------------------------------------------------------------------------

def test_empty_candidate_log_is_inconclusive(baseline, tmp_path):
    assert run("", tmp_path, record=baseline)["verdict"] == INCONCLUSIVE


def test_whitespace_only_candidate_log_is_inconclusive(baseline, tmp_path):
    assert run("   \n\n  ", tmp_path, record=baseline)["verdict"] == INCONCLUSIVE


def test_zero_tests_executed_is_inconclusive(baseline, tmp_path):
    """The CE-01 shape: pytest aborts at collection and runs nothing."""
    r = run("ERROR tests/test_autonomy.py\n"
            "Interrupted: 1 error during collection\n"
            "1 skipped, 1 error in 2.96s\n", tmp_path, record=baseline)
    assert r["verdict"] == INCONCLUSIVE
    assert any("interrupted" in x.lower() or "0 tests" in x for x in r["reasons"])


def test_collection_abort_with_passing_tests_is_inconclusive(baseline, tmp_path):
    r = run("ERROR tests/test_autonomy.py\n"
            "Interrupted: 1 error during collection\n"
            "12 passed, 1 error in 4.00s\n", tmp_path, record=baseline)
    assert r["verdict"] == INCONCLUSIVE


def test_truncated_candidate_log_is_inconclusive(baseline, tmp_path):
    """A log cut before the summary line has no complete report."""
    assert run("FAILED tests/test_a.py::test_alpha\n", tmp_path,
               record=baseline)["verdict"] == INCONCLUSIVE


def test_non_pytest_output_is_inconclusive(baseline, tmp_path):
    assert run("build failed: nothing ran here\n", tmp_path,
               record=baseline)["verdict"] == INCONCLUSIVE


def test_rf_subset_shape_is_inconclusive(baseline, tmp_path):
    """`-rf` hides ERROR lines; the fingerprint would describe a subset."""
    text = "\n".join(l for l in BASELINE_LOG.splitlines() if not l.startswith("ERROR "))
    assert run(text, tmp_path, record=baseline)["verdict"] == INCONCLUSIVE


def test_missing_baseline_log_is_inconclusive(baseline, tmp_path):
    rec = {**baseline, "log": str(tmp_path / "gone.log")}
    assert run(CANDIDATE_LOG, tmp_path, record=rec)["verdict"] == INCONCLUSIVE


def test_baseline_log_not_matching_its_fingerprint_is_inconclusive(baseline, tmp_path):
    """A baseline log edited after the fact is corrupt, not authoritative."""
    log = tmp_path / "baseline.log"
    log.write_text(BASELINE_LOG + "FAILED tests/test_extra.py::test_x\n")
    assert run(CANDIDATE_LOG, tmp_path, record=baseline)["verdict"] == INCONCLUSIVE


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("3 failed, 40 passed, 2 skipped, 1 error in 12.34s", 46),
    ("1 skipped, 1 error in 2.96s", 2),
    ("8 failed, 3276 passed, 17 skipped, 1 error in 274.19s (0:04:34)", 3302),
    ("nothing here", None),
])
def test_executed_count(text, expected):
    assert executed_count(text) == expected


def test_merge_base_resolves_and_fails_closed():
    """Derived, never assumed; an unresolvable ref yields None, not a fallback."""
    assert merge_base(str(REPO_ROOT), "HEAD", "HEAD") is not None
    assert merge_base(str(REPO_ROOT), "HEAD", "no-such-ref-xyz") is None
