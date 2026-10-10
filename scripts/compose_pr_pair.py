#!/usr/bin/env python3
"""Compose two branches/PR heads into one tree and report the integration facts.

A `git apply --3way` (or a textual diff inspection) proves two change sets do not
*textually* collide. It does not prove the composed tree is what a merge would
actually produce, and it says nothing about which changed paths the two branches
share. Gate-cluster merge decisions in this repository rest on both, and the
existing records were produced by hand each time.

This harness makes the measurement reproducible. It performs a *real* `git merge`
of two refs in an isolated, temporary worktree (never the caller's checkout), in
both orders, and reports:

  * the changed-path overlap (paths touched by both refs since their merge base),
  * whether each merge is clean, and the conflicting paths when it is not,
  * the composed tree object id (a byte identity, not a patch identity),
  * whether the two orders agree (order-independent composition).

Stdlib-only, read-only with respect to the repository (it adds and removes a
temporary linked worktree under a scratch directory). It never pushes, never
touches `main`, and never prints credentials. Exit code is non-zero when the
merge is not clean, so it can gate a decision.

Usage:
    python scripts/compose_pr_pair.py <refA> <refB> [--repo PATH] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def merge_base(repo: Path, a: str, b: str) -> str:
    return _git(repo, "merge-base", a, b).stdout.strip()


def changed_paths(repo: Path, base: str, ref: str) -> set:
    out = _git(repo, "diff", "--name-only", base, ref).stdout
    return {line for line in out.splitlines() if line.strip()}


def overlapping_paths(repo: Path, a: str, b: str) -> list:
    base = merge_base(repo, a, b)
    return sorted(changed_paths(repo, base, a) & changed_paths(repo, base, b))


def merge_once(repo: Path, first: str, second: str, scratch: Path, tag: str) -> dict:
    """Real-merge `second` onto a detached worktree of `first`."""
    worktree = scratch / f"wt-{tag}"
    add = _git(repo, "worktree", "add", "--detach", str(worktree), first)
    if add.returncode != 0:
        return {"clean": False, "conflicts": [], "tree": None, "error": add.stderr.strip()}
    try:
        merge = subprocess.run(
            ["git", "-c", "user.email=compose@local", "-c", "user.name=compose",
             "merge", "--no-edit", second],
            cwd=str(worktree), capture_output=True, text=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        clean = merge.returncode == 0
        conflicts = []
        if not clean:
            status = _git(worktree, "diff", "--name-only", "--diff-filter=U").stdout
            conflicts = sorted(l for l in status.splitlines() if l.strip())
        tree = _git(worktree, "rev-parse", "HEAD^{tree}").stdout.strip() or None
        return {"clean": clean, "conflicts": conflicts, "tree": tree}
    finally:
        _git(repo, "worktree", "remove", "--force", str(worktree))


def compose(repo: Path, a: str, b: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="compose-pr-pair-") as tmp:
        scratch = Path(tmp)
        forward = merge_once(repo, a, b, scratch, "ab")
        reverse = merge_once(repo, b, a, scratch, "ba")
    order_independent = (
        forward["tree"] is not None
        and forward["tree"] == reverse["tree"]
    )
    return {
        "refA": a,
        "refB": b,
        "merge_base": merge_base(repo, a, b),
        "overlapping_paths": overlapping_paths(repo, a, b),
        "forward": forward,
        "reverse": reverse,
        "order_independent": order_independent,
        "composed_tree": forward["tree"],
        "clean": forward["clean"] and reverse["clean"],
    }


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("refA")
    parser.add_argument("refB")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    result = compose(repo, args.refA, args.refB)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"refs        : {result['refA']} x {result['refB']}")
        print(f"merge base  : {result['merge_base']}")
        print(f"overlap     : {len(result['overlapping_paths'])} path(s)")
        for p in result["overlapping_paths"]:
            print(f"              {p}")
        print(f"forward     : clean={result['forward']['clean']} tree={result['forward']['tree']}")
        print(f"reverse     : clean={result['reverse']['clean']} tree={result['reverse']['tree']}")
        print(f"order-indep : {result['order_independent']}")
        print(f"composed    : {'CLEAN' if result['clean'] else 'CONFLICT'}")
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    sys.exit(_main())
