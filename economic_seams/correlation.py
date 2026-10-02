from __future__ import annotations

"""Evidence-gated seam correlation.

A lead is not a verified opportunity. Independent corroboration is counted by
registered provider identity, not URL, snapshot, or content hash. API callers
cannot promote their own evidence by submitting reviewer booleans.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable
import hashlib
import json


REQUIRED_FACTS = (
    "demand", "supply", "price_basis", "costs", "capital_requirement",
    "counterparty", "execution_path", "failure_conditions",
)
VERIFIED_STATUS = "VERIFIED_CANDIDATE"
CANDIDATE_STATUS = "CANDIDATE_SEAM"
\n# Canonical provider identities. A URL or content hash is never an identity.\n# New providers must be registered here before they can satisfy independence.\nREGISTERED_PROVIDER_IDENTITIES = {\n    "portal", "prices", "nocopo", "cbn_fx", "nepc_prices",\n}\n

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_id: str
    source_class: str
    source_url: str
    content_hash: str
    observed_at: str
    fact_key: str
    fact_value: str
    independently_verified: bool = False

    def identity(self) -> str:
        """Provider identity, deliberately stable across URLs and snapshots."""
        return self.source_id.strip().lower()


@dataclass(frozen=True)
class TransactionFacts:
    demand: str = ""
    supply: str = ""
    price_basis: str = ""
    costs: str = ""
    capital_requirement: str = ""
    counterparty: str = ""
    execution_path: str = ""
    failure_conditions: str = ""
    legal_basis: str = ""
    why_spread_exists: str = ""
    human_eligibility_review: bool = False
    reviewer_uid: str = ""
    reviewed_at: str = ""


def assess_seam(*, title: str, seam_type: str, evidence: Iterable[Evidence],
                facts: TransactionFacts) -> dict:
    """Return a transparent assessment without fabricating missing facts."""
    items = list(evidence)
    evidence_ids = list(dict.fromkeys(item.evidence_id for item in items))
    source_classes = {item.source_class.strip().upper() for item in items if item.source_class.strip()}
    source_ids = {item.identity() for item in items if item.identity() in REGISTERED_PROVIDER_IDENTITIES}
    # Each provider can support only the source class registered for this
    # observation. Reposts or different pages from one provider never add a
    # second independent source.
    class_providers: dict[str, set[str]] = {}
    for item in items:
        if item.source_class.strip() and item.identity():
            if item.identity() in REGISTERED_PROVIDER_IDENTITIES:\n                class_providers.setdefault(item.source_class.strip().upper(), set()).add(item.identity())
    independent = len(source_ids) >= 2 and len(source_classes) >= 2
    missing = [key for key in REQUIRED_FACTS if not str(getattr(facts, key)).strip()]
    if not facts.legal_basis.strip():
        missing.append("legal_basis")
    if not facts.why_spread_exists.strip():
        missing.append("why_spread_exists")
    legal_reviewed = bool(
        facts.human_eligibility_review and facts.legal_basis.strip()
        and facts.reviewer_uid.strip() and facts.reviewed_at.strip()
    )
    verified = (
        independent and not missing and legal_reviewed and len(items) >= 2
        and all(item.independently_verified for item in items)
    )
    status = VERIFIED_STATUS if verified else CANDIDATE_STATUS if independent else "LEAD"
    blockers = []
    if not independent:
        blockers.append("Requires at least two registered provider identities across at least two evidence classes.")
    if missing:
        blockers.append("Missing transaction facts: " + ", ".join(missing) + ".")
    if not legal_reviewed:
        blockers.append("Auditable human eligibility review is incomplete (reviewer identity and timestamp required).")
    unverified = [item.evidence_id for item in items if not item.independently_verified]
    if unverified:
        blockers.append("Evidence not independently verified: " + ", ".join(unverified) + ".")
    return {
        "title": title,
        "seam_type": seam_type,
        "status": status,
        "evidence_ids": evidence_ids,
        "evidence_classes": sorted(source_classes),
        "independent_source_count": len(source_ids),
        "facts": asdict(facts),
        "missing_facts": missing,
        "blockers": blockers,
        "verified": verified,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def persist_assessment(connection, assessment: dict) -> str:
    """Persist an assessment into the engine's existing opportunity table."""
    raw = json.dumps(assessment, sort_keys=True, separators=(",", ":"))
    opportunity_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """INSERT OR REPLACE INTO opportunities
           (id, title, seam_type, status, legal_basis, evidence_ids,
            evidence_level, rationale, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            opportunity_id, assessment["title"], assessment["seam_type"],
            assessment["status"], assessment["facts"].get("legal_basis", ""),
            json.dumps(assessment["evidence_ids"]),
            "INDEPENDENTLY_VERIFIED" if assessment["verified"] else "UNVERIFIED",
            raw, now, now,
        ),
    )
    return opportunity_id
