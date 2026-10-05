# EVIDENCE — gate-hygiene/independent-queue-verification-04

Independent, reproduction-first verification of the open PR cluster **#262–#266** against
`main`, performed from a clone that did **not** author any of those PRs. This pass makes
**no source, test, or policy change**. The only file added is this evidence directory.

## 1. Reconstruction (live evidence)

| item | value |
|---|---|
| canonical repo | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` |
| BASE_MAIN (origin/main) | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| latest commit subject | `Merge pull request #261 ... authority-boundary-control-case-identity-01` |
| open PRs | **5** — #262, #263, #264, #265, #266 (all `mergeable: true`, `mergeState: unstable`) |
| open issues (excl. PRs) | 3 — #209 (MIE MVP-01), #77 (CAL-10), #7 (A.I.S funnel) |
| observation timestamp | `2026-10-04T20:0xZ` (automation run) |

Each PR head carried two check-runs, both `success`: `Vercel Preview Comments` and
`Full-history secret scan`. PR #265's head **commit status** additionally shows
`Vercel – console` = `failure` — this is **pre-existing on BASE_MAIN** (build-rate-limit,
`?upgradeToPro=build-rate-limit`), not introduced by the PR.

## 2. Load-bearing measurement — full suite, `main` vs composed tree

Run in this environment (python 3.13), command:
`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors`

| tree | result | node set (outcomes) | node set (ids) |
|---|---|---|---|
| `main` @ `1b7c089` | **9 failed / 1414 passed / 20 skipped / 1 error** | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |
| composed tree `80a4b060…` | **9 failed / 1423 passed / 20 skipped / 1 error** | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |

**Zero regression.** The failure/error node set is **byte-identical** on both trees; the
`+9 passed` delta is fully attributed below. The skipped count is identical (20) and the
single collection error is identical (`tests/test_autonomy.py` —
`ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'`, the
pre-existing CE-01 module/package collision).

### 2.1 The `+9 passed` delta is exactly the cluster's new guard tests

Collected-ID diff (`--collect-only -q`), `main` 1442 ids vs composed 1451 ids —
**9 added, 0 removed**:

| new node | contributed by |
|---|---|
| `test_baseline_fingerprint.py::test_complete_log_is_accepted` | #265 |
| `test_baseline_fingerprint.py::test_live_node_set_is_a_proper_subset_of_the_superseded_18_node_set` | #265 |
| `test_baseline_fingerprint.py::test_log_missing_an_error_line_is_rejected_not_under_reported` | #265 |
| `test_baseline_fingerprint.py::test_recorded_set_excludes_the_live_reconciled_repairs` | #265 |
| `test_baseline_fingerprint.py::test_superseded_18_node_set_reproduces_the_superseded_pair` | #265 |
| `test_gate2_production_observation.py::test_deployments_are_fetched_unfiltered` | #263 |
| `test_gate2_production_observation.py::test_project_suffixed_production_labels_are_admitted` | #263 |
| `test_gate2_production_observation.py::test_suffixed_preview_label_is_not_admitted` | #263 |
| `test_nodes_composition_seam.py::test_configure_routers_is_idempotent` | #264 |

No test was removed, renamed, or turned green by weakening an assertion. #262 and #266 add
documentation only and contribute no collected node.

## 3. Fingerprint-convention reconciliation (resolves an apparent cluster contradiction)

Two conventions are in play and both are correct; they must not be read as drift.

| derivation | value on `main` @ `1b7c089` |
|---|---|
| `grep -E '^FAILED' \| sort \| sha256sum` (with pytest reason suffix) | `00b3984e7ad487f1c36e1449429834cdf398f5dde8d4591f4079942c180af48b` |
| `grep -E '^FAILED' \| sed 's/ - .*//' \| sort \| sha256sum` (the deprecated `-rf` subset) | `7d1bf895e134c701f65e4d6fcec0b2f99fbba1305184de65de004147173ac4b1` |
| `grep -E '^(FAILED\|ERROR)' \| sed 's/ - .*//' \| sort \| sha256sum` | `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` |
| ids only (`awk '{print $2}'`) | `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` |

- `00b3984e…` is **reproduced exactly** — it is the `-rEf`-derived FAILED-with-reason hash.
  PR #262's record is therefore reproducible, not stale.
- `7d1bf895…` is **reproduced exactly** — it is the `-rf` log's *FAILED-only* subset, which
  **omits the collection `ERROR` line** and so under-reports the node set. PR #265's
  classification of it as a subset is confirmed by direct reproduction.
- The canonical pair `9a54f5b4…` / `124bfdfd…` is reproduced by `scripts/baseline_fingerprint.py`
  and by the explicit derivation above.

## 4. PR #263 premise verified against the live API (it is a real harness bug)

`GET /repos/.../deployments?environment=Production` returns **only bare** `Production`
records, while an unfiltered page-walk over 500 deployments shows suffixed labels that the
server-side filter never returns:

| label | count over 500 |
|---|---|
| `Production – console` | 5 |
| `Production – arkadia-prism` | 4 |
| `Production` (bare, what the filter returns) | ≥5 |

**Reproduced end-to-end through the repo's own harness.** Running
`python scripts/gate2_production_observation.py` on `main` reports the newest Production
deploy as `57e67c534ff6` (id `6802423130`, `2026-10-02T06:06:28Z`); running the same script
from the composed tree (which carries #263) reports `fa1b40787544` (id `6838852040`,
`2026-10-04T08:42:37Z`) — an ancestor of `main`, 5 commits back. The unpatched harness
silently skipped the newer suffixed records, and #263 recovers them.

Consequence for the boundary classification: on the composed tree, `build ↔ source lineage`
moves from `UNKNOWN` to `VERIFIED (marker set matches, source closed)`. `main → deployment
identity` remains `STALE` because the newest Production deploy still predates `main`
(`fa1b4078` is 5 commits behind `1b7c089`).

## 5. Gate-2 boundary re-pulse (read-only, no credential)

`python scripts/gate2_production_observation.py`, composed tree, `main` @ `1b7c089`:

| boundary | classification |
|---|---|
| current main resolved | `VERIFIED` |
| main → deployment identity | `STALE` (newest Production deploy `fa1b4078` predates `main`) |
| deployment build output observed | `BLOCKED` (deployment-specific URL → HTTP 410 / SSO) |
| alias reachable | `VERIFIED` (`https://arkadia-prism.vercel.app/` → HTTP 200) |
| alias → deployment SHA binding | `UNKNOWN` (immaterial — all candidates share frontend source) |
| build ↔ source lineage | `VERIFIED` (marker set matches, source closed) |
| browser-rendered UI correctness | `UNKNOWN` |
| production acceptance | `NOT CLAIMED` (human authority) |

Marker-set lineage on the deployed bundle: `separate explicit downstream stages` = 1 (the
current wording) while `separate downstream stages` = 0 (the pre-change control) — the
presence/absence contrast holds. SG-04 `activity-runtime-draft.v1:` is present in both
source and the deployed artifact → **no SG-04 regression**.

## 6. Protected surfaces on the composed tree

| gate | command | measured |
|---|---|---|
| boot compile | `python -m py_compile api/main.py` | OK |
| line budget | `wc -l api/main.py` | **2582 / 2600** |
| architecture | `python -m pytest tests/architecture -q` | **11 passed** (11/11) |
| CP10 mutation boundary | `git diff main --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, rc 0 |
| #263 harness tests | `python -m pytest tests/test_gate2_production_observation.py -q` | **16 passed** |

## 7. Independent classification of the cluster

| PR | classification | basis |
|---|---|---|
| #262 | `VERIFIED` (evidence-only) | adds one evidence dir; its `00b3984e…` fingerprint reproduced exactly here |
| #263 | `VERIFIED` | real harness bug reproduced live; recovers `build ↔ source lineage` to `VERIFIED`; 3 new guard tests pass |
| #264 | `VERIFIED` | idempotency guard; negative control (revert to `main`) fails `assert 17 == 13`, proving the test is genuine |
| #265 | `VERIFIED` | node-set reconciliation reproduced (`9a54f5b4…` / `124bfdfd…`); 5 new guard tests pass |
| #266 | `VERIFIED` (evidence-only) | composition claim reproduced independently: queue order and shuffled order both yield tree `80a4b060fdc7900a99c455653ec38aef25d44c92` |

All five are conflict-free and order-insensitive against `main`. **Merging all five together
introduces zero test-debt regression** (§2) and moves the Gate-2 boundary forward (§4).

## 8. Remaining uncertainty (not resolved by this pass)

- The 9 pre-existing failures on `main` are unchanged by the cluster and are **not** repaired
  here (contract rule: do not fix unrelated baseline debt inside a verification pass).
  One of them, `test_steward_filter.py`, fails on a substantive predicate
  (`steward_filter("You have transcended")` returns non-`None`, expected `None`), not a
  literal pin. That is a **separate bounded workstream**, proposed below.
- `main → deployment identity` stays `STALE`: the newest Production deploy (`fa1b4078`)
  is 5 commits behind `main`. Closing that needs a deployment, which is human-authorized.

## 9. Proposed next bounded task (NOT executed — `NO SELF-EXPANSION`)

`test-hygiene/steward-filter-identity-predicate-01` — bound the substantive
`weaver/filters/steward.py` identity-claim defect (3 failing nodes) as its own workstream,
with a negative control. This is outside the current verification pass and requires
sovereign selection.

## 10. Status

`IMPLEMENTED` — evidence only. No source, test, or policy change. Authorization required:
sovereign review + merge of #262–#266 (order-insensitive).

## 11. Evidence commands (reproduce)

```bash
# main baseline
cd <clone> && git checkout main
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf \
  --continue-on-collection-errors | tee /tmp/main_suite.log
python scripts/baseline_fingerprint.py /tmp/main_suite.log

# composed tree (#262-#265)
git worktree add /tmp/wtcomp <composed-tree>
cd /tmp/wtcomp && PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf \
  --continue-on-collection-errors | tee /tmp/comp_suite.log
python <repo>/scripts/baseline_fingerprint.py /tmp/comp_suite.log

# delta attribution
python -m pytest tests/ --collect-only -q | grep '::' | sort > /tmp/main_ids.txt
comm -13 /tmp/main_ids.txt /tmp/comp_ids.txt

# gate-2 boundary (read-only, no credential)
GH_TOKEN=<token> python scripts/gate2_production_observation.py
```
