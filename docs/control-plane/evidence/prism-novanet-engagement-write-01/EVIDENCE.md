# Lane 2 — NovaNet interactive engagement (reactions + comments)

**Workstream:** Prism UI reconciliation (Lane 2 — NovaNet + Project Opportunity Radar).
**Branch:** `feat/prism-next7-02-pipeline-strip` (PR #492, draft). Continues the
active lane PR rather than reopening a merged/closed one.
**Base observed:** `main` @ `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`.

## Objective

Reconcile the archived Prism field card's **interactive engagement** into the active
console. PR #492's own `EngagementBar` docstring deferred exactly this as "a separate
bounded slice": the field rendered the declared readings read-only, so a product
interaction the archived card had — react to a post, reply to a post — was missing
even though both write handlers are live.

## Evidence-backed defect / need

- The archived Prism card (`archive/frontend/arkadia-prism/web/public_prism/src/pages/NovaNetPage.tsx`)
  had a `PostCard` where each reaction glyph was a button and the comment count toggled
  a thread with a composer.
- The active console (`web/arkadia_console/src/components/novaNet/EngagementBar.tsx`)
  rendered the same readings as static `<span>`s. The two write handlers the console
  never called are declared, live, on `api/transmissions.py`:
  - `POST /api/transmissions/{post_id}/react` — `{type}` over `{"heart","fire","star","mind"}`, 400 otherwise.
  - `POST /api/transmissions/{post_id}/comment` — `{content}`, 400 on blank.

## Change

- `web/arkadia_console/src/components/novaNet/EngagementBar.tsx` — the four reaction
  readings become buttons calling `react`; the comment count toggles a thread with a
  composer calling `comment`. Both paths are composed from `endpoints.transmissions`
  (registry-derived, `encodeURIComponent`-guarded). `reposts` stays a **reading with no
  control** — the router declares no repost write handler. Counts still read the
  server's own `0` when absent.
- `web/arkadia_console/src/pages/NovaNetPage.tsx` — mounts `<EngagementBar … onChanged={field.reload} />`
  so a write re-reads the feed and the server's counts are shown.
- `tests/test_prism_novanet_engagement_readings.py` — rewritten to pin the interactive
  contract: exactly two write paths, no third unverified route, registry-derived paths,
  no invented counts, and `reposts` carries no control.

## Tests / proof

- `python -m pytest tests/test_prism_novanet_engagement_readings.py tests/test_prism_novanet_author_controls.py -q -rEf` → **24 passed**.
- `python -m pytest tests/test_prism_console_ci_wiring.py tests/test_prism_novanet_author_controls.py -q -rEf` → **39 passed**.
- Frontend typecheck: `cd web/arkadia_console && npx tsc --noEmit` → **exit 0**.
- Console-contract domain: `python scripts/console_contract_domain.py --json` → **23** guards
  (the engagement guard is already in the derived domain, so the CI gate executes it
  without any workflow edit).

## Boundaries kept

- **No new write path invented.** Only the two handlers the router serves are wired; a
  guard asserts the component makes exactly two `apiRequest` calls and that no repost
  route exists on the backend.
- **No shared file touched.** `lib/endpoints.ts`, `lib/types.ts`, `App.tsx` etc. belong to
  Lane 1 and were referenced, never edited.
- Draft PR; no merge, deploy, or acceptance claimed.

## Remaining uncertainty

- The reaction/comment interaction is proven at **source + typecheck + guard** level.
  No browser observation of the live field was made this pass (out of the lane's
  read-only budget); the runtime behaviour of `react`/`comment` against a live post is
  NOT TESTED here.
