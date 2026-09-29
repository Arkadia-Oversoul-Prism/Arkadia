# AEAS Frontend Seam Map + Experience Hierarchy Matrix

**STATUS:** DIAGNOSIS ARTIFACT / NO CODE CHANGES
**MODE:** AEAS · EVIDENCE-DRIVEN · BOUNDED
**AUTHORITY:** HUMAN
**SOURCE OF TRUTH:** CURRENT REPOSITORY @ `67a660c`
**COMPANION:** `docs/architecture/AEAS_FRONTEND_BRAND_CALIBRATION.md` (dimensions + Pass A–D audit sequence)

> This artifact inventories the seams. It does not implement, patch, restyle, or refactor.
> Every claim below carries a `file:line` reference or is explicitly labelled `UNVERIFIED`.

---

## 0. CONTRADICTION REPORT (read first)

The prior pass reported creating this file at commit `fafcccd9d7438336c3029074f40f6a822b196880`
and recording it on PR #116. **Neither exists.**

| Claim | Verification | Result |
|-------|--------------|--------|
| Commit `fafcccd9…` | `git cat-file -t` | **bad object — does not exist** |
| `docs/architecture/AEAS_FRONTEND_SEAM_MAP.md` | `ls`, `git log --all -- <path>` | **absent from all refs** |
| PR #116 contains the seam map | GitHub API `/pulls/116/files` | **only `AEAS_FRONTEND_BRAND_CALIBRATION.md` (+253)** |
| PR #116 exists and merged | GitHub API | **TRUE** — merged; different artifact |

PR #116 is real and merged, but its sole file is `docs/architecture/AEAS_FRONTEND_BRAND_CALIBRATION.md`
(a calibration brief: 10 dimensions, Pass A–D sequence). It is **not** the seam map described in the
prior summary, and it does not contain the S1–S16 seam table, the disposition classifications, or the
acceptance conditions that were reported.

**Classification: CONTRADICTED.** The described artifact was reported as delivered and was not.
This file is the actual deliverable. The prior narrative is not treated as evidence.

---

## 1. Evidence base

Inspected read-only at `67a660c` (PR #122 merged):

| Area | Files |
|------|-------|
| App shell + routing | `web/public_prism/src/App.tsx` |
| Global navigation | `web/public_prism/src/components/ArkadiaNavigation.tsx` |
| Authenticated shell | `web/public_prism/src/components/PrismInteriorShell.tsx` |
| Consolidation wrapper | `web/public_prism/src/components/ExperienceConsolidationFrame.tsx` |
| Workspace shell | `web/public_prism/src/components/solspire/SolSpireExperience.tsx` |
| Console entry | `web/public_prism/src/pages/SolariunConsole.tsx` |
| Home | `web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx` |
| Project surface | `web/public_prism/src/pages/ProjectDashboard.tsx` |
| Lab | `…/solspire/EngineeringLabLens.tsx`, `…/EngineeringLabRuntimeLens.tsx` |
| Constraint tests | `tests/test_prism_pass_c_surface_ownership.py`, `tests/test_prism_interior_shell.py`, `tests/test_solariun_*.py`, `tests/test_solspire_*.py` |

**Runtime/visual claims are the sovereign's screenshots.** This artifact does not assert visual
quality from source alone; screenshot-derived observations are marked `[SCREENSHOT]`.

---

## 2. Shell ownership inventory (measured)

The authenticated Solariun route nests **five** conceptual shells:

```
ArkadiaNavigation                      (global nav + mobile drawer)   App.tsx:121
  └ SonataBar
  └ AnimatePresence
      └ ExperienceConsolidationFrame   surface="Solariun"             App.tsx:148
          └ SolariunConsole            auth gate                      SolariunConsole.tsx:6
              └ SolSpireExperience     canonical workspace shell      SolariunConsole.tsx:6
```

Separately, `PrismInteriorShell` provides **its own** identity bar + surface rail + "More" lenses
(`PrismInteriorShell.tsx:48`, `:96`), i.e. a **second** global chrome implementation.

**Finding:** `ArkadiaNavigation` and `PrismInteriorShell` are two parallel global-chrome systems.
`ExperienceConsolidationFrame` is a pure wrapper whose `onNavigate` prop is **unused** — it adds a
DOM boundary and test id but no consolidation (`ExperienceConsolidationFrame.tsx:20–29`).

---

## 3. Navigation systems inventory (measured — 6 concurrent)

| # | System | Location | Contents |
|---|--------|----------|----------|
| N1 | Global nav drawer (grouped) | `ArkadiaNavigation.tsx:12–26` | Field/Nexus/Workspaces/System + 7 quick buttons (`:39`) |
| N2 | Authenticated surface rail | `PrismInteriorShell.tsx:44,96` | PRIMARY + SECONDARY + "More" expander |
| N3 | Solariun sidebar | `SolSpireExperience.tsx:66` | 12 lenses, each with a question sub-label |
| N4 | Solariun mobile bottom rail | `SolSpireExperience.tsx:64–65` | 9 items from `BOTTOM_NAV` |
| N5 | Solariun mobile "More" menu | `SolSpireExperience.tsx:210–211` | NAV + NETWORK duplicated in a sheet |
| N6 | Context bar breadcrumb | `SolSpireExperience.tsx:66` (`ContextBar`) | `ARKADIA / SOLARIUN / <LENS>` |
| N7 | Project tab strip | `ProjectDashboard.tsx:1174–1185` | 11 tabs |

**Three distinct taxonomies are exposed simultaneously:** product rail (N2: NovaNet/Solariun/SolSpire/…),
workspace lenses (N3: 12), project tabs (N7: 11). None declares itself canonical.

### 3.1 Taxonomy disagreement (measured)
`ArkadiaNavigation` groups surfaces as **Field / Nexus / Workspaces / System**.
`PrismInteriorShell` splits the same surfaces into **PRIMARY / SECONDARY / More**.
Both are rendered in the same product. The same concept therefore has two different homes.

### 3.2 Label drift `[SCREENSHOT + UNVERIFIED]`
The screenshot shows a bottom item labelled **"Radar"**. No `Radar` string exists anywhere in
`web/public_prism/src` (`grep -rn "Radar"` → empty). Source label is `Commercial`
(`SolSpireExperience.tsx:36`). Either the screenshot is from a different revision or the label is
rendered from data. **Not asserted** — flagged for runtime confirmation.

### 3.3 Dead routes (measured)
`type View` declares 30 members (`App.tsx:36`); only 27 have a render block.
**No render block:** `dashboard`, `loops`, `nexus`.
They are still reachable — `handleNavigate` remaps them (`App.tsx:115–118`) — so they are
compatibility aliases, not dead code, but they remain in the public type surface.

### 3.4 Orphan pages (measured)
Five social-field implementations exist; **none is referenced by `App.tsx`**:
`GovernedSocialField.tsx`, `SocialFieldFinal.tsx`, `SocialFieldPage.tsx`,
`SocialFieldStable.tsx`, `SocialFieldVerified.tsx`.

---

## 4. The seam map

| Seam | Colliding layers | Evidence | Effect |
|------|------------------|----------|--------|
| **S1** | Global chrome × 2 | `ArkadiaNavigation.tsx:12` vs `PrismInteriorShell.tsx:44,48,96` | Two identity bars, two rails |
| **S2** | 6–7 navigation systems | §3 table | Orientation ambiguity |
| **S3** | Product × workspace × object taxonomy | N2 / N3 / N7 | Everything reads as a peer |
| **S4** | Backend objects rendered as UI blocks | Home sections `SolariunHomeCockpit.tsx:253–474` | Schema leakage |
| **S5** | State honesty × state exposure | `stateLabel`/`diagnosticLabel` `:64–70`; bootstrap bar `:254` | Honest but exhausting |
| **S6** | Mythology × operational language | `FieldSection` labels `:253–474`; sigils §6 | Decoding burden |
| **S7** | Operator UI × user UI | Lab `EngineeringLabLens.tsx`; RuntimeLens | Audience collision |
| **S8** | Current × legacy architecture | `View` union 30 (`App.tsx:36`); `LEGACY_MAP` (`SolariunConsole.tsx:5`) | Archaeological feel |
| **S9** | Workspace × project nesting | App→Console→Experience→ProjectDashboard (4 levels) | Nested nav stacks |
| **S10** | Weaver as capability × destination | Weaver in NAV `:43` **and** as project tab `ProjectDashboard.tsx:1176` | Fragmentation |
| **S11** | Lab observability × architecture docs × governance | Lab section headings `>System state<`, `>Lab version<`, `>Commit classifications<`, `>Authority ceiling<`, `>Observation warnings<` | Report gravity |
| **S12** | Visual identity × decoration | §6 iconography; §7 typography | Signal-to-noise |
| **S13** | Mobile viewport × density | N4 (9 items) + N6 + N3 + N7 at 366px `[SCREENSHOT]` | Vertical overload |
| **S14** | Evidence IDs × human objects | `ObjectCard` renders `object.id` (`SolSpireExperience.tsx:68`) | Database feel |
| **S15** | Configuration × navigation | `settings` inside NAV `:45` and inside project TABS `:1185` | Settings contamination |
| **S16** | "What matters now?" × 12-subsystem inventory | heading `:240` vs sections `:253–474` | Home loses purpose |

### 4.1 Weaver is presented twice (measured, S10)
- As a **top-level lens**: `{id:'weaver', …}` in `NAV` (`SolSpireExperience.tsx:43`).
- As a **project tab**: `{ id: 'weaver', label: 'Weaver', sigil: '⟐' }` (`ProjectDashboard.tsx:1176`).
Its real API surface is project-scoped (`/solspire/projects/{id}/weaver/*`, `ProjectDashboard.tsx:81–218`).
The workspace-level entry therefore leads to a **project picker**, not to work.

### 4.2 Engineering Lab mixes three products (S7/S11)
Observability + architecture documentation + governance, at equal visual weight.
Headings: `System state`, `Lab version`, `Commit classifications`, `Authority ceiling`,
`Observation warnings` (`EngineeringLabLens.tsx`). No dominant first answer.

---

## 5. Hierarchy ownership matrix (proposed — one owner per layer)

| Layer | Question it answers | Proposed sole owner | Currently owned by |
|-------|--------------------|---------------------|--------------------|
| GLOBAL SHELL | What product am I in? | `ArkadiaNavigation` | ArkadiaNavigation **+** PrismInteriorShell |
| PRODUCT SHELL | Which workspace? | `PrismInteriorShell` rail (N2) | N2 **+** ArkadiaNavigation groups |
| WORKSPACE SHELL | Where inside the workspace? | Solariun sidebar (N3) | N3 **+** N4 **+** N5 |
| OBJECT CONTEXT | Which project/object? | `ContextBar` (N6) | N6 **+** project header |
| ACTION | What can I do? | lens body | lens body **+** ContextBar buttons |
| EVIDENCE / INSPECTION | Prove it | progressive disclosure | rendered inline everywhere |

**Rule for the eventual implementation:** each layer gets exactly one owner; every other
implementation is `MERGE`d into it or `HIDE`d behind progressive disclosure.

---

## 6. Iconography findings (measured)

Three unrelated glyph systems are in use across the shells:

1. **Latin letters as sigils** — `H O * N A # S P` (`ArkadiaNavigation.tsx:13–26`)
2. **Unicode geometry** — `◈ ◎ ⌁ ◉ ◫ ◌ □ ∞ ⚒ ⟐ ⌬ ◆ ▦ ✧ ⌘ ✦` (`SolSpireExperience.tsx`, `PrismInteriorShell.tsx`)
3. **Emoji** — `💬 📄 ⟁ ⚙` (`ProjectDashboard.tsx:1178–1185`)

### 6.1 Sigil collisions (measured — same glyph, different meanings)
```
◈  → Projects | Solariun (×3) | Knowledge | Overview
◉  → Knowledge | Nexus Hub | NovaNet
◎  → Home | Echofeild | Events
⟐  → Activity | Weaver | Workflows
✧  → Oracle | Spiral Grove
✦  → Offerings | Spiral Codex
◇  → Commercial | Encyclopedia
⌘  → ReasoMate | Spiral Command
∞  → Memory (×2, consistent)
▦  → SolSpire (×2, consistent)
```
**8 glyphs carry multiple meanings.** A sigil cannot function as recognition when it is ambiguous.
This is the concrete form of the "funny looking icons" observation.

---

## 7. Typography findings (measured)

Micro-uppercase levels in simultaneous use within one viewport:

| Level | Example | Source |
|-------|---------|--------|
| 7px mono | `PRISM · AUTHENTICATED` | `PrismInteriorShell.tsx:48` |
| 8px sans | role, username | `PrismInteriorShell.tsx:48` |
| 8px sans | section labels | `SolariunHomeCockpit.tsx:73` |
| 9px mono | identity / workspace state line | `SolariunHomeCockpit.tsx:264` |
| 10px mono | bootstrap status | `SolariunHomeCockpit.tsx:254` |
| 10–12px sans | body/muted | throughout |
| 17px serif | object titles | `:290` |
| clamp 26–52px serif | page H2 | `:240` |

Six type sizes below 13px, each with distinct letter-spacing and case treatment, produce
**label fatigue**: the reader must classify each label's role before reading it.

---

## 8. Empty-state and state-vocabulary findings

**Truthfulness is correct and must be preserved.** Home explicitly refuses substitution
(`SolariunHomeCockpit.tsx:255`, `:471`). The problem is **composition**, not honesty:

- Five sibling empty states stack vertically (`No open-loop state…`, `No active workload…`,
  `No current signal…`, `No recent activity events…`, `No proposals…`).
- Raw state vocabulary is surfaced to the user: `SurfaceState` = `LOADING|LIVE|EMPTY|UNAVAILABLE|FAILED`
  (`:44`), rendered verbatim (`:254`, `:264`).
- Internal diagnostic strings are user-visible: `diagnosticLabel` emits
  `STATE [kind · status · path]` (`:64–70`).

**Direction:** compress to one honest workspace state + actions; move vocabulary into an inspector.

---

## 9. Disposition table

Classification vocabulary (frozen): **KEEP · MERGE · CONTEXTUALIZE · PROGRESSIVE DISCLOSURE · HIDE · ARCHIVE**

| Item | Location | Disposition |
|------|----------|-------------|
| Dark Arkadia field + gold/teal/violet palette | global CSS | **KEEP** |
| Serif/sans/mono relationship | global | **KEEP** |
| State honesty (no substitution) | `SolariunHomeCockpit.tsx:255` | **KEEP** |
| `SolariunConsole` auth gate | `SolariunConsole.tsx:6` | **KEEP** |
| Weaver lifecycle concept | `SolariunGrammar.tsx` | **KEEP** (compress presentation) |
| Follow-the-thread concept | `SolariunHomeCockpit.tsx:443` | **KEEP** (relocate/compress) |
| `ArkadiaNavigation` global shell | `ArkadiaNavigation.tsx` | **KEEP as sole global owner** |
| `PrismInteriorShell` rail + identity bar | `PrismInteriorShell.tsx:44,48,96` | **MERGE** into global shell |
| `ExperienceConsolidationFrame` (no-op wrapper) | `ExperienceConsolidationFrame.tsx:20–29` | **MERGE** / remove boundary |
| Solariun sidebar N3 + mobile N4 + More N5 | `SolSpireExperience.tsx:64–66` | **MERGE** to one nav, responsive variants |
| Context bar breadcrumb N6 | `SolSpireExperience.tsx:66` | **CONTEXTUALIZE** (object scope only) |
| Project tab strip (11 tabs) | `ProjectDashboard.tsx:1174–1185` | **CONTEXTUALIZE** (group by job) |
| `settings` inside NAV | `SolSpireExperience.tsx:45` | **HIDE** from primary nav |
| `settings` inside project TABS | `ProjectDashboard.tsx:1185` | **HIDE** from tab strip |
| Weaver as top-level lens | `SolSpireExperience.tsx:43` | **CONTEXTUALIZE** (→ project work mode) |
| Weaver as project tab | `ProjectDashboard.tsx:1176` | **KEEP** (becomes the canonical home) |
| Engineering Lab report blocks | `EngineeringLabLens.tsx` | **PROGRESSIVE DISCLOSURE** |
| Lab governance / authority ceiling | `EngineeringLabLens.tsx` | **PROGRESSIVE DISCLOSURE** |
| `object.id` in `ObjectCard` | `SolSpireExperience.tsx:68` | **PROGRESSIVE DISCLOSURE** |
| Raw `SurfaceState` vocabulary | `SolariunHomeCockpit.tsx:44,254` | **PROGRESSIVE DISCLOSURE** (inspector) |
| Diagnostic `[kind · status · path]` | `SolariunHomeCockpit.tsx:64–70` | **PROGRESSIVE DISCLOSURE** |
| Emoji sigils `💬 📄 ⟁ ⚙` | `ProjectDashboard.tsx:1178–1185` | **MERGE** into one glyph system |
| Ambiguous Unicode sigils (§6.1) | multiple | **MERGE** (dedupe) or **HIDE** |
| Latin-letter sigils `H O N A S P` | `ArkadiaNavigation.tsx:13–26` | **MERGE** into one glyph system |
| `View` union aliases `dashboard`/`loops`/`nexus` | `App.tsx:36,115–118` | **ARCHIVE** (keep aliases, drop from type) |
| `LEGACY_MAP` | `SolariunConsole.tsx:5` | **ARCHIVE** |
| 5 orphan SocialField pages | `pages/SocialField*.tsx` | **ARCHIVE** |
| Micro-uppercase levels 7–10px (§7) | multiple | **MERGE** to ≤3 levels |
| Enterprise surfaces | `EnterpriseConsole.tsx` | **CONTEXTUALIZE** (reachable from Home) |

---

## 10. Constraint register (what any change must not break)

Source-level tests constrain this work. Any implementation must satisfy these **without weakening them**:

| Test | Constraint |
|------|-----------|
| `test_prism_pass_c_surface_ownership.py` | `knowledge-os`/`codex`/`loops` resolve via `SolariunConsole`; **no new top-level views** |
| `test_prism_interior_shell.py` | `novanet-primary-rail`, `identity-persistence` test ids |
| `test_solariun_experience_consolidation_01.py` | `surface="Solariun"`, `ExperienceConsolidationFrame`, `experience-inspector`, `experience-context-bar` |
| `test_solspire_p1_experience_01.py` | `solariun-knowledge-library-mode`, `solariun-object-sheet`, Arkana context pack strings |
| `test_p0_1_project_field_continuity.py` | `PROJECT_LENS_TO_TAB`, `data-field-continuity="p0.1"` |
| `test_solariun_thread_navigation_01.py` | `onNavigate` bounded to 3 targets; `onThreadTarget={selectSection}` |

**Implication:** consolidating shells will require *amending these tests deliberately*, not
silently. That is a governance act and must be declared in the implementation PR.

---

## 11. Implementation order (when authorized)

```
1. NAVIGATION OWNERSHIP          (one canonical taxonomy; N1/N2/N3/N4/N5 decision)
2. SHELL CONSOLIDATION           (merge PrismInteriorShell rail; drop no-op frame)
3. HOME HIERARCHY                (one dominant state + actions; compress empties)
4. PROJECT HIERARCHY             (group 11 tabs by job; settings out of strip)
5. WEAVER CONTEXT                (project work mode, not a peer destination)
6. ENGINEERING LAB HIERARCHY     (runtime first; docs + governance disclosed)
7. MOBILE COMPOSITION            (stress-test at 366px)
8. TYPOGRAPHY / ICONOGRAPHY      (≤3 levels; one glyph system; dedupe collisions)
9. COPY                          (Layer 1 human action before Layer 3 Arkadia language)
10. PROGRESSIVE DISCLOSURE       (ids, state vocabulary, diagnostics → inspector)
11. ACCESSIBILITY                (focus, contrast, landmarks, reduced motion)
12. RUNTIME VERIFICATION         (desktop + mobile, empty + populated)
```

**Do not begin at step 8.** Cosmetic work before ownership consolidation re-decorates the seams.

---

## 12. Acceptance conditions

An implementation is acceptable only when, at 366px and desktop:

1. **Where am I?** — exactly one answer (no competing breadcrumbs/rails/headers).
2. **Why am I here?** — one sentence, in human language.
3. **What matters now?** — one dominant state, even when that state is "nothing needs attention".
4. **What can I do next?** — 1–3 meaningful actions above the fold.
5. **What deeper architecture exists?** — available on demand, not pre-loaded.
6. No glyph carries two meanings.
7. No raw state token or internal id is visible without an explicit inspection act.
8. State honesty preserved: no fabricated activity, no substituted placeholder.
9. No new top-level view; no second navigation or state system.
10. Constrained tests pass, with any amendment explicitly declared.

---

## 13. Do not throw away

Dark Arkadia field · gold/teal/violet semantics · serif/sans/mono relationship ·
Solariun/SolSpire distinction · object grammar · state honesty · Follow-the-thread concept ·
Engineering Lab capability · Weaver governance substrate · unified project resources ·
Arkadia mythology **as atmosphere, not as operating manual**.

---

## 14. North star

> **Arkadia should feel smaller than it actually is.**
> The architecture may be enormous. The user's next decision should not be.

The substrate stays deep. The interface gets quiet.

---

## 15. Verdict

The frontend has successfully **accumulated** the architecture but has not yet performed the
**compression** of that architecture into an experience. The primary defect is **hierarchy
collision** — many individually reasonable components each asking to be first — not component
quality, not styling, and not the absence of capability.

**No code was changed by this artifact.** Merge and production deployment remain human-only.
