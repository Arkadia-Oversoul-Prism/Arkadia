#!/usr/bin/env python3
"""Decide whether an open pull request still has anything to contribute.

"Open" is not "unfinished", and it is not "already landed" either. The queue holds
many draft PRs whose work has been merged by another route, and nothing in the tree
distinguished those from live work:

* ``scripts/open_pr_inventory.py`` reads ``mergeable``/``mergeable_state`` — "can this
  land", not "has it landed";
* ``scripts/pr_wave_dry_run.py`` (#736) composes heads in a throwaway worktree and lets
  ``git merge`` decide conflict-freedom — a different question again;
* ``scripts/pr_batch_reconcile.py`` (#733) reports dependency and path-overlap clusters.

The only input a non-destructive closure decision needs is the one none of them answers.

**Why content-addressed, not ``git cherry``.** A squash merge rewrites commits, so
patch-id comparison reports every squashed PR as unlanded. GitHub's
``GET /pulls/{n}/files`` carries the *blob sha* of each changed path at the PR head, so
comparing that to the blob at the base-branch head decides the question without
depending on commit identity.

Read-only: ``GET`` requests only, plus local ``git ls-tree``. It never mutates a pull
request, never pushes, and never grants readiness or closure authority.

Usage:
    python scripts/pr_integration_oracle.py
    python scripts/pr_integration_oracle.py --json
    python scripts/pr_integration_oracle.py --prs 744,736 --base origin/main
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"
UA = "arkadia-pr-integration-oracle"

# The files endpoint truncates a PR's file list. A truncated list cannot decide the
# question, so it must read UNKNOWN rather than "the paths I saw are landed".
FILE_LIST_CEILING = 3000

INTEGRATED = "INTEGRATED"
PARTIAL = "PARTIAL"
CONTRIBUTES = "CONTRIBUTES"
UNKNOWN = "UNKNOWN"

# statuses whose head blob can be compared directly against the base tree
_DIRECT_STATUSES = frozenset({"added", "modified", "changed", "copied"})


def _token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "github_token"):
        value = os.environ.get(name)
        if value:
            return value
    return None


def _get(url: str, token: str, api: str = API) -> tuple[int, object]:
    """Return (status, json-or-None). Never echoes the token."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return 0, None


def blob_map(repo_root: str, rev: str) -> dict[str, str] | None:
    """``path -> blob sha`` for every blob in ``rev``'s tree, or None if unresolvable."""
    proc = subprocess.run(
        ["git", "-C", repo_root, "ls-tree", "-r", "-z", rev],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    out: dict[str, str] = {}
    for record in proc.stdout.split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            continue
        out[path] = parts[2]
    return out


def _classify_path(entry: dict, base_blobs: dict[str, str]) -> bool | None:
    """True when this path already carries the PR's content at base."""
    path = entry.get("filename")
    status = entry.get("status")
    head_blob = entry.get("sha")
    if not path or not status:
        return None

    if status == "removed":
        return path not in base_blobs

    if status == "renamed":
        previous = entry.get("previous_filename")
        if not previous or not head_blob:
            return None
        return base_blobs.get(path) == head_blob and previous not in base_blobs

    if status in _DIRECT_STATUSES:
        if not head_blob:
            return None
        return base_blobs.get(path) == head_blob

    return None


def classify(files: list[dict], base_blobs: dict[str, str]) -> tuple[str, list[dict]]:
    """Decide a single PR from its changed paths.

    ``INTEGRATED``  every changed path already carries the PR's content at base.
    ``PARTIAL``     at least one path landed and at least one still differs.
    ``CONTRIBUTES`` no changed path is already at base.
    ``UNKNOWN``     a path could not be decided, the list was truncated, or the
                    list is empty.

    An empty list is ``UNKNOWN``, never ``INTEGRATED``. ``pr_files`` returns
    ``None`` when the endpoint could not be read, and a lenient reader that
    treats "no paths" as "nothing outstanding" reports an unreadable PR as
    landed -- the one direction that would justify closing live work.
    """
    if len(files) >= FILE_LIST_CEILING:
        return UNKNOWN, []

    rows: list[dict] = []
    for entry in files:
        landed = _classify_path(entry, base_blobs)
        rows.append(
            {
                "path": entry.get("filename"),
                "status": entry.get("status"),
                "head_blob": entry.get("sha"),
                "base_blob": base_blobs.get(entry.get("filename") or ""),
                "landed": landed,
            }
        )

    if any(row["landed"] is None for row in rows):
        return UNKNOWN, rows
    if not rows:
        return UNKNOWN, rows
    if all(row["landed"] for row in rows):
        return INTEGRATED, rows
    if not any(row["landed"] for row in rows):
        return CONTRIBUTES, rows
    return PARTIAL, rows


def _url(api: str, path: str, **params: object) -> str:
    query = urllib.parse.urlencode(params)
    return f"{api.rstrip('/')}{path}" + (f"?{query}" if query else "")


def list_open_prs(token: str, repo: str, api: str = API) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        status, payload = _get(
            _url(api, f"/repos/{repo}/pulls", state="open", per_page=100, page=page), token, api
        )
        if status != 200 or not isinstance(payload, list):
            break
        out.extend(payload)
        if len(payload) < 100:
            break
        page += 1
    return out


def pr_files(token: str, repo: str, number: int, api: str = API) -> list[dict] | None:
    """The PR's changed paths, or ``None`` when the endpoint could not be read.

    ``None`` is distinct from ``[]`` on purpose: a rate limit, a 403 or a network
    failure must not be reported as an empty diff, because an empty diff is not a
    landing claim and an unreadable one certainly is not.
    """
    out: list[dict] = []
    page = 1
    while True:
        status, payload = _get(
            _url(api, f"/repos/{repo}/pulls/{number}/files", per_page=100, page=page), token, api
        )
        if status != 200 or not isinstance(payload, list):
            return None
        out.extend(payload)
        if len(payload) < 100 or len(out) >= FILE_LIST_CEILING:
            return out
        page += 1


def evaluate(
    prs: list[dict],
    token: str,
    repo: str,
    base_blobs: dict[str, str],
    base_rev: str,
    api: str = API,
) -> list[dict]:
    rows: list[dict] = []
    for pr in prs:
        number = pr.get("number")
        files = pr_files(token, repo, int(number), api)
        if files is None:
            rows.append(
                {
                    "number": number,
                    "title": (pr.get("title") or "")[:80],
                    "head": (pr.get("head") or {}).get("sha"),
                    "changed_paths": None,
                    "verdict": UNKNOWN,
                    "reason": "file_list_unavailable",
                    "base_rev": base_rev,
                    "paths": [],
                }
            )
            continue
        verdict, detail = classify(files, base_blobs)
        rows.append(
            {
                "number": number,
                "title": (pr.get("title") or "")[:80],
                "head": (pr.get("head") or {}).get("sha"),
                "changed_paths": len(files),
                "verdict": verdict,
                "reason": "empty_diff" if not files else "",
                "base_rev": base_rev,
                "paths": detail,
            }
        )
    return rows


def render_table(rows: list[dict]) -> str:
    lines = [f"{'PR':>5}  {'verdict':<10} {'paths':>5}  title"]
    for row in rows:
        paths = "n/a" if row["changed_paths"] is None else str(row["changed_paths"])
        lines.append(
            f"{row['number']:>5}  {row['verdict']:<10} {paths:>5}  {row['title']}"
        )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    summary = "  ".join(f"{k}={counts[k]}" for k in sorted(counts))
    lines.append("")
    lines.append(f"{len(rows)} open PRs  |  {summary}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decide whether an open PR still contributes.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--api", default=API)
    parser.add_argument("--repo-root", default=os.getcwd())
    parser.add_argument("--base", default="origin/main", help="revision to compare against")
    parser.add_argument("--prs", default="", help="comma-separated PR numbers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    token = _token()
    if not token:
        print("no GitHub token in GH_TOKEN/GITHUB_TOKEN", file=sys.stderr)
        return 2

    base_sha = subprocess.run(
        ["git", "-C", args.repo_root, "rev-parse", args.base],
        capture_output=True,
        text=True,
    )
    if base_sha.returncode != 0:
        print(f"cannot resolve base revision {args.base!r}", file=sys.stderr)
        return 2
    base_rev = base_sha.stdout.strip()

    base_blobs = blob_map(args.repo_root, base_rev)
    if base_blobs is None:
        print(f"cannot read the tree at {base_rev}", file=sys.stderr)
        return 2

    prs = list_open_prs(token, args.repo, args.api)
    if args.prs:
        wanted = {int(n) for n in args.prs.split(",") if n.strip()}
        prs = [pr for pr in prs if int(pr.get("number", 0)) in wanted]

    rows = evaluate(prs, token, args.repo, base_blobs, base_rev, args.api)

    if args.json:
        print(json.dumps({"base_rev": base_rev, "pull_requests": rows}, indent=2))
    else:
        print(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
