# WORKSTREAM_STATE — gate-hygiene / F-02 steward_filter provenance

**Gate:** GATE-00 baseline hygiene (pre-gate engineering envelope)
**Workstream:** `gate-hygiene` → `SH-02` queue disposition
**Pass:** heartbeat, `BASE_MAIN` = `df7a99a067382401c00de5e7bbaaac0125ba2088`
**Branch:** `gate-hygiene/f02-steward-filter-provenance-01`
**Classification:** `VERIFIED` (repository-layer) — **READY FOR SOVEREIGN MERGE**

---

## Objective (bounded)

Resolve a **contradiction between two open PRs** over the 3 `tests/test_steward_filter.py` nodes
(ledger rows **27–29**, registered `F-02`):

- PR **#138** §7: *"only `tests/test_steward_filter.py` (3 nodes) remains a plausible
  in-envelope candidate, now queued"* → implies `SH-02`-repairable.
- PR **#140** §4: *"the three `test_steward_filter.py` nodes are new: the behaviour, not only the
  assertion, has diverged"* → implies a decision.

Both are open, both target `df7a99a`, both are docs-only. The disposition of 3 of the 35
`STALE_ASSERTION` rows depends on which is correct.

**Result: #140 is correct; #138 §7 is superseded.** Evidence: `EVIDENCE.md`.

---

## State reconstructed this pass (from live evidence, not memory)

| item | value |
|---|---|
| `main` / `origin/main` / `origin/HEAD` | `df7a99a` (merge of #131) — agree |
| open PRs | **7** (#133, #135, #136, #137, #138, #139, #140) |
| full suite | `32 failed / 1025 passed / 13 skipped / 2 collection errors` |
| `tests/architecture` | **11/11** |
| `api/main.py` | 2519 lines, `py_compile` clean |
| `vite build` | environment-blocked (no npm registry) — unchanged |

Fingerprint is **identical to the recorded baseline** — no drift attributable to any open PR.

## Finding — F-02 is Genesis-origin and never passed

1. `tests/test_steward_filter.py` and `weaver/filters/steward.py` are **blob-identical to the
   Genesis root commit `9ab26fc`**; **zero** commits since Genesis touch either path (verified
   with rename-aware `--follow` *and* blob-hash comparison).
2. All three nodes **fail at `9ab26fc`** as well as on `main` — reproduced in a detached
   worktree. There is **no green revision**, so `STALE_ASSERTION` ("drifted from intact
   behaviour") has no support.
3. Each failure is a **module-vs-own-docstring contradiction** — Rule 4 density rejects before
   Rule 3 action language is consulted; Rule 1 forbids `"transcendent"` not `"transcended"`;
   `compress_to_choices` splits on `"\n"` while its docstring says *"sentences"*.
4. `weaver/filters/steward.py` has **no importer anywhere** — unwired; corroborated by
   `docs/verification/P1-1_PRIVATE_BETA.md:42` ("EXISTING + UNWIRED").

## Disposition

| rows | verdict | next action |
|---|---|---|
| 27–29 (`F-02`) | **DEFECT — module narrower than its own contract** | **keep red**; sovereign ruling; repair is a *module* change, not an `SH-02` test edit |

`SH-02`'s envelope is *"re-point the assertion at the surface that now owns the behaviour;
test-only edits."* No surface owns the asserted behaviour, so these rows are **out of envelope**.
They remain a **decision**, not a batch — PR #140's disposition stands.

## Queue state (unchanged by this pass)

| disposition | count |
|---|---|
| GREEN on `main` | 19 |
| IN_OPEN_PR | 12 (#133 ×5, #135 ×3, #136 ×2, #137 ×2) |
| RESIDUAL / decisions | 4 (rows 27–29 `F-02`; `F-01` `test_no_firebase_persistence_in_gate`) |
| open `SH-02` batch | **0** |
| **total** | **35** |

## Cross-PR verification performed this pass

- **CP10 mutation-boundary judge re-run independently** on each PR's real changed-file set:
  **PASS ×7**. (None of the seven touches a gated path, so `sg-02-fe-2-v.yml` correctly does not
  trigger — its `pull_request` filter is path-scoped.)
- **CI on every PR head**: 2 check-runs each (`Full-history secret scan` success,
  `Vercel Preview Comments` success). No red.
- **Pairwise file overlap**: only `#135 ↔ #136`, `#135 ↔ #137`, `#136 ↔ #137` share a file —
  all three append to `…/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.
  **#133, #138, #139, #140 are file-disjoint.** This confirms PR #139 §3 from the file set alone.

## Anomaly resolved — GitHub auth

The previous pass recorded `401 Bad credentials` and classified GitHub access `BLOCKED`.
Root cause: **`GITHUB_PERSONAL_ACCESS_TOKEN` (an expired `ghp_…`) shadows the valid
`github_token`**, and `gh`/ambient-`GITHUB_TOKEN` resolution prefers the dead value.

The working credential is the **`$github_token` environment variable**, which is the same
credential embedded in the `origin` remote URL. It carries `push: true` on this repository
(Contents write) — so push is **not** blocked.

**Operational note:** use `$github_token` explicitly for API calls; do not rely on `gh`'s
default resolution. No token value is recorded here.

## Regression boundary

Docs-only. No executable file touched. Full-suite node set and architecture fitness are
**unchanged**; no baseline failure is re-attributed.

## Authority boundary

- No merge, no push to `main`, no force-push.
- **No product decision made.** §7 of `EVIDENCE.md` recommends keeping the rows red and defers
  the contract ruling to the sovereign.
- No scope expansion: the module repair is **recorded for the queue**, not proposed for
  execution here.

## Next bounded task (for the next heartbeat)

Reconstruct from live evidence first (contract §14). Open threads, in dependency order:

1. **#140 merge** — settles the `SH-02` denominator (`19 / 12 / 4 / 0`). Now fully verified:
   12-node disposition and the 19-green rows were both independently reproduced this pass.
2. **#133 merge** — `PARTIAL by design` (`F-01` deliberately left red).
3. **#138, #139 merge** — docs-only; #138 §7 needs a one-line supersede note pointing at this
   artifact (do **not** rewrite another PR's file — note it at merge time).
4. **Ledger-append collision** — #135/#136/#137 all touch the same ledger; **#137 conflicts in
   every ordering** (PR #139 §3). Merge #137 **last** with a union-append resolve.
5. **Then** the residual decisions: `F-01`, `F-02` (rows 27–29), `SH-03` (DRIFT contract split),
   `SH-05` (ENV), `SH-07`, `SH-08` (CONTRADICTION — 4 `test_spiral_grove_activity_runtime.py`
   nodes, needs a sovereign surface decision).
6. Out-of-ledger, separate workstream: `R1/R2/R3` + `spiral_grove_activity_runtime` (4 live nodes
   absent from the ledger; already recorded in `gate-hygiene-baseline-ledger-correction-01`).
   Their CI workflows are inert for `main` — no gate pressure.

**Do not** open another `SH-02` batch: the candidate set is exhausted (0 remaining).
