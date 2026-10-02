"""Regression guard for the baseline test-debt fingerprint (gate-hygiene).

The published fingerprint in `.bootstrap/01_STATE.md` was, for two revisions,
not reproducible from the derivation printed beside it: the derivation read as
bare node ids, but the value was actually `"FAILED/ERROR <nodeid>"`. Worse, the
node ids had been read from `pytest -q` output *including* the assertion reason,
which pytest truncates to the terminal width -- so the same node set hashed
differently in a 120-column job and an 80-column shell.

These tests pin the derivation with known-answer tests (so a change in how the
fingerprint is computed fails loudly) and prove the two properties that make a
fingerprint usable: it is independent of the reporting terminal width and of
the order in which pytest reports nodes.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "baseline_fingerprint", REPO_ROOT / "scripts" / "baseline_fingerprint.py"
)
assert _SPEC and _SPEC.loader
baseline_fingerprint = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(baseline_fingerprint)

# Known-answer test: sorted `"<OUTCOME> <nodeid>"` lines joined by "\n" plus a
# trailing newline.
KAT_LOG = (
    "FAILED tests/a.py::test_one - AssertionError: assert 1 == 2\n"
    "FAILED tests/b.py::test_two - assert 'x' in 'y'\n"
    "ERROR tests/c.py\n"
)
KAT_OUTCOMES = "6dca8d694c688a8bb845222d2ddedde7a190c7fcd5eaa78a3e4292f300cb0f49"
# sha256(b"\n") -- the empty fingerprint, which is a fixed value, not a special case.
EMPTY_FINGERPRINT = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"


def _write(tmp_path: Path, text: str, name: str = "suite.log") -> Path:
    # Distinct names matter: a shared filename makes a two-log comparison
    # compare one file with itself and pass vacuously.
    log = tmp_path / name
    log.write_text(text, encoding="utf-8")
    return log


def test_known_answer_outcomes_fingerprint(tmp_path):
    log = _write(tmp_path, KAT_LOG)
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [
        "ERROR tests/c.py",
        "FAILED tests/a.py::test_one",
        "FAILED tests/b.py::test_two",
    ]
    assert ids == ["tests/a.py::test_one", "tests/b.py::test_two", "tests/c.py"]
    assert baseline_fingerprint.fingerprint(outcomes) == KAT_OUTCOMES


def test_fingerprint_is_independent_of_terminal_width(tmp_path):
    """The defect this script exists to remove: reason truncation must not matter."""
    wide = _write(
        tmp_path,
        "FAILED tests/a.py::test_one - AssertionError: assert 'alpha' == 'beta' "
        "where 'alpha' is a very long repr that an 80-column terminal would clip\n"
        "ERROR tests/c.py\n",
        name="wide.log",
    )
    narrow = _write(
        tmp_path,
        "FAILED tests/a.py::test_one - Assert...\n"
        "ERROR tests/c.py\n",
        name="narrow.log",
    )
    wide_out, wide_ids = baseline_fingerprint.extract(str(wide))
    narrow_out, narrow_ids = baseline_fingerprint.extract(str(narrow))
    assert baseline_fingerprint.fingerprint(wide_out) == baseline_fingerprint.fingerprint(narrow_out)
    assert baseline_fingerprint.fingerprint(wide_ids) == baseline_fingerprint.fingerprint(narrow_ids)


def test_fingerprint_is_independent_of_report_order(tmp_path):
    a = _write(
        tmp_path,
        "FAILED tests/a.py::t\nERROR tests/c.py\nFAILED tests/b.py::t\n",
        name="order_a.log",
    )
    b = _write(
        tmp_path,
        "ERROR tests/c.py\nFAILED tests/b.py::t\nFAILED tests/a.py::t\n",
        name="order_b.log",
    )
    assert baseline_fingerprint.fingerprint(baseline_fingerprint.extract(str(a))[0]) == (
        baseline_fingerprint.fingerprint(baseline_fingerprint.extract(str(b))[0])
    )


def test_node_set_is_invariant_but_outcomes_distinguish_failure_from_error(tmp_path):
    """A node flipping FAILED<->ERROR is not a node-set change, but is a real
    outcome change; the two fingerprints must not conflate them."""
    failed = _write(tmp_path, "FAILED tests/a.py::t\nFAILED tests/b.py::t\n", name="failed.log")
    errored = _write(tmp_path, "ERROR tests/a.py::t\nFAILED tests/b.py::t\n", name="errored.log")
    f_out, f_ids = baseline_fingerprint.extract(str(failed))
    e_out, e_ids = baseline_fingerprint.extract(str(errored))
    assert baseline_fingerprint.fingerprint(f_ids) == baseline_fingerprint.fingerprint(e_ids)
    assert baseline_fingerprint.fingerprint(f_out) != baseline_fingerprint.fingerprint(e_out)


def test_empty_log_hashes_the_empty_fingerprint(tmp_path):
    log = _write(tmp_path, "no outcomes here\n")
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [] and ids == []
    assert baseline_fingerprint.fingerprint(ids) == EMPTY_FINGERPRINT


def test_extract_matches_an_independent_implementation(tmp_path):
    """Guard against the extractor drifting from the published derivation:
    `sha256("\\n".join(sorted(ids)) + "\\n")`, computed here by hand."""
    log = _write(tmp_path, KAT_LOG)
    _, ids = baseline_fingerprint.extract(str(log))
    independent = hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()
    assert baseline_fingerprint.fingerprint(ids) == independent


def test_json_output_shape(tmp_path, capsys):
    log = _write(tmp_path, KAT_LOG)
    rc = baseline_fingerprint.main([str(log), "--json"])
    assert rc == 0
    import json

    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"] == 3
    assert payload["failed"] == 2
    assert payload["errors"] == 1
    assert payload["outcomes_fingerprint"] == KAT_OUTCOMES


@pytest.mark.parametrize(
    "line",
    [
        "tests/a.py::test_one",  # a bare node id is not an outcome line
        "  FAILED tests/a.py::t",  # indented (continuation), not a report line
        "1 failed, 2 passed",  # summary line
    ],
)
def test_non_outcome_lines_are_ignored(tmp_path, line):
    log = _write(tmp_path, line + "\n")
    outcomes, ids = baseline_fingerprint.extract(str(log))
    assert outcomes == [] and ids == []
