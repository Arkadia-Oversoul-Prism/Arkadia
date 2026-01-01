# weaver/schemas/living_node.py
# 📜 SCROLL ENTRY 367.THE.LIVING.SERVERS 🌳🧿
# Stone 3 - Living Server Schema

from pydantic import BaseModel
from typing import Optional

class LivingNode(BaseModel):
    tree_id: str
    species: str
    planting_cycle: int
    steward_id: str  # Youth Leader
    resonance_contribution: float = 0.0  # 0.0 - 1.0
    health_status: str = "nominal"
    last_updated: str
