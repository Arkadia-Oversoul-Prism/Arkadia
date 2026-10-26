"""Lane 2 (NovaNet / Nexus Hub) — every declared hub sub-view carries a measured contract.

The Nexus Hub lens lists legacy sub-views that are declared in the reconciliation
inventory but not reconciled in the console. Before this guard the whole lens
rendered a single ``contract={"UNKNOWN"}`` with a note saying the distribution and
grove contracts were "not yet classified" — i.e. the page asserted that a
measurement had not been made.

A page that says "not yet classified" is indistinguishable from one whose
classification is wrong, so the invariant here is that each declared sub-view
resolves to a *measured* contract (a handler that was read, or the measured
absence of one), and that the rendered panel is derived from that one table
rather than restating it.

These are source-level assertions against ``NovaNetPage.tsx``, following the
convention of the other console contract tests in this repository.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web" / "arkadia_console" / "src" / "pages" / "NovaNetPage.tsx"

SOURCE = PAGE.read_text(encoding="utf-8")

#: The legacy Nexus hub sub-views declared in the reconciliation inventory. Named
#: here from the pre-repair note the page carried ("IMS archive, Spiral Grove,
#: Larder, distribution"), so the guard's domain does not silently shrink to
#: whatever the page happens to mention after an edit.
DECLARED_HUB_SUBVIEWS = ("ims", "grove", "larder", "distribution")

#: The exact shape this guard exists to reject: the hub lens rendered as a single
#: blanket UNKNOWN while the note deferred the classification. Kept verbatim as
#: the negative control's input so the detector is proven against the measured
#: pre-repair text rather than a paraphrase of it.
PRE_REPAIR_SHAPE = """
const DEFERRED: Record<string, string> = {
  hub: "UNKNOWN",
};

const note =
  "the distribution and grove contracts are not yet classified.";
"""


def _object_block(source: str, name: str) -> str:
    """Return the `{...}` body of the `const <name> ... = { ... }` declaration."""
    match = re.search(
        rf"const\s+{re.escape(name)}\s*:[^=]*=\s*\{{(.*?)\n\}};",
        source,
        re.S,
    )
    assert match, f"{name} declaration not found in {PAGE.name}"
    return match.group(1)


def _object_block_or_empty(source: str, name: str) -> str:
    match = re.search(
        rf"const\s+{re.escape(name)}\s*:[^=]*=\s*\{{(.*?)\n\}};",
        source,
        re.S,
    )
    return match.group(1) if match else ""


def _string_list_or_empty(source: str, name: str) -> list[str]:
    match = re.search(
        rf"const\s+{re.escape(name)}\s*:[^=]*=\s*\[(.*?)\];",
        source,
        re.S,
    )
    return re.findall(r'"([^"]*)"', match.group(1)) if match else []


def _string_list(source: str, name: str) -> list[str]:
    """Return the string literals of the `const <name> ... = [ ... ]` declaration."""
    match = re.search(
        rf"const\s+{re.escape(name)}\s*:[^=]*=\s*\[(.*?)\];",
        source,
        re.S,
    )
    assert match, f"{name} declaration not found in {PAGE.name}"
    return re.findall(r'"([^"]*)"', match.group(1))


def classify(source: str) -> dict[str, list[str]]:
    """Pure detector over a page source. Returns the violations it finds.

    Importing nothing and executing nothing is deliberate: the detector must be
    runnable against the pre-repair text (a string) as well as the live file.
    """
    violations: list[str] = []
    block = _object_block_or_empty(source, "HUB_SUBVIEWS")
    unclassified = _string_list_or_empty(source, "UNCLASSIFIED_HUB_SUBVIEWS")

    classified = [
        name
        for name in DECLARED_HUB_SUBVIEWS
        if re.search(rf"^\s*{re.escape(name)}\s*:\s*\{{", block, re.M)
    ]

    for name in DECLARED_HUB_SUBVIEWS:
        if name not in classified and name not in unclassified:
            violations.append(
                f"{name}: declared in the inventory but neither classified in "
                f"HUB_SUBVIEWS nor listed in UNCLASSIFIED_HUB_SUBVIEWS"
            )

    # A blanket UNKNOWN on the hub lens is the defect, not a conservative default.
    if re.search(
        r'DEFERRED\s*:\s*Record<string,\s*string>\s*=\s*\{\s*hub\s*:\s*"UNKNOWN"',
        source,
    ):
        violations.append(
            "the hub lens still renders a blanket UNKNOWN contract "
            "(DEFERRED.hub) instead of a measured per-sub-view contract"
        )

    return {
        "violations": violations,
        "classified": classified,
        "unclassified": unclassified,
    }


def test_every_declared_hub_sub_view_is_classified() -> None:
    result = classify(SOURCE)
    assert result["violations"] == []
    assert sorted(result["classified"]) == sorted(DECLARED_HUB_SUBVIEWS)


def test_no_classified_contract_is_the_unknown_placeholder() -> None:
    """`UNKNOWN` must not stand in for a contract that was measurable."""
    block = _object_block(SOURCE, "HUB_SUBVIEWS")
    for name in DECLARED_HUB_SUBVIEWS:
        entry = re.search(
            rf"^\s*{re.escape(name)}\s*:\s*\{{(.*?)\n\s*\}},", block, re.M | re.S
        )
        assert entry, f"{name} has no entry in HUB_SUBVIEWS"
        contract = re.search(r'contract:\s*"([^"]*)"', entry.group(1))
        assert contract, f"{name} declares no contract"
        assert contract.group(1).strip().upper() != "UNKNOWN", (
            f"{name} is still classified as UNKNOWN; measure its handler or record "
            f"the measured absence of one"
        )
        disposition = re.search(r"disposition:\s*\n?\s*\"([^\"]*)\"", entry.group(1))
        assert disposition, f"{name} carries no measured disposition"
        assert len(disposition.group(1).strip()) > 40, (
            f"{name}'s disposition is too short to be a measurement"
        )


def test_rendered_panel_is_derived_from_the_single_table() -> None:
    """The panel must not restate the table — a second copy is what drifts."""
    assert "HUB_CONTRACT_SUMMARY" in SOURCE and "HUB_NOTE" in SOURCE
    assert "HUB_SUBVIEW_IDS.map" in SOURCE, (
        "the rendered rows must be derived from HUB_SUBVIEWS, not hand-listed"
    )
    # The defect was a *prose* deferral that read as an unmade measurement. The
    # guarded label may still exist, but only as a conditional on a non-empty
    # unclassified set -- never as a standing claim in the note.
    assert "contracts are not yet classified" not in SOURCE, (
        "the page still defers the classification in prose"
    )
    assert re.search(
        r"UNCLASSIFIED_HUB_SUBVIEWS\.length\s*>\s*0", SOURCE
    ), "the 'not yet classified' label must be conditional on a non-empty set"
    assert re.search(r"UNCLASSIFIED_HUB_SUBVIEWS[^=]*=\s*\[\s*\]", SOURCE), (
        "this revision classifies every declared sub-view, so the unclassified "
        "set must be empty; a non-empty set means a sub-view was left unmeasured"
    )


def test_declared_inventory_matches_the_archived_hub_sub_views() -> None:
    """Anchor the domain to the archived hub, not to this file's own list."""
    archive = (
        ROOT
        / "archive/frontend/arkadia-prism/web/public_prism/src/pages"
    )
    for name in ("DistributePage", "LivingLarderPage", "SpiralGrovePage"):
        assert (archive / f"{name}.tsx").exists(), (
            f"{name}.tsx is missing from the archive; the hub inventory this guard "
            f"covers has moved and DECLARED_HUB_SUBVIEWS needs re-measuring"
        )


def test_detector_flags_the_pre_repair_shape() -> None:
    """Negative control: the detector must redden on the text it was written for."""
    result = classify(PRE_REPAIR_SHAPE)
    assert result["violations"], (
        "the detector is silent on the pre-repair shape it exists to catch"
    )
    assert any("blanket UNKNOWN" in v for v in result["violations"])


def test_detector_is_not_trivially_true() -> None:
    """Positive control: the live page must be reported clean."""
    assert classify(SOURCE)["violations"] == []
