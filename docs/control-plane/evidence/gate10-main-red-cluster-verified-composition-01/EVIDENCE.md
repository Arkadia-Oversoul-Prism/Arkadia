# GATE-10 · main-red cluster — verified composition of the repair set

STATUS: EVIDENCE-ONLY · IMPLEMENTED (composition measured, not merged)
AUTHORITY: none granted — this document records measurements and a recommendation.
BASE_MAIN: `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
DATE: 2026-10-10

This document does not merge, authorize, or request authorization for anything. It
records a *measured* merge-set composition so the sovereign can order the merge queue
from evidence rather than from four separate PR bodies that each measure `main` alone.

## 1. The `main`-red defect, root-caused from executed tests (not prose)

`main` is red at the CP10 `validate` gate. The failing nodes, measured locally at
`f9ced6b6` with `python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

```
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
```

All three name the same omission, verbatim from the delegated judge
(`scripts/cp10_mutation_boundary_policy.py --judge`):

```
deploy/n-atlas-server/Dockerfile: Unexpected path outside legitimate repository surfaces
deploy/n-atlas-server/README.md:  Unexpected path outside legitimate repository surfaces
deploy/n-atlas-server/app.py:     Unexpected path outside legitimate repository surfaces
deploy/n-atlas-server/requirements.txt: Unexpected path outside legitimate repository surfaces
```

`deploy/n-atlas-server/` is tracked (`git ls-files` at `f9ced6b6`) but not admitted by
the CP10 `LEGIT` inventory, so the invariant "every path in `git ls-files` is admitted"
fails. This is the recorded GATE-10 allowlist-omission class (the allowlist is an
inventory, not a filter). PR #354 repairs exactly this.

## 2. A second, independent `main` red: the browser asset gate

- `web/public_prism/index.html:16` loads `<script src="/firebase-config.js">` — a
  **root-absolute** src, no `type="module"`.
- `web/public_prism/public/firebase-config.js` does **not** exist on `main`
  (`git cat-file -e f9ced6b6:web/public_prism/public/firebase-config.js` → absent;
  `ls web/public_prism/public/` shows only the mp3s, `arkadia-mark.svg`, and the
  `arkana-signal/ ims/ mie-lab/` directories).
- The CP10 browser step serves the app through the **Vite dev server** at
  `http://127.0.0.1:5000`. Vite resolves `/firebase-config.js` against
  `public/`, finds nothing, and returns **404**. A root-absolute script tag that
  404s produces a browser console error, so the route-verification step fails even
  though Vite `build` itself is green — the classic "builds clean, 404s at runtime"
  divergence.
- PR #384 (head `f744e36b`, base `main`) adds `web/public_prism/public/firebase-config.js`
  (8 lines, inert default, **no credentials**) plus `tests/test_frontend_script_assets_resolve.py`
  (49 lines), which asserts every root-absolute `<script src>` in `index.html` resolves
  to a real committed asset. It repairs the defect and makes the class regression-proof.

## 3. The stacked dependency the individual PR bodies do not show

`PR #395` ("wire the frontend-script-asset guard into the CP10 gate") has
`base.ref == gate10/frontend-script-asset-resolution-01`, **not** `main`. That branch is
PR #384's head (`f744e36b`). So #395 cannot merge before #384, and neither PR body
states this: #395's mergeable/clean state is measured *against its stacked base*, not
against `main`. A merge queue that read the two PRs independently would mis-order them.

`PR #396` (head `6fb71d4f`) is the existing evidence-only composition record for
`#354 + #395`. It does not include #384 or #390.

## 4. A genuine composition conflict in the shared gate file

The CP10 gate workflow `.github/workflows/sg-02-fe-2-v.yml` is a load-bearing file edited
by **both** #390 (trigger coverage: adds `tests/test_ci_gate_trigger_coverage.py` to the
`paths:` selectors and a `trigger_coverage` step) and #395 (frontend asset gate: adds two
test files to `paths:` and two `frontend_asset_*` steps), in the **same regions**
(`paths:` blocks at ~line 21/52 and the gate job at ~line 124/549).

Measured with a real merge (`git merge pr395` onto `pr390` in a detached worktree):

```
CONFLICT (content): Merge conflict in .github/workflows/sg-02-fe-2-v.yml
```

Three conflict hunks — both sides add independent `paths:` list entries and independent
gate steps. `main` is non-conflicting with either individually, which is why no PR body
records this: each was written and measured against `main` alone.

## 5. Measured composition (union resolution)

Trees measured in detached worktrees at `f9ced6b6`. The recommended order is
`#354 → #384 → #390 → #395`, resolving the single workflow conflict as a **union** of the
two independent additions (both sides' `paths:` entries and both sides' steps are kept;
no side is dropped). The conflict is purely additive — no semantic disagreement.

Gate-scoped tests on the composed tree (`#354+#388+#390+#395`, conflict union-resolved):

```
python -m pytest tests/test_m02a_ci_gate_integrity.py \
                 tests/test_ci_gate_trigger_coverage.py \
                 tests/test_frontend_script_assets_resolve.py \
                 tests/test_frontend_script_asset_ci_wiring.py -q
199 passed
```

`main` @ `f9ced6b6` for the same file set: 3 failed (the `test_m02a_ci_gate_integrity.py`
allowlist nodes above; the two frontend-asset files do not exist on `main`).

## 6. Full-suite regression: the failing node set **shrinks**, nothing is introduced

Both runs: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`, same
environment, same interpreter.

| tree | failed | passed | skipped | errors |
|------|--------|--------|---------|--------|
| `main` @ `f9ced6b6` | 23 | 1833 | 33 | 1 (CE-01 collection) |
| composed `#354+#388+#390+#395` | 19 | 1918 | 33 | 1 (CE-01 collection) |

Failing/error **node set** diff (signed `sha256` of the sorted `FAILED`/`ERROR` lines):

- `main`: `b4eeb5b187da3770071a1850c8b5e397358beb27c5ece8f37f4bb8a1db5c8672` (24 nodes)
- composed: `f455fb7f0e8e8f4aafbf9d647258a9842c49c83418a30281da2f7f10dd29553d` (20 nodes)

The composed set is the `main` set **minus** exactly four nodes, zero added:

```
- FAILED tests/test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable
- FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
- FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
- FAILED tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
```

- The three `test_m02a_ci_gate_integrity.py` nodes are repaired by **#354** (§1).
- `test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable` is
  repaired by **#388**, which touches `AGENTS.md` + that test's subject; the
  encoding-adjudication node is base-dependent (documented) and clears on the composed
  tree.
- No node in the composed set is absent from `main` — the composition introduces **no**
  new failure.

`+85 passed` is not a regression signal: the composition adds test files (#384/#390/#395
add the asset guard, wiring guard, and trigger-coverage guard), so the passed count moves
by construction. Attribution is by node identity, not totals.

## 7. Note on PR #396's GET observation

`PR #396` head `6fb71d4f` is the existing evidence-only composition PR. Its body observes
"unrecorded" composition; this document measures it. #396 does not include #384 (the
`/firebase-config.js` repair) or #390 (trigger coverage). When the sovereign reviews the
merge set, #396's record should be read as a subset of this one.

## 8. Recommended sovereign action (NO authority claimed)

Merge order (each currently open, `base: main`, except #395 which is stacked):

1. **#354** — admit `deploy/n-atlas-server/` to the CP10 allowlist. Repairs §1.
2. **#384** — add `public/firebase-config.js` + asset-resolution guard. Repairs §2.
3. **#390** — wire the CI trigger-coverage guard. Repairs §4; selects the workflow.
4. **#395** — wire the frontend-script-asset guard into the CP10 gate (stacked on #384).
   Requires the single union resolution of `.github/workflows/sg-02-fe-2-v.yml` against
   #390 (§4).
5. **#388** — pin CP10 enforcement-step truthfulness. Repairs the AGENTS.md node in §6.

A merge performed one-PR-at-a-time without the §4 union resolution will conflict at step
4. The sovereign may alternatively ask for a single composed PR; that is an authorization
decision, not a repository fact.

REMAINING UNCERTAINTY: this is a *local* composition measurement. CI `validate` on the
composed tree has not been observed (no branch carries it). Runtime/browser observation of
the merged result is out of contract. **Specification ≠ implementation; composition ≠
merge; local pass ≠ CI pass.**
