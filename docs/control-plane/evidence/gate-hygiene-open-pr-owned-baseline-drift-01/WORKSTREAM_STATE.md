# WORKSTREAM_STATE — gate-hygiene/open-pr-owned-baseline-drift-01

| field | value |
|---|---|
| base main | `441379913d1b03ceb6a5af45ea543ca6762cb482` |
| branch | `gate-hygiene/open-pr-owned-baseline-drift-01` |
| objective | reconcile the recorded baseline test-debt node set to a live `main` measurement; attribute the 7 newly-recorded nodes to their owner PRs; make the reconciliation compositional (era set ∪ open-PR-owned set) |
| change set | `tests/fixtures/baseline_node_set.txt` (10 → 17), `tests/fixtures/open_pr_owned_drift_node_set.txt` (new), `tests/fixtures/superseded_baseline_node_set_10.txt` (new archival), `tests/test_baseline_fingerprint.py` (guards), health docs, this evidence |
| architecture | 11/11 (`tests/architecture -q`) |
| fingerprint tests | 28 collected / 28 passed (24 before; +4 guard functions) |
| full suite (`main` baseline) | 16F / 1772P / 22S / 1E — 17 failing/error nodes (branch: 1776P, +4 new guards) |
| canonical fingerprint | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` (outcomes) / `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224` (ids) |
| superseded pair (10 nodes) | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` / `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |
| superseded pair (18 nodes) | `6c7bf8218fd1e0ae9bc970653e98c18b3a78b69a5c4920dac9f4747c033e4648` / `2bc35996b21de6529ffffab63446c8bd7295c388e841a2807101d189eaf7da01` |
| failure node-set delta | **none** — `tests/`, fixtures, docs only; no node enters or leaves the failing set |
| `api/main.py` | untouched, compiles, 2462 / 2600 |
| open PRs at pass start | 12 (#337–#358) |
| status | IMPLEMENTED — ready for sovereign review |

## Deterministic next action

- **Current state**: branch `gate-hygiene/open-pr-owned-baseline-drift-01` carries a bounded,
  test-side baseline reconciliation; 28/28 fingerprint tests pass; architecture 11/11.
- **Evidence**: `docs/control-plane/evidence/gate-hygiene-open-pr-owned-baseline-drift-01/EVIDENCE.md`.
- **Blockers**: none for this branch. The 3 `test_m02a_ci_gate_integrity.py::test_allowlist_*`
  failures remain `main` debt owned by open PR #354; the `test_autonomy.py` ERROR is the
  sovereign-reserved CE-01 collision.
- **Authorized next action**: sovereign review and merge of this PR. Then re-measure `main`
  and, with #347/#354/#355/#356 (drift-set owners) and #357 (repairs three era-set solspire
  nodes) merged, expect the recorded set to shrink — re-run the
  fingerprint pass rather than reuse this pair.
- **Forbidden**: merge, force-push, push to `main`, fixing the CP10 allowlist here, touching
  `weaver/autonomy`.
