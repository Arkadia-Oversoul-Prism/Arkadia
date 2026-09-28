# SOLARIUN-THREAD-01 — Whole-Architecture Experience Calibration — EVIDENCE

**Authorization:** human ("Proceed") on the whole-architecture experience-calibration pass.
**Base:** `e6f79f177053eb9a9b414e6744d3f78165f28f9a` (production `main`, PR #102 merged).
**Branch:** `solariun/thread-navigation-01`.
**Merge / production deploy:** HUMAN ONLY. Neither performed.

---

## 1. Four evidence questions

Answered from read-only inspection of the tree at `e6f79f1` (frontend + backend routers).

### Q1 — Can the UI expose real enterprise state?
**Partially.** Home renders only real, live data (`/solspire/workspace`, `/pulses/today`,
`/workloads`, `/workevents`, `/syntheses/current`, `/proposals`, `/api/me/field`) with a
genuine `data-solariun-identity-alignment=ALIGNED|MISMATCH|UNKNOWN` check and an explicit
"No placeholder state has been substituted." **But organisation/enterprise state is not
reachable from Home at all**: `GET /solspire/enterprise/workspaces` is consumed only by
`EnterpriseConsole.tsx`, which Home does not reference and cannot navigate to.

### Q2 — Can it expose real Engineering Lab / Weaver state?
**Yes for the Lab; project-scoped only for Weaver; and the two are mutually unlinked.**
`EngineeringLabLens` reads `/api/lab/overview`; `EngineeringLabRuntimeLens` reads
`/api/lab/engineering/overview` (sessions, agents, gateway, authority ceilings, android,
voice). Weaver execution state lives behind the **project** tab
(`/solspire/projects/{id}/weaver/*`) in `ProjectDashboard`. Neither references the other.

### Q3 — Is Knowledge OS the memory/evidence substrate, or another destination?
**Another destination tab.** It is one sidebar entry rendering a leaf `KnowledgeOSPage`,
explicitly annotated *"GLOBAL KNOWLEDGE LIBRARY · System-wide Knowledge OS — not the active
project corpus"*. It has zero outbound links. Knowledge *feeds* Home's counts via
`/api/me/field`, but is never presented as the evidentiary substrate of a thread.

### Q4 — Can a human follow one consequential thread across the surfaces?
**No.** There is no UI element carrying one artifact identity through
identity → workspace → event → proposal → authority → execution → evidence → knowledge →
verification. The only working handoffs are lens → project-tab. Home, Lab and Knowledge are
mutually unlinked leaves. The components that visually resemble a chain
(`WEAVER_LIFECYCLE`, `EpistemicInspector`) are display-only captions that explicitly
disclaim proving causal provenance.

**Diagnosis confirmed:** the frontend is not empty and is not crashing — it is
**experience composition debt**. The backend connective tissue exists; the UI does not make
it perceptually obvious.

---

## 2. Bounded objective

Make the chain **followable** from Home without introducing:
- a new dashboard or top-level view,
- second navigation or state system,
- a derived "continuity" value,
- any implied transition the substrate has not established.

**Completion condition:** Home exposes a truthful handoff to Weaver / Engineering Lab /
Knowledge, the chain is named, and the no-authority/no-derivation boundary is explicit.

**Regression boundary:** full suite gains no failure vs `main`; existing frontend-source
contracts unchanged.

---

## 3. Changes

| File | Change |
|------|--------|
| `web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx` | Added optional bounded `onNavigate` prop; added "Follow the thread" section naming the full chain with three destination buttons; truthful no-handler fallback |
| `web/public_prism/src/components/solspire/SolSpireExperience.tsx` | `LensContent` accepts `onThreadTarget`; Home wired to `selectSection` (existing lens state, no new router) |
| `tests/test_solariun_thread_navigation_01.py` | **New** guard for the thread contract |

Deliberately **not** done: no new route, no `View` union change, no new component library, no
enterprise/Weaver unification (that requires artifact-level identity the backend does not yet
expose at workspace scope — recorded as a limitation, not faked).

---

## 4. Verification

| Gate | Result |
|------|--------|
| New thread tests | **6 passed** |
| Lab substrate/API tests | unchanged (passing) |
| Full suite (branch) | **49 failed / 897 passed / 12 skipped / 2 errors** |
| Full suite (clean `main`, same env) | **49 failed / 891 passed / 12 skipped / 2 errors** |

### 4.1 Baseline comparison
```
introduced by this change : (empty)   — 0 new failures
resolved by this change   : (empty)   — 0 (none claimed)
failure sets              : byte-identical (49 = 49)
passing delta             : +6 = exactly the new tests
```
Branch-local pre-existing failures (`test_solariun_experience_consolidation_01`,
`test_solspire_p1_experience_01`) were confirmed against a stashed clean tree with
**identical fingerprints** — not attributable to this work.

### 4.2 Build limitation
`vite build` remains **environment-blocked**: the sandbox cannot reach
`registry.npmjs.org` (`npm install` → network error; no local `node_modules` or TypeScript
toolchain). This matches the recorded baseline (`vite_build := environment-blocked`). The
change is TS-checked by inspection only (balanced JSX/binding, prop types conform to the
existing `SolSpireLens` union) — **not** compiled. Flagged for reviewer awareness.

---

## 5. Consent boundaries preserved

- UI is projection. Backend remains sole source of truth.
- No new parallel state; no second intelligence spine; no fake reasoning.
- No autonomous authority. Copy states explicitly: "not a second source of truth",
  "no transition is implied that the substrate has not established".
- Home degrades truthfully when no handler is injected ("No synthetic destination has been
  substituted.") rather than fabricating navigation.

---

## 6. Known limitations

- **Artifact-level thread continuity is not solved.** Weaver remains project-scoped; a
  workspace-level proposal→run→evidence thread needs a backend identifier that does not
  currently exist at that scope. Not fabricated.
- **Enterprise state is not surfaced on Home.** `EnterpriseConsole` remains a separate door;
  unifying it is a larger, separately-authorizable workstream.
- Lab ↔ Weaver remain unlinked — the shared identifier is absent.
- `vite build` unverified in this environment (see 4.2).

---

## 7. Rollback

Revert the commit / delete the branch. Changes are confined to 2 source files + 1 test file;
`SolariunHomeCockpit` reverts to its propless signature.

---

## 8. References

- Base: `e6f79f177053eb9a9b414e6744d3f78165f28f9a`
- Branch: `solariun/thread-navigation-01`
- Verdict: **VERIFIED** (source-level; build environment-blocked as baseline)
