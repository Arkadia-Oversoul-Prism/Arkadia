# WORKSTREAM_STATE — gate-hygiene/baseline-node-set-live-reconciliation-01

| field | value |
|---|---|
| base main | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| branch | `gate-hygiene/baseline-node-set-live-reconciliation-01` |
| objective | reconcile the recorded baseline test-debt node set to a live `main` measurement; preserve the superseded set; make the fingerprint derivation fail closed on the `-rf` subset hazard |
| change set | fingerprint script + tests + fixture (18 -> 10 + archival) + health docs |
| architecture | 11/11 |
| full suite (branch) | 9F / 1419P / 20S / 1E (~125s) |
| failure node-set sha256 | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` (outcomes) / `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` (ids) |
| superseded pair (18 nodes) | `6c7bf821…` / `2bc35996…`, reproducible from `tests/fixtures/superseded_baseline_node_set_18.txt` |
| fingerprint tests | 24 passed (19 before; +5: two guard controls + archival-fixture tests) |
| `api/main.py` | untouched, compiles, 2582 / 2600 |
| CP10 mutation boundary | PASS (rc 0) |
| regression | node set identical to `main`; `+5 passed` = 19 -> 24 in the fingerprint file |
| status | **VERIFIED** (reconciliation + fail-closed guard with negative control) |
| authorization | sovereign merge only |

## What changed and why

The recorded fixture `tests/fixtures/baseline_node_set.txt` carried **18** nodes; a live run
on `main` reports **10**. Eight recorded entries had been repaired by later merges while the
fixture kept them as debt. Each of the 8 was verified passing in isolation (17 passed), so the
reduction is measurement-backed, not a clone-depth artifact. The superseded set is retained as
`tests/fixtures/superseded_baseline_node_set_18.txt` so the prior pair stays reproducible.

The documented command used `-rf`, which suppresses pytest's `ERROR` summary lines: the same
run then fingerprints **9** nodes (`7d1bf895…`) instead of 10, silently dropping the
`test_autonomy.py` collection error. `extract()` now fails closed on that mismatch and
`summary_counts()` anchors on the `in <n>s` duration. Two tests pin the guard: a negative
control feeding the exact `-rf` shape (must raise) and a positive control (must parse).

## Next bounded task (deterministic resume block)

- **State**: baseline node set reconciled to live; derivation hardened; superseded pair
  preserved; architecture/CP10/compile gates green.
- **Evidence**: `EVIDENCE.md` in this dir.
- **Blockers**: none for this workstream. The 9 live failures each require a
  product/architecture/sovereign decision (PR #262 §4) — **not** repair-by-test-edit. PR #262
  is the evidence-only carrier for that classification; PR #264 implements #262 §10.6
  (test-isolation hardening) as a separate bounded task.
- **Authorized action**: sovereign review of this PR -> merge. Then a *separately authorized*
  workstream may take `SH-06` (steward filter policy) or `SH-03` (DERIVED contract). Re-pulse
  the Gate-2 deployment boundary with `scripts/gate2_production_observation.py` once the
  provider rate limit expires.
- **Forbidden**: merging; pushing to `main`; widening this PR; "fixing" a classified failure
  by editing a test literal without a decision.
- **Completion condition**: this PR merged -> next heartbeat reconstructs from live evidence.

_Workstream state written by an AI agent (OpenHands) on behalf of the sovereign._
