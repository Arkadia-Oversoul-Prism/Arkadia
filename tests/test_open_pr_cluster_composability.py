"""Guard: independent gate-hygiene PRs may overlap only on AGENTS.md.

Every gate-hygiene PR appends its account to the tail of ``AGENTS.md``, so two such PRs
always collide there mechanically; that collision is resolved by a union append and is not
a semantic conflict. Any *other* shared path — a test file, a script, a workflow — is a real
semantic conflict: two live PRs would be editing the same load-bearing source, so the
composed tree cannot be assumed green from the pieces. This guard fails when the recorded
cluster manifest shows such an overlap, so a future pass must surface it before composing.

Source-level only: it reads the manifest and imports no application module.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

_EVIDENCE = Path(__file__).resolve().parents[1] / "docs/control-plane/evidence"
_MANIFEST = _EVIDENCE / "gate-hygiene-open-pr-cluster-composability-pass8/cluster_manifest.json"
# Pass 9 widened the measured population from the #354-#357 sub-cluster to every open PR, which
# is where the #337/#338 dependency pair was found.
_FULL_MANIFEST = _EVIDENCE / "gate-hygiene-open-pr-cluster-composability-pass9/cluster_manifest.json"

# The tail of AGENTS.md is appended to by every workstream; it is not a semantic surface.
_TAIL_APPEND_ALLOWLIST = {"AGENTS.md"}

# Measured, classified dependency pair: PR #337 (the AEAS-01 operator surface) and PR #338 (its
# browser verification runner). They share load-bearing source and conflict on 4 files in 15
# hunks, but this is a component-plus-instrument pairing, not the independent-overlap hazard the
# detector below guards against. Recorded so a future pass does not re-derive the pair — and so
# the pair is not mistaken for two independent PRs that may be merged in any order.
_KNOWN_DEPENDENCY_PAIRS = {frozenset({"337", "338"})}


def _load() -> dict[str, list[str]]:
    return {k: list(v) for k, v in json.loads(_MANIFEST.read_text(encoding="utf-8"))["prs"].items()}


def _load_full_population() -> dict[str, list[str]]:
    data = json.loads(_FULL_MANIFEST.read_text(encoding="utf-8"))["prs"]
    return {k: list(v["files"]) for k, v in data.items()}


def overlapping_sources(prs: dict[str, list[str]]) -> list[tuple[str, str, set[str]]]:
    """Return (pr_a, pr_b, shared_paths) for every pair sharing a non-AGENTS.md path."""
    overlaps = []
    for (a, files_a), (b, files_b) in combinations(prs.items(), 2):
        shared = (set(files_a) & set(files_b)) - _TAIL_APPEND_ALLOWLIST
        if shared:
            overlaps.append((a, b, shared))
    return overlaps


def test_cluster_prs_overlap_only_on_agents_md() -> None:
    overlaps = overlapping_sources(_load())
    assert overlaps == [], (
        "independent gate-hygiene PRs share a load-bearing source file (not just AGENTS.md); "
        f"this is a semantic conflict, not a tail-append one: {overlaps}"
    )


def test_detector_flags_a_shared_test_file_negative_control() -> None:
    """Negative control: the detector must fire when two PRs touch the same test source."""
    synthetic = {
        "900": ["AGENTS.md", "tests/test_shared.py"],
        "901": ["AGENTS.md", "tests/test_shared.py"],
    }
    overlaps = overlapping_sources(synthetic)
    assert len(overlaps) == 1
    assert overlaps[0][2] == {"tests/test_shared.py"}


def test_detector_is_silent_on_the_measured_cluster_positive_control() -> None:
    """Positive control: the real composed cluster shares only AGENTS.md, so it is silent."""
    assert overlapping_sources(_load()) == []


# --------------------------------------------------------------------------- #
# Pass 9: the whole open-PR population, not just the #354-#357 sub-cluster.
# --------------------------------------------------------------------------- #


def test_full_population_overlaps_are_all_classified_dependency_pairs() -> None:
    """Every non-AGENTS.md overlap across all recorded open PRs must be a known dependency pair.

    Pass 8 measured only the #354-#357 sub-cluster, so it could not see that #337/#338 share
    four load-bearing paths. Widening the population is what surfaces it: an unclassified
    overlap here means two PRs presented as independent are editing the same load-bearing
    source, which must be reconciled before merge rather than merged in any order.
    """
    overlaps = overlapping_sources(_load_full_population())
    unclassified = [
        (a, b, sorted(p))
        for a, b, p in overlaps
        if frozenset({a, b}) not in _KNOWN_DEPENDENCY_PAIRS
    ]
    assert unclassified == [], f"unclassified non-AGENTS.md overlap across open PRs: {unclassified}"


def test_the_337_338_dependency_pair_is_actually_present() -> None:
    """Positive control: the detector must *find* the measured pair, not merely tolerate it.

    A guard that passes because it sees no overlap would also pass if #338's manifest entry were
    dropped. This asserts the pair is present in the measured data with the recorded shared paths,
    so the silence in the test above is meaningful.
    """
    overlaps = overlapping_sources(_load_full_population())
    pairs = {frozenset({a, b}): p for a, b, p in overlaps}
    assert frozenset({"337", "338"}) in pairs
    assert pairs[frozenset({"337", "338"})] == {
        "api/lab_routes.py",
        "web/public_prism/src/App.tsx",
        "web/public_prism/src/components/ArkadiaNavigation.tsx",
        "web/public_prism/src/pages/EngineeringLabPage.tsx",
    }


def test_full_population_detector_flags_an_unclassified_overlap_negative_control() -> None:
    """Negative control: an overlap outside the known pair must be reported, not ignored."""
    synthetic = {
        "900": ["AGENTS.md", "api/lab_routes.py"],
        "901": ["AGENTS.md", "api/lab_routes.py"],
    }
    overlaps = overlapping_sources(synthetic)
    unclassified = [
        (a, b, sorted(p))
        for a, b, p in overlaps
        if frozenset({a, b}) not in _KNOWN_DEPENDENCY_PAIRS
    ]
    assert unclassified == [("900", "901", ["api/lab_routes.py"])]
