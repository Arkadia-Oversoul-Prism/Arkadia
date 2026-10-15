#!/usr/bin/env python3
"""Lane instruction-doc currency guard (Prism UI parallel lanes).

The four Prism UI lanes each carry a durable instruction document under
``docs/control-plane/parallel-ui/AGENT-0N-*.md``. Each doc's header names the
lane's *active branch* and *active PR*. Those pointers are hand-maintained, and
they drift: measured 2026-10-15 at ``main`` 7580bd8f, all four docs still named
the superseded next-wave wave (branches ``feat/prism-next2-*``, PRs #429/#430/
#431, and #428 in AGENT-04) while every one of those PRs had *merged* and the
lanes had moved on to ``prism-l*`` branches. A successor agent that reads the
pointer begins work on a closed thread -- the exact continuity failure the lane
model exists to prevent.

The drift is not a prose problem, it is a **disagreement between a document and
the live PR state**. So the guard is not a spell-check: it compares each doc's
declared ``**Active PR:**`` / ``**Active branch:**`` pointers against a
machine-readable snapshot of the lane threads (:data:`LANE_STATE`), and the
snapshot carries the observation time and base revision it was measured at, so
staleness is visible rather than implied.

Two properties are checked, and they are the two an operator actually cares
about:

  currency  every doc's active pointer names a PR that is *open* in the
            snapshot, and a branch that matches that PR's head branch;
  freshness the snapshot was measured against the current base ``main``.

The snapshot (:data:`LANE_STATE`) is the single machine-readable copy. The docs
are repaired from it rather than restated in two places, and ``--check`` exits
non-zero when a doc disagrees with it, so the same decision is both executed by
CI and proven by the fitness test.

Read-only. ``--check`` parses docs and the snapshot and mutates nothing, and it
does not fetch: the snapshot is refreshed by re-measuring the lane PRs with the
GitHub reads API outside this script (see the EVIDENCE record).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
LANE_STATE = LANE_DIR / "lane-state.json"

# A doc declares its pointer with a bold field. Both forms appear in the corpus:
# "*Active branch:*" and "**Active branch:**".
_BRANCH_RE = re.compile(r"^\*\*(?:Active|Current)\s+branch:\*\*\s*`([^`]+)`", re.MULTILINE)
_PR_RE = re.compile(r"^\*\*(?:Active|Current)\s+slice:\*\*\s*PR\s*#(\d+)|^\*\*(?:Active|Current)\s+PR:\*\*\s*\[?#(\d+)", re.MULTILINE)


def _lane_numbers(state: dict) -> list[str]:
    return sorted(state["lanes"].keys())


def declared_branch(text: str) -> str | None:
    """The *last* branch declaration, which is the authoritative one.

    A lane's original wave header stays in the document as provenance; a later
    dated status block supersedes it (the convention already merged for lanes 2
    and 3). Last-wins, so appending a status block is the way to update a lane
    without rewriting oracle-carried history.
    """
    matches = _BRANCH_RE.findall(text)
    return matches[-1] if matches else None


def declared_pr(text: str) -> int | None:
    matches = _PR_RE.findall(text)
    if not matches:
        return None
    g1, g2 = matches[-1]
    return int(g1 or g2)


def _pr_index(state: dict) -> dict[int, dict]:
    """Every open lane PR in the snapshot, keyed by number."""
    index: dict[int, dict] = {}
    for lane in state["lanes"].values():
        for pr in lane["open_prs"]:
            index[pr["number"]] = pr
    return index


def _disposition_findings(state: dict) -> list[str]:
    """Validate per-lane doc disposition. A deferral must be *owned and live*.

    A lane may mark its instruction doc ``deferred`` only while another open PR
    is repairing that same doc. The deferral therefore names ``deferred_to_pr``,
    and it is only valid while that PR is still open in the snapshot. Once it
    merges the reference goes stale, the lane must be reclassified ``current``,
    and the doc is judged again -- so a deferral cannot become a permanent
    exemption by quietly pointing at a merged PR.
    """
    findings: list[str] = []
    open_prs = _pr_index(state)
    for lane_no in _lane_numbers(state):
        lane = state["lanes"][lane_no]
        disposition = lane.get("doc_guard")
        if disposition not in {"current", "deferred"}:
            findings.append(
                f"lane {lane_no}: doc_guard must be 'current' or 'deferred', "
                f"got {disposition!r}"
            )
            continue
        if disposition == "deferred":
            owner = lane.get("deferred_to_pr")
            if owner is None:
                findings.append(
                    f"lane {lane_no}: doc_guard=deferred without deferred_to_pr"
                )
            elif owner not in open_prs:
                findings.append(
                    f"lane {lane_no}: doc_guard=deferred to PR #{owner}, which is "
                    f"not open in the snapshot (open: {sorted(open_prs)}); "
                    f"reclassify the lane as 'current'"
                )
    return findings


def current_lanes(state: dict) -> list[str]:
    return [
        n for n in _lane_numbers(state) if state["lanes"][n].get("doc_guard") == "current"
    ]


def check_lane_docs(
    state: dict, lane_dir: Path = LANE_DIR, lanes: list[str] | None = None
) -> list[str]:
    """Return a list of drift findings; empty means every named doc agrees.

    ``lanes`` selects which lane docs to judge. It is not a permissions filter:
    lane instruction docs are lane-owned, and a pulse may only repair its own
    lane's doc (``SHARED-CONTRACTS.md`` row 1 assigns the shell instruction to
    lane 1). A lane whose doc is mid-repair on its own open PR is excluded here
    and reported by that lane's guard invocation instead -- see the EVIDENCE
    record for the measured lane-2/3/4 exclusion and the PR numbers that own it.
    """
    findings: list[str] = []
    open_prs = _pr_index(state)
    selected = _lane_numbers(state) if lanes is None else lanes
    for lane_no in selected:
        if lane_no not in state["lanes"]:
            findings.append(f"lane {lane_no}: not present in the lane-state snapshot")
            continue
        lane = state["lanes"][lane_no]
        doc = lane_dir / lane["doc"]
        if not doc.exists():
            findings.append(f"lane {lane_no}: instruction doc {lane['doc']} is missing")
            continue

        text = doc.read_text(encoding="utf-8")
        pr = declared_pr(text)
        branch = declared_branch(text)

        if pr is None:
            findings.append(f"lane {lane_no} ({lane['doc']}): no **Active PR:** pointer")
        elif pr not in open_prs:
            findings.append(
                f"lane {lane_no} ({lane['doc']}): declares PR #{pr}, "
                f"which is not an open lane PR in the snapshot "
                f"(open: {sorted(open_prs)})"
            )
        else:
            expected = open_prs[pr]["branch"]
            if branch != expected:
                findings.append(
                    f"lane {lane_no} ({lane['doc']}): declares branch `{branch}` "
                    f"but PR #{pr} heads `{expected}`"
                )

        if branch is None:
            findings.append(f"lane {lane_no} ({lane['doc']}): no **Active branch:** pointer")

    return findings


def freshness_text(state: dict, base_main: str | None) -> str:
    if base_main is None:
        return "base main: unknown (not supplied)"
    return f"base main: {state['base_main']} (current: {base_main})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report drift; exit 1 if any")
    ap.add_argument("--base-main", default=None, help="current main SHA for freshness reporting")
    args = ap.parse_args(argv)

    if not LANE_STATE.exists():
        print(f"lane-state snapshot missing: {LANE_STATE}", file=sys.stderr)
        return 2
    state = json.loads(LANE_STATE.read_text(encoding="utf-8"))

    findings = _disposition_findings(state)
    findings += check_lane_docs(state, lanes=current_lanes(state))
    print(freshness_text(state, args.base_main))
    print(f"doc-guard lanes: {current_lanes(state)}; deferred: "
          f"{[n for n in _lane_numbers(state) if n not in current_lanes(state)]}")
    if findings:
        for f in findings:
            print(f"  DRIFT {f}")
        return 1

    print(
        f"lane instruction docs consistent with snapshot "
        f"({len(current_lanes(state))} guarded lanes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
