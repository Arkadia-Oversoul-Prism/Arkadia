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

Usage:
    python scripts/open_pr_inventory.py                 # table
    python scripts/open_pr_inventory.py --json          # machine output
    python scripts/open_pr_inventory.py --no-detail     # skip N detail calls
"""

from __future__ import annotations

import argparse
import json
import os
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open-PR inventory (read-only).")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--api", default=API)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--no-detail", action="store_true", help="skip per-PR detail calls")
    args = parser.parse_args(argv)

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
