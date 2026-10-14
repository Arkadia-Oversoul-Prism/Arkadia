# Lane 2 — NovaNet public-field composer (create a transmission)

**Workstream:** Prism UI reconciliation (Lane 2 — NovaNet + Project Opportunity Radar).
**Branch:** `feat/prism-next7-02-pipeline-strip` (PR #492, draft). Continues the active
lane PR rather than reopening a merged/closed one.
**Base observed:** `main` @ `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1`
("feat(solariun): add runtime and personal memory lenses").

## Objective

Reconcile the archived Prism field's **create path** into the active console. PR #492's
lane history reconciled the field's *read* side (declared engagement readings, author-only
edit/delete) and then its *write* side for react/comment. The composer that **originates**
a public transmission — the first control the archived field renders — was never
reconciled, so an authenticated reader could reply to a post yet not author one.

## Evidence-backed defect / need

- The archived product gates a composer on the verified identity
  (`archive/frontend/arkadia-prism/web/public_prism/src/pages/SocialFieldVerified.tsx`:
  `const canTransmit = Boolean(isAuthenticated && profile);` -> `{canTransmit ? <Composer ...> : ...}`).
- The active console (`web/arkadia_console/src/pages/NovaNetPage.tsx`) rendered the field
  with engagement readings and author controls but **no** create control
  (`grep -rn "TransmissionComposer\|novanet-transmission-composer" web/arkadia_console` -> 0
  before this change).
- The create contract is declared, live and verified on `api/transmissions.py`:
  - `POST /api/transmissions` — body `{content, author}`; blank content -> `400`; response
    `{"transmission": {...}}`. The author block is projected server-side
    (`_author_block(body_author, uid)` from the verified Firebase uid), so the client does
    not author the identity it stores.

## Change

- **new** `web/arkadia_console/src/components/novaNet/TransmissionComposer.tsx` —
  feature-local composer. Exactly **one** write call (`POST` on the
  `endpoints.transmissions` registry collection; no inline literal). Renders the composer
  **only** for an authenticated caller (`isAuthenticated`); an anonymous reader gets a
  stated sign-in line (`novanet-transmit-signin`) instead of a decorative control. A
  refusal renders (`novanet-transmit-error`) and an auth failure is named (`AUTH_REQUIRED`)
  rather than shown as a fault. The client never sends an `owner_uid` — the backend
  resolves ownership.
- `web/arkadia_console/src/pages/NovaNetPage.tsx` — mounts `<TransmissionComposer
  isAuthenticated={isAuthenticated} profile={profile} onCreated={() => field.reload()} />`
  so a create re-reads the feed and the server's own list/count is shown (no optimistic
  client-appended row).
- **new** `tests/test_prism_novanet_transmission_composer.py` — 12 nodes pinning the create
  contract, each behavioural claim with a **negative control** (second write path, inline
  path, ungated composer, swallowed refusal, dropped mount).

## Changed-path inventory

| Path | Change |
| --- | --- |
| `web/arkadia_console/src/components/novaNet/TransmissionComposer.tsx` | new (feature-local, lane-2 owned) |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | mount + auth gate pass-through |
| `tests/test_prism_novanet_transmission_composer.py` | new guard |
| `docs/control-plane/evidence/prism-novanet-transmission-composer-01/EVIDENCE.md` | this record |

No shared shell file (`App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`,
`lib/types.ts`, `SurfaceLenses.tsx`) was touched — they are **referenced**, never edited.
No backend file was touched: the route already exists.

## Tests / proof (measured)

- `python -m pytest tests/test_prism_novanet_transmission_composer.py -q -rEf` -> **12 passed**.
- `python -m pytest tests/test_prism_console_ci_wiring.py tests/test_prism_novanet_author_controls.py
  tests/test_prism_novanet_engagement_readings.py tests/test_prism_novanet_transmission_composer.py -q -rEf`
  -> **66 passed**.
- `python -m pytest tests/architecture -q` -> **11 passed** (unchanged).
- Console-contract domain: `python scripts/console_contract_domain.py --json` -> **24**
  guards (was 23). The new guard is derived into the domain, so
  `.github/workflows/prism-console-contract.yml` executes it **without a workflow edit** —
  the derivation (`scripts/console_contract_domain.py`, introduced by PR #435) is exactly
  what removes the hand-maintained-list drift class. Wiring judge: **passed**.
- Frontend build: `cd web/arkadia_console && corepack pnpm install && corepack pnpm build`
  -> `tsc --noEmit` clean, `vite build` -> `84 modules transformed`,
  `dist/assets/index-BrpIZSoQ.js` (107.22 kB). Built-bundle marker check:
  `novanet-transmit-composer` / `novanet-transmit-signin` present (1 line each); the
  pre-change control literal `canTransmit` is **0** — the archived name did not survive
  into the console, confirming the marker is a new surface, not a rename.
- CP10 mutation boundary:
  `printf '<each new path>\n' | python scripts/cp10_mutation_boundary_policy.py --judge`
  -> `PASS`, exit **0**.
- `web/arkadia_console/dist/` is **untracked** (`git ls-files web/arkadia_console/dist` ->
  0); the local build leaves a clean tree.

## Boundaries kept

- **No new write path invented.** Exactly one `apiRequest` call; no second mutation path.
- **No shared file touched** — lane-1 owned files referenced only, per `SHARED-CONTRACTS.md`.
- **No test weakened.** The guard adds assertions and negative controls; none removed.
- Draft PR; no merge, deploy, or production acceptance claimed.

## Remaining uncertainty

- The composer's runtime behaviour against the **canonical deployment** is **NOT TESTED**
  (no identity credential in this sandbox, and the Render origin is the serving path). The
  proof here is source-level plus a clean typecheck/build — consistent with the repo's
  established console-guard convention, and not a production claim.
- Whether the archived composer should also carry attachment / audience affordances is
  **UNKNOWN**; only the text create path is verified on `api/transmissions.py`, so nothing
  else is wired (a control with no verified handler would be decorative).
- Baseline debt on `main` was not repaired or attributed to this change; the delta is the
  new guard's own nodes only.

## Full-suite attribution (measured, one pass — no second full run)

`python -m pytest tests/ -q -rEf --continue-on-collection-errors` at head `d4b9c1fe`:

```
8 failed, 3032 passed, 17 skipped, 2 warnings, 1 error in 217.03s
```

Failing/error node set (9 nodes) sha256
`c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`.

The same seven files that carry those nodes were then measured on a detached worktree at
`origin/main` (`2a1bca75`) in the **same environment** — `8 failed, 35 passed, 1 error` —
and the sorted failing/error node list is **byte-identical** (`diff` empty, same sha256):

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

Zero node-set delta; no node from this change's guard is in the failing set. The absolute
counts (`3032 passed` here vs the lower totals recorded in `AGENTS.md`) are
dependency-set dependent in this sandbox — **compare node identity, never totals**. This is
a record of pre-existing `main` debt, not attributed to, and not repaired by, this slice.
