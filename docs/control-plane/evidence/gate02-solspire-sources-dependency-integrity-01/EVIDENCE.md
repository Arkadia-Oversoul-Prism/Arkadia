# GATE-02 — SolSpire Sources Dependency Integrity — EVIDENCE

**Authorization:** bounded GATE-02 engineering repair under the standing Weaver
hourly contract. **Merge: HUMAN ONLY** — this work does not merge, does not push
to `main`, and does not force-push.
**Base:** `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f` (`main`, observed
2026-10-01T16:06Z).
**Branch:** `gate02/solspire-sources-dependency-integrity-01`.

This document is evidence, not authorization.

---

## 1. What was measured, and what it said

Running the Gate 2 harness against production as-is:

```
$ python3 scripts/gate2_backend_observation.py
backend host      : https://arkadia-kw64.onrender.com
schema            : HTTP 200  operations=275
deployed digest   : 359677ac7fa906d7e952
ROUTE-SET ORACLE
  main:3e1cd007c93f        81668b968759fc1ac48e
  distinct signatures: 1  => discriminating: False
BOUNDARY CLASSIFICATION
  main -> backend deployment identity        UNKNOWN
  backend runtime observation                CONTRADICTED
  backend <-> source lineage                 CONTRADICTED -- route-set oracle
NOTES
  - schema differs; only in deployment:
      DELETE /solspire/sources/{source}
      GET    /solspire/sources
      POST   /solspire/sources/{source}/connect
      POST   /solspire/sources/{source}/sync
```

`CONTRADICTED` is the strongest negative state in the contract, and it was
pointed at the *deployment*. It was not a deployment defect.

## 2. Root cause — an undeclared module-scope dependency

`api/source_connections.py` imports `cryptography` at **module scope** (Fernet,
for source credentials encrypted at rest). The module is reached through
`api/key_routes.py`:

```python
try:
    from api.source_routes import router as _source_router
    router.include_router(_source_router)
except Exception as _source_err:
    logger.warning("[SOURCES] Source connection router skipped: %s", _source_err)
```

That guard is deliberate and correct — it is the P1-A lesson (a boot-time
failure must not take production down). Its cost is **silence**: an environment
missing the dependency serves a *smaller* route set and still looks healthy.

`cryptography` was never declared. `grep -in cryptography requirements.txt`
returned nothing. It was present only **transitively**, pulled in by
`pdfminer.six`. Nothing in the repository stated that contract, and nothing
failed when it was absent.

## 3. The discriminating measurement

The observer environment lacked `cryptography`, so the local signature import
of `api.main` ran **without** the source router and compared a 271-operation
signature against production's 275. The four-operation difference was an
environment gap being reported as a source divergence.

With the dependency present, the local signature is **byte-identical** to
production:

```
local digest (with cryptography): 359677ac7fa906d7e95212adbb1a8d1a33ed86a1e97908d1b8574ae8864d3301
production digest reported      : 359677ac7fa906d7e952
solspire/sources routes: 4      total ops: 275
```

Re-running the harness with the dependency available:

```
ROUTE-SET ORACLE
  main:3e1cd007c93f        359677ac7fa906d7e952
BOUNDARY CLASSIFICATION
  backend runtime observation                VERIFIED (undiscriminating)
  backend <-> source lineage                 VERIFIED (undiscriminating)
```

The digest matches production exactly. **`main` is consistent with the deployed
backend**; the earlier `CONTRADICTED` was an artifact of the observer's
environment, not of the deployment.

## 4. Boundary states after this work

| Boundary | State | Basis |
|---|---|---|
| current main resolved | VERIFIED | `3e1cd007c93f…` |
| main → backend deployment identity | **UNKNOWN** | Render publishes no source SHA; no route exposes the deploy commit |
| backend runtime observation | VERIFIED (undiscriminating) | digest `359677ac7fa906d7e952…` |
| backend ↔ source lineage | VERIFIED (undiscriminating) | route-set oracle, 275 ops, identical digest |
| production acceptance | **NOT CLAIMED** | human authority |

Two limits are stated rather than papered over:

1. **Deployment identity remains UNKNOWN.** Matching route sets and a matching
   digest show the deployed process agrees with `main`'s schema. They do **not**
   name the deployed commit. The oracle is *undiscriminating* — all candidate
   revisions share one signature — so equality cannot separate the deployed
   revision. This is reported as `VERIFIED (undiscriminating)`, never promoted
   to plain `VERIFIED`.
2. **`UNKNOWN` is not converted to `VERIFIED` by repetition.** The parity
   question (PR #143 lineage) stays open until a deployment identity is
   obtainable.

## 5. The bounded change

| Path | Change |
|---|---|
| `requirements.txt` | declare `cryptography` explicitly, with the reason |
| `tests/test_solspire_sources_dependency_integrity.py` | hold the declaration as a contract (6 tests) |

The guard test asserts the general invariant — *every module-scope third-party
import of `api/source_connections.py` must be declared* — rather than
special-casing one package name. Two negative controls are included:

- removing the `cryptography` line from a **doctored copy** of requirements must
  be detected (proves the check fails when it should);
- the parser must not be vacuous (proves the check can pass for the right
  reason).

## 6. Verification

| Check | Command | Result |
|---|---|---|
| guard tests | `pytest tests/test_solspire_sources_dependency_integrity.py -q` | **6 passed** |
| full suite (baseline, `main`) | `pytest tests/ -q --continue-on-collection-errors` | 22 failed / 1127 passed / 13 skipped / 1 error |
| full suite (branch) | same | see §7 |
| architecture fitness | `pytest tests/architecture -q` | see §7 |
| CP10 mutation boundary | `scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| boot compile | `python -m py_compile api/main.py` | see §7 |

## 7. Results

Measured on the branch, both trees run under an identical interpreter and
`PYTHONPATH`, `--continue-on-collection-errors` (no `pytest.ini`/`pyproject`
`[tool.pytest]` exists in the repository, and without the flag the single
collection error aborts the whole run):

```
baseline  main:3e1cd00   22 failed, 1127 passed, 13 skipped, 1 error
branch  gate02/solspire-  22 failed, 1133 passed, 13 skipped, 1 error
```

**Failing-node fingerprint diff — identical.** The 23 failing/erroring node IDs
(22 `FAILED` + 1 `ERROR`) are byte-identical between the two runs:

```
$ diff <(grep -E '^(FAILED|ERROR)' baseline.txt | sed 's/ - .*//' | sort) \
       <(grep -E '^(FAILED|ERROR)' branch.txt   | sed 's/ - .*//' | sort)
(no output)
```

The `+6 passed` is exactly the six tests added by this work; none appear in
either failure list. **No new test-node delta. No pre-existing failure repaired
or newly broken.**

| Check | Result |
|---|---|
| `pytest tests/test_solspire_sources_dependency_integrity.py -q` | **6 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | **OK** |
| `api/main.py` line count | 2531 / 2600 budget (untouched by this work) |
| CP10 `--judge` on the three changed paths | **PASS** |

Baseline drift against the ledgered figures is recorded, not silently absorbed:
the ledger held `804 passed / 54 failed / 12 skipped / 2 collection errors`,
the live tree measures `1127 passed / 22 failed / 13 skipped / 1 error`. The
live measurement is authoritative and is what this work was compared against.

## 7a. Verification of the #163 defect claim

PR #163 (§7) asserted, of `main`:

> `main` today imports `ActivityRuntime` and **never renders it** — a dead import.

Re-measured against live `main` (`3e1cd00`) by direct grep of
`web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx`:

```
$ grep -n "ActivityRuntime" CapabilityChamber.tsx
(no matches)
$ grep -n "<ActivityRuntime" CapabilityChamber.tsx
(no matches)
```

**Contradicted on current `main`.** The claim was accurate when written, but
`main` moved underneath it: PR #166 (`47e4128`) removed the line —

```
$ git show 47e4128 -- CapabilityChamber.tsx | grep ActivityRuntime
-import ActivityRuntime from './ActivityRuntime'
```

Current `main` therefore carries **neither** the import **nor** the mount. It is
not a dead import; it is an absent one. The #163 document is a merged,
point-in-time artifact and was not wrong when authored — it is stale now.

What remains **verified** from #163:

| #163 claim | State on `main:3e1cd00` |
|---|---|
| `main` imports `ActivityRuntime` but never renders it | **CONTRADICTED** — #166 removed the import |
| the four named `test_spiral_grove_activity_runtime.py` tests fail | **VERIFIED** — 4 failed / 8 passed |
| the deployed artifact matches `main`; not a stale deployment | **VERIFIED** — digest `359677ac7fa906d7e952…` identical |
| harness label "SG-04 REGRESSION" is mis-worded | **VERIFIED** — source and artifact agree |

**Residual genuine defect (separate, still open).** Independently testing PR
#174's head (`4c1bc70`, worktree `/tmp/wt174`):

```
4 failed, 8 passed   ->   1 failed, 11 passed
```

3 of the 4 fixed; the survivor is
`test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`, which
requires a literal `data-testid="activity-surface-<kind>"` while
`ActivityRuntime.tsx` renders a template expression. #174's own evidence
documents this as an open dependency rather than claiming it fixed. That
matches the measurement. **Not fixed here — out of scope for this PR.**

## 8. Non-goals — explicitly not done

- **No guard removed.** The `try/except` in `api/key_routes.py` stays. Removing
  it would reintroduce the P1-A boot-failure class.
- **No boot-manifest added.** Making silent skips loud is a genuinely valuable
  separate workstream; it touches boot code and belongs in its own bounded PR.
  It is **proposed**, not executed here (see §9).
- **No baseline debt repaired.** The pre-existing failures are unrelated and
  were not touched.
- **No production claim.** Deployment identity remains `UNKNOWN`.

## 9. Proposed (not authorized) follow-on

**Boot-manifest observability.** `api/main.py` wraps ~12 router mounts in
`try/except Exception` that log a warning and continue. A missing dependency
therefore degrades the runtime silently. A future bounded workstream could
record mount outcomes into a machine-readable manifest exposed on a health
route, so a degraded boot is *observable* rather than inferred. This is
classified, dependency-linked, and **not executed** in this pass.
