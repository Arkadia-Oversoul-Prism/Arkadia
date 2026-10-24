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

`web/arkadia_console/src/pages/NovaNetPage.tsx` (23 insertions, 4 deletions):

- `FIELD_PAGE_LIMIT = 50` is declared once and drives the request —
  `` `${endpoints.transmissions}?limit=${FIELD_PAGE_LIMIT}` `` — so the fetched
  page and the notice cannot drift apart.
- The list is wrapped in a fragment and gains a notice, rendered only when
  `field.data.total > field.data.transmissions.length`, carrying
  `data-testid="novanet-transmissions-truncation"`.

No backend change: the cap and the `total` are both correct. The defect was
purely that the surface did not say which of the two it was showing.

## Proof

New guard `tests/test_prism_novanet_field_completeness.py` (6 nodes):

- Backend half is **executed**: 60 posts seeded via the real store, the real
  route read, asserting `total == 60` and `len(transmissions) == 50`; a 50-post
  store asserts **no** shortfall (the notice must stay off at the boundary); and
  the requested page size is accepted verbatim up to the handler ceiling.
- Frontend half is a pure source detector scoped to the field panel, with a
  **negative control** that rebuilds the pre-change silent-cap form and asserts
  the detector flags it.

| command | result |
|---|---|
| `pytest tests/test_prism_novanet_field_completeness.py -q` | 6 passed |
| live negative control (testid removed from the real file) | 1 failed, 5 passed |
| `pytest tests/architecture -q` | 11 passed |
| adjacent lane-2 guards (4 files) | 38 passed |
| `pytest tests/test_prism_console_ci_wiring.py -q` | 30 passed |
| `cd web/arkadia_console && corepack pnpm build` | `tsc --noEmit` + vite build, exit 0 |

The negative control was run against the **real** file, not a synthetic fixture,
and the file was restored byte-identically before commit.

### CI selection

`.github/workflows/prism-console-contract.yml` derives its domain at run time
(`python -m pytest -q $(python scripts/console_contract_domain.py)`), so the new
guard is executed by the gate without editing the workflow — verified by the
domain script returning the new path once the file is tracked.

## Regression boundary

- Failing/error node set compared by node identity against `main`; the change
  adds nodes and removes none.
- `api/main.py` untouched (boot-syntax budget irrelevant to this slice).
- No file owned by another lane was edited. `router.ts`, `App.tsx`,
  `surfaces.ts`, `endpoints.ts`, `types.ts` are all untouched.

## Remaining uncertainty

- The notice is a disclosure, not a pagination control: a reader still cannot
  reach transmissions 51+. Adding "load more" is a separate bounded slice.
- Frontend proof is source-level plus a real `tsc --noEmit`/build; no browser
  rendering was observed in this pass.

## Status

IMPLEMENTED — draft PR, not marked ready. Human merge authority is final.
