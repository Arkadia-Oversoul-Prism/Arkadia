# Lane 2 — bind the repost count reading to a detector that rejects fabrication

**Lane:** 2 (NovaNet + project Opportunity Radar)
**Base:** `main` `4b91c2f416a104589283c3846a0766e252a08900`
**Branch:** `lane2/reposts-count-detector-binding-01`
**Scope:** `tests/test_prism_novanet_engagement_readings.py` only — lane-2 owned
(`SHARED-CONTRACTS.md` §1: opportunity/NovaNet feature-local tests). No console source,
backend contract, registry, or other lane's file is touched. Node count unchanged at **15**.

## 1. The defect

`test_no_invented_counts` asserted two count readings, and bound only one of them:

```python
assert "reactions?.[type] ?? 0" in src        # a regex over the fallback expression
assert "typeof transmission.reposts" in src   # a bare substring
```

The second literal is a **prefix of the reading, not the reading**. `EngagementBar.tsx`
derives the value as

```ts
const reposts = typeof transmission.reposts === "number" ? transmission.reposts : 0;
```

so any replacement that keeps the `typeof transmission.reposts` prefix and discards the
server value satisfies the assertion. The guard judged the shape of the expression and not
whether the server's count reached the surface — the same "assert a literal, not the
property" class recorded for the SG-04 mount and the row-cap convention.

## 2. Measured before the repair

Rewriting the repost binding to a constant, leaving the asserted substring intact:

```
const reposts = typeof transmission.reposts === "number" ? 7 : 0;
```

```
15 passed in 0.08s
```

Every node in the module stayed green with the repost count fabricated for every post. The
guard could not report the defect it exists to catch.

## 3. The repair

The two count readings move to a module-level table and the predicate to
`_invented_count_defects(source)`. The live node and the control **both** call it, so neither
restates the property:

```python
_COUNT_READINGS = (
    ("reaction", _ZERO_FALLBACK, "a missing reaction count must read 0, not be invented"),
    ("repost",   _REPOST_READ,   "the repost reading must be the server value with 0 as its only fallback"),
)

def _invented_count_defects(source: str) -> list[str]:
    if "export function EngagementBar" not in source:
        return []
    return [reason for _, pattern, reason in _COUNT_READINGS if not pattern.search(source)]
```

`_REPOST_READ` requires the **server value on the true branch and `0` on the false branch**,
so a constant on either side is reported:

```python
_REPOST_READ = re.compile(
    r"typeof transmission\.reposts\s*===\s*[\"']number[\"']\s*\?\s*transmission\.reposts\s*:\s*0"
)
```

`_invented_count_defect(source)` is retained as the boolean view (`bool(...)`) so the
detector-silence sweep keeps one line per property; it now delegates rather than carrying a
second copy of the predicate.

## 4. Proof the repair bites

The **same** mutation that previously left 15 passing, re-measured against the repaired guard:

```
FAILED tests/test_prism_novanet_engagement_readings.py::test_no_invented_counts
FAILED tests/test_prism_novanet_engagement_readings.py::test_detectors_are_silent_on_the_live_tree
FAILED tests/test_prism_novanet_engagement_readings.py::test_detector_flags_an_invented_count
3 failed, 12 passed in 0.09s
```

The source file was restored byte-identically (`git diff --stat -- web/` empty) and the
module returns to **15 passed**.

### The second polarity — the detector must not be vacuous

A control that only proves the repair bites says nothing about whether the predicate itself
still measures anything. Making the detector answer `[]` unconditionally:

```
FAILED tests/test_prism_novanet_engagement_readings.py::test_detector_flags_an_invented_count
1 failed, 14 passed in 0.09s
```

The control reddens, so emptying `_COUNT_READINGS` or short-circuiting the predicate cannot
pass silently. Restored byte-identically; **15 passed**.

## 5. Verification

| Check | Command | Result |
|---|---|---|
| Target module | `pytest tests/test_prism_novanet_engagement_readings.py -q -rEf` | **15 passed** |
| Node count | `pytest ... --collect-only -q` (branch vs `main`) | **15 / 15** — unchanged, a binding repair not a new node |
| Related lane-2 guards | composer + field + echoes + author controls | **36 passed** |
| Architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| Lane currency | `python scripts/lane_state.py --check` | exit **0** |
| Console-contract domain | derived 73-path domain, branch vs `main` | **10 failed / 1204 passed / 4 skipped**, node set **identical** to `main` (`comm -3` empty) |
| Mutation boundary | `cp10_mutation_boundary_policy.py --judge` | **PASS** |

The 10 failing nodes in the console-contract domain are **pre-existing on `main`** and are an
environment gap, not repository debt: `test_mission_lifecycle_adapter_contract.py` asserts
`TSC.exists()` at `web/arkadia_console/node_modules/typescript/lib/typescript.js`, and this
sandbox has no `node_modules`. The same 10 nodes fail identically on `main` `4b91c2f4`. The
workflow's `console-contract` check passes on CI, where the console is installed.

## 6. Wiring

No new wiring is needed. `tests/test_prism_novanet_engagement_readings.py` is already a member
of the derived console-contract domain (`python scripts/console_contract_domain.py` → 73
paths), and `.github/workflows/prism-console-contract.yml` executes that domain by derivation
rather than by a restated list. A guard added to the corpus is executed by the gate without
editing it.

## 7. Boundaries

- No protected authority, identity, K15/K3 governance, approval enforcement, constitutional
  architecture, or deployment configuration is altered. The diff is one test module.
- The console source is **not** modified: the shipped `EngagementBar.tsx` already reads the
  server value correctly, and the repair changes only whether the guard can tell.
- PR is **draft**. Merge, production deployment and acceptance remain human-only under GOV-03.
