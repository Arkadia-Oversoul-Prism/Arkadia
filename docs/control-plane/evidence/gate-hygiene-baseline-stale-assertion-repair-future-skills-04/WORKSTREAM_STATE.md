# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> This supersedes the batch-3 state at
> `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-identity-spine-03/WORKSTREAM_STATE.md`.

## Fingerprint (measured this pass, not remembered)

```
main 4164573                     : 39 failed / 1020 passed / 11 skipped   (39 nodes)
main 4164573 + batch 4           : 38 failed / 1021 passed / 11 skipped   (38 nodes)
architecture                     : 11/11
py_compile api/main.py           : pass    (api/main.py = 2519 / 2600 lines)
vite build                       : environment-blocked (no npm registry access)
```

Measured with the two collection errors ignored explicitly (they abort an unfiltered run):

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -p no:cacheprovider \
  --ignore=tests/test_autonomy.py --ignore=tests/test_render_codex.py \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline to attribute a delta by *name*, never by
count alone.

**Ledger counts are not counts-of-failures.** The classification ledger fixes 51 classified
nodes at `a26af408`; the live run measures fewer because PR #127 (SH-02b) removed 6 and PR
#130 (batch 3, in flight) removes 3 more. Re-measure; do not decrement the ledger.

## Classification ledger

`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
is the single source of truth for node→bucket assignment.

Bucket counts at that pass: **STALE_ASSERTION 35**, **DRIFT 11**, **ENV/ARTIFACT 2**,
**REAL_DEFECT 1**, **COLLECTION_ERROR 2**.

Taxonomy note (still binding): nodes **36 / 37 / 40 are `STALE_ASSERTION`** despite their row
position (quote-style drift only); **node 41 is genuinely `DRIFT`** and is registered as
`SH-09`. Use the bucket by its mechanism, not by its row position.

## Ledger correction — SH-02b is CLOSED (stale prose, corrected here)

The batch-3 `WORKSTREAM_STATE.md` and the `SH-02` row state "**SH-02b not started — still the
next dense bounded task**". **That is stale.** Live evidence this pass:

```
PR #127 (SH-02b) : MERGED
main 4164573     : tests/test_prism_pass_c_surface_ownership.py -> 9 passed / 9
```

The failed-assertion count in that module is **0** on current `main`; nodes 13–18 of the
classification ledger are repaired. PR **#130** carries the authoritative ledger correction
for the classification ledger itself; the correction is repeated here so a reader of the batch
state is not misled in the interim. **The independent re-measurement agrees with PR #130** —
no drift between PR #130's claim and live evidence.

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **15 / 35 repaired** (batch 1: SCI/nexus 6; batch 2: solariun-consolidation 3; batch 3: identity-spine 5 (PR #130, in flight); **batch 4: future-skills 1**) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) | STALE_ASSERTION | **CLOSED — merged via PR #127, 9/9 on `main`**. The batch-3 "not started" prose was stale. |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `SH-08` | `/api/pulse/analyze` contradiction, plus the LivingGate family (nodes 3–8) | CONTRADICTION | **not `SH-02`** — **escalated, OFF-LIMITS per PR #129**. Do not repair or touch. |
| `SH-09` | `NodeEntry.tsx` copy (`test_identity_spine_w1.py`, ledger row 41) | DRIFT | **not `SH-02`** — product presentation decision. Attempted and **reverted** this pass. |
| `F-01` | `test_no_firebase_persistence_in_gate` proxy-invalidation | DRIFT (proxy) | sovereign decision — do not silently loosen |

New node flagged this pass, **not** in the original ledger and **not** repaired:

- `test_solspire_p1_experience_01.py` (nodes 22–23, STALE_ASSERTION). The panel survives
  (`data-testid="solariun-arkana-context-pack"`, label now `CURRENT CONTEXT`) but both
  governance literals are absent repo-wide (`"CONTEXT PACK (explicit)"`,
  `"Not an authorization authority"`). Re-pinning the copy would restate a boundary the UI no
  longer states → **product decision, classify as `SH-10` (proposed, unstarted)**. Do not fold
  into `SH-02`.

## Batch 4 change (this pass)

`tests/test_ais_w6_future_skills_challenge.py::test_w6_is_self_guided_and_timed` — one node,
one assertion: `"60-minute challenge"` → `"self-guided practical challenge"`. The behavioural
constraint (`LIMIT_MS = 60 * 60 * 1000`) is unchanged and still asserted. Negative control and
base-failure control recorded in `EVIDENCE.md`.

Deliberately small: every other `STALE_ASSERTION` node is owned by a merged PR (#127), an open
PR (#130), or a product decision (`SH-08`, `SH-09`, `SH-06`, `SH-10`). Padding the batch with a
product call is the exact scope creep `SH-02` is bounded against.

## Next bounded task

`SH-02` batch 5 is **thin** — the remaining unowned `STALE_ASSERTION` nodes are few. Candidates,
in preference order:

1. `test_prism_interior_shell.py` (nodes 10–12) — **only if** a surface-ownership determination
   is recorded first: the test pins `prism-primary-rail`; the shell now emits
   `novanet-primary-rail` and no longer lists `sci` / `knowledge-os`. Re-pointing the literal
   without deciding whether the rail rename is canonical would launder a contract change into a
   test repair. **Prefer to propose it as a bounded determination task, not a repair.**
2. Once PR #130 merges, the batch-3 nodes land and the `SH-02` count becomes comparable again.

Do **not** fold `SH-08` (escalated/off-limits), `SH-09`, `SH-10`, or `SH-06` into `SH-02` — all
are product decisions dressed as test repairs.

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and run a
negative control proving the repaired assertion can still fail. Test-only edits; never touch
`api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.

## Open PR boundary

Open PRs at this pass: **#129** (`gate-hygiene/baseline-ledger-correction-sg04-01`, ready,
mergeable/clean, not to be widened), **#130** (batch 3, in flight), and this branch's own PR
(batch 4). Human-sovereign merge only; no merge, no `main` push, no force-push from this
workstream. `main` is untouched by this pass.
