# WEAVER-MVP1 — Durable Governed Operator Loop

**Starting SHA:** `e7247ac7033d54411e7f41e5cde08919ab93c9ec` (W5 / origin/main)  
**Scope:** Minimum viable Project → Knowledge → Weaver → Patch → PassSpec → PatchApproval → K15 (precheck) path.

## Proven

- Project ownership isolation  
- Knowledge → Weaver context without authorizing execution  
- Pipeline objective → analysis → plan → changeset → patch  
- Line-local unified diffs (no redesign-region hunks)  
- PassSpec + PatchApproval hash binding  
- Hash mismatch blocks  
- K15-only mutation route (no direct K3 from project layer)  
- Precheck without repository mutation  
- verification NOT_RUN without execution  
- embeddings NOT_AVAILABLE  

## NOT_RUN

- Browser UI automation  
- Live `run_k3=true` mutation against real branch  

## Files

- `weaver/patch.py` — minimal line-local diffs  
- `solspire/project_execution.py` — auth state + K15 wrapper  
- `solspire/weaver_bridge.py` — project helpers  
- `solspire/console_router.py` — owner-guarded execution routes  
- `tests/test_weaver_mvp1.py`  

## Publication

Single commit pushed to `origin/main` under explicit MVP1 authorization.
