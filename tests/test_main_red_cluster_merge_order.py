"""Guard: the main-red cluster carries a duplicate PR pair, and it is order-independent.

The open PRs that repair the `main`-red node set overlap on ``AGENTS.md`` (a benign tail
append) **and** on one load-bearing test+asset pair: PR #354 deliberately composes PR #384's
CP10 browser-asset repair, so the two share two byte-identical files. That is a *duplicate*,
not a conflict — either merge order yields the same tree, so it must be recorded rather than
re-derived or mistaken for a semantic conflict.

This guard is source-level: it reads a recorded manifest and imports no application module.
It fails when a future pass records an overlap whose files are **not** identical, which is the
signature of two live PRs editing the same load-bearing source independently.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

_EVIDENCE = (
    Path(__file__).resolve().parents[1]
    / "docs/control-plane/evidence/gate-hygiene-main-red-cluster-merge-order-01"
)
_MANIFEST = _EVIDENCE / "merge_order_manifest.json"

# The tail of AGENTS.md is appended to by every workstream; not a semantic surface.
_TAIL_APPEND_ALLOWLIST = {"AGENTS.md"}


def duplicate_pairs(prs: dict[str, list[str]]) -> list[tuple[str, str, set[str]]]:
    """Return (a, b, shared_paths) for every pair sharing a non-AGENTS.md path.

    A non-empty result means two PRs touch the same load-bearing source. That is only safe
    when the shared blobs are identical (one PR deliberately composes the other); the manifest
    records which, and ``test_recorded_duplicate_blobs_are_identical`` enforces it.
    """
    overlaps: list[tuple[str, str, set[str]]] = []
    for (a, files_a), (b, files_b) in combinations(prs.items(), 2):
        shared = (set(files_a) & set(files_b)) - _TAIL_APPEND_ALLOWLIST
        if shared:
            overlaps.append((a, b, shared))
    return overlaps


def _load() -> dict:
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def test_recorded_duplicate_is_the_superset_relationship() -> None:
    data = _load()
    rel = data["duplicate_file_relationship"]
    assert rel["superset_pr"] == "354"
    assert rel["subset_pr"] == "384"
    assert rel["main_is_ancestor_of_both"] is True
    assert rel["real_merge_conflicts"] == 0
    assert rel["order_independent"] is True


def test_recorded_duplicate_blobs_are_identical() -> None:
    """The one shared pair must be byte-identical, or it is a semantic conflict."""
    rel = _load()["duplicate_file_relationship"]
    shared = rel["shared_files"]
    assert len(shared) == 2
    for path, info in shared.items():
        assert info["identical"] is True, f"{path} is not identical across the two PRs"
        assert info["pr384_blob"] == info["pr354_blob"], (
            f"{path}: #354 must carry the exact blob #384 carries, else the pair is a "
            "conflict, not a duplicate"
        )


def test_recorded_node_ownership_covers_the_baseline() -> None:
    data = _load()
    owners = data["baseline_node_owners"]
    # Every non-sovereign node must name a PR number.
    for node, owner in owners.items():
        if owner.startswith("sovereign"):
            continue
        assert owner.isdigit(), f"{node} has a non-numeric owner {owner!r}"


def test_detector_flags_a_shared_load_bearing_file() -> None:
    """Negative control: the detector must fire when two PRs touch the same test source."""
    synthetic = {
        "900": ["AGENTS.md", "tests/test_shared.py"],
        "901": ["AGENTS.md", "tests/test_shared.py"],
    }
    overlaps = duplicate_pairs(synthetic)
    assert len(overlaps) == 1
    assert overlaps[0][2] == {"tests/test_shared.py"}


def test_detector_is_silent_when_prs_share_only_agents_md() -> None:
    """Positive control: a pure tail-append overlap is not reported."""
    synthetic = {
        "900": ["AGENTS.md", "tests/test_a.py"],
        "901": ["AGENTS.md", "tests/test_b.py"],
    }
    assert duplicate_pairs(synthetic) == []
