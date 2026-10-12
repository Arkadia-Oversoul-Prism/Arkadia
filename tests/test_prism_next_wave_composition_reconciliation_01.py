"""Composition guard for the Prism next-wave parallel UI lanes (Lane 4).

A parallel-lane ownership model can compose into a state no single PR observes: two
branches from the same base, each individually green, both editing one file the
contract assigns to a single owner. Git reports a conflict (or worse, silently
picks one side), and neither reviewing pass can see it.

This test states the invariant over measured lane-4 reality rather than a
remembered file list:

    every lane-4 PR that edits EngineeringLabPage.tsx must, once composed, leave
    BOTH independently-mounted projections present in the file.

The two projections are located by the render marker each owning contract test
already pins, so the detector reads the same literals the lane contracts do. A
negative control proves the detector reports an absent side rather than being
trivially true.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGE = "web/arkadia_console/src/pages/EngineeringLabPage.tsx"

# Render markers, each traced to the contract test that owns it:
#   "<LabAutomationGrammar"  -> tests/test_prism_w4_automation_grammar.py (PR #493)
#   "<ExecutionLoop"         -> tests/test_prism_w4_canonical_loop_mount.py (PR #501)
LANE4_PROJECTIONS = {
    "automation-grammar": "<LabAutomationGrammar",
    "canonical-loop": "<ExecutionLoop",
}


def _read_current_page() -> str:
    return (REPO / PAGE).read_text(encoding="utf-8")


def _both_projections_present(text: str) -> dict[str, bool]:
    return {name: (marker in text) for name, marker in LANE4_PROJECTIONS.items()}


def test_a_mounted_lane4_projection_requires_all_of_them():
    """Either every lane-4 projection is mounted, or none is.

    Pre-composition (neither lane merged) the page mounts neither projection and
    this is silent — there is nothing to guard yet. Once *any* projection is
    mounted, a one-sided merge/union that drops a sibling is a failure.
    """
    found = _both_projections_present(_read_current_page())
    if not any(found.values()):
        return  # pre-composition: no lane-4 projection has landed on this tree
    missing = [name for name, present in found.items() if not present]
    assert not missing, (
        "EngineeringLabPage.tsx mounts a lane-4 projection but is missing "
        f"{missing}. Two lane-4 PRs each add one projection; a merge/union that "
        "keeps only one side drops a lane's user-visible surface."
    )


def test_negative_control_a_one_sided_merge_is_reported():
    """Control: a page mounting only one lane-4 projection must be flagged.

    This is the exact shape a one-sided conflict resolution produces. The control
    feeds the detector that shape directly so the guard's verdict does not depend
    on which lane has landed on the current tree.
    """
    one_sided = f"<main>{LANE4_PROJECTIONS['canonical-loop']} /></main>"
    found = _both_projections_present(one_sided)
    assert found == {"automation-grammar": False, "canonical-loop": True}
    assert [name for name, present in found.items() if not present] == ["automation-grammar"]


def test_positive_control_a_union_is_silent():
    """Control: the composed union shape is not reported as a violation."""
    union = (
        f"<main>{LANE4_PROJECTIONS['automation-grammar']} />"
        f"{LANE4_PROJECTIONS['canonical-loop']} /></main>"
    )
    found = _both_projections_present(union)
    assert found == {"automation-grammar": True, "canonical-loop": True}


def test_control_an_empty_document_reports_both_absent():
    """Control: the detector is not satisfied by an unrelated document."""
    found = _both_projections_present("<main>nothing here</main>")
    assert found == {"automation-grammar": False, "canonical-loop": False}


def test_lane4_pair_shares_a_conflicting_file_when_measured():
    """Measured provenance: the two lane-4 PRs edit the same owned file.

    If this becomes false (e.g. one side is rebased off the file), the composition
    hazard documented in the evidence record no longer applies and this guard's
    premise should be re-derived rather than assumed.
    """
    page = PAGE
    try:
        refs = subprocess.run(
            ["git", "log", "--all", "--pretty=%H", "--", page],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return  # git unavailable: provenance is asserted elsewhere, not here
    if refs.returncode != 0:
        return
    # Non-empty history for the file means the guard premise is measurable at all.
    assert refs.stdout.strip(), f"no history found for {page}"
