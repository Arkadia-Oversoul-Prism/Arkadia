# NovaNet public field — declared engagement readings (reactions / comments / reposts)

Workstream 2 (NovaNet & Project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, shared contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: reconcile an archived Prism **product capability** the console
field lacks — the engagement readings the public transmissions feed already
returns but the console discarded. The archived Prism field card
(`archive/frontend/arkadia-prism/.../SocialFieldPage.tsx`) rendered four reaction
counters, a comment count and a repost count on every post; the console rendered
none of them, so engagement a reader could already fetch was invisible.

Authority: human retains merge, production deployment, and acceptance. Nothing
here claims any of the three.

Successor slice to `prism-novanet-author-controls-01` (same branch/PR #492,
draft). It adds one feature-local component and one page mount; it adds **no**
route, **no** endpoint-registry entry, **no** mutation and **no** authority.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, base `main`).
- `origin/main` at the start of this pass:
  `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`.
- Branch head before this slice: `e5e6871d` (`prism-novanet-author-controls-01`).
- Environment: node `v24.21.0`, pnpm `10.26.1`.

## 1. The precondition — the shape is declared and served (measured)

The feed handler was read (`api/transmissions.py`):

- `list_transmissions` (`GET /api/transmissions`) returns `_hydrate_post(p)` for
  each post, and the create handler seeds the record with
  `"reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0}` and
  `"comments": [], "reposts": 0`. `_hydrate_post` only rewrites the `author`
  block, so these readings survive to the client unchanged.
- The reaction vocabulary is the backend's own:
  `valid = {"heart", "fire", "star", "mind"}` in `react_to_transmission`.

**Scope decision (recorded, not silently made).** `reactions` and `comments`
each have a live write handler on the router (`POST .../react`,
`POST .../comment`). `reposts` has **no** write handler — a grep of the router
shows no repost route. This slice is therefore **read-only readings only**: it
renders what is served and adds no control. Wiring the reaction/comment write
paths is a separate bounded slice and is explicitly not done here, so nothing is
offered that the client cannot prove. (`reposts` is shown as a reading with no
control, per the lane's standing rule: do not invent a capture path for a
capability with no verified write route.)

## 2. The change

- New `web/arkadia_console/src/components/novaNet/EngagementBar.tsx` —
  display-only. It iterates `REACTION_TYPES = ["heart","fire","star","mind"]`
  (the backend's keys, in its order), renders each count, the comment count and
  the repost count, and invents no value: a reaction the server did not return
  reads `reactions?.[type] ?? 0`, and `reposts` is read only when it is a number.
  It performs no request (`apiRequest` is absent; no `method:` token) — a reading
  surface must not mutate.
- `web/arkadia_console/src/pages/NovaNetPage.tsx` — mounts
  `<EngagementBar transmission={t} />` under each transmission's content, above
  the existing author controls.

No shared file (`endpoints.ts`, `types.ts`, router, `surfaces.ts`, `App.tsx`)
was touched — `types.ts` already declares `reactions`, `comments` and `reposts`
on `Transmission`.

## 3. Proof

- New guard: `tests/test_prism_novanet_engagement_readings.py` — **10 passed**.
  It asserts the backend's declared shape, that the surface is read-only, that
  the vocabulary is the backend's four keys, that no count is invented, and that
  the page mounts it. Each claim carries a **negative control** (a synthetic
  mutating bar, a fabricated count, a divergent vocabulary, a dropped mount)
  proven against the same detector.
- Lane 2 + wiring + contract suite:
  `pytest tests/test_prism_console_ci_wiring.py tests/test_prism_novanet_author_controls.py tests/test_prism_opportunity_entry_flow.py tests/test_prism_opportunity_radar_module.py -q`
  — **145 passed**.
- The guard is inside the derived console-contract domain
  (`python scripts/console_contract_domain.py`) — 22 guards, up from 21 — so the
  gate executes it and the wiring judge verifies it. No gate edit was needed; the
  domain is content-derived.
- Frontend: `corepack pnpm build` (`tsc --noEmit && vite build`) — **succeeds**
  (102.46 kB app bundle), so the new component type-checks.

## 4. Regression boundary

Additive only: one new feature-local component, one import, one mount, one new
test module. No existing test node changed. `api/main.py` and every backend file
are untouched.

## 5. Remaining uncertainty

- Reaction / comment **write** paths are declared and served but deliberately not
  wired in this slice; they are the next bounded candidate, pending a proof that
  the client can offer them without a decorative (403-ing) control.
- `reposts` has no handler at all, so it will never gain a control.
