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

That one-directionality left a second continuity hole, and it is the more
dangerous one because it is silent. Local ancestry can prove *merged*; it can
never prove *closed without merging*, which is precisely the state a lane
instruction must stop naming. Measured 2026-10-24: **all ten** PRs the snapshot
listed under ``open_prs`` were closed, and three of those ten had never merged.
The guard printed "lane instruction docs consistent with snapshot" regardless,
so a successor agent would have been sent to a dead thread -- the failure the
lane model exists to prevent. ``merged_prs`` only covers PRs the snapshot
already believes merged, so a PR the snapshot wrongly believes open is never
tested at all.

Hence the **authoritative** oracle: :func:`fetch_pr_records` reads live PR
state from the GitHub REST API (read-only, ``GET`` only) and
:func:`_pr_state_findings` requires every claimed-open lane PR -- including a
``deferred_to_pr`` -- to be reported *open*, with ``merged`` read separately
from ``state`` because GitHub returns ``closed`` for both a merged and an
abandoned PR. It is opt-in via ``--verify-live`` so the default ``--check``
stays offline, and every failure to obtain state (no token, transport error,
non-200) is ``UNKNOWN`` and fails closed rather than reading as open.

Freshness is decided by a **guarded-path window**, not by SHA equality. The
earlier rule was ``snapshot.base_main == current main``, which conflates two
different conditions: a snapshot can be perfectly current while ``main`` has
moved, as long as the movement did not touch anything the snapshot governs.
Measured 2026-10-24 at ``main`` 68acf89f: 31 commits had landed since the
snapshot's ``7580bd8f``, exactly **two** of them touched
``docs/control-plane/parallel-ui/``, and the four lane docs agreed with the
snapshot -- yet the guard reported drift, because the SHAs differed. A rule
that reddens on unrelated merges trains its operators to ignore it.

So staleness is now: does any commit in ``(base_main, current_main]`` touch a
**guarded path** (the lane docs the snapshot names, plus the snapshot itself)?
The commit that recorded the snapshot is exempt -- it *is* the measurement, so
it cannot invalidate itself. Every way of failing to establish that window
(unresolvable base, a base that is not an ancestor of current ``main``, an
unreadable clone) is reported as drift rather than passed: an unprovable
freshness is not a pass, and it is not a pass in the direction that matters,
because it would let a genuinely superseded snapshot through.

The snapshot (:data:`LANE_STATE`) is the single machine-readable copy. The docs
are repaired from it rather than restated in two places, and ``--check`` exits
non-zero when a doc disagrees with it, so the same decision is both executed by
CI and proven by the fitness test.

Read-only. ``--check`` parses docs and the snapshot and mutates nothing, and it
does not fetch: the snapshot is refreshed by re-measuring the lane PRs with the
GitHub reads API outside this script (see the EVIDENCE record). ``--verify-live``
adds the one read-only network call the guard can make -- ``GET`` on each
claimed-open PR -- so the authoritative liveness oracle can be executed rather
than merely described; it is opt-in so the default check stays offline.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
LANE_STATE = LANE_DIR / "lane-state.json"

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"

# A doc declares its pointer with a bold field. Both forms appear in the corpus:
# "*Active branch:*" and "**Active branch:**".
_BRANCH_RE = re.compile(r"^\*\*(?:Active|Current)\s+branch:\*\*\s*`([^`]+)`", re.MULTILINE)
_PR_RE = re.compile(r"^\*\*(?:Active|Current)\s+slice:\*\*\s*PR\s*#(\d+)|^\*\*(?:Active|Current)\s+PR:\*\*\s*\[?#(\d+)", re.MULTILINE)
# A lane that holds no open PR must *state* that, not leave the pointer blank:
# an omitted pointer is indistinguishable from a doc that forgot to declare one,
# which is the defect this check exists to catch. The declaration is therefore
# positive and machine-checkable, so "no active thread" cannot be spelled by
# silence.
_IDLE_RE = re.compile(r"^\*\*Active\s+thread:\*\*\s*`?none`?\b", re.MULTILINE)


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


def declared_idle(text: str) -> bool:
    """Whether the doc positively declares that it holds no active thread.

    Last-wins like :func:`declared_pr`: a lane that later opens a thread appends
    its new pointer, and the newest declaration is the authoritative one. The
    comparison is by *position*, not by kind, so an appended ``**Active PR:**``
    supersedes an earlier idle declaration and vice versa.
    """
    pr = _PR_RE.search(text)
    idle = _IDLE_RE.search(text)
    if idle is None:
        return False
    return pr is None or idle.start() > pr.start()


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


def clone_is_shallow(repo: Path = REPO) -> bool:
    """True when this clone's history is truncated.

    A shallow checkout grafts HEAD's ancestry, so ``merge-base --is-ancestor``
    cannot walk past the graft and exits non-zero for a commit that *is* an
    ancestor in the real history. That is the opposite conclusion from a
    rewritten ``main``, and the two need opposite responses: a truncated clone
    is repaired by fetching history, a rewritten ``main`` by re-measuring the
    lane PRs. Reporting the first as the second sends an operator to
    investigate a rewrite that never happened.

    Measured 2026-10-26 at ``main`` 36f53be2: on a depth-1 clone the guard
    reported "the recorded provenance is void (was main rewritten?)" for
    ``base_main`` 68acf89f, and the identical tree returned exit 0 from
    ``--check`` after ``git fetch --unshallow``. The commit was present in both
    clones, so only the ancestry walk was truncated.

    Read-only. A git failure reports *not* shallow, so the caller falls back to
    the ancestry verdict rather than claiming a truncation it did not observe.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


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

    A merge commit that is *present but unwalkable* is split out by
    :func:`clone_is_shallow`, for the same reason ``_freshness_findings`` splits
    its non-ancestor branch: on a truncated checkout the graft on HEAD stops the
    ancestry walk, so a non-ancestor verdict is undecidable rather than a
    "not merged" pass.
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
                continue
            if clone_is_shallow(repo=repo):
                # The commit is present but unwalkable: the graft on HEAD stops
                # the ancestry walk, so "not an ancestor" here does not mean
                # "not merged". Scoring it as *not* merged is a silent pass in
                # exactly the direction this oracle exists to catch -- a
                # snapshot still claiming a merged PR is open would go
                # unreported. Fail closed instead; the diagnosis is the same
                # split :func:`_freshness_findings` makes, for the same reason.
                findings.append(
                    f"lane {lane_no}: PR #{number} cannot be adjudicated -- merge "
                    f"commit {commit[:8]} is in this clone but this is a *shallow* "
                    f"checkout, whose graft truncates the ancestry walk; liveness "
                    f"is UNKNOWN, not a pass -- re-run from a full clone "
                    f"(fetch-depth: 0 / git fetch --unshallow)"
                )
    return findings


def claimed_open_prs(state: dict) -> dict[int, list[str]]:
    """Every PR the snapshot claims is open, mapped to where the claim is made.

    Two places make an open-claim, and both are load-bearing: ``open_prs`` (the
    lane's live threads) and ``deferred_to_pr`` (a lane whose doc is being
    repaired elsewhere). A deferral pointing at a closed PR is the same
    continuity defect as an ``open_prs`` entry that has closed -- it tells a
    successor agent the doc is being handled by a thread that no longer exists --
    so both are collected here and judged by one rule.
    """
    claims: dict[int, list[str]] = {}
    for lane_no in _lane_numbers(state):
        lane = state["lanes"][lane_no]
        for pr in lane.get("open_prs", []):
            claims.setdefault(int(pr["number"]), []).append(f"lane {lane_no} open_prs")
        owner = lane.get("deferred_to_pr")
        if owner is not None:
            claims.setdefault(int(owner), []).append(f"lane {lane_no} deferred_to_pr")
    return claims


def _pr_state_findings(
    state: dict, records: dict[int, dict], failure: str | None = None
) -> list[str]:
    """Require every claimed-open lane PR to be *authoritatively* open.

    The local-ancestry oracle in :func:`_liveness_findings` can only prove
    *merged*. It is silent on a PR that was closed without merging, which is the
    state a lane instruction most needs to stop naming, and it cannot confirm
    that a PR is still open at all. Measured 2026-10-24: ten PRs recorded under
    ``open_prs`` were closed -- three of them never merged -- and the guard
    passed, because ``merged_prs`` only ever covered PRs the snapshot already
    believed merged.

    So this is the authoritative half: live PR state, fetched read-only. The
    decision table is total and fails closed.

      OPEN            the claim stands.
      MERGED          the claim is stale -- re-measure and re-point the lane.
      CLOSED_UNMERGED the claim is stale *and* the thread is dead -- the case
                      local ancestry can never see.
      UNKNOWN         no token, transport error, non-200, or a PR number absent
                      from the response. Reported, never treated as open.

    ``merged`` is read separately from ``state`` because GitHub reports
    ``state == "closed"`` for a merged PR *and* for an abandoned one; collapsing
    them would make the two findings above indistinguishable to an operator.
    """
    if failure:
        return [
            f"live PR state unavailable ({failure}); every claimed-open lane PR "
            f"is UNKNOWN, not a pass -- re-measure with GitHub read access"
        ]

    findings: list[str] = []
    for number, claimants in sorted(claimed_open_prs(state).items()):
        where = ", ".join(claimants)
        record = records.get(number)
        if record is None:
            findings.append(
                f"PR #{number} ({where}) is not in the live PR response; its state "
                f"is UNKNOWN, not a pass -- re-measure the lane PRs"
            )
            continue
        status = pr_status(record)
        if status == "OPEN":
            continue
        if status == "MERGED":
            findings.append(
                f"PR #{number} ({where}) is recorded as open but is MERGED "
                f"(merge commit {str(record.get('merge_commit_sha'))[:8]}); "
                f"re-measure the lane PRs and re-point the lane"
            )
        elif status == "CLOSED_UNMERGED":
            findings.append(
                f"PR #{number} ({where}) is recorded as open but is CLOSED without "
                f"merging; the thread is dead -- re-measure the lane PRs and "
                f"re-point the lane, do not send an agent to it"
            )
        else:
            findings.append(
                f"PR #{number} ({where}) has an unrecognised live state "
                f"{record.get('state')!r}; classified UNKNOWN, not a pass"
            )
    return findings


def _declared_pointer_findings(
    state: dict,
    records: dict[int, dict],
    failure: str | None = None,
    lane_dir: Path = LANE_DIR,
    lanes: list[str] | None = None,
) -> list[str]:
    """Require a lane doc's own declared PR to be authoritatively open.

    This closes the *deferral* hole. ``check_lane_docs`` skips a lane whose doc
    is mid-repair elsewhere, which is right for the snapshot-agreement property --
    but it meant a deferred doc's pointer was judged by nobody, and the pointer
    is exactly what a successor agent reads. Measured 2026-10-24: open PR #548
    installs ``**Active PR:** #526`` into ``AGENT-03`` and open PR #555 installs
    ``#536`` into ``AGENT-04``; #526 and #536 are both closed without merging.
    Each of those PRs passed its own gate, because both lanes were deferred.

    So liveness is judged on the *document*, for every lane, independently of
    disposition. Callers pass ``lanes`` to separate *blocking* scope (the lanes
    whose docs this guard owns) from *reporting* scope (all lanes): a dead
    pointer is always reported, and it blocks when its lane is one the guard
    judges. The old hole was that it was reported nowhere; it is not that it
    blocks nowhere.

    An earlier draft let a lane suppress this finding by naming an open "owner"
    PR that would re-point the doc. Measurement killed it: the two PRs that
    would have been named as owners each *install* a dead pointer rather than
    repair one, so the suppression would have been false. A deferral that
    suppresses a finding it does not fix is the same defect as the one being
    repaired, one level up.
    """
    if failure:
        return [
            f"live PR state unavailable ({failure}); declared lane-doc pointers "
            f"are UNKNOWN, not a pass"
        ]

    findings: list[str] = []
    for lane_no in lanes if lanes is not None else _lane_numbers(state):
        if lane_no not in state["lanes"]:
            continue
        doc = lane_dir / state["lanes"][lane_no]["doc"]
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        if declared_idle(text) and not state["lanes"][lane_no].get("open_prs"):
            # The doc positively declares no active thread and the snapshot
            # agrees the lane holds no open PR, so any earlier pointer it still
            # carries is provenance, not a live pointer. The suppression is
            # deliberately conditional on *both* facts: a lane that declares
            # idle while the snapshot lists its own open PRs keeps its pointer
            # judged here, so an idle claim cannot be used to hide live work.
            continue
        number = declared_pr(text)
        if number is None:
            # A lane with no declared PR is stating that it has no active
            # thread, which is the truthful form for an idle lane.
            continue
        record = records.get(number)
        if record is None:
            findings.append(
                f"lane {lane_no} ({doc.name}) declares PR #{number}, which is not "
                f"in the live PR response; its state is UNKNOWN, not a pass"
            )
            continue
        status = pr_status(record)
        if status == "OPEN":
            continue
        detail = "MERGED" if status == "MERGED" else (
            "CLOSED without merging" if status == "CLOSED_UNMERGED"
            else f"UNKNOWN ({record.get('state')!r})"
        )
        findings.append(
            f"lane {lane_no} ({doc.name}) declares PR #{number}, which is {detail} "
            f"-- the lane instruction points a successor agent at a dead thread; "
            f"re-point it at a live lane PR"
        )
    return findings


def pr_status(record: dict) -> str:
    """Classify one GitHub PR record into the four states the guard decides on.

    ``merged`` is consulted before ``state`` because GitHub returns
    ``state == "closed"`` for both outcomes. A record missing either field, or
    carrying a state outside the known set, is ``UNKNOWN`` -- guessing there
    would defeat the whole point of asking an authority.
    """
    state = record.get("state")
    if state == "open":
        return "OPEN"
    if state == "closed":
        if record.get("merged") is True:
            return "MERGED"
        if record.get("merged") is False:
            return "CLOSED_UNMERGED"
        return "UNKNOWN"
    return "UNKNOWN"


def fetch_pr_records(
    numbers: list[int], repo_slug: str = DEFAULT_REPO, timeout: float = 20.0
) -> tuple[dict[int, dict], str | None]:
    """Read live PR state for ``numbers`` from the GitHub REST API.

    Read-only: ``GET`` only, no mutation, and the token is never printed or
    logged. Returns ``(records, failure)`` -- exactly one of which is meaningful.
    Any transport, auth, or non-200 outcome becomes a ``failure`` string so the
    caller can fail closed; it never degrades to an empty-but-successful read,
    which would look identical to "no PRs exist" and pass every claim.
    """
    token = _github_token()
    if not token:
        return {}, "no GitHub token in GH_TOKEN/GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN"

    records: dict[int, dict] = {}
    for number in sorted(set(numbers)):
        url = f"{API}/repos/{repo_slug}/pulls/{number}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "arkadia-lane-state-guard",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    return records, f"PR #{number}: HTTP {resp.status}"
                records[number] = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return records, f"PR #{number}: HTTP {exc.code}"
        except Exception as exc:  # transport, DNS, timeout, malformed JSON
            return records, f"PR #{number}: {type(exc).__name__}"
    return records, None


def _github_token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value
    return None


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


def _rev_list(spec: str, paths: list[str], repo: Path = REPO) -> list[str] | None:
    """Commit SHAs (newest first) in ``spec`` touching ``paths``; None on failure.

    None is returned rather than an empty list because the two are *not* the
    same answer here: "no commits touched these paths" is a freshness pass, and
    a git failure that silently reads as one would convert an unprovable state
    into the most permissive verdict available.
    """
    proc = subprocess.run(
        ["git", "rev-list", spec, "--", *paths],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return [c for c in proc.stdout.split() if c]


def _freshness_findings(state: dict, current_main: str | None, repo: Path = REPO) -> list[str]:
    """Flag a snapshot superseded by movement in the paths it governs.

    The criterion is deliberately *not* ``base_main == current_main``. A
    snapshot is a measurement of the lane threads, and unrelated merges move
    ``main`` without changing any fact it records -- so SHA inequality alone is
    not staleness, and treating it as such reddens the gate on every merge.
    Measured 2026-10-24 at ``main`` 68acf89f: 31 commits had landed since the
    snapshot's ``7580bd8f``, exactly **two** touched
    ``docs/control-plane/parallel-ui/``, the four lane docs still agreed with
    the snapshot, and the guard failed anyway.

    Staleness is therefore: **a lane doc the snapshot names changed after the
    snapshot was last written.** That reference point is derived, not recorded.
    An earlier draft exempted a snapshot-declared ``refresh_commit``, which
    cannot work: the commit that writes the snapshot necessarily appears in its
    own window, so recording the exemption requires knowing a SHA that does not
    exist until the commit is made -- and any snapshot shipped without it
    re-reddens ``main`` the moment it merges. Deriving "the newest commit that
    touched the snapshot" has neither problem, and it is correct under both
    squash and merge topologies (measured: a single commit touching doc +
    snapshot, a doc edit with no refresh, a refresh *after* a doc edit, and a
    doc edit *after* a refresh all classify correctly).

    Note what this does *not* claim: a snapshot commit is treated as a
    re-measurement whether or not it really re-measured anything. That residue
    is covered by the other two oracles rather than by this one -- a doc that
    disagrees with the snapshot fails :func:`check_lane_docs`, and a snapshot
    whose PRs have closed fails :func:`_pr_state_findings`.

    Every inability to establish the window is a finding, not a pass. That
    includes an unresolvable current ``main``, a ``base_main`` absent from the
    clone, a ``base_main`` that is not an ancestor of current ``main`` (a
    rewritten ``main`` -- the recorded provenance is void), and a git failure.
    Failing closed is the only safe direction: this check exists to stop a
    superseded snapshot from laundering stale lane pointers.

    A non-ancestor ``base_main`` is split by :func:`clone_is_shallow`, because
    the ancestry exit code cannot tell a truncated checkout from a rewritten
    ``main`` and the two require opposite responses. Both remain findings; only
    the diagnosis and the instructed repair differ.
    """
    if current_main is None:
        return [
            "current main is not resolvable (shallow or detached clone?); "
            "snapshot freshness is UNKNOWN, not a pass -- re-measure the lane "
            "PRs from a clone that holds main's history"
        ]

    base = state.get("base_main")
    if not base:
        return [
            "snapshot has no base_main; freshness is UNKNOWN, not a pass -- "
            "re-measure the lane PRs"
        ]

    if not commit_is_present(base, repo=repo):
        return [
            f"snapshot base_main {base} is not in this clone; freshness is "
            f"UNKNOWN, not a pass -- re-measure the lane PRs from a full clone"
        ]

    if not is_ancestor_of_head(base, repo=repo):
        # Distinguish a truncated clone from a rewritten ``main``. The two are
        # indistinguishable from the ancestry exit code alone, and the wrong
        # diagnosis sends an operator hunting a rewrite that never happened.
        if clone_is_shallow(repo=repo):
            return [
                f"snapshot base_main {base[:8]} is not an ancestor of HEAD "
                f"{current_main[:8]} in this *shallow* clone; the checkout "
                f"truncates the ancestry walk, so whether the recorded "
                f"provenance still holds is UNKNOWN, not a pass -- re-run from a "
                f"full clone (fetch-depth: 0 / git fetch --unshallow)"
            ]
        return [
            f"snapshot base_main {base[:8]} is not an ancestor of HEAD "
            f"{current_main[:8]}; the recorded provenance is void (was main "
            f"rewritten?), so freshness is UNKNOWN, not a pass -- re-measure "
            f"the lane PRs against the current main"
        ]

    snapshot_commits = _rev_list(
        f"{base}..{current_main}", [str(LANE_STATE.relative_to(REPO))], repo=repo
    )
    if snapshot_commits is None:
        return [
            f"cannot read the snapshot's history in {base[:8]}..{current_main[:8]}; "
            f"freshness is UNKNOWN, not a pass -- re-measure the lane PRs"
        ]
    reference = snapshot_commits[0] if snapshot_commits else base

    docs = guarded_doc_paths(state)
    changed = _rev_list(f"{reference}..{current_main}", docs, repo=repo)
    if changed is None:
        return [
            f"cannot compute the guarded-path window {reference[:8]}.."
            f"{current_main[:8]}; freshness is UNKNOWN, not a pass -- "
            f"re-measure the lane PRs"
        ]

    if changed:
        return [
            f"snapshot is stale: {len(changed)} commit(s) since it was recorded "
            f"({reference[:8]}) changed a guarded lane doc ({', '.join(docs)}) -- "
            f"re-measure the lane PRs and refresh the snapshot "
            f"(first: {changed[0][:8]})"
        ]
    return []


def guarded_doc_paths(state: dict) -> list[str]:
    """The lane instruction docs whose movement makes the snapshot stale.

    Derived from the snapshot rather than hardcoded, so adding a lane cannot
    silently leave its doc unguarded. The snapshot file itself is deliberately
    *excluded*: it is the reference point the comparison is anchored on, so
    including it would make every refresh invalidate itself.
    """
    return sorted(
        str((LANE_DIR / lane["doc"]).relative_to(REPO))
        for lane in state["lanes"].values()
        if lane.get("doc")
    )


def guarded_paths(state: dict) -> list[str]:
    """Every path the guard owns: the lane docs plus the snapshot itself.

    Reported for operator context and used where a total inventory is wanted
    (the printed freshness line). The freshness *decision* uses
    :func:`guarded_doc_paths`, which omits the snapshot so a refresh cannot
    invalidate itself.
    """
    return sorted(
        set(guarded_doc_paths(state)) | {str(LANE_STATE.relative_to(REPO))}
    )


def _disposition_findings(state: dict) -> list[str]:
    """Validate per-lane doc disposition. A deferral must be *owned and live*.

    A lane may mark its instruction doc ``deferred`` only while another open PR
    is repairing that same doc. The deferral therefore names ``deferred_to_pr``,
    and it is only valid while that PR is still open in the snapshot. Once it
    merges the reference goes stale, the lane must be reclassified ``current``,
    and the doc is judged again -- so a deferral cannot become a permanent
    exemption by quietly pointing at a merged PR.

    ``idle`` is the third state, for a lane that holds no open PR at all. It is
    not an exemption: an idle lane is still judged by :func:`check_lane_docs`
    and must positively declare ``**Active thread:** none``. Without it the
    guard was unsatisfiable for an empty lane -- the doc was required to name an
    open PR, and a lane holding none cannot name one, so *every* disposition of
    an idle lane reported drift.
    """
    findings: list[str] = []
    open_prs = _pr_index(state)
    for lane_no in _lane_numbers(state):
        lane = state["lanes"][lane_no]
        disposition = lane.get("doc_guard")
        if disposition not in {"current", "deferred", "idle"}:
            findings.append(
                f"lane {lane_no}: doc_guard must be 'current', 'deferred', or "
                f"'idle', got {disposition!r}"
            )
            continue
        if disposition == "idle":
            # ``idle`` is a claim about the lane's *own* thread count, so it is
            # checked against the lane's own open PRs. A lane that declares
            # itself idle while it lists open PRs is not idle -- it is a lane
            # whose instruction tells a successor agent to stand down while live
            # work exists, which is the continuity failure in the opposite
            # direction.
            if lane.get("open_prs"):
                findings.append(
                    f"lane {lane_no}: doc_guard=idle but the lane lists open PRs "
                    f"{sorted(p['number'] for p in lane['open_prs'])}; reclassify "
                    f"the lane as 'current'"
                )
            if lane.get("deferred_to_pr") is not None:
                findings.append(
                    f"lane {lane_no}: doc_guard=idle cannot also carry "
                    f"deferred_to_pr=#{lane['deferred_to_pr']}; pick one"
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


def current_lanes(state: dict, invert: bool = False) -> list[str]:
    """Lane numbers whose doc this guard judges.

    ``invert`` returns the complement -- the deferred lanes, which
    :func:`deferred_branch_findings` judges for the property
    :func:`check_lane_docs` cannot reach.

    An ``idle`` lane is judged, not exempted. Its doc must still *state* that it
    holds no active thread, and the snapshot must agree the lane is empty; an
    idle lane that says nothing at all is the "forgot to declare" defect, and it
    is reported by :func:`check_lane_docs`. Only ``deferred`` -- a doc mid-repair
    on another open PR -- leaves the blocking scope.
    """
    return [
        n
        for n in _lane_numbers(state)
        if (state["lanes"][n].get("doc_guard") == "deferred") is invert
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

        if declared_idle(text):
            # The lane states it holds no active thread. That is the truthful
            # form for an idle lane, and it is *checked*, not trusted: the claim
            # is only accepted while the snapshot agrees the lane is idle. A
            # lane that declares idle while the snapshot lists open PRs of its
            # own is the continuity failure in the opposite direction -- an
            # instruction telling a successor agent to stand down while live
            # work exists in this lane. (``lane["open_prs"]``, not the repo-wide
            # index: another lane's thread is not this lane's work.)
            #
            # ``declared_idle`` is last-wins, so a lane that retains its earlier
            # wave-header pointer as provenance and appends the idle block is
            # judged idle -- which is why this test does not also require
            # ``pr is None``.
            if lane.get("open_prs"):
                findings.append(
                    f"lane {lane_no} ({lane['doc']}): declares no active thread, "
                    f"but the snapshot lists open lane PRs "
                    f"{sorted(p['number'] for p in lane['open_prs'])} -- "
                    f"re-point it at a live lane PR"
                )
            continue

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


def deferred_branch_findings(
    state: dict, lane_dir: Path = LANE_DIR, lanes: list[str] | None = None
) -> list[str]:
    """Branch/head agreement for lanes ``check_lane_docs`` does not judge.

    A deferred lane's doc is mid-repair on its own open PR, so ``check_lane_docs``
    excludes it by design. That exclusion is correct for the *snapshot-agreement*
    property, but it silently dropped the branch/head agreement check as well:
    measured, a deferred lane whose doc declares a branch its PR does not head was
    reported by nobody. ``_declared_pointer_findings`` covers pointer *liveness*,
    not branch agreement, so the two are disjoint and this closes the remainder.

    Scoped to the case where the declared PR is **live in the snapshot**. When it
    is not, the pointer itself is already the finding (and is reported advisory
    today), so blocking here would duplicate a pre-existing signal rather than
    close a hole. Measured against the live snapshot at ``36f53be2``: zero new
    findings, because both deferred lanes point at dead threads -- the branch
    comparison is only meaningful once the pointer is live.
    """
    findings: list[str] = []
    open_prs = _pr_index(state)
    selected = _lane_numbers(state) if lanes is None else lanes
    for lane_no in selected:
        if lane_no not in state["lanes"] or lane_no in current_lanes(state):
            continue  # already judged by check_lane_docs
        lane = state["lanes"][lane_no]
        doc = lane_dir / lane["doc"]
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        pr = declared_pr(text)
        if pr is None or pr not in open_prs:
            continue  # pointer not live: reported by _declared_pointer_findings
        branch = declared_branch(text)
        expected = open_prs[pr]["branch"]
        if branch != expected:
            findings.append(
                f"lane {lane_no} ({lane['doc']}): declares branch `{branch}` "
                f"but PR #{pr} heads `{expected}`"
            )
    return findings


def freshness_text(state: dict, base_main: str | None) -> str:
    if base_main is None:
        return f"base main: {state['base_main']} (current: unknown -- not resolvable)"
    return (
        f"base main: {state['base_main']} (current: {base_main}); "
        f"guarded paths: {', '.join(guarded_paths(state))}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report drift; exit 1 if any")
    ap.add_argument(
        "--base-main",
        default=None,
        help="current main SHA; default is resolved from local refs (origin/main)",
    )
    ap.add_argument(
        "--verify-live",
        action="store_true",
        help=(
            "also require every claimed-open lane PR to be authoritatively open "
            "per the GitHub reads API (needs GH_TOKEN/GITHUB_TOKEN); an "
            "unavailable live state fails closed"
        ),
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
    # A deferred lane's doc is excluded above by design, which also excluded its
    # branch/head agreement check -- judged by nobody until this ran.
    findings += deferred_branch_findings(state, lanes=current_lanes(state, invert=True))
    findings += _liveness_findings(state)

    if args.verify_live:
        numbers = sorted(claimed_open_prs(state))
        declared = {
            declared_pr((LANE_DIR / state["lanes"][n]["doc"]).read_text(encoding="utf-8"))
            for n in _lane_numbers(state)
            if (LANE_DIR / state["lanes"][n]["doc"]).exists()
        }
        records, failure = fetch_pr_records(
            numbers + sorted(n for n in declared if n is not None)
        )
        findings += _pr_state_findings(state, records, failure)
        # Dead pointers block only for the lanes this guard owns. Every lane is
        # still *reported*: a finding nobody prints is the hole being repaired.
        # Blocking on a doc the guard does not own would make the gate
        # permanently red for work it cannot do -- the failure mode that trains
        # operators to ignore a gate.
        owned = current_lanes(state)
        findings += _declared_pointer_findings(state, records, failure, lanes=owned)
        advisory = [
            f
            for f in _declared_pointer_findings(state, records, failure)
            if f not in findings
        ]
        print(
            f"live PR state: {len(records)} PR(s) read from {DEFAULT_REPO} "
            f"({len(numbers)} claimed-open + declared doc pointers)"
            + (f" -- {failure}" if failure else "")
        )
        for note in advisory:
            print(f"  NOTE {note} (lane not owned by this guard; reported, not blocking)")

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
