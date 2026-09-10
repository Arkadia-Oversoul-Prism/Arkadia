"""Phase 4 — Evolution Planner (proposal generation only).

Produces schema-bound Evolution Proposals from Lab evidence.
Does not execute, branch, PR, merge, or deploy.
"""
from .planner import EvolutionProposal, plan_from_patterns, validate_proposal

__all__ = ["EvolutionProposal", "plan_from_patterns", "validate_proposal"]
