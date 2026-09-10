"""Phase 10 — Governed binding from Phase 9 APPROVE decisions to Phase 5 dry-run.

APPROVE selects a candidate. Binding produces a dry-run execution package only.
Never merges, deploys, or auto-executes without injected operator callables.
"""

from .binder import bind_approved_decision, BindingResult

__all__ = ["bind_approved_decision", "BindingResult"]
