# WORKSTREAM_STATE — gate-hygiene/gate2-marker-oracle-soundness-01

Observation time: 2026-10-09T01:2xZ
Base main: `24a00f856a0286cbb464a4b585117dd57a2646fa`
Branch: `gate-hygiene/gate2-marker-oracle-soundness-01`
PR: #366 (head `589eca24e378b6385448ab672abfca074aa32c21`, base `main`)

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

## Authority boundary

Sovereign merge authority. No merge performed; no push to `main`; no force-push.
