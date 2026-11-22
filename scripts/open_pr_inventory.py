#!/usr/bin/env python3
"""Open-PR inventory (gate-hygiene recon).

Builds a reproducible inventory of a repository's open pull requests. Exists to
retire ad-hoc, non-durable recon: the queue is a live fact, so it must be
re-derivable by an independent operator rather than carried in an agent's
memory or a previous pass's prose.

The defect this fixes: the GitHub *list* endpoint
(`GET /repos/{owner}/{repo}/pulls?state=open`) omits `mergeable` and
`mergeable_state`; only the *detail* endpoint (`GET /repos/{owner}/{repo}/pulls/{n}`)
exposes them. An inventory that reads `pr["mergeable"]` off a list item raises
`KeyError: 'mergeable'`. This module reads `mergeable` only from the detail
endpoint and treats a `null` value (GitHub still computing it) as `UNKNOWN`
rather than crashing.

Read-only: only `GET` requests. Never prints the token. No mutation.

Composition conflicts
---------------------
A PR's `mergeable` field answers only "does this merge into its *base*", never
"can these two merge together". With a queue of open PRs that question decides
merge order, and two branches can each be `MERGEABLE` against `main` while
conflicting with each other. `--conflicts` answers it locally from git, with no
network call: `git merge-tree --write-tree` performs the merge in the object
database and reports conflicted paths, so no worktree is touched.

    python scripts/open_pr_inventory.py --conflicts \
        --ref 681=refs/pr/681 --ref 687=refs/pr/687

A revision git cannot resolve is `UNPROVABLE`, never `CLEAN`: an unanswered
question must not read as a pass.

Usage:
    python scripts/open_pr_inventory.py                 # table
    python scripts/open_pr_inventory.py --json          # machine output
    python scripts/open_pr_inventory.py --no-detail     # skip N detail calls
    python scripts/open_pr_inventory.py --conflicts --ref LABEL=REV ...
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"

# GitHub returns these keys on the *detail* endpoint only. The list endpoint
# omits them entirely, which is the whole reason this module exists.
DETAIL_ONLY_KEYS = ("mergeable", "mergeable_state")


def _token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "github_token"):
        value = os.environ.get(name)
        if value:
            return value
    return None


def _get(url: str, token: str) -> tuple[int, object]:
    """Return (status, json-or-body). Never echoes the token."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "arkadia-open-pr-inventory",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, None


def list_open_prs(token: str, repo: str, api: str = API, per_page: int = 100) -> list[dict]:
    """All open PRs via the list endpoint, following pagination."""
    out: list[dict] = []
    page = 1
    while True:
        url = f"{api}/repos/{repo}/pulls?state=open&per_page={per_page}&page={page}"
        status, body = _get(url, token)
        if status != 200 or not isinstance(body, list):
            raise RuntimeError(f"list_open_prs: HTTP {status}")
        out.extend(body)
        if len(body) < per_page:
            break
        page += 1
    return out


def fetch_detail(token: str, repo: str, number: int, api: str = API) -> dict:
    """Detail record for one PR. Carries `mergeable`/`mergeable_state`."""
    status, body = _get(f"{api}/repos/{repo}/pulls/{number}", token)
    if status != 200 or not isinstance(body, dict):
        raise RuntimeError(f"fetch_detail #{number}: HTTP {status}")
    return body


def _mergeable(pr: dict) -> str:
    """`mergeable`/`mergeable_state` are detail-only, and may be null while GitHub
    computes them. Normalise to a printable string; never KeyError."""
    if "mergeable" not in pr:
        return "LIST_ENDPOINT"  # detail was not fetched
    value = pr.get("mergeable")
    if value is None:
        return "UNKNOWN"
    state = pr.get("mergeable_state") or ""
    return f"{'clean' if value else 'conflict'}:{state}" if state else ("clean" if value else "conflict")


def summarize(pr: dict) -> dict:
    """Flatten one PR record to the fields an inventory needs, tolerating the
    list/detail difference for the mergeable fields."""
    return {
        "number": pr.get("number"),
        "title": pr.get("title", ""),
        "head_ref": (pr.get("head") or {}).get("ref", ""),
        "head_sha": (pr.get("head") or {}).get("sha", ""),
        "base_ref": (pr.get("base") or {}).get("ref", ""),
        "base_sha": (pr.get("base") or {}).get("sha", ""),
        "draft": bool(pr.get("draft", False)),
        "mergeable": _mergeable(pr),
    }


def inventory(token: str, repo: str, api: str = API, detail: bool = True) -> list[dict]:
    """Summarise every open PR, oldest first. With `detail=True`, merges in the
    detail-only mergeable fields (one extra request per PR)."""
    rows = []
    for pr in sorted(list_open_prs(token, repo, api), key=lambda p: p["number"]):
        row = summarize(pr)
        if detail:
            try:
                row.update(summarize(fetch_detail(token, repo, row["number"], api)))
            except RuntimeError:
                pass  # keep the list-derived row; mergeable stays LIST_ENDPOINT
        rows.append(row)
    return rows


def render_table(rows: list[dict]) -> str:
    lines = [f"{len(rows)} open PR(s)", ""]
    for r in rows:
        draft = " [draft]" if r["draft"] else ""
        lines.append(
            f"#{r['number']:>4}  {r['head_ref'][:46]:46}  "
            f"base={r['base_ref']:>6}  {r['mergeable']:>16}{draft}"
        )
    return "\n".join(lines)


def merge_conflict_paths(a: str, b: str, repo: str | None = None) -> list[str] | None:
    """Paths that conflict if `a` and `b` are merged; `[]` if they compose.

    `None` means the question could not be answered (unresolvable revision, git
    missing, merge machinery unavailable). That distinction is load-bearing: a
    failed merge-tree run must never be reported as a clean composition.

    `--write-tree` merges in the object database, so no worktree or index is
    touched. On conflict, stdout is the tree oid, then one conflicted path per
    line, then a blank line and human-readable messages.
    """
    try:
        proc = subprocess.run(
            ["git", "merge-tree", "--write-tree", "--name-only", a, b],
            cwd=repo,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode == 0:
        return []
    if proc.returncode != 1:
        return None  # git error, not a conflict
    paths: list[str] = []
    for line in proc.stdout.splitlines()[1:]:  # [0] is the tree oid
        if not line.strip():
            break
        paths.append(line.strip())
    return paths or None  # exit 1 with no parseable path is unprovable


def conflict_verdict(paths: list[str] | None) -> str:
    if paths is None:
        return "UNPROVABLE"
    return "CONFLICT" if paths else "CLEAN"


def conflict_matrix(refs: dict[str, str], repo: str | None = None) -> list[dict]:
    """Every unordered pair of `refs` (label -> revision), judged for composition."""
    rows = []
    for a, b in itertools.combinations(sorted(refs), 2):
        paths = merge_conflict_paths(refs[a], refs[b], repo)
        rows.append(
            {"a": a, "b": b, "verdict": conflict_verdict(paths), "paths": paths or []}
        )
    return rows


def render_conflicts(rows: list[dict]) -> str:
    lines = [f"{len(rows)} pair(s) judged", ""]
    for r in rows:
        lines.append(f"{r['a']:>10} x {r['b']:<10}  {r['verdict']:<10}  {', '.join(r['paths'])}")
    return "\n".join(lines)


def _parse_refs(values: list[str]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for value in values:
        label, sep, rev = value.partition("=")
        if not sep or not label.strip() or not rev.strip():
            raise SystemExit(f"--ref expects LABEL=REV, got {value!r}")
        refs[label.strip()] = rev.strip()
    return refs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open-PR inventory (read-only).")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--api", default=API)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--no-detail", action="store_true", help="skip per-PR detail calls")
    parser.add_argument(
        "--conflicts",
        action="store_true",
        help="judge pairwise composition of --ref revisions instead of querying GitHub",
    )
    parser.add_argument(
        "--ref",
        action="append",
        default=[],
        metavar="LABEL=REV",
        help="a revision to compose (repeatable; requires --conflicts)",
    )
    parser.add_argument("--git-repo", default=None, help="git working tree to read refs from")
    args = parser.parse_args(argv)

    if args.conflicts:
        if len(args.ref) < 2:
            print("ERROR: --conflicts needs at least two --ref LABEL=REV", file=sys.stderr)
            return 2
        rows = conflict_matrix(_parse_refs(args.ref), repo=args.git_repo)
        if args.json:
            print(json.dumps({"pairs": rows}, indent=2))
        else:
            print(render_conflicts(rows))
        return 0

    token = _token()
    if not token:
        print("ERROR: no GitHub token in GH_TOKEN / GITHUB_TOKEN / github_token", file=sys.stderr)
        return 2

    try:
        rows = inventory(token, args.repo, args.api, detail=not args.no_detail)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"repo": args.repo, "count": len(rows), "pulls": rows}, indent=2))
    else:
        print(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
