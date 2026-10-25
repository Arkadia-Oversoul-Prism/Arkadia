# PRISM-L2-FIELD-COMPLETENESS-01 — the public field states completeness

Lane 2 (NovaNet). Base `main` `68acf89f3045a01b0ba04038fabac4edfb5f937e`
(PR #556 merge, 2026-10-23T16:31:57+01:00).

## Defect (measured, not inferred)

`api/transmissions.py::list_transmissions` clamps the page and reports the
uncapped total:

```python
limit = max(1, min(int(limit), 100))
return {"transmissions": posts[offset:offset + limit], "total": len(posts)}
```

`NovaNetPage.tsx` rendered `field.data.transmissions` and headed the panel with
`${field.data.total} transmissions`. Past 50 posts the header therefore stated a
count the list beneath it could not contain, and nothing disclosed the
shortfall — an incomplete render presented as the whole public field.

Measured against a seeded store of 60 posts through the real route:

| request | `total` | returned | shortfall |
|---|---|---|---|
| `GET /api/transmissions` (default) | 60 | 50 | 10, undisclosed |
| `GET /api/transmissions?limit=100` | 60 | 60 | none |

The echoes panel beside it already satisfied this property (`ECHO_DISPLAY_LIMIT`
+ notice), so the field panel was the outlier, not the convention.

## Change

`web/arkadia_console/src/pages/NovaNetPage.tsx` (+27 / −4):

- `FIELD_PAGE_LIMIT = 50` is declared once and drives the request, so the
  fetched page and the notice cannot drift apart.
- The path is a **registry-derived local binding**, not an inline path — the
  shape Lane 1's registry contract requires (see the regression note below).
- The list is wrapped in a fragment and gains a notice, rendered only when
  `field.data.total > field.data.transmissions.length`, carrying
  `data-testid="novanet-transmissions-truncation"`.

No backend change: the cap and the `total` are both correct. The defect was
purely that the surface did not say which of the two it was showing.

## Regression introduced and repaired within this pass

The first commit passed the page size as an **inline template literal** at the
`useHydration` call site:

```tsx
useHydration<TransmissionList>(`${endpoints.transmissions}?limit=${FIELD_PAGE_LIMIT}`, …)
```

That is precisely the page-local endpoint contract Lane 1's
`test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`
forbids. Measured: the node **passed on clean `main`** (`1 passed in 0.11s` in a
detached `origin/main` worktree) and **failed on this branch's first commit** —
a regression this slice introduced, inside a guard owned by another lane.

Repaired by adopting the sanctioned shape already in use at
`components/knowledge/KnowledgeTimelinePanel.tsx:69` — a local binding built
from `endpoints.*`, which the detector's `_registry_derived_names` accepts as the
one registry expressed:

```tsx
const fieldPath = `${endpoints.transmissions}?limit=${FIELD_PAGE_LIMIT}`;
const field = useHydration<TransmissionList>(fieldPath, …);
```

The new guard pins that shape too, so the fix cannot be silently undone.

## Proof

New guard `tests/test_prism_novanet_field_completeness.py` (7 nodes):

- Backend half is **executed**: 60 posts seeded via the real store, the real
  route read, asserting `total == 60` and `len(transmissions) == 50`; a 50-post
  store asserts **no** shortfall (the notice must stay off at the boundary); and
  the requested page size is accepted verbatim up to the handler ceiling.
- Frontend half is a pure source detector scoped to the field panel, with a
  **negative control** that rebuilds the pre-change silent-cap form and asserts
  the detector flags it.

| command | result |
|---|---|
| `pytest tests/test_prism_novanet_field_completeness.py -q` | 7 passed |
| `pytest tests/test_console_endpoint_registry_contract.py -q` | 18 passed (was 1 failed pre-repair) |
| live negative control (testid removed from the real file) | 1 failed, 6 passed |
| `pytest tests/architecture -q` | 11 passed |
| `pytest tests/test_prism_console_ci_wiring.py -q` | 30 passed |
| `cd web/arkadia_console && corepack pnpm build` | `tsc --noEmit` + vite, exit 0 |

The negative control was run against the **real** file, not a synthetic fixture,
and the file was restored byte-identically before commit.

### CI selection

`.github/workflows/prism-console-contract.yml` derives its domain at run time
(`python scripts/console_contract_domain.py`), which now returns **52** paths
including `tests/test_prism_novanet_field_completeness.py`, so the new guard is
executed by the gate without editing the workflow.

## Regression boundary

Baseline measured at `main` `68acf89f`: the full suite reports **9 failed, 3433
passed, 20 skipped, 1 error**. All ten failing/error nodes are pre-existing debt
— each reproduced in a detached `origin/main` worktree. The failing/error **node
set** across those files is byte-identical between `main` and this branch
(`comm -3` empty), so this slice adds nodes and removes none.

The one node this slice *did* break (the Lane 1 registry contract) is repaired
above and verified green. Baseline debt is recorded, not repaired: the
`test_engineering_lab_api.py` pins touch an authority surface
(`api/lab_routes.py`) and are sovereign-only.

- `api/main.py` untouched.
- No file owned by another lane was edited. `router.ts`, `App.tsx`,
  `surfaces.ts`, `endpoints.ts`, `types.ts` are all untouched — the Lane 1
  shared-file surface needed no change for this slice.

## Remaining uncertainty

- The notice is a disclosure, not a pagination control: a reader still cannot
  reach transmissions 51+. Adding "load more" is a separate bounded slice.
- Frontend proof is source-level plus a real `tsc --noEmit`/build; no browser
  rendering was observed in this pass.

## Status

IMPLEMENTED — draft PR, not marked ready. Human merge authority is final.

## Lane-continuity drift repair + main-gate diagnosis — 2026-10-25

### 1. The inherited claim "main's lane gate is red because two repair PRs are open" is STALE

Both named repair PRs are **already MERGED**, measured live:

| PR | state | merged_at | head |
|----|-------|-----------|------|
| #565 `gate-hygiene/lane-currency-isolated-01` | MERGED | 2026-10-25T05:13:02Z | `a671c4e4` |
| #566 `docs/lane-currency-evidence-currency-01` | MERGED | 2026-10-25T07:46:12Z | `a9bc2c45` |
| #492 `feat/prism-next7-02-pipeline-strip` | MERGED | — | `acfbf521` |

So they are not open repair PRs and are not a reason to open another. The only
`main` push run of `lane-doc-currency.yml` on record is **success** at `3a1088c5`
(2026-10-25T05:13:04Z). The red runs at 15:20Z/17:28Z are **pull_request** runs on
lane branches, not on `main`.

### 2. main's gate IS red, for a different and still-open reason

`scripts/lane_state.py --check --verify-live` exits **1** on `origin/main`'s own
`lane-state.json` (`36f53be2`), with two findings:

```
DRIFT PR #508 (lane 4 open_prs) is recorded as open but is CLOSED without merging
DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging
```

Measured live: **#508 CLOSED 2026-10-25T15:23:41Z** (not merged), **#563 CLOSED
2026-10-25T05:16:10Z** (not merged). The snapshot's `open_prs` still lists both, so
the snapshot is stale against its own oracle.

Cause is `_liveness_findings`' documented limit: it adjudicates a claimed-open PR
**only when a merge commit is recorded** for it (`if not commit: continue`). A PR
closed *without* merging has no merge commit, so the local-ancestry oracle cannot
see it. The live-GitHub oracle (`--verify-live`) can, which is why only the
`--verify-live` run reddens.

**This drift is owned by two already-open PRs — do not open a third.**
- #569 `gate-hygiene/lane-state-refresh-01` — clears the #563 record (touches
  `docs/control-plane/parallel-ui/lane-state.json`).
- #568 `gate-hygiene/lane-guard-fixed-scope-01` — derives the enforced set from a
  constant rather than PR activity.
- #571 `gate-hygiene/lane-state-refresh-composition-01` — records that #569 is a
  strict subset of #568.

### 3. Lane instruction-doc drift — one real instance, repaired on this branch

`AGENT-02-NOVANET-OPPORTUNITY.md`'s own header named
`feat/prism-next2-02-opportunity-entry-flow` / **PR #430** as Active branch/PR.
#430 is **MERGED** (`04e1b83b`) — a successor agent following the header is sent to a
dead thread. Re-pointed at the live lane thread (`feat/prism-l2-field-completeness-01`,
PR #564), base re-measured at `36f53be2`.

The guard itself reports the two remaining doc-pointer defects as **NOTE, not
blocking**, because those lanes are `deferred`:

```
NOTE lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #450, CLOSED without merging
NOTE lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #428, MERGED
```

Those are real drift in lane 3/lane 4 docs, outside lane 2's ownership — recorded
here, not repaired here.

### 4. Verification

- `tests/test_lane_instruction_doc_currency.py` + `tests/test_lane_currency_ci_wiring.py`
  → **49 passed** (before and after the header edit).
- `scripts/lane_state.py --check --verify-live` after the edit → **exit 1**, and the
  lane-2 finding is gone; the two remaining findings are the inherited
  `lane-state.json` records above.
- Earlier in this branch: field-completeness tests 9 → 11 passed; console contract
  domain 30 → 815 passed; `corepack pnpm build` clean (104 modules, 1.73s) with the
  retrieval control absent from the minified bundle (0 occurrences).

### 5. Boundary

No merge, no deployment, no acceptance. `main`'s gate repair is left to the two open
PRs that already own it.
