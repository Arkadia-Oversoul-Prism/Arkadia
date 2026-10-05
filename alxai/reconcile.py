from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from .protocol import (
    ALXModel, Claim, DIRECT_MODES, Evidence, Event, Decision, State, Status,
    _claim_key, _parse_dt, digest,
)


class Reconciliation(ALXModel):
    reconciliation_id: str
    base_state_id: str
    left_state_id: str
    right_state_id: str
    resulting_state_id: str
    created_at: datetime
    status: Literal["MERGED", "CONFLICTED", "ADJUDICATION_REQUIRED"]
    merged_claim_ids: list[str] = []
    corroborated_claim_ids: list[str] = []
    superseded_claim_ids: list[str] = []
    conflict_claim_ids: list[str] = []
    reasons: list[str] = []


def _claim_time(c: Claim) -> datetime:
    return _parse_dt(c.observed_at) or datetime.min.replace(tzinfo=timezone.utc)


def _authority_applies(c: Claim, state: State) -> bool:
    authority = c.source_authority.strip().lower()
    for source in state.source_registry:
        names = {source.source_id.strip().lower(), source.domain.strip().lower()}
        scopes = {s.strip().lower() for s in source.authority_scope}
        if authority in names and (
            "*" in scopes
            or c.predicate.strip().lower() in scopes
            or c.scope.strip().lower() in scopes
        ):
            return True
    return False


def reconcile_states(
    base: State,
    left: State,
    right: State,
    *,
    reconciliation_id: str,
    created_at: datetime,
) -> tuple[State, Reconciliation]:
    if left.parent_state_id != base.state_id or right.parent_state_id != base.state_id:
        raise ValueError("both branch states must descend directly from the supplied base state")

    claims = {c.claim_id: c for c in base.claims}
    evidence = {e.evidence_id: e for e in base.evidence}
    events = {e.event_id: e for e in base.events}
    decisions = {d.decision_id: d for d in base.decisions}
    conflicts = list(base.conflicts)
    merged_ids: list[str] = []
    corroborated_ids: list[str] = []
    superseded_ids: list[str] = []
    conflict_ids: list[str] = []
    reasons: list[str] = []

    for e in [*left.evidence, *right.evidence]:
        evidence[e.evidence_id] = e
    for e in [*left.events, *right.events]:
        events[e.event_id] = e
    for d in [*left.decisions, *right.decisions]:
        decisions[d.decision_id] = d

    by_key: dict[tuple[str, str, str, str], list[Claim]] = {}
    for c in [*left.claims, *right.claims]:
        by_key.setdefault(_claim_key(c), []).append(c)

    for key, candidates0 in by_key.items():
        candidates = list({c.claim_id: c for c in candidates0}.values())
        if len(candidates) == 1:
            claims[candidates[0].claim_id] = candidates[0]
            merged_ids.append(candidates[0].claim_id)
            continue

        if len({_canon(c.object) for c in candidates}) == 1:
            winner = max(candidates, key=_claim_time)
            refs = list(dict.fromkeys(r for c in candidates for r in c.evidence_refs))
            claims[winner.claim_id] = winner.model_copy(update={"evidence_refs": refs})
            for c in candidates:
                if c.claim_id != winner.claim_id:
                    claims[c.claim_id] = c.model_copy(update={"status": Status.SUPERSEDED})
            corroborated_ids.append(winner.claim_id)
            reasons.append(f"independent corroboration for {key}")
            continue

        direct = [c for c in candidates if c.observation_mode in DIRECT_MODES]
        authoritative = [
            c for c in direct
            if _authority_applies(c, left) or _authority_applies(c, right)
        ]
        winner = None
        if authoritative:
            newest = max(authoritative, key=_claim_time)
            if sum(_claim_time(c) == _claim_time(newest) for c in authoritative) == 1:
                winner = newest
                reasons.append(f"domain-authoritative source selected within declared scope for {key}")
        if winner is None and direct:
            newest = max(direct, key=_claim_time)
            if sum(_claim_time(c) == _claim_time(newest) for c in direct) == 1:
                winner = newest
                reasons.append(f"newer direct observation superseded older observation for {key}")

        if winner is not None:
            claims[winner.claim_id] = winner
            for c in candidates:
                if c.claim_id != winner.claim_id:
                    claims[c.claim_id] = c.model_copy(update={"status": Status.SUPERSEDED})
                    superseded_ids.append(c.claim_id)
            merged_ids.append(winner.claim_id)
        else:
            for c in candidates:
                claims[c.claim_id] = c.model_copy(update={"status": Status.CONFLICTED})
                conflict_ids.append(c.claim_id)
            conflicts.append(f"RECONCILIATION:{reconciliation_id}:{key}")
            reasons.append(f"contradictory direct observations require adjudication for {key}")

    source_registry = sorted(
        {
            s.source_id: s
            for s in [*base.source_registry, *left.source_registry, *right.source_registry]
        }.values(),
        key=lambda x: x.source_id,
    )
    result = State(
        state_id=f"STATE-MERGED-{reconciliation_id}",
        parent_state_id=base.state_id,
        protocol_version=base.protocol_version,
        created_at=created_at,
        claims=sorted(claims.values(), key=lambda x: x.claim_id),
        evidence=sorted(evidence.values(), key=lambda x: x.evidence_id),
        events=sorted(events.values(), key=lambda x: x.event_id),
        decisions=sorted(decisions.values(), key=lambda x: x.decision_id),
        conflicts=list(dict.fromkeys(conflicts)),
        unknowns=list(dict.fromkeys(base.unknowns + left.unknowns + right.unknowns)),
        capabilities=right.capabilities or left.capabilities or base.capabilities,
        source_registry=source_registry,
    ).with_root()
    rec = Reconciliation(
        reconciliation_id=reconciliation_id,
        base_state_id=base.state_id,
        left_state_id=left.state_id,
        right_state_id=right.state_id,
        resulting_state_id=result.state_id,
        created_at=created_at,
        status="ADJUDICATION_REQUIRED" if conflict_ids else "MERGED",
        merged_claim_ids=list(dict.fromkeys(merged_ids)),
        corroborated_claim_ids=list(dict.fromkeys(corroborated_ids)),
        superseded_claim_ids=list(dict.fromkeys(superseded_ids)),
        conflict_claim_ids=list(dict.fromkeys(conflict_ids)),
        reasons=list(dict.fromkeys(reasons)),
    )
    return result, rec


def _canon(value):
    import json
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AuthorityBinding(ALXModel):
    """Exact authority grant captured at adjudication time.

    This is an authorization boundary, not a capability expansion. The
    authority record is resolved from a Decision in the supplied state.
    """

    authority_id: str
    authority_record_id: str
    authority_record_digest: str
    authority_scope: str
    granted_actions: list[str] = []
    issued_at: datetime
    valid_until: datetime | None = None


class Adjudication(ALXModel):
    adjudication_id: str
    reconciliation_id: str
    decision_maker: str
    scope: str
    selected_claim_id: str
    rejected_claim_ids: list[str] = []
    evidence_refs: list[str] = []
    authorized_actions: list[str] = []
    decided_at: datetime
    rationale: str
    authority_binding: AuthorityBinding
    status: Literal["ACCEPTED", "REJECTED", "UNKNOWN"] = "ACCEPTED"
    certificate_digest: str | None = None

    def with_certificate(self) -> "Adjudication":
        raw = self.model_copy(update={"certificate_digest": None})
        return raw.model_copy(
            update={
                "certificate_digest": digest(
                    raw.model_dump(mode="json", exclude={"certificate_digest"})
                )
            }
        )

    def _verify_authority_binding(self, state: State, *, now: datetime | None = None) -> None:
        binding = self.authority_binding
        if binding.authority_id != self.decision_maker:
            raise ValueError("adjudication authority does not match decision maker")
        if binding.authority_scope != self.scope:
            raise ValueError("adjudication scope does not exactly match bound authority scope")
        if set(self.authorized_actions) - set(binding.granted_actions):
            raise ValueError("adjudication requests actions outside bound authority grant")

        record = next(
            (d for d in state.decisions if d.decision_id == binding.authority_record_id),
            None,
        )
        if record is None:
            raise ValueError("bound authority record does not exist in state")
        if record.decision_maker != binding.authority_id:
            raise ValueError("bound authority record maker does not match authority binding")
        if record.decision_scope != binding.authority_scope:
            raise ValueError("bound authority record scope does not match authority binding")
        if set(self.authorized_actions) - set(record.authorized_actions):
            raise ValueError("adjudication action exceeds authority record actions")
        if binding.authority_record_digest != digest(
            record.model_dump(mode="json")
        ):
            raise ValueError("bound authority record digest mismatch")

        current = _parse_dt(now) or datetime.now(timezone.utc)
        issued = _parse_dt(binding.issued_at)
        if issued and current < issued:
            raise ValueError("authority binding is not yet valid")
        expiry = _parse_dt(binding.valid_until)
        if expiry and current > expiry:
            raise ValueError("authority binding has expired")
        if expiry and issued and expiry < issued:
            raise ValueError("authority binding valid_until precedes issued_at")

    def can_authorize(
        self,
        *,
        action: str,
        subject_scope: str,
        state: State,
        now: datetime | None = None,
    ) -> bool:
        """Fail closed: test an exact action against the certificate's authority.

        Acceptance of a claim never creates new authority. This method only
        returns true when the action and subject scope remain inside the
        original authority record bound into the certificate.
        """
        self._verify_authority_binding(state, now=now)
        if action not in self.authorized_actions:
            return False
        return _scope_contains(self.scope, subject_scope)


def _scope_contains(parent: str, child: str) -> bool:
    parent = parent.strip()
    child = child.strip()
    if not parent or not child:
        return False
    if parent == "*":
        return True
    if parent == child:
        return True
    return child.startswith(parent + ".")


def apply_adjudication(state: State, adjudication: Adjudication) -> State:
    if adjudication.status != "ACCEPTED":
        raise ValueError("only ACCEPTED adjudications may alter a state")
    if adjudication.certificate_digest != digest(
        adjudication.model_dump(mode="json", exclude={"certificate_digest"})
    ):
        raise ValueError("adjudication certificate digest mismatch")

    adjudication._verify_authority_binding(state)

    ids = {c.claim_id for c in state.claims}
    if adjudication.selected_claim_id not in ids:
        raise ValueError("selected claim does not exist in state")
    if not set(adjudication.rejected_claim_ids).issubset(ids):
        raise ValueError("rejected claim does not exist in state")
    if adjudication.selected_claim_id in adjudication.rejected_claim_ids:
        raise ValueError("selected claim cannot also be rejected")

    selected = next(c for c in state.claims if c.claim_id == adjudication.selected_claim_id)
    if not _scope_contains(adjudication.scope, selected.scope):
        raise ValueError("selected claim scope exceeds adjudication authority scope")

    missing_evidence = set(adjudication.evidence_refs) - {
        e.evidence_id for e in state.evidence
    }
    if missing_evidence:
        raise ValueError(f"adjudication references missing evidence: {sorted(missing_evidence)}")

    updated = []
    for claim in state.claims:
        if claim.claim_id == adjudication.selected_claim_id:
            updated.append(claim.model_copy(update={"status": Status.ACTIVE}))
        elif claim.claim_id in adjudication.rejected_claim_ids:
            updated.append(claim.model_copy(update={"status": Status.SUPERSEDED}))
        else:
            updated.append(claim)

    conflict_prefix = f"RECONCILIATION:{adjudication.reconciliation_id}:"
    remaining_conflicts = [
        x for x in state.conflicts if not x.startswith(conflict_prefix)
    ]
    remaining_conflicts.append(
        f"ADJUDICATED:{adjudication.adjudication_id}:{adjudication.selected_claim_id}"
    )
    return State(
        state_id=f"STATE-ADJ-{adjudication.adjudication_id}",
        parent_state_id=state.state_id,
        protocol_version=state.protocol_version,
        created_at=adjudication.decided_at,
        claims=sorted(updated, key=lambda x: x.claim_id),
        evidence=state.evidence,
        events=state.events,
        decisions=state.decisions,
        conflicts=remaining_conflicts,
        unknowns=state.unknowns,
        capabilities=state.capabilities,
        source_registry=state.source_registry,
    ).with_root()
