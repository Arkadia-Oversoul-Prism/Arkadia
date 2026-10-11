# Workstream 1 — shared endpoint/route contract reconciliation (next2, pass 2)

**Status:** implementation + evidence. No merge, deployment, or acceptance.
**Prepared:** 2026-10-11
**Branch:** `feat/prism-next2-01-shell-contract-map` (PR #429, draft)
**Base:** `main` `f390526ab14e122fef358ef9b9e1cd438509463c`
**Instruction:** `docs/control-plane/parallel-ui/AGENT-01-SHELL.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (§3, §8)

## 0. Revision binding

| Item | Value | How measured |
|---|---|---|
| `main` | `f390526ab14e122fef358ef9b9e1cd438509463c` | `git rev-parse origin/main` |
| This branch, before this pass | `616aeae9e3885e330e873f098ab989f1e7551ad4` | `git rev-parse HEAD` |
| PR #429 | open, draft, `mergeable: true` | `GET /repos/.../pulls/429` |
| PR #430 head | `e6780d47af247b994fb76f0ef921fb99527dbac3` | `GET /repos/.../pulls/430` |
| PR #431 head | `a2024fbae7b5c993d0089364ad251f3dfe06a747` | `GET /repos/.../pulls/431` |
| PR #432 head | `dcb3e2f219e0b440be6b5f17081680790527f104` | `GET /repos/.../pulls/432` |

All three feature PRs are open, draft, and `mergeable: true`, each with **one** changed
file at this measurement (its own `AGENT-0N-*.md` instruction file). No feature-owned
source path is modified by any of them yet, so there is no current overlap to reconcile
beyond the recorded contract requests below.

## 1. What the three merged slices actually request (measured, not assumed)

Read from each slice's merged evidence on `main`, not from PR prose:

| Slice | Merge | Registry request |
|---|---|---|
| Shell/endpoints (W1 pass 1) | `67696372` | added `knowledgeSearch`, `labSessions`, `labAgents`, `labArtifacts`, `labGateway`, `labNAtlasCatalog`, `labSession(id)` |
| Opportunity (W2) | `11a81fb2` | **none** — `prism-parallel-02-opportunity-radar-01/EVIDENCE.md` §5: "No route, surface id, endpoint constant, or shared type is requested: the contract module carries its own paths and types" |
| Knowledge search (W3) | `3b606450` | none — reads `endpoints.knowledgeSearch`, which already existed |
| Arkana / Lab (W4) | `f390526a` | `labAutomations`, and a first-class `labCanvas(id)` / `labSession(id)` (`prism-w4-arkana-thread-history-01/EVIDENCE.md:391`) |

## 2. Served-route verification

Read from `api.main:app`'s served OpenAPI schema in this environment:

| Path | Methods | Verdict |
|---|---|---|
| `/api/lab/engineering/artifacts` | `get` | served |
| `/api/lab/engineering/artifacts/{artifact_id}` | — | **not served** |
| `/api/lab/engineering/canvas` | — | **not served** |
| `/api/lab/engineering/canvas/{artifact_id}` | `get` | served |
| `/api/lab/engineering/automations` | `get`, `post` | served |
| `/api/lab/engineering/automations/{automation_id}` | — | not served |
| `/api/lab/engineering/automations/{automation_id}/state` | `post` | served (mutation — deliberately unwired) |
| `/api/lab/engineering/sessions/{session_id}` | `get` | served |
| `/api/knowledge/search` | `post` | served (POST-only) |
| `/api/commune/resonance` | `post` | served (POST-only) |
| `/solspire/buyer-recon/projects/{project_id}` | `get` | served |

**The canvas route is a sibling, not a sub-resource.** This is the load-bearing finding
of this pass: `/engineering/canvas/{artifact_id}` is not `/engineering/artifacts/{id}`,
and the bare canvas root is not a route. Two consequences, both acted on:

1. A `labCanvasRoot: "/api/lab/engineering/canvas"` registry entry would be **rejected**
   by the served-path guard (`test_every_declared_endpoint_is_served_by_the_canonical_app`),
   because the app serves no handler at that exact path.
2. `labCanvas` therefore derives its base from the declared artifacts collection by
   substituting the terminal segment, and the substitution is asserted — a registry
   rename cannot degrade it into a silent no-op that composes a 404.

## 3. Changes in this pass

| File | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | `+labAutomations` entry; `+labCanvas(id)` builder derived from `endpoints.labArtifacts` with a substituted terminal segment; `labSession(id)` unchanged (re-verified) |
| `tests/test_console_endpoint_registry_contract.py` | `+_canvas_route_template` shared derivation; `+test_lab_canvas_builder_derives_from_artifacts_and_encodes`; `+test_lab_canvas_builder_composes_the_served_route`; `+test_registry_declares_the_automations_collection`; `+test_detector_flags_an_artifacts_sub_resource_canvas_path` (negative control) |
| `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` | §1 branch map head refreshed to `616aeae9`; **new §8** — reconciliation record (entries added, requests declined with reasons, recorded-not-repaired findings) |
| `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` | **new** "Measured contract facts" section so the next pass does not re-derive them |

### 3.1 Declined, with the reason

`buyerRecon: "/solspire/buyer-recon"` was drafted and then **reverted**. The owning
workstream explicitly declined a shared constant in its merged evidence, and the path is
handler-derived in `opportunityRadarContract.ts` from `solspire/buyer_recon_router.py`.
Adding it would create a *second* declaration of the same contract — the opposite of
reconciliation. Recorded in §8.2 rather than executed.

## 4. Verification (measured in this environment)

| Check | Command | Result |
|---|---|---|
| Endpoint-registry guard | `pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **15 passed** (was 11) |
| Focused contract set | `pytest tests/test_console_endpoint_registry_contract.py tests/test_console_shell_nav_contract.py tests/test_canonical_frontend_routing.py tests/test_aeas05_canonical_frontend_acceptance.py tests/test_prism_w4_lab_read_model.py tests/test_prism_w4_arkana_thread_history.py tests/test_lab_artifact_canvas_contract.py tests/test_lab_agent_registry_contract.py tests/test_knowledge_search_boundary.py tests/test_arkana_thread_history_contract.py -q -rEf` | **157 passed** |
| Architecture fitness | `pytest tests/architecture -q -rEf` | **11 passed** |
| Console typecheck | `corepack pnpm exec tsc --noEmit` | exit 0 |
| Console build | `corepack pnpm build` | exit 0 — 74 modules, assets emitted |
| CP10 admission | `scripts/cp10_mutation_boundary_policy.py --judge` on all four paths | PASS (exit 0) |

### 4.1 Live negative controls (both proven on the real file, then restored)

| Control | Mutation of `endpoints.ts` | Result |
|---|---|---|
| NC1 | remove the `labAutomations` entry | **1 failed** (`test_registry_declares_the_automations_collection`), 14 passed |
| NC2 | replace the canvas builder body with the pre-repair composition (append the id to the artifacts collection) | **2 failed** (`test_lab_canvas_builder_composes_the_served_route`, `test_detector_flags_an_artifacts_sub_resource_canvas_path`), 13 passed |

Both were restored byte-identically (`git status --porcelain` clean against the intended
diff) and the guard returned to 15 passed.

### 4.2 Baseline comparison — zero node-set delta

Both trees measured in **this environment**, same command, same dependency set
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`):

| | `main` @ `f390526a` (worktree) | this branch |
|---|---|---|
| Summary line | 27 failed, 2342 passed, 17 skipped, 1 error | 27 failed, 2346 passed, 17 skipped, 1 error |
| Failing/error nodes | 28 | 28 |
| Node-set sha256 | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | same |
| `comm -3` on the sorted `FAILED`/`ERROR` lines | — | **empty** |

The `+4 passed` (2342 → 2346) is exactly this file's added node count:
`--collect-only` → **15** on this branch vs **11** on `main`.

The 28 pre-existing nodes are unchanged and unrepaired: the `weaver.autonomy`
module-vs-package collection error, the two `tests/test_engineering_lab_api.py`
pins (`api/lab_routes.py` is an authority surface — sovereign-only), the
Landing/NodeEntry copy pins, and the `test_voice_*` set (missing optional
dependency in this sandbox). None is caused by, or repaired by, this pass.

## 5. Explicit non-claims

- No merge, no production deployment, no acceptance. Canonical production remains
  `https://arkadia-qzu4.onrender.com` (ADR-016).
- No Vercel deployment was created, promoted, or treated as evidence.
- No feature-owned path (`pages/NovaNetPage.tsx`, `components/opportunities/**`,
  Knowledge OS modules, Arkana/Weaver/Lab components) was edited.
- No backend authority, runtime, or deployment configuration was changed.
- The W4 read surface for automations is **not** mounted here; that is Workstream 4's
  bounded follow-up now that the registry entry exists.

## 6. Next bounded move

Taken in this pass (see §7): the registry guard's detector domain was widened from
`useHydration` arguments to `apiRequest` **literals** — the bounded, decidable half of
the gap recorded in §8.4. The remaining Workstream 1 candidate, the next shell/navigation
gap from the live inventory, is taken in §8 (router address-bar normalisation), landed
concurrently with §7.

## 7. Second bounded move — widened one-registry detector

`useHydration` always receives its path as a page-local expression, so the original
detector could judge every argument. `apiRequest` does not: its dominant shape is
`useHydration<T>(path, (p) => apiRequest<T>(p))`, where the path is a *callback
parameter* — not a page-local decision, and not decidable without interprocedural
analysis. The widened detector therefore flags **string and template literals only**
and leaves registry-derived expressions, parameters, and local bindings alone by
construction. A literal is precisely the second, unreviewed endpoint contract the guard
exists to catch.

| Check | Result |
|---|---|
| Registry guard | **17 passed** (was 15) |
| Live negative control | planting `apiRequest<VersionInfo>("/api/invented/route")` in `pages/HomePage.tsx` reddens `test_no_page_passes_a_literal_path_to_api_request`; restored byte-identically (`git status --porcelain` shows only the intended test edit) |
| In-source control | `test_request_detector_is_not_trivially_true` pins both polarities — a string literal **and** a template literal must be reported; five legitimate shapes (registry member, three parameter forms, the `useHydration` callback form) must not |

Without the in-source control, a detector that matched nothing would pass on any tree,
including one that inlines every path.

**Deliberately still out of scope:** `ProjectOpportunityRadar`'s `readPath` prop
(Workstream 2's composition) and `KnowledgeGraphPanel`'s `readGraph(path)` (Workstream
3's). Both receive their path from a caller; judging them is not a shell-owned decision.

*Superseded:* this section previously ended by proposing to migrate the two feature-local
canvas/session compositions (`LabArtifactCanvas.tsx:63`, `LabSessionList.tsx:86`) onto the
new helpers and to widen the detector domain. Both proposals are now taken — the widening
in §7, and the shell/navigation gap in §8. The helper migration remains the owning
workstream's edit and is not Workstream 1's to make.

---

## 8. Continuation pass — router address-bar normalisation (shell gap)

Appended after two concurrent passes on this branch landed while local work was in
flight: `9b1b3ef1` (the registry reconciliation) and `e8b0b77a` (the widened
one-registry detector, §7 above). Both were fetched and reconciled before this
section was committed; no work was duplicated.

### 8.1 Remote advance, and the duplicate dropped

| Item | Value | How measured |
|---|---|---|
| Branch head on remote at this pass's start | `9b1b3ef1312978d6103e74a2a9153cf391203614` | `git ls-remote origin` |
| Branch head in the working clone | `616aeae9e3885e330e873f098ab989f1e7551ad4` | `git rev-parse HEAD` |
| Divergence | `1 2` (remote ahead 1, local ahead 2) | `git rev-list --left-right --count origin/…...HEAD` |

`9b1b3ef1` added `labAutomations` and `labCanvas(id)` — the exact step-2 work — so the
duplicate local commit was **dropped** rather than re-landed, and the non-overlapping
work was rebased onto the remote head: `git rebase --onto 9b1b3ef1 abec3743 HEAD`.
After the rebase, `git diff --stat origin/… HEAD` → `router.ts` +14,
`test_console_shell_nav_contract.py` +109. `9b1b3ef1` touches neither file
(`git show --name-only 9b1b3ef1`), so there is no overlap between the two.

A **second** concurrent commit then landed mid-pass: `e8b0b77a` (the widened
one-registry detector, §7) — which was this pass's own identified next bounded task,
independently taken. It was fetched and reconciled the same way (`git rebase --onto
e8b0b77a 9b1b3ef1`), with one evidence-file conflict resolved by keeping **both**
sections: the remote's §7 and this pass's continuation, renumbered §8. No work was
duplicated, and nothing already pushed was reverted.

The guard this pass added is disjoint from `e8b0b77a`'s: that commit widens
`test_console_endpoint_registry_contract.py`'s `apiRequest`-literal detector, while this
pass adds the router-evaluation nodes to `test_console_shell_nav_contract.py`. Measured
after the second rebase: `git diff --stat origin/… HEAD` → `router.ts` +14,
`test_console_shell_nav_contract.py` +109, plus the three documentation files.

### 8.2 The gap

`useRouter` resolved a surface from an inbound pathname but never wrote the canonical path
back. `/nexus` (the declared legacy alias), a trailing slash, or an unrouted path rendered
the correct surface while the address bar kept the inbound value, so a copied or shared link
kept propagating a path no surface declares. The archived Prism normalised once on load
(`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:102 history.replaceState`);
the console owned no equivalent. This is a shell/navigation gap in Workstream 1's own
`lib/router.ts`, not a feature-page edit.

### 8.3 Change and guard

`lib/router.ts` (+14): one `useEffect` that resolves the inbound pathname and
`history.replaceState`s the canonical path when the two differ. `replaceState`, not
`pushState` — the inbound path is not a navigation the user can go back to. The rewrite is
conditional, so a canonical path is untouched.

The guard is an **evaluation, not a source-text pin**: `_js_route_resolver` strips type
annotations and runs the real, pure `resolvePath`/`routeForSurface`/`SURFACES` code in Node
over eight probes, then asserts each resolved path is a declared surface path or a section of
one. Pinned: `/nexus` → `/novanet`, an unrouted path → `/`, and a section path
(`/solariun/knowledge`) is not flattened. `_normalises_on_load` strips comments before
matching, so the call's name appearing in a comment cannot pass as the call.

Two defects in the guard's first draft are worth recording, because both are this
repository's recurring failure modes:

1. The detector matched `history.replaceState` **including in a comment**, so the
   negative control (which removes only the call) still read as "repaired". Fixed by
   stripping `//` comments before the match.
2. The Node probe passed the probe list through `process.argv[2]`, but `node -e` makes
   `argv[1]` the source and `argv[2]` the first extra argument — it received `undefined`
   and died in `JSON.parse`. Fixed by embedding the probes in the generated script.

### 8.4 Measurements

| Check | Command | Result |
|---|---|---|
| Shell-nav guard | `pytest tests/test_console_shell_nav_contract.py -q -rEf` | **28 passed** |
| Both guards together | `pytest tests/test_console_shell_nav_contract.py tests/test_console_endpoint_registry_contract.py -q -rEf` | **43 passed** |
| **Live negative control** | replace the `replaceState` call in the real `router.ts`, rerun | **2 failed, 26 passed** — exactly the two new nodes; restored byte-identically → **28 passed**, empty mutation diff |
| Typecheck + build | `corepack pnpm build` (`tsc --noEmit && vite build`) | **exit 0**, 74 modules |
| CP10 admission | `--judge` per changed path | **PASS** for all five paths |
| CP10 gate integrity | `pytest tests/test_m02a_ci_gate_integrity.py -q -rEf` | **64 passed** |
| Full suite (branch, post-change) | `pytest tests/ -q -rEf --continue-on-collection-errors` | **27 failed, 2349 passed, 17 skipped, 1 error** |
| Failing/error node set | sorted `FAILED`/`ERROR` lines | **28 nodes, sha256 `92fcd59cb4f0aee3249c93045c3d1ddd5bfd591c24d5b628db829c0fd1645048`** |
| Node-set delta vs pre-change tree | `comm` | **empty** |

The `+2 passed` (2347 → 2349) is exactly this pass's new node count. The 28-node failing set
is the same set on both trees and is pre-existing debt, not attributable to this pass.

### 8.5 Opportunity Radar — reviewed, not modified

Mount chain read from live source: `SolSpirePage.tsx:33` → `OpportunityRadarSection` →
`ProjectOpportunityRadar`. Paths come from `opportunityRadarContract.ts`
(`BASE = "/solspire/buyer-recon"`, each `encodeURIComponent`-ed). All three composed shapes
are served by the canonical app (`app.openapi()["paths"]` → `served=True`). The component is
reconnaissance-only: no execute/spend control, and a network/server failure renders "not an
empty board" rather than an empty board. **No shared integration change is needed**, and
Workstream 2's merged evidence explicitly requests no shared endpoint constant for that path.

### 8.6 Branch map refreshed

`SHARED-CONTRACTS.md` §1 heads re-measured 2026-10-11T13:0xZ: W1 → `46326ba4`,
W2 `e6780d47` → `d40de704`, W3 `a2024fba` → `f5f8b70e`, W4 unchanged `dcb3e2f2`; all four
draft/OPEN/MERGEABLE; `main` unchanged at `f390526a`. `AGENT-01-SHELL.md` gained the measured
facts a later pass must not re-derive, including the fetch-before-commit rule this pass learned
from `9b1b3ef1`.

### 8.7 Non-claims (this continuation)

- The router change is a **repository-source** claim. It is not an observation of the deployed
  bundle; production parity is not claimed and would need a post-merge deployment.
- No merge, no deployment, no acceptance. No Vercel deployment created or promoted.
- No feature-owned path was edited; Workstream 2's opportunity implementation was reviewed only.

### 8.8 Second shell/navigation gap — the archived Oracle deep links

`resolvePath` handled `/nexus` but not `/oracle` or `/commune`. The archived Prism's route
table declares `commune: '/oracle'` and accepts **both** `/oracle` and `/commune` as direct
routes (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:44,70`), and its home
surface sends the Oracle portal to `commune` (`onNavigate('commune')`). The console names that
surface `arkana`. So a real archived deep link — `/oracle` or `/commune` — fell through
`resolvePath` to `home`, and §8.3's normalisation then wrote `/` to the address bar, making the
loss permanent for a shared link.

**Change:** both paths added to `PATH_ALIASES` → `arkana`. They are aliases, not surfaces:

- Neither is a declared surface path, so neither duplicates a real route (the existing
  alias-soundness detector rejects that).
- Neither collides with a backend route. Measured against the live app:
  `app.openapi()["paths"]` has no exact `/oracle`, `/commune`, `/nexus`, or `/arkana` entry and
  no sibling under any of them; `_RESERVED_PREFIXES` contains none of them.

**Guard** — one positive assertion and one negative control, both in
`tests/test_console_shell_nav_contract.py`:

- `test_oracle_and_commune_reconcile_to_the_arkana_surface` asserts both resolve to `arkana`,
  that neither is a declared surface path, and re-runs `_alias_defects` so a future collision
  is still caught.
- `test_detector_flags_an_oracle_alias_that_falls_through_to_home` strips the two entries from
  the **real** router and asserts they then reproduce the pre-repair fall-through to `/`.
  A control that only asserted the repaired state would be silent on the defect.

**Live negative control, measured:** deleting the two entries from the real `router.ts` reddens
**3 nodes** (27 passed) — the new positive test, the new control, and the §8.3 canonical-path
test, which now also probes `/oracle` and `/commune`. Restored byte-identically
(`git diff --stat` → empty) and green again (**30 passed**).

Two guards were drafted first and **removed** before commit: a Node-evaluated `PATH_ALIASES`
reader plus its own alias-soundness test. Both duplicated the existing
`_path_aliases` / `_alias_defects` suite (which already asserts alias targets are declared and
that an alias never collides with a canonical path), and the reader failed on helper scope
(`strip_types` is nested inside `_js_route_resolver`). Duplicating a guard is not a guard; the
existing one was reused and extended instead.

| Check | Result |
|---|---|
| `tests/test_console_shell_nav_contract.py` | **30 passed** (was 28) |
| Both guards together | **47 passed** (was 43) |
| **Live negative control** | entries removed → **3 failed, 27 passed**; restored → **30 passed**, empty mutation diff |
| Typecheck + build | `corepack pnpm build` → **exit 0** |
| Full suite | **27 failed / 2352 passed / 17 skipped / 1 error** |
| Failing/error node set | **28 nodes, sha256 `92fcd59cb4f0aee3249c93045c3d1ddd5bfd591c24d5b628db829c0fd1645048`** — **identical** to the pre-change tree |
| CP10 admission | `--judge` → **PASS** for both changed paths |

The `+3 passed` is exactly this change's new node count. The failing set is unchanged, so the
increment introduces no regression.

**Still not reconciled (recorded, not executed):** the archived Prism also declared
`/living-gate` + `/gate` (its `gate` view) and `/home`. The console has no `gate` surface —
sign-in is `/login` — so `/gate` is not an alias of anything and reconciling it would require
deciding what the surface *is*, which is a product decision, not a routing one. `/home` is the
same case as `/` and is a candidate for a later bounded pass.

---

## 9. Transport-detector domain widened to `.ts` — 2026-10-11

### 9.1 The defect

§8.5 widened the one-registry guard from `useHydration` arguments to `apiRequest`
literals, but ran the widened detector over `_tsx_sources()`. The read is what carries the
endpoint contract, not the extension of the file that performs it: `lib/arkana.ts` reaches
`POST /api/commune/resonance` through `apiRequest` and is a `.ts` module. A contract module,
hook, or plain helper that inlined a path would therefore have passed
`test_no_page_passes_a_literal_path_to_api_request` unjudged — the same blind spot the §8.5
widening closed one layer down.

Measured: a planted `apiRequest<unknown>("/api/ghost-feed")` in `lib/arkana.ts` was reported
by the widened domain and **missed** by the pre-change `.tsx` domain (`[]`).

### 9.2 The change (one file)

`tests/test_console_endpoint_registry_contract.py`:

- `_transport_sources()` — `.ts` **and** `.tsx` under `web/arkadia_console/src`, excluding
  `lib/apiClient.ts`. The transport is excluded because it *is* the boundary: its own
  `fetch(path, …)` receives the path as a parameter, so scanning it would report the
  transport's signature rather than a page-local contract.
- `test_no_page_passes_a_literal_path_to_api_request` now asserts over `_transport_sources()`.
- `test_transport_detector_domain_includes_ts_modules` (new) pins the domain: a real `.ts`
  transport read must be scanned, the transport itself must not, a `.ts` literal must be
  reported, and the control premise (`.ts` is outside `_tsx_sources()`) must hold.

No production source was edited. `_tsx_sources()` is retained and still used by the
`useHydration` detector, whose path is always a page-local `.tsx` expression.

### 9.3 Verification

| Check | Result |
|---|---|
| `tests/test_console_endpoint_registry_contract.py` | **18 passed** (was 17) |
| Guard + shell-nav + gate-integrity | **110 passed** |
| `tests/architecture` | **11 passed** |
| CP10 admission (`--judge`) | **PASS** for the changed path |
| Live tree under the widened domain | **37 modules, 0 defects** (no false positive) |
| **Live negative control** | planted `.ts` literal → `test_no_page_passes_a_literal_path_to_api_request` **FAILED**; file restored byte-identically (`sha256 4ecea80c…`) |
| Load-bearing proof | widened domain reports the planted literal; pre-change `.tsx` domain returns `[]` |
| Full suite (branch, clean run) | **27 failed / 2351 passed / 17 skipped / 1 error** |
| Full suite (baseline `7a81095d`, same env) | **27 failed / 2350 passed / 17 skipped / 1 error** |
| Failing/error **node set** vs baseline | **identical** — 28 nodes, sha256 `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` on both trees |
| `+1 passed` attribution | exactly the one new node; the branch adds one test |

The 28-node failing set is pre-existing debt (voice context/pipeline, `knowledge.db`
cross-test contamination, the `weaver.autonomy` module-vs-package collection error, the
sovereign-only `tests/test_engineering_lab_api.py` pins, Landing copy pins) — the same set on
both trees.

**Measurement note (a real hazard, recorded).** A first branch run reported **28** failures to
the baseline's 27, the delta being
`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`. That
node is the repo's **documented intermittent**: it snapshots global `git status --porcelain`
around `execute_agent_loop`, so any concurrent repository write fails it — and this pass edited
`SHARED-CONTRACTS.md` in that same worktree while its suite was running. It passes 1/1 in
isolation. A clean re-run with no concurrent writes reproduced the baseline node set exactly
(`521c63e1…`). Attribute this class of delta by **node identity**, never by count.

### 9.4 Non-claims

Repository-source claim only. No merge, no deployment, no acceptance; production parity is
not claimed. No feature-owned path (`opportunityRadarContract.ts`, `knowledgeContracts.ts`,
`arkanaThreadsContract.ts`, the Lab components) was edited.

### 9.5 Next bounded task (deterministic resume block)

- **Current state:** `feat/prism-next2-01-shell-contract-map` @ `af379094`, rebased onto
  `main` `f390526a`, pushed; PR #429 draft, `MERGEABLE/CLEAN`, 13/13 check-runs success.
- **Evidence:** §9 above; negative control reconfirmed this pass (`lib/arkana.ts` planted
  literal reddens the guard; file restored byte-identically, sha256 `4ecea80c…`).
- **Blockers:** none. `main` advanced mid-pass (`962434b` → `f390526a`) and touched this same
  guard (+182 lines) and `SHARED-CONTRACTS.md`; the branch **already contains** it
  (`git merge-base --is-ancestor f390526a af379094` → true), and new main still carries
  `rglob("*.tsx")`, so the `.ts` widening is not superseded.
- **Authorized action:** continue WS1 §8 contract work on this branch; the remaining
  unreviewed endpoint-contract shapes are the **caller-supplied path props** deliberately left
  out of scope — `ProjectOpportunityRadar.readPath` (WS2 composition) and
  `KnowledgeGraphPanel.readGraph(path)` (WS3 composition). Each belongs to its owning
  workstream's contract, not the shell's.
- **Forbidden:** merge, deployment, Vercel promotion/acceptance, editing WS2/WS3/WS4-owned
  files, adding a second endpoint registry.
- **Completion condition:** the guard judges every `apiRequest`/`useHydration` call site in
  `web/arkadia_console/src/**/*.{ts,tsx}` (excluding `lib/apiClient.ts`), or each out-of-scope
  shape is explicitly assigned to its owning workstream with a recorded rationale.

**Classify deployments by `creator` + commit-status `context`, never by the `environment`
label.** A pass here briefly read `render[bot]` per-branch previews as Vercel previews (the
`environment` string is provider-formatted, e.g. `feat/… - Arkadia PR #429`) and nearly
recorded a boundary regression. `creator=render[bot]` and zero Vercel commit statuses refute
it.
