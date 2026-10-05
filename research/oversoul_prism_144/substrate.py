from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "architecture" / "oversoul_prism_12x12_registry.json"

def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()

def node_id(function_id: str, layer_id: str) -> str:
    functions = {f"A{i:02d}" for i in range(1, 13)}
    layers = {f"L{i:02d}" for i in range(1, 13)}
    if function_id not in functions or layer_id not in layers:
        raise ValueError(f"invalid Prism coordinate: {function_id}-{layer_id}")
    return f"{function_id}-{layer_id}"

def load_registry() -> Mapping[str, Any]:
    with REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def registry_index() -> dict[str, Mapping[str, Any]]:
    return {cell["node_id"]: cell for cell in load_registry().get("cells", [])}

@dataclass(frozen=True)
class NodeAddress:
    function_id: str
    layer_id: str

    @property
    def node_id(self) -> str:
        return node_id(self.function_id, self.layer_id)

    def validate(self) -> None:
        cell = registry_index().get(self.node_id)
        if cell is None:
            raise ValueError(f"node is not in historical registry: {self.node_id}")
        if cell.get("authority") != "none":
            raise ValueError(f"historical node unexpectedly carries authority: {self.node_id}")
        if cell.get("execution_implemented") is not False:
            raise ValueError(f"historical node unexpectedly executable: {self.node_id}")

@dataclass(frozen=True)
class PrismState:
    claims: Mapping[str, Any]
    evidence_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "claims": dict(self.claims),
            "evidence_refs": list(self.evidence_refs),
            "unknowns": list(self.unknowns),
            "provenance": list(self.provenance),
            "conflicts": list(self.conflicts),
        }

    @property
    def state_root(self) -> str:
        return digest(self.as_dict())

@dataclass(frozen=True)
class StateDelta:
    base_root: str
    result_root: str
    node_id: str
    changes: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.1.0",
            "base_root": self.base_root,
            "result_root": self.result_root,
            "node_id": self.node_id,
            "changes": dict(self.changes),
            "authority": "none",
        }

def apply_node(state: PrismState, address: NodeAddress) -> tuple[PrismState, StateDelta]:
    address.validate()
    before = state.as_dict()
    after = PrismState(
        claims=dict(state.claims),
        evidence_refs=tuple(state.evidence_refs),
        unknowns=tuple(state.unknowns),
        provenance=(*state.provenance, address.node_id),
    )
    delta = StateDelta(
        base_root=state.state_root,
        result_root=after.state_root,
        node_id=address.node_id,
        changes={"provenance": {"before": before["provenance"], "after": list(after.provenance)}},
    )
    return after, delta

@dataclass(frozen=True)
class BranchResult:
    branch_id: str
    state: PrismState
    deltas: tuple[StateDelta, ...]

    @property
    def root(self) -> str:
        return self.state.state_root


FORBIDDEN_AUTHORITY_KEYS = frozenset({
    "authority", "authorization_id", "authorization_scope",
    "human_authority", "approval", "production_acceptance", "work_event",
})


def _reject_authority_fields(changes: Mapping[str, Any]) -> None:
    leaked = sorted(set(changes) & FORBIDDEN_AUTHORITY_KEYS)
    if leaked:
        raise ValueError("Prism research transformation cannot create authority fields: " + ", ".join(leaked))


def transform_node(state: PrismState, address: NodeAddress, *,
                   claim_updates: Mapping[str, Any] | None = None,
                   evidence_refs_add: tuple[str, ...] = (),
                   unknowns_add: tuple[str, ...] = ()) -> tuple[PrismState, StateDelta]:
    address.validate()
    updates = dict(claim_updates or {})
    _reject_authority_fields(updates)
    claims = dict(state.claims)
    claims.update(updates)
    after = PrismState(
        claims=claims,
        evidence_refs=tuple(dict.fromkeys((*state.evidence_refs, *evidence_refs_add))),
        unknowns=tuple(dict.fromkeys((*state.unknowns, *unknowns_add))),
        provenance=(*state.provenance, address.node_id),
        conflicts=state.conflicts,
    )
    delta = StateDelta(
        base_root=state.state_root, result_root=after.state_root, node_id=address.node_id,
        changes={"claims": updates, "evidence_refs_add": list(evidence_refs_add),
                 "unknowns_add": list(unknowns_add),
                 "provenance": {"before": list(state.provenance), "after": list(after.provenance)}},
    )
    return after, delta


def replay_branch(branch_id: str, addresses: list[NodeAddress], state: PrismState, *,
                  claim_updates_by_node: Mapping[str, Mapping[str, Any]] | None = None) -> BranchResult:
    if not branch_id:
        raise ValueError("branch_id is required")
    current = state
    deltas = []
    update_map = claim_updates_by_node or {}
    for address in addresses:
        current, delta = transform_node(current, address, claim_updates=update_map.get(address.node_id))
        deltas.append(delta)
    return BranchResult(branch_id=branch_id, state=current, deltas=tuple(deltas))


def reconcile_branches(branches: list[BranchResult]) -> PrismState:
    if not branches:
        raise ValueError("at least one branch is required")
    claim_values: dict[str, list[Any]] = {}
    for branch in branches:
        for key, value in branch.state.claims.items():
            claim_values.setdefault(key, []).append(value)
    merged_claims: dict[str, Any] = {}
    conflicts: list[str] = []
    for key in sorted(claim_values):
        values = claim_values[key]
        canonical = {json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for v in values}
        if len(canonical) == 1:
            merged_claims[key] = values[0]
        else:
            conflicts.append(key)
    provenance = []
    for branch in branches:
        provenance.append(f"branch:{branch.branch_id}@{branch.root}")
        provenance.extend(branch.state.provenance)
    return PrismState(
        claims=merged_claims,
        evidence_refs=tuple(sorted({ref for b in branches for ref in b.state.evidence_refs})),
        unknowns=tuple(sorted({u for b in branches for u in b.state.unknowns})),
        provenance=tuple(provenance), conflicts=tuple(conflicts),
    )


def assert_non_governing(state: PrismState) -> None:
    payload = state.as_dict()
    if payload.get("authority") not in (None, "none"):
        raise ValueError("research state acquired authority")
    if any(key in payload for key in FORBIDDEN_AUTHORITY_KEYS):
        raise ValueError("research state acquired a forbidden authority field")

def validate_delta(delta: StateDelta, state: PrismState) -> None:
    if delta.base_root != state.state_root:
        raise ValueError("delta base_root does not match supplied state")
    if delta.node_id not in registry_index():
        raise ValueError("delta references an unknown historical node")
    if delta.as_dict()["authority"] != "none":
        raise ValueError("research delta cannot carry authority")

def replay(addresses: list[NodeAddress], state: PrismState) -> tuple[PrismState, tuple[StateDelta, ...]]:
    current = state
    deltas: list[StateDelta] = []
    for address in addresses:
        current, delta = apply_node(current, address)
        deltas.append(delta)
    return current, tuple(deltas)
