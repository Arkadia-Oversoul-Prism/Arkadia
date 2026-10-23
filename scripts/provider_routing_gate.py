#!/usr/bin/env python3
"""Provider-routing regression attribution gate.

Replaces "the full suite must be green" with a question that can actually be
answered: *did this candidate introduce any new failing/error node?*

`provider-routing.yml` runs the whole suite, and the repository carries known
pre-existing failures (the CE-01 `weaver.autonomy` collection error, the Lab
authority-surface pins, and others). A gate that requires green therefore returns
the same red for a regression this candidate introduced and for debt it merely
observed, which makes it unusable for the question it is used to answer.

Verdicts (exit codes are part of the contract):

  PASS (0)          candidate introduces no new failing/error node vs a valid baseline
  FAIL (1)          candidate introduces >=1 new failing/error node
  INCONCLUSIVE (2)  baseline or candidate evidence is missing, stale, truncated,
                    unparseable, or incomparable -> BLOCKING, never a pass

Design commitments:

  * Comparison is set-based. Passed/skipped counts move with how many tests exist
    and with the environment; the failing/error node *set* does not.
  * Resolved and unchanged baseline failures are reported in their own buckets and
    can never be counted as regressions.
  * The baseline is bound to an exact source SHA and an exact environment
    (interpreter, command, dependency source). A baseline recorded against a
    different SHA is stale; a different environment is incomparable. Neither is
    silently accepted, and the latest `main` is never substituted for a differing
    comparison base.
  * A run that executed nothing -- empty output, a collection abort, an
    interruption, a truncated log -- must never be read as "no failures". Every
    such shape is INCONCLUSIVE.

Parsing is delegated to `scripts/baseline_fingerprint.py` rather than duplicated:
a second parser drifts from the first and the drift is invisible.

Read-only. Runs no tests itself; it compares two pytest logs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_fingerprint import extract, fingerprint  # noqa: E402

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"
EXIT = {PASS: 0, FAIL: 1, INCONCLUSIVE: 2}
SCHEMA = "arkadia.provider-routing-gate/1"

# pytest's terminal summary line, and the shapes that mean "this run did not execute".
_SUMMARY_RE = re.compile(r"\bin \d+(?:\.\d+)?s\b(?:\s*\(\d+:\d+:\d+\))?\s*$")
_EXECUTED_RE = re.compile(r"(\d+) (passed|failed|error|errors|skipped)")
_INTERRUPT_RE = re.compile(r"(Interrupted:|errors during collection|no tests ran)", re.I)


def _read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def executed_count(text: str) -> int | None:
    """Tests pytest reported executing, or None when there is no summary line.

    The distinction matters: `None` means "no usable report", `0` means "a report
    that says nothing ran". Both are unusable as evidence, for different reasons.
    """
    for line in reversed(text.splitlines()):
        if _SUMMARY_RE.search(line.rstrip()):
            total, found = 0, False
            for m in _EXECUTED_RE.finditer(line):
                total += int(m.group(1))
                found = True
            return total if found else None
    return None


def evidence_problems(path: str, label: str) -> list[str]:
    """Reasons this log is NOT usable evidence. Empty list means usable.

    Every condition here is a way a run could look clean while having executed
    nothing, or a truncated subset. This is the false-pass guard.
    """
    if not os.path.exists(path):
        return [f"{label}: log does not exist ({path})"]
    text = _read(path)
    if not text.strip():
        return [f"{label}: log is empty"]

    reasons: list[str] = []
    n = executed_count(text)
    if n is None:
        reasons.append(f"{label}: no pytest summary line (truncated or non-pytest output)")
    elif n == 0:
        reasons.append(f"{label}: summary reports 0 tests executed")

    if _INTERRUPT_RE.search(text):
        reasons.append(f"{label}: run was interrupted or aborted during collection")

    # A summary claiming more failures/errors than the log carries FAILED/ERROR
    # lines means the outcome list is a subset (the `-rf` shape).
    try:
        extract(path)
    except ValueError as exc:
        reasons.append(f"{label}: {exc}")
    return reasons


def merge_base(repo: str, base_ref: str, candidate_ref: str) -> str | None:
    """The candidate's actual comparison base. Never defaults to the latest base ref."""
    try:
        out = subprocess.run(
            ["git", "-C", repo, "merge-base", base_ref, candidate_ref],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def environment_problems(baseline_env: dict, candidate_env: dict) -> list[str]:
    """Both sides must be comparable. Returns the reasons they are not."""
    problems = []
    for key in ("python", "command", "dependency_source"):
        b, c = baseline_env.get(key), candidate_env.get(key)
        if b != c:
            problems.append(
                f"environment mismatch on `{key}`: baseline={b!r} candidate={c!r}")
    return problems


def compare(*, baseline: dict | None, candidate_log: str, candidate_env: dict,
            candidate_base_sha: str | None) -> dict:
    """Compare a candidate log against the recorded baseline."""
    if baseline is None:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE,
                "reasons": ["baseline record absent or unreadable"]}

    reasons: list[str] = []

    b_sha = baseline.get("source_sha")
    if not b_sha:
        reasons.append("baseline lacks source_sha; identity is incomplete")
    elif candidate_base_sha and b_sha != candidate_base_sha:
        reasons.append(
            f"baseline is STALE: recorded against {b_sha[:12]}, candidate merge base "
            f"is {candidate_base_sha[:12]}")

    reasons += environment_problems(baseline.get("environment", {}), candidate_env)
    if reasons:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE, "reasons": reasons}

    reasons += evidence_problems(baseline.get("log", ""), "baseline")
    reasons += evidence_problems(candidate_log, "candidate")
    if reasons:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE, "reasons": reasons}

    try:
        b_outcomes, b_ids = extract(baseline["log"])
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE,
                "reasons": [f"baseline unparseable: {exc}"]}
    try:
        c_outcomes, c_ids = extract(candidate_log)
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE,
                "reasons": [f"candidate unparseable: {exc}"]}

    recorded = baseline.get("ids_fingerprint")
    if recorded and fingerprint(b_ids) != recorded:
        return {"schema": SCHEMA, "verdict": INCONCLUSIVE,
                "reasons": ["baseline log no longer matches its recorded fingerprint"]}

    b_set, c_set = set(b_ids), set(c_ids)
    newly_failing = sorted(c_set - b_set)
    resolved = sorted(b_set - c_set)
    unchanged = sorted(b_set & c_set)

    b_map = {o.split(" ", 1)[1]: o.split(" ", 1)[0] for o in b_outcomes}
    c_map = {o.split(" ", 1)[1]: o.split(" ", 1)[0] for o in c_outcomes}
    class_shift = sorted(n for n in unchanged if b_map.get(n) != c_map.get(n))

    verdict = FAIL if newly_failing else PASS
    return {
        "schema": SCHEMA,
        "verdict": verdict,
        "reasons": ([f"{len(newly_failing)} newly failing node(s)"] if newly_failing else []),
        "newly_failing": newly_failing,
        "unchanged": unchanged,
        "resolved": resolved,
        "class_shift": class_shift,
        "baseline_nodes": len(b_ids),
        "candidate_nodes": len(c_ids),
        "baseline_ids_fingerprint": fingerprint(b_ids),
        "candidate_ids_fingerprint": fingerprint(c_ids),
        "baseline_outcomes_fingerprint": fingerprint(b_outcomes),
        "candidate_outcomes_fingerprint": fingerprint(c_outcomes),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, help="baseline record (JSON)")
    ap.add_argument("--candidate", required=True, help="candidate pytest log")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--baseline-ref", default="origin/main")
    ap.add_argument("--candidate-ref", default=None,
                    help="candidate ref; merge base is derived against --baseline-ref")
    ap.add_argument("--candidate-base-sha", default=None,
                    help="override; otherwise derived from the merge base")
    ap.add_argument("--python", default=None)
    ap.add_argument("--command", required=True)
    ap.add_argument("--dependency-source", default="requirements.txt")
    ap.add_argument("--report", default=None, help="write the result JSON here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    base_sha = args.candidate_base_sha
    if base_sha is None and args.candidate_ref:
        base_sha = merge_base(args.repo, args.baseline_ref, args.candidate_ref)
        if base_sha is None:
            result = {"schema": SCHEMA, "verdict": INCONCLUSIVE,
                      "reasons": [f"could not derive a merge base for "
                                  f"{args.baseline_ref}..{args.candidate_ref}"]}
            _emit(result, args)
            return EXIT[INCONCLUSIVE]

    candidate_env = {"python": args.python, "command": args.command,
                     "dependency_source": args.dependency_source}
    try:
        with open(args.baseline, encoding="utf-8") as fh:
            baseline = json.load(fh)
    except (OSError, ValueError):
        baseline = None

    result = compare(baseline=baseline, candidate_log=args.candidate,
                     candidate_env=candidate_env, candidate_base_sha=base_sha)
    result["candidate_base_sha"] = base_sha
    result["candidate_environment"] = candidate_env
    _emit(result, args)
    return EXIT[result["verdict"]]


def _emit(result: dict, args) -> None:
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"PROVIDER-ROUTING GATE — VERDICT: {result['verdict']}")
    for key in ("reasons", "newly_failing", "resolved", "class_shift"):
        if result.get(key):
            print(f"  {key}: {result[key]}")
    if result.get("unchanged") is not None:
        print(f"  unchanged baseline failures: {len(result['unchanged'])}")


if __name__ == "__main__":
    sys.exit(main())
