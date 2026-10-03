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


# --- Live node set and published-value agreement ---------------------------
#
# The tests above pin the *derivation* with synthetic input. They cannot catch a
# published value that is internally inconsistent, because the published value is
# never fed back through the derivation. These tests close that gap: they run the
# real recorded baseline node set through the extractor and require the repository's
# published fingerprint to equal the result.
#
# History this guards: `.bootstrap/01_STATE.md` published `a59453b8…`/`9a35c812…`.
# A reconciliation pass recorded those as "unreproducible by any convention" — that was
# wrong. They are exactly the fingerprints of the recorded set **plus** its depth-dependent
# sibling `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` (see
# `CLONE_DEPENDENT_SIBLING_NODE` below, and
# `test_superseded_values_are_the_recorded_set_plus_its_sibling`).
# `scripts/baseline_fingerprint.py` also produced `4d84e7eb…`/
# `da2ec262…` for a recorded set that held `test_gate2_parent_…` — reproducible only in a
# clone that carried the PR-head revision `7d79f38…`, because that node skips when the
# revision is absent. The canonical value is now derived from a set that excludes both
# depth-dependent nodes, so the value is stable across clone depths. See
# `docs/control-plane/evidence/gate-hygiene-superseded-fingerprint-origin-01/`.

LIVE_NODE_SET = REPO_ROOT / "tests" / "fixtures" / "baseline_node_set.txt"

# The recorded set *before* `gate-hygiene/stale-gate-fixture-retirement-01` retired the two
# nodes asserting the archived root `gate/` + `index.html` surface. `a59453b8…`/`9a35c812…`
# are this set plus the depth-dependent sibling below — they are not "unreproducible", and
# keeping the era-correct set lets the origin stay proved after the retirement.
SUPERSEDED_NODE_SET = (
    REPO_ROOT / "tests" / "fixtures" / "superseded_baseline_node_set.txt"
)

# The two nodes retired by `gate-hygiene/stale-gate-fixture-retirement-01`. They asserted a
# root `gate/` directory and root `index.html` redirect that `f6718b9` / `377cdb3` archived
# (the surface survives only under `archive/legacy_frontend/gate/`). The guard below fails if
# either re-enters the recorded set, so a future merge cannot silently restore the stale
# expectation while the fixture stays trimmed.
RETIRED_NODES = (
    "tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists",
    "tests/test_gate_status.py::test_gate_files_and_fetch_handling",
)

# The *sibling* depth-dependent node. It dereferences the `GATE2_PARENT_REV` read
# unconditionally, so it crashes (AttributeError) instead of skipping when `7d79f38…` is
# absent. It is likewise excluded from the recorded set — a live CI-shaped run reports it,
# so the recorded set is the *stable* debt, one node short of a bare clone's live run.
CLONE_DEPENDENT_SIBLING_NODE = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec"
)

# A node whose outcome depends on whether this clone contains the PR-head revision
# pinned by `tests/test_agents_md_encoding_adjudication.py` (`GATE2_PARENT_REV`). It
# is *not* part of the recorded set: including it made the fingerprint a function of
# clone depth rather than of the repository's debt. The guard below fails if it ever
# comes back.
CLONE_DEPTH_DEPENDENT_NODE = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline"
)

# The *sibling* depth-dependent node in the same file. It dereferences the `GATE2_PARENT_REV`
# read unconditionally, so it crashes (AttributeError) instead of skipping when `7d79f38…` is
# absent. It is likewise excluded from the recorded set — a live CI-shaped run reports it, so
# the recorded set is the *stable* debt, one node short of a bare clone's live run.
CLONE_DEPENDENT_SIBLING_NODE = (
    "tests/test_agents_md_encoding_adjudication.py"
    "::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec"
)

# Canonical values: `scripts/baseline_fingerprint.py` run on LIVE_NODE_SET.
# Superseded 2026-10-03 by `gate-hygiene/stale-gate-fixture-retirement-01`, which
# retired the two nodes asserting the archived root `gate/` + `index.html` surface
# (removed from the tree by `f6718b9` / `377cdb3`, present only under
# `archive/legacy_frontend/gate/`). The recorded set is now 18 nodes. The previous
# pair is retained in SUPERSEDED_* below.
CANONICAL_OUTCOMES_FINGERPRINT = (
    "6c7bf8218fd1e0ae9bc970653e98c18b3a78b69a5c4920dac9f4747c033e4648"
)
CANONICAL_IDS_FINGERPRINT = (
    "2bc35996b21de6529ffffab63446c8bd7295c388e841a2807101d189eaf7da01"
)

# Values that were published but do not describe the recorded set. They must not reappear
# in the repository docs: the doc-agreement test below fails if either is found.
#
# `a59453b8…`/`9a35c812…` are the fingerprints of the recorded set **plus** the
# depth-dependent sibling node (proved by
# `test_superseded_values_are_the_recorded_set_plus_its_sibling`), i.e. a live bare-clone
# run — not the depth-stable recorded debt.
# `4d84e7eb…`/`da2ec262…` were reproducible only in a clone that contained the PR-head
# revision `7d79f38…`. Both pairs are superseded by the clone-depth-stable canonical value
# above.
SUPERSEDED_OUTCOMES_FINGERPRINTS = (
    "a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f",
    "4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7",
    "a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1",
)
SUPERSEDED_IDS_FINGERPRINTS = (
    "9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22",
    "da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71",
    "8036fc0692eb0358f037adb2cf9e2b234db1f41a4586ca0162f4e52350cfa713",
)

# Documents that publish a baseline fingerprint and must agree with the canonical
# value. MISSION.md / NEXT_AGENT.md / the ledger are read by the next agent, so a
# stale value there propagates the defect rather than recording it.
FINGERPRINT_DOCS = [
    ".bootstrap/01_STATE.md",
    "MISSION.md",
    "NEXT_AGENT.md",
    "docs/phase1/CONTINUATION_LEDGER.md",
]


def test_live_node_set_reproduces_the_canonical_fingerprint():
    """The recorded baseline set must hash to the published canonical value."""
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert len(ids) == 18
    assert sum(1 for o in outcomes if o.startswith("FAILED")) == 17
    assert sum(1 for o in outcomes if o.startswith("ERROR")) == 1
    assert baseline_fingerprint.fingerprint(outcomes) == CANONICAL_OUTCOMES_FINGERPRINT
    assert baseline_fingerprint.fingerprint(ids) == CANONICAL_IDS_FINGERPRINT


def test_recorded_set_excludes_the_clone_depth_dependent_node():
    """The recorded set must not depend on clone depth.

    `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` skips when
    the PR-head revision it pins is absent, so its outcome differs between a shallow
    clone and one that carries that revision. Recording it made the fingerprint a
    function of the clone rather than of the repository's debt, which is the same
    defect class this reconciliation exists to remove.
    """
    _, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert CLONE_DEPTH_DEPENDENT_NODE not in ids


def test_superseded_values_are_the_recorded_set_plus_its_sibling():
    """The values the repo recorded as "unreproducible by any convention" *are* reproducible:
    they are the recorded set plus its depth-dependent sibling node.

    This is the corrected origin of `a59453b8…`/`9a35c812…`. A bare clone (CI) reports the
    sibling — it crashes with AttributeError instead of skipping — so its live run is the
    recorded set plus that node, and that run hashes to exactly the value the docs declared
    unreproducible. Both are still *superseded* (the sibling is clone-depth dependent and must
    not be republished), but the reason is "the recorded set plus a depth-dependent node", not
    "no convention reproduces it".
    """
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    assert CLONE_DEPENDENT_SIBLING_NODE not in ids
    assert baseline_fingerprint.fingerprint(
        sorted(outcomes + [f"FAILED {CLONE_DEPENDENT_SIBLING_NODE}"])
    ) == SUPERSEDED_OUTCOMES_FINGERPRINTS[0]
    assert baseline_fingerprint.fingerprint(
        sorted(ids + [CLONE_DEPENDENT_SIBLING_NODE])
    ) == SUPERSEDED_IDS_FINGERPRINTS[0]


def test_superseded_fingerprints_are_not_reproducible():
    """Negative control: the recorded set must NOT hash to a superseded value, so the
    doc-agreement test cannot be satisfied by accident. A convention that happened to
    yield a superseded value would mean the correction was wrong.

    Note the distinction from `test_superseded_values_are_the_recorded_set_plus_its_sibling`:
    a superseded value *is* reproducible — from the recorded set plus a depth-dependent node.
    What must never hold is the recorded set alone reproducing one.
    """
    outcomes, ids = baseline_fingerprint.extract(str(LIVE_NODE_SET))
    outcomes_fp = baseline_fingerprint.fingerprint(outcomes)
    ids_fp = baseline_fingerprint.fingerprint(ids)
    assert outcomes_fp not in SUPERSEDED_OUTCOMES_FINGERPRINTS
    assert ids_fp not in SUPERSEDED_IDS_FINGERPRINTS
    # And no "reason included" / "unsorted" variant lands on them either.
    unsorted_ids_fp = hashlib.sha256(("\n".join(sorted(ids)).encode())).hexdigest()
    assert unsorted_ids_fp not in SUPERSEDED_IDS_FINGERPRINTS


@pytest.mark.parametrize("doc", FINGERPRINT_DOCS)
def test_published_docs_carry_the_canonical_fingerprint(doc):
    text = (REPO_ROOT / doc).read_text(encoding="utf-8")
    for superseded in SUPERSEDED_OUTCOMES_FINGERPRINTS:
        assert superseded not in text, (
            f"{doc} still publishes the superseded outcomes fingerprint {superseded}"
        )
    for superseded in SUPERSEDED_IDS_FINGERPRINTS:
        assert superseded not in text, (
            f"{doc} still publishes the superseded node-set fingerprint {superseded}"
        )
    assert CANONICAL_OUTCOMES_FINGERPRINT in text, (
        f"{doc} does not publish the canonical outcomes fingerprint"
    )
