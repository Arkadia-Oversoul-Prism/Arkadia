"""PR #366 x PR #368 are a same-instrument composition hazard, not two independent PRs.

#366 repairs marker-oracle soundness in ``scripts/gate2_production_observation.py``;
#368 repairs a pagination artifact in the *same script* (and its test) that reported
``main -> deployment identity := UNKNOWN`` while ``main`` was deployed and sha-identical.
Both are green alone and GitHub reports both ``MERGEABLE`` — that verdict compares each
head to ``main`` only and cannot see a cross-PR overlap, so it is not evidence the pair
composes. Measured at base ``24a00f85``, a 3-way apply of #368 onto #366 yields ``UU`` on
both files; the conflicts are additive, so the honest resolution keeps *both* sides, and
the composed tree is then green (39 passed on the merged test file).

This guard makes that reconciliation executable and pins the invariants a later pass must
not silently break. Source-level only: it reads the frozen manifest in
``scripts/gate2_366_368_composition.py`` and imports no application module.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "gate2_366_368_composition.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("gate2_366_368_composition", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


# --------------------------------------------------------------------------- #
# The population overlap is fully classified.
# --------------------------------------------------------------------------- #


def test_every_population_overlap_is_classified() -> None:
    """No open PR may share a non-AGENTS.md path with another unless it is recorded."""
    unclassified = mod.unclassified_overlaps(mod.POPULATION)
    assert unclassified == [], (
        "unclassified non-AGENTS.md overlap across the recorded open-PR population: "
        f"{unclassified}"
    )


def test_population_has_exactly_the_two_measured_overlaps() -> None:
    """Positive control: the detector must *find* the overlaps, not merely tolerate them.

    A guard that passed because it saw no overlap would also pass if the manifest were
    emptied. Pin the two measured pairs so the silence above is meaningful.
    """
    overlaps = {(a, b): shared for a, b, shared in mod.overlapping_sources(mod.POPULATION)}
    assert set(overlaps) == {("337", "338"), ("366", "368")}


def test_the_366_368_hazard_is_present_with_the_recorded_paths() -> None:
    """The same-instrument hazard must be recorded with both shared paths."""
    overlaps = {(a, b): shared for a, b, shared in mod.overlapping_sources(mod.POPULATION)}
    assert overlaps[("366", "368")] == [
        "scripts/gate2_production_observation.py",
        "tests/test_gate2_production_observation.py",
    ]
    entry = mod.CLASSIFIED[frozenset({"366", "368"})]
    assert entry["kind"] == "same-instrument hazard"
    assert entry["shared"] == overlaps[("366", "368")]


def test_366_368_recorded_reconciliation_orders_the_merge() -> None:
    """The recorded disposition must name an order (or a composed PR), not 'either'."""
    disposition = mod.CLASSIFIED[frozenset({"366", "368"})]["disposition"]
    lowered = disposition.lower()
    assert "rebase" in lowered or "composed" in lowered
    # The two repairs are independently necessary, so dropping either is not a resolution.
    assert "both" in lowered or "keep both" in lowered


# --------------------------------------------------------------------------- #
# Controls: the detector and the classifier can both still fail.
# --------------------------------------------------------------------------- #


def test_detector_flags_an_unclassified_overlap_negative_control() -> None:
    """Negative control: a synthetic overlap outside the classified set must be reported."""
    synthetic = {
        "900": ["AGENTS.md", "scripts/gate2_production_observation.py"],
        "901": ["AGENTS.md", "scripts/gate2_production_observation.py"],
    }
    unclassified = mod.unclassified_overlaps(synthetic)
    assert len(unclassified) == 1
    assert unclassified[0][2] == ["scripts/gate2_production_observation.py"]


def test_classifier_can_still_fail_when_the_366_368_entry_is_dropped() -> None:
    """Positive control for the classification itself: remove the entry and the guard fires.

    This proves ``test_every_population_overlap_is_classified`` is testing the recorded
    classification rather than a detector that is silent no matter what.
    """
    reduced = {
        k: v for k, v in mod.CLASSIFIED.items() if k != frozenset({"366", "368"})
    }
    unclassified = mod.unclassified_overlaps(mod.POPULATION, classified=reduced)
    assert [frozenset({o[0], o[1]}) for o in unclassified] == [frozenset({"366", "368"})]


def test_agents_md_only_overlap_is_not_a_hazard() -> None:
    """Tail-append collisions are mechanical and must not be reported as semantic hazards."""
    synthetic = {"900": ["AGENTS.md", "docs/x.md"], "901": ["AGENTS.md", "docs/x.md"]}
    assert mod.overlapping_sources({"900": ["AGENTS.md"], "901": ["AGENTS.md"]}) == []
    assert mod.overlapping_sources(synthetic) == [("900", "901", ["docs/x.md"])]


# --------------------------------------------------------------------------- #
# Drift pin: a moved branch head invalidates the recorded reconciliation.
# --------------------------------------------------------------------------- #


def _git_show_blob(ref_path: str) -> str | None:
    # ``git rev-parse`` echoes the *argument* to stdout on failure, so a missing ref
    # still yields non-empty stdout. Gate on the exit code, or an absent branch is
    # mistaken for a moved head (measured: exit 128 with stdout == ref_path).
    result = subprocess.run(
        ["git", "rev-parse", ref_path], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


@pytest.mark.parametrize(
    ("branch", "path"),
    [
        (
            "origin/gate-hygiene/gate2-marker-oracle-soundness-01",
            "scripts/gate2_production_observation.py",
        ),
        (
            "origin/gate-hygiene/gate2-deployment-window-01",
            "scripts/gate2_production_observation.py",
        ),
    ],
)
def test_recorded_head_blob_matches_live_branch_when_available(branch: str, path: str) -> None:
    """If the branch is present, its script blob must match the recorded identity.

    A mismatch means the head moved and the reconciliation text (including the composed
    blob ids) must be re-measured before it is trusted.
    """
    expected = mod.BLOBS["366" if "marker-oracle" in branch else "368"][path]
    live = _git_show_blob(f"{branch}:{path}")
    if live is None:
        pytest.skip(f"{branch} not fetched in this clone")
    assert live == expected, (
        f"{branch} head moved: recorded {expected}, live {live}. Re-run "
        "`python scripts/gate2_366_368_composition.py --measure` and update the record."
    )


def test_absent_ref_is_read_as_absent_not_as_a_moved_head() -> None:
    """Negative control for the drift pin's absence detection.

    ``git rev-parse <missing-ref>`` exits 128 with the ref echoed to stdout, so a
    stdout-only presence check reads a deleted/never-fetched branch as a *moved head*
    and hard-fails the guard in any clone that did not fetch the PR branches (CI).
    Measured before the fix: simulating the absent refs gave ``2 failed, 7 passed``;
    the control pins the exit-code contract so a future refactor cannot reintroduce it.
    """
    assert _git_show_blob("origin/this-ref-does-not-exist-arbitrary") is None
