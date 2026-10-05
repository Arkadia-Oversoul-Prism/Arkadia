from datetime import datetime, timezone

from alxai.protocol import (
    Claim, Evidence, EpistemicClass, ObservationMode,
    create_delta, create_state, validate_packet, apply_delta, digest,
)

T0 = datetime(2026, 10, 5, 3, 0, tzinfo=timezone.utc)
PR = "ee5e26cd1bc6c3901a113c1d72f7cf59b1bc83b2"


def claim(cid, node, mode, obj, evidence_id, authority="GitHub"):
    return Claim(
        claim_id=cid, subject="github:PR#294", predicate="head_sha", object=obj,
        source_authority=authority, observation_mode=mode,
        epistemic_class=EpistemicClass.OBSERVED_FACT,
        observed_at=T0, evidence_refs=[evidence_id],
    )


def evidence(eid, node, mode, locator="github:pull/294"):
    return Evidence(
        evidence_id=eid, source_id="github", source_authority="GitHub",
        observation_mode=mode, observed_at=T0, locator=locator,
        collector_node=node, integrity_status="VALID",
    )


def test_state_root_and_delta_round_trip():
    genesis = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    e = evidence("E-CHATGPT", "CHATGPT", ObservationMode.DIRECT_API)
    c = claim("C-PR294-HEAD", "CHATGPT", ObservationMode.DIRECT_API, PR, e.evidence_id)
    s1 = create_state(parent_state_id=genesis.state_id, created_at=T0, state_id="STATE-001", claims=[c], evidence=[e])
    d = create_delta(parent=genesis, contributor_node="CHATGPT", created_at=T0, resulting_state=s1, delta_id="DELTA-001", claims_added=[c], evidence_added=[e])
    rebuilt = apply_delta(genesis, d)
    assert rebuilt.state_digest == s1.state_digest
    assert rebuilt.state_id == s1.state_id
    assert d.integrity_digest == digest(d.canonical_payload())


def test_original_chatgpt_gemini_grok_chatgpt_relay():
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    e1 = evidence("E1", "CHATGPT", ObservationMode.DIRECT_API)
    c1 = claim("C1", "CHATGPT", ObservationMode.DIRECT_API, PR, "E1")
    s1 = create_state(parent_state_id=s.state_id, created_at=T0, state_id="STATE-001", claims=[c1], evidence=[e1])
    d1 = create_delta(parent=s, contributor_node="CHATGPT", created_at=T0, resulting_state=s1, claims_added=[c1], evidence_added=[e1], delta_id="DELTA-001")
    s1 = apply_delta(s, d1)

    inherited = c1.model_copy(update={"observation_mode": ObservationMode.INHERITED_PACKET, "epistemic_class": EpistemicClass.REPORTED_FACT})
    e2 = evidence("E2", "GEMINI", ObservationMode.INHERITED_PACKET, locator="relay:CHATGPT→GEMINI")
    s2 = create_state(parent_state_id=s1.state_id, created_at=T0, state_id="STATE-002", claims=[inherited], evidence=[e2])
    d2 = create_delta(parent=s1, contributor_node="GEMINI", created_at=T0, resulting_state=s2, claims_updated=[inherited], evidence_added=[e2], delta_id="DELTA-002")
    s2 = apply_delta(s1, d2)
    assert next(c for c in s2.claims if c.claim_id == "C1").observation_mode == ObservationMode.INHERITED_PACKET

    e3 = evidence("E3", "GROK", ObservationMode.DIRECT_API)
    c3 = claim("C1", "GROK", ObservationMode.DIRECT_API, PR, "E3")
    s3 = create_state(parent_state_id=s2.state_id, created_at=T0, state_id="STATE-003", claims=[c3], evidence=[e3])
    d3 = create_delta(parent=s2, contributor_node="GROK", created_at=T0, resulting_state=s3, claims_updated=[c3], evidence_added=[e3], delta_id="DELTA-003")
    s3 = apply_delta(s2, d3)
    assert next(c for c in s3.claims if c.claim_id == "C1").observation_mode == ObservationMode.DIRECT_API

    e4 = evidence("E4", "CHATGPT", ObservationMode.DIRECT_API)
    c4 = claim("C1", "CHATGPT", ObservationMode.DIRECT_API, PR, "E4")
    s4 = create_state(parent_state_id=s3.state_id, created_at=T0, state_id="STATE-004", claims=[c4], evidence=[e4])
    d4 = create_delta(parent=s3, contributor_node="CHATGPT", created_at=T0, resulting_state=s4, claims_updated=[c4], evidence_added=[e4], delta_id="DELTA-004")
    s4 = apply_delta(s3, d4)
    packet = {"created_at": "2026-10-05T03:00:00+00:00", "state": s4.model_dump(mode="json")}
    assert validate_packet(packet)["status"] == "VALID"


def test_inference_cannot_claim_direct_observation():
    e = evidence("E-INF", "CHATGPT", ObservationMode.INFERRED)
    c = Claim(
        claim_id="C-INF", subject="x", predicate="y", object=True,
        source_authority="GitHub", observation_mode=ObservationMode.INFERRED,
        epistemic_class=EpistemicClass.OBSERVED_FACT, evidence_refs=[e.evidence_id],
    )
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000", claims=[c], evidence=[e])
    assert validate_packet({"state": s.model_dump(mode="json")})["status"] == "INVALID"


def test_temporal_supersession_and_invalid_intervals():
    old_e = evidence("E-OLD", "CHATGPT", ObservationMode.DIRECT_API)
    old = claim("C-OLD", "CHATGPT", ObservationMode.DIRECT_API, "old-sha", "E-OLD")
    new_e = evidence("E-NEW", "GROK", ObservationMode.DIRECT_API)
    new = claim("C-NEW", "GROK", ObservationMode.DIRECT_API, "new-sha", "E-NEW").model_copy(
        update={"supersedes": ["C-OLD"], "valid_from": T0}
    )
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000", claims=[old, new], evidence=[old_e, new_e])
    assert validate_packet({"state": s.model_dump(mode="json")})["status"] == "VALID"
    bad = new.model_copy(update={"claim_id": "C-BAD", "valid_from": T0, "valid_until": datetime(2026, 10, 4, tzinfo=timezone.utc)})
    sb = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000", claims=[bad], evidence=[new_e])
    assert validate_packet({"state": sb.model_dump(mode="json")})["status"] == "INVALID"


def test_future_timestamp_and_malformed_root_are_rejected():
    e = evidence("E-FUTURE", "CHATGPT", ObservationMode.DIRECT_API)
    c = claim("C-FUTURE", "CHATGPT", ObservationMode.DIRECT_API, PR, "E-FUTURE").model_copy(
        update={"observed_at": datetime(2030, 1, 1, tzinfo=timezone.utc)}
    )
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000", claims=[c], evidence=[e])
    assert validate_packet({"created_at": "2026-10-05T03:00:00+00:00", "state": s.model_dump(mode="json")})["status"] == "INVALID"
    tampered = s.model_copy(update={"state_digest": "sha256:tampered"})
    assert validate_packet({"state": tampered.model_dump(mode="json")})["status"] == "INVALID"


def test_missing_evidence_refs_are_rejected():
    c = claim("C-MISSING", "CHATGPT", ObservationMode.DIRECT_API, PR, "NOPE")
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000", claims=[c])
    assert validate_packet({"state": s.model_dump(mode="json")})["status"] == "INVALID"


def test_delta_tampering_and_wrong_parent_are_rejected():
    genesis = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    s1 = create_state(parent_state_id=genesis.state_id, created_at=T0, state_id="STATE-001")
    d = create_delta(parent=genesis, contributor_node="GROK", created_at=T0, resulting_state=s1, delta_id="DELTA-T")
    tampered = d.model_copy(update={"unknowns_added": ["tampered"]})
    try:
        apply_delta(genesis, tampered)
        assert False, "tampered delta must be rejected"
    except ValueError as exc:
        assert "integrity" in str(exc)
    wrong_parent = d.model_copy(update={"parent_state_id": "STATE-X"})
    try:
        apply_delta(genesis, wrong_parent)
        assert False, "wrong parent must be rejected"
    except ValueError as exc:
        assert "parent" in str(exc)


def test_long_chain_preserves_lineage_and_provenance():
    nodes = [
        ("CHATGPT", ObservationMode.DIRECT_API), ("GEMINI", ObservationMode.INHERITED_PACKET),
        ("GROK", ObservationMode.DIRECT_API), ("CLAUDE", ObservationMode.INHERITED_STATE),
        ("LOCAL", ObservationMode.INHERITED_PACKET), ("CHATGPT", ObservationMode.DIRECT_API),
        ("GEMINI", ObservationMode.INHERITED_PACKET), ("GROK", ObservationMode.DIRECT_API),
    ]
    state = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    lineage = [state.state_id]
    for i, (node, mode) in enumerate(nodes, 1):
        eid = f"E-LONG-{i}"
        e = evidence(eid, node, mode, locator=f"relay:{i}")
        ec = EpistemicClass.OBSERVED_FACT if mode == ObservationMode.DIRECT_API else EpistemicClass.REPORTED_FACT
        c = claim("C-LONG", node, mode, PR, eid).model_copy(update={"epistemic_class": ec})
        next_state = create_state(parent_state_id=state.state_id, created_at=T0, state_id=f"STATE-{i:03d}", claims=[c], evidence=[e])
        delta = create_delta(parent=state, contributor_node=node, created_at=T0, resulting_state=next_state,
                             delta_id=f"DELTA-{i:03d}", claims_updated=[c], evidence_added=[e])
        state = apply_delta(state, delta)
        lineage.append(state.state_id)
    assert lineage == ["STATE-000"] + [f"STATE-{i:03d}" for i in range(1, 9)]
    final = next(c for c in state.claims if c.claim_id == "C-LONG")
    assert final.observation_mode == ObservationMode.DIRECT_API
    assert final.evidence_refs == ["E-LONG-8"]


from alxai.reconcile import Reconciliation, reconcile_states
from alxai.protocol import Source


def branch_state(base, sid, claim_items=(), evidence_items=(), sources=()):
    return create_state(
        parent_state_id=base.state_id, created_at=T0, state_id=sid,
        claims=list(claim_items), evidence=list(evidence_items), source_registry=list(sources),
    )


def test_reconcile_non_overlapping_branches_and_commutative_root():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    ea = evidence("E-A", "CHATGPT", ObservationMode.DIRECT_API, locator="a")
    eb = evidence("E-B", "GROK", ObservationMode.DIRECT_API, locator="b")
    ca = Claim(claim_id="C-A", subject="a", predicate="status", object="ready",
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-A"])
    cb = Claim(claim_id="C-B", subject="b", predicate="status", object="ready",
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-B"])
    left = branch_state(base, "STATE-L", [ca], [ea])
    right = branch_state(base, "STATE-R", [cb], [eb])
    merged1, rec1 = reconcile_states(base, left, right, reconciliation_id="R-001", created_at=T0)
    merged2, rec2 = reconcile_states(base, right, left, reconciliation_id="R-001", created_at=T0)
    assert rec1.status == rec2.status == "MERGED"
    assert merged1.state_digest == merged2.state_digest
    assert {c.claim_id for c in merged1.claims} == {"C-A", "C-B"}


def test_reconcile_same_value_becomes_corroboration():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    ea = evidence("E-A", "CHATGPT", ObservationMode.DIRECT_API, locator="a")
    eb = evidence("E-B", "GROK", ObservationMode.DIRECT_API, locator="b")
    ca = Claim(claim_id="C-A", subject="repo", predicate="head", object=PR,
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-A"])
    cb = ca.model_copy(update={"claim_id": "C-B", "evidence_refs": ["E-B"], "observed_at": datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc)})
    left = branch_state(base, "STATE-L", [ca], [ea])
    right = branch_state(base, "STATE-R", [cb], [eb])
    merged, rec = reconcile_states(base, left, right, reconciliation_id="R-CORROBORATE", created_at=T0)
    assert rec.status == "MERGED"
    assert rec.corroborated_claim_ids == ["C-B"]
    assert next(c for c in merged.claims if c.claim_id == "C-A").status == "SUPERSEDED"
    assert next(c for c in merged.claims if c.claim_id == "C-B").evidence_refs == ["E-A", "E-B"]


def test_reconcile_contradictory_direct_observations_requires_adjudication():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    ea = evidence("E-A", "CHATGPT", ObservationMode.DIRECT_API, locator="a")
    eb = evidence("E-B", "GROK", ObservationMode.DIRECT_API, locator="b")
    ca = Claim(claim_id="C-A", subject="repo", predicate="head", object="sha-A",
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-A"])
    cb = ca.model_copy(update={"claim_id": "C-B", "object": "sha-B", "evidence_refs": ["E-B"]})
    left = branch_state(base, "STATE-L", [ca], [ea])
    right = branch_state(base, "STATE-R", [cb], [eb])
    merged, rec = reconcile_states(base, left, right, reconciliation_id="R-CONFLICT", created_at=T0)
    assert rec.status == "ADJUDICATION_REQUIRED"
    assert set(rec.conflict_claim_ids) == {"C-A", "C-B"}
    assert all(c.status == "CONFLICTED" for c in merged.claims)
    assert merged.conflicts


def test_reconcile_authoritative_source_wins_only_with_declared_scope():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    src = Source(source_id="github", domain="GitHub", authority_scope=["head"], access_status="AVAILABLE")
    ea = evidence("E-A", "LOCAL", ObservationMode.DIRECT_FILE, locator="local")
    eb = evidence("E-B", "GROK", ObservationMode.DIRECT_API, locator="github")
    ca = Claim(claim_id="C-AUTH", subject="repo", predicate="head", object="authoritative-sha",
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-A"])
    cb = ca.model_copy(update={"claim_id": "C-LOCAL", "object": "local-sha", "source_authority": "LOCAL", "evidence_refs": ["E-B"]})
    left = branch_state(base, "STATE-L", [ca], [ea], [src])
    right = branch_state(base, "STATE-R", [cb], [eb])
    merged, rec = reconcile_states(base, left, right, reconciliation_id="R-AUTH", created_at=T0)
    assert rec.status == "MERGED"
    assert next(c for c in merged.claims if c.claim_id == "C-AUTH").status == "ACTIVE"
    assert next(c for c in merged.claims if c.claim_id == "C-LOCAL").status == "SUPERSEDED"


def test_reconcile_newer_direct_observation_supersedes_older_when_no_authority():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    old_t = T0
    new_t = datetime(2026, 10, 5, 5, 0, tzinfo=timezone.utc)
    ea = evidence("E-A", "CHATGPT", ObservationMode.DIRECT_API, locator="old")
    eb = evidence("E-B", "GROK", ObservationMode.DIRECT_API, locator="new")
    ca = Claim(claim_id="C-OLD", subject="repo", predicate="state", object="old",
               source_authority="LOCAL", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=old_t, evidence_refs=["E-A"])
    cb = ca.model_copy(update={"claim_id": "C-NEW", "object": "new", "observed_at": new_t, "evidence_refs": ["E-B"]})
    merged, rec = reconcile_states(base, branch_state(base, "STATE-L", [ca], [ea]), branch_state(base, "STATE-R", [cb], [eb]),
                                   reconciliation_id="R-TIME", created_at=T0)
    assert rec.status == "MERGED"
    assert "C-OLD" in rec.superseded_claim_ids
    assert next(c for c in merged.claims if c.claim_id == "C-NEW").status == "ACTIVE"


from alxai.reconcile import Adjudication, apply_adjudication


def test_adjudication_requires_explicit_human_certificate_and_preserves_history():
    base = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    ea = evidence("E-AJ-A", "CHATGPT", ObservationMode.DIRECT_API, locator="a")
    eb = evidence("E-AJ-B", "GROK", ObservationMode.DIRECT_API, locator="b")
    ca = Claim(claim_id="C-AJ-A", subject="repo", predicate="head", object="sha-A",
               source_authority="GitHub", observation_mode=ObservationMode.DIRECT_API,
               epistemic_class=EpistemicClass.OBSERVED_FACT, observed_at=T0, evidence_refs=["E-AJ-A"])
    cb = ca.model_copy(update={"claim_id": "C-AJ-B", "object": "sha-B", "evidence_refs": ["E-AJ-B"]})
    conflicted, rec = reconcile_states(
        base, branch_state(base, "STATE-AJ-L", [ca], [ea]), branch_state(base, "STATE-AJ-R", [cb], [eb]),
        reconciliation_id="R-AJ", created_at=T0,
    )
    assert rec.status == "ADJUDICATION_REQUIRED"

    adjudication = Adjudication(
        adjudication_id="ADJ-001", reconciliation_id="R-AJ", decision_maker="HUMAN:AUTH-01",
        scope="repo.head", selected_claim_id="C-AJ-B", rejected_claim_ids=["C-AJ-A"],
        evidence_refs=["E-AJ-B"], authorized_actions=["supersede:C-AJ-A"],
        decided_at=datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc),
        rationale="Human authority selected the verified branch result.",
    ).with_certificate()
    resolved = apply_adjudication(conflicted, adjudication)
    assert resolved.state_id == "STATE-ADJ-ADJ-001"
    assert next(c for c in resolved.claims if c.claim_id == "C-AJ-B").status == "ACTIVE"
    assert next(c for c in resolved.claims if c.claim_id == "C-AJ-A").status == "SUPERSEDED"
    assert any(x.startswith("ADJUDICATED:ADJ-001") for x in resolved.conflicts)

    tampered = adjudication.model_copy(update={"rationale": "changed"})
    try:
        apply_adjudication(conflicted, tampered)
        assert False, "tampered adjudication certificate must be rejected"
    except ValueError as exc:
        assert "certificate" in str(exc)

# authority-boundary conformance
