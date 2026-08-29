# WEAVER-MVP1 — Durable Governed Operator Loop

**Base:** W5 / prior docs tip on main  
**Scope:** Project → Knowledge → Weaver → Patch → PassSpec → PatchApproval → K15 precheck

## Proven

- Project ownership isolation
- Knowledge does not authorize
- Line-local patch diffs (no redesign-region)
- PassSpec + PatchApproval hash binding
- Hash mismatch blocks
- K15-only mutation route (no direct K3 from project layer)
- Precheck without repository mutation
- verification NOT_RUN without execution
- embeddings NOT_AVAILABLE

## NOT_RUN

- Browser UI automation
- Live run_k3=true mutation

## Files

- weaver/patch.py
- solspire/project_execution.py
- solspire/weaver_bridge.py
- solspire/console_router.py
- tests/test_weaver_mvp1.py
