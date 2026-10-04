#!/usr/bin/env python3
"""Bounded 3x3 Oversoul Prism topology validator.

This harness validates historical topology only. It does not call an LLM,
perform external side effects, create WorkEvents, or grant authority.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "topology.json").read_text(encoding="utf-8"))

def main() -> int:
    assert DATA["status"] == "research_prototype"
    assert DATA["authority"] == "none"
    assert DATA["production"] is False
    assert DATA["execution"]["llm"] is False
    assert DATA["execution"]["external_side_effects"] is False
    assert len(DATA["nodes"]) == 9
    assert len(DATA["edges"]) == 6

    node_ids = {n["node_id"] for n in DATA["nodes"]}
    for source, target in DATA["edges"]:
        assert source in node_ids and target in node_ids
        sf, sl = source.split("-")
        tf, tl = target.split("-")
        assert sf == tf, "Cross-function edge introduced into bounded slice"
        assert int(tl[1:]) == int(sl[1:]) + 1

    print("OK: bounded 3x3 topology = 9 nodes / 6 sequential intra-function edges")
    print("OK: no authority, LLM calls, external side effects, or production route")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
