import json
import os

STATUS_PATH = os.path.join(os.path.dirname(__file__), "status.json")

def load_status() -> dict:
    """Load sanctum status from JSON file."""
    if not os.path.exists(STATUS_PATH):
        return {
            "cycle": 0,
            "phase": "Foundation",
            "governance_mode": "manual",
            "autonomy_enabled": False,
            "llm_provider": "stub",
            "engine_ready": False
        }
    with open(STATUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_status(status: dict) -> None:
    """Save sanctum status to JSON file."""
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

__all__ = ["load_status", "save_status"]
