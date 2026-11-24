#!/usr/bin/env python3
"""GOV-04 platform-precondition oracle.

GOV-04 (``docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md``)
authorises a bounded merge delegation whose condition 2 reads:

    "All required checks pass; required reviews/CODEOWNERS approvals are present;
     branch protections and merge queue are satisfied."

Every clause names a *platform-enforced* control. Nothing in this repository
measured whether such controls exist. ``grep -rn "branch protection|
branch_protection|rulesets" tests/ scripts/ .github/`` matched only the GOV-04
document pin in ``tests/test_gov04_bounded_merge_delegation.py``, which reads the
document's wording and never the platform. Measured at ``main`` ``fd0a4fdc``
(2026-11-24):

    GET /repos/<owner>/<repo>/branches/main/protection  -> 404 "Branch not protected"
    GET /repos/<owner>/<repo>/rulesets                  -> []

Condition 2 is therefore **vacuously satisfiable** -- nothing is required, so
nothing can fail -- and the clause reads as a safeguard while measuring nothing.
This is the same class already recorded for a field that is written but never
judged and a guard that prints a verdict but does not act on it.

This module is the missing oracle. It turns the two REST payloads into *evidence*
and returns one verdict:

``ENFORCED``
    positive evidence of at least one control that a merge can *fail*: required
    status checks, required pull-request reviews, or an active ruleset carrying
    one of those rules.
``VACUOUS``
    measured absence of every such control, so the precondition cannot fail.
``UNKNOWN``
    the evidence could not be read, or it contradicts itself. Never promoted to
    ``ENFORCED`` -- an unprovable control is not a satisfied one.

The classifier is pure and never touches the network, so a guard can test it
offline. ``--measure`` performs the read-only fetch and prints the evidence
alongside the verdict; it needs ``GITHUB_TOKEN`` and never prints it.

A verdict is an **observation, not a defect**. ``VACUOUS`` does not fail a gate:
enabling branch protection is a sovereign/provider configuration decision, and a
guard that reddened ``main`` for the operator's choice would be reporting a
decision as repository debt. The guard's teeth are on the classifier -- a verdict
may never be ``ENFORCED`` without positive evidence. See
``tests/test_gov04_platform_preconditions.py``.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

ENFORCED = "ENFORCED"
VACUOUS = "VACUOUS"
UNKNOWN = "UNKNOWN"

PROTECTION_PRESENT = "present"
PROTECTION_ABSENT = "absent"
PROTECTION_UNKNOWN = "unknown"

PROTECTION_STATES = (PROTECTION_PRESENT, PROTECTION_ABSENT, PROTECTION_UNKNOWN)

# Ruleset rule types that constrain a merge rather than a push.
_MERGE_CONTROL_RULES = frozenset(
    {"required_status_checks", "pull_request", "required_deployments", "merge_queue"}
)

API_ROOT = "https://api.github.com"
DEFAULT_REPO = "Arkadia-Oversoul-Prism/Arkadia"
DEFAULT_BRANCH = "main"


@dataclass(frozen=True)
class Classification:
    verdict: str
    required_checks: tuple[str, ...] = ()
    required_reviews: int = 0
    ruleset_rules: tuple[str, ...] = ()
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "required_checks": list(self.required_checks),
            "required_reviews": self.required_reviews,
            "ruleset_rules": list(self.ruleset_rules),
            "detail": self.detail,
        }


def _required_checks(protection: dict) -> tuple[str, ...]:
    block = protection.get("required_status_checks") or {}
    contexts = [c for c in (block.get("contexts") or []) if isinstance(c, str) and c]
    for check in block.get("checks") or []:
        if isinstance(check, dict) and isinstance(check.get("context"), str):
            contexts.append(check["context"])
    return tuple(sorted(set(contexts)))


def _required_reviews(protection: dict) -> int:
    block = protection.get("required_pull_request_reviews") or {}
    count = block.get("required_approving_review_count")
    return count if isinstance(count, int) and count > 0 else 0


def _ruleset_rules(rulesets) -> tuple[str, ...]:
    types: set[str] = set()
    for ruleset in rulesets or []:
        if not isinstance(ruleset, dict):
            continue
        for rule in ruleset.get("rules") or []:
            if isinstance(rule, dict) and isinstance(rule.get("type"), str):
                types.add(rule["type"])
    return tuple(sorted(types))


def _active_rulesets(rulesets) -> int:
    return sum(
        1
        for ruleset in rulesets or []
        if isinstance(ruleset, dict) and ruleset.get("enforcement") == "active"
    )


def classify(
    protection: dict | None = None,
    protection_state: str = PROTECTION_UNKNOWN,
    rulesets: list | None = None,
) -> Classification:
    """Classify the GOV-04 condition-2 platform evidence.

    ``protection_state`` distinguishes a *measured absence* (``absent``, the REST
    404 "Branch not protected") from an *unreadable* one (``unknown``). They need
    opposite responses -- ``VACUOUS`` is a fact about the platform, ``UNKNOWN`` is
    a fact about the measurement -- so they never share a verdict.
    """
    if protection_state not in PROTECTION_STATES:
        raise ValueError(f"unknown protection_state: {protection_state!r}")

    if protection_state == PROTECTION_PRESENT and not isinstance(protection, dict):
        # "Protected" with no payload is contradictory evidence, not enforcement.
        protection_state = PROTECTION_UNKNOWN

    checks = _required_checks(protection) if protection_state == PROTECTION_PRESENT else ()
    reviews = _required_reviews(protection) if protection_state == PROTECTION_PRESENT else 0
    rules = _ruleset_rules(rulesets)
    controlling = tuple(r for r in rules if r in _MERGE_CONTROL_RULES)

    if protection_state == PROTECTION_UNKNOWN or rulesets is None:
        return Classification(
            UNKNOWN,
            checks,
            reviews,
            rules,
            "platform-control evidence could not be read; an unprovable control is not "
            "a satisfied one, so the verdict is not promoted to ENFORCED",
        )

    if checks or reviews or (_active_rulesets(rulesets) and controlling):
        return Classification(
            ENFORCED,
            checks,
            reviews,
            rules,
            "at least one platform control can fail a merge",
        )

    if protection_state == PROTECTION_PRESENT:
        return Classification(
            VACUOUS,
            checks,
            reviews,
            rules,
            "the branch is protected but carries no required status checks, no required "
            "reviews, and no active merge-controlling ruleset, so GOV-04 condition 2 "
            "cannot fail",
        )

    return Classification(
        VACUOUS,
        checks,
        reviews,
        rules,
        "no branch protection and no ruleset is configured, so every clause of GOV-04 "
        "condition 2 ('required checks pass', 'required reviews are present', 'branch "
        "protections are satisfied') is vacuously true",
    )


def _get_json(url: str, token: str) -> tuple[object, int]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "arkadia-gov04-platform-preconditions",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return (json.loads(body) if body.strip() else None), response.status
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, 404
        raise


def measure(repo: str = DEFAULT_REPO, branch: str = DEFAULT_BRANCH, token: str | None = None) -> dict:
    """Read the two REST payloads and classify them. Read-only; prints no token."""
    token = token or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set; --measure needs a read-only credential")

    protection, status = _get_json(f"{API_ROOT}/repos/{repo}/branches/{branch}/protection", token)
    if status == 200:
        protection_state = PROTECTION_PRESENT
    elif status == 404:
        protection_state = PROTECTION_ABSENT
    else:
        protection_state = PROTECTION_UNKNOWN

    try:
        rulesets, _ = _get_json(f"{API_ROOT}/repos/{repo}/rulesets", token)
        if not isinstance(rulesets, list):
            rulesets = None
    except (urllib.error.URLError, OSError, ValueError):
        rulesets = None

    return {
        "schema": "arkadia.gov04-platform-preconditions/v1",
        "repo": repo,
        "branch": branch,
        "evidence": {
            "protection_state": protection_state,
            "protection_status_code": status,
            "ruleset_count": len(rulesets or []),
        },
        "classification": classify(protection, protection_state, rulesets).as_dict(),
    }


def _judge(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    state = payload.get("protection_state", PROTECTION_UNKNOWN)
    rulesets = payload.get("rulesets")
    if rulesets is not None and not isinstance(rulesets, list):
        raise ValueError("rulesets must be a list or null")
    return classify(payload.get("protection"), state, rulesets).as_dict()


def main(argv: list[str]) -> int:
    if "--measure" in argv:
        repo, branch = DEFAULT_REPO, DEFAULT_BRANCH
        if "--repo" in argv:
            repo = argv[argv.index("--repo") + 1]
        if "--branch" in argv:
            branch = argv[argv.index("--branch") + 1]
        try:
            print(json.dumps(measure(repo, branch), indent=2, sort_keys=True))
        except (RuntimeError, urllib.error.URLError, OSError, ValueError) as exc:
            print(f"gov04-platform-preconditions: {exc}", file=sys.stderr)
            return 2
        return 0

    if "--judge" in argv:
        try:
            print(json.dumps(_judge(json.load(sys.stdin)), indent=2, sort_keys=True))
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"gov04-platform-preconditions: {exc}", file=sys.stderr)
            return 2
        return 0

    print(__doc__.strip(), file=sys.stderr)
    print("\nusage: gov04_platform_preconditions.py --measure [--repo O/R] [--branch NAME]",
          file=sys.stderr)
    print("       gov04_platform_preconditions.py --judge  < payload.json", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
