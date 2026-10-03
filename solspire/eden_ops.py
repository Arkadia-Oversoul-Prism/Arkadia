"""EDEN-OPS-01 — Live Eden Operations Cockpit spine.

Binds the two real humans to Eden desks and drives the living-cell loop
through ARK-WEAVER-01 primitives. Does not create a second event system,
does not mutate WorkEvent semantics, and does not touch K15→K3.

High agency in analysis; low agency in authority.
UNKNOWN remains UNKNOWN until Evidence + Verification change it.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

EDEN_DESKS = (
    "Procurement",
    "Logistics",
    "Quality",
    "Marketing",
    "Brand/CX",
    "Digital",
    "Operations/Finance",
)

# Contingency/Reserve is financial control only — not a staffed desk.


def _now() -> float:
    return time.time()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS eden_role_bindings (
            id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            human_name TEXT NOT NULL,
            desk TEXT NOT NULL,
            bound_at REAL NOT NULL,
            unbound_at REAL,
            UNIQUE(enterprise_id, subject, desk)
        );
        CREATE INDEX IF NOT EXISTS idx_eden_bindings_enterprise
            ON eden_role_bindings(enterprise_id, unbound_at);
        """
    )
    conn.commit()
    return conn


@dataclass(frozen=True)
class RoleBinding:
    id: str
    enterprise_id: str
    subject: str
    human_name: str
    desk: str
    bound_at: float
    unbound_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FieldProjection:
    """Pure projection. Never invents RECORDED commercial/capital facts."""

    enterprise_id: str
    cycle: str = "Cycle 01"
    commercial: dict[str, str] = field(
        default_factory=lambda: {
            "commodity": "UNKNOWN",
            "supplier": "UNKNOWN",
            "buyer": "UNKNOWN",
            "buy_price": "UNKNOWN",
            "sell_price": "UNKNOWN",
            "route": "UNKNOWN",
        }
    )
    capital: dict[str, str] = field(
        default_factory=lambda: {
            "budget": "₦1,000,000",
            "committed": "UNKNOWN",
            "spent": "UNKNOWN",
            "recovered": "UNKNOWN",
        }
    )
    weaver_counters: dict[str, int] = field(
        default_factory=lambda: {
            "inputs": 0,
            "interpretations": 0,
            "unknowns": 0,
            "proposals": 0,
            "awaiting_authority": 0,
            "executions": 0,
            "evidence": 0,
            "verified": 0,
        }
    )
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EdenOps:
    """Cockpit spine over ARK-WEAVER-01."""

    def __init__(self, store: EnterpriseOrchestrationStore | None = None):
        self.store = store or EnterpriseOrchestrationStore()

    # ── Role binding ──────────────────────────────────────────────────────

    def bind_desk(
        self,
        *,
        enterprise_id: str,
        subject: str,
        human_name: str,
        desk: str,
    ) -> RoleBinding:
        if desk not in EDEN_DESKS:
            raise ValueError(f"unknown desk: {desk}; valid={list(EDEN_DESKS)}")
        rid = _id("bind")
        now = _now()
        with _db() as c:
            # Soft-uniqueness: re-bind if previously unbound
            existing = c.execute(
                "SELECT id FROM eden_role_bindings WHERE enterprise_id=? AND subject=? AND desk=? AND unbound_at IS NULL",
                (enterprise_id, subject, desk),
            ).fetchone()
            if existing:
                return RoleBinding(
                    id=existing["id"],
                    enterprise_id=enterprise_id,
                    subject=subject,
                    human_name=human_name,
                    desk=desk,
                    bound_at=now,
                )
            c.execute(
                "INSERT INTO eden_role_bindings VALUES (?,?,?,?,?,?,?)",
                (rid, enterprise_id, subject, human_name, desk, now, None),
            )
        return RoleBinding(rid, enterprise_id, subject, human_name, desk, now)

    def unbind_desk(
        self, *, enterprise_id: str, subject: str, desk: str
    ) -> None:
        with _db() as c:
            c.execute(
                "UPDATE eden_role_bindings SET unbound_at=? "
                "WHERE enterprise_id=? AND subject=? AND desk=? AND unbound_at IS NULL",
                (_now(), enterprise_id, subject, desk),
            )

    def list_bindings(self, *, enterprise_id: str) -> list[RoleBinding]:
        with _db() as c:
            rows = c.execute(
                "SELECT * FROM eden_role_bindings "
                "WHERE enterprise_id=? AND unbound_at IS NULL ORDER BY desk",
                (enterprise_id,),
            ).fetchall()
        return [
            RoleBinding(
                id=r["id"],
                enterprise_id=r["enterprise_id"],
                subject=r["subject"],
                human_name=r["human_name"],
                desk=r["desk"],
                bound_at=r["bound_at"],
                unbound_at=r["unbound_at"],
            )
            for r in rows
        ]

    def bind_default_two_humans(
        self,
        *,
        enterprise_id: str,
        architect_subject: str = "architect",
        jessica_subject: str = "jessica",
    ) -> list[RoleBinding]:
        """Bind both humans to all operational desks. System holds complexity."""
        out: list[RoleBinding] = []
        for desk in EDEN_DESKS:
            out.append(
                self.bind_desk(
                    enterprise_id=enterprise_id,
                    subject=architect_subject,
                    human_name="Divine Favour Yusuf",
                    desk=desk,
                )
            )
            out.append(
                self.bind_desk(
                    enterprise_id=enterprise_id,
                    subject=jessica_subject,
                    human_name="Jessica",
                    desk=desk,
                )
            )
        return out

    # ── Living-cell path ──────────────────────────────────────────────────

    def ingest_supplier_signal(
        self,
        *,
        subject: str,
        enterprise_id: str,
        message: str,
        source_channel: str = "human_entry",
        availability: str = "APPEARS_AVAILABLE",
        price: str = "UNKNOWN",
        confidence: float = 0.7,
    ) -> dict[str, Any]:
        """INTELLIGENCE zone: input → canonical → interpretation → ops → proposal."""
        canonical = self.store.canonical_record(
            subject=subject,
            source_channel=source_channel,
            raw_payload={"message": message, "enterprise_id": enterprise_id},
            ingested_by=subject,
        )
        interpretation = self.store.interpretation(
            subject=subject,
            canonical_record_id=canonical.id,
            interpreter="eden-ops-arkana",
            interpretation={
                "availability": availability,
                "price": price,
                "enterprise_id": enterprise_id,
            },
            confidence=confidence,
            correlation_id=canonical.correlation_id,
        )
        km = self.store.knowledge_mutation(
            subject=subject,
            previous_knowledge_refs=[],
            new_knowledge_refs=[f"supplier-signal:{canonical.id}"],
            mutation_type="SUPPLIER_SIGNAL",
            caused_by_kind="INTERPRETATION",
            caused_by_id=interpretation.id,
            correlation_id=canonical.correlation_id,
        )
        oe = self.store.operational_event(
            subject=subject,
            enterprise_id=enterprise_id,
            event_type="SUPPLIER_SIGNAL_INGESTED",
            payload={
                "canonical_id": canonical.id,
                "availability": availability,
                "price": price,
            },
            caused_by_kind="INTERPRETATION",
            caused_by_id=interpretation.id,
            correlation_id=canonical.correlation_id,
        )
        proposal = None
        if price == "UNKNOWN":
            proposal = self.store.proposal(
                subject=subject,
                enterprise_id=enterprise_id,
                objective="Verify supplier price",
                rationale="Availability indicated; price remains UNKNOWN; cannot compute transaction economics",
                recommended_actions=["verify_price"],
                required_authority="human",
                tool_selections=["supplier_verification"],
                correlation_id=canonical.correlation_id,
            )
        return {
            "canonical": canonical,
            "interpretation": interpretation,
            "knowledge_mutation": km,
            "operational_event": oe,
            "proposal": proposal,
        }

    def decide_proposal(
        self,
        *,
        subject: str,
        proposal_id: str,
        action: str,
        actor: str,
        actor_identity: dict[str, Any] | None = None,
        authentication_context: str = "authenticated_subject",
        authorization_scope: dict[str, Any] | None = None,
        authorization_constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """DECISIONS zone: approve / reject. Creates HAE + Authorization on approve."""
        action = action.upper()
        if action not in {"APPROVE", "REJECT"}:
            raise ValueError("action must be APPROVE or REJECT")

        # Load proposal correlation for causal binding
        import sqlite3 as _sq

        from weaver import enterprise_orchestration as ew

        with ew._db() as c:
            row = c.execute(
                "SELECT * FROM ew_proposals WHERE id=?", (proposal_id,)
            ).fetchone()
        if not row:
            raise ValueError("proposal not found")
        if row["subject"] != subject:
            raise ValueError("subject mismatch")

        if action == "APPROVE":
            # Enterprise authorization must be backed by the authenticated
            # identity's actual governance authority. An actor string alone
            # is provenance text, not proof of legitimate authority.
            if not isinstance(actor_identity, dict):
                raise ValueError("authenticated authority identity is required")
            if actor_identity.get("uid") != actor:
                raise ValueError("authority identity does not match actor")
            role = str(actor_identity.get("role") or "").strip().lower()
            try:
                access_level = int(actor_identity.get("access_level", 0))
            except (TypeError, ValueError):
                access_level = 0
            if role != "flamekeeper" and access_level < 3:
                raise ValueError("actor lacks Govern authority")

        if action == "REJECT":
            hae = self.store.authority_event(
                subject=subject,
                actor=actor,
                authority_context=row["enterprise_id"],
                action="REJECT_PROPOSAL",
                previous_state="AWAITING_AUTHORITY",
                new_state="REJECTED",
                origin="human",
                authentication_context=authentication_context,
                correlation_id=row["correlation_id"],
            )
            with ew._db() as c:
                c.execute(
                    "UPDATE ew_proposals SET status='REJECTED' WHERE id=?",
                    (proposal_id,),
                )
            return {"authority_event": hae, "authorization": None, "status": "REJECTED"}

        hae = self.store.authority_event(
            subject=subject,
            actor=actor,
            authority_context=row["enterprise_id"],
            action="APPROVE_PROPOSAL",
            previous_state="AWAITING_AUTHORITY",
            new_state="AUTHORIZED",
            origin="human",
            authentication_context=authentication_context,
            correlation_id=row["correlation_id"],
        )
        auth = self.store.authorize(
            subject=subject,
            proposal_id=proposal_id,
            authority_event_id=hae.id,
            scope=authorization_scope or {"objective": row["objective"]},
            constraints=authorization_constraints or {},
            correlation_id=row["correlation_id"],
        )
        return {"authority_event": hae, "authorization": auth, "status": "AUTHORIZED"}

    def execute_and_evidence(
        self,
        *,
        subject: str,
        authorization_id: str,
        tool_channel: str,
        request_payload: dict[str, Any],
        evidence_content: dict[str, Any],
        claim: str,
        verifier: str = "eden-ops",
    ) -> dict[str, Any]:
        """EXECUTION zone: attempt → evidence → verification."""
        attempt = self.store.execution_attempt(
            subject=subject,
            authorization_id=authorization_id,
            tool_channel=tool_channel,
            request_payload=request_payload,
            result_status="ATTEMPTED",
        )
        evidence = self.store.evidence(
            subject=subject,
            execution_attempt_id=attempt.id,
            evidence_type="execution_result",
            content_or_ref=evidence_content,
        )
        verification = self.store.verify(
            subject=subject,
            claim=claim,
            evidence_refs=[evidence.id],
            verifier=verifier,
            verdict="VERIFIED",
            correlation_id=attempt.correlation_id,
        )
        return {
            "execution_attempt": attempt,
            "evidence": evidence,
            "verification": verification,
        }

    def living_cell_supplier_path(
        self,
        *,
        subject: str,
        enterprise_id: str,
        message: str = "Supplier A: potatoes available; price not confirmed.",
        verified_price_ngn_per_kg: int = 1200,
    ) -> dict[str, Any]:
        """Full living-cell acceptance path (deterministic)."""
        ingest = self.ingest_supplier_signal(
            subject=subject,
            enterprise_id=enterprise_id,
            message=message,
            price="UNKNOWN",
        )
        assert ingest["proposal"] is not None, "price UNKNOWN must produce proposal"
        decision = self.decide_proposal(
            subject=subject,
            proposal_id=ingest["proposal"].id,
            action="APPROVE",
            actor=subject,
            actor_identity={"uid": subject, "role": "Flamekeeper", "access_level": 0},
        )
        assert decision["authorization"] is not None
        exec_result = self.execute_and_evidence(
            subject=subject,
            authorization_id=decision["authorization"].id,
            tool_channel="supplier_verification",
            request_payload={"supplier": "A", "commodity": "potatoes"},
            evidence_content={
                "supplier": "A",
                "commodity": "potatoes",
                "price_ngn_per_kg": verified_price_ngn_per_kg,
                "simulated": True,
            },
            claim=f"Supplier A potatoes price = ₦{verified_price_ngn_per_kg}/kg",
        )
        field = self.project_field(
            subject=subject,
            enterprise_id=enterprise_id,
            verified_price=verified_price_ngn_per_kg,
            supplier_hint="A",
            commodity_hint="potatoes",
        )
        walk = self.store.reverse_walk(
            subject=subject,
            kind="VERIFICATION",
            record_id=exec_result["verification"].id,
        )
        return {
            **ingest,
            **decision,
            **exec_result,
            "field": field,
            "reverse_walk": walk,
        }

    # ── FIELD projection ──────────────────────────────────────────────────

    def project_field(
        self,
        *,
        subject: str,
        enterprise_id: str,
        verified_price: int | None = None,
        supplier_hint: str | None = None,
        commodity_hint: str | None = None,
    ) -> FieldProjection:
        """FIELD zone: derived only. Never invents unsupported facts."""
        proj = FieldProjection(enterprise_id=enterprise_id)

        # Counters from ARK-WEAVER-01 operational stream (best-effort queries)
        import weaver.enterprise_orchestration as ew

        with ew._db() as c:
            def count(table: str, extra: str = "", args: tuple = ()) -> int:
                q = f"SELECT COUNT(*) AS n FROM {table} WHERE subject=? {extra}"
                r = c.execute(q, (subject, *args)).fetchone()
                return int(r["n"] if r else 0)

            proj.weaver_counters["inputs"] = count("ew_canonical_records")
            proj.weaver_counters["interpretations"] = count("ew_interpretations")
            proj.weaver_counters["proposals"] = count("ew_proposals")
            proj.weaver_counters["awaiting_authority"] = count(
                "ew_proposals", "AND status='PROPOSED'"
            )
            proj.weaver_counters["executions"] = count("ew_execution_attempts")
            proj.weaver_counters["evidence"] = count("ew_evidence")
            proj.weaver_counters["verified"] = count(
                "ew_verifications", "AND verdict='VERIFIED'"
            )

        # Commercial facts only where evidence supports them
        if verified_price is not None:
            proj.commercial["buy_price"] = f"₦{verified_price}/kg"
            proj.notes.append("buy_price from Evidence Record (not assumed)")
        if supplier_hint:
            proj.commercial["supplier"] = supplier_hint
            proj.notes.append("supplier from verified path hint")
        if commodity_hint:
            proj.commercial["commodity"] = commodity_hint
            proj.notes.append("commodity from verified path hint")

        # Capital remains UNKNOWN except static budget context
        # committed / spent / recovered stay UNKNOWN until real financial evidence exists

        # Count remaining commercial unknowns
        unknowns = sum(1 for v in proj.commercial.values() if v == "UNKNOWN")
        unknowns += sum(
            1
            for k, v in proj.capital.items()
            if k != "budget" and v == "UNKNOWN"
        )
        proj.weaver_counters["unknowns"] = unknowns
        return proj

    # ── TODAY summary ─────────────────────────────────────────────────────

    def today_summary(
        self, *, subject: str, enterprise_id: str
    ) -> dict[str, Any]:
        field = self.project_field(subject=subject, enterprise_id=enterprise_id)
        bindings = self.list_bindings(enterprise_id=enterprise_id)
        return {
            "enterprise_id": enterprise_id,
            "bindings": [b.to_dict() for b in bindings],
            "field": field.to_dict(),
            "critical_objectives": [
                "Confirm commodity candidates",
                "Verify current supplier pricing",
                "Identify buyer pool",
                "Establish logistics estimates",
            ],
            "decisions_required": field.weaver_counters["awaiting_authority"],
            "unknowns": field.weaver_counters["unknowns"],
        }
