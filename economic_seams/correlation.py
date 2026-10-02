from __future__ import annotations

"""Evidence-gated seam correlation.

This module deliberately separates a source signal from a verified opportunity.
It does not infer demand, prices, counterparties, or legal eligibility from prose.
Promotion is deterministic and requires independently sourced evidence classes
plus explicit, human-reviewable transaction facts.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable
import hashlib
import json


REQUIRED_FACTS = (
    "demand",
    "supply",
    "price_basis",
    "costs",
    "capital_requirement",
    "counterparty",
    "execution_path",
    "failure_conditions",
)
VERIFIED_STATUS = "VERIFIED_CANDIDATE"
CANDIDATE_STATUS = "CANDIDATE_SEAM"


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
        """Stable identity prevents copied observations counting as independent."""
        material = "|".join((self.source_id, self.source_url, self.content_hash))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


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


def assess_seam(
    *,
    title: str,
    seam_type: str,
    evidence: Iterable[Evidence],
    facts: TransactionFacts,
) -> dict:
    """Return an explainable assessment; never fabricate missing facts."""
    items = list(evidence)
    # Count evidence classes only where source identities differ. Reposts,
    # duplicate URLs, and repeated snapshots cannot create independence.
    independent_by_class: dict[str, set[str]] = {}
    evidence_ids: list[str] = []
    for item in items:
        evidence_ids.append(item.evidence_id)
        independent_by_class.setdefault(item.source_class, set()).add(item.identity())
    independent_classes = {
        cls for cls, identities in independent_by_class.items()
        if identities and len(identities) >= 1
    }
    # Two classes are necessary, and each class must be represented by a
    # distinct source identity. Cross-class copies of the same source are not
    # independent evidence.
    distinct_sources = {item.identity() for item in items}
    missing = [key for key in REQUIRED_FACTS if not getattr(facts, key).strip()]
    if not facts.legal_basis.strip():
        missing.append("legal_basis")
    if not facts.why_spread_exists.strip():
        missing.append("why_spread_exists")
    independent = len(independent_classes) >= 2 and len(distinct_sources) >= 2
    legal_reviewed = bool(facts.human_eligibility_review and facts.legal_basis.strip())
    verified = independent and not missing and legal_reviewed and all(
        item.independently_verified for item in items
    ) and len(items) >= 2
    status = VERIFIED_STATUS if verified else CANDIDATE_STATUS if independent else "LEAD"
    blockers = []
    if not independent:
        blockers.append("Requires at least two independent evidence classes and distinct source identities.")
    if missing:
        blockers.append("Missing transaction facts: " + ", ".join(missing) + ".")
    if not legal_reviewed:
        blockers.append("Legal basis and eligibility require explicit human review.")
    unverified = [item.evidence_id for item in items if not item.independently_verified]
    if unverified:
        blockers.append("Evidence not independently verified: " + ", ".join(unverified) + ".")
    return {
        "title": title,
        "seam_type": seam_type,
        "status": status,
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
        "evidence_classes": sorted(independent_classes),
        "independent_source_count": len(distinct_sources),
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
            opportunity_id,
            assessment["title"],
            assessment["seam_type"],
            assessment["status"],
            assessment["facts"].get("legal_basis", ""),
            json.dumps(assessment["evidence_ids"]),
            "INDEPENDENTLY_VERIFIED" if assessment["verified"] else "UNVERIFIED",
            raw,
            now,
            now,
        ),
    )
    return opportunity_id
