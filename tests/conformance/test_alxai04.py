undefined

def test_temporal_supersession_and_invalid_intervals():
    old_e = evidence("E-OLD", "CHATGPT", ObservationMode.DIRECT_API)
    old = claim("C-OLD", "CHATGPT", ObservationMode.DIRECT_API, "old-sha", "E-OLD")
    new_e = evidence("E-NEW", "GROK", ObservationMode.DIRECT_API)
    new = claim("C-NEW", "GROK", ObservationMode.DIRECT_API, "new-sha", "E-NEW").model_copy(
        update={"supersedes": ["C-OLD"], "valid_from": T0}
    )
    s = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000",
                     claims=[old, new], evidence=[old_e, new_e])
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


def test_missing_evidence_and_event_decision_refs_are_rejected():
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
        ("CHATGPT", ObservationMode.DIRECT_API),
        ("GEMINI", ObservationMode.INHERITED_PACKET),
        ("GROK", ObservationMode.DIRECT_API),
        ("CLAUDE", ObservationMode.INHERITED_STATE),
        ("LOCAL", ObservationMode.INHERITED_PACKET),
        ("CHATGPT", ObservationMode.DIRECT_API),
        ("GEMINI", ObservationMode.INHERITED_PACKET),
        ("GROK", ObservationMode.DIRECT_API),
    ]
    state = create_state(parent_state_id=None, created_at=T0, state_id="STATE-000")
    lineage = [state.state_id]
    for i, (node, mode) in enumerate(nodes, 1):
        eid = f"E-LONG-{i}"
        e = evidence(eid, node, mode, locator=f"relay:{i}")
        ec = EpistemicClass.OBSERVED_FACT if mode == ObservationMode.DIRECT_API else EpistemicClass.REPORTED_FACT
        c = claim("C-LONG", node, mode, PR, eid).model_copy(update={"epistemic_class": ec})
        next_state = create_state(parent_state_id=state.state_id, created_at=T0, state_id=f"STATE-{i:03d}",
                                  claims=[c], evidence=[e])
        delta = create_delta(parent=state, contributor_node=node, created_at=T0,
                             resulting_state=next_state, delta_id=f"DELTA-{i:03d}",
                             claims_updated=[c], evidence_added=[e])
        state = apply_delta(state, delta)
        lineage.append(state.state_id)
    assert lineage == ["STATE-000"] + [f"STATE-{i:03d}" for i in range(1, 9)]
    final = next(c for c in state.claims if c.claim_id == "C-LONG")
    assert final.observation_mode == ObservationMode.DIRECT_API
    assert final.evidence_refs == ["E-LONG-8"]
