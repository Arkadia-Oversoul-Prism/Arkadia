# SG-04 activity-surface literal pin — test-side defect repair — EVIDENCE

Bounded workstream: `gate-hygiene/sg04-activity-surface-literal-01`
Base main at pass start: `3d4df9ec890c8b8f6d087c5c1577450cfacf1360`
Observed: 2026-10-02 (UTC)
Scope: **test-only** — `tests/test_spiral_grove_activity_runtime.py`

## 1. Defect (VERIFIED)

`tests/test_spiral_grove_activity_runtime.py:79` demanded an **expanded** literal that the
component can never emit, because the component emits a **template**:

```python
assert f'data-testid="activity-surface-{kind}"' in runtime   # test (expanded literal)
```

```tsx
<div data-testid={`activity-surface-${kind}`}>               // ActivityRuntime.tsx (template)
```

The assertion checks that the *rendered* string is present in *source*. It cannot match its
own template. The test was red on `main`, and — measured across every revision that contains
the file — **was never green**:

| revision | template present | expanded literal present |
|---|---|---|
| `74f5494` (SG-04 foundation) | 0 | 0 |
| `1b63994` (typed surfaces) | 1 | 0 |
| `06ad5f2` (persistence hardening) | 1 | 0 |

The `activity-surface-*` testids **are** implemented — via the template. The runtime DOM
testid for each kind is correct; only the source-level assertion form is wrong.

## 2. The property the test protects is intact (VERIFIED)

The test exists to prove each of the eight activity kinds dispatches to a deterministic
renderer that carries a kind-specific surface. That property holds:

- 8/8 renderers exist: `ResearchSurface … CollaborativeSurface`.
- 8/8 dispatch arms exist: `case '<kind>': return <<Renderer>`.
- 8/8 kind bindings exist: each renderer renders `<Surface {...p} kind="<kind>" />`, so the
  shared `Surface` emits `data-testid={`activity-surface-<kind>`}` for that kind.

```bash
grep -cE 'return <Surface \{\.\.\.p\} kind="[a-z]+"' ActivityRuntime.tsx   # 8
grep -c 'data-testid={`activity-surface-${kind}`}' ActivityRuntime.tsx    # 1
```

### Negative controls — the assertions can detect the defects they claim to detect

The repaired assertions were probed against mutated source, confirming each control flips
the property it guards (a harness that cannot fail is not evidence):

| mutation | template assertion | kind-binding assertion |
|---|---|---|
| unmodified source | holds | holds (0 unbound) |
| template removed | **fails** | holds |
| one kind binding mutated (`creative` → `writing`) | holds | **fails** (1 unbound) |
| one renderer renamed | holds | holds (`function` assertion fails) |

## 3. Classification lineage — why this is test-side, not a product defect

An earlier ledger entry (`gate-hygiene-baseline-test-debt-classification-01` §11.2)
proposed **REAL_DEFECT** for this node, on the ground that `activity-surface-*` was
"never implemented". That reading matched the **expanded literal only** — i.e. it repeated
the test's own defect. §11's REAL_DEFECT verdict is superseded by three later, independent,
*measured* records, all of which classify the node as test-side and explicitly reserve it
for **its own bounded workstream**:

| record | verdict |
|---|---|
| `gate02-capability-chamber-merge-loss-repair-01` §5.2 | "test-side assertion-form defect" |
| `gate02-capability-chamber-union-repair-02` §8 | "Test-side defect on `main` … needs its own bounded workstream" |
| `gate01-relational-lineage-canonical-provenance-01` WORKSTREAM_STATE | "asserts a literal where the component renders a template … its own bounded workstream" |

This pass is that workstream. It is **test-only** and therefore stays inside the test-hygiene
boundary; it is not a frontend capability change.

### Boundary preserved — the three sibling nodes were NOT touched

`tests/test_spiral_grove_activity_runtime.py` carries four historically-failing nodes. Only
node `::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` is repaired here.
The other three were already green on base `3d4df9e` and remain untouched, because an earlier
proposed remedy ("align the test with the mounted runtime") would have **relaxed boundary
guards** for no gain (`BASELINE_TEST_DEBT_CLASSIFICATION.md` §11.2.1). Measured on base:

| node | base `3d4df9e` | this branch |
|---|---|---|
| `::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | **FAILED** | **passes** |
| `::test_runtime_is_mounted_by_the_capability_chamber` | passes | passes |
| `::test_chamber_preserves_sg03_downstream_boundary` | passes | passes |
| `::test_spiral_grove_uses_the_nexus_canonical_header` | passes | passes |

## 4. Change set

```
tests/test_spiral_grove_activity_runtime.py | 3 ++-
```

```diff
         assert f"case '{kind}': return <{renderer}" in runtime
         assert f"function {renderer}" in runtime
-        assert f'data-testid="activity-surface-{kind}"' in runtime
+        # The shared Surface emits the testid from a template; the kind is bound by each renderer.
+        assert 'data-testid={`activity-surface-${kind}`}' in runtime
+        assert f'kind="{kind}"' in runtime
```

The assertion is replaced by the **stronger** pair: the template (present) plus each
renderer's kind binding (which is what makes the runtime testid kind-specific). It does not
weaken the property; it asserts it at the level the source actually expresses it.

## 5. Verification

| command | base `3d4df9e` | this branch |
|---|---|---|
| `pytest tests/test_spiral_grove_activity_runtime.py -q` | 1 failed / 11 passed | **12 passed** |
| `pytest tests/architecture -q` | 11 passed | **11 passed** |
| `pytest tests/test_m02a_ci_gate_integrity.py -q` | 51 passed | **51 passed** |
| `cp10_mutation_boundary_policy.py --judge` (changed path) | — | **PASS** (rc=0) |
| `python -m py_compile api/main.py weaver/agent.py` | OK | OK |
| `api/main.py` line budget | 2571 / 2600 | 2571 / 2600 (untouched) |
| `vite build` | environment-blocked (no registry access) — **not claimed** | same |

### Fingerprint — full suite, node-set delta

Captured with `--continue-on-collection-errors` so the documented `test_autonomy.py`
collection error does not abort the run. The environment-independent claim is the
**relative** one: no node-set delta other than the repaired node.

```
base  3d4df9e : 20 failed / 1236 passed / 17 skipped / 1 error   (21 nodes)
               sha256(sorted node ids) = c2f31d8caab562fa92fa693ee6bcda3caa8a95da7e26ae8d5255e94657f3c7e5
this branch   : 19 failed / 1237 passed / 17 skipped / 1 error   (20 nodes)
               sha256(sorted node ids) = 66a69c500d9c1be2f807af77334480869673bda8896e50c5089318cdba199393

node-set delta (normalized to node id):
  RESOLVED : tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
  NEW      : (none)
```

**Exactly one node resolved, zero new.** The base fingerprint sha256 `c2f31d8c…` matches the
recorded pre-pass fingerprint exactly.

## 6. CI applicability (derived from the workflow, not assumed)

`SG-02-FE.2-V` (`sg-02-fe-2-v.yml`) is **path-filtered**. This change touches
`tests/test_spiral_grove_activity_runtime.py`, which is **not** in the filter list, so the
`validate` job is not triggered by this path alone. The gate is still exercised on the
branch's evidence path via the policy module directly (§5) and by
`tests/test_m02a_ci_gate_integrity.py`. `security-secret-scan` has an unfiltered
`pull_request` trigger and runs on every PR. `provider-routing` triggers on `weaver/**` only
and is untouched here.

## 7. Remaining uncertainty

- `vite build` remains environment-blocked; no frontend build claim is made. The change is
  test-only, so this does not bound the repair.
- The full-suite absolute counts are environment-dependent (`fastapi` and optional deps
  installed this session; the contract's recorded `804/54/12/2` fingerprint does not
  reproduce here). Only the node-set delta is claimed as environment-independent.
- No product/frontend behaviour was changed, so no runtime/DOM evidence is required or
  claimed for this pass. The property proven is source-level, matching the test's own level.

## 8. Authority

No merge, no push to `main`, no force-push. This pass changes no authority, identity,
K15/K3 governance, mutation path, or product surface. Human sovereign merge only.
