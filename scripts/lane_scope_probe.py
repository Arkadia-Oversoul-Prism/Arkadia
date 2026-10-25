#!/usr/bin/env python3
"""Read-only probe: can live PR activity change the lanes a guard enforces against?

The invariant under investigation is stated in
``docs/control-plane/evidence/lane-currency-guard-authority-boundary-01/DESIGN-INVESTIGATION.md``:

    The set of lanes subject to governance checks must not be widened or reduced
    by the live PR activity being evaluated.

    The effective blocking scope must remain non-empty under adversarial input.

This probe encodes both as executable checks, so a candidate repair can be judged by
running it rather than by arguing about it. It exits non-zero while the defect is
present, which is what makes it usable as an acceptance test: a candidate passes only
when every check passes.

The checks are parameterised by a *scope resolver* -- the function that decides which
lanes are judged -- so the same checks run against both the shipped implementation and
a conforming stub. That is the probe's own control: a detector that fails on every
implementation is not a detector, so ``--selftest`` proves these checks PASS on a design
that satisfies the invariant.

Nothing here mutates the repository, the snapshot, or GitHub. It imports the shipped
modules and synthesises PR inputs in memory; there is no network call and no write.

Usage::

    python scripts/lane_scope_probe.py            # judge the shipped implementation
    python scripts/lane_scope_probe.py --selftest # prove the checks can pass (control)
    python scripts/lane_scope_probe.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import lane_state  # noqa: E402
import lane_state_refresh as refresh  # noqa: E402

BASE_MAIN = "0" * 40
LANES = sorted(refresh.LANE_OWNERSHIP)
DOC = {n: f"{refresh.DOC_OWNING_PREFIX}{s['doc']}" for n, s in refresh.LANE_OWNERSHIP.items()}
OWNED = {n: list(s["paths"]) for n, s in refresh.LANE_OWNERSHIP.items()}


def _pr(number: int, ref: str) -> dict:
    return {
        "number": number,
        "head": {"ref": ref, "sha": "a" * 40},
        "draft": False,
        "updated_at": "2026-10-25T00:00:00Z",
        "title": f"PR {number}",
    }


def shipped_scope(state: dict) -> list[str]:
    """The lanes the shipped implementation actually judges."""
    return sorted(lane_state.current_lanes(state))


def conforming_scope(state: dict) -> list[str]:
    """A conforming resolver: the enforced set is fixed, non-empty, and independent
    of PR activity. Exists only to prove the checks below can pass.

    Note where the set comes from: ``LANE_OWNERSHIP`` (a constant), **not** the
    snapshot. Sourcing it from ``state["lanes"]`` is the shipped defect -- an empty or
    truncated snapshot would then empty the enforced set, which is exactly what check 3
    measures. The snapshot may only ever *add* lanes (so an unknown lane is still
    judged, check 4); it may never remove one.
    """
    return sorted(set(LANES) | set(state.get("lanes", {})))


def _state(open_prs, files):
    return refresh.build(open_prs, files, BASE_MAIN, "owner/repo")


def check_one_pr_cannot_exempt_its_own_lane(scope) -> dict:
    """A PR touching one lane's paths *and* that lane's doc must not remove it."""
    baseline = scope(_state([], {}))
    per_lane = {}
    for lane_no in LANES:
        changed = [OWNED[lane_no][0], DOC[lane_no]]
        after = scope(_state([_pr(900, "b/x")], {900: changed}))
        per_lane[lane_no] = {"judged_before": lane_no in baseline,
                             "judged_after": lane_no in after}
    removed = [n for n, d in per_lane.items()
               if d["judged_before"] and not d["judged_after"]]
    return {
        "name": "one PR cannot exempt its own lane from judgement",
        "detail": {"removed": removed},
        "passed": not removed,
    }


def check_one_pr_cannot_empty_the_scope(scope) -> dict:
    """A single PR touching every lane's paths and every doc must not empty the scope."""
    changed = [p for n in LANES for p in OWNED[n]] + list(DOC.values())
    after = scope(_state([_pr(901, "b/all")], {901: changed}))
    return {
        "name": "one PR cannot empty the blocking scope",
        "detail": {"judged_after": after, "of": len(LANES)},
        "passed": bool(after),
    }


def check_scope_is_nonempty_for_adversarial_input(scope) -> dict:
    """An empty or fully-deferred snapshot must fail closed, not pass vacuously."""
    empty = scope({"lanes": {}, "schema": "arkadia.lane-state/1.2"})
    all_deferred = scope({
        "lanes": {n: {"doc": DOC[n], "doc_guard": "deferred"} for n in LANES},
        "schema": "arkadia.lane-state/1.2",
    })
    return {
        "name": "an empty or fully-deferred snapshot cannot pass vacuously",
        "detail": {"empty_lanes_map": empty, "all_deferred": all_deferred},
        "passed": bool(empty) and bool(all_deferred),
    }


def check_missing_ownership_data(scope) -> dict:
    """A lane in the snapshot but absent from LANE_OWNERSHIP must be handled, not dropped."""
    missing = "99"
    state = {
        "lanes": {
            missing: {"doc": "AGENT-99-UNKNOWN.md", "doc_guard": "current"},
            **{n: {"doc": DOC[n], "doc_guard": "current"} for n in LANES},
        },
        "schema": "arkadia.lane-state/1.2",
    }
    judged = scope(state)
    return {
        "name": "a lane with no ownership entry is still subject to judgement",
        "detail": {"unknown_lane": missing, "unknown_lane_judged": missing in judged},
        "passed": missing in judged,
    }


CHECKS = (
    check_one_pr_cannot_exempt_its_own_lane,
    check_one_pr_cannot_empty_the_scope,
    check_scope_is_nonempty_for_adversarial_input,
    check_missing_ownership_data,
)


def run(scope) -> list[dict]:
    return [c(scope) for c in CHECKS]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true",
                    help="run the checks against a conforming design (control)")
    args = ap.parse_args(argv)

    if args.selftest:
        results = run(conforming_scope)
        failed = [r for r in results if not r["passed"]]
        if args.json:
            print(json.dumps({"target": "conforming_control",
                              "checks": results, "all_passed": not failed},
                             indent=2, sort_keys=True))
        else:
            print("SELFTEST: checks run against a conforming (fixed-scope) design")
            for r in results:
                print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['name']}")
            print()
            if failed:
                print(f"CONTROL FAILED: {len(failed)} check(s) fail on a conforming "
                      f"design -- the checks are not satisfiable and are unusable.")
            else:
                print(f"CONTROL OK: all {len(results)} checks pass on a conforming "
                      f"design, so a failure below is attributable to the shipped "
                      f"implementation.")
        return 1 if failed else 0

    results = run(shipped_scope)
    failed = [r for r in results if not r["passed"]]

    if args.json:
        print(json.dumps({"target": "shipped_implementation", "lanes": LANES,
                          "checks": results, "defect_present": bool(failed)},
                         indent=2, sort_keys=True))
    else:
        print("lane scope probe -- enforced set derived from the shipped implementation")
        print(f"lanes under consideration: {LANES}\n")
        for r in results:
            print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['name']}")
            print(f"       {r['detail']}")
        print()
        if failed:
            print(f"DEFECT PRESENT: {len(failed)} of {len(results)} checks failed.")
            print("The guard's enforced set is a function of the live PR activity it")
            print("evaluates, so opening a PR can remove a lane from judgement and one")
            print("broad PR can empty the blocking scope.")
        else:
            print(f"All {len(results)} checks passed: PR activity cannot alter the")
            print("enforced set, and the set cannot be emptied.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
