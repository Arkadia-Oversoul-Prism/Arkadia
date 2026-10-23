# PRISM-REC-SPIRAL-CODEX-01 — explicit follow-ups

Carried forward from the human review of PR #560. These are **proposed workstreams, not
authorizations**. Each names its own entry condition so a later pass does not have to
reconstruct the reason it exists.

Recorded against `main` `68403b9e` / PR #560 head `e11d93b4`.

---

## FU-1 — Legacy route recovery: `/encyclopedia` and `/spiral-codex`

**State:** `BROKEN` (deep links), deliberately not repaired in #560.

Both routes resolve to `home`. They are **not** an alias-table entry: `PATH_ALIASES` maps a
path segment to a **surface** (`router.ts:66`), but these two legacy routes addressed a
*lens within* the NovaNet surface — the archive routed them to `NexusSpiralCodex`, which the
console now expresses as the NovaNet `codex` lens.

Repairing them requires the resolver to express **"surface + default lens"**, a change to
`resolvePath`'s return shape — a **shared seam** owned by whoever owns `lib/router.ts`.
Doing it inside a lens slice would have been scope creep on a contended file.

**Entry condition:** a bounded slice that owns `lib/router.ts`, adds the default-lens
mechanism, and carries **regression tests for both routes** (resolve → correct surface *and*
correct lens; round-trip through `routeForSurface`; and a control proving an unknown legacy
path still falls through to `home`).

**Do not** add these to `PATH_ALIASES` as-is: that would resolve `/encyclopedia` to NovaNet
*without* selecting the `codex` lens, i.e. to the wrong view of the right surface.

---

## FU-2 — `/api/ims/*` is `UNKNOWN` beyond the one route probed

**State:** `UNKNOWN` — explicitly *not* generalized.

Only `/api/ims/inquiries` was probed: `403 Sovereign key required`. The inventory lists
three `/api/ims` paths in the reconciliation gap:

```
/api/ims/archetypal-analyze
/api/ims/diagnostic
```

**One 403 is not a conclusion about the family.** A sibling route may be an open read, a
different auth class, or absent entirely. The `NovaNetPage` copy was corrected in #560 to
state the *measured* reason per endpoint rather than a blanket "unverified" claim; the
remaining family members stay unclassified until each is probed individually.

**Entry condition:** probe each path against the canonical origin, record status + body
shape per path, then classify individually. Classify by **observed response**, never by the
prefix.

---

## FU-3 — Production acceptance for #560

**State:** `NOT CLAIMED`.

Production runs `main` `68403b9e`, which does **not** contain the Spiral Codex lens.
`OBSERVED` in #560 is claimed for the **contract** (`/api/codex` → 200, 661 docs) and for the
journey against a **dev server proxying to** the canonical origin — not for the deployed UI.

Render auto-deploys `main`, so **a merge is a production release**. Deployment is not
acceptance.

**Entry condition (after an authorized merge):**

1. Read `GET /api/version` and confirm `source_revision` == the merge SHA.
2. Confirm the served bundle actually contains the change — marker-set comparison, not an
   asset hash (build output is env-dependent; a hash mismatch is not divergence).
3. Exercise the real journey on the deployed origin: the Encyclopedia Galactica lens loads,
   the corpus renders, search narrows the set, Read expands a real document.
4. Record the deployment identity (host + revision) **with** the observation. A matching
   revision is necessary evidence of source↔runtime consistency, not proof the UI works.

**`/health` is the liveness route; `/api/health` is not a route** (a 404 there is correct).

---

## FU-4 — The 73-endpoint target is conditional on its set definitions

**State:** valid *only* while its definitions hold.

The target is `gap (legacy ∩ served, not in console)`, computed by
`scripts/prism_endpoint_inventory.py` from three set definitions:

| Set | Definition |
|---|---|
| legacy | paths referenced under `archive/frontend/arkadia-prism/web/public_prism/src/**` |
| served | `api.main:app.openapi()["paths"]` — the real route table, not a source grep |
| console | paths referenced under `web/arkadia_console/src/**` |

Measured at `68403b9e`: legacy **127** / served **262** / console **46** (`id`
normalization) → target **73**. The `raw` normalization gives 72/71 and is a different
figure, not a better one.

**If any definition changes — a new archive path, a new served route, a widened console
scan root, or a normalization change — record a baseline migration.** A changed count is
then a *measurement* change, and presenting it as product progress would be false.

**Entry condition for any count claim:** quote the normalization variant alongside the
number, and re-derive rather than carrying a prior figure forward.
