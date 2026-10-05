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

from .substrate import (
    BranchResult, StateDelta,
    assert_non_governing,
    reconcile_branches,
    replay_branch,
)


def _slice():
    return [NodeAddress(f"A{f:02d}", f"L{l:02d}") for f in range(1, 4) for l in range(1, 4)]


def test_9_cell_branch_replay_is_recursive_and_root_continuous():
    genesis = PrismState(
        claims={"probe.fact": "seed"},
        evidence_refs=("E-SEED",),
        unknowns=("probe.verification",),
    )
    branches = []
    for function_id in ("A01", "A02", "A03"):
        addresses = [NodeAddress(function_id, f"L{layer:02d}") for layer in range(1, 4)]
        branch = replay_branch(
            f"branch-{function_id}",
            addresses,
            genesis,
            claim_updates_by_node={
                addresses[-1].node_id: {"probe.fact": "same"},
            },
        )
        assert len(branch.deltas) == 3
        assert branch.deltas[0].base_root == genesis.state_root
        assert branch.deltas[1].base_root == branch.deltas[0].result_root
        assert branch.deltas[2].base_root == branch.deltas[1].result_root
        assert branch.root == branch.deltas[-1].result_root
        branches.append(branch)

    merged = reconcile_branches(branches)
    assert merged.claims["probe.fact"] == "same"
    assert merged.evidence_refs == ("E-SEED",)
    assert merged.unknowns == ("probe.verification",)
    assert len(merged.provenance) == 12
    assert merged.conflicts == ()
    assert_non_governing(merged)


def test_deliberate_branch_contradiction_is_preserved_not_resolved():
    genesis = PrismState(
        claims={"probe.fact": "seed"},
        evidence_refs=("E-SEED",),
        unknowns=("probe.verification",),
    )
    branches = []
    values = {"A01": "left", "A02": "right", "A03": "left"}
    for function_id in ("A01", "A02", "A03"):
        addresses = [NodeAddress(function_id, f"L{layer:02d}") for layer in range(1, 4)]
        branches.append(replay_branch(
            f"branch-{function_id}",
            addresses,
            genesis,
            claim_updates_by_node={
                addresses[-1].node_id: {"probe.fact": values[function_id]},
            },
        ))

    merged = reconcile_branches(branches)
    assert "probe.fact" not in merged.claims
    assert merged.conflicts == ("probe.fact",)
    assert "E-SEED" in merged.evidence_refs
    assert "probe.verification" in merged.unknowns
    assert_non_governing(merged)


def test_authority_smuggling_is_rejected_at_transformation_boundary():
    genesis = PrismState(claims={"probe.fact": "seed"})
    address = NodeAddress("A01", "L01")
    try:
        transform_node(genesis, address, claim_updates={"authorization_id": "AUTH-001"})
        assert False, "authority smuggling must fail closed"
    except ValueError as exc:
        assert "authority" in str(exc)


def test_reconciliation_does_not_create_authority_from_branch_content():
    genesis = PrismState(claims={"probe.fact": "seed"})
    safe = replay_branch(
        "safe",
        [NodeAddress("A01", "L01")],
        genesis,
        claim_updates_by_node={"A01-L01": {"probe.fact": "ok"}},
    )
    forged = BranchResult(
        branch_id="forged",
        state=PrismState(
            claims={"probe.fact": "ok"},
            provenance=("A02-L01",),
        ),
        deltas=(),
    )
    merged = reconcile_branches([safe, forged])
    assert_non_governing(merged)
    assert "authorization_id" not in merged.as_dict()
    assert "authority" not in merged.as_dict()


def test_forged_delta_cannot_smuggle_authority():
    genesis = PrismState(claims={"probe.fact": "seed"})
    forged = StateDelta(
        base_root=genesis.state_root,
        result_root=genesis.state_root,
        node_id="A01-L01",
        changes={"authority": "human", "authorization_id": "AUTH-001"},
    )
    try:
        validate_delta(forged, genesis)
        assert False, "forged authority delta must fail closed"
    except ValueError as exc:
        assert "authority" in str(exc)
