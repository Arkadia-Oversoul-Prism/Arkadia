"""GOV-04 condition 2 names platform controls; this pins the oracle that reads them.

GOV-04's merge delegation requires that "required checks pass", "required reviews
are present" and "branch protections and merge queue are satisfied". Those are
platform-enforced facts, and until ``scripts/gov04_platform_preconditions.py``
existed nothing in the repository measured them: the only other GOV-04 surface,
``tests/test_gov04_bounded_merge_delegation.py``, reads the authorization
document's wording. Measured at ``main`` ``fd0a4fdc`` the platform enforces
nothing (``branches/main/protection`` -> 404 "Branch not protected",
``rulesets`` -> ``[]``), so every clause is vacuously true.

The guard's teeth are on the **classifier**, not on the operator's choice to leave
``main`` unprotected. Enabling branch protection is a sovereign/provider
configuration decision; a guard that reddened CI for it would report a decision as
repository debt. What must never happen is a verdict of ``ENFORCED`` without
positive evidence, or an unreadable measurement promoted to a satisfied control --
and each of those has a control below that fails if the classifier is weakened.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gov04_platform_preconditions.py"

_SPEC = importlib.util.spec_from_file_location("gov04_platform_preconditions", SCRIPT)
gov04 = importlib.util.module_from_spec(_SPEC)
# The module carries a dataclass under `from __future__ import annotations`, so it
# must be registered before exec for the decorator to resolve its own namespace.
sys.modules[_SPEC.name] = gov04
_SPEC.loader.exec_module(gov04)


def _judge(payload: dict) -> dict:
    return gov04._judge(payload)


# --- positive control -------------------------------------------------------

FULL_PROTECTION = {
    "required_status_checks": {"contexts": ["test", "boot-syntax"], "strict": True},
    "required_pull_request_reviews": {"required_approving_review_count": 2},
}


def test_positive_control_a_protected_branch_with_controls_is_enforced():
    verdict = gov04.classify(FULL_PROTECTION, gov04.PROTECTION_PRESENT, [])
    assert verdict.verdict == gov04.ENFORCED
    assert verdict.required_checks == ("boot-syntax", "test")
    assert verdict.required_reviews == 2


def test_status_checks_declared_as_checks_objects_are_read_too():
    protection = {"required_status_checks": {"checks": [{"context": "console-contract"}]}}
    verdict = gov04.classify(protection, gov04.PROTECTION_PRESENT, [])
    assert verdict.verdict == gov04.ENFORCED
    assert verdict.required_checks == ("console-contract",)


# --- negative controls ------------------------------------------------------

def test_negative_control_measured_absence_is_vacuous():
    """The live state at fd0a4fdc: not protected, no rulesets."""
    verdict = gov04.classify(None, gov04.PROTECTION_ABSENT, [])
    assert verdict.verdict == gov04.VACUOUS
    assert verdict.required_checks == ()
    assert verdict.required_reviews == 0


def test_protection_present_without_required_checks_or_reviews_is_still_vacuous():
    """`enforce_admins` and push `restrictions` do not gate a merge."""
    protection = {"enforce_admins": {"enabled": True}, "restrictions": {"users": []}}
    verdict = gov04.classify(protection, gov04.PROTECTION_PRESENT, [])
    assert verdict.verdict == gov04.VACUOUS


def test_an_inactive_ruleset_is_not_a_control():
    """A ruleset in `evaluate` mode reports, it does not enforce."""
    rulesets = [{"enforcement": "evaluate", "rules": [{"type": "required_status_checks"}]}]
    verdict = gov04.classify(None, gov04.PROTECTION_ABSENT, rulesets)
    assert verdict.verdict == gov04.VACUOUS


def test_an_active_ruleset_without_merge_rules_is_not_a_control():
    rulesets = [{"enforcement": "active", "rules": [{"type": "deletion"}]}]
    verdict = gov04.classify(None, gov04.PROTECTION_ABSENT, rulesets)
    assert verdict.verdict == gov04.VACUOUS


def test_an_active_ruleset_carrying_required_checks_is_enforced():
    """A ruleset is an equivalent control, so it must be honoured."""
    rulesets = [{"enforcement": "active", "rules": [{"type": "required_status_checks"}]}]
    verdict = gov04.classify(None, gov04.PROTECTION_ABSENT, rulesets)
    assert verdict.verdict == gov04.ENFORCED


# --- fail-closed controls ---------------------------------------------------

def test_unreadable_evidence_is_unknown_and_never_enforced():
    assert gov04.classify(None, gov04.PROTECTION_UNKNOWN, None).verdict == gov04.UNKNOWN
    assert gov04.classify(None, gov04.PROTECTION_UNKNOWN, []).verdict == gov04.UNKNOWN
    assert gov04.classify(FULL_PROTECTION, gov04.PROTECTION_PRESENT, None).verdict == gov04.UNKNOWN


def test_contradictory_evidence_fails_closed():
    """"Present" with no payload is a contradiction, not an enforcement."""
    assert gov04.classify(None, gov04.PROTECTION_PRESENT, []).verdict == gov04.UNKNOWN


def test_an_unrecognised_protection_state_raises_rather_than_guessing():
    with pytest.raises(ValueError):
        gov04.classify(None, "maybe", [])


# --- CLI contract -----------------------------------------------------------

def _run(args, stdin=None, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def test_cli_judge_round_trips_a_payload():
    payload = json.dumps({"protection_state": "absent", "rulesets": []})
    result = _run(["--judge"], stdin=payload)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verdict"] == gov04.VACUOUS


def test_cli_judge_rejects_malformed_input():
    assert _run(["--judge"], stdin="{not json").returncode == 2
    assert _run(["--judge"], stdin=json.dumps({"protection_state": "nonsense"})).returncode == 2
    assert _run(["--judge"], stdin=json.dumps({"rulesets": "not-a-list"})).returncode == 2


def test_cli_measure_refuses_without_a_credential_and_prints_none():
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
    result = _run(["--measure"], env=env)
    assert result.returncode == 2
    assert "GITHUB_TOKEN is not set" in result.stderr
    assert result.stdout.strip() == ""
