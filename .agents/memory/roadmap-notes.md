---
name: Strategic Roadmap
description: Phase sequence rationale, Architecture Freeze v1.0 criteria, and CI enforcement milestone. Read before proposing new phases or reordering workstreams.
---

# Strategic Roadmap — Durable Notes

## Phase Sequence (dependency-ordered)

```
Phase 0: Secure the platform                ✅ complete
Phase 1: Stabilize the runtime              🚧 implementation ready
Phase 2: Canonicalize the domain            blocked on Phase 1
Phase 3: Unified Knowledge Layer            blocked on Phase 2
Phase 4: Experience Projection              blocked on Phase 3
Phase 5: Scale Without Compromise           blocked on Phase 4
```

**Why:** Each phase is a strict precondition for the next. Runtime durability before domain canonicalization; canonical types before knowledge interfaces; knowledge interfaces before experience projection.

## Architecture Freeze v1.0

Not a feature freeze. A freeze on foundational architectural decisions (layer map, dependency direction, kernel scope, domain model). After this point those evolve only via a new ADR.

All criteria are in `ROADMAP.md`. Estimated: after Phase 3 complete.

## CI Enforcement Milestone

Fitness tests are pure AST-based Python — no secrets, no network required. They wire to any CI provider as-is. This is the next step after Phase 5 infrastructure work. When wired, architectural governance shifts from "best practice" to "enforced practice."

## What NOT to Do

- Do not skip phases to reach visible experience features (Phase 4) before the runtime is stable (Phase 1).
- Do not treat ROADMAP.md as a backlog. It is strategic sequencing. Tactical work belongs in the Continuation Ledger.
- Do not add phases without documenting the dependency rationale.
