# gate-hygiene — Gate-2 PR #366 × #368 composition reconciliation (pass 1)

**Class:** decision record + regression guard (test/harness/evidence only)
**Base main:** `24a00f856a0286cbb464a4b585117dd57a2646fa` ("fix: complete HF auth on N-ATLaS Gradio SSE")
**Branch:** `gate-hygiene/gate2-366-368-composition-reconciliation-01`
**Status:** IMPLEMENTED — ready for sovereign review
**Authority:** no merge; no push to `main`; no product code; no workflow; `api/main.py` untouched

---

## 1. Objective

The two open Gate-2 instrument PRs repair **the same two files** from the same base. Measure
whether they compose, record the reconciliation, and pin it so a future pass neither re-derives
it nor merges the pair in either order and silently loses one repair.

## 2. What was reconstructed

| item | value |
|---|---|
| BASE_MAIN | `24a00f856a0286cbb464a4b585117dd57a2646fa` |
| `main` tip confirmed by | `git log -1`, `git rev-parse origin/main`, GitHub API — all agree |
| open PRs at start | 21 (#337–#369, minus already-merged) |
| clone depth | not shallow |

## 3. The defect

`tests/…`/GitHub reports **both** #366 and #368 as `MERGEABLE`. That verdict compares each head
against `main` only. It cannot see a *cross-PR* overlap, so it is **not** evidence the pair
composes. Two PRs editing the same load-bearing file from the same base is exactly the class the
repo's own `test_open_pr_cluster_composability` guard (PR #358, unmerged) exists to surface.

## 4. Measured evidence

### 4.1 Population overlap (live GitHub pull-files API, paginated)

21 open PRs, changed paths fetched per PR:
**exactly two** non-`AGENTS.md` overlaps exist.

| pair | shared paths | classification |
|---|---|---|
| #337 × #338 | `api/lab_routes.py`, `web/public_prism/src/App.tsx`, `ArkadiaNavigation.tsx`, `EngineeringLabPage.tsx` | **dependency pair** (already recorded) |
| **#366 × #368** | `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py` | **same-instrument hazard** (new) |

### 4.2 The composition is real, and it is additive

A 3-way apply of #368 onto #366 yields `UU` on **both** files. The conflicted regions are
**additive**, not contradictory:

- `scripts/gate2_production_observation.py` — the constant block at `BUILD_INPUTS`:
  #366 adds `KNOWN_FRONTENDS` / `MARKER_APP`; #368 adds `DEPLOYMENT_SCAN_PAGES`.
- `tests/test_gate2_production_observation.py` — the import block, plus appended test blocks
  (ordering fault vs fetch window).

### 4.3 Composed tree, measured

| tree | result |
|---|---|
| #366 alone | 29 passed |
| #368 alone | 24 passed |
| **#366 + #368 composed** ("keep both" on every conflict) | **39 passed** |

Composed blob identities:
`scripts/gate2_production_observation.py` = `cf09b073f12753f43514a6baef7fc6fb62bd82b8`,
`tests/test_gate2_production_observation.py` = `07aefd2e642e3d8aea278238fad06262cbfb17d7`.
The composed script carries **both** markers (`DEPLOYMENT_SCAN_PAGES` ×4, `KNOWN_FRONTENDS` ×3),
so neither repair is dropped.

Recorded head blobs (drift pin): base script `9b481812…`; #366 script `82907d6e…`; #368 script
`c5ec73a3…`; #366 test `b81ed488…`; #368 test `bcdc4bf3…`.

### 4.4 #369 does not compose into the hazard

PR #369 (`gate2-canonical-alias-app-binding-01`) adds only **new** files
(`scripts/gate2_alias_app_binding.py`, `tests/test_gate2_alias_app_binding.py`, one evidence
dir) — zero overlap with the composed tree.

## 5. Reconciliation (sovereign's call; recorded, not executed)

Merge **#366 first**, then rebase **#368** onto it keeping **both** edits — or land one composed
PR. Do **not** merge the pair unreconciled, and do **not** drop either repair: they are
independently necessary (pagination + marker-app identity).

## 6. Change

- `scripts/gate2_366_368_composition.py` — read-only, stdlib-only classifier over a frozen
  manifest; `--measure` re-derives the drift pin from a live git tree. Imports no application
  module; mutates nothing.
- `tests/test_gate2_366_368_composition_reconciliation.py` — 9 tests: the classification
  invariant, a **positive control** that the detector *finds* the two measured pairs, a
  **negative control** that an unclassified overlap is reported, a positive control that the
  classification entry is load-bearing, and drift pins for both heads.

## 7. Verification

| command | result |
|---|---|
| `python -m py_compile scripts/gate2_366_368_composition.py` | OK |
| `python -m pytest tests/test_gate2_366_368_composition_reconciliation.py -q` | **9 passed** |
| `python scripts/gate2_366_368_composition.py` | classification `CLASSIFIED`, exit 0 |
| `python -m pytest tests/architecture -q` | **11 passed** |
| full suite vs freshly measured `main` `24a00f85` | node set **unchanged** (see §8) |

## 8. Baseline comparison

Full suite against `main` `24a00f85` and against this branch, compared by **failing/error node
identity** (counts are a local dependency delta): zero node-set delta. The `+9 passed` is
exactly this guard file.

## 9. What is NOT claimed

- **Not** a Gate-2 closure. The standing Gate-2 boundary — *deployment build output observed* —
  remains `BLOCKED` on Vercel Deployment Protection (SSO).
- **Not** a merge. The ordering is recorded for the sovereign, not executed.
- **Not** production parity, **not** production acceptance (`NOT CLAIMED` — human authority).

---

_This evidence record was created by an AI agent (OpenHands) on behalf of the sovereign._
