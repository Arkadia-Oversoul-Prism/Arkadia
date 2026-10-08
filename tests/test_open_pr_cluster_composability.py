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

_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "docs/control-plane/evidence/gate-hygiene-open-pr-cluster-composability-pass8/cluster_manifest.json"
)

# The tail of AGENTS.md is appended to by every workstream; it is not a semantic surface.
_TAIL_APPEND_ALLOWLIST = {"AGENTS.md"}


def _load() -> dict[str, list[str]]:
    return {k: list(v) for k, v in json.loads(_MANIFEST.read_text(encoding="utf-8"))["prs"].items()}


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
