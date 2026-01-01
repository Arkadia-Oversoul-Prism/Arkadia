"""
Weaver Bootstrap — Canonical Runtime Reinitialization
Single source of truth for starting Weaver across any agent environment.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weaver.recursive import RecursiveEngine

def load_sanctum_status() -> dict:
    """Load status from sanctum/status.json"""
    import json
    status_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sanctum", "status.json")
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            return json.load(f)
    return {"cycle": 0, "phase": "Foundation", "governance_mode": "manual"}

def initialize_weaver():
    """Initialize Weaver engine with governance constraints."""
    status = load_sanctum_status()
    
    cycle = status.get("cycle", 0)
    governance_mode = status.get("governance_mode", "manual")
    autonomy_enabled = status.get("autonomy_enabled", False)
    
    engine = RecursiveEngine(
        initial_task=f"Cycle {cycle} Reinitialization",
        enabled=True
    )
    
    engine.cycle = cycle
    engine.mode = governance_mode
    engine.governance_mode = governance_mode
    engine.autonomy_enabled = autonomy_enabled
    engine.llm_provider = status.get("llm_provider", "stub")
    
    # ⚖️ THE SOVEREIGN GATE (Stone 2)
    def verified_write(proposal_id: str, token: str, content: str, path: str):
        if status.get("governance_mode") == "sovereign-execution":
            if token != os.environ.get("VERIFIED_COMMIT_TOKEN"):
                raise PermissionError("Sovereign Gate Locked: Invalid Commit Token")
        with open(path, "w") as f:
            f.write(content)
            
    engine.verified_write = verified_write
    
    validation = engine.validate()
    all_ok = all(v != "missing" for v in validation.values())
    
    if not all_ok:
        missing = [k for k, v in validation.items() if v == "missing"]
        raise AssertionError(f"Weaver not ready — missing modules: {missing}")
    
    return engine

if __name__ == "__main__":
    engine = initialize_weaver()
    print("🌀 Weaver initialized")
    print(f"Cycle: {engine.cycle}")
    print(f"Mode: {engine.mode}")
    print(f"Governance: {engine.governance_mode}")
    print(f"LLM Provider: {engine.llm_provider}")
    print(f"Autonomy: {engine.autonomy_enabled}")
