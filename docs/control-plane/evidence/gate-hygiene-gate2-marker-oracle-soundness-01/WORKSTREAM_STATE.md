# WORKSTREAM_STATE — gate-hygiene/gate2-marker-oracle-soundness-01

Observation time: 2026-10-09T01:2xZ
Base main: `24a00f856a0286cbb464a4b585117dd57a2646fa`
Branch: `gate-hygiene/gate2-marker-oracle-soundness-01`
PR: #366 (base `main`; do not pin the moving head - the PR owns its head)

## Current state

| field | value |
| --- | --- |
| status | IMPLEMENTED (awaiting sovereign review; not VERIFIED) |
| gate | GATE-02 production parity observation |
| changed paths | `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py`, `docs/control-plane/evidence/gate-hygiene-gate2-marker-oracle-soundness-01/` |
| product code | none |
| `api/main.py` | untouched (budget irrelevant to this pass) |

## Boundary as re-derived this pass (post-repair)

```
main -> deployment identity   VERIFIED  (deploy 6939001431, sha == main 24a00f85)
deployment build output       BLOCKED   (Vercel Deployment Protection / SSO)
alias reachable               VERIFIED  (HTTP 200)
alias -> deployment SHA       UNKNOWN   (immaterial: candidates share frontend source)
build <-> source lineage      VERIFIED  (source closed; marker set NOT observed)
marker-set oracle             NOT OBSERVED (artifact is 'console'; markers describe 'arkadia-prism')
browser-rendered UI           UNKNOWN
production acceptance         NOT CLAIMED (human authority)
```

The pre-repair harness fused source closure and the marker claim into one `VERIFIED`,
so an absent marker set was reportable as agreement. That verdict is now unreachable
by construction (negative control in the test file).

## Pass 2 — residual soundness gap repaired (2026-10-09)

Independent verification of the PR head `af496f2` found the same defect class surviving
at the report call site: `report.get("deployed_app") or MARKER_APP` coerced `None`
(no observable deployment) to `MARKER_APP`, making the classifier's `NOT OBSERVED`
branch unreachable. The live run therefore printed `marker-set oracle CONTRADICTED`
for an *undetermined* app instead of `NOT OBSERVED`. The SG-04 link had the same
class of phantom verdict: `regression: true` for an artifact of another (or no) app.

Repair: pass the app identity through unchanged; move the SG-04 verdict into a tested
`classify_sg04` predicate that reports `regression: None` unless the artifact is the app
the literals describe. Tests **32 passed** (29 + 3); both new source-level controls are
non-vacuous (restoring the defect reddens them, 2F/30P). Architecture **11 passed**.

| field | value |
| --- | --- |
| status | IMPLEMENTED (awaiting sovereign review; not VERIFIED) |
| marker-set oracle (live) | `NOT OBSERVED (served app undetermined; markers describe 'arkadia-prism')` |
| sg04 (live) | `evaluable: False`, `regression: None` |

## Pass 1 — independent reconciliation of PR #361 (measured, not inherited)

PR #361 is **open** (head `04857ce2`, base `44137991`). It records a canonical 17-node
baseline fingerprint. This pass measured live `main` independently and reconciles:

| claim (#361) | live measurement (this pass) | verdict |
| --- | --- | --- |
| 17 nodes, `16 failed / 22 skipped / 1 error` | `16 failed, 1782 passed, 22 skipped, 1 error` | **CONFIRMED** |
| outcomes `26c2b4c7b5efb56d…` | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` | **CONFIRMED** |
| ids `571e599f91e680fe…` | `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224` | **CONFIRMED** |
| era 10-node fixture is a strict subset of live | `era ⊂ live = True`, 0 extra | **CONFIRMED** |
| the 7 delta nodes are open-PR-owned (#347/#355/#356/#354) | all four owners open; node list matches exactly | **CONFIRMED** |

Method: `python -m pytest tests/ -q -rEf --continue-on-collection-errors` on
`main` `24a00f85`; fingerprint via `scripts/baseline_fingerprint.py` (17 nodes,
16 failed / 1 error). Set algebra computed directly from the log vs
`tests/fixtures/baseline_node_set.txt`.

Reproduce:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors | tee /tmp/live.txt
python scripts/baseline_fingerprint.py /tmp/live.txt --json
```

No unexplained drift. #361's figures are reproducible from current `main` and are not
inherited from its own recorded prose.

## Next bounded task (classified, not started)

Gate-2 closure remains blocked at `deployment build output` (provider auth). Any
Prism-surface observation requires either a Vercel credential, Deployment Protection
relaxed, or a runtime observation from an operator with access. Repeating the pass
cannot move `BLOCKED`/`UNKNOWN` to `VERIFIED`.

## Pass 3 — ordering fault of the same defect class (2026-10-09)

Head `b7eee811` → `48b0f14b` (PR #366).

- Defect: `classify_sg04` read `report.get("deployed_app")` at line 469 while the key was
  assigned at line 481. The classifier always saw `None`, so its evaluable branch was
  unreachable and a genuine SG-04 regression could never be reported. The §7 tests pinned
  call-site *presence*, not ordering — 32 tests were green on a vacuous call.
- Repair: resolve `deployed_app` once before any classifier reads it; pass the local
  binding to `classify_sg04`; closure reuses the same binding.
- Guard: `test_deployed_app_is_resolved_before_the_sg04_classifier_reads_it` + negative
  control `test_ordering_detector_flags_the_defective_order`.
- Measured: 34 passed; pre-repair order → 1F/33P (non-vacuous); `tests/architecture` 11
  passed; `py_compile` OK.
- CI at `48b0f14b`: `Full-history secret scan`, `beta-beta-01-english`,
  `beta-beta-02-hausa`, `bundle-beta-evidence`, `native-arkadia-golden-workflow` → pass.
  `Vercel – arkadia-prism` / `Vercel – console` → fail (build rate limit) — pre-existing on
  `main`, not attributable.
- Status: READY FOR SOVEREIGN MERGE. Gate-2 closure itself remains `BLOCKED` on provider
  auth (Vercel SSO); repository-source instrument fix only.

## Authority boundary

Sovereign merge authority. No merge performed; no push to `main`; no force-push.
