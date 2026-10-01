# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> Supersedes `docs/control-plane/evidence/gate-hygiene-baseline-ledger-correction-01/WORKSTREAM_STATE.md`.

## Pass record — 2026-09-30 (heartbeat)

- **Reconstructed:** `origin/main` = `002b189d` (merge of PR #141,
  `gate-hygiene/f02-steward-filter-provenance-01`). Working tree clean.
- **Open PRs at pass start: 7** — `#142` (SH-05 provenance), `#143`, `#144`
  (test-session DB isolation), `#145` (intermittency attribution), `#146`
  (`gate-k/k5-status-reconciliation`), `#147` (Gate-2 AGENTS.md encoding repair, based on
  `gate-hygiene/gate2-production-parity-02`), `#148` (scheduler bootstrap test-spec repair).
  **All 7 re-confirmed `mergeable: true / mergeable_state: clean`** via the PRs API — the
  earlier `mergeable_state: ?` readings were an unresolved-computation artefact, not a
  conflict. None was merged; none was superseded; **no duplicate work opened.**
- **Continuity:** `SH-02` is exhausted (0 nodes left to batch) — confirmed by `#142`'s own
  ledger. The gate-hygiene queue's remaining items are `SH-03`/`SH-06` (product judgement),
  `SH-07` (architectural gate), `SH-08` (sovereign surface decision), `SH-05` (sovereign
  disposition, evidence now attached by `#142`), and `R1/R2/R3` (separate workstream).
  The smallest valid unclaimed item was the **second `COLLECTION_ERROR` node** — the only
  baseline node this workstream had never actually investigated.
- **Measured fingerprint at pass start** (`PYTHONPATH=<repo>/archive/legacy_python`, i.e. the
  documented environment, `--continue-on-collection-errors`):
  `20 failed / 1039 passed / 13 skipped / 2 warnings / 2 errors`. Reproduced twice, stable.
- **Publication:** PR (this branch) → `gate-hygiene/render-codex-collection-error-provenance-01`,
  **READY_FOR_SOVEREIGN_MERGE**. No merge, no force-push, `main` untouched.

## Finding — `test_render_codex.py` is a naming defect, not missing infrastructure

The ledger (`BASELINE_TEST_DEBT_CLASSIFICATION.md` §4.5) and `AGENTS.md` both explain this
collection error as *"`arkadia_drive_sync` absent — expected when
`PYTHONPATH=<repo>/archive/legacy_python` is set"*. **That is false, and it has been
propagated into five documents without ever being tested.** Full derivation in `EVIDENCE.md`.

Three independent proofs:

1. **The file is not a test module.** `grep -cE '^def test_|^async def test_|^class Test'` → `0`.
   It is a 46-line manual probe with placeholder API keys and a `__main__` guard.
2. **No green revision exists.** `arkadia_drive_sync.py` was deleted (`88a0cafd`, 10:50:58,
   2026-03-11); `tests/test_render_codex.py` was *created by rename* later the same day
   (`784acb4d`). The dependency was already gone when the file entered `tests/`. Genesis has
   the dependency but not the test file.
3. **The documented remedy does not work.** Running with the prescribed `PYTHONPATH` still
   raises `ModuleNotFoundError`. The module exists nowhere in the repository — not at the
   root, not under `archive/legacy_python/`.

**Repair:** `git mv tests/test_render_codex.py tests/render_codex_probe.py` — rename only,
byte-identical (`0 insertions(+), 0 deletions(-)`). This matches the convention the repository
already set for the identical sibling probe `tests/render_test_console.py`, which shares the
same `codex_brain` import and has never been pytest-visible.

**Rejected alternatives and why** — see `EVIDENCE.md` §3.1. The important one: stubbing or
vendoring `arkadia_drive_sync` would manufacture an outbound Google-Drive credential path
(`GOOGLE_SERVICE_ACCOUNT_JSON_FILE`, `googleapiclient`) purely to make an import succeed. That
is a new external consequential path created by a hygiene pass — a hard stop, not a fix.

## Fingerprint (measured this pass, not remembered)

```
main 002b189 (baseline)          : 20 failed / 1039 passed / 13 skipped / 2 warnings / 2 errors
this branch (rename only)        : 20 failed / 1039 passed / 13 skipped / 2 warnings / 1 error
node-list diff                   : -1  (ERROR tests/test_render_codex.py)  — nothing else moved
collect-only                     : 1071 collected / 2 errors  ->  1071 collected / 1 error
architecture                     : 11/11
CP10 boundary judge (full tracked corpus, 1463 paths) : PASS
tests/test_m02a_ci_gate_integrity.py                  : 49/49
py_compile api/main.py           : pass    (api/main.py = 2519 / 2600)
vite build                       : environment-blocked (no npm registry access)
```

**pytest counts collection errors separately from `failed`.** A repair to a file that
contained no tests therefore must *not* move the `failed` count. Compare by **node list**, as
this ledger already prescribes — not by count alone.

The automation contract's `main := 6038989` / `804 passed / 54 failed` / `architecture 9/10`
figures are **stale** — always re-measure.

## Node inventory (reproducible)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

## Repair queue (`SH-*` — proposed, sovereign authorizes)

Unchanged from the correction ledger, with one bucket explanation corrected:

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions | STALE_ASSERTION | **exhausted** (0 nodes left) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` helper rewrite | STALE_ASSERTION | **done** (PR #127) |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | `CapabilityRegistry` cycle detection | DRIFT | **RESOLVED — no defect** |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV/ARTIFACT → **tracked-artifact regression** | evidence attached by **#142**; disposition still sovereign |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` | DRIFT (high) | awaits architectural gate |
| `SH-08` | which activity surface is canonical? | CONTRADICTION | **sovereign decision** |
| `R1/R2/R3` | solspire recon error-contract drift | REAL_DEFECT | recorded, not started (separate workstream) |
| `F-01` | `test_no_firebase_persistence_in_gate` proxy invalidation | DRIFT | **sovereign decision** |
| `CE-01` | `test_autonomy.py` collection error (module/package collision) | CONTRADICTED | **sovereign decision** — autonomous mutation path |
| `CE-02` | `test_render_codex.py` collection error | **naming defect** | **repaired this pass** |

### Correction carried from this pass

`CE-01` and `CE-02` have been reported together as *"the two documented, pre-existing
collection errors"* in `AGENTS.md`, `PARKING_LOT.md`, `CONTINUATION_LEDGER.md`,
`M01-CLOSURE.md`, and `P1-A_FINAL.md`. **They are not the same kind of thing.** `CE-01` is a
genuine import collision on the autonomy governance surface and needs a sovereign decision;
`CE-02` was a file-naming error with no dependency defect at all. Those five documents are
**not** edited here (out of this workstream's scope; two are other workstreams' artifacts) —
recorded for the sovereign.

## Next bounded task

Reconstruct first. The gate-hygiene queue is now thin: every remaining `SH-*` item is gated on
a **product, architectural, or sovereign decision**, not on engineering effort. Candidates, in
order:

1. **`SH-05`** — `#142` has now attached provenance and reclassified rows 47–48 as a
   *tracked-artifact regression*. If the sovereign picks `SH-05a` (retire) or `SH-05b`
   (restore), that becomes a bounded hygiene task. **Do not pick a disposition.**
2. **`F-01`** — proxy invalidation in `test_no_firebase_persistence_in_gate`. Needs the
   sovereign to say whether the intent is to be re-expressed against a new proxy or the
   coverage waived. **Do not silently loosen.**
3. **Verify a merged PR** — if `#142`–`#148` merge, re-measure the fingerprint and confirm
   the claimed deltas landed (each PR states its own delta; an unlanded delta is a finding).

**Do not** pick SG-04 (`SH-08`) — investigated twice, conclusion recorded in
`…/baseline-ledger-correction-01/EVIDENCE.md` §2 and `…/BASELINE_TEST_DEBT_CLASSIFICATION.md`
§11.1. Re-opening it without new evidence is the repetition failure mode the contract forbids.

## Boundaries

Test-hygiene workstream holds **no** authority over merge, authorization, identity,
authority-model, constitutional architecture, or `web/public_prism/**` capability changes. It
must not create a second mutation or authorization path. This pass touched **no** executable
code: one file rename in `tests/` plus documentation.
