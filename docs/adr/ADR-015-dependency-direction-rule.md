# ADR-015: Dependency Direction Rule

**Status:** Accepted  
**Date:** ARK Y1 · D116 (2026-07-24)  
**Decider:** Flamekeeper + Principal Engineer  
**Supersedes:** None  
**References:** ADR-014 (Phase 1), `docs/phase1/ARCHITECTURE_MAP.md`

---

## Context

Large software systems collapse into unmaintainable monoliths through a single repeating failure: layers that were meant to be isolated begin importing from each other in the wrong direction. Once a stable layer depends on an unstable one, every change to the unstable layer becomes a risk to the stable one. This spreads across the codebase until everything depends on everything and nothing can be changed safely.

The Phase 1 dependency analysis identified five existing violations of this type in Arkadia's kernel layer (`kernel/agents.py → api.arkadia_engine`, `kernel/planner.py → api.key_manager`, etc.). These did not arise from negligence — they arose from the absence of a written rule.

This ADR establishes that rule as a constitutional constraint, enforceable in CI.

---

## Decision

**Dependencies may point only toward more stable architectural layers.**

A more stable layer never imports from a less stable layer. Stability is defined by layer position in the canonical map.

---

## Layer Stability Order

From most stable (lowest position — depended upon by others) to least stable (highest position — depends on others):

```
Layer 5 — Constitution         (ADRs, laws, governance)
Layer 4 — Storage Substrate    (SQLite, Markdown vault)
Layer 3 — Identity Layer       (auth, nodes, sovereign)
Layer 3 — Provider Layer       (AI adapters — orthogonal to domain)
Layer 3 — Knowledge Layer      (vault, embeddings, graph, retrieval)
Layer 2 — Runtime Core         (kernel, planner, workers, tools)
Layer 1 — API Surface          (FastAPI routes, middleware)
Layer 0 — Presentation         (frontend, bots, mobile)
```

Layers 3 (Identity, Provider, Knowledge) are orthogonal — they do not depend on each other. They may be depended upon by Layers 2, 1, and 0.

---

## The Rule, Precisely

```
Permitted:   Layer N → Layer N-1 (or lower)
             i.e., less stable depends on more stable

Forbidden:   Layer N → Layer N+1 (or higher)
             i.e., more stable depends on less stable

Forbidden:   Layer 3 (Knowledge) → Layer 3 (Provider)  [or vice versa]
Layer 3 sub-layers are orthogonal — no cross-dependencies.
```

### Concrete examples

| Import | Permitted? | Reason |
|---|---|---|
| `api/main.py` → `kernel/execution.py` | ✅ | API Surface → Runtime Core |
| `kernel/planner.py` → `providers/gemini.py` | ✅ | Runtime Core → Provider Layer |
| `kernel/memory.py` → `knowledge/context_engine.py` | ✅ | Runtime Core → Knowledge Layer |
| `kernel/agents.py` → `api/arkadia_engine.py` | ❌ | Runtime Core → API Surface (inversion) |
| `kernel/planner.py` → `api/key_manager.py` | ❌ | Runtime Core → API Surface (inversion) |
| `kernel/jobs.py` → `api/firebase_store.py` | ❌ | Runtime Core → API Surface (inversion) |
| `knowledge/context_engine.py` → `providers/gemini.py` | ❌ | Knowledge → Provider (orthogonal violation) |
| `providers/gemini.py` → `kernel/execution.py` | ❌ | Provider → Runtime Core (inversion) |
| `web/public_prism` → `kernel/` (direct import) | ❌ | Presentation → Runtime Core (skip-layer) |

---

## Enforcement

This rule is enforced automatically in CI by `tests/architecture/test_layer_boundaries.py`.

The test suite:
1. Parses all Python `import` and `from ... import` statements in each layer using the `ast` module
2. Maps each file to its layer using the canonical directory-to-layer table
3. Asserts that no import points from a lower layer to a higher layer
4. Produces a human-readable violation report when it fails

The CI check runs on every pull request. A PR that introduces a new layer violation cannot merge.

See `tests/architecture/test_layer_boundaries.py` for the implementation.

---

## Exceptions

Exceptions to this rule are permitted only when:
1. A new ADR explicitly grants the exception with a documented rationale
2. The exception is temporary (migration period, maximum one sprint)
3. The exception is recorded in the fitness test as an `ALLOWED_VIOLATIONS` entry with an expiry date

The current five violations identified in Phase 1 analysis are **temporary exceptions** with a Phase 1 deadline. They are listed in `test_layer_boundaries.py` as `ALLOWED_VIOLATIONS` until remediated.

---

## How to Add a New Layer

When Arkadia grows new subsystems (Oversoul Prism, NovaNet, Canonical Domain):
1. Update `docs/phase1/ARCHITECTURE_MAP.md` with the new layer and its position
2. Update `tests/architecture/LAYER_MAP.py` with the directory→layer mapping
3. File an ADR (or update this one) recording the stability position decision
4. The CI check automatically applies the rule to the new layer

---

## Consequences

### Positive
- Any engineer — new or returning — can determine whether a proposed import is architecturally valid by consulting the stability order
- Layer violations are caught at PR time, not at architecture review time
- The rule is self-documenting: the layer map is the enforcement specification
- Future layers (Oversoul Prism, NovaNet) inherit the rule automatically

### Risks
- Enforcing the rule on the existing codebase requires remediating the five known violations (Phase 1 Workstream A). Until remediated, they are recorded as temporary exceptions.
- The rule does not prevent bad design within a layer — it only governs cross-layer imports. Intra-layer quality is governed by the Responsibility Matrix principle (one capability, one home).

---

## Related ADRs

- ADR-013: Phase 0 Security Hardening (established the precedent of constitutional enforcement)
- ADR-014: Phase 1 Kernel Stabilisation (identifies the five current violations to remediate)
- ADR-016 (future): Canonical Domain Model — will define the entity layer and its position
