# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> Supersedes the pass record at
> `docs/control-plane/evidence/gate-hygiene-surface-ownership-01/WORKSTREAM_STATE.md`.

## Pass record — 2026-09-29 (heartbeat)

- **Reconstructed:** `origin/main` = `4164573586860b9c7e04e1815bca4957559046a2` (PR #128,
  `gate-l1.1-boundary-hardening`, merged). Working tree clean; **no open PRs** (verified via
  the PRs API, not assumed).
- **CI:** `actions/runs?head_sha=4164573` → **0 runs**. Expected, not a gap: the only
  workflows that could fire there are CP10 (path-filtered to `web/public_prism/**`,
  `spiral_grove/**`, `lab/**` and named test files) and the secret scan; PR #128's paths are in
  neither set. `solspire-r{1,2,3}-validation` trigger only on `push` to `recon/solspire-r0`
  (last run `aed112b` / `611f69e`, 2026-09-29, **red**). `weaver-mvp2-validation` last ran on a
  PR and passed.
- **Corrected a prior mis-diagnosis, and stop-checked a bad instruction.** The previous
  heartbeat queued *"repair SG-04 contradictory artifacts"*. That task is **not** a test-hygiene
  job — it is a frontend capability change on a CP10-fenced path, with an unresolved product
  choice. Escalated as `SH-08`; **not** executed. See Finding A.
- **Publication:** PR opened — sovereign review. No merge, no force-push, `main` untouched.

## Fingerprint (measured this pass, not remembered)

```
main 4164573                    : 39 failed / 1018 passed / 13 skipped / 2 errors   (41 nodes)
main 4164573 + this correction  : identical (documentation-only change)
architecture                    : 11/11
CP10 mutation boundary          : this diff is outside the path filter (no CP10 run expected)
py_compile api/main.py          : pass    (api/main.py = 2519 / 2600 lines)
vite build                      : environment-blocked (no npm registry access)
```

The automation contract's `main := 6038989` / `804 passed / 12 skipped` /
`architecture 9/10` figures are **stale** — always re-measure.

## Node inventory (reproducible)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline by **name**, never by count alone — counts
move when tests are added. Ledger-vs-live reconciliation for this pass is recorded at
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md` §11.

## Classification ledger

`…/BASELINE_TEST_DEBT_CLASSIFICATION.md` remains the source of truth for node→bucket
assignment, **with §11 correcting it**:

- 51 rows classified at `a26af408`; **18 of those nodes now pass** (PRs #104→#128).
- **4 live nodes absent from the ledger** (suites post-date `a26af408`):
  `test_solspire_r1_governance_convergence.py` ×2, `test_solspire_r2_github_mutation.py` ×1,
  `test_solspire_r3_execution_runtime.py` ×1 — all **REAL_DEFECT** (error-contract drift; the
  safety boundary in each holds). Workflows inert for `main` CI.
- **SG-04 reclassified** from `STALE_ASSERTION` to **merge CONTRADICTION** (Findings A).

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **9 / 35 repaired** (batch 1: SCI/nexus 6; batch 2: solariun-consolidation 3) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) — helper rewrite | STALE_ASSERTION | **done** (PR #127, `surface-ownership-01`) |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | **RESOLVED — no defect.** Self-prerequisite raises `CapabilityCycleError`; a↔b raises `UnknownCapabilityError('cap-b')` because registration is incremental and the membership loop runs to completion first. The test is wrong about *ordering*, and its name is misleading. No dead code. |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `SH-08` | **which activity surface is canonical?** The chamber's inline SG-03 work surface (as `chambers`/`frontend_projection`/`learning_path_projection` assert) or the mounted `<ActivityRuntime/>` (as `test_spiral_grove_activity_runtime.py` asserts). **Mutually exclusive — no revision ever satisfied both.** Until decided, the 7 SG-04 nodes stay red and must not be repaired. | CONTRADICTION | **sovereign decision** |
| `R1/R2/R3` | solspire recon copies: `pass_id` not delegated to Weaver; `execute_patch` absent; `commit_file` drops `code`; `ExecutionRuntime` raises instead of returning `MUTATION_DISABLED` | REAL_DEFECT | recorded, not started (separate workstream) |
| `F-01` | `test_no_firebase_persistence_in_gate` — `sessionStorage` proxy no longer measures its "no cloud persistence" intent | DRIFT (proxy-invalidation) | **sovereign decision** — do not silently loosen |

## Next bounded task

`SH-02` batch 3 — the next dense group of plain `STALE_ASSERTION` string assertions (safe,
test-only, no product decision required). **Do not** pick SG-04 (`SH-08`, needs a sovereign
surface decision) and **do not** pick the solspire R1/R2/R3 nodes (separate workstream; two of
them touch governance-adjacent module contracts).

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and run a
negative control proving the repaired assertion can still fail. Test-only edits; never touch
`api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.

**Do not re-derive a "repair the merge" task for SG-04.** It has been investigated twice now;
the conclusion is documented in
`docs/control-plane/evidence/gate-hygiene-baseline-ledger-correction-01/EVIDENCE.md` §2 and
`…/BASELINE_TEST_DEBT_CLASSIFICATION.md` §11.1. Re-opening it without new evidence is the
repetition failure mode the contract forbids.

## Boundaries

Test-hygiene workstream holds **no** authority over merge, authorization, identity,
authority-model, constitutional architecture, or `web/public_prism/**` capability changes. It
must not create a second mutation or authorization path.
