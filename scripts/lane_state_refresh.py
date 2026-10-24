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
            "tests/test_console_shell_nav_contract.py",
            "tests/test_console_legacy_route_coverage.py",
            "tests/test_console_document_title_contract.py",
            "tests/test_console_surface_error_boundary.py",
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


def _active_thread(open_prs: list[dict]) -> tuple[int, str]:
    """The lane PR its instruction doc should name, chosen by a stated rule.

    "Most recently updated open PR in the lane" -- measured, not judged. The
    alternative is an operator's opinion about which thread is the lane's real
    continuation, which is exactly the hand-maintained pointer that drifted: at
    the point this rule was written, all four lane docs named a dead PR. A rule
    derived from live data cannot drift from live data.

    Ties break on the higher PR number so the choice is total and reproducible.
    """
    ranked = sorted(
        open_prs,
        key=lambda p: (p.get("updated_at") or "", p["number"]),
        reverse=True,
    )
    chosen = ranked[0]
    return chosen["number"], chosen["branch"]


def build(
    open_prs: list[dict], files: dict[int, list[str]], base_main: str, repo: str
) -> dict:
    lanes: dict[str, dict] = {
        lane_no: {
            "doc": spec["doc"],
            "title": spec["title"],
            "active_pr": None,
            "active_branch": None,
            "open_prs": [],
            "merged_prs": [],
            "doc_guard": "idle",
        }
        for lane_no, spec in LANE_OWNERSHIP.items()
    }

    unassigned: list[dict] = []
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

    # Disposition. A lane with a live thread is judged; a lane whose doc is being
    # repaired by another open PR defers; a lane with no live thread at all is
    # idle -- truthful about its history without pretending to own current work.
    for lane_no, lane in lanes.items():
        lane["open_prs"].sort(key=lambda p: p["number"])
        if not lane["open_prs"]:
            lane["doc_guard"] = "idle"
            continue
        lane["doc_guard"] = "deferred" if lane.get("deferred_to_pr") else "current"
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
    open_prs, files = fetch_all(token, args.repo)
    state = build(open_prs, files, base_main, args.repo)
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
