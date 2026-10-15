# L2 combined buyer-recon repair — #538 + #544

Observed 2026-10-15. One bounded unit. No merge authority.

## Outcome

**PASS (candidate only)** — one combined `update_entry` repair produced and
validated at an exact head. Ready for a separate acceptance decision. No merge.

| Item | Value |
|---|---|
| Baseline | `341867ebe4ea80ead557ca632707833b7620430a` (`main`, unmoved) |
| Candidate head | `8f4a6ea056ca` on `l2/buyer-recon-combined-01` |
| #538 | `1a36f23536c6` — CONFLICTING/DIRTY, base `7580bd8f` |
| #544 | `73575cd781d8` — CONFLICTING/DIRTY, base `7580bd8f` |

## 1. Why these two are one unit, not two merges

Both PRs repair `BuyerReconManager.update_entry` in `solspire/buyer_recon.py`.
Merging them independently would put two competing edits on one function.

**#544 is a strict superset of #538.** Measured, not assumed:

```
git diff 1a36f23536 73575cd781 -- solspire/buyer_recon.py
  adds only the `evidence_supplied` block
git show 1a36f23536:solspire/buyer_recon.py | grep evidence_supplied  -> absent
git show 73575cd781:solspire/buyer_recon.py | grep 'normalized["status"]' -> present
```

So #538's status-normalization is wholly contained in #544, and #544 adds the
evidence-patch repair. Source taken from #544.

## 2. The test file is a union — and a naive union is wrong

`#544`'s copy of `tests/test_prism_opportunity_entry_flow.py` **predates main's
opportunity-radar drift**. Measured node counts:

| Revision | Test nodes |
|---|---|
| `main` `341867eb` | **81** |
| `#544` `73575cd7` | **55** |

Taking #544's file wholesale would have **deleted 34 tests**. So the change was
applied as a 3-way patch of #544's *diff* onto main's file, not as a file copy.

Result: **88 nodes** — main's 81 minus 1 superseded pin, plus #544's 8.

Exactly one node is removed:

```
test_update_does_not_normalize_a_lowercase_status
```

That is not a lost test, it is the **defect pin the repair supersedes**. The two
are mutually exclusive by construction — main's test asserts the status is *not*
normalized; #544's asserts it *is*. Keeping both would be self-contradictory.
#544 replaces it with `test_update_normalizes_a_lowercase_status`.

Probe-block union verified independently: `#544` contributes 22 `out.*` keys,
the union carries **51**, and **0** of #544's keys were dropped.

## 3. Verification at the exact head `8f4a6ea0`

| Check | Result |
|---|---|
| `tests/test_prism_opportunity_entry_flow.py` | **88 passed** |
| + related suites (`solspire_route_composition`, `buyer_recon_router_board_scope`) | **96 passed** |
| full suite, candidate | 8 failed, **3276 passed**, 17 skipped, 1 error |
| full suite, `main` baseline (same env) | 8 failed, **3269 passed**, 17 skipped, 1 error |
| failing/error **node set** sha256 | `d9615caa…` on **both** — identical |
| CI `provider-routing` @ candidate | 14 nodes |
| CI `provider-routing` @ `main` | 14 nodes, sha256 `d5b21991…` on **both** |

The `+7 passed` is fully attributed: #544's **8** new tests minus the **1**
superseded pin. Not inferred from the delta — counted from the node set.

## 4. Negative controls — each fix is load-bearing

Each fix was reverted independently and the suite re-run:

| Reverted | Result |
|---|---|
| status normalization (`normalized["status"] = status`) | **1 failed** — exactly `test_update_normalizes_a_lowercase_status` |
| evidence patch (`evidence_supplied` + `current["evidence"]`) | **3 failed** — exactly the three evidence tests |

Neither revert breaks the other's tests, so the two repairs are independent and
each is pinned by its own assertions.

## 5. Other files

- `AGENTS.md`: main's 1588 lines **byte-preserved**; #544's 20-line section
  appended. Encoding audit: `alterations=0`, Cyrillic `0 -> 0`,
  `oracle_reproduced=True` — the insertion-only constraint holds.
- Evidence docs: `prism-l2-buyer-recon-status-normalization-01/EVIDENCE.md` and
  `prism-l2-evidence-patch-replacement-01/EVIDENCE.md` taken from #544 (neither
  is on main). The change to `prism-opportunity-entry-flow-01/EVIDENCE.md` is
  **purely additive** (verified: zero removed lines; 264 -> 271 lines).
- **No `web/` source touched** (0 paths under `web/`), so the frontend production
  build is not implicated by this change.

## 6. Safety declaration

- **No merge.** `main` is unmoved at `341867eb`.
- No production change, no deployment triggered.
- No EAA/dispatch PR advanced.
- No unrelated PR disposition changed; #538 and #544 remain open drafts.
- One review branch published (`l2/buyer-recon-combined-01`) at an explicit SHA.
- #525 remains held; #542/#543 untouched.

## 7. Next authorized action

Human review of `8f4a6ea0`, then a separate acceptance decision. If accepted,
#538 becomes **superseded by the combined candidate** and #544 **partially
included** (its source is taken; its test file is superseded by the union).
Do not merge without explicit authorization.

## 8. Exact-head verification of the published tip (added on review request)

A reviewer querying the **branch tip** `e79c9758eef6276426ea41f8cf4c809f3f5031e8`
for CI checks correctly found none, and asked for confirmation that the recorded
results belong to its code ancestor. Confirmed, with the reason:

| SHA | check-runs | reason |
|---|---|---|
| `8f4a6ea056ca85d1504bc070ac3b17c2dd63c99c` (code) | **4** | the workflows ran on this commit |
| `e79c9758eef6276426ea41f8cf4c809f3f5031e8` (tip) | **0** | the only commit on top adds one docs file |

- Published branch tip == `e79c9758eef6276426ea41f8cf4c809f3f5031e8` (verified via
  `git ls-remote`, not from local state).
- `8f4a6ea0` **is** an ancestor of `e79c9758`; the reverse is false. The diff
  between them is **one file, 116 insertions** —
  `docs/control-plane/evidence/l2-buyer-recon-combined-01/EVIDENCE.md`. No code
  path differs between the two SHAs.
- The tip touches **no** workflow path filter, so no workflow re-runs on it.
  The absence of checks on the tip is therefore expected, not a gap.

The four check-runs on the code commit `8f4a6ea0`:

| Check | Conclusion | Run |
|---|---|---|
| `router-composition` (SolSpire Router Composition Tests) | success | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38790040753 |
| `boundary` (SolSpire project execution boundary) | success | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38790054478 |
| `governance` (Prism Execution-WorkEvent Governance) | success | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38790058061 |
| `provider-routing` (Provider Routing Verification) | **failure** | https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38790036691 |

`provider-routing` is red **on `main` itself**, so it is not attributable to the
candidate. Two independent `main` runs fail identically (`38791309255`,
`38783706933`), and the node sets match exactly (14 nodes, sha256
`d5b21991…` on both `main` and the candidate). Its count delta
(13F/3260P -> 13F/3267P) is the same `+7` seen in the full suite, with the
failure count unchanged.
