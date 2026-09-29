# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.

## Fingerprint (measured, not remembered)

```
main 67a660c : 54 failed / 964 passed / 10 skipped / 2 collection errors   (56 nodes)
architecture : 11/11
py_compile api/main.py : pass    (api/main.py = 2519 / 2600 lines)
vite build   : environment-blocked (no npm registry access)
```

Re-measure at the start of every pass; the automation contract's `main := 6038989` /
`804 passed / 12 skipped` / `architecture 9/10` figures are stale.

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
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **6 / 35 repaired** (SCI/nexus family) |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |

## Next bounded task

Continue `SH-02`: the next batch of stale string assertions. Suggested dense groups
(all pre-classified `STALE_ASSERTION`, all test-only):

- `test_prism_pass_c_surface_ownership.py` (6 nodes)
- `test_ais_w2_living_gate_grove_handoff.py` (6 nodes)
- `test_solariun_experience_consolidation_01.py` (3 nodes)

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and
run a negative control proving the repaired assertion can still fail. Test-only edits;
never touch `api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.

## Open PRs

`0` at `67a660c` (PR #122 merged). This pass opens a new bounded PR.

## Boundaries

Test-hygiene workstream holds **no** authority over merge, authorization, identity,
authority-model, or constitutional architecture. It must not create a second mutation or
authorization path (`examples: CP10 boundary judge`, `APS`/`ASI` status surfaces).
