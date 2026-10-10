"""Guard: the main-red debt-repair cluster composes to a strict subset of ``main``'s nodes.

The phase-1 workstream's central claim is that the open owner cluster repairs every
non-sovereign `main`-red node without introducing any new failure. On `main` @ `f9ced6b6`
that is **16** failing/error nodes; on the composed 9-PR tree it is **2** — both sovereign
reserved. This guard reads the recorded manifest and enforces the *shape* of that claim so a
future pass cannot record a composition that regressed without reddening CI.

Source-level: reads JSON evidence and imports no application module, runs no tests, performs
no network access.
"""

from __future__ import annotations

import json
from pathlib import Path

_EVIDENCE = (
    Path(__file__).resolve().parents[1]
    / "docs/control-plane/evidence/gate10-main-red-cluster-current-tip-composition-01"
)
_MANIFEST = _EVIDENCE / "composition_manifest.json"

# The two nodes no PR targets; both are governance decisions reserved to the sovereign.
_SOVEREIGN_RESERVED = frozenset(
    {
        "tests/test_autonomy.py",
        "tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate",
    }
)


def _load() -> dict:
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def test_composition_reduces_the_node_set() -> None:
    m = _load()["measured"]
    assert m["main_full_suite_nodes"] == 16
    assert m["composed_cluster_nodes"] == 2
    assert m["composed_cluster_nodes"] < m["main_full_suite_nodes"]


def test_composed_residual_is_exactly_the_sovereign_reserved_set() -> None:
    data = _load()
    assert set(data["sovereign_reserved_nodes"]) == set(_SOVEREIGN_RESERVED)
    assert data["repaired_nodes"] == data["measured"]["main_full_suite_nodes"] - (
        data["measured"]["composed_cluster_nodes"]
    )


def test_no_new_failures_are_recorded() -> None:
    """The load-bearing property: the composed set is a strict subset of ``main``.

    ``no_new_failures`` must be True and the fingerprints must differ (a composition that did
    not change the node set would be a no-op, not a repair).
    """
    data = _load()
    assert data["no_new_failures"] is True
    assert data["composed_node_set_is_subset_of_main"] is True
    m = data["measured"]
    assert m["main_outcomes_fingerprint"] != m["composed_outcomes_fingerprint"]


def test_duplicate_pair_blobs_are_identical_and_order_independent() -> None:
    rel = _load()["duplicate_pair"]
    assert rel["superset_pr"] == "354"
    assert rel["subset_pr"] == "384"
    assert rel["blobs_identical"] is True
    assert rel["real_merge_conflicts"] == 0
    assert set(rel["shared_files"]) == {
        "web/public_prism/public/firebase-config.js",
        "tests/test_frontend_script_assets_resolve.py",
    }


def test_only_agents_md_conflicts_in_merge_sequence() -> None:
    """A load-bearing-file conflict would make the composition a semantic, not additive, change."""
    order = _load()["merge_order"]
    assert order["load_bearing_conflicts"] == 0
    assert set(order["conflict_files"]) == {"AGENTS.md"}
