# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> This supersedes the batch-2 state at
> `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-solariun-consolidation-01/WORKSTREAM_STATE.md`.

## Fingerprint (measured this pass, not remembered)

```
main 4164573                     : 39 failed / 1018 passed / 13 skipped / 2 errors   (41 nodes)
main 4164573 + this repair       : 36 failed / 1021 passed / 13 skipped / 2 errors   (38 nodes)
architecture                     : 11/11
py_compile api/main.py           : pass    (api/main.py = 2519 / 2600 lines)
vite build                       : environment-blocked (no npm registry access)
```

`main` advanced from `ee3fac1` to `4164573` (PR #128, `gate-l1.1-boundary-hardening`)
between the batch-2 pass and this one, and the measured counts moved with it — batch 2
recorded `48→45 failed`. **Always re-measure**; the automation contract's
`main := 6038989` / `804 passed` / `architecture 9/10` figures remain stale.

Reproduction (note: the two collection errors abort an unfiltered run, so they are
ignored explicitly rather than via `--continue-on-collection-errors`):

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -p no:cacheprovider \
  --ignore=tests/test_autonomy.py --ignore=tests/test_render_codex.py \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline to attribute a delta by *name*, never by
count alone.

## Classification ledger

`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
is the single source of truth for node→bucket assignment (51 nodes at `a26af408`).

Bucket counts at that pass: **STALE_ASSERTION 35**, **DRIFT 10**, **ENV/ARTIFACT 2**,
**REAL_DEFECT 1**, **COLLECTION_ERROR 2**.

Taxonomy note (resolved this pass, for whoever next reads the classification): nodes
**36, 37, 40, 41** were classified `DRIFT`, but **36 / 37 / 40 are `STALE_ASSERTION`** —
they are quote-style drift only (see below). **Node 41 is genuinely `DRIFT`** (copy change)
and stays out of `SH-02`. Use the bucket by its mechanism, not by its row position.

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **14 / 35 repaired** (batch 1: SCI/nexus 6; batch 2: solariun-consolidation 3; **batch 3: identity-spine 5**) |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) — needs a **helper rewrite**, not string edits | STALE_ASSERTION | not started — still the next dense bounded task |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `SH-08` | `/api/pulse/analyze` contradiction: `test_ais_w2_living_gate_grove_handoff.py` asserts present, `test_ais_capability_profile_onboarding.py` asserts absent | CONTRADICTION | **not `SH-02`** — needs a product/governance decision before any edit |
| `SH-09` | `NodeEntry.tsx` copy — `"Let's form your node."` vs rendered `See my shape →` (`test_identity_spine_w1.py`) | DRIFT | **not `SH-02`** — product presentation decision |
| `F-01` | `test_no_firebase_persistence_in_gate` — `sessionStorage` proxy no longer measures its "no cloud persistence" intent | DRIFT (proxy-invalidation) | **sovereign decision** — do not silently loosen |

## Batch 3 change (this pass)

`tests/test_ais_w8_canonical_identity.py` + `tests/test_identity_spine_w1.py` — 3 nodes,
5 assertions, `assert 'X' in src` → quote-agnostic `assert re.search(...)`. Pattern shape:
still requires the exact symbol, the exact route path, and the exact indexing relationship;
it only stops pinning *which* quote character the source author chose. Compensating negative
control added so the original `'"ais_capability_portfolio"' not in ais` intent survives.

Evidence: `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-identity-spine-03/EVIDENCE.md`
(9 negative + 8 positive controls, all pass).

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
assertions from the STALE_ASSERTION bucket. Do **not** fold `SH-08` or `SH-09` into it —
both are product decisions dressed as test repairs, which is exactly the scope creep
`SH-02` is bounded against.

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and run
a negative control proving the repaired assertion can still fail. Test-only edits; never
touch `api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.

## Open PR boundary

Only open PR is **#129** (`gate-hygiene/baseline-ledger-correction-sg04-01`, ready). It is
**not** to be widened. This batch lives on its own branch
(`gate-hygiene/baseline-stale-assertion-repair-identity-spine-03`) and its own PR.
Human-sovereign merge only; no merge, no `main` push, no force-push from this workstream.
