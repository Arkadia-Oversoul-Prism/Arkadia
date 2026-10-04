"""Deterministic resolution-authority and evidence-sufficiency probe.

No LLM, external side effect, or production authorization lookup is used.
"""

from __future__ import annotations

from copy import deepcopy

RESOLUTION_ACTION = "resolve_conflict"

def resolution_eligibility(
    conflict: dict,
    proposed_claim: dict,
    evidence: dict | None,
    authorization: dict | None,
) -> dict:
    evidence_ok = bool(
        evidence
        and evidence.get("source_id")
        and proposed_claim in evidence.get("supports", [])
    )
    authority_ok = bool(
        authorization
        and authorization.get("authorization_id")
        and authorization.get("scope") == conflict.get("scope")
        and RESOLUTION_ACTION in authorization.get("permitted_actions", [])
    )

    if evidence_ok and authority_ok:
        status = "RESOLVED_PENDING_VERIFICATION"
    else:
        status = "REJECTED"

    return {
        "status": status,
        "evidence_sufficient": evidence_ok,
        "authority_sufficient": authority_ok,
    }

def resolve(
    conflict: dict,
    proposed_claim: dict,
    evidence: dict | None,
    authorization: dict | None,
) -> dict:
    eligibility = resolution_eligibility(
        conflict, proposed_claim, evidence, authorization
    )
    out = deepcopy(conflict)
    out["resolution_eligibility"] = eligibility
    out["verification_state"] = "UNKNOWN"
    out["authority_created"] = False

    if eligibility["status"] != "RESOLVED_PENDING_VERIFICATION":
        return out

    out["conflicts"] = []
    out["claims"] = [proposed_claim]
    out["resolution"] = {
        "status": "RESOLVED_PENDING_VERIFICATION",
        "evidence": evidence,
        "authorization": authorization,
    }
    return out

def run() -> None:
    conflict = {
        "scope": "sample.project",
        "claims": [],
        "conflicts": [{"subject": "sample.fact", "values": ["A", "B"]}],
        "verification_state": "UNKNOWN",
        "authority_created": False,
    }
    claim = {"subject": "sample.fact", "value": "A"}
    evidence = {"source_id": "E-100", "supports": [claim]}
    authorization = {
        "authorization_id": "AUTH-100",
        "scope": "sample.project",
        "permitted_actions": ["resolve_conflict"],
    }

    cases = [
        (None, None, "missing evidence and authority"),
        (evidence, None, "evidence without authority"),
        (None, authorization, "authority without evidence"),
        (evidence, {**authorization, "scope": "other.project"}, "scope mismatch"),
    ]
    for ev, auth, _label in cases:
        result = resolve(conflict, claim, ev, auth)
        assert result["resolution_eligibility"]["status"] == "REJECTED"
        assert result["conflicts"] == conflict["conflicts"]
        assert result["verification_state"] == "UNKNOWN"

    result = resolve(conflict, claim, evidence, authorization)
    assert result["resolution_eligibility"]["status"] == "RESOLVED_PENDING_VERIFICATION"
    assert result["conflicts"] == []
    assert result["claims"] == [claim]
    assert result["verification_state"] == "UNKNOWN"
    assert result["authority_created"] is False

    print("PASS: missing or mismatched evidence/authority cannot resolve")
    print("PASS: sufficient evidence + scoped authorization permits resolution pending verification")
    print("PASS: resolution does not imply verification or create authority")

if __name__ == "__main__":
    run()