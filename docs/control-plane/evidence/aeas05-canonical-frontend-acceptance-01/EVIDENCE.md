# AEAS-05 — Canonical Frontend Acceptance (pre-deployment stage)

Branch: `frontend/arkadia-console-01` (continuing PR #413) · base `main` =
`eb63342d1951e638b8952f4b66ea1308f052ed2f`.

This pass is the pre-deployment half of AEAS-05. It resolves the acceptance
gates that can be satisfied in the repository — the ones a production cutover
would otherwise have to assume. No production mutation was performed.

## Measured starting state (2026-10-11)

- `main` = `origin/main` = `eb63342d` (clean).
- PR #413: open, draft, mergeable, head `c081d200`; 15 check-runs on the full
  head SHA, 3 failing.

## Gate 1 — source honesty of the failing check-runs

Three check-runs failed on `c081d200`:

| check | classification |
| --- | --- |
| `N-ATLAS external beta validation` (run `38099353141`) | pre-existing / environmental (provider credential), not caused by this branch |
| `SG-02-FE.2-V` / `validate` (run `38099353157`) | **caused by this branch** — its browser gate now observed the console and asserted retired Prism copy |

The SG-02 failure is the load-bearing one and is repaired below.

## Gates 2–4 — application identity, build artifact, backend compatibility

### G2 — bind the observation to the application it measures

Two distinct app-identity defects were found and repaired:

1. **CP10 browser gate pinned retired copy.** `sg-02-fe-2-v.yml` asserted
   `UNAUTH_THRESHOLD = 'Enter the enterprise layer.'` — the retired Prism
   SolSpire sign-in copy — against the console, whose protected surfaces render
   `Sign in to continue`. The gate could never pass on the console. Rebound the
   threshold and the authenticated-lens route (`/engineering-lab`) to the console
   application.

2. **Gate-2 marker oracle was Prism-only.** `scripts/gate2_production_observation.py`
   declared one global `MARKERS` list (Prism literals) and scored *any* observed
   artifact against it. A console artifact therefore read `0` on every literal —
   a category error, not a regression. Introduced `MARKER_APPS` (per-app source
   root, dist root, and marker list with per-literal polarity); `markers_in`,
   `source_markers_present`, `local_bundle_markers`, and `classify_marker_oracle`
   are now scoped to the observed app. A reading whose literals are not the
   observed app's set is reported `NOT OBSERVED` (category error), never
   `CONTRADICTED`. The archived Prism build input is read under
   `archive/frontend/arkadia-prism/web/public_prism/` so Prism lineage stays
   observable after the move.

Live read-only harness run on this branch (alias still serves the pre-console
production build, so this is the *starting* classification, correctly reported):

```
main SHA                : eb63342d
newest Production deploy: c8abb28e  (STALE — predates main)
alias -> HTTP 200, manifest assets/index-BzLymmg4.js (892397 B)
artifact app: console   scoring against: console
  6 console literals   0  (expect>0)   <-- ABSENT  (served build predates console)
  "Enter the enterprise layer."   1  (expect 0)  <-- UNEXPECTED
marker-set oracle  : CONTRADICTED (markers absent from served artifact: ...)
build <-> source lineage : UNKNOWN
deployment build output observed : BLOCKED (Vercel SSO)
production acceptance : NOT CLAIMED (human authority)
```

This is the honest pre-cutover state: the served artifact is not the console, so
the console markers are absent and the retired control is present. It is not a
false `VERIFIED` and not a phantom regression.

Against the branch's own local console build the marker set scores
`VERIFIED (marker set observed in served artifact)` — every positive literal
present, control absent.

### G3 — build artifact

- `corepack pnpm build` in `web/arkadia_console`: PASS (tsc + vite).
- Every console marker literal survives minification in `dist/assets` (counts
  `1,1,1,1,2,2`, control `0`).

### G4 — backend compatibility

- No backend contract, route, persistence, or authorization change in this pass.
- `api/main.py` untouched; the console consumes the canonical FastAPI origin.

## Gates 5–7

- **G5/G6 (deployment + browser acceptance): BLOCKED on human authorization.**
  Merging and deploying PR #413 is a sovereign step. After deploy, acceptance
  requires `GET /api/version` matching the merged `main` SHA plus a browser read
  of `/`, `/arkana`, `/solariun`, and `/engineering-lab`.
- **G7 (rollback): VERIFIED.** The archived Prism app retains `package.json`,
  `vite.config.ts`, and `pnpm-lock.yaml` with a documented recovery procedure
  (`archive/frontend/arkadia-prism/README.md`; `git mv` history preserved).

## Additional defect found by this pass

The console had **no sign-in surface and no protected-route gating** — a
protected contract was only attempted at fetch time. Added `SignInPage.tsx`
(carrying the CP10 gate testids) and an `AuthThreshold` gate in `App.tsx`,
driven by a `requiresAuth` flag per surface. There is still no development
bypass: when Firebase is not configured the form is not offered.

## Verification

- Full suite `-q -rEf --continue-on-collection-errors`, branch vs a clean `main`
  worktree: **52 failing/error nodes on both; `comm -3` empty** — zero node-set
  delta.
- `tests/test_aeas05_canonical_frontend_acceptance.py` (11 tests): PASS. Proven
  to bite — restoring the retired threshold string reddens 2 of its controls
  (restored byte-identically afterwards).
- Architecture suite: 11 passed.
- CP10 mutation-boundary judge over all changed paths: PASS (exit 0).
- `python -m py_compile scripts/gate2_production_observation.py`: PASS.

## Boundaries held

- No production cutover. Repository-source only.
- Authorization unchanged — no bypass, no weakened boundary.
- Providers unchanged — no simulated inference.
- Proposal / approval / execution / verification remain distinct.
- Persistence and ownership boundaries untouched.
