# PRISM-L1 — focus-ring + reduced-motion recovery (Slice B)

Lane 1 (shell / navigation / design system / integration seam).
Governing docs: `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`,
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

- Lane branch: `feat/prism-l1-lens-strip-keyboard-01` (PR #529 — **updated in place**,
  no new PR opened).
- Base observed at pass start: `origin/main` = `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1`.
  Main was **merged into the lane branch** before this slice (`0c62b377`), so the
  slice is measured against current main and PR #529 becomes mergeable again.
- Scope: 2 files — `web/arkadia_console/src/index.css` (+39),
  `tests/test_console_focus_ring_contract.py` (new, 11 nodes).

## 1. What was measured (not assumed)

Two capabilities the archived Prism carried in its `index.css` were dropped by the
console rebuild (`c081d200`, "Frontend rebuild: archive Prism UI, scaffold canonical
Arkadia Console") and have never been restored. Measured on `main` @ `2a1bca75`:

```
grep -rn "focus-visible"      web/arkadia_console/src   -> 0 matches
grep -rn "prefers-reduced-motion" web/arkadia_console/src -> 0 matches
```

Meanwhile the console *animates*:

```
grep -rn "animate-pulse" web/arkadia_console/src
  components/ui.tsx, pages/ArkanaPage.tsx,
  components/opportunities/ProjectOpportunityRadar.tsx
```

and it *un-styles* focus on five surfaces:

```
grep -rn "outline-none" web/arkadia_console/src
  pages/ArkanaPage.tsx:78            outline-none focus:border-emerald/50
  pages/SignInPage.tsx:60,71         outline-none focus:border-gold/60
  components/Shell.tsx:115           focus:outline-none
  components/knowledge/KnowledgeTimelinePanel.tsx:77
  components/knowledge/KnowledgeSearchPanel.tsx:97
  components/opportunities/ProspectEntryForm.tsx:86
```

Each of those supplies a `focus:border-*` colour cue — but `Shell.tsx:115` is the
global search field and supplies **none** (`className="min-w-0 flex-1 focus:outline-none"`),
so that control has *no* focus indicator at all. The shared ring is the general fix;
it is not a substitute for the per-control cue, and vice-versa.

## 2. The correction this pass had to make

The inherited tracker claimed the next Lane 1 gap was *"non-focusable onClick"* on
`ArkanaPage.tsx:81` and `SolariunPage.tsx:153`. Measured: **both are `<button>`**
(verified by reading the opening tags), as is every one of the ~20 `onClick`
handlers under `web/arkadia_console/src`. There is no `onClick` on a non-interactive
element on current main. The declared gap was a mis-diagnosis; the two rules above
are the real, measured, unclaimed defect.

## 3. The change

`web/arkadia_console/src/index.css` (+39) — both rules recovered from the archive's
own stylesheet (`archive/frontend/arkadia-prism/web/public_prism/src/index.css`):

```css
@layer base {
  a:focus-visible, button:focus-visible, input:focus-visible,
  select:focus-visible, textarea:focus-visible {
    @apply outline outline-2 outline-offset-2 outline-emerald/65;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Two deliberate deviations from the archive text, both recorded:

- The archive wrote `outline: 2px solid rgba(0,212,170,.65)` as a raw literal. The
  console is token-driven, so the ring is expressed as `outline-emerald/65` — the
  `emerald: #00D4AA` token at the same alpha. **Verified equivalent**: the built
  stylesheet emits `outline-color:#00d4aaa6`, and `0xa6/0xff = 0.65`.
- `select` is added to the archive's four selectors for parity with the console's
  form-control set.

## 4. Runtime proof (build, not prose)

`cd web/arkadia_console && corepack pnpm run build` → **PASS** (`tsc --noEmit && vite build`,
85 modules, 1.63s). The emitted stylesheet carries both rules:

```
dist/assets/index-CAyfhlzZ.css
  ,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible
  {outline-style:solid;outline-width:2px;outline-offset:2px;outline-color:#00d4aaa6}

  @media (prefers-reduced-motion: reduce){*,*:before,*:after{animation-duration:.01ms
  !important;animation-iteration-count:1!important;transition-duration:.01ms!important;
  scroll-behavior:auto!important}}
```

This proves the `@apply` resolved against the real Tailwind token — a rule that
failed to compile would simply be absent from the bundle.

## 5. Guard + negative controls

`tests/test_console_focus_ring_contract.py` — 11 nodes. Comment-stripping is
load-bearing: the module docstring **and** the inline comment both quote
`:focus-visible`, so a raw-text detector would score the prose as the fix
(`test_detector_ignores_the_provenance_comment` is the control for exactly that).

Six negative controls, each fed the real defect shape:

| control | mutation | must be reported |
|---|---|---|
| `test_detector_flags_the_pre_repair_stylesheet` | both blocks removed | ring + motion |
| `test_detector_flags_a_ring_that_is_not_token_derived` | `emerald/65` → `[#00D4AA]` | raw hex |
| `test_detector_flags_a_ring_that_covers_only_buttons` | `a`/`input`/`textarea` dropped | partial coverage |
| `test_detector_flags_a_motion_query_that_forgets_transitions` | `transition-duration` dropped | incomplete query |
| `test_detector_ignores_the_provenance_comment` | comment-only file | not a rule |
| `test_the_archive_rule_is_quoted_verbatim_for_auditability` | archive file moved | pins provenance |

**Live negative control on the real file** (not a synthetic string): removing
`@layer base {…}` from `web/arkadia_console/src/index.css` in the working tree →
`4 failed, 7 passed`; removing the `@media` block → `7 failed, 4 passed`; restoring
byte-identically → `11 passed`. The detectors read the shipped file.

## 6. Regression boundary — no node-set delta

- `tests/test_console_focus_ring_contract.py` — **11 passed** (new; 11 collected).
- `tests/test_console_shell_nav_contract.py` + `tests/test_console_lens_landmark_contract.py`
  + `tests/test_prism_console_ci_wiring.py` — **67 passed**, then wiring judge alone
  **30 passed**. Zero failures.
- `tests/architecture` — **11 passed** (matches the documented 11/11).
- `python -m py_compile api/main.py` — **OK** (`api/main.py` untouched; no boot risk).
- CP10 mutation boundary — `printf '<both paths>' | python scripts/cp10_mutation_boundary_policy.py --judge`
  → `PASS`, exit **0**.
- `+11` on the tree is entirely the new guard file's 11 nodes, attributed by
  `--collect-only` rather than inferred from a count delta (no second full-suite run
  was spent, per the pulse contract).

## 7. CI wiring — derived, not restated

`scripts/console_contract_domain.py` derives the console-contract guard domain from
`git ls-files` **at call time**. The new guard names `web/arkadia_console` in its
source, so it enters the domain by content: `python scripts/console_contract_domain.py`
→ **27** entries (26 before), including `tests/test_console_focus_ring_contract.py`.
The CI gate runs `pytest -q $(python scripts/console_contract_domain.py)`, so the
guard is executed **without editing any workflow**, and the wiring judge
(`tests/test_prism_console_ci_wiring.py`) stays green because it reads the same
derivation. No new workflow, no new allowlist entry.

## 8. Authorization boundary

Draft PR only. **No merge, no deploy, no acceptance claim.** PR #529 is updated in
place per the operating rule (one PR per lane, never a new PR per pulse). Nothing
here touches an authority surface: `api/`, `solspire/`, governance and identity code
are all unmodified; the change is two presentation files.

## 9. Remaining uncertainty

- The ring is verified **in the built stylesheet**, not in a browser. There is no
  browser observation in this pass; the CSS-cascade claim (that the ring wins over
  the `outline-none` utilities) is reasoned from Tailwind's `base`-layer ordering —
  utilities are generated after `@layer base`, so `outline-none` on a control still
  wins, which is why those controls keep their `focus:border-*` cue. Stated, not
  measured.
- `Shell.tsx:115` (global search) has no focus cue of its own; the shared ring now
  covers it. Whether it should also carry a `focus:border-*` is a separate, small
  design decision left to Lane 1 rather than widened into this slice.
### CI confirmation — measured, not asserted

Read from the run log, not from the job conclusion.

- **`console-contract` (run `38544636238`) — PASS.** Step log: `Verify the console contract
  guards` ✓ and `Console-contract CI-wiring guard` ✓. This is the runtime proof that the new
  guard is *executed*, not merely admitted to the derived domain (26 -> 27).
- Also green on head `83f049ca`: `backend`, `frontend`, `test`, `boot-syntax`,
  `production-read-only-probe`, `provider-forensics`, `bundle-beta-evidence`,
  `native-arkadia-golden-workflow`, `beta-beta-01-english`, `beta-beta-02-hausa`,
  `Full-history secret scan`.

Still in flight at the time of writing (not failures): the two Docker image builds
(`Build canonical Render image`, `Build and smoke-test the N-ATLAS self-host image`) and
`validate`. PR stays **draft**; the two Vercel commit statuses are the known pre-existing
failure on `main` itself and are not attributable to this branch.
