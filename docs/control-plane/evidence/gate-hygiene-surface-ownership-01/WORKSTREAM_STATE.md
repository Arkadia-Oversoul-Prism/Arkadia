# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> Supersedes the batch-2 state at
> `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-solariun-consolidation-01/WORKSTREAM_STATE.md`.

## Pass record — 2026-09-29 (heartbeat)

- **Reconstructed:** branch on `417d32d` (current main, PR #126); `git merge-base HEAD origin/main`
  = `417d32d`. `ee3fac1` is batch-1 (PR #124), NOT the parent of this branch; the earlier
  `BASE_MAIN = ee3fac1` in EVIDENCE.md was corrected in a follow-up commit (force-push forbidden).
- **CI:** secret scan on the PR head = success. `SG-02-FE.2-V` (CP10) runs on `main` push and
  `pull_request` per `.github/workflows/sg-02-fe-2-v.yml`; locally delegated judge = PASS (exit 0).
- **Local ref hygiene:** `gate-hygiene/prism-pass-c-helper-rewrite-01` is a stale, never-pushed
  local ref at `417d32d`. Not a competing PR; no duplicate work on the remote.
- **Publication:** PR opened — sovereign review. No merge, no force-push, `main` untouched.
- **Frontend CI (not mine, not blocking the claim):** Vercel reports `failure` on main `417d32d`,
  i.e. it was already red *before* this branch. It is `success` on `ee3fac1` and on this branch
  head, because the Vercel status is per-commit and this diff contains no frontend file. Outside
  this bounded task — recorded, not diagnosed further (would require frontend scope).

## Fingerprint (measured this pass, not remembered)

```
main 417d32d (clean)          : 45 failed / 985 passed / 13 skipped / 2 errors   (47 nodes)
main 417d32d + SH-02b         : 39 failed / 991 passed / 13 skipped / 2 errors   (41 nodes)
  removed                     : 6 nodes, all in test_prism_pass_c_surface_ownership.py
  added                       : none
architecture                  : 11/11
CP10 mutation boundary        : PASS (exit 0)
py_compile api/main.py        : pass    (api/main.py = 2519 / 2600 lines)
vite build                    : environment-blocked (no npm registry access)
```

`main` advanced mid-pass (`ee3fac1` -> `417d32d`, PR #126) and the endorsed fingerprint was
re-measured at the new base rather than reused; see the EVIDENCE section 1a for why the
recorded base was corrected. `417d32d` is the true parent of this branch.

The two suites were measured back-to-back on the same runner with the same
`PYTHONPATH=<repo>/archive/legacy_python`, and the delta was attributed by **sorted node
name**, not by count. The automation contract's `main := 6038989` /
`804 passed / 12 skipped` / `architecture 9/10` figures are stale — always re-measure.

## Node inventory (reproducible)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline to attribute a delta by *name*, never by
count alone — counts move when tests are added.

## Classification ledger

`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
is the single source of truth for node→bucket assignment (51 nodes at `a26af408`).

Bucket counts at that pass: **STALE_ASSERTION 35**, **DRIFT 10**, **ENV/ARTIFACT 2**,
**REAL_DEFECT 1**, **COLLECTION_ERROR 2**.

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **15 / 35 repaired** (batch 1: 6; batch 2: 3; batch 3 `SH-02b`: 6) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) — helper rewrite, not string edits | STALE_ASSERTION | **done**, PR #127 open, sovereign merge pending. **Heartbeat follow-up (this pass):** two *false claims* in that repair corrected — `codex` routes to the **knowledge** lens, not `memory` (§3.4); `knowledge-os` **does** have a redirect rule (§4). Both nodes strengthened; `SH-02c` withdrawn |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `F-01` | `test_no_firebase_persistence_in_gate` — `sessionStorage` proxy no longer measures its "no cloud persistence" intent (gate has 0 firebase refs; storage is ephemeral handoff) | DRIFT (proxy-invalidation) | **sovereign decision** — do not silently loosen |
| `SH-02c` | ~~`knowledge-os` legacy id has **no** redirect rule in `App.tsx` (mount-only)~~ | ~~DRIFT (proposed)~~ | **WITHDRAWN — finding was false.** `knowledge-os` *does* have a grouped `handleNavigate` redirect rule (line 115) and a `'/knowledge-os'` path-table entry (line 57) beside its mount (line 150). The node under-asserted; corrected in `SH-02b`. No product decision needed |

## Next bounded task

`SH-02` next batch — the plain string-assertion rows still in the STALE_ASSERTION bucket
(the dense remainder). `SH-02b` deliberately did **not** touch anything outside its one
file. Rule unchanged: re-point the assertion at the surface that now owns the behaviour,
and run a **negative control proving the repaired assertion can still fail** (see the
`SH-02b` EVIDENCE §3.3 for the mutation-anchor technique — a control whose mutation does
not actually apply is vacuous, and must be recorded as such rather than counted as proof).

Do not start `SH-03`/`SH-04`/`SH-06`/`SH-07`/`F-01`/`SH-02c`: each needs a product or
architectural decision, not a test edit.

Test-only workstream. Never touch `api/main.py`, `LAYER_MAP.py`, ADRs, policy modules,
workflows, or governance files from here. Nothing merges without the sovereign.