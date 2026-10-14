"""Integrity guard for the lane-4 composition guard (anti-revert).

``tests/test_prism_next_wave_composition_reconciliation_01.py`` derives the lane-4
projection set from the corpus. Its soundness depends on resolving page-bound
locals **per test function** rather than module-wide; a module-wide read counted a
``<LabWorkLoop`` pin on a sibling page as a Lab-page projection and failed the
correct union.

That repair is reversible by a merge, and the reversal is **silent**. PR #493
carries the pre-repair blob of the guard (``cad8bd65``) while PR #504 carries the
repaired one (``3305ec80``). Merging #504 then #493 produces an add/add conflict on
the guard file, and the natural resolution (``git checkout --theirs``) restores the
pre-repair blob: the guard still reports ``5 passed`` -- no failure signal -- while
the repaired controls and derived-set assertions disappear.

A reverted guard cannot police its own deletion, so the invariant lives here, in a
file the reverting side does not carry:

    the composition guard must carry the per-function binding machinery and the
    controls that prove it, so a merge that restores the pre-repair blob reddens
    THIS test instead of passing quietly.

The detector is a pure function over source text so the negative control below can
feed it the pre-repair shape without a worktree.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUARD = "tests/test_prism_next_wave_composition_reconciliation_01.py"

# Naming the guarded surface places this module in the console-contract guard
# domain (``scripts/console_contract_domain.py``), so the same gate that executes
# the composition guard also executes its integrity check. A guard no gate runs is
# decoration.
PAGE = "web/arkadia_console/src/pages/EngineeringLabPage.tsx"

# Structural features of the repaired guard. Each is load-bearing: the first two
# are the per-function binding resolution, the rest are the controls that prove it.
REQUIRED = (
    "_block_bindings",
    "_page_locals_in_block",
    "test_the_derived_projection_set_is_not_empty",
    "test_control_a_name_reused_for_a_sibling_page_does_not_leak",
    "test_control_a_module_not_binding_the_page_yields_nothing",
)


def missing_features(source: str, required=REQUIRED) -> list[str]:
    return [name for name in required if name not in source]


def test_the_composition_guard_carries_the_per_function_binding_repair():
    source = (REPO / GUARD).read_text(encoding="utf-8")
    missing = missing_features(source)
    assert not missing, (
        f"{GUARD} is missing {missing}. The pre-repair blob resolved page-bound "
        "locals module-wide, which made a sibling-page pin a phantom Lab projection "
        "and failed the correct union. A merge that restores that blob passes "
        "quietly; this guard exists so it does not."
    )


def test_negative_control_the_pre_repair_shape_is_reported():
    """Feed the detector the pre-repair shape; it must report the gap.

    Without this control the guard above could be satisfied by a file that merely
    mentions the names, and could never fail for the defect it names.
    """
    pre_repair = (
        '"""Composition guard (pre-repair)."""\n'
        "def test_a_mounted_lane4_projection_requires_all_of_them():\n"
        "    pass\n"
    )
    missing = missing_features(pre_repair)
    assert missing == list(REQUIRED), (
        "the detector did not report the pre-repair shape as missing the repair: "
        f"{missing}"
    )


def test_positive_control_the_repaired_shape_is_silent():
    """A source carrying every feature must yield no gap."""
    repaired = "\n".join(REQUIRED)
    assert missing_features(repaired) == []
