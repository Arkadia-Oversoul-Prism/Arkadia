# gate-hygiene · pass 7 — open-PR queue composability re-proof + baseline-node classification

Evidence-only pass. **No source, test, or governance change.** Base `main` =
`162f574b05dd839540d803aadda7608342618a84` (`Merge pull request #214`). Observation
timestamp 2026-10-03T11:0xZ. Stdlib/`pytest` measurements only; no merge, no push to `main`.

Companion to pass 6 (`gate-hygiene/open-pr-queue-merge-order-map-02`, PR #219).

## 1. Live open-PR queue (measured via `gh pr list`)

| # | branch | tip SHA | draft | base | surface |
|---|--------|---------|-------|------|---------|
| 215 | `gate-hygiene/baseline-node-depth-stability-01` | `0c18fbb40b3dd2572389f04fcc59bd94b48da69e` | no | main | EVIDENCE.md only |
| 216 | `gate-hygiene/superseded-fingerprint-origin-01` | `4747e4c62ffacd5c965be8acc6a1c756a5eccd23` | no | main | AGENTS.md + docs |
| 217 | `gate-hygiene/live-file-fixture-revision-pin-01` | `3b5e4cdcca3968d74cde944450c990675057d77d` | no | main | `tests/test_agents_md_encoding_adjudication.py` |
| 218 | `gate-hygiene/adjudication-fixture-commit-pin-01` | `54e2e988c08ea771403bc6642f3c5eae43142641` | no | main | adjudication test + docs |
| 219 | `gate-hygiene/open-pr-queue-merge-order-map-02` | `c3ddf61cab13735d5c1fd4162cdee5104f0d217b` | no | main | docs only (pass 6) |
| 220 | `gate-hygiene/stale-gate-fixture-retirement-01` | `0893987be909543d8fe645b4660633a1aad13249` | **yes** | main | SH-05 retirement — HOLD (sovereign) |
| 221 | `gate-hygiene/stale-gate-fixture-pin-forensics-01` | `89603329129712e7ebc8361b06dc49cacc14368c` | **yes** | **218** | stacked on #218 |
| 222 | `test-hygiene/authority-boundary-async-01` | `88debcfb0383d27b716b679473fee44d0c834392` | no | main | `requirements.txt` + authority-boundary test + docs |
| 223 | `gate-hygiene/pr-217-221-lineage-equivalence-01` | `ee90d3322741d717c3d070cd3262045b1b52fa6d` | no | main | docs only |

### Cluster boundary correction
Pass 6 measured #219 at `e60bc913` and a 5-PR cluster #215–#219. In this pass #219's tip
**moved** (`e60bc913` → `c3ddf61`, still docs-only) and **two PRs have been added since**
(#222, #223) plus #220/#221 had already appeared. The "5-PR cluster" is therefore no longer
the whole queue. #222 is the highest-value item: it is the *only* open PR whose diff changes
runtime behaviour (`requirements.txt` declares `pytest-asyncio`), and it directly repairs one
of the two baseline nodes classified in §5.

## 2. Composition re-proof (independent, at live tips)

Fresh worktree off `162f574`; merged in queue order #215 → #216 → #217 → #218 → #219.

```
clean 0c18fbb40b…   clean 4747e4c62f…   clean 3b5e4cdcca…
Auto-merging tests/test_agents_md_encoding_adjudication.py
clean 54e2e988c0…   Auto-merging AGENTS.md
clean c3ddf61cab…
composed tree = f6d76802c3c9dfbead698f429797bf0e73752d81
```

No conflict markers in the tree. A **shuffled** re-composition (same five tips, different
order) produced the **identical tree** `f6d76802c3…`, reproducing pass 6's order-insensitivity
finding.

Protected surfaces on the composed tree:
- `python -m py_compile api/main.py` → OK; `api/main.py` = **2582** lines (budget 2600).
- `python -m pytest tests/architecture -q` → **11 passed** (recorded convention; pass 6 saw 10).
- CP10 mutation boundary on `main..HEAD` → `Mutation boundary PASS`, `rc=0`.

### Node-set delta (the environment-independent claim)

| set | count | sha256 |
|-----|-------|--------|
| baseline (`162f574`) | 21 | `8ba2c9c93b6d…` |
| composed | 19 | `f9504a606a9b…` |

Counts: baseline `20 failed / 1306 passed / 17 skipped / 1 error`; composed
`18 failed / 1308 passed / 18 skipped / 1 error`.

**Fixed (in baseline, absent in composed) — exactly 2:**
1. `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
2. `tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`

**New — none.** This supersedes pass 6's *second-fixed-node* claim: measured directly,
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` is **not in the
baseline set** (it is *skipped* at baseline), so it cannot be "fixed". The second fixed node
is the **shadow** node, which fails at baseline (unguarded `_rev(GATE2_PARENT_REV)` → `None`)
and is *skipped* by the #215 guard once the pinned revision is absent. #215 therefore
converts one failure into a skip and #217 converts the other failure into a pass.

## 3. Pinned-revision availability is the load-bearing variable

`GATE2_PARENT_REV = 7d79f38bd520a99637785db80bbe786192900d6d` is **not present** in this
clone (`git cat-file -e` → MISSING). Consequently:
- `test_gate2_parent…` — already guarded → **skip** at both baseline and composed.
- `test_shadow…` — un-guarded at baseline → fails; guarded by #215 → skip on composed.
- `test_exit_code…` — #217 replaces the moving `origin/main` fixture with the pinned
  `CORRUPTION_COMMIT` → baseline fail becomes composed pass.

This is clone-depth dependent, which is precisely the depth-stability defect #215 sets out to
neutralise. The claim is statement-level and holds regardless of clone depth.

## 4. Baseline-node classification (nodes no evidence doc had named)

A repository-wide grep of `docs/`/`AGENTS.md` for each of the four (confirmed) unnamed
baseline nodes returns **zero** evidence-document matches. Classifications are measured, not
inferred:

1. `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
   — **environment-sensitive (clone-depth / branch corruption state)**, repaired in source by #217.
   Not a logic defect.
2. `tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
   — **environment-sensitive (missing pinned revision `7d79f38`)**, repaired in source by #215.
3. `tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`
   — **genuine test defect**: real `AttributeError: 'Depends' object has no attribute 'get'`
   at `api/approval_routes.py:64` (`user.get(...)` called on a default `Depends` sentinel).
   Repaired in source by #222 (passes `user=approver`). Independent of clone depth.
4. `tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`
   — **genuine test-side literal defect**: demands
   `<SolariunHomeCockpit onNavigate={onThreadTarget}/>`, but `SolSpireExperience.tsx` renders
   the expanded-literal form absent (measured ABSENT) while carrying
   `onThreadTarget={selectSection}` and `onThreadTarget:(s:SolSpireLens)=>void` (both PRESENT).
   Reproduces pass 6's recurring "expanded-literal vs template / near-miss" class. No repair PR
   assigned yet — see §7 disposition.

`test_authorized_identity_is_the_control_case_and_creates_both_records` also carries no
evidence-document match but is the **same-file sibling** of node 3 and is repaired by the same
mechanism (#222).

## 5. Pass-6 doc reconciliation (discrepancies confirmed)

- **§7.2** in pass 6 claimed the async node "never executes (no async plugin)". Measured: the
  async node **does execute** in this environment (`pytest_asyncio 1.4.0` installed) and fails
  with a *runtime* `AttributeError`, not a non-execution. It is not declared in `requirements.txt`,
  so the pass-6 concern about CI coverage is *valid for CI*, but the local failure is a real
  runtime defect. Both claims are reconciled by #222.
- Pass-6 "second fixed node" claim → corrected in §2 above.

## 6. Disposition / next bounded task

- **#215, #216, #217, #218, #219** — composable from clean `main`; order-insensitive; CP10
  clean; protected architecture green; net node-set delta = −2 / +0. **READY FOR SOVEREIGN MERGE**
  as an ordered (or single batched) set.
- **#222** — repairs classified node 3; **READY FOR SOVEREIGN MERGE** (highest value; the only
  runtime-behaviour change in the queue).
- **#223** — lineage-equivalence evidence; **READY FOR SOVEREIGN MERGE** (docs).
- **#220, #221** — drafts; #220 is a sovereign HOLD; #221 is stacked on #218. **HOLD**.
- **Next bounded task (pinned):** repair node 4
  (`test_shell_wires_home_to_lens_selection`) — a bounded test-side literal fix in
  `tests/test_solariun_thread_navigation_01.py` aligning the assertion with the expanded
  `SolariunHomeCockpit onNavigate={onThreadTarget}/` form actually rendered in
  `SolSpireExperience.tsx` (or the inverse). **Not executed in this pass** — pass 6/7 are
  evidence-only, and it needs an explicit implementation authorization.

## 7. Authority boundary

Merge is the sovereign's. This PR is evidence-only; it changes no source, test, or governance
surface. It requests no merge of the cluster; it records composability evidence for the
sovereign to act on.
