# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> This supersedes the batch-1 state at
> `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-sci-nexus-01/WORKSTREAM_STATE.md`.
>
> Per-pass heartbeat record: `HEARTBEAT.md` (same directory) — reconstruct, classify,
> precondition corrections, negative controls, classification, credential boundary.

## Fingerprint (measured this pass, not remembered)

```
main ee3fac1  (test reverted) : 48 failed / 968 passed / 12 skipped / 2 errors   (50 nodes)
main ee3fac1  + this repair   : 45 failed / 971 passed / 12 skipped / 2 errors   (47 nodes)
  + binding-guard node (§3.4)  : 45 failed / 972 passed / 12 skipped / 2 errors   (48 nodes)
architecture                  : 11/11
gate integrity + architecture : 60 passed
py_compile api/main.py        : pass    (api/main.py = 2519 / 2600 lines)
vite build                    : environment-blocked (no npm registry access)
```

Note: `main` advanced from `67a660c` to `ee3fac1` (PR #124 merged) between the batch-1
pass and this one, and the measured counts moved with it — batch 1 recorded
`54 failed / 964 passed`. Always re-measure; the automation contract's
`main := 6038989` / `804 passed / 12 skipped` / `architecture 9/10` figures are stale.

## Node inventory (reproducible)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline to attribute a delta by *name*, never
by count alone — counts move when tests are added.

## Classification ledger

`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
is the single source of truth for node→bucket assignment (51 nodes at `a26af408`).

Bucket counts at that pass: **STALE_ASSERTION 35**, **DRIFT 10**, **ENV/ARTIFACT 2**,
**REAL_DEFECT 1**, **COLLECTION_ERROR 2**.

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **9 / 35 repaired** (batch 1: SCI/nexus 6; batch 2: solariun-consolidation 3) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) — needs a **helper rewrite**, not string edits | STALE_ASSERTION | not started — see below |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `F-01` | `test_no_firebase_persistence_in_gate` — `sessionStorage` proxy no longer measures its "no cloud persistence" intent (gate has 0 firebase refs; storage is ephemeral handoff) | DRIFT (proxy-invalidation) | **sovereign decision** — do not silently loosen |

## Next bounded task

`SH-02b` — `tests/test_prism_pass_c_surface_ownership.py` (6 nodes). This is **not** a
string-repoint job: `_block(view)` (`:20-24`) regex-matches
`{view === '<v>' && (\(.*?\)\n\)}` against `App.tsx`, but `App.tsx` now resolves views
through a `requested`/`next` mapping with explicit redirects (`App.tsx:111-120`). Views
whose JSX block survives (`personal-echofeild`, `echofeild-matrix` — `App.tsx:152-153`)
and views that are redirected to another surface with a section (`knowledge-os`, `codex`
→ `solariun` + `initialSection="knowledge"`) must be asserted by **two different
mechanisms**. Rewrite the helper to model both, and keep every node able to fail
(negative control per node, as in batch 2 §3.3).

Alternative if `SH-02b` scope looks ambiguous: the next dense batch of plain string
assertions from the STALE_ASSERTION bucket.

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and
run a negative control proving the repaired assertion can still fail. Test-only edits;
never touch `api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.