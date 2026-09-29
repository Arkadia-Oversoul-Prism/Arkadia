# AEAS Frontend Scalpel Plan

**STATUS:** AUTHORIZED FOR ANALYSIS ONLY — IMPLEMENTATION NOT AUTHORIZED
**MODE:** AEAS · EVIDENCE-DRIVEN · BOUNDED
**AUTHORITY:** HUMAN SOVEREIGN
**MERGE:** HUMAN ONLY
**SOURCE OF TRUTH:** CURRENT MAIN + CURRENT TEST SUITE
**COMPANION:** `docs/architecture/AEAS_FRONTEND_SEAM_MAP.md` (PR #123, documentation only)

> ¯\(ツ)/¯ DON'T KNOW IS ALLOWED. BUT WE CAN FIND OUT.

**No UI component, route, test, or token was modified by this artifact.**

---

## 1. VERIFIED CURRENT STATE

### 1.1 SHAs

| Ref | Value | Verification |
|-----|-------|--------------|
| `CURRENT_MAIN_SHA` | `67a660c251af43159ea130b127fdc7040495501f` | `git rev-parse origin/main` (`Merge PR #122`) |
| `PR123_HEAD_SHA` | `a664c1774af92d181b42c7c109d750b19a05ae1b` | GitHub API `/pulls/123` |
| `PR123_BASE_SHA` | `67a660c251af43159ea130b127fdc7040495501f` | GitHub API `/pulls/123` |
| PR #123 state | `open · merged: false · mergeable: true` | GitHub API |

**PR #123 is unmerged.** This plan is built on `main`, not on PR #123's branch. No dependency on PR #123 being merged.

### 1.2 Corrections to the prior seam map (repository wins)

Two claims in the prior pass were wrong. Recorded here rather than smoothed over.

**Correction A — `label: 'Radar'` DOES exist.**
Prior claim: *"no `Radar` string exists; source label is `Commercial`"* (`SEAM_MAP.md` §3.2, `UNVERIFIED`).
Verified: `SolSpireExperience.tsx:38` → `{id:'opportunity-radar',label:'Radar',sigil:'⌁',…}`.
Earlier `grep` missed it because the shell renders from a `NAV` array, not inline JSX. **The screenshot was correct; the plan was wrong.**

**Correction B — `PrismInteriorShell` is NOT dead; it is LIVE for every authenticated interior view.**
Prior claim: *"`PrismInteriorShell` … not mounted"*.
Verified: `ArkadiaNavigation.tsx:46–47` — `const interior = !['home','gate','login'].includes(currentView) && isAuthenticated; if (interior) return <PrismInteriorShell …>{children}</PrismInteriorShell>`.
For `view = 'solariun' | 'solspire' | 'novanet' | 'sci' | …` the shell **is** rendered, wrapping the entire view. It supplies a second identity bar and a second product rail above Solariun's own header.

**Correction C — `ExperienceConsolidationFrame` is not a no-op; it is a CSS suppression layer.**
Prior claim: *"pure wrapper … adds a DOM boundary and test id but no consolidation"*.
Verified: it imports `experience-repair.css` (**460 lines**) and `experience-consolidation.css` (**123 lines**). `experience-repair.css:101–106` contains:
```css
/* The old Prism/global door strip must never compete with the Solariun field. */
.experience-repair-scope .solspire-prism-rail,
.experience-repair-scope .solspire-global-doors { display: none !important; }
```
This is the load-bearing catch: **the duplicate chrome (S1) was previously visible, and was hidden in CSS rather than removed.** The shell's own `CLARITY_CSS` (`PrismInteriorShell.tsx:54+`) separately overrides `.solspire-canonical-header`.

*Residual unknown:* whether `onNavigate` was ever used historically remains `UNKNOWN`; it is unused **now** (`experience-repair.css` header comment asserts the frame "deliberately does not add another navigation/header/inspector/search system"). Removal safety is still unproven — the two CSS files are imported **only** there.

### 1.3 Current shell composition (measured, for `view = 'solariun'`)

```
ArkadiaNavigation                                  ArkadiaNavigation.tsx:42
  └ (interior === true) PrismInteriorShell         ArkadiaNavigation.tsx:47
       ├ header  → IdentityPersistence             PrismInteriorShell.tsx:48   ← GLOBAL identity bar #1
       └ nav     → NovaNetRail (PRIMARY+More)      PrismInteriorShell.tsx:44   ← GLOBAL product rail
  └ AnimatePresence → ExperienceConsolidationFrame App.tsx:148
       ├ imports experience-repair.css             (460 lines)                 ← suppresses the above
       └ SolariunConsole → auth gate               SolariunConsole.tsx:6
            └ SolSpireExperience                   SolariunConsole.tsx:6
                 ├ Header (brand + identity)        SolSpireExperience.tsx:64   ← identity bar #2
                 ├ GlobalDoors (NETWORK)            SolSpireExperience.tsx:65   ← product rail #2 (CSS-hidden)
                 ├ ContextBar breadcrumb            SolSpireExperience.tsx:69
                 ├ Sidebar (12 lenses)              SolSpireExperience.tsx:68
                 └ MobileNav (10 items)             SolSpireExperience.tsx:67
```
**Confirmed: two identity bars, two product rails, a CSS layer whose stated purpose is to hide one of them.**

### 1.4 Navigation composition — 10 systems

| ID | System | Location | Items |
|----|--------|----------|-------|
| N1 | Global nav drawer (grouped) | `ArkadiaNavigation.tsx:12–26` | Field/Nexus/Workspaces/System (10 items) + 7 quick buttons (`:39`) |
| N2 | Authenticated global rail | `PrismInteriorShell.tsx:10–25,44` | PRIMARY (7) + SECONDARY (5) behind "More" |
| N3 | Solariun sidebar | `SolSpireExperience.tsx:68` | 12 lenses |
| N4 | Solariun mobile bottom rail | `SolSpireExperience.tsx:66–67` | 10 items (`BOTTOM_NAV`) |
| N5 | Solariun mobile "More" sheet | `SolSpireExperience.tsx:210,213` | NAV (12) + NETWORK (6) |
| N6 | Solariun context bar |  `SolSpireExperience.tsx:69` | breadcrumb + 2 actions |
| N7 | Solariun network doors |  `SolSpireExperience.tsx:49–56` | 6 cross-workspace doors |
| N8 | Project tab strip | `ProjectDashboard.tsx:1174–1185` | 11 tabs |
| N9 | SolSpire enterprise step nav | `EnterpriseConsole.tsx:79,98` | 7 onboarding steps |
| N10 | Legacy/compat remap | `App.tsx:112–120`, `SolariunConsole.tsx:5` | `LEGACY_MAP` (11 keys) + 3 `View` aliases |

### 1.5 Route map (measured)

`type View` = 30 members (`App.tsx:36`). 27 have a render block. `dashboard`, `loops`, `nexus` have **none** — they are remap-only aliases (`App.tsx:115–118`).

### 1.6 Weaver placement (measured)

- Lens `weaver` in `NAV` (`SolSpireExperience.tsx:44`) → renders `WeaverSummary`.
- **`WeaverSummary` is a placeholder disclosure, not a surface.** `SolSpireWorkspacePanels.tsx:48` states verbatim: *"Weaver remains project-scoped. SolSpire is the window into it, not a new execution authority."* It lists active projects and emits `onOpenProject`.
- Real work: `WeaverPanel` (`ProjectDashboard.tsx:69–218`) → `/solspire/projects/{id}/weaver/execution/{pass-spec,approval,readiness}`.

### 1.7 Engineering Lab placement (measured)

Lens `engineering-lab` (`SolSpireExperience.tsx:46`) → `EngineeringLabLens` (`SolSpireExperience.tsx:190`). APIs: `/api/lab/overview`, `/api/lab/engineering/overview`. `tests/test_engineering_lab_substrate.py` = **38 passed**.

### 1.8 Test baseline (measured on `main` @ `67a660c`, full deps installed)

```
54 failed, 962 passed, 12 skipped, 2 errors
```

Shell/navigation-related failures = **20**:

| Test file | Failed | Protecting |
|-----------|--------|-----------|
| `test_prism_pass_c_surface_ownership.py` | 6 | `SolSpireConsole` alias routing (superseded) |
| `test_ais_w2_living_gate_grove_handoff.py` | 6 | Living Gate internals (not shell) |
| `test_prism_interior_shell.py` | 3 | `prism-primary-rail`, `prism-secondary-toggle` (superseded) |
| `test_solariun_experience_consolidation_01.py` | 3 | frame internals that moved to CSS |
| `test_weaver_sci_boundary_01.py` | 3 | Weaver↔SCI boundary via `SolSpireConsole` |
| `test_weaver_sci_contract_01.py` | 2 | same |
| `test_solspire_p1_experience_01.py` | 2 | Arkana context pack strings |
| `test_weaver_mvp2_08.py` | 1 | `nexus → novanet` remap string form |

**These failures are pre-existing on `main`. They are not attributable to this plan, which changes nothing.**

### 1.9 Stale symbols (measured)

| Symbol | Referenced by tests | Present in source |
|--------|--------------------|-------------------|
| `SolSpireConsole` | 6 failures | **yes** (`SolSpireConsole.tsx`) — but it is a 4-line alias to `EnterpriseConsole`, and `'initialSection="codex"'`-style props are meaningless to it |
| `prism-primary-rail` | `test_prism_interior_shell.py` | **ABSENT** (shell emits `novanet-primary-rail`) |
| `prism-secondary-toggle` / `prism-secondary-lenses` | `test_prism_interior_shell.py` | **ABSENT** |
| `"Same identity · same context · same backend"` | `test_prism_interior_shell.py` | **ABSENT** |
| `Merge: human_only` / `Deploy: human_only` | `test_solariun_experience_consolidation_01.py` | **ABSENT** from `SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md` |

Last-touch dates: `test_prism_interior_shell.py` + `test_prism_pass_c_surface_ownership.py` = `2026-09-15`; `PrismInteriorShell.tsx` = `2026-09-27`; `experience-repair.css` = `2026-09-16`.

---

## 2. CANONICAL OWNERSHIP MATRIX

One canonical owner per layer. Where two remain, the reason is stated.

| Experience Layer | Current Owners | Proposed Canonical Owner | Redundant Owners | Evidence | Confidence |
|------------------|----------------|--------------------------|------------------|----------|------------|
| **Identity** | (1) `PrismInteriorShell:48` `IdentityPersistence`; (2) `SolSpireExperience:62` Header identity; (3) `ArkadiaNavigation:33` `UserSection` | **Global shell (one identity bar)** | (2) workspace header identity; (3) drawer user block (keep as *account control*, not identity display) | both bars render simultaneously (§1.3); repair CSS de-emphasises #2 | HIGH |
| **Product switching** | (1) `PrismInteriorShell:10–25` PRIMARY+SECONDARY; (2) `ArkadiaNavigation:18–21` Workspaces group; (3) `SolSpireExperience:49–56` NETWORK; (4) `SolSpireExperience:210` mobile NETWORK | **Global rail (N2)** | (3)(4) CSS-hidden duplicate; (2) drawer duplicate | `experience-repair.css:101–106` hides (3) explicitly | HIGH |
| **Workspace navigation** | (1) `Solariun sidebar`; (2) `SolSpire enterprise step-nav` | **(1) for Solariun; (2) for SolSpire** — two owners, legitimate | — | different consoles: `SolariunConsole`→`SolSpireExperience`; `SolSpireConsole`→`EnterpriseConsole` | HIGH |
| **Lens navigation** | (1) sidebar `:68`; (2) mobile rail `:67`; (3) mobile More `:210`; (4) `BOTTOM_NAV` subset `:66` | **One responsive lens nav** (sidebar desktop ↔ rail mobile) | (2)(3)(4) are responsive duplicates of (1) with **divergent item sets** | sidebar 12 items vs `BOTTOM_NAV` 10 items vs sheet 12+6 | HIGH |
| **Project context** | (1) `SolSpireExperience:212` project canvas; (2) `ProjectDashboard` project heading/tabs | **(1)** | (2) tab strip is content, heading duplicates (1) | `:212` already renders `PROJECT CONTEXT` + `← Projects` | MED |
| **Work execution** | (1) `WeaverPanel` (`ProjectDashboard.tsx:69`); (2) `WeaverSummary` lens (`SolSpireWorkspacePanels.tsx:48`) | **(1) — project-scoped** | (2) is a disclosure placeholder, not an executor | (2)'s own copy disclaims authority | HIGH |
| **Evidence** | (1) `ProjectDashboard:1249` `EpistemicInspector`+`Events`; (2) Home "Follow the thread" | **(1)** | (2) is a projection/navigator | `:1249`; Home section is `:443` in cockpit | MED |
| **Architecture inspection** | (1) `EngineeringLabLens` | **(1)** | none | 38 substrate tests pass | HIGH |
| **Configuration** | (1) Solariun `settings` lens; (2) project Settings tab; (3) `ArkadiaNavigation:25–26` System group | **(1) workspace-scoped + (2) project-scoped** (both legitimate scopes) | (3) global drawer entry | `:45`, `ProjectDashboard.tsx:1185`, `ArkadiaNavigation.tsx:25` | MED |
| **Legacy compatibility** | (1) `App.tsx:112–120` remaps; (2) `LEGACY_MAP`; (3) `PrismInteriorShell:27–34` `activeSurfaceFor` | **App.tsx route resolver** | (2)(3) fold into (1) | measured | MED |

**Two-owner exceptions (justified):** *Workspace navigation* — Solariun and SolSpire are genuinely different workspaces with different substrates (`SolSpireExperience` vs `EnterpriseConsole`); a single lens nav cannot serve both. *Configuration* — workspace settings and project settings have different scopes.

---

## 3. NAVIGATION COLLISION MAP

| System | Owner | Purpose | Routes | Duplicates | Overlaps | Callers | Dependencies | Test coverage |
|--------|-------|---------|--------|-----------|----------|---------|--------------|---------------|
| N1 drawer | `ArkadiaNavigation` | Global entry | 10 views | N2 (product switching) | N2 | `App.tsx:121` | `AuthContext`, `ArkadiaLandingPage` | — |
| N2 rail | `PrismInteriorShell` | Product switching | 12 keys | N1, N3(NETWORK) | N1, N3 | `ArkadiaNavigation:47` | `AuthContext` | `test_prism_interior_shell.py` (3 fail) |
| N3 sidebar | `SolSpireExperience` | Lens nav | 12 lenses | N4, N5 | N4, N5 | `:68` | `NAV` | `test_p0_1_*` (5 pass) |
| N4 mobile rail | `SolSpireExperience` | Lens nav (mobile) | 10 lenses | N3, N5 | N3 | `:67,212,213` | `BOTTOM_NAV` | — |
| N5 mobile sheet | `SolSpireExperience` | Lens + network | 12+6 | N3, N4, N7 | all | `:210,213` | `NAV`,`NETWORK` | — |
| N6 context bar | `SolSpireExperience` | Breadcrumb | — | product rail | N2 | `:69` | `lens` | `test_solariun_experience_consolidation_01` (frame parts fail) |
| N7 network doors | `SolSpireExperience` | Cross-workspace | 6 views | N2 | N2 | `:63` | `onNavigate`/`navigateGlobal` | — |
| N8 project tabs | `ProjectDashboard` | Object nav | 11 tabs | N3 (knowledge/files/tasks/conversations/memory/events) | N3 | `:1174` | `ProjTab` | `test_p0_1_*` (pass) |
| N9 step nav | `EnterpriseConsole` | Onboarding | 7 steps | — | — | `:98` | local state | — |
| N10 legacy | `App.tsx`, `SolariunConsole` | Compat | 11 keys | N1 | N1 | `:112` | `LEGACY_MAP` | `test_prism_pass_c_*` (6 fail) |

### 3.1 Canonical navigation graph

Every existing item mapped to exactly one node.

```
GLOBAL        N2 rail (products) · N1 drawer (account/config/compat entry)
   ↓
WORKSPACE     N3 sidebar (Solariun)  |  N9 step-nav (SolSpire)
   ↓
LENS          N3 lens ids (12)
   ↓
OBJECT/PROJECT  ProjectsWorkspace → N8 project tabs
   ↓
WORK MODE     WeaverPanel (project-scoped work execution)
   ↓
INSPECTOR     EpistemicInspector · EngineeringLab inspection · project Events
```

**Mapping of every item:**

| Item | Node | Notes |
|------|------|-------|
| NovaNet, Solariun, SolSpire, Oracle, ReasoMate, Encyclopedia, Offerings, Echo Field, Spiral Codex, Spiral Grove, Living Larder, SCI, About, Settings, Account | GLOBAL | N2/N1 |
| Home, Projects, Commercial, Radar, Knowledge, Files, Conversations, Tasks, Memory, Weaver, Activity, Settings, Engineering Lab | LENS | N3 |
| Overview, Weaver, Knowledge, Conversations, Files, Repos, Tasks, Workflows, Memory, Events, Settings | OBJECT (project) | N8 |
| `field`,`codex`,`loops`,`projects`,`encyclopedia`,`goals`,`releases`,`jobs`,`traces`,`tools`,`system` | GLOBAL (compat → LENS) | N10 remaps |
| `dashboard`,`loops`,`nexus` | GLOBAL (compat aliases) | N10 remaps |

### 3.2 UNRESOLVED

| Item | Why unresolved |
|------|----------------|
| `Radar` / `opportunity-radar` lens | Renders `OpportunityRadarPage` from **static hardcoded data** (`data/opportunityRadar.ts`, 6 targets: 3 named organisations with contact PII). No API call. Whether this is a **live product lens**, a **private working list**, or **demo data that should not ship** is a product decision, not an architectural one. **Do not place it in a canonical category until the sovereign decides.** **UNRESOLVED** |
| `Spiral Codex` / `Distribute` dual location | `spiral-codex` is both a `View` (`App.tsx:135`) and a `NETWORK` entry (`SolSpireExperience.tsx:54`); `distribute` is a `View` (`App.tsx:138`) with no navigation entry. **UNRESOLVED** |

No category was invented to absorb these.

---

## 4. TEST CONSTRAINT REGISTER

No test edited. Classifications: **A INVARIANT · B OBSOLETE · C REWRITE REQUIRED · D UNKNOWN**.

### 4.1 `test_prism_pass_c_surface_ownership.py` — 6 failed / 3 passed

| Test | Protects | Class | Future assertion | Risk |
|------|----------|-------|------------------|------|
| `test_spiral_codex_not_solspire_field` | Codex ≠ SolSpire field | **C** | assert `SpiralCodexFeed` mounted | low |
| `test_spiral_codex_uses_feed_component` | Feed import | **A** | unchanged | none |
| `test_echo_field_aliases_resolve_to_solspire_field` | Aliases resolve | **C** | assert alias resolves to canonical *destination*, not `SolSpireConsole` | medium — **but see 4.2: these routes may not exist** |
| `test_nav_echo_field_opens_solspire` | Drawer entry | **C** | assert entry resolves canonically | low |
| `test_knowledge_os_resolves_to_solspire_knowledge` | KO route | **C** | assert resolves to `SolariunConsole initialSection="knowledge"` | medium |
| `test_codex_resolves_to_solspire_codex` | Codex route | **C** | assert resolves to `memory` lens (`LEGACY_MAP`) | medium |
| `test_loops_resolves_to_solspire_loops` | Loops route | **C** | assert resolves to `tasks` lens | medium |
| `test_no_new_top_level_views_introduced` | No new `View` ids | **A (CRITICAL)** | unchanged — **preserve** | none |
| `test_frontend_no_k3_transaction_in_app` | No K3 call in App | **A (CRITICAL)** | unchanged — **preserve** | none |

### 4.2 ⚠ CONTRADICTION FOUND — the pass-C route tests reference routes that do not exist

`_block(view)` requires a literal `{view === 'X' && (…)}` JSX block. Verified in `App.tsx`:

| View | `handleNavigate` remaps it? | Literal render block? |
|------|----------------------------|----------------------|
| `personal-echofeild`, `echofeild-matrix` | **no** | yes — render `UniversalEchofeildMatrix`, **not** `SolSpireConsole` |
| `knowledge-os` | yes (`:115`) | yes (`:150`) — `SolariunConsole initialSection="knowledge"` |
| `codex` | yes (`:115`) | yes (`:145`) |
| `loops` | yes (`:117`) | **NO render block** |

So `test_echo_field_aliases_resolve_to_solspire_field` asserts a mount that was **deliberately replaced** by `UniversalEchofeildMatrix`; and `test_loops_resolves_to_solspire_loops` asserts a block that no longer exists.

**Implication:** these 6 failures encode a *superseded* architecture. Amending them is **not** weakening protection — it is removing assertions that no longer describe the product. This requires human acknowledgement, because a green suite would otherwise mask it. **Class C, flagged for explicit sovereign review.**

### 4.3 `test_prism_interior_shell.py` — 3 failed / 2 passed

| Test | Protects | Class | Note |
|------|----------|-------|------|
| `test_authenticated_interior_uses_one_prism_shell` | "one prism shell" | **C** | asserts `"Same identity · same context · same backend"` — string **ABSENT**; but the *principle* is exactly Gate A/B |
| `test_shell_exposes_canonical_primary_surfaces` | PRIMARY surfaces | **C** | asserts testid `prism-primary-rail`; source emits `novanet-primary-rail` |
| `test_shell_exposes_secondary_nexus_lenses` | SECONDARY lenses | **C** | asserts `prism-secondary-toggle`/`prism-secondary-lenses` — **ABSENT**; also asserts label `"Weaver"` in shell — see below |
| `test_shell_does_not_create_authority_or_backend_paths` | No backend calls in shell | **A (CRITICAL)** | **preserve verbatim** |
| `test_novanet_view_mounts_content_not_nested_hub` | NovaNet not nested | **A** | preserve |

**Note:** `test_shell_exposes_secondary_nexus_lenses` expects `"Weaver"` inside the *shell*. Neither `PRIMARY` nor `SECONDARY` contains Weaver today. If Gate A removes the SECONDARY expander, this test must be **rewritten to target whichever component becomes the canonical product rail** — or deleted if the rail itself is removed. Class **C**, high coupling.

### 4.4 `test_solariun_experience_consolidation_01.py` — 3 failed / 4 passed

| Test | Protects | Class | Note |
|------|----------|-------|------|
| `test_area_a_novanet_is_bound_to_shared_experience_shell` | `surface="NovaNet"` | **A** | passes |
| `test_area_b_solariun_workspace_is_bound…` | `surface="Solariun"`, `<SolariunConsole`, `<SolSpireConsole`, `/solariun` | **C** | the `SolSpireConsole` assertion is the stale part |
| `test_area_c_solspire_substrate_uses_existing_search_and_context_grammar` | **that `ExperienceConsolidationFrame.tsx` contains** `searchKnowledge`, `"Knowledge OS search only"`, `"No universal object index"`, `"ACTIVITY ≠ PROVENANCE"`, `"Existing repository components + existing APIs"` | **C / B** | **These strings are not in the frame.** The assertions target *documentation prose* that once lived in the component. The architectural intent (bounded search, no universal index) is **INVARIANT**; the assertion location is obsolete. **Rewrite to assert behaviour** (e.g. no universal-index endpoint), not strings. |
| `test_area_d_spiral_command_is_bound…` | SCI bounded, `K15`/`K3`, no authority | **A (CRITICAL)** | passes — **preserve** |
| `test_responsive_composition_and_inspector_exist` | `experience-inspector`, `experience-context-bar` testids | **C** | frame emits neither; moved to CSS/other components. If Gate B removes the frame, this test's target must be **reassigned to the canonical owner** |
| `test_forbidden_architecture_not_introduced` | No `CREATE TABLE`/`WorkEvent`/`K15 -> K3` in frame | **A (CRITICAL)** | **preserve** |
| `test_preimplementation_map_is_present_and_bounded` | Map prose incl. `Merge: human_only`, `Deploy: human_only` | **C** | those two strings **ABSENT** from the map; add them to the map (safe) or rewrite the assertion |

### 4.5 `test_solspire_p1_experience_01.py` — 2 failed / 3 passed

| Test | Protects | Class |
|------|----------|-------|
| `test_p1_1_arkana_context_pack` | Bounded Arkana context pack | **A (CRITICAL)** — strings need locating, intent invariant |
| `test_p1_1_not_authorization` | Arkana ≠ authorization | **A (CRITICAL)** — preserve |
| `test_p1_2_object_sheet` | Object sheet + CSS max-width | **A** passes |
| `test_p1_3_knowledge_library_mode` | Global-vs-project knowledge distinction | **A** passes — **preserve; this is the S4 epistemic boundary** |
| `test_packet_scope_excludes_p2_claims` | Scope honesty | **A** |

### 4.6 Weaver boundary tests

| Test | Protects | Class |
|------|----------|-------|
| `test_weaver_sci_boundary_01` (3 fail) | Weaver must not become a second SCI/authority path | **C** — asserts `"ProjectDashboard"` inside `SolSpireConsole` and `"WEAVER-SCI-BOUNDARY-01"` inside `ArkadiaNavigation`; both strings absent. **Intent (no second authority path) is INVARIANT and must survive re-expression.** |
| `test_weaver_sci_contract_01` (2 fail) | same + `nexus → novanet` remap form | **C** |
| `test_weaver_mvp2_08` (1 fail) | `"v === 'nexus' ? 'novanet'"` literal | **C** — remap now uses `if (requested === 'nexus')`; behaviour identical |
| `test_weaver_k2` (8 pass) | K2 governance | **A** — preserve |

### 4.7 Invariant set (must NOT be weakened by any gate)

1. No new top-level `View` id (`test_no_new_top_level_views_introduced`).
2. No `run_transaction` / `execute_patch` / K3 call in frontend (`test_frontend_no_k3_transaction_in_app`, `test_shell_does_not_create_authority_or_backend_paths`).
3. SCI bounded; K15/K3 not bypassed (`test_area_d_*`).
4. Arkana is not an authorization authority (`test_p1_1_not_authorization`).
5. Global knowledge library ≠ project corpus (`test_p1_3_*`).
6. Weaver remains project-scoped; no second authority path.
7. No fabricated state / no substituted placeholder (`test_solariun_thread_navigation_01`, Home copy).
8. Project field continuity `p0.1` (`test_p0_1_*`, 5 pass).

---

## 5. SHELL CONSOLIDATION DEPENDENCY GRAPH

| Component | Renders it | Navigated through by | Owns state | Owns routing | Owns search | Owns identity | Owns product switch | Owns mobile nav |
|-----------|-----------|---------------------|-----------|--------------|-------------|---------------|--------------------|-----------------|
| `ArkadiaNavigation` | `App.tsx:121` | drawer | drawer open | **no** (delegates) | no | **yes** (drawer) | drawer only | no |
| `PrismInteriorShell` | `ArkadiaNavigation:47` | rail | `lensesOpen` | **no** | no | **yes** | **yes** | no |
| `ExperienceConsolidationFrame` | `App.tsx` ×6 | — | none | no | no | no | no | no |
| `SolSpireExperience` | `SolariunConsole` | sidebar, rail, sheet, context | section, project, projectTab, search, arkana, more | **calls up** | **yes** | **yes** (header) | NETWORK doors (CSS-hidden) | **yes** |
| `SolariunConsole` | `App.tsx:145,148,150` | — | auth gate | no | no | no | no | no |
| `ProjectDashboard` | `SolSpireExperience:212` | tab strip | tab, project data | no | no | no | no | no |
| `WeaverPanel` | `ProjectDashboard:1241` | — | plan/approval/readiness | no | no | no | no | no |
| `EngineeringLab` | `SolSpireExperience:190` | — | lab data | no | no | no | no | no |

**Routing owner:** `App.tsx` `handleNavigate` alone. **Search owner:** `SolSpireExperience` alone. **Identity owner: two** (shell + workspace). **Product switching owner: two+** (shell rail, workspace doors CSS-hidden).

### 5.1 `ExperienceConsolidationFrame` determination

| Option | Verdict | Basis |
|--------|---------|-------|
| SAFE TO REMOVE | **NO** | it is the **only importer** of `experience-repair.css` (460 lines) and `experience-consolidation.css` (123 lines). Removing it removes the suppression that keeps duplicate chrome hidden. **Removing the frame without first removing the duplicate chrome would make the UI worse.** |
| SAFE TO REDUCE | **YES, but only after Gate B** | once the rail/identity duplicates are removed in source, the suppression CSS becomes inert and can be retired |
| REQUIRED ARCHITECTURAL BOUNDARY | **NO** | the header comment claims a boundary, but the component contributes no navigation, state, or routing; the boundary is purely visual |
| TEST-ONLY BOUNDARY | **PARTIALLY** | `test_solariun_experience_consolidation_01.py` targets it; the `surface="…"` testids are its only durable contract |
| UNKNOWN | on historical `onNavigate` use | not resolvable from current source |

**Ordering constraint:** `remove duplicate chrome (Gate A/B) → verify → then retire suppression CSS → then reduce frame`. Never the reverse.

---

## 6. HOME CONTRACT

**Future contract — every Home render answers, in order:**

1. **WHERE AM I?** — one identity, one workspace. (Today: identity is stated twice.)
2. **WHY AM I HERE?** — one sentence.
3. **WHAT MATTERS NOW?** — **one** dominant state, even when the answer is "nothing needs attention".
4. **WHAT CAN I DO NEXT?** — 1–3 actions, above the fold.
5. **WHAT RECENTLY CHANGED?** — one continuity/activity line.
6. **WHAT CAN I INSPECT?** — the substrate, on demand.

**Current sections (`SolariunHomeCockpit.tsx`), classified:**

| # | Section | Class | Rationale |
|---|---------|-------|-----------|
| 0 | Field state (loading) | **PRIMARY** | honest loading |
| 1 | Bootstrap status strip `:254` | **PROGRESSIVE_DISCLOSURE** | raw `SurfaceState` vocabulary |
| 2 | Identity context `:261` | **PRIMARY** (reduce to 1 line) | currently restsates workspace+identity |
| 3 | Personal field `:287` | **SECONDARY** | counts; useful, not dominant |
| 4 | Attention `:312` | **PRIMARY** | this *is* "what matters now" |
| 5 | Active world `:314` | **SECONDARY** | |
| 6 | Current signal `:316` | **SECONDARY** | |
| 7 | Continuity `:318` | **SECONDARY** | overlaps "what recently changed" |
| 8 | Synthesis `:320` | **PRIMARY** if present, else fold | |
| 9 | Decisions `:399` | **PRIMARY** | the one place a human must act |
| 10 | Follow the thread `:443` | **PROGRESSIVE_DISCLOSURE** | architecture map → inspector |
| — | 5 sibling empty states | **MERGE** into one honest workspace state | composition, not honesty, is the defect |

**Epistemic rule preserved:** *absence is valid state.* Never fabricate. Exact strings retained: `"No placeholder state has been substituted."`, `"No synthetic destination has been substituted."`

**Continuity note — a prior pass of this workstream contributed to the density.** PR #104 (merged, `a26af408c269`) added the "Follow the thread" section now at `SolariunHomeCockpit.tsx:443`. It is architecturally honest (bounded to three destinations, no implied transition) but it is a **10th block on a 10-section Home** — it participates in S16. Gate C should treat it as a candidate for `PROGRESSIVE_DISCLOSURE`, not as an untouchable asset. Recorded here so the plan does not exempt its own prior output.

---

## 7. PROJECT CONTRACT

11 tabs (`ProjectDashboard.tsx:1174–1185`), classified:

| Tab | Class | Proposed tier |
|-----|-------|---------------|
| Overview | SUMMARY | **PRIMARY** |
| Weaver | WORK | **PRIMARY** |
| Tasks | WORK | **PRIMARY** |
| Workflows | WORK | **CONTEXTUAL** |
| Knowledge | RESOURCE | **CONTEXTUAL** |
| Files | RESOURCE | **CONTEXTUAL** |
| Repos | RESOURCE | **CONTEXTUAL** |
| Conversations | RESOURCE | **CONTEXTUAL** |
| Memory | RESOURCE | **INSPECTOR** |
| Events | EVIDENCE | **INSPECTOR** (already carries `EpistemicInspector`) |
| Settings | CONFIGURATION | **SETTINGS** (out of the strip) |

Result: **3 primary · 5 contextual · 2 inspector · 1 settings** — replaces a flat 11-item strip. Not implemented here.

---

## 8. WEAVER CONTRACT

Answered from evidence, not philosophy.

| Question | Evidence | Answer |
|----------|----------|--------|
| Routing | lens `weaver` `:43`; project tab `:1176` | **both** |
| Component ownership | `WeaverSummary` (`SolSpireWorkspacePanels.tsx:48`) = disclosure; `WeaverPanel` (`ProjectDashboard.tsx:69`) = executor | executor is **project-scoped** |
| API scope | `/solspire/projects/{id}/weaver/execution/*` | **project-scoped** |
| Project relationship | `WeaverSummary` takes `onOpenProject` | **contextual on project** |
| Navigation | top-level lens **and** project tab | duplicative |
| State | `WeaverPanel`: plan/approval/readiness/K15 | **project-local** |
| Tests | `test_weaver_k2` (8 pass); SCI-boundary tests failing | boundary intent invariant |

**Verdict: F — multiple things depending on context.** Exactly:

| Context | Weaver is | Evidence |
|---------|-----------|----------|
| Global lens (`weaver`) | **a directory / disclosure** — *not* an execution surface | `WeaverSummary` copy: *"SolSpire is the window into it, not a new execution authority."* |
| Project tab | **a work mode** (executor) | `WeaverPanel` + `/execution/*` |
| SCI | **a governed party with no second authority path** | SCI-boundary tests |

**Proposed access model (not implemented):**
- **GLOBAL ACCESS** — Weaver lens remains a *directory* to active project threads (keep as-is; it is already honest).
- **PROJECT ACCESS** — project tab remains the work surface (canonical).
- **WORK ITEM ACCESS** — within `WeaverPanel` (exists).
- **EXECUTION ACCESS** — `/execution/*` only, never a second path.

**The Archimedean point:** Weaver is *already correctly scoped in copy and API*. The defect is that the lens is presented *as a peer destination* in a 12-item nav, making it *look* like a product. Fix presentation, not architecture.

---

## 9. ENGINEERING LAB CONTRACT

Separate the Lab into four concerns:

| Concern | Current evidence | Default viewport? |
|---------|------------------|-------------------|
| **CURRENT OBSERVATION** | "What is running now": agents, gateway, sessions (`/api/lab/engineering/overview`) | **YES — first** |
| **ARCHITECTURE** | "What exists now", "How the system arrived here", "Structural signals" | **NO — disclose** |
| **GOVERNANCE** | "Authority remains outside the Lab", "Authority ceiling" | **NO — disclose** (but never hide the *existence* of the boundary) |
| **EVIDENCE** | commit classifications, observation warnings | **NO — inspect** |

**Implementation topology leaking into navigation:** `engineering-lab` is a *lens* (fine). But the Lab's default view currently opens the entire audit table at once — **report gravity** (S11). Governance must remain *visible as a boundary* while being *quiet in weight*.

---

## 10. LEGACY SURFACE REGISTER

| Legacy Surface | Current Route | Canonical Destination | Still Needed? | Visible in Primary UI? | Disposition |
|----------------|---------------|----------------------|---------------|------------------------|-------------|
| `field` | `/` legacy | `overview` lens | yes | no | **CONTEXTUALIZE** |
| `codex` | `?` → `memory` | `memory` lens | yes | via alias | **COMPATIBILITY_ONLY** |
| `loops` | (no render block) → `tasks` | `tasks` lens | yes | no | **COMPATIBILITY_ONLY** |
| `projects` | legacy | `projects` lens | yes | no | **CONTEXTUALIZE** |
| `encyclopedia` | → `memory` | `NexusSpiralCodex` view | yes | yes (drawer) | **KEEP_VISIBLE** |
| `goals`,`releases` | → `overview` | `overview` lens | unknown | no | **ARCHIVE** (pending confirmation) |
| `jobs`,`traces`,`tools` | → `observatory` | `observatory` lens | unknown | no | **ARCHIVE** (pending) |
| `system` | → `settings` | `settings` lens | yes | no | **COMPATIBILITY_ONLY** |
| `dashboard` | alias → `overview` | `overview` lens | yes | no | **COMPATIBILITY_ONLY** |
| `nexus` | alias → `novanet` | `novanet` view | yes | no | **COMPATIBILITY_ONLY** |
| `personal-echofeild`,`echofeild-matrix` | own render block | `UniversalEchofeildMatrix` | yes | yes (drawer) | **KEEP_VISIBLE** |
| `distribute` | own render block | — | unknown | **no nav entry** | **UNKNOWN** — orphan route |
| 5 × `SocialField*.tsx` | none | — | **no references** | no | **UNKNOWN** → likely **ARCHIVE** (needs owner confirmation) |

**Not removed merely for looking obsolete.** `ARCHIVE` entries require owner confirmation.

---

## 11. IMPLEMENTATION DEPENDENCY ORDER

Each gate is independently shippable and independently revertible.

### GATE A — Canonical navigation ownership
- **Files:** `ArkadiaNavigation.tsx`, `PrismInteriorShell.tsx`
- **Tests:** `test_prism_interior_shell.py` (C), `test_prism_pass_c_surface_ownership.py` (C)
- **Runtime surfaces:** every authenticated view; desktop + mobile drawer
- **Invariants:** §4.7 (1)(2)(7)
- **Rollback:** revert 2 files
- **Closure evidence:** exactly one product rail and one identity bar render per view; screenshot desktop + 366px

### GATE B — Shell consolidation
- **Files:** `ArkadiaNavigation.tsx`, `ExperienceConsolidationFrame.tsx`, `experience-repair.css`, `experience-consolidation.css`
- **Tests:** `test_solariun_experience_consolidation_01.py` (C)
- **Closure evidence:** duplicate chrome removed **in source**, not hidden in CSS; frame reduction safe; `surface="…"` testids preserved or reassigned
- **Rollback:** restore CSS imports (this is why Gate B follows Gate A)
- **⚠ Ordering:** never retire suppression CSS before removing its target

### GATE C — Home composition
- **Files:** `SolariunHomeCockpit.tsx`
- **Tests:** `test_solariun_thread_navigation_01.py` (**A — must stay green**)
- **Closure evidence:** one dominant state + 1–3 actions above fold at 366px; empty states merged; no fabrication; thread section becomes disclosure
- **Rollback:** single file

### GATE D — Project composition
- **Files:** `ProjectDashboard.tsx` (tab strip only; 1255 lines — touch the strip, not the panels)
- **Tests:** `test_p0_1_project_field_continuity.py` (**A — must stay green**)
- **Closure evidence:** 3 primary / 5 contextual / 2 inspector / 1 settings; `PROJECT_LENS_TO_TAB` mapping unchanged

### GATE E — Weaver contextualization
- **Files:** `SolSpireExperience.tsx` (nav entry), `SolSpireWorkspacePanels.tsx`
- **Tests:** `test_weaver_k2` (**A**), `test_weaver_sci_boundary_01`/`contract_01` (C)
- **Closure evidence:** Weaver no longer reads as a peer product; project is canonical work surface; no second authority path

### GATE F — Engineering Lab hierarchy
- **Files:** `EngineeringLabLens.tsx`, `EngineeringLabRuntimeLens.tsx`
- **Tests:** `test_engineering_lab_substrate.py` (**38 A — must stay green**)
- **Closure evidence:** runtime first; architecture/governance/evidence disclosed

### GATE G — Mobile composition
- **Files:** `SolSpireExperience.tsx` (nav duplication), CSS
- **Closure evidence:** single responsive nav; 366px shows one rail, one header, one first action

### GATE H — Typography / iconography / copy
- **Closure evidence:** ≤3 sub-13px levels; one glyph system; zero glyph collisions (§6.1 of seam map)

### GATE I — Accessibility + runtime verification
- **Closure evidence:** focus/contrast/landmarks/reduced-motion; populated **and** empty states verified

**Hard rule:** Gate H is last. Cosmetics before ownership re-decorate the seams.

---

## 12. RUNTIME VERIFICATION PLAN

`vite build` is **environment-blocked** in the sandbox (no npm registry access; no local TypeScript toolchain) — consistent with the recorded baseline. Therefore:

| Gate | Required evidence | Honest limitation |
|------|-------------------|-------------------|
| A | desktop + 366px screenshots, authenticated, one rail/one identity bar | visual claims require human/runtime capture |
| B | DOM inspection proving duplicate chrome absent (not merely `display:none`) | build unavailable → source + runtime DOM |
| C | 366px first-action above fold; empty-state count = 1 | screenshots required |
| D | tab strip tiering visible; `p0.1` continuity intact | test-backed |
| E | Weaver contextual; no new authority route | test-backed (`weaver_k2`) |
| F | Lab default viewport = runtime only | test-backed (38) |
| G | 366px single nav | screenshots required |
| H | ≤3 type levels; glyph collision count = 0 | source-counted |
| I | focus/contrast/a11y + populated & empty | needs runtime |

**Source-level test suite** must be run before and after each gate; the §4.7 invariant set must remain green, and any Class-C amendment must be **declared in that gate's PR** with the rewrite rationale.

---

## 13. OPEN UNKNOWNS

1. **`Radar` / `opportunity-radar`** renders **static hardcoded data** incl. contact PII for 3 named organisations. Live product, private list, or demo? — **product decision; UNRESOLVED.**
2. **5 × `SocialField*.tsx`** orphan pages — intentionally retired or abandoned work? **UNKNOWN.**
3. **`distribute` route** has no navigation entry — reachable only by URL. **UNKNOWN.**
4. **`goals`/`releases`/`jobs`/`traces`/`tools`** legacy keys — any external bookmarks? **UNKNOWN.**
5. **`ExperienceConsolidationFrame.onNavigate`** historical use. **UNKNOWN.**
6. **`test_area_c` / `p1_1` string assertions** — need replacement *behavioural* assertions; not yet designed. **UNKNOWN** (scope for Gates B/C).
7. **CI coverage:** 7 workflows mention `pytest`; whether they gate merges on these tests is **UNVERIFIED**.
8. **`PrismInteriorShell` repair-CSS/mobile interaction** — the sidebar was converted from a flex row to `position:fixed` (`experience-repair.css:113+`); whether the original mobile layout still functions after Gate B is **UNKNOWN** without runtime.

---

## 14. EXPLICIT NON-GOALS

- No new frontend design system.
- No new product concept or surface.
- No new navigation system.
- No new persistence layer.
- No backend change.
- No visual token / icon / copy change.
- No test edits.
- No route deletion.
- No shell removal.
- No cosmetic redesign.
- No implementation of any kind.

---

## 15. VERDICT

The evidence is sufficient to establish ownership, collisions, dependencies, the test constraint register, and gate ordering. The unknowns in §13 are **product decisions and runtime verification requirements**, not architectural blockers.

**SCALPEL READY**

The architecture has been mapped sufficiently for implementation.
No implementation has been performed.
Human authorization is required before crossing into the implementation phase.

**Recommended first cut: GATE A only**, with the Class-C test amendments from §4.2 declared explicitly in that PR.

---

### Corollary — the governing rule for this work

> Do not make the frontend simpler by destroying architectural depth.
> Make the frontend simpler by giving each layer exactly one place to speak.

*Repository wins. Absence is valid state. Merge and deployment remain human-only.*
