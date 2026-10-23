# ARK-VSR-2026-10-22 — final review record

**Mission:** visual-to-source reconciliation, VIS-001 / VIS-002 (VIS-003 recorded, not repaired).
**Base:** `main` `3cd81f76d0149a8a821a5152813ac50a68144b0e` — untouched.
**Candidate:** `26ee15eb625592292343724938c0c4fb2b2f3d6f`, tree `8d6e216d56307ea8c398b66eedbed8d5cf531221`.
**Branch:** `mission/ark-vsr-2026-10-22-clean`, 6 commits ahead of `origin/main`, 0 remote refs.
**Authorization:** investigate / reconcile / implement locally / verify. **No** merge, push,
deploy, production mutation, or acceptance. Nothing in this record authorizes a release.

## 1. What is fixed

| ID | Defect | Status | Change |
|---|---|---|---|
| VSR-001 | The mobile nav strip (`Shell.tsx`, `md:hidden`) never revealed its `aria-current="page"` item on a programmatic route change, so the strip could render with no visible current-page indicator. | **FIXED** | `revealActiveItem` (a `useCallback`) invoked from a route effect and a `ResizeObserver` on the strip; adjusts `scrollLeft` only. |
| VSR-001b | The first cut of that repair keyed on `[current]` alone and never re-ran on resize — 4/4 narrowings stranded the active item. | **FIXED** | Found by the guard's own negative control before review; the observer was added. |
| VSR-002 | The shared `Facts` `<dd>` value column could not wrap a long unbroken token (40-char SHA, `EVD-…`, stringified object). Latent: live values were short, so no live page overflowed. Trigger proven. | **FIXED** | `min-w-0 break-words` on the `<dd>`. |
| VIS-003 | Repeated scaffolded surfaces in SolSpire / Weaver. | **RECORDED, NOT REPAIRED** | Classified as drift; repairing it is a product decision, not a visual one. |

Scope is 6 files: `Shell.tsx` (+54/−1), `ui.tsx` (+13/−1), two new test files (+797), one evidence
doc, and `web/arkadia_console/.gitignore` (+3, see §5).

## 2. What passed

| Check | Result | Tree |
|---|---|---|
| New guards | **27 passed** (17 nav + 10 Facts) | `26ee15eb` |
| Guards vs. 10 broken variants | **10/10 caught**, each for its intended reason | `26ee15eb` |
| Full suite (`-rEf --continue-on-collection-errors`) | 8 failed, **3357 passed**, 17 skipped, 1 error | `120bbefe` |
| Failing/error node set vs. `main` | 9 nodes, sha256 `c280ddc6…`, **identical**, `comm -3` empty | `120bbefe` |
| Derived console-contract gate | **732 passed** (supersedes a stale 725) | `120bbefe` |
| Browser A/B, deep-link load | `main` **1/6** visible → candidate **6/6** | both built |
| Browser A/B, resize | `main` **0/4** → candidate **4/4** | both built |
| Observer growth while idle | 0 | candidate |
| `pnpm build` (`tsc --noEmit` + vite) | clean | `120bbefe` |
| Patch-series reproduction | tree `8d6e216d…` reproduced exactly; 27 passed | from base |

`main` and the candidate were built with the same toolchain and probed on identical viewports —
an A/B, not a before/after on one tree. The 8 pre-existing failures and 1 collection error are
unchanged and were **not** repaired.

## 3. What remains unverified

- **Cross-browser:** Chromium only. No Firefox, WebKit, or physical device.
- **Accessibility:** no screen-reader pass; no reduced-motion check (the scroll is instant and the
  comment says why, but that is reasoning, not a measurement).
- **Touch:** no real touch-scroll interaction.
- **CI enforcement:** the browser harnesses are **operator-run**. Measured: `grep -rln playwright
  tests/` → 0 files; CI's browser steps are ad-hoc Node scripts inside workflows. Wiring them in
  is a separate bounded change and is **not** claimed.
- **Production:** no deployment-identity observation was made. This is a repository-source claim.
  `/health` and `/api/version` were read-only probed (`200`); that is not acceptance.
- **VSR-002 in production:** the overflow was measured by substituting a value into the live
  element. Whether a real backend value long enough to trigger it is currently served is unknown.

## 4. Scope disclosure

`web/arkadia_console/.gitignore` (+3, `dist-verify/`) is **not required by either defect**. It
exists because a local verification build used a second output directory. It is defensible (a
stray build dir must not be tracked) but it is a change beyond the two defects, and it is
disclosed here rather than folded silently into the repair.

One defect was found **while reading the diff for this review**: the nav guard's docstring said
"Three properties" and then listed four. Corrected in `26ee15eb`. Comment-only; cannot affect
collection or outcomes, but it is the kind of thing a reviewer should not have to find.

## 5. Delta since the last full-suite run

`120bbefe` → `26ee15eb` changes **one docstring line** in a test file
(`git diff --name-only 120bbefe..26ee15eb` → the guard file and the evidence doc only). The
full-suite row in §2 therefore still applies; the 27 guards were re-run at `26ee15eb` and pass.

## 6. Handoff — the decision

**Ready for the human decision.** No material blocker was found in the diff inspection. The
candidate is a bounded, verified repair of two defects with guards that were themselves falsified,
and the boundaries of what was *not* verified are stated above rather than implied away.

**Not ready for production release**, and not claimed to be: no deployment-identity observation,
Chromium-only, operator-run harnesses, and no merge authorization.

Next authorized action: a human decision on `mission/ark-vsr-2026-10-22-clean`
(`26ee15eb`, tree `8d6e216d`). Forbidden without new authorization: push, merge, deploy, or
treating this record as acceptance.
