# gate-hygiene — open-PR queue Pass 2: 4-PR overlap, composability, merge order, and the `7d79f38` regime check

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-02`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.** Supersedes only
the *queue inventory* of `EVIDENCE.md` (Pass 1, base `002b189`, 16 PRs). Pass 1's method
precondition (unshallow first; test commit ancestry, not branch names) still holds.

---

## 1. Why this pass exists

Pass 1 mapped a **16-PR** queue at `main 002b189`. The queue has since drained to **4 PRs**
(all `gate-hygiene`) and `main` advanced to `162f574`. A sovereign merging these four has no
artifact that answers, against the *current* tree, the same three pre-merge questions:
overlap, real composability, and merge order. This pass answers them and additionally
adjudicates whether the `7d79f38…` revision is *genuinely absent* or *hiding a defect*.

## 2. Queue inventory (freshly reconstructed)

| PR | head | mergeable | state | changed files |
|---|---|---|---|---|
| #215 | `0c18fbb40b3dd2572389f04fcc59bd94b48da69e` | MERGEABLE | UNSTABLE | test + evidence doc |
| #216 | `4747e4c62ffacd5c965be8acc6a1c756a5eccd23` | MERGEABLE | UNSTABLE | AGENTS.md, MISSION.md, NEXT_AGENT.md, .bootstrap/01_STATE.md, CONTINUATION_LEDGER.md, test_baseline_fingerprint.py, 2 evidence docs |
| #217 | `3b5e4cdcca3968d74cde944450c990675057d77d` | MERGEABLE | UNSTABLE | test + evidence doc |
| #218 | `54e2e988c08ea771403bc6642f3c5eae43142641` | MERGEABLE | UNSTABLE | test + evidence doc |

`UNSTABLE` is environmental: `Vercel – console` / `Vercel – arkadia-prism` report
*deployment rate limit / deployment has failed* on every head. `Full-history secret scan` is
**success** on all four.

## 3. Overlap map — one hot file

Writers per file:

| file | writers |
|---|---|
| `tests/test_agents_md_encoding_adjudication.py` | **#215, #217, #218** |
| `AGENTS.md` | #216 only |
| `MISSION.md`, `NEXT_AGENT.md`, `.bootstrap/01_STATE.md`, `docs/phase1/CONTINUATION_LEDGER.md` | #216 only |
| `tests/test_baseline_fingerprint.py` | #216 only |
| evidence docs | one each |

Only the adjudication test module is multiply modified, and the three edits land in **different
functions**:

- #215 → `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` (adds `None` guard → skip)
- #217 → `test_exit_code_does_not_call_a_divergent_clean_file_verified` (fixture pinned to `CORRUPTION_COMMIT`)
- #218 → `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` (fixture pinned to `CORRUPTION_COMMIT`)

## 4. Composability — git-object proof

Command: `git merge-tree --write-tree prA prB` (two-argument form; the three-argument
`A B C` form is retired in git ≥ 2.x and exits 129 — a false "conflict" if misread).

Result: **all 6 pairwise merges and all 4 PR-onto-`main` merges return rc=0 with 0 conflict
markers.** Cross-checking the three writers of the hot file pairwise (#215×#217, #215×#218,
#217×#218) is clean.

### Deterministic composed tree

Merge order **#215 → #216 → #217 → #218** on `main 162f574`:

```
after #215 -> 0c18fbb40b3dd2572389f04fcc59bd94b48da69e
after #216 -> 6d7d77ca575745975248afd85c1e916ddccb88b0
after #217 -> ddf1aee83d1069851acc78d3e84e26915b64116b
after #218 -> db5510a8200b58d5144b3d44cfd483c1bea544f8
```

`git diff --stat` between this tree and an independently built one is **empty**, so the
composition is order-insensitive within this set — as expected for disjoint hunks.

## 5. Baseline vs composed — proof by node set, not counts

Environment: `PYTHONPATH=archive/legacy_python`, `python -m pytest tests/ -q
--continue-on-collection-errors` (the flag is required; a bare `pytest tests/` *interrupts*
at the collection error).

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| baseline `main 162f574` | 20 | 1306 | 17 | 1 (`tests/test_autonomy.py`) |
| composed `db5510a` | 18 | 1308 | 18 | 1 (`tests/test_autonomy.py`) |

Set difference:

- **Fixed by composition (2):**
  `test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`,
  `test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
- **Newly failing (0):** the composed-minus-baseline set is **empty**.

The −2/+2 count delta is entirely the two adjudication nodes; no other node changed state.
The single collection error (`tests/test_autonomy.py`) is pre-existing debt, unchanged.

Architecture suite on the composed tree: **11 passed / 11**.

## 6. CP10 mutation boundary

`git diff --name-only main db5510a | python scripts/cp10_mutation_boundary_policy.py --judge`
→ **exit 0** ("Mutation boundary PASS"). `docs/` and `tests/` are admitted surfaces. The CP10
workflow (`sg-02-fe-2-v.yml`) is **path-filtered** and does not trigger on any of the four PRs
— none touches its filter. This is an *absence*, established against the workflow trigger,
not inferred from a missing check-run.

## 7. The `7d79f38` regime check — absence vs. concealed defect

**Claim under test:** is `7d79f38bd520a99637785db80bbe786192900d6d` genuinely unavailable, or
does its absence hide a defect?

Findings:

1. **Absent from the clone, present on GitHub.** `git cat-file` fails locally (clone is
   *not* shallow: 1604 commits, 8 refs; `fetch --all --prune` does not fetch it — it is a
   PR-head-only revision). The GitHub API resolves it, message *"gate2: close backend runtime
   link VERIFIED (discriminating), main 002b189"*. A normal CI clone legitimately never
   carries it.
2. **The sibling node crashes, it does not skip.** On `main`, with the revision absent,
   `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` raises
   `AttributeError` at `scripts/agents_md_encoding_audit.py:184` (it reads the absent
   revision's text and dereferences `None`). #215 adds `if text is None: pytest.skip(...)`.
   Measured: `FAILED` on `main` → `skipped` on the composed tree.
3. **It is the deferred workstream, not a cover-up.** `AGENTS.md` (from #216) states the
   excluded node's own assertion defect "remains a separate proposed workstream — do not fix
   them inside a fingerprint workstream." #215 **is** that workstream, done as its own bounded
   change.
4. **The fix preserves the property.** With the revision present the node still runs its full
   oracle-determined codec assertion; only the absent-revision path changes from crash to skip.
5. **The recorded baseline set is deliberately one node short** of a bare clone's live run
   (20 vs 21) exactly because of this clone-depth-dependent node — so the published debt
   fingerprint stays stable across clone depths. #216 proves this
   (`test_superseded_values_are_the_recorded_set_plus_its_sibling`).

**Verdict: legitimately unavailable; the skip is a correct, bounded guard repair. No concealed
defect.**

### 7.1 Second sibling — #218's latent fix

`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` already guards the
absent revision with a skip, but then dereferences **`origin/main`** — a *moving branch*.
#218 pins it to `CORRUPTION_COMMIT`. On the current tree that node **passes** (because
`origin/main` still resolves to the corrupt revision), so #218 is a **latent-expiry** fix:
**0** new passes, **0** regressions today. It removes a premise that expires with the very
repair it guards.

## 8. Merge order (advisory; merge is HUMAN)

Git-safe in any order. Recommended, to keep each PR's evidence narrative aligned with the tree
it describes:

1. **#216** — disjoint; describes the recorded set and the depth-dependent sibling.
2. **#218** — pins the skip-branch fixture's corrupt revision.
3. **#215** — guards the crash-branch sibling.
4. **#217** — pins the divergent-file node's corrupt revision.

## 9. Remaining uncertainty

- Composability probes are **git-object** merges, not a build or a deployment; they make **no**
  production-parity claim and assert only *conflict-free*, not *green*.
- The composed-tree suite is **local** (not CI); counts are environment-sensitive
  (`AGENTS.md`: full-suite fingerprint is UNSTABLE). Attribution is by node **set**, which is
  environment-independent.
- #216's authoring base (`64cbe74`) predates current `main` (`162f574`); its guard test passes
  on both (`17 passed` → `18 passed` on its head), and no other open PR writes its files.
- No PR here touches `api/main.py`, so the 2600-line budget is unaffected
  (`main` measured 2582/2600; `py_compile` OK).
