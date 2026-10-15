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
  liveness  the declared PR is not *proven merged* against local git history.

Currency alone is **not sound**, because it trusts the snapshot to say which
PRs are open. A snapshot that lags (the common case: it is refreshed by a human
or a pulse, not by the guard) will still list a merged PR under ``open_prs``,
and the guard then approves a doc pointing at a closed thread -- exactly the
continuity failure it exists to prevent. Measured 2026-10-15: with ``#429``
re-added to lane 1's ``open_prs``, ``check_lane_docs`` returned no findings for
a doc declaring ``feat/prism-next2-01-shell-contract-map`` / ``#429``.

So liveness is decided by a **second, independent oracle** that does not
consult the snapshot's opinion at all: every merged lane PR records its
``merge_commit_sha``, and a PR is *proven merged* when that commit is an
ancestor of the checked-out revision (``git merge-base --is-ancestor``). Local
git history is the truth here, so a stale snapshot can no longer launder a
merged PR into an open one. The oracle is deliberately one-directional: it can
prove *merged*, never *open* (an absent commit proves nothing), so it is a
rejection rule layered on top of the snapshot, not a replacement for it.

Freshness is **reported, not asserted**: the guard cannot know the current
``main`` without the network, so ``--check`` prints the comparison and fails
only when the caller supplies ``--base-main``. The docstring says so because the
earlier revision claimed freshness was checked while the workflow never passed
``--base-main`` at all.

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
import subprocess
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


def merged_pr_commits(state: dict) -> dict[int, str]:
    """Every recorded merged lane PR, mapped to its merge commit.

    ``merge_commit_sha`` is the independent half of the snapshot: it is not an
    opinion about what is open, it is a commit that either is or is not in local
    history. A snapshot missing it cannot support the liveness check, which is
    reported as a snapshot defect rather than passed silently.
    """
    merged: dict[int, str] = {}
    for lane in state["lanes"].values():
        for entry in lane.get("merged_prs", []):
            if isinstance(entry, dict):
                merged[int(entry["number"])] = entry.get("merge_commit_sha", "")
            else:
                # Bare-int form is tolerated but carries no commit, so liveness
                # cannot be decided from it; recorded as "" and reported.
                merged[int(entry)] = ""
    return merged


def merged_pr_numbers(state: dict) -> set[int]:
    """The set of PR numbers the snapshot records as merged."""
    return {int(entry["number"]) if isinstance(entry, dict) else int(entry)
            for lane in state["lanes"].values()
            for entry in lane.get("merged_prs", [])}


def commit_is_present(commit: str, repo: Path = REPO) -> bool:
    """True when the clone actually holds ``commit`` as a commit object.

    Distinguished from ancestry on purpose. On a shallow clone
    (``fetch-depth: 1``) the merge commits of long-merged PRs are absent, so
    ``git merge-base --is-ancestor`` exits 128 and a naive reader would score
    every PR as "not merged" -- a silent pass in exactly the direction that
    hides the defect this oracle exists to catch. Reporting "cannot decide" is
    the only sound answer there.
    """
    if not commit:
        return False
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo,
        capture_output=True,
    )
    return proc.returncode == 0


def is_ancestor_of_head(commit: str, repo: Path = REPO) -> bool:
    """True when ``commit`` is an ancestor of the checked-out revision.

    Read-only: ``git merge-base --is-ancestor`` exits 0/1 and writes nothing.
    Callers must have established ``commit_is_present`` first; an unknown
    object exits 128 and is reported as *not* an ancestor here, which is why
    the caller treats "absent object" as undecidable rather than as a pass.
    """
    if not commit:
        return False
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=repo,
        capture_output=True,
    )
    return proc.returncode == 0


def _liveness_findings(state: dict, repo: Path = REPO) -> list[str]:
    """Flag a PR the snapshot *claims is open* that is provably already merged.

    This is the check a stale snapshot cannot defeat, because it never trusts
    ``open_prs`` to be true -- it tests that claim against local git history.
    ``merged_prs`` records each merged lane PR's merge commit, and
    ``git merge-base --is-ancestor`` decides whether that commit is in history.
    So a snapshot refreshed carelessly (a merged PR left under ``open_prs``, or
    a ``deferred_to_pr`` pointing at a thread that has since merged) is reported
    instead of laundering a closed thread into an open one.

    Scoped to what the guard owns. It is deliberately *not* a per-doc check on
    the deferred lanes: lanes 2/3/4 are mid-repair on their own open PRs
    (SHARED-CONTRACTS.md row 1 gives lane 1 only the shell doc), so a deferred
    doc naming its *previous* merged wave is expected and is judged by the PR
    that owns it -- not by this guard. What lane 1 can and must judge is whether
    the snapshot's own open-PR claims are sound, and that is this function.
    """
    findings: list[str] = []
    merged = merged_pr_commits(state)
    for lane_no in _lane_numbers(state):
        lane = state["lanes"][lane_no]
        claimed_open = [pr["number"] for pr in lane["open_prs"]]
        owner = lane.get("deferred_to_pr")
        if owner is not None:
            claimed_open.append(owner)
        for number in claimed_open:
            commit = merged.get(number)
            if not commit:
                continue
            if not commit_is_present(commit, repo=repo):
                findings.append(
                    f"lane {lane_no}: PR #{number} cannot be adjudicated -- merge "
                    f"commit {commit[:8]} is not in this clone (shallow checkout?); "
                    f"liveness is UNKNOWN, not a pass"
                )
                continue
            if is_ancestor_of_head(commit, repo=repo):
                findings.append(
                    f"lane {lane_no}: PR #{number} is recorded as open but its "
                    f"merge commit {commit[:8]} is already an ancestor of HEAD -- "
                    f"the snapshot is stale; re-measure the lane PRs"
                )
    return findings


def _merge_commit_findings(state: dict) -> list[str]:
    """Every recorded merged PR must carry a merge commit, or liveness is blind.

    The liveness oracle is only as good as the snapshot's ``merged_prs``. If an
    entry is a bare PR number the guard silently loses the ability to prove that
    PR merged, and a stale ``open_prs`` entry naming it would pass. Requiring the
    commit turns that silent hole into a reported snapshot defect.
    """
    findings: list[str] = []
    for lane_no in _lane_numbers(state):
        for entry in state["lanes"][lane_no].get("merged_prs", []):
            if not isinstance(entry, dict):
                findings.append(
                    f"lane {lane_no}: merged_prs entry {entry!r} is a bare PR "
                    f"number; record {{'number': .., 'merge_commit_sha': ..}} so "
                    f"the liveness oracle can decide it"
                )
            elif not entry.get("merge_commit_sha"):
                findings.append(
                    f"lane {lane_no}: merged PR #{entry.get('number')} has no "
                    f"merge_commit_sha; liveness cannot be decided for it"
                )
    return findings


def resolve_main(repo: Path = REPO) -> str | None:
    """The current ``main`` SHA from local refs, or None when unresolvable.

    Read-only and network-free: it reads the already-fetched ``origin/main``
    ref. Returning None (a shallow or detached clone) is reported as unknown
    rather than passed, so the guard never claims a freshness it did not check.
    """
    for ref in ("origin/main", "main"):
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    return None


def _freshness_findings(state: dict, current_main: str | None) -> list[str]:
    """Flag a snapshot measured against a superseded ``main``.

    A stale snapshot is what makes the currency check unsound, so this is an
    assertion when ``main`` can be resolved, not merely a printed note. When it
    cannot be resolved the caller reports ``unknown`` and the check abstains --
    an unprovable freshness is not a pass, and it is not a drift claim either.
    """
    if current_main is None:
        return []
    if state.get("base_main") != current_main:
        return [
            f"snapshot base_main {state.get('base_main')} != current main "
            f"{current_main}; re-measure the lane PRs and refresh the snapshot"
        ]
    return []


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
        return f"base main: {state['base_main']} (current: unknown -- not resolvable)"
    return f"base main: {state['base_main']} (current: {base_main})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report drift; exit 1 if any")
    ap.add_argument(
        "--base-main",
        default=None,
        help="current main SHA; default is resolved from local refs (origin/main)",
    )
    args = ap.parse_args(argv)

    if not LANE_STATE.exists():
        print(f"lane-state snapshot missing: {LANE_STATE}", file=sys.stderr)
        return 2
    state = json.loads(LANE_STATE.read_text(encoding="utf-8"))

    base_main = args.base_main if args.base_main is not None else resolve_main()

    findings = _disposition_findings(state)
    findings += _merge_commit_findings(state)
    findings += _freshness_findings(state, base_main)
    findings += check_lane_docs(state, lanes=current_lanes(state))
    findings += _liveness_findings(state)
    print(freshness_text(state, base_main))
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
