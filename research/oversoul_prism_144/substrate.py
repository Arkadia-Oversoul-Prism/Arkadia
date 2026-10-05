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

    def as_dict(self) -> dict[str, Any]:
        return {
            "claims": dict(self.claims),
            "evidence_refs": list(self.evidence_refs),
            "unknowns": list(self.unknowns),
            "provenance": list(self.provenance),
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
