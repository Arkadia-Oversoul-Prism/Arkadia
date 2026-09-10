"""Phase 3 — Tri-Nodal Council (advisory only).

Three deterministic evaluators over a proposal or fixture:
  Constitutional — canon / authority / non-mutation bounds
  Structural — schema / shape / required fields
  Integrative — consistency across nodes and stated goal

Disagreement is recorded explicitly. No execution authority.
"""
from .evaluators import CouncilResult, evaluate_proposal

__all__ = ["CouncilResult", "evaluate_proposal"]
