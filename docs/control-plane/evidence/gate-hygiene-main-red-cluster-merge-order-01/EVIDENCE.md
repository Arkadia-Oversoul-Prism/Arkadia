# Main-red cluster — duplicate-file merge order (gate-hygiene)

**Base:** `main` @ `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Head:** `gate-hygiene/main-red-cluster-merge-order-01`
**Environment:** Python 3.13 · pytest · git · `PYTHONPATH=archive/legacy_python`
**Mutation:** none to product/test/workflow/authority surfaces — evidence + one read-only guard.

This record answers one question left open by the composability passes (#358/#361/#376):
the open PRs that repair the `main`-red node set overlap on `AGENTS.md` (a tail append, benign)
and on one **load-bearing test+asset pair** (#354 ⊇ #384). It proves that overlap is a
*duplicate*, not a conflict, and that the two PRs are order-independent.

---

## 1. Live reconstruction (this pass)

| item | value |
|---|---|
| BASE_MAIN (measured) | `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` |
| full-suite failing/error nodes | **16** (15 failed, 1 error) |
| outcomes fingerprint | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` |
| ids fingerprint | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |
| architecture suite | **11 passed** |
| `api/main.py` | 2450 lines (budget 2600) — `py_compile` OK |
| AGENTS.md mojibake (U+0400–U+04FF) | 0 |

The 16-node baseline and its outcomes/ids fingerprints match PR #375/#376's record
(`bfcfe592…` / `ed5e4714…`) byte-for-byte — this pass re-derived them independently rather
than inheriting them.

## 2. Every baseline node is owned by an open PR (no unowned work)

| failing/error node | owner PR |
|---|---|
| `tests/test_autonomy.py` (collection ERROR) | CE-01 module-vs-package collision — **reserved to sovereign**, not a PR target |
| `tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | #356 |
| `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` | #356 |
| `tests/test_steward_filter.py::test_allows_mythic_with_action` | #365 |
| `tests/test_steward_filter.py::test_compress_to_choices` | #365 |
| `tests/test_ais_capability_profile_onboarding.py::…home_is_offer_led…` | #347 |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | **sovereign-decision placeholder** (F-01; documented in-test, not stale drift) |
| `test_oracle_runtime_uses_the_shared_session_key` (+ other AIS/frontend copy pins) | #363 |
| 3 CP10 allowlist nodes (`test_m02a_ci_gate_integrity.py`) | #354 (+ #384 for the browser asset) |

Conclusion: **no genuinely unowned baseline failure exists.** Any new safety work must be a
continuity/merge-order artifact, not a repair.

## 3. The duplicate-file finding (#354 ⊇ #384)

`gh`'s file list for both PRs, and the git blobs, agree:

| file | #384 `f744e36b` | #354 `b6eec36b` |
|---|---|---|
| `web/public_prism/public/firebase-config.js` | `d9973c17ad63e8411926d8bbce294ca0c2931551` | `d9973c17ad63e8411926d8bbce294ca0c2931551` |
| `tests/test_frontend_script_assets_resolve.py` | `17be550d18b34392baecbdbe40dead112e658096` | `17be550d18b34392baecbdbe40dead112e658096` |

The blobs are **byte-identical**. PR #354's body states it deliberately
"composes PR #384's browser-asset repair here, so a single sovereign merge of #354 closes
CP10 on main."

Also verified: `main` is an ancestor of **both** #384 and #354 (`git merge-base --is-ancestor`),
so neither is stacked on the other — they are independent branches off `main`.

### Order-independence (proven by real merge, not by patch)

Detached worktree at `origin/pr384`, then `git merge origin/pr354`:

```
Merge made by the 'ort' strategy.
 AGENTS.md                                                |  91 +++
 .../gate10-cp10-allowlist-deploy-surface-01/EVIDENCE.md  | 875 ++++
 .../WORKSTREAM_STATE.md                                  | 182 +++
 scripts/cp10_mutation_boundary_policy.py                 |  12 +
 4 files changed, 1160 insertions(+)
```

Zero conflicts; the two shared blobs did not appear in the stat because they are identical
(same blob → nothing to merge). So **#384 then #354 and #354 then #384 both produce the same
tree**: #384's repair + #354's `deploy/` allowlist + #354's two evidence docs.

## 4. The composed tree is green on the CP10 surfaces

On `origin/pr354` (which already carries the composed change set):

```
python -m pytest tests/test_m02a_ci_gate_integrity.py tests/test_frontend_script_assets_resolve.py -q -rEf
67 passed
```

```
git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)   # exit 0
```

On `main` the same three allowlist nodes fail (`deploy` prefix rejected), so #354 is the
carrier of that repair.

## 5. What this does **not** claim

- **Not** a merge and **not** an authorization. The sovereign decides merge order/timing.
- **Not** a live-measurement of the composed full suite. Only the CP10 surfaces (#354's own
  scope) were executed here; the composed **node set** is #376/#377's measurement, not re-run.
- The `test_autonomy.py` collection ERROR and the Living-Gate F-01 node are **out of scope**
  by design — the first is reserved to the sovereign, the second awaits a sovereign decision.

## 6. Recommended merge order (advisory, sovereign decides)

Either order is safe. Recommended to avoid the duplicate PR being merged to no effect:

1. **#384** first (closes the CP10 browser gate — the runtime red).
2. **#354** second (adds the `deploy/` allowlist; its embedded copies of #384's files become
   no-ops).

Merging **#354 first** and then **#384** also works, but #384 then contributes nothing beyond
its (identical) content already present — merging it would be a no-op commit. A reviewer who
merged #354 first should expect #384 to show zero diff and can close it instead.

## 7. Provenance

- `docs/control-plane/evidence/gate-hygiene-main-red-cluster-merge-order-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate-hygiene-main-red-cluster-merge-order-01/merge_order_manifest.json`
- `tests/test_main_red_cluster_merge_order.py` (live guard + negative control)
