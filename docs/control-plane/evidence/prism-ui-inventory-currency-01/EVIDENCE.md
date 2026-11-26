# Prism UI inventory currency — the roadmap described a console that did not exist

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 05
- **Observed:** 2026-11-23T18:1xZ
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** `ark-ops-continuous-001-cycle-01` … `-cycle-04` (carried on the open
  contract-record branch/PR #705).

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /repos/…/commits/main`; local `HEAD` agrees |
| open PRs | **29**, all draft, all `base: main` | `GET /pulls?state=open` |
| production revision | `source_revision = bb19aabd…`, `revision_source: RENDER_GIT_COMMIT`, `revision_conflict: false` | `GET https://arkadia-qzu4.onrender.com/api/version` → 200, 643 B |
| production liveness | `{"status":"radiant","path":"/health"}` | `GET /health` → 200 |
| deployed route table | **300** paths | `GET /openapi.json` |
| local route table | **300** paths, identical `/solspire/buyer-recon*` set | `api.main.app.openapi()` |

Source ↔ running revision is **VERIFIED** for this revision. That is necessary evidence of
consistency; it is **not** proof of application correctness and **not** deployment acceptance.

### 1.1 Console → backend coherence re-measured (no defect found)

- Every path in the two endpoint registries (`src/lib/endpoints.ts` 45 entries,
  `src/operator/api/endpoints.ts`) resolves in the deployed `app.openapi()`, **0 unserved**,
  including the derived helpers (`/api/lab/engineering/canvas/{id}`,
  `/solspire/projects/{id}/{runtime-context,tasks,files,events,conversations}`).
- The call sites that name a method match the served operation: `/api/transmissions/{post_id}`
  serves `PATCH`+`DELETE`, `/api/operator/security-verification` `GET`,
  `/api/lab/engineering/n-atlas/{test-session,run}` `POST`.
- A scan of **103** route literals in `web/arkadia_console/src` found 10 non-matches; all 10 are
  either base prefixes used for concatenation (`/solspire`, `/api/job/${…}`) or the four
  **honest** "this contract is not served" disclosures around `/api/codex/categories`
  (`SpiralCodexPanel.tsx`, `spiralCodexContract.ts`) — that route is indeed absent from the
  deployed spec, so the copy is correct.
- All **15** declared surface paths serve the SPA on production (`Accept: text/html` → 200,
  1256 B, `<title>ARKADIA</title>`), including `/enterprise` and `/n-atlas-lab`.

No unowned defect was found in the console↔backend contract. The gap was in the artifact that
directs the work.

## 2. The defect measured

`docs/control-plane/overnight/PRISM-UI-INVENTORY.md` §2 is the route/capability matrix the
reconciliation workstream is chosen from. It disagreed with the console's own declaration in
both directions.

### 2.1 Rows that called a reconciled capability `MISSING`

| legacy route | row said | console actually does |
|---|---|---|
| `/encyclopedia`, `/spiral-codex` | `MISSING`, surface `—` | `LENS_ALIASES` → `novanet` + `codex` lens; `NovaNetPage.tsx` header says the lens **is** reconciled over `GET /api/codex` |
| `/settings`, `/account` | `MISSING`, surface `—` | `settings` surface at `/settings` (`SettingsPage.tsx`, 223 lines); `/account` is a `PATH_ALIASES` entry |
| `/personal-echofeild`, `/echofeild-matrix` | `MISSING`, surface `—` | `solariun` `memory` lens → `PersonalFieldPanel` |
| `/dashboard` | `MISSING`, surface `—` | `solariun` `overview` lens → `SolariunOverview`, whose header names the archived cockpit |

The `/settings` row also carried a **stale contract claim**: it advertised `/api/keys` and
`/api/provider-keys`, which `SettingsPage.tsx` never reads. It reads `/api/me`,
`/api/me/ais-profile`, `/api/sources`, `/api/knowledge/providers` and `/solspire/workspace` —
all five served.

### 2.2 Surfaces the document never mentioned

`/workspace`, `/projects`, `/operator`, `/n-atlas-lab` are declared in `surfaces.ts` and served
in production, and appeared nowhere in the inventory. An inventory that omits live surfaces
cannot be used to decide what to build next — and a stale `MISSING` row sends the next pulse to
rebuild something that already exists.

## 3. The correction

`docs/control-plane/overnight/PRISM-UI-INVENTORY.md`:

- the five stale rows now name the resolving surface, its canonical path, the contract the
  surface actually reads, and `PARTIAL` (reconciled but narrower than the archived module);
- the "no legacy counterpart" paragraph became a table enumerating all six new-architecture
  surfaces (`workspace`, `projects`, `engineering-lab`, `weaver`, `operator`, `n-atlas`);
- §9 records the measurement, the superseded figures (§3's "288 paths" → **300** now; §4's page
  line counts → **229/475/148/88**), and the non-claims.

No product code, `api/main.py` line, or deployment configuration was changed.

## 4. The guard

`tests/test_prism_ui_inventory_currency.py` derives its domain from the live declarations:

- `declared_surfaces()` parses `SURFACES` from `surfaces.ts`;
- `path_aliases()` / `lens_aliases()` parse `router.ts` (comment lines stripped, so a prose
  example cannot be read as a declaration);
- `matrix_rows()` / `surface_table()` parse the inventory's §2.

It fails when a declared surface is unaccounted for; when the document names an undeclared
surface or a wrong path; when a `MISSING` row names a surface; when an `IMPLEMENTED`/`PARTIAL`
row names none; and **when a `MISSING` row covers a legacy route the router resolves** through
a declared path, `PATH_ALIASES` or `LENS_ALIASES`. A parser that finds fewer than 10 surfaces
or 20 rows raises rather than passing vacuously.

### 4.1 Controls (the part that makes it a guard)

| control | input | result |
|---|---|---|
| live negative | `git show main:docs/…/PRISM-UI-INVENTORY.md` | **9 findings** — 5 unaccounted surfaces + 4 resolved-but-`MISSING` routes (`/encyclopedia`, `/spiral-codex`, `/settings`, `/account`) |
| live positive | this branch's document | **0 findings** |
| synthetic negative | the pre-repair rows verbatim, plus `/offerings` (`MISSING`, unresolved) | `/encyclopedia` and `/settings` reported; `/offerings` **not** reported |
| planted defect | one repaired row reverted to `MISSING`/`—` | `/settings` reported; unplanted tree silent |
| invented surface | table + `("dashboard", "/dashboard")` | reported as undeclared |
| dropped accounting | table minus `operator` | `'operator'` reported unaccounted |

The last two rows of the negative control matter: a detector that flags every `MISSING` row
would pass the first assertion while proving nothing. `/offerings` is a `MISSING` row whose
route the router genuinely does not resolve, and it must stay silent.

## 5. Wiring — the guard must be executed, and its input must select the gate

- `scripts/console_contract_domain.py` derives **75** guards (was 74); the new guard is in the
  derived set, so `prism-console-contract.yml` executes it through
  `pytest $(python scripts/console_contract_domain.py)` with **no** restated list.
- The guard reads the inventory document, so the document was added to **both** `paths:`
  filters of that gate. Otherwise a doc-only edit — exactly the drift this guard judges — would
  run no gate. This is the recorded class: *a workflow's trigger filter must name every input
  its guard reads.*
- `tests/test_prism_console_ci_wiring.py` re-run after the domain grew: **passes**.

## 6. Checks executed

| check | result |
|---|---|
| `tests/test_prism_ui_inventory_currency.py` | **5 passed** |
| console/routing/architecture bundle (`test_canonical_frontend_routing`, `test_console_endpoint_registry_contract`, `test_console_legacy_route_coverage`, `test_prism_console_ci_wiring`, `tests/architecture`) | **94 passed** |
| guard bundle (`test_prism_ui_inventory_currency`, `test_prism_console_ci_wiring`, `test_ci_gate_trigger_coverage`, `test_workflow_injection_boundary`, `test_console_endpoint_registry_contract`, `tests/architecture`) | **220 passed** |
| CP10 mutation boundary (`--judge` on the three changed paths) | **PASS** (exit 0) |
| full suite (`-q -rEf --continue-on-collection-errors`) | see §6.1 |
| `python -m py_compile api/main.py` | not applicable — `api/main.py` untouched (`2597` lines, budget 2600) |

### 6.1 Full suite

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 19 failed, 4255 passed, 22 skipped, 6 warnings, 1 error in 290.38s (0:04:50)
```

Against cycle 04's same-SHA measurement (19 failed / 4250 passed / 22 skipped / 1 error) the
delta is **+5 passed and nothing else**, and `--collect-only` on the new module reports **5**
nodes, so the delta is exactly this change.

The failing/error set is **20 nodes**, with the same composition cycle 04 classified:

| node(s) | count | classification |
|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | **sovereign-reserved** — CE-01 `weaver.autonomy` module-vs-package collision |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | **sovereign-reserved** — FINDING F-01 |
| `tests/test_identity_spine_w1.py::…`, `tests/test_m02_reasomate_truth.py::…` | 2 | owned by open **#700** |
| `tests/test_m01_persistence.py::…`, `tests/test_m05_files.py::…` | 2 | owned by open **#690** |
| `tests/test_solspire_r1_governance_convergence.py::…` | 2 | owned by open **#693** |
| `tests/test_solspire_r3_execution_runtime.py::…` | 1 | owned by open **#691** |
| `tests/test_static_ingestion_idempotency.py::…` | 1 | owned by open **#698** |
| `tests/test_mission_lifecycle_adapter_contract.py::…` | 10 | **environment-only** — needs `web/arkadia_console/node_modules/typescript`, absent in this sandbox |

No unowned, non-reserved node is left, and no node is attributable to this change.

**Hash convention, named rather than assumed.** The outcomes-set sha256 measured here is
`0481fdc3…`, not cycle 04's `8d70e46e…`, for the *same 20 node identities*. The cause is
formatting, not drift: this sandbox runs pytest 9.2.0, whose short summary appends a reason to
one node — `tests/test_m05_files.py::test_update_file_supports_rename - TypeError:...`. A
fingerprint that includes the summary line is therefore a function of the pytest version as
well as the tree. Attribute by node identity; treat a hash mismatch between environments as
unproven until the node lists are compared (they are identical here).

## 7. Explicit non-claims

- No merge, no deployment, no production acceptance. This is a draft PR.
- The console was not rebuilt in this pass; nothing here claims what the deployed SPA renders
  beyond the `/api/version` revision identity recorded in §1.
- The `PARTIAL` statuses are an assessment of capability coverage, not a verification of the
  rendered product.
- No Vercel path was used, promoted, or treated as evidence (ADR-016).
