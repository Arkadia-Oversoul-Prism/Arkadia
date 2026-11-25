#!/usr/bin/env python3
"""Read-only, queue-wide PR reconciliation packet.

This tool inventories all open PRs with pagination, gathers bounded evidence,
and reports dependency/path-overlap clusters. It never changes PR state, merges,
or grants readiness. Missing/stale/failed evidence is an exception, not a pass.

Usage:
  GH_TOKEN=... python scripts/pr_batch_reconcile.py --json
  GH_TOKEN=... python scripts/pr_batch_reconcile.py --repo owner/name
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"
UA = "arkadia-pr-batch-reconcile"
DEPENDENCY = re.compile(
    r"(?i)\b(?:depends on|dependency|blocked by|requires|after)\s+(?:PR\s*)?#(\d+)\b"
)


class EvidenceError(RuntimeError):
    """A required GitHub read failed or returned an unexpected shape."""


def _token() -> str | None:
    return next((os.environ.get(k) for k in ("GH_TOKEN", "GITHUB_TOKEN", "github_token")
                 if os.environ.get(k)), None)


def _get(token: str, url: str) -> tuple[int, object]:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"GET failed ({type(exc).__name__})") from exc


def _url(api: str, path: str, **params: object) -> str:
    query = urllib.parse.urlencode(params)
    return f"{api.rstrip('/')}{path}" + (f"?{query}" if query else "")


def get_object(token: str, api: str, path: str) -> dict:
    status, body = _get(token, f"{api.rstrip('/')}{path}")
    if status != 200 or not isinstance(body, dict):
        raise EvidenceError(f"{path}: HTTP {status} or invalid object")
    return body


def get_pages(token: str, api: str, path: str, *, per_page: int = 100) -> list[dict]:
    """Read every page; any missing page invalidates completeness."""
    items: list[dict] = []
    page = 1
    while True:
        status, body = _get(token, _url(api, path, per_page=per_page, page=page))
        if status != 200 or not isinstance(body, list):
            raise EvidenceError(f"{path} page {page}: HTTP {status} or invalid list")
        items.extend(x for x in body if isinstance(x, dict))
        if len(body) < per_page:
            return items
        page += 1


def inventory(token: str, repo: str, api: str = API) -> list[dict]:
    pulls = get_pages(token, api, f"/repos/{repo}/pulls", per_page=100)
    return sorted(pulls, key=lambda p: int(p.get("number", 0)))


def _files(token: str, api: str, repo: str, number: int) -> list[str]:
    rows = get_pages(token, api, f"/repos/{repo}/pulls/{number}/files")
    return sorted({str(x["filename"]) for x in rows if x.get("filename")})


def _reviews(token: str, api: str, repo: str, number: int) -> dict:
    rows = get_pages(token, api, f"/repos/{repo}/pulls/{number}/reviews")
    latest: dict[str, dict] = {}
    for review in sorted(rows, key=lambda x: x.get("submitted_at") or ""):
        user = (review.get("user") or {}).get("login")
        if user and review.get("state") not in ("PENDING",):
            latest[user] = review
    states = [r.get("state") for r in latest.values()]
    return {"effective_approvals": states.count("APPROVED"),
            "changes_requested": states.count("CHANGES_REQUESTED"),
            "reviewers": sorted(latest)}


def _checks(token: str, api: str, repo: str, sha: str) -> dict:
    path = f"/repos/{repo}/commits/{sha}/check-runs"
    rows = get_pages(token, api, path)
    statuses = [str((r.get("conclusion") or r.get("status") or "UNKNOWN")).upper()
                for r in rows]
    bad = [s for s in statuses if s not in ("SUCCESS",)]
    return {"count": len(rows), "conclusions": statuses,
            "all_success": bool(rows) and not bad,
            "unknown_or_non_success": bad}


def _dependencies(pr: dict, known: set[int]) -> list[int]:
    text = "\n".join(str(pr.get(k) or "") for k in ("title", "body"))
    number = int(pr.get("number", 0))
    return sorted({int(m.group(1)) for m in DEPENDENCY.finditer(text)
                   if int(m.group(1)) in known and int(m.group(1)) != number})


def build_packet(token: str, repo: str, api: str = API) -> dict:
    prs = inventory(token, repo, api)
    numbers = {int(p["number"]) for p in prs}
    rows, errors = [], []
    for listed in prs:
        n = int(listed["number"])
        base = listed.get("base") or {}
        head = listed.get("head") or {}
        row = {
            "number": n, "title": listed.get("title", ""),
            "url": listed.get("html_url", ""),
            "draft": bool(listed.get("draft")),
            "state": listed.get("state", "UNKNOWN"),
            "base": base.get("ref", "UNKNOWN"),
            "base_sha": base.get("sha"),
            "head_branch": head.get("ref", "UNKNOWN"),
            "head_sha": head.get("sha"),
            "author": (listed.get("user") or {}).get("login", "UNKNOWN"),
            "labels": sorted(x.get("name", "") for x in listed.get("labels", [])),
            "dependencies": _dependencies(listed, numbers),
            "changed_files": [], "mergeable": "UNKNOWN",
            "checks": {"all_success": False, "reason": "NOT_FETCHED"},
            "reviews": {"effective_approvals": 0, "changes_requested": 0},
            "evidence_errors": [],
            "classification": "HUMAN_REVIEW_REQUIRED",
        }
        try:
            detail = get_object(token, api, f"/repos/{repo}/pulls/{n}")
            row["mergeable"] = ("UNKNOWN" if detail.get("mergeable") is None else
                               "CLEAN" if detail.get("mergeable") else "CONFLICT")
            row["mergeable_state"] = detail.get("mergeable_state", "UNKNOWN")
        except EvidenceError as exc:
            row["evidence_errors"].append(f"detail: {exc}")
        try:
            row["changed_files"] = _files(token, api, repo, n)
        except EvidenceError as exc:
            row["evidence_errors"].append(f"files: {exc}")
        try:
            row["reviews"] = _reviews(token, api, repo, n)
        except EvidenceError as exc:
            row["evidence_errors"].append(f"reviews: {exc}")
        sha = row.get("head_sha")
        if sha:
            try:
                row["checks"] = _checks(token, api, repo, sha)
            except EvidenceError as exc:
                row["evidence_errors"].append(f"checks: {exc}")
        else:
            row["evidence_errors"].append("checks: missing exact head SHA")
        # Deliberately advisory: this script does not certify M1-M13, branch
        # protection, CODEOWNERS, reserved decisions, or semantic review.
        if row["draft"]:
            row["classification"] = "DRAFT_OWNER_ACTION"
        elif row["evidence_errors"]:
            row["classification"] = "EVIDENCE_INCOMPLETE"
        elif row["dependencies"]:
            row["classification"] = "DEPENDENCY_ORDER_REVIEW"
        elif row["mergeable"] == "CONFLICT" or row.get("mergeable_state") not in ("clean", "UNKNOWN"):
            row["classification"] = "CONFLICT_REVIEW"
        elif not row["checks"]["all_success"]:
            row["classification"] = "CHECKS_NOT_GREEN_OR_UNKNOWN"
        elif row["reviews"]["changes_requested"]:
            row["classification"] = "CHANGES_REQUESTED"
        else:
            row["classification"] = "FULL_HUMAN_REVIEW_REQUIRED"
        if row["evidence_errors"]:
            errors.append({"pr": n, "errors": row["evidence_errors"]})
        rows.append(row)

    # Composition is a conservative changed-path overlap map, not a claim of
    # semantic conflict. It makes shared-file clusters visible for reviewer triage.
    owners: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        for path in row["changed_files"]:
            owners[path].append(row["number"])
    overlaps = [{"path": path, "prs": sorted(nums)}
                for path, nums in sorted(owners.items()) if len(nums) > 1]
    adjacency: dict[int, set[int]] = defaultdict(set)
    for item in overlaps:
        for n in item["prs"]:
            adjacency[n].update(x for x in item["prs"] if x != n)
    clusters = []
    seen: set[int] = set()
    for n in sorted(adjacency):
        if n in seen:
            continue
        stack, group = [n], set()
        while stack:
            current = stack.pop()
            if current in group:
                continue
            group.add(current)
            stack.extend(adjacency[current] - group)
        seen.update(group)
        clusters.append(sorted(group))
    return {
        "schema": "arkadia.pr-batch-reconciliation.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repo,
        "complete_inventory": True,
        "open_pr_count": len(rows),
        "evidence_error_count": len(errors),
        "classification_counts": {k: sum(r["classification"] == k for r in rows)
                                  for k in sorted({r["classification"] for r in rows})},
        "composition": {"overlapping_paths": overlaps, "clusters": clusters},
        "exceptions": errors,
        "pull_requests": rows,
        "authority": {
            "read_only": True,
            "merge_or_mutation_performed": False,
            "ready_for_merge_authorized": False,
            "note": "Packet is triage evidence only. M1-M13, branch protection, reserved-human decisions, and semantic composition require independent review. Never treat a classification as merge authorization."
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--api", default=API)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    token = _token()
    if not token:
        print("ERROR: GH_TOKEN/GITHUB_TOKEN is required; no token is printed.", file=sys.stderr)
        return 2
    try:
        packet = build_packet(token, args.repo, args.api)
    except EvidenceError as exc:
        print(f"ERROR: inventory incomplete; no packet emitted: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(packet, indent=2))
    else:
        print(f"{packet['open_pr_count']} open PRs | {packet['evidence_error_count']} evidence errors")
        for status, count in packet["classification_counts"].items():
            print(f"{status:34} {count:>3}")
        print(f"Composition clusters: {packet['composition']['clusters']}")
        print("READ-ONLY: no PR state or repository mutation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
