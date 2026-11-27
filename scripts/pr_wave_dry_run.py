#!/usr/bin/env python3
"""Read-only merge-wave dry-run for the open pull-request queue.

Milestone 2 of #732. Candidate PR heads are composed onto a base revision inside a
throwaway git worktree, in queue order, and each composition is decided by a real
``git merge``. A shared file is *not* a conflict; only git decides that. This is the
property a changed-path overlap map cannot establish.

A conflict is reported as one of two states, because they need opposite responses:

* ``CONFLICT_BASE`` -- the head conflicts with the *base revision alone*, before any
  pull request is composed. The remedy is to rebase that one branch; the queue
  composed fine. It is not evidence that the queue is incompatible.
* ``CONFLICT`` -- the head composes with the base and conflicts with an earlier merge
  in the wave. That is an adjudication between two pull requests.

The distinction cannot be inferred from the conflict edges: a base conflict has no
earlier merge touching its path, so it looks exactly like a wave conflict with no
overlapping merge. It is therefore measured, not inferred, by re-probing the head
against the base in a second throwaway worktree.

Read-only with respect to the repository and to GitHub: it never pushes, never
merges a pull request, never mutates the caller's working tree, and never grants
readiness.

Usage:
  GH_TOKEN=... python scripts/pr_wave_dry_run.py --base origin/main
  python scripts/pr_wave_dry_run.py --base origin/main --prs 675,679,681 --json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"
GIT_IDENTITY = ("-c", "user.name=arkadia-wave-dry-run",
                "-c", "user.email=wave-dry-run@invalid")


class DryRunError(RuntimeError):
    """The dry-run cannot reach a sound verdict; it must not report a clean wave."""


CONFLICT_BASE = "CONFLICT_BASE"


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(("git", "-C", repo, *args), capture_output=True, text=True)


def _must(repo: str, *args: str) -> str:
    done = _git(repo, *args)
    if done.returncode != 0:
        raise DryRunError(f"git {' '.join(args)} failed: {done.stderr.strip()[:400]}")
    return done.stdout.strip()


def resolve_revision(repo: str, rev: str) -> str:
    done = _git(repo, "rev-parse", "--verify", f"{rev}^{{commit}}")
    if done.returncode != 0:
        raise DryRunError(f"cannot resolve base revision {rev!r}")
    return done.stdout.strip()


def changed_paths(repo: str, base_sha: str, head_sha: str) -> list[str]:
    """Paths a PR actually changes, measured against its own merge base.

    An empty list is a measurement here, never a default. A head with no merge base
    against the composed revision cannot have its conflict attributed to an earlier
    merge, and silently returning ``[]`` would report that as "no overlapping merge".
    """
    merge_base = _git(repo, "merge-base", base_sha, head_sha)
    if merge_base.returncode != 0:
        raise DryRunError(
            f"no merge base between {base_sha[:8]} and {head_sha[:8]}; the conflict "
            "edges cannot be measured")
    out = _git(repo, "diff", "--name-only", merge_base.stdout.strip(), head_sha)
    if out.returncode != 0:
        raise DryRunError(f"cannot diff {head_sha[:8]}: {out.stderr.strip()[:400]}")
    return sorted({line for line in out.stdout.splitlines() if line})


def unmerged_paths(worktree: str) -> list[str]:
    out = _git(worktree, "diff", "--name-only", "--diff-filter=U")
    return sorted({line for line in out.stdout.splitlines() if line}) if out.returncode == 0 else []


def _merge(worktree: str, sha: str) -> tuple[bool, list[str]]:
    """True when the merge landed. False only for a genuine textual conflict."""
    done = subprocess.run(
        ("git", "-C", worktree, *GIT_IDENTITY, "merge", "--no-ff", "--no-edit", sha),
        capture_output=True, text=True)
    if done.returncode == 0:
        return True, []
    conflicted = unmerged_paths(worktree)
    if conflicted:
        _git(worktree, "merge", "--abort")
        return False, conflicted
    raise DryRunError(
        f"merge of {sha[:8]} failed without a conflict: {done.stderr.strip()[:400]}")


def conflicts_at_base(repo: str, base_sha: str,
                      heads: list[tuple[int, str]]) -> dict[int, list[str]]:
    """Which of `heads` conflict with `base_sha` alone, and on which paths.

    Measured rather than inferred. `edges` cannot answer this: a head that conflicts
    with the base has no earlier merge touching its path, so its edge list is empty
    exactly as a wave conflict's would be. A merge conflict requires both sides to
    change the same path, so the two conditions need opposite responses -- rebase one
    branch, versus adjudicate between two -- and sharing one label hides which.
    """
    if not heads:
        return {}
    worktree = tempfile.mkdtemp(prefix="arkadia-wave-base-")
    shutil.rmtree(worktree)
    added = False
    conflicted_by_head: dict[int, list[str]] = {}
    try:
        done = subprocess.run(
            ("git", "-C", repo, "worktree", "add", "--detach", worktree, base_sha),
            capture_output=True, text=True)
        if done.returncode != 0:
            raise DryRunError(f"cannot create base probe worktree: {done.stderr.strip()[:400]}")
        added = True
        for number, sha in heads:
            merged, conflicted = _merge(worktree, sha)
            if merged:
                _must(worktree, "reset", "--hard", base_sha)
            else:
                conflicted_by_head[number] = conflicted
    finally:
        if added:
            subprocess.run(("git", "-C", repo, "worktree", "remove", "--force", worktree),
                           capture_output=True, text=True)
        shutil.rmtree(worktree, ignore_errors=True)
        _git(repo, "worktree", "prune")
    return conflicted_by_head


def dry_run(repo: str, base: str, pulls: list[dict]) -> dict:
    """Compose `pulls` in the given order onto `base`; report per-PR composition.

    `pulls` is an ordered list of {"number": int, "head_sha": str}. Every pull
    request is accounted for exactly once as CLEAN, ALREADY_CONTAINED, CONFLICT (with
    an earlier merge in the wave) or CONFLICT_BASE (with the base revision alone).
    """
    base_sha = resolve_revision(repo, base)
    worktree = tempfile.mkdtemp(prefix="arkadia-wave-")
    shutil.rmtree(worktree)
    added = False
    results: list[dict] = []
    touched: list[tuple[int, set[str]]] = []
    heads: dict[int, str] = {}
    try:
        done = subprocess.run(
            ("git", "-C", repo, "worktree", "add", "--detach", worktree, base_sha),
            capture_output=True, text=True)
        if done.returncode != 0:
            raise DryRunError(f"cannot create scratch worktree: {done.stderr.strip()[:400]}")
        added = True
        for pull in pulls:
            number = int(pull["number"])
            sha = str(pull.get("head_sha") or "")
            if not sha:
                raise DryRunError(f"PR #{number}: missing head SHA")
            heads[number] = sha
            if _git(worktree, "merge-base", "--is-ancestor", sha, "HEAD").returncode == 0:
                results.append({"number": number, "state": "ALREADY_CONTAINED",
                                "conflicted_paths": [], "edges": []})
                continue
            merged, conflicted = _merge(worktree, sha)
            if merged:
                touched.append((number, set(changed_paths(repo, base_sha, sha))))
                results.append({"number": number, "state": "CLEAN",
                                "conflicted_paths": [], "edges": []})
                continue
            edges = sorted(n for n, paths in touched if paths & set(conflicted))
            results.append({"number": number, "state": "CONFLICT",
                            "conflicted_paths": conflicted, "edges": edges})
    finally:
        if added:
            subprocess.run(("git", "-C", repo, "worktree", "remove", "--force", worktree),
                           capture_output=True, text=True)
        shutil.rmtree(worktree, ignore_errors=True)
        _git(repo, "worktree", "prune")

    wave_conflicts = [row for row in results if row["state"] == "CONFLICT"]
    if wave_conflicts:
        at_base = conflicts_at_base(
            repo, base_sha, [(int(row["number"]), heads[int(row["number"])])
                             for row in wave_conflicts])
        for row in wave_conflicts:
            number = int(row["number"])
            if number in at_base:
                row["state"] = CONFLICT_BASE
                row["conflicted_paths_at_base"] = at_base[number]
                row["edges"] = []

    states = [row["state"] for row in results]
    return {
        "schema": "arkadia.pr-wave-dry-run.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": {"requested": base, "resolved": base_sha},
        "order": [int(p["number"]) for p in pulls],
        "accounted": len(results),
        "clean": [r["number"] for r in results if r["state"] == "CLEAN"],
        "already_contained": [r["number"] for r in results if r["state"] == "ALREADY_CONTAINED"],
        "conflicts": [r for r in results if r["state"] == "CONFLICT"],
        "base_conflicts": [r for r in results if r["state"] == CONFLICT_BASE],
        "state_counts": {s: states.count(s) for s in sorted(set(states))},
        "authority": {
            "read_only": True,
            "pull_request_mutated": False,
            "merge_or_push_performed": False,
            "ready_for_merge_authorized": False,
            "note": ("A CLEAN composition is a textual fact about one ordering. It is not "
                     "merge authorization, not M1-M13 eligibility, and not a test-suite "
                     "result. A CONFLICT is a resolution task for a human. A "
                     "CONFLICT_BASE is not a queue-composition failure: that branch does "
                     "not merge into the base at all and needs a rebase."),
        },
    }


def open_pulls(token: str, repo: str, api: str = API) -> list[dict]:
    pulls: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"state": "open", "per_page": 100, "page": page})
        request = urllib.request.Request(
            f"{api.rstrip('/')}/repos/{repo}/pulls?{query}",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": "arkadia-pr-wave-dry-run"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, json.JSONDecodeError) as exc:
            raise DryRunError(f"inventory page {page} failed: {type(exc).__name__}") from exc
        if not isinstance(body, list):
            raise DryRunError(f"inventory page {page}: unexpected payload")
        pulls.extend({"number": int(p["number"]), "head_sha": (p.get("head") or {}).get("sha")}
                     for p in body if isinstance(p, dict) and p.get("number"))
        if len(body) < 100:
            return sorted(pulls, key=lambda p: p["number"])
        page += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".", help="git checkout to compose in")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub owner/name for --prs")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--prs", help="comma-separated PR numbers, in composition order")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.prs:
            token = next((os.environ.get(k) for k in ("GH_TOKEN", "GITHUB_TOKEN", "github_token")
                          if os.environ.get(k)), None)
            if not token:
                print("ERROR: GH_TOKEN/GITHUB_TOKEN is required to resolve --prs",
                      file=sys.stderr)
                return 2
            wanted = [int(x) for x in args.prs.replace(" ", "").split(",") if x]
            known = {p["number"]: p for p in open_pulls(token, args.repo)}
            missing = [n for n in wanted if n not in known]
            if missing:
                raise DryRunError(f"not open in {args.repo}: {missing}")
            pulls = [known[n] for n in wanted]
        else:
            token = next((os.environ.get(k) for k in ("GH_TOKEN", "GITHUB_TOKEN", "github_token")
                          if os.environ.get(k)), None)
            if not token:
                print("ERROR: GH_TOKEN/GITHUB_TOKEN is required for the open-PR inventory",
                      file=sys.stderr)
                return 2
            pulls = open_pulls(token, args.repo)
        packet = dry_run(args.repo_root, args.base, pulls)
    except DryRunError as exc:
        print(f"ERROR: no verdict emitted: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(packet, indent=2))
    else:
        print(f"base {packet['base']['resolved'][:8]} | {packet['accounted']} PRs composed "
              f"in queue order")
        print("  " + "  ".join(f"{k}={v}" for k, v in packet["state_counts"].items()))
        for row in packet["conflicts"]:
            print(f"  CONFLICT #{row['number']} on {', '.join(row['conflicted_paths'])}"
                  f" (after {row['edges'] or 'UNATTRIBUTED: no earlier merge touched these paths'})")
        for row in packet["base_conflicts"]:
            print(f"  CONFLICT_BASE #{row['number']} on "
                  f"{', '.join(row['conflicted_paths'])} -- does not merge into the base "
                  f"at all; rebase the branch, the queue is not the cause")
        print("READ-ONLY: no PR state, no push, no merge performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
