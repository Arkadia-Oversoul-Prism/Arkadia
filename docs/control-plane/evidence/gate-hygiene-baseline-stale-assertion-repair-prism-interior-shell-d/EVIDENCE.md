# EVIDENCE — `gate-hygiene` / SH-02 batch d (Prism interior shell)

Repair the three `STALE_ASSERTION` failures in `tests/test_prism_interior_shell.py`.
Test-only, bounded. Derived from live repository evidence at run time.

| | |
| --- | --- |
| **BASE_MAIN** | `df7a99a067382401c00de5e7bbaaac0125ba2088` (PR #131 merged) |
| **Branch** | `gate01/sh02d-prism-interior-shell` |
| **Nodes** | 10–12 (Appendix A, classification doc) |
| **Class** | `STALE_ASSERTION` — property intact, source-string anchor moved |
| **Not touched** | product code (`web/public_prism/src/**`), `api/**`, `knowledge/**`, `weaver/**`, governance/identity/authority code, `.gitleaks.toml`, CP10 policy module |

## 1. Why this was blocked, and why it is not now

Batch d was first authored at `8d1c386` on `gate-hygiene/sh02d-prism-interior-shell`,
based on `4164573` (PR #128). It was **never published**: the batch-5 ledger records it as
*"blocked on a rebase decision"* because the commit edited
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`,
which PR #129 rewrote by 321 lines.

Reconstruction this pass: **PR #129 merged** (`2026-09-29T15:00:46Z`), and `8d1c386` is now
an **orphan** — it predates `df7a99a` and its parent `4164573` is an ancestor of `main`.
The dependency batch d was waiting on is satisfied. PR #133 (`open`, W2 batch,
`gate-w2/living-gate-grove-handoff`) explicitly names batch d as the next bounded task.

This branch is therefore a **fresh reconstruction off current `main`**, carrying the test
repair only. The ledger edit is deliberately dropped: the classification doc was rewritten
by #129 and re-applying the pre-#129 text would be a regression against a merged artifact.
The continuity state instead lands in this batch's own evidence directory, matching the
batch-5 / batch-6 convention.

## 2. Nodes repaired

| node | was asserting | now asserts |
| --- | --- | --- |
| `test_authenticated_interior_uses_one_prism_shell` | the literal prose `"Same identity · same context · same backend"` | the structure that *delivers* it: `prism-interior-shell` testid, `useAuth`, `identity-persistence` testid, and the `ArkadiaNavigation` mount |
| `test_shell_exposes_canonical_primary_surfaces` | substring `'<view>'` anywhere in the file, `"PRIMARY"`, `prism-primary-rail` | the `PRIMARY` rail is **parsed**; canonical anchors survive; every primary key is resolvable by `activeSurfaceFor`; rail testid present |
| `test_shell_exposes_secondary_nexus_lenses` | `"SECONDARY"`, `prism-secondary-toggle`, `prism-secondary-lenses`, seven lens labels | the `SECONDARY` rail is **parsed**; ≥4 lenses; rendered via `SECONDARY.map(`; disclosure control is real (`aria-expanded={lensesOpen}` + `setLensesOpen`); every lens label present |

None of the three assertions was load-bearing for a governance claim: all three were
source-text anchors whose referenced constructs had been reworded or replaced while the
property they described remained intact.

Two nodes in the file were already structurally sound and are unchanged:
`test_shell_does_not_create_authority_or_backend_paths` (a negative authority assertion)
and `test_novanet_view_mounts_content_not_nested_hub` (W3 nesting guard).

### Structural drift the repair records (not repaired here)

- The shell has **no** `prism-primary-rail` / `prism-secondary-toggle` /
  `prism-secondary-lenses` testids. The rails are identified by
  `aria-label` + `data-testid="novanet-primary-rail"`.
- The secondary lens control is an inline `<button aria-expanded={lensesOpen}>More</button>`,
  not a `prism-secondary-toggle`.
- The PRIMARY rail keys are `novanet, solariun, solspire, commune, reasomate, encyclopedia,
  offerings` — the `sci` and `knowledge-os` keys the old assertion probed are gone
  (`knowledge-os` resolves to the `encyclopedia` surface).

These are reported, not silently re-pinned: re-adding testids to product code is a product
change and lies outside this bounded task's authority.

## 3. Mutation-anchored proof (the assertions are not vacuous)

A re-pinned source-string assertion is only worth what it rejects. Each mutation below was
applied to `web/public_prism/src/components/PrismInteriorShell.tsx` (temporarily, then
reverted — the working tree carries **zero** product diff) and the file re-run:

| control | mutation | result |
| --- | --- | --- |
| NC1 | `identity-persistence` testid renamed | **1 failed** |
| NC2 | canonical anchor `commune` removed from `PRIMARY` | **1 failed** |
| NC3 | primary key added that `activeSurfaceFor` cannot resolve | **1 failed** |
| NC4 | `SECONDARY` collapsed to 3 entries | **1 failed** |
| NC5 | `aria-expanded={lensesOpen}` → `aria-expanded={false}` | **1 failed** |
| NC6 | `SECONDARY.map(` renamed (lenses no longer rendered from the rail) | **1 failed** |
| — | unmutated | **5 passed** |

Rejection is not uniform — each control reds a different node — so the three repaired
assertions each carry independent teeth.

## 4. Regression boundary — measured, not assumed

```
base  df7a99a  : 32 failed / 1025 passed / 13 skipped / 2 errors  (34 nodes)
branch         : 29 failed / 1028 passed / 13 skipped / 2 errors
  delta         : -3 failures, exactly the three repaired nodes; ZERO added nodes
  node diff     : `comm -13` (new failures) = EMPTY
architecture    : 11/11 (unchanged)
py_compile api/main.py : pass   (api/main.py = 2519 / 2600, untouched)
CP10 mutation boundary : PASS on this diff
vite build      : environment-blocked (no npm registry access)
```

The two documented pre-existing collection errors (`tests/test_autonomy.py`,
`tests/test_render_codex.py` — missing `load_autonomy_config` / `arkadia_drive_sync`) are
ignored in both measurements so the comparison is like-for-like.

Node-level comparison is against BASE_MAIN, not `4164573`. Comparing against `4164573`
produced seven false "new failures" in the batch-6 pass because `#130`–`#132` landed in
between; the node-id diff is only meaningful against the commit the branch is actually
based on.

**Contract baseline is stale.** The brief's `main := 6038989`, `804 passed`,
`architecture 9/10` and the batch-5 ledger's `39F / 1018P @ 4164573` both predate
`#130`–`#133`. Re-measured above.

## 5. Remaining uncertainty

- `vite build` is environment-blocked, so frontend contracts are verified by source
  inspection. That is this repository's existing convention for `.tsx` contract tests
  (`tests/test_solariun_*`, `test_solspire_*`, `test_prism_pass_c_*`).
- The clone was **shallow** at the start of this pass; `git fetch --unshallow` was run, so
  ancestry is now inspectable to the root. Before that, `4164573` reported as *not* an
  ancestor of `main` — a false negative that would have mis-classified batch d as orphaned.
  Recorded because a shallow clone silently inverts ancestry queries.
- The structural drift in §2 is recorded for a future bounded task. Re-adding testids or
  restoring `sci` / `knowledge-os` primary keys would change the product surface and
  requires sovereign direction.

## 6. Authority

Test-only repair, root-cause diagnosis, and evidence. No merge, no push to `main`, no
force-push, no product decision, no governance change. Human sovereign merge only.

### Reproduction

```bash
git fetch --unshallow origin
git checkout -b verify gate01/sh02d-prism-interior-shell
PYTHONPATH=<repo>/archive/legacy_python python3 -m pytest tests/test_prism_interior_shell.py -q
PYTHONPATH=<repo>/archive/legacy_python python3 -m pytest tests/architecture -q
```
