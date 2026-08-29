# WEAVER-W1 — Workbench / Observability Consolidation

**Expose what we have already built before building more of it.**

## Modules

- `weaver/workbench_view.py` — observatory + read-only pipeline aggregation
- `weaver/workbench_app.py` — CLI entry: `python -m weaver.workbench_app observatory|analyze "..."`

## Default

Read-only. No PassSpec inference. Mutation path remains **K3 ONLY** via K15 when separately authorized.
