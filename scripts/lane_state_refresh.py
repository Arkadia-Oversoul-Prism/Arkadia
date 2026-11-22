#!/usr/bin/env python3
"""Re-measure the lane-state snapshot from live GitHub PR state.

Exists because the snapshot was hand-transcribed, and hand-transcription is
what produced the defect this workstream repairs: measured 2026-10-24, **all
ten** PRs the snapshot listed under ``open_prs`` had closed -- three of them
without ever merging -- so four lane instruction documents pointed at dead
threads. A snapshot an operator types by hand drifts silently; a snapshot a
script derives from the same authority that judges it (``scripts/lane_state.py
--verify-live``) cannot drift without the two disagreeing in public.

Read-only against GitHub: ``GET`` only, no mutation, and the token is never
printed. It writes exactly one file -- the snapshot -- and only when ``--write``
is passed, so the default invocation is a dry run that reports the diff.

Lane assignment is by **exclusive path ownership** (``SHARED-CONTRACTS.md`` §1),
not by PR title or author intent: a PR is recorded in every lane whose owned
paths it changes, and a PR matching no lane is recorded under
``unassigned_open_prs`` rather than dropped. Overlap is therefore visible in the
snapshot instead of being resolved by guessing.

Usage:
    python scripts/lane_state_refresh.py                 # dry run, print summary
    python scripts/lane_state_refresh.py --write         # rewrite the snapshot
    python scripts/lane_state_refresh.py --base-main <sha>
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
LANE_STATE = LANE_DIR / "lane-state.json"

# Explicit, auditable aggregate-PR classification. An *aggregate* PR composes
# other PRs' contributions (an integration/evidence baseline) and therefore
# touches paths owned by several lanes without taking ownership of any of them.
# Path ownership alone cannot tell that apart from genuine multi-lane work, so
# the distinction is declared here as data rather than inferred from a title
# substring or a branch-name convention -- both of which would silently
# misclassify a real multi-lane implementation PR.
#
# This file is the single source of truth. It is version-controlled, so every
# classification decision is reviewable in the same diff as the code that reads
# it, and no PR number is hardcoded in classifier logic.
AGGREGATE_CONFIG = LANE_DIR / "aggregate-prs.json"

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"

# Exclusive ownership markers per lane, from SHARED-CONTRACTS.md §1. A prefix
# ending in "/" matches a directory; otherwise the path must match exactly.
#
# Deliberately *narrow*. The contract's lane-4 row names "Arkana/Oracle, Weaver,
# Engineering Lab feature-local page modules/components/tests/evidence", which is
# narrower than the `weaver/` and `lab/` trees: those hold the runtime, authority,
# and acceptance surfaces the same row says lane 4 "must not edit". A blanket
# prefix over them measured wrong on the first dry run -- it swept the EAA,
# dispatch, and acceptance-authority PRs (#499/#500/#502/#508/#535/#553) into lane
# 4, none of which touch a feature-local console module. Ownership here is
# therefore the console feature surface plus the lane's own evidence records; a
# PR matching no lane is recorded as unassigned rather than attributed by guess.
LANE_OWNERSHIP: dict[str, dict] = {
    "1": {
        "doc": "AGENT-01-SHELL.md",
        "title": "Shell / navigation / design system / integration seam",
        "paths": (
            "web/arkadia_console/src/App.tsx",
            "web/arkadia_console/src/components/Shell.tsx",
            "web/arkadia_console/src/components/SurfaceLenses.tsx",
            "web/arkadia_console/src/components/ErrorBoundary.tsx",
            "web/arkadia_console/src/lib/router.ts",
            "web/arkadia_console/src/lib/surfaces.ts",
            "web/arkadia_console/src/lib/endpoints.ts",
            "web/arkadia_console/src/lib/types.ts",
            "tests/test_console_endpoint_registry_contract.py",
            "tests/test_console_shell_nav_contract.py",
            "tests/test_console_legacy_route_coverage.py",
            "tests/test_console_document_title_contract.py",
            "tests/test_console_surface_error_boundary.py",
            "tests/test_prism_solspire_control_plane.py",
        ),
    },
    "2": {
        "doc": "AGENT-02-NOVANET-OPPORTUNITY.md",
        "title": "NovaNet + project Opportunity Radar",
        "paths": (
            "web/arkadia_console/src/pages/NovaNetPage.tsx",
            "web/arkadia_console/src/components/opportunities/",
            "solspire/buyer_recon.py",
            "solspire/buyer_recon_router.py",
            "tests/test_prism_novanet_engagement_readings.py",
        ),
    },
    "3": {
        "doc": "AGENT-03-SOLARIUN-KNOWLEDGE.md",
        "title": "Solariun + Knowledge OS",
        "paths": (
            "web/arkadia_console/src/pages/KnowledgePage.tsx",
            "web/arkadia_console/src/pages/knowledge/",
            "knowledge/",
            "api/knowledge_routes.py",
            "tests/test_knowledge_graph_provenance_boundary.py",
        ),
    },
    "4": {
        "doc": "AGENT-04-ARKANA-WEAVER-LAB.md",
        "title": "Arkana + Weaver + Engineering Lab",
        "paths": (
            "web/arkadia_console/src/pages/ArkanaPage.tsx",
            "web/arkadia_console/src/pages/WeaverPage.tsx",
            "web/arkadia_console/src/components/arkana/",
            "web/arkadia_console/src/components/weaver/",
            "web/arkadia_console/src/components/lab/",
            "web/arkadia_console/src/lib/arkana.ts",
            "api/commune_threads.py",
            "weaver/engineering_router.py",
            "weaver/github_readonly_evidence_adapter.py",
            "tests/test_arkana_signal_schema_guard.py",
            "tests/test_lab_repository_surface_contract.py",
        ),
    },
}

# Paths that make a lane's doc defer to another open PR repairing that same doc.
DOC_OWNING_PREFIX = "docs/control-plane/parallel-ui/"


def _token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value
    return None


def _get(url: str, token: str, timeout: float = 30.0):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "arkadia-lane-state-refresh",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_all(token: str, repo: str) -> tuple[list[dict], dict[int, list[str]]]:
    """Every open PR with its changed-file list, plus details for each.

    The list endpoint omits ``merged``, so each PR is re-read from the detail
    endpoint: the guard decides merged-ness from ``merged``, and a list-shaped
    record would classify every closed PR as unknown.
    """
    out: list[dict] = []
    files: dict[int, list[str]] = {}
    page = 1
    while True:
        batch = _get(
            f"{API}/repos/{repo}/pulls?state=open&per_page=100&page={page}", token
        )
        if not batch:
            break
        for item in batch:
            detail = _get(f"{API}/repos/{repo}/pulls/{item['number']}", token)
            changed = _get(
                f"{API}/repos/{repo}/pulls/{item['number']}/files?per_page=100", token
            )
            files[item["number"]] = [f["filename"] for f in changed]
            out.append(detail)
        if len(batch) < 100:
            break
        page += 1
    return out, files


def lanes_for(changed: list[str]) -> list[str]:
    """Lane numbers whose exclusively-owned paths ``changed`` touches."""
    matched: list[str] = []
    for lane_no, spec in LANE_OWNERSHIP.items():
        for marker in spec["paths"]:
            if any(
                f.startswith(marker) if marker.endswith("/") else f == marker
                for f in changed
            ):
                matched.append(lane_no)
                break
    return sorted(matched)


# --------------------------------------------------------------- aggregate PRs
#
# Classification contract
# -----------------------
# A PR is classified into exactly one of three kinds:
#
#   AGGREGATE   declared in ``aggregate-prs.json``. It composes other PRs'
#               contributions. It is recorded in ``aggregate_prs`` (an explicit,
#               auditable collection) and is EXCLUDED from every lane's
#               ``open_prs`` and from ``active_pr`` selection. It is never
#               dropped: it stays visible in the snapshot and in the evidence
#               record.
#   LANE        not declared aggregate, and its changed paths match at least one
#               lane's exclusive ownership. Recorded in each matching lane --
#               including a genuine multi-lane PR, which appears in every lane it
#               touches. This is the pre-existing behaviour, preserved.
#   UNASSIGNED  not declared aggregate, and matches no lane. Recorded under
#               ``unassigned_open_prs``.
#
# Why not infer it: a title substring ("integration:") or a branch prefix
# ("integration/") would classify a genuine multi-lane implementation PR as
# aggregate and silently strip it from lane ownership. The declaration is
# therefore explicit data, and the classifier reads only that.
#
# Failure behaviour (fail closed, never silently "ordinary"):
#   * config file absent            -> no PR is aggregate; every PR is classified
#                                      by path ownership as before, and the
#                                      snapshot records ``aggregate_config``
#                                      status ``absent`` so the omission is
#                                      visible rather than assumed.
#   * config unreadable / malformed -> the refresh ABORTS (exit 2). It does not
#                                      fall back to "nothing is aggregate",
#                                      because that fallback would silently
#                                      re-admit an aggregate PR as a lane owner
#                                      -- the exact defect being repaired.
#   * a declared number not open    -> recorded in ``aggregate_prs`` with
#                                      ``state: "not_open"`` so a stale
#                                      declaration is visible, not silent.
#   * a declared number that is also a genuine lane PR -> still aggregate: the
#                                      declaration wins, and the snapshot records
#                                      the overlap under ``aggregate_prs`` so a
#                                      reviewer can see the conflict.


class AggregateConfigError(RuntimeError):
    """The aggregate classification config exists but cannot be trusted."""


def load_aggregate_config(path: Path | None = None) -> dict:
    """Read the explicit aggregate-PR declaration.

    Returns ``{"status": ..., "numbers": set[int], "entries": [...]}``. A missing
    file is a *reported* state, not an error: a repository that has never needed
    an aggregate PR should not be forced to create the file. A file that exists
    but cannot be parsed is an error, because the only safe reading of "I cannot
    tell which PRs are aggregate" is to stop, not to assume none are.
    """
    target = AGGREGATE_CONFIG if path is None else path
    if not target.exists():
        return {"status": "absent", "numbers": set(), "entries": []}
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AggregateConfigError(
            f"aggregate classification config {target} is unreadable: {exc}"
        ) from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("aggregate_prs"), list):
        raise AggregateConfigError(
            f"aggregate classification config {target} must be an object with an "
            f"'aggregate_prs' list"
        )
    numbers: set[int] = set()
    entries: list[dict] = []
    for item in raw["aggregate_prs"]:
        if not isinstance(item, dict) or not isinstance(item.get("number"), int):
            raise AggregateConfigError(
                f"aggregate classification config {target}: every entry needs an "
                f"integer 'number', got {item!r}"
            )
        numbers.add(item["number"])
        entries.append(dict(item))
    return {"status": "present", "numbers": numbers, "entries": entries}



def _active_thread(open_prs: list[dict]) -> tuple[int | None, str | None]:
    """The lane PR its instruction doc should name, chosen by a stated rule.

    "Most recently updated open PR in the lane" -- measured, not judged. The
    alternative is an operator's opinion about which thread is the lane's real
    continuation, which is exactly the hand-maintained pointer that drifted: at
    the point this rule was written, all four lane docs named a dead PR. A rule
    derived from live data cannot drift from live data.

    Ties break on the higher PR number so the choice is total and reproducible.
    """
    if not open_prs:
        # A lane with no open thread names no active PR; returning None is the
        # honest representation and the caller must not invent one.
        return (None, None)
    ranked = sorted(
        open_prs,
        key=lambda p: (p.get("updated_at") or "", p["number"]),
        reverse=True,
    )
    chosen = ranked[0]
    return chosen["number"], chosen["branch"]


def build(
    open_prs: list[dict],
    files: dict[int, list[str]],
    base_main: str,
    repo: str,
    aggregate: dict | None = None,
) -> dict:
    lanes: dict[str, dict] = {
        lane_no: {
            "doc": spec["doc"],
            "title": spec["title"],
            "active_pr": None,
            "active_branch": None,
            "open_prs": [],
            "merged_prs": [],
            "doc_guard": "deferred",
        }
        for lane_no, spec in LANE_OWNERSHIP.items()
    }

    aggregate = aggregate or {"status": "absent", "numbers": set(), "entries": []}
    aggregate_numbers: set[int] = set(aggregate.get("numbers") or set())

    unassigned: list[dict] = []
    aggregate_prs: list[dict] = []
    for pr in open_prs:
        number = pr["number"]
        changed = files.get(number, [])
        entry = {
            "number": number,
            "branch": pr["head"]["ref"],
            "head_sha": pr["head"]["sha"],
            "draft": pr["draft"],
            "updated_at": pr.get("updated_at"),
            "title": pr["title"],
        }
        matched = lanes_for(changed)

        if number in aggregate_numbers:
            # Declared aggregate: recorded in its own auditable collection and
            # excluded from lane ownership and active-thread selection. It is
            # NOT dropped -- ``lanes_touched`` keeps the fact that its diff spans
            # those lanes visible to a reviewer, which is the whole reason it
            # used to be misclassified as their owner.
            aggregate_prs.append(
                {
                    **entry,
                    "classification": "aggregate",
                    "lanes_touched": matched,
                    "reason": next(
                        (
                            e.get("reason")
                            for e in aggregate.get("entries", [])
                            if e.get("number") == number
                        ),
                        None,
                    ),
                }
            )
            continue

        if not matched:
            unassigned.append(entry)
            continue
        for lane_no in matched:
            lanes[lane_no]["open_prs"].append(dict(entry))
            if f"{DOC_OWNING_PREFIX}{LANE_OWNERSHIP[lane_no]['doc']}" in changed:
                # Only the PR that actually edits *this lane's* doc can carry its
                # deferral. Recording any open lane PR here would let a deferral
                # name a thread that never touches the doc -- a permanent
                # exemption dressed up as ownership.
                lanes[lane_no]["deferred_to_pr"] = number

    # A declared aggregate PR that is no longer open is recorded as such, so a
    # stale declaration is visible instead of silently inert.
    open_numbers = {pr["number"] for pr in open_prs}
    for declared in aggregate.get("entries", []):
        if declared["number"] not in open_numbers:
            aggregate_prs.append(
                {
                    "number": declared["number"],
                    "classification": "aggregate",
                    "state": "not_open",
                    "reason": declared.get("reason"),
                }
            )
    aggregate_prs.sort(key=lambda p: p["number"])


    # Disposition, in the vocabulary the guard accepts (``current``/``deferred``/
    # ``idle``). A lane with a live thread is judged; a lane whose doc is being
    # repaired by another open PR defers; a lane that holds no open PR at all is
    # ``idle`` -- a truthful state, not an exemption. ``current`` for an empty
    # lane was the defect: the guard still required such a doc to name an open
    # PR, which no lane can do when it holds none, so the gate was unsatisfiable
    # for every idle lane (measured 2026-10-28: 0 open PRs repo-wide, 4 idle
    # lanes, ``--check --verify-live`` red).
    for lane_no, lane in lanes.items():
        lane["open_prs"].sort(key=lambda p: p["number"])
        if lane.get("deferred_to_pr"):
            lane["doc_guard"] = "deferred"
        elif lane["open_prs"]:
            lane["doc_guard"] = "current"
        else:
            lane["doc_guard"] = "idle"
        lane["active_pr"], lane["active_branch"] = _active_thread(lane["open_prs"])
        if lane.get("deferred_to_pr") is None:
            lane.pop("deferred_to_pr", None)

    return {
        "schema": "arkadia.lane-state/1.2",
        "observed_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "base_main": base_main,
        "source": (
            f"GitHub REST reads API ({repo}), read-only, derived by "
            f"scripts/lane_state_refresh.py"
        ),
        "note": (
            "Machine-readable mirror of the four Prism UI lane threads, DERIVED "
            "from live PR state rather than hand-transcribed. Lane assignment is "
            "by exclusive path ownership (SHARED-CONTRACTS.md section 1); a PR "
            "touching more than one lane's owned paths appears in each. "
            "scripts/lane_state.py judges the docs against this file; --verify-live "
            "additionally requires every claimed-open PR to be authoritatively "
            "open. Refresh with scripts/lane_state_refresh.py --write."
        ),
        "lanes": lanes,
        "aggregate_prs": aggregate_prs,
        "aggregate_config": {
            "status": aggregate.get("status", "absent"),
            "source": str(AGGREGATE_CONFIG.relative_to(REPO)),
            "declared": sorted(aggregate_numbers),
        },
        "unassigned_open_prs": sorted(unassigned, key=lambda p: p["number"]),
    }


def merge_history(
    existing: dict, open_prs: list[dict], token: str, repo: str
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Carry forward merged history and record what has since closed.

    A PR that leaves ``open_prs`` has either merged or been closed unmerged, and
    the two must not be conflated: the merged ones keep their ``merge_commit_sha``
    so the local-ancestry oracle can still prove them, and the closed-unmerged
    ones are recorded as such so no future refresh re-lists them as open.
    """
    merged: dict[str, list[dict]] = {
        lane_no: [dict(e) for e in lane.get("merged_prs", [])]
        for lane_no, lane in existing.get("lanes", {}).items()
    }
    closed = [dict(e) for e in existing.get("closed_unmerged", [])]
    closed_numbers = {int(e["number"]) for e in closed}
    known_merged = {
        int(e["number"]) for entries in merged.values() for e in entries
    }
    previously_claimed = {
        int(p["number"])
        for lane in existing.get("lanes", {}).values()
        for p in lane.get("open_prs", [])
    }
    still_open = {pr["number"] for pr in open_prs}

    for number in sorted(previously_claimed - still_open):
        if number in known_merged or number in closed_numbers:
            continue
        detail = _get(f"{API}/repos/{repo}/pulls/{number}", token)
        if detail.get("merged"):
            owner = next(
                (
                    lane_no
                    for lane_no, lane in existing.get("lanes", {}).items()
                    if any(int(p["number"]) == number for p in lane.get("open_prs", []))
                ),
                None,
            )
            if owner is not None:
                merged.setdefault(owner, []).append(
                    {
                        "number": number,
                        "merge_commit_sha": detail.get("merge_commit_sha"),
                    }
                )
        else:
            closed.append(
                {
                    "number": number,
                    "branch": detail["head"]["ref"],
                    "state": "closed_unmerged",
                }
            )
    for lane_no in merged:
        merged[lane_no].sort(key=lambda e: e["number"])
    return merged, sorted(closed, key=lambda e: e["number"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="rewrite the snapshot")
    ap.add_argument("--base-main", default=None, help="revision the snapshot is measured against")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    args = ap.parse_args(argv)

    token = _token()
    if not token:
        print("no GitHub token in GH_TOKEN/GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN", file=sys.stderr)
        return 2

    base_main = args.base_main
    if not base_main:
        import subprocess

        base_main = subprocess.run(
            ["git", "rev-parse", "origin/main"], cwd=REPO, capture_output=True, text=True
        ).stdout.strip()
    if len(base_main) != 40:
        print(f"base main is not a full 40-char SHA: {base_main!r}", file=sys.stderr)
        return 2

    existing = json.loads(LANE_STATE.read_text(encoding="utf-8"))
    try:
        aggregate = load_aggregate_config()
    except AggregateConfigError as exc:
        # Fail closed. Falling back to "nothing is aggregate" would silently
        # re-admit an aggregate PR as a lane owner -- the defect being repaired.
        print(f"aggregate classification unavailable: {exc}", file=sys.stderr)
        return 2
    open_prs, files = fetch_all(token, args.repo)
    state = build(open_prs, files, base_main, args.repo, aggregate=aggregate)
    merged, closed = merge_history(existing, open_prs, token, args.repo)
    for lane_no, entries in merged.items():
        if lane_no in state["lanes"]:
            state["lanes"][lane_no]["merged_prs"] = entries
    state["closed_unmerged"] = closed

    for lane_no, lane in sorted(state["lanes"].items()):
        print(
            f"lane {lane_no}: doc_guard={lane['doc_guard']:<8} "
            f"active=#{lane['active_pr']} open={[p['number'] for p in lane['open_prs']]} "
            f"merged={[e['number'] for e in lane['merged_prs']]}"
        )
    print(f"unassigned open PRs: {[p['number'] for p in state['unassigned_open_prs']]}")
    print(
        f"aggregate PRs (excluded from lane ownership): "
        f"{[p['number'] for p in state['aggregate_prs']]} "
        f"(config: {state['aggregate_config']['status']})"
    )
    print(f"closed unmerged: {[e['number'] for e in closed]}")

    rendered = json.dumps(state, indent=1, sort_keys=False) + "\n"
    if not args.write:
        print(f"\ndry run -- {LANE_STATE.relative_to(REPO)} not modified (pass --write)")
        return 0
    LANE_STATE.write_text(rendered, encoding="utf-8")
    print(f"\nwrote {LANE_STATE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
