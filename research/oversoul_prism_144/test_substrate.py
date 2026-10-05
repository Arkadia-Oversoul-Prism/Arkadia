from .substrate import NodeAddress, PrismState, replay, validate_delta

def test_all_144_registry_addresses_validate():
    addresses = [NodeAddress(f"A{f:02d}", f"L{l:02d}") for f in range(1, 13) for l in range(1, 13)]
    for address in addresses:
        address.validate()

def test_state_root_is_deterministic():
    state = PrismState(claims={"claim": "sample"}, evidence_refs=("E-001",), unknowns=("verification",))
    assert state.state_root == state.state_root

def test_bounded_3x3_replay_preserves_unknowns_and_evidence():
    state = PrismState(claims={"claim": "sample"}, evidence_refs=("E-001",), unknowns=("verification", "completion"))
    addresses = [NodeAddress(f"A{f:02d}", f"L{l:02d}") for f in range(1, 4) for l in range(1, 4)]
    result, deltas = replay(addresses, state)
    assert len(deltas) == 9
    assert result.evidence_refs == ("E-001",)
    assert result.unknowns == ("verification", "completion")
    assert result.provenance == tuple(d.node_id for d in deltas)
    assert deltas[0].base_root == state.state_root

def test_delta_chain_is_strict():
    state = PrismState(claims={"claim": "sample"})
    result, deltas = replay([NodeAddress("A01", "L01"), NodeAddress("A01", "L02")], state)
    validate_delta(deltas[0], state)
    assert deltas[1].base_root == deltas[0].result_root
    assert result.state_root == deltas[-1].result_root
