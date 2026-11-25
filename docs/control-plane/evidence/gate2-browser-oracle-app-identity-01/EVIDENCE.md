# Gate 2 browser observation — the oracle scored a retired application

**Contract:** ARK-OPS-CONTINUOUS-001 (continuous reconciliation & gap-closure)
**Observed:** 2026-11-25
**main at observation:** `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T18:30:03+01:00,
`governance(GOV-04): bounded merge delegation with exact-head safeguards (#722)`)
**Canonical production:** `https://arkadia-qzu4.onrender.com` (ADR-016)
**Authority:** none exercised. No merge, no deployment, no acceptance.

---

## 1. Production boundary at this revision

| Link | Classification | Evidence |
|---|---|---|
| current `main` resolved | **VERIFIED** | `git rev-parse origin/main` = `fd0a4fd…`; local `HEAD` identical |
| runtime ↔ source revision | **VERIFIED** | `GET /api/version` → `source_revision: fd0a4fdc081064b2074aab9e17b4c7841736dd9f`, `revision_source: RENDER_GIT_COMMIT`, `revision_conflict: false` |
| alias reachable | **VERIFIED** | `GET /` → HTTP 200 after one cold-start `503` (see §1.1) |
| served SPA assets | **VERIFIED** | shell references `/assets/index-CYGHeCpJ.js` (426232 B), `/assets/index-BJojPKi_.css` (91922 B), `vendor-react-nf7bT_Uh.js`, `vendor-firebase-DNJjg0gV.js` — all HTTP 200 |
| all 15 declared surfaces served | **VERIFIED** | every path in `src/lib/surfaces.ts` returns `200 text/html` (1256 B shell) at the FastAPI origin |
| main → deployment identity (GitHub deployments API) | **UNKNOWN** | 0 Production deployment records — the Vercel integration is disconnected by design (ADR-016) |
| browser-rendered UI correctness | **OBSERVED (this pass)** | independent browser observation, §5 — the harness itself is `BLOCKED` on playwright here |

### 1.1 Cold start is not an outage

The first request returned `503` and the second (12 s later) returned `200` on the same
revision. This is the already-recorded warming-deployment class
(`gate2-alias-cold-start-classification-01`), not an unreachable alias. Recorded so a future
pulse does not re-diagnose it as a production failure.

---

## 2. The defect

`scripts/gate2_browser_observation.py` is the only harness that exists to close the standing
`browser-rendered UI correctness = UNKNOWN` boundary. Its route table, its anchor table and its
freshness oracle all described the **archived Prism frontend**, not the application the
canonical origin serves.

Measured at `fd0a4fd`:

| Probe | Result |
|---|---|
| anchors present in `archive/frontend/arkadia-prism/web/public_prism/src` | **6 / 6** |
| the same anchors present in `web/arkadia_console/src` | **0 / 6** |
| routes that are declared console surfaces (`/`, `/oracle`, `/nexus`, `/solariun`, `/solspire`, `/spiral-codex`) | **2 / 6** (`/` and `/solariun` only) |
| `/solspire` at the canonical origin | reserved backend namespace; the console surface is `/enterprise` |

Four independent consequences, all in one file:

1. **Wrong routes.** `/oracle`, `/nexus`, `/spiral-codex` are not console surfaces, and
   `/solspire` is a reserved API prefix the SPA is refused on. Probing them cannot report
   anything about the console.
2. **Wrong anchors.** Six Prism literals (`become one continuous field`,
   `pattern intelligence`, …) that the console does not contain. Scoring the console against
   them fails on a correct application.
3. **The freshness oracle certified the wrong list.** `source_anchors_present()` read the
   *archive* tree, so it reported every anchor present and `stale_anchors: []` — a green
   certificate for a table that could not match the served app. A freshness check scoped to a
   different application is not a freshness check.
4. **Staleness was computed and then ignored.** `stale` was printed in the text branch and
   recorded in JSON, but it never affected the verdict or the exit code. The "a guard that
   prints a verdict but does not act on it is not a guard" class.

The harness was correct when it was written: its own evidence
(`gate-hygiene-gate2-production-parity-02`, PR #143) records
"**browser-rendered UI OBSERVED** (§11, 6/6 routes)" against a Render alias serving **Prism**.
Prism was archived at `c081d200` (2026-10-11) and the origin now serves the console. That
result is therefore **STALE** — bound to a superseded application, not to current production.

The failure direction is the dangerous one: a sentinel whose anchors default to *absent* turns
a harness defect into a production alarm ("the UI stopped rendering") that is
indistinguishable from the real regression it was built to catch.

---

## 3. The repair

Bounded to one script and its fitness tests. No route, backend, authority or deployment change.

- `ANCHOR_APP = web/arkadia_console` — the application the canonical origin serves. The anchor
  table is scoped to it, and `source_anchors_present()` now reads *that* tree.
- The route table is six declared console surfaces, each carrying `(anchors, provenance, state)`.
  Two render states are declared rather than inferred:
  - `public` — the surface renders its own copy to an anonymous visitor;
  - `auth_threshold` — the surface is protected (`requiresAuth` in `surfaces.ts`), so
    `App.tsx::AuthThreshold` renders the shared sign-in threshold *instead of* the surface's own
    copy. Scoring a protected route against its own subtitle would fail on a correct app.
- **Staleness now fails closed.** A stale anchor list, or a missing app source tree, returns
  `browser_rendered_ui: STALE` and exit `2` **before the probe runs**, and no route is scored.
- The benign-exemption reason now names the console module that records the unserved route
  (`components/novaNet/spiralCodexContract.ts`) instead of a Prism-era component.
- `playwright_available()` reports the line that names the cause
  (`Cannot find module 'playwright'`) instead of Node's version banner.

---

## 4. Verification

### 4.1 Harness behaviour

```
$ python3 scripts/gate2_browser_observation.py
browser-rendered UI: BLOCKED -- playwright unavailable: Error: Cannot find module 'playwright'
EXIT=2
```
`anchor_app: web/arkadia_console`, `stale_anchors: []`. `BLOCKED` is correct here: playwright is
not installed in this sandbox, and the harness now says so instead of scoring.

### 4.2 Tests — 14 → 22 nodes

```
$ python3 -m pytest tests/test_gate2_browser_observation.py -q
22 passed
```
`--collect-only` measures the delta rather than inferring it: **14** at `fd0a4fd` → **22** on
the branch (+8, exactly the new nodes).

New/rebound assertions, each derived rather than restated:

- `test_every_route_is_a_declared_console_surface` — parses `src/lib/surfaces.ts` at test time;
  a route the console does not declare fails.
- `test_route_render_state_matches_the_surface_auth_flag` — the declared state must agree with
  the surface's own `requiresAuth` flag, so the two cannot drift.
- `test_both_render_states_are_covered` — both render paths stay exercised.
- `test_the_retired_prism_routes_are_gone` — negative control against re-adopting `/oracle`,
  `/nexus`, `/spiral-codex`, `/solspire`.
- `test_anchor_source_is_the_console_not_the_archive` — the Prism-only literal must be present
  in the archive and absent from the console, so the control is discriminating.
- `test_stale_anchor_list_fails_closed` / `test_a_current_table_is_not_reported_stale` — a
  paired control proving the guard bites *and* is not trivially true.
- `test_no_retired_deployment_host_is_referenced` — the retired `arkadia-kw64` alias, which one
  pre-existing test still embedded, must not appear in the harness.

### 4.3 Live negative controls on the real file

| Control | Result | Tests |
|---|---|---|
| `ANCHOR_APP` pointed back at the archived Prism tree | harness → **STALE**, refuses to score | 4 failed, 18 passed |
| a retired Prism route (`/oracle`) re-added | route not declared by the console | 5 failed, 17 passed |
| restored byte-identically | — | 22 passed |

### 4.4 Adjacent suites

```
$ python3 -m pytest tests/test_gate2_browser_observation.py \
    tests/test_gate2_backend_observation.py \
    tests/test_gate2_production_observation.py tests/architecture -q
92 passed
```
Architecture suite **11 passed**. `api/main.py` untouched. CP10 mutation-boundary judge on the
three touched/added paths: **PASS**.

### 4.5 Full-suite baseline (pre-change, same environment)

```
22 failed, 4251 passed, 22 skipped, 1 error in 292.60s
```
The single collection error is the sovereign-reserved CE-01 `weaver.autonomy` module-vs-package
collision. Of the console-contract domain's 12 failures, **10** are environment-only
(`tests/test_mission_lifecycle_adapter_contract.py` requires
`web/arkadia_console/node_modules/typescript`, absent here) and **2**
(`tests/test_prism_w4_lab_pr_state.py`) fail because the ambient `GITHUB_TOKEN` falsifies their
"no token in the environment" premise — owned by open PR #683. Neither is touched here.

---

## 5. Independent live browser observation (this pass)

Playwright is unavailable, so the harness cannot probe. The boundary was therefore observed
directly against `https://arkadia-qzu4.onrender.com` at `fd0a4fd`, and every anchor in the
repaired table was confirmed to render. This is also the control that matters most: it proves
the *new* table does not repeat the defect.

| Route | State | Anchor | Observed |
|---|---|---|---|
| `/` | public | `one coherent application over the canonical backend` | **present** |
| `/about` | public | `one human-governed intelligence architecture` | **present** |
| `/novanet` | public | `the public field` | **present** (720 public echoes, 1 transmission; anonymous read) |
| `/operator` | public | `boundary posture, evidence, and authority` | **present** |
| `/login` | public | `authenticate against the canonical arkadia backend` | **present** |
| `/knowledge` | auth_threshold | `this surface requires an authenticated arkadia identity` | **present** (`PROTECTED SURFACE`, "Go to sign in") |

Had playwright been present, the repaired harness would report `OBSERVED` on 6/6 routes. That
statement is an inference from six measured anchors, not a harness run; the harness's own
verdict at this revision is **BLOCKED**.

A clipping artefact in the first screenshots (page titles appearing cut under the sticky
header) was **disproved**: the header is `sticky` and in-flow, and scrolling to the top renders
the title fully. Recorded so it is not re-raised as a layout defect.

---

## 6. Known gaps (recorded, not repaired)

1. **No workflow executes this harness.** `grep -rn gate2_browser_observation .github/` → 0
   matches; only its fitness tests reference it, and those run through broad-suite selection.
   Wiring a playwright job is a separate bounded change and would add a surface that can only
   report `BLOCKED` where playwright is absent.
2. **`scripts/gate2_production_observation.py` still reports
   `main -> deployment identity := UNKNOWN`** at a revision whose runtime publishes
   `source_revision == main`. That harness consults only the retired provider's deployment
   records and never reads `/api/version`. It is owned by open PRs #681 and #687 — recorded
   here, deliberately not edited.
3. **`SOURCE-LINEAGE CLOSURE` prints `all 0 candidate Production SHAs are its descendants:
   False`.** `lineage_closed()` is `bool(closure) and all(...)`, so an empty candidate set reads
   as a failed closure while the boundary classifier correctly returns `UNKNOWN`. Display
   wording only, same owned file.
4. **The Playwright probe is unexercised in this environment**, so `classify()` is proven by
   unit controls and the anchors by independent browser observation, not by an end-to-end run.

---

## 7. Disposition

- **No merge performed.** GOV-03/GOV-04 place merge execution with the human sovereign.
- **No deployment.** No provider configuration touched; Vercel not contacted.
- **No acceptance.** Production acceptance remains `NOT CLAIMED`.
- `api/main.py` untouched (budget unaffected).

**Next single bounded move:** wire a playwright-bearing job for
`scripts/gate2_browser_observation.py` so the repaired oracle executes under CI, or — if that
is judged out of scope — close gap 2 above once #681/#687 are dispositioned by the sovereign.
