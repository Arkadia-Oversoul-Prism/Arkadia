# Arkadia Engineering Worker Contract

**Contract ID:** `ARKADIA-WORKER-CONTRACT-v1`  
**Move:** M09  
**Schema:** `docs/control-plane/worker.contract.schema.json`  
**Instance:** `docs/control-plane/worker.contract.json`  
**Parent:** AEAS-v0.1.1 (frozen) · Engineering Runner

## Authority chain

```
Architect
  → Trajectory (direction)
  → Scheduler (cadence)
  → Engineering Lab / Runner (load → route → dispatch)
  → Worker (bounded session)
  → Agent / ExecutionAdapter (replaceable)
  → Repository (mutation evidence)
  → Evidence (durable)
  → Human Review (accept / revision)
```

The worker is **subordinate** to the approved trajectory and selected move scope.  
It does **not** redefine AEAS, trajectory authority, K15/K3, or governance.

## Lifecycle phases

| Phase | Meaning |
|-------|---------|
| WAKE | Session starts (manual or scheduled); no move chosen yet |
| LOAD | Trajectory + evidence + HEAD SHA |
| VALIDATE | Structure, authorization surface, concurrency |
| ROUTE | Weaver selects first legal move (or NO_LEGAL_MOVE) |
| PLAN | Bounded plan from move spec |
| EXECUTE | Adapter runs only if not dry-run and in scope |
| CHECKPOINT | Durable intermediate state when required |
| VERIFY | Tests / acceptance checks |
| REPORT | Machine + human report |
| TERMINATE | Stop at review; no next-move auto-advance |

## Hard prohibitions

- No autonomous merge  
- No autonomous production deploy  
- No trajectory rewrite by the worker  
- No inventing moves or expanding scope  
- No second identity / memory / Knowledge OS / execution architecture  

## Resumability

Sessions may resume from CHECKPOINTED / REVISION_REQUIRED using repository evidence, not chat memory.

## Implementation mapping (existing)

| Contract element | Repository surface |
|------------------|-------------------|
| Router | `weaver/engineering_router.py` |
| Worker session | `weaver/engineering_worker.py` |
| Adapter | `weaver/execution_adapter.py` (`NullExecutionAdapter` default) |
| Scheduler | `.github/workflows/arkadia-engineering-scheduler.yml` |
| Evidence root | `docs/control-plane/evidence/` |

M09 **defines** the contract. It does not activate unbounded autonomous execution.
