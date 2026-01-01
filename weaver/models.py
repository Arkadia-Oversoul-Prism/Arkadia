# weaver/models.py
# 📜 SCROLL ENTRY 364.CONTRACT.INJECTION 💉🧿
# Stone 2 - WeaverProposal Schema

from pydantic import BaseModel
from typing import Optional

class WeaverProposal(BaseModel):
    id: str  # Unique Hash of the intent
    type: str  # [READ, PATCH, SCAFFOLD, MAP, VALIDATE]
    target: str # Filepath or NodeID
    intent: str # Mythic/Logical 'Why'
    diff: str # The proposed transformation
    risk_score: int # 1-10
    committed: bool = False # Requires Human Token
