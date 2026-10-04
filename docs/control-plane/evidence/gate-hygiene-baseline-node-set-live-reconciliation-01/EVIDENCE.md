# EVIDENCE — gate-hygiene/baseline-node-set-live-reconciliation-01

Bounded workstream: **live reconciliation of the recorded baseline test-debt node set** on
`main`, plus a **fail-closed guard on the fingerprint derivation** that was silently
under-reporting the debt.

The recorded fixture `tests/fixtures/baseline_node_set.txt` had drifted: it still carried 8
nodes that later merges had repaired, so the "canonical" fingerprint described debt that no
longer exists and masked the one collection error. This pass re-measures `main`, reduces the
recorded set to the nodes a live run actually reports, preserves the superseded set as an
archival fixture, and hardens the extractor so a log missing pytest's `ERROR` summary line
fails closed instead of fingerprinting a subset.

## 1. Reconstruction (live evidence)

| item | value |
|---|---|
| canonical repo | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` |
| BASE_MAIN (origin/main) | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| clone | **not** shallow (`git rev-parse --is-shallow-repository` -> `false`), 2005 commits |
| open PRs at start | 3 — #262 (evidence-only, this workstream's carrier), #263 (Gate-2 deploy fetch), #264 (`configure_routers` idempotency) |
| working tree at start | carried the fixture reduction + hardening edits (this pass) |

Observation timestamp: `2026-10-04T17:0xZ` (automation run).

## 2. The recorded set was stale — 8 entries now pass

A live full-suite run on `main` `1b7c089` reports **10** failing/error nodes, not the 18 the
fixture recorded. Every one of the 8 removed entries was verified **passing in isolation** in
this environment (non-shallow clone, `pyyaml` present):

```
python -m pytest \
  tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified \
  tests/test_authority_api_enterprise_boundary.py \
  tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection \
  tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write \
  tests/test_spiral_grove_registry.py \
  tests/test_upstream_causal_continuity_01.py::test_api_approval_does_not_create_enterprise_authorization \
  -q
-> 17 passed
```

The removed entries are: the `agents_md_encoding_adjudication` divergent-file node, both
`authority_api_enterprise_boundary` nodes, `solariun_thread_navigation_01`, the
`solspire_r2_github_mutation` node, both `spiral_grove_registry` nodes, and
`upstream_causal_continuity_01`. Their origin is preserved in
`tests/fixtures/superseded_baseline_node_set_18.txt` (untracked -> now added) rather than
deleted, so the superseded pair stays reproducible from an era-correct set.

## 3. The reduced set is live-accurate — same pair from fixture and from a real run

| derivation | outcomes fingerprint | node-set fingerprint |
|---|---|---|
| `python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt` | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |
| live full-suite run on this branch (`-rEf`) | `9a54f5b4…` | `124bfdfd…` |

They agree. The fixture therefore records the set a run actually produces, which is the
property the fingerprint is supposed to carry.

Live run: **9 failed / 1419 passed / 20 skipped / 1 error** (~125s). The error is the
documented `tests/test_autonomy.py` collection error (`weaver.autonomy` module/package
collision, CE-01). The 9 failures are the classified product/architecture/sovereign items
already recorded in PR #262 §4 (`SH-06` steward filter x3, `SH-07` shared-session key,
`F-01` proxy-invalidation, R1/R3 governance+contract nodes, and the W1 identity DRIFT node).
**No node was reclassified and no failure was repaired by this pass** — the change is to what
is *recorded*, not to what passes.

## 4. The derivation had a silent subset hazard — now fail-closed

The documented evidence command was `... -rf`. pytest's default is `-r fE`; `-rf` alone
**suppresses the `ERROR` summary lines**, so a collection error is invisible to a line-based
extractor. Measured on the same run:

```
... -rf   -> "failing/error nodes : 9 (9 failed, 0 error)"   # error line absent
... -rEf  -> "failing/error nodes : 10 (9 failed, 1 error)"  # complete
```

The `-rf` log hashed to `7d1bf895…` — a **subset** fingerprint that looked well-formed. A
future pass that recorded it would have silently dropped the collection error from the debt
record. `scripts/baseline_fingerprint.py::extract` now raises `ValueError` when the summary
line reports more failures/errors than the log carries `FAILED`/`ERROR` lines, and
`summary_counts` anchors on the `in <n>s` duration (optionally followed by a `(H:MM:SS)`
suffix) so a synthetic fragment is not mistaken for a summary.

Negative control (the guard must reject the exact shape `-rf` produces):

```
python scripts/baseline_fingerprint.py /tmp/verify_suite.log   # a -rf log
-> ValueError: summary reports 9 failed / 1 error(s), but the log carries 9 FAILED / 0 ERROR
   line(s). Re-run with `-rEf`; ...      rc=1
```

Positive control (a complete log parses):

```
python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt   -> rc=0
```

Both controls are pinned by tests, so the guard cannot be disarmed by editing the workflow or
the script without failing CI:
`test_log_missing_an_error_line_is_rejected_not_under_reported` (negative) and
`test_complete_log_is_accepted` (positive).

## 5. Verification battery

| gate | command | measured |
|---|---|---|
| fingerprint tests | `python -m pytest tests/test_baseline_fingerprint.py -q` | **24 passed** (19 before; +5) |
| architecture | `python -m pytest tests/architecture -q` | **11 passed** (11/11) |
| full suite (this branch) | `... tests/ -q --continue-on-collection-errors -rEf` | **9F / 1419P / 20S / 1E**, node set `9a54f5b4…` |
| regression boundary | node-set vs `main` | **identical** (10 nodes); `+5 passed` is exactly the 19 -> 24 test addition |
| `api/main.py` | `wc -l` + `python -m py_compile` | **2582 / 2600**, compiles OK (untouched) |
| CP10 mutation boundary | `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, rc 0 |
| superseded pair | `python scripts/baseline_fingerprint.py tests/fixtures/superseded_baseline_node_set_18.txt` | `6c7bf821…` / `2bc35996…` (as documented) |

## 6. Files changed

| file | change |
|---|---|
| `scripts/baseline_fingerprint.py` | `summary_counts()` + summary/parse mismatch guard in `extract()`; duration-anchored summary regex |
| `tests/test_baseline_fingerprint.py` | 19 -> 24 tests: two guard controls (negative/positive) plus archival-fixture tests for the superseded 18-node set |
| `tests/fixtures/baseline_node_set.txt` | reduced 18 -> 10 nodes to the live set |
| `tests/fixtures/superseded_baseline_node_set_18.txt` | **added** — era-correct archival set |
| `MISSION.md`, `NEXT_AGENT.md`, `.bootstrap/01_STATE.md`, `docs/phase1/CONTINUATION_LEDGER.md` | Repository Health / fingerprint sections reconciled to the measured pair; prior measurements marked superseded |

## 7. Remaining uncertainty

- **Environment sensitivity of counts is unchanged.** The passed count moves with the number
  of tests present (`1414` on `main` vs `1419` here); only the failing/error **node set** is
  the load-bearing invariant, and it is identical. A shallow clone additionally reports
  `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` (clone-depth dependent) —
  attributed to clone depth, not regression (PR #262 §9.2).
- **The 9 failures are untouched** and each remains a product/architecture/sovereign decision
  (PR #262 §4). This pass changes the debt *record*, not the debt.
- Nothing here is a production claim.

## 8. Classification and disposition

**VERIFIED (reconciliation)** — the recorded node set is live-accurate, the superseded pair is
reproducible from an archival fixture, and the derivation fails closed on the subset hazard,
with a negative control proving it detects the defect it claims to detect.

Authorization required: sovereign review -> merge. No merge, no push to `main`.

_Evidence written by an AI agent (OpenHands) on behalf of the sovereign._
