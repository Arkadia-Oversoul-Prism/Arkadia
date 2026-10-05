#!/usr/bin/env python3
"""Validate the historical Arkadia Oversoul Prism 12x12 registry.

This is a reconstruction validator, not an execution engine.
"""
from __future__ import annotations
import json
from pathlib import Path

REGISTRY = Path(__file__).parents[1] / "docs" / "architecture" / "oversoul_prism_12x12_registry.json"

EXPECTED_ROLES = {
    "A01": "Threshold Guardian",
    "A02": "Resonance Weaver",
    "A03": "Ignition Spark",
    "A04": "Harmonizing Stream",
    "A05": "Directive Alchemist",
    "A06": "Semantic Bridge",
    "A07": "Chronos Regulator",
    "A08": "Insight Architect",
    "A09": "Resource Steward",
    "A10": "Sovereign Manifestor",
    "A11": "Transmutation Engine",
    "A12": "Source Current Seeker",
}

def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    cells = data["cells"]
    assert data["dimensions"] == {"functions": 12, "layers": 12, "total_nodes": 144}
    assert len(cells) == 144
    ids = [c["node_id"] for c in cells]
    assert len(set(ids)) == 144
    assert set(data["function_axis"][i]["function_id"] for i in range(12)) == set(EXPECTED_ROLES)
    for cell in cells:
        assert cell["function_id"] in EXPECTED_ROLES
        assert cell["historical_role"] == EXPECTED_ROLES[cell["function_id"]]
        assert cell["layer_id"] in {f"L{i:02d}" for i in range(1, 13)}
        assert cell["layer_semantics"] == "UNKNOWN"
        assert cell["authority"] == "none"
        assert cell["execution_implemented"] is False
    print("OK: 12 functions × 12 layers = 144 historical registry cells")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
