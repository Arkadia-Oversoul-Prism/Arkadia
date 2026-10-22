# ARK-VSR-2026-10-22 — Visual-to-Source Reconciliation, UI Quality, Verified Refinement

**Mission ID:** ARK-VSR-2026-10-22
**Repository:** `Arkadia-Oversoul-Prism/Arkadia`
**Canonical production origin:** `https://arkadia-qzu4.onrender.com` (ADR-016)
**Authorization:** investigate / reconcile / implement locally / verify. **No** merge, push,
deploy, production mutation, or acceptance.
**Status:** bounded implementation complete and verified; 3 defects repaired (2 in product source,
1 in this mission's own first cut), 1 drift class and 1 routing gap reported; merge/deploy/
acceptance **NOT CLAIMED**.

---

## 0. Revision note — a second defect in this branch, found while preparing review

A verification pass carried out **to enable** human review found a real defect in the branch
itself, so the branch was re-cut. Read this before reviewing any SHA.

Commit `3f38c942` accidentally **tracked a build artifact** —
`web/arkadia_console/dist-verify/` (7 files, ~1,600 lines of minified JS). A later commit removed
it, so the **net** diff was always clean and every test result in this document is unaffected.
But the intermediate commit is permanent history, and a patch series that adds then deletes a
1.5k-line artifact is not something that should be merged.

The artifact was inspected before any decision was made: `firebase-config.js` is the documented
**inert** default (`window.__ARKADIA_FIREBASE_CONFIG__ = window.__ARKADIA_FIREBASE_CONFIG__ || {}`)
and the only embedded absolute URL is the public canonical origin
`https://arkadia-qzu4.onrender.com`. **No credential, token, or private value is present**, and a
regex scan of the candidate diff for credential shapes returned nothing.

| | SHA | tree |
|---|---|---|
| Base (`main`) | `3cd81f76d0149a8a821a5152813ac50a68144b0e` | — |
| **Candidate (review this)** | `mission/ark-vsr-2026-10-22-clean` @ `9dd305f6` | `ddf21933` |
| Superseded, kept for audit | `mission/ark-vsr-2026-10-22` @ `48da2897` | `ddf21933` |

The clean branch re-applies the same five commits with the artifact stripped, so **no commit in it
carries the artifact** while the final tree is **byte-identical**. Nothing was rewritten or
force-pushed; the original is preserved as `-original`.

Verified: sequential `git am` of the five patches onto the base reproduces tree `ddf21933` exactly,
and the 20 guards pass on the reproduced tree.

**A local review bundle is at `/tmp/vsr-bundle/`** (`README.md`, `full.diff`, `commits/*.patch`,
test logs, node sets, measurement harnesses + captured JSON). It exists because the earlier review
could not inspect a branch that had never been pushed — the reviewer's request for local artifacts
is what surfaced the artifact defect above.

### One measurement caveat, recorded rather than smoothed over

A candidate suite run reported a **10th** failing node,
`tests/test_weaver_mvp2_exec_binding.py::test_eb_valid_reaches_k15_seam`, absent from every
baseline run. It was traced, not dismissed. Its fixture calls `current_head(repo_root)` — it reads
**live git HEAD** — and the assertion message is `HEAD drift: patch base ...`. `git checkout` and
`cherry-pick` were running in the same working tree **while the suite executed**, so the fixture's
captured `base_head_sha` went stale mid-run.

Re-run with no concurrent git activity: **8 failed / 3350 passed / 17 skipped / 1 error**, with the
failing/error node set **byte-identical to baseline** (`sha256 c280ddc6…`, 9 nodes, `comm -3`
empty). The node is a harness race, not a product defect — this diff contains no Python. It is the
same cross-test-contamination class already recorded for
`test_engineering_lab_agent_loop_does_not_mutate_repository`.

**Do not run the full suite in the same working tree you are checking out branches in.** The
fixture will capture a HEAD that moves underneath it.

---

## 1. Exact baseline (re-measured, not inherited)

The mission brief carried a prior "main" revision of `3cd81f76…`. Re-measured: it **is** still
current, so the brief's lead held — recorded as a confirmation, not an assumption.

| Item | Measured value | How |
|---|---|---|
| Branch / HEAD | `main` @ `3cd81f76d0149a8a821a5152813ac50a68144b0e` | `git rev-parse HEAD` |
| `origin/main` | `3cd81f76d0149a8a821a5152813ac50a68144b0e` | `git rev-parse origin/main` |
| Worktree at start | **clean** (`git status --porcelain` empty) | `git status` |
| Clone | full, **not** shallow | `git rev-parse --is-shallow-repository` → `false` |
| HEAD commit | `Merge pull request #557 from …/ci/provider-routing-artifact-evidence-01` | `git log -1` |
| Frontend manager | pnpm 10.26.1 (declared in `package.json`), node 24 | `web/arkadia_console/package.json` |
| Python deps | absent at start; `pip install -r requirements.txt` succeeded | `pip` exit 0 |

### Live runtime vs repository

| Probe | Result |
|---|---|
| `GET /health` | `200` `{"status":"radiant","path":"/health"}` in 0.35s |
| `GET /api/version` | `200`; `source_revision` = **`3cd81f76d0149a8a821a5152813ac50a68144b0e`**, `revision_source` = `RENDER_GIT_COMMIT`, `revision_conflict` = **`false`** |

**Production is running exactly current `main`.** Source↔runtime revision consistency is
VERIFIED. Per the endpoint's own `verification_note`, this is necessary but not sufficient
evidence of correct behaviour, and is not deployment acceptance — production **acceptance** is
**NOT CLAIMED**.

### Two frontends, one origin — resolved

The brief asks whether the primary application and the operator console are intentionally
served together. They are, and it is deliberate:

- `Dockerfile` builds **both**: `web/arkadia_console` (primary) and `web/console` (operator).
- `api/frontend_routes.py::configure_frontends` mounts the operator console under `/operator`,
  `/n-atlas-lab`, `/n-atlas-tester`; the primary console takes `/assets` and the SPA catch-all.
- The retired Prism UI is archived (`archive/frontend/arkadia-prism`) and is **not** built.
  The archive is not the active product; neither is the operator console the primary app.

`/solspire` is a **reserved backend prefix** (`api/frontend_routes.py::_RESERVED_PREFIXES`), so
a UI route cannot live there. This matters for the reported inventory — see §3.

---

## 2. Reported route inventory vs. source — the brief's paths are stale

Three of the nine reported routes do **not** exist as written. The source is authoritative.

| IMG | Reported path | Actual path | Status | Evidence |
|---|---|---|---|---|
| IMG-01 | `/` | `/` | ✅ matches | `surfaces.ts` `home` |
| IMG-02 | `/novanet` | `/novanet` | ✅ matches | `surfaces.ts` `novanet` |
| IMG-03 | `/arkana` | `/arkana` | ✅ matches | `surfaces.ts` `arkana` |
| IMG-04 | `/solariun` | `/solariun` | ✅ matches | `surfaces.ts` `solariun` |
| IMG-05 | `/engineering` | **`/engineering-lab`** | ❌ **stale** | `surfaces.ts:79` |
| IMG-06 | `/solspire` | **`/enterprise`** | ❌ **stale** | `surfaces.ts:92` |
| IMG-07 | `/knowledge` | `/knowledge` | ✅ matches | `surfaces.ts` `knowledge` |
| IMG-08 | `/weaver` | `/weaver` | ✅ matches | `surfaces.ts` `weaver` |
| IMG-09 | `/about` | `/about` | ✅ matches | `surfaces.ts` `about` |

`surfaces.ts` documents *why* `/solspire` is not the surface path: `/solspire` is a reserved
backend API namespace, so "the SPA cannot be served on that path — a hard load would fall
through to the API and 404." `/engineering-lab` is the declared name of the Lab surface.

Both stale paths are handled deliberately rather than silently broken:

- **`/solspire`** → `_RESERVED_PREFIXES` returns `404 Route not found` from the SPA catch-all.
  Measured live: `/solspire/projects` is a real **auth-gated API** (`401`), so a user typing
  `/solspire` lands on the API, not the UI.
- **`/engineering`** → not in `PATH_ALIASES`, so `resolvePath` falls through to **`home`**.
  The console renders Home, and the load-time `replaceState` rewrites the address bar to `/`.
  **This is a silent mis-route, not a 404.** It is a candidate finding (see §7, VSR-004).

Legacy aliases that *are* reconciled (`router.ts::PATH_ALIASES`): `/nexus`→novanet,
`/oracle`→arkana, `/commune`→arkana, `/home`→home, `/knowledge-os`→knowledge, `/gate`→login,
`/living-gate`→login. Alias resolution carries a single remainder segment as a section, so
`/nexus/ims` reaches NovaNet rather than being discarded to Home.

### Route-to-source matrix

Confidence: **High** = read from source and verified in a browser. All nine routes were loaded
in Chromium; each returned the expected `<h1>` with **zero JS page errors**.

| Surface | Path | Page component | Lenses | Endpoints | Auth | Verified |
|---|---|---|---|---|---|---|
| Home | `/` | `pages/HomePage.tsx` | — | `/api/version` | public | ✅ `h1` "ARKADIA" |
| NovaNet | `/novanet` | `pages/NovaNetPage.tsx` | 4 (field/echoes/…) | `/api/transmissions`, `/api/echoes` | public | ✅ |
| Arkana | `/arkana` | `pages/ArkanaPage.tsx` | — | `/api/commune/*` | public shell | ✅ |
| Solariun | `/solariun` | `pages/SolariunPage.tsx` | 4 (projects/knowledge/memory/weaver) | `/solspire/projects` | **required** | ✅ threshold |
| Engineering Lab | `/engineering-lab` | `pages/EngineeringLabPage.tsx` | — | `/api/lab/engineering/*` | **required** | ✅ threshold |
| SolSpire | `/enterprise` | `pages/SolSpirePage.tsx` | — | `/solspire/projects` | **required** | ✅ threshold |
| Knowledge OS | `/knowledge` | `pages/KnowledgePage.tsx` | — | `/api/knowledge/*` | **required** | ✅ threshold |
| Weaver | `/weaver` | `pages/WeaverPage.tsx` | — | `/api/approvals` | **required** | ✅ threshold |
| About | `/about` | `pages/AboutPage.tsx` | — | — | public | ✅ `h1` "About Arkadia" |

Anonymous probes confirm the auth boundary is real, not cosmetic:

```
/api/version                    200      /api/me                       401
/api/transmissions              200      /api/commune/threads          401
/api/echoes                     200      /api/lab/engineering/overview 401
/api/knowledge/status           200      /api/approvals                401
                                         /solspire/projects            401
```

Public reads are public; protected reads return `401` rather than empty data — so a broken or
unauthenticated API is **distinguishable** from an empty result, as `ContractState` intends.

---

## 3. Design-system forensics — reported palette vs. actual tokens

The brief's palette was explicitly "estimates, not verified design tokens". Measured against
the real source **and** the computed styles of the live production page:

| Brief (estimated) | Actual source token | Computed on production | Match |
|---|---|---|---|
| Canvas `#0b0b12` | `ink: #080A11` (`tailwind.config.js:9`) | `rgb(8,10,17)` | ❌ different |
| Card `#13131f` | `panel: #0E1120` | `rgba(14,17,32,0.7)` (`bg-panel/70`) | ❌ different |
| Gold `#d4af37` | `gold: #C9A84C` | `rgb(201,168,76)` | ❌ different |
| Main text `#e0e0e6` | `#e8e8e8` (`index.css` body) | `rgb(232,232,232)` | ❌ different |
| Teal `#4df8c1` | `emerald: #00D4AA` | (accent per surface) | ❌ different |
| Border `#22223b` | `line: #1B2033` | `rgb(27,32,51)` | ❌ different |

**All six estimates were wrong.** This is expected — they were reconstructed from screenshots —
and it is the reason the mission says not to create tokens from estimates. **No token was
changed.** The real palette is a coherent seven-token system, and it is enforced:
`test_console_shell_nav_contract.py::test_design_tokens_are_not_bypassed_by_page_local_hex_literals`
asserts no page-local hex literal exists in any `.tsx`.

Two further measured tokens the brief did not report:

| Property | Source | Computed |
|---|---|---|
| Title face | `display: ["Cinzel","serif"]` | `Cinzel, serif` |
| Title colour/size/tracking | `font-display text-3xl tracking-[0.16em] text-gold` | `rgb(201,168,76)`, `30px`, `4.8px` |
| Mono face | `mono: ["IBM Plex Mono", …]` | `"IBM Plex Mono", ui-monospace, monospace` |
| Card radius / border | `rounded-xl border-line` | `12px` / `rgb(27,32,51)` |
| Body face | `Inter, "DM Sans", system-ui` | matches |

Fonts are loaded from Google Fonts in `index.html` with `Cinzel:wght@500;600`,
`Inter:wght@300..600`, `IBM+Plex+Mono:wght@400;500`. The visual language is shared **because it
is a shared design system** (one Tailwind palette + one `index.css`), not because components
happen to look alike. Contrast was measured rather than eyeballed: nav active `8.49:1`,
inactive `4.51:1` against the composited strip background — both pass WCAG AA.

---

## 4. VIS-001 — mobile navigation — **CONFIRMED DEFECT, REPAIRED**

**Claim:** nav items "become clipped or crowded on narrow mobile viewports."

**Verified, with a correction to the claim.** The strip is *intentionally* a single
horizontally-scrolling row (`flex gap-1 overflow-x-auto … md:hidden`), and this is deliberate:
`Shell.tsx` carries the comment "the same surfaces, no second global nav bar", and
`test_console_shell_nav_contract.py` enforces one navigation model. So the overflow is **by
design** — and document-level overflow is **0px** at 320/390/414px, meaning the page itself
never scrolls sideways. The brief's "clipped" reading is the intended affordance.

**But a real defect sits behind it.** Measured in Chromium at 390×844:

```
nav scrollWidth 799   clientWidth 390   overflow 409px   9 items
  HOME              x=   8 ..  65   ✓ visible
  NOVANET           x=  69 .. 152   ✓
  ARKANA            x= 156 .. 230   ✓
  SOLARIUN          x= 234 .. 325   ✓
  ENGINEERING LAB   x= 329 .. 445   ✗ past right edge
  SOLSPIRE          x= 449 .. 540   ✗
  KNOWLEDGE OS      x= 544 .. 643   ✗
  WEAVER            x= 647 .. 721   ✗
  ABOUT             x= 725 .. 791   ✗
```

Five of nine items sit past the right edge. The strip marks the current surface with
`aria-current="page"` plus the surface accent, and **keyboard focus reveals an item natively**
(measured: tabbing to `nav-solspire` scrolled the strip to 299, to `nav-about` to 409). What
never happened was a reveal on a **programmatic route change**:

| Route | scrollLeft | active item | fully visible |
|---|---|---|---|
| `/` | 0 | Home | ✅ |
| `/about` | 0 | About (x=725..791 in a 0..390 box) | ❌ |
| `/weaver` | 0 | Weaver (x=647..721) | ❌ |
| `/knowledge` | 0 | Knowledge OS (x=544..643) | ❌ |

So a user arriving at `/about` by deep link, portal click, or back/forward saw a navigation
strip with **no visible current-page indicator at all**. `grep` confirms no
`scrollIntoView`/`scrollLeft`/`activeElement` logic existed anywhere in the console source, and
**no test in `tests/` named the strip's `aria-label`** — the mobile navigation was an unpinned
surface.

**Reproduced on the canonical deployment** at revision `3cd81f76`: identical
`scrollWidth 799 / clientWidth 390 / scrollLeft 0`, `About` at x=725..791, `fullyVisible false`.
This is a product defect, not a local build artifact.

**Repair** (`ded3b7ab`, `Shell.tsx`, 1 file): keep the single scrolling strip — no hamburger,
no second nav model, no new breakpoint — and adjust only `scrollLeft` in an effect keyed on
`[current]`. `scrollIntoView` is deliberately **not** used because it would also scroll the page
vertically, which the shell already owns via its content-landmark focus. A layout-box guard
(`clientWidth === 0`) keeps the effect inert on desktop, where `md:hidden` leaves the strip with
zeroed rects.

**Verified after repair** — active item fully visible on every route at 320/390/414px, Home
still at `scrollLeft 0`, desktop unchanged:

```
w390  /about      scrollLeft 409  active x=316..382  fullyVisible ✓
      /weaver     scrollLeft 339  active x=308..382  ✓
      /knowledge  scrollLeft 261  active x=283..382  ✓
      /enterprise scrollLeft 158  active x=291..382  ✓
desktop (1280) mobile clientWidth 0 → effect inert; desktop nav visible ✓
```

One observation explicitly **not** attributed to this change: `/` and `/about` settle at
`window.scrollY = 66` on mobile. Measured on the **unfixed production** build at the same
viewport and it is **also 66** — pre-existing, from the content-landmark focus scrolling the
tall Home page. Not caused by, and not repaired by, this work.

### VSR-001b — a second defect in the first cut of my own repair

An adversarial stress pass over the repair (not over the original product) found that the first
cut was **incomplete**. It keyed the reveal on `[current]` alone, so it fixed the reported defect
and left a narrower one: a route change is not the only event that can hide the active item.
Narrowing the viewport grows the strip's scrollable range without moving `scrollLeft`, stranding
the active item past the right edge again.

Measured against that first cut in Chromium — **4/4 narrowings failed**:

| Resize | active item right edge | strip right edge | fully visible |
|---|---|---|---|
| 700 → 400 | 692 | 400 | ❌ |
| 600 → 360 | 592 | 360 | ❌ |
| 390 → 320 | 382 | 320 | ❌ |
| 767 → 300 | 759 | 300 | ❌ |

**Repair** (`07c93d6c`): the reveal becomes a `useCallback` invoked from both the route effect and
a `ResizeObserver` on the strip. Observing the strip rather than `window.resize` covers the case
without introducing a second breakpoint constant that could drift from Tailwind's `md:`.

All four narrowings now report `fullyVisible: true`. Two risks were ruled out by measurement
rather than assumed:

- **ResizeObserver feedback loop** — the observer fires **once**, attribute-mutation growth while
  idle is **0**, and `scrollLeft` is stable across 8 samples (409 every time). A loop would show
  as unbounded growth in one of those counters.
- **Desktop inertness** — at 1280px the strip's `clientWidth` is `0` (`md:hidden`), so the reveal
  returns early and never computes an offset from zeroed rects.

A **font-swap race** was also tested and **not reproduced**: sampling from `waitUntil: 'commit'`
onward, the first measurable sample was already correct (`scrollLeft 411`, then settling to 409),
so the reveal is not racing webfont metrics.

This is recorded because the first cut was committed as a fix and would have shipped a partial
one. The lesson is that "the reported symptom is gone" and "the defect class is closed" are
different claims, and only the second is worth asserting.

---

## 5. VIS-002 — Engineering Lab density — **CONFIRMED LATENT DEFECT, REPAIRED**

**Claim:** dense technical data and raw JSON blocks on mobile.

**Partially confirmed, with the mechanism identified.** The Lab is *deliberately* dense, and
that is defensible: it is an operator surface whose copy says it reports "the deployment's
effective configuration, not repository defaults", and `NotYetWired` exists precisely so a
scaffold states what is missing instead of rendering mock data. The engineering intent is
honest disclosure, not decorative dashboards.

The real defect is not density but **overflow**. `scalarOverview`
(`components/lab/labOperational.ts:232`) emits `JSON.stringify(value)` for an object-valued
overview key straight into the shared `Facts` primitive. That `<dd>` sat in a
`grid-cols-[minmax(0,10rem)_1fr]` grid with **no `min-w-0` and no `break-words`**. The label
track is capped, but a bare `1fr` track still refuses to shrink below its content's intrinsic
minimum width, so a long unbroken token overflows the whole document.

Measured in Chromium 390×844 against the canonical deployment, on the live element:

```
A  pre-repair classes              document overflow  405px
B  + min-w-0 break-words           document overflow    0px
C  short value (40-char SHA)       document overflow    0px   (unaffected)
```

A controlled A/B on the *same live element*, changing only the two classes.

**Recorded precisely as LATENT:** the values rendered at measurement time were short
(`arkadia`, `one_reconciled_deployment`, the revision SHA), so **no live page overflowed**. It
is reachable because the value is backend-controlled — a long objective, session id, or
`EVD-…` id needs no frontend change to appear. `Facts` has **20** consumers, so the defect was
shared by every surface.

**Repair** (`3f38c942`, `components/ui.tsx`, 1 file): `min-w-0 break-words` on the `dd`. The
`minmax(0,10rem)` label cap is unchanged, so no existing reading is re-laid-out.

### The `display: contents` question, settled by measurement

The `dd` is not a direct grid child: it sits inside `<div className="contents">`, which makes the
`div` generate no box, so the `dt`/`dd` participate in the *grandparent* grid. That makes "does
`min-w-0` on the `dd` actually work?" a real question rather than an assumption, so it was tested
against the **exact** DOM structure and the production stylesheet, at 390px:

| | strip overflow | `dd` width | `dt` (label) width |
|---|---|---|---|
| pre-repair | **414px** | 772 | **0** |
| repaired | **0px** | 198 | 160 |

The fix is confirmed effective through the `contents` wrapper. It also exposed a symptom the
original measurement had not shown: pre-repair the value column squeezed the **label to zero
width** — the label was being pushed out of the layout entirely, not merely the value overflowing.
The repair restores it (160px, the `minmax(0,10rem)` cap).

---

## 6. VIS-003 — scaffolded surfaces — **CONFIRMED DRIFT (recorded, deliberately not repaired)**

**Claim:** multiple placeholder panels in SolSpire and Weaver describing interfaces not yet
implemented.

**Confirmed — and the panels understate what exists.** All `NotYetWired` contract strings were
enumerated from source and checked against the **deployed** `GET /openapi.json` (288 paths):

| Advertised contract | In deployed schema | Reality |
|---|---|---|
| `/api/solspire/workloads` | ❌ **absent** | real path `/solspire/workloads` — `GET,POST` |
| `/api/solspire/proposals` | ❌ **absent** | real path `/solspire/proposals` — `GET,POST` |
| `/api/solspire/pulses` | ❌ **absent** | real path `/solspire/pulses` — `GET,POST` |
| `/api/solspire/voice` | ❌ **absent** | real path `/solspire/voice/status` — `GET` |
| `/api/lab/engineering/sessions/{id}/execute` | ✅ **present** | real path uses `{session_id}` — `POST` |

The four SolSpire panels advertise `/api/solspire/*`, which **404s**; the real contracts are
`/solspire/*` and they are **fully implemented**. Live probes:

```
/solspire/workloads     401   (exists, auth-gated)
/solspire/proposals     401   (exists, auth-gated)
/solspire/pulses/today  401   (exists, auth-gated)
/solspire/voice/status  401   (exists, auth-gated)
/api/solspire/workloads 404   (does not exist — the advertised path)
```

Source confirms the handlers are mounted: `solspire/console_router.py` declares
`prefix="/solspire"` and `include_router`s the workload, pulse, proposal, and voice routers.

So the classification for these four is **"implemented but not wired to the UI"**, *not*
"not yet implemented" — and the panel's advertised contract string is wrong. This is exactly
the distinction the mission asked for, and the current copy conflates them.

**Why this was not repaired.** It is already **recorded** as bounded debt in
`tests/test_console_endpoint_registry_contract.py::RECORDED_ADVERTISED_DRIFT`, which states the
reason explicitly: these strings "live in feature pages owned by other workstreams, so this
file records them as a bounded finding … rather than editing those pages."
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §1 confirms `SolSpirePage.tsx` belongs to
Workstream 2, not to shell/integration. Repairing it here would breach an explicit ownership
boundary — the mission's "do not expand scope" rule. It is reported, with the corrected
contracts, as a bounded follow-on for the owning workstream.

The fifth row is a **near-miss, not a defect**: `{id}` vs `{session_id}` is a parameter-name
difference the recorded-drift detector deliberately normalises, and the route genuinely exists.
The Weaver/Engineering Lab panel therefore advertises a real contract.

---

## 7. Defect register

| ID | Defect | Class | Status | Evidence |
|---|---|---|---|---|
| **VSR-001** | Mobile nav never reveals the active item on a programmatic route change | product defect | **REPAIRED** `ded3b7ab` | Chromium A/B + production reproduction |
| **VSR-001b** | The first cut of that repair ignored viewport resize — 4/4 narrowings stranded the active item again | defect in the repair | **REPAIRED** `07c93d6c` | Chromium resize matrix + loop check |
| **VSR-002** | Shared `Facts` value column cannot wrap a long token → up to 405px document overflow, and the label column collapsed to 0px | latent defect | **REPAIRED** `3f38c942` | Chromium A/B on live element + exact-DOM harness |
| **VSR-003** | Four SolSpire scaffolds advertise `/api/solspire/*` (404); real contracts are `/solspire/*` and are implemented | recorded drift | **REPORTED** — owned by Workstream 2 | deployed `/openapi.json` + live 401/404 probes |
| **VSR-004** | `/engineering` silently resolves to Home and rewrites the address bar | routing gap | **REPORTED** — needs a product decision | `router.ts::resolvePath` fallthrough |
| **VSR-005** | `/solspire` as a UI route returns API `404 Route not found` | by design | **NOT A DEFECT** | `_RESERVED_PREFIXES` |
| **VSR-006** | Reported palette (6 values) does not match the real tokens | report inaccuracy | **NOT A DEFECT** — no change made | `tailwind.config.js` + computed styles |
| **VSR-007** | Mobile nav items "clipped" | report inaccuracy | **NOT A DEFECT** — intentional scroll affordance | document overflow 0px |
| **VSR-008** | `window.scrollY = 66` on mobile `/` and `/about` | pre-existing | **NOT ATTRIBUTED** — present on unfixed production | production A/B |
| **VSR-009** | Font-swap race could reveal before webfont metrics settle | hypothesised | **NOT REPRODUCED** | sampled from `waitUntil: 'commit'`; correct at first measurable sample |

**VSR-004 detail.** `/engineering` is absent from `PATH_ALIASES`, so `resolvePath` returns
`{surface:"home", path:"/"}` and the load-time `replaceState` rewrites the bar to `/`. The user
asks for the Lab and silently gets Home. The fix is one alias entry — but `/engineering` vs
`/engineering-lab` is a **naming/product decision** (the same class the router's own comments
decline to make for `/codex`), and a wrong alias would create a duplicate route, which
`test_console_shell_nav_contract.py::test_detector_flags_an_alias_that_shadows_a_canonical_path`
forbids. Left as a decision, not taken unilaterally.

---

## 8. Verification and regression evidence

### Guard tests added (both with a negative control per failure mode)

| File | Tests | Purpose |
|---|---|---|
| `tests/test_console_mobile_nav_active_reveal.py` | 12 | VSR-001 / VSR-001b |
| `tests/test_console_facts_value_overflow_contract.py` | 8 | VSR-002 |

**Each guard was proven to bite by reverting the source fix and re-running:**

```
VSR-001   pre-repair Shell.tsx (main)   → 11 failed,  1 passed
          first-cut route-only Shell    →  6 failed,  6 passed
          repaired Shell.tsx            → 12 passed

VSR-002   pre-repair ui.tsx             →  4 failed,  4 passed
          repaired ui.tsx               →  8 passed
```

The three-state row for VSR-001 is the important one. The middle state is **my own first cut**:
it satisfies the ref, marker, horizontal-only, and layout-box assertions and still leaves the
active item off-screen on a resize. Without the negative control that reconstructs that shape,
the regression would have shipped with a green guard.

A guard that cannot fail on the defect it claims to detect is not a guard; this is measured,
not asserted.

### Full-suite comparison (same environment, `-rEf --continue-on-collection-errors`)

| Tree | Result |
|---|---|
| `main` `3cd81f76` (isolated worktree) | **8 failed, 3330 passed, 17 skipped, 1 error** |
| branch `07c93d6c` | **8 failed, 3350 passed, 17 skipped, 1 error** |

```
failing/error node sets, sorted:
  main   : 9 nodes   sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b
  branch : 9 nodes   sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b
  comm -3 → empty
```

**Zero regression, attributed by node identity, not by count.** The `+20 passed` is exactly the
two new guard files' 20 nodes. The 8 pre-existing failures and 1 collection error are unchanged
and were **not** repaired — they are unrelated debt (`test_solspire_r1_governance_convergence`,
`test_solspire_r3_execution_runtime`, `test_identity_spine_w1`, `test_m02_reasomate_truth`,
others).

The baseline was **re-derived** after an environment restart wiped `/tmp`, rather than reused
from the earlier run; both derivations agreed exactly, which is itself worth noting because a
baseline that only exists in one's notes is not a baseline.

### Other checks

- `cd web/arkadia_console && pnpm build` → **clean** (`tsc --noEmit` + vite, 1.7s).
- The repository's own derived console-contract gate, run exactly as CI runs it
  (`python -m pytest -q $(python scripts/console_contract_domain.py)`) → **725 passed**. Both new
  guard files enter that derived domain automatically (the workflow derives its inventory and
  filters on `tests/**`), so no workflow edit was needed — verified, not assumed.
- `tests/test_prism_console_ci_wiring.py` + `tests/test_m02a_ci_gate_integrity.py` → **98 passed**.
- CP10 mutation boundary admits all five changed paths (`--judge` → admitted each).
- Focused console contract set (12 files) → **146 passed**.
- All nine routes loaded in Chromium → expected `<h1>`, **zero JS page errors**.
- `/health` and `/api/version` read-only probes → `200`.

---

## 9. Limitations and what was NOT verified

Stated explicitly, because an unverified claim is not evidence:

- **No authenticated session was used.** Solariun, Engineering Lab, SolSpire, Knowledge OS, and
  Weaver were verified only as far as the **auth threshold** (correctly rendered) and their
  source. The authenticated content of those five surfaces is **NOT OBSERVED**. Their endpoint
  contracts were verified from the deployed `/openapi.json` and anonymous `401`s, not by
  rendering authed data.
- **Visual inspection was programmatic, not human.** Measurements come from Chromium via
  Playwright (DOM geometry, computed styles, screenshots). No screenshot was interpreted by a
  human or vision model in this pass, so no claim rests on visual judgement.
- **The reported screenshots were not available.** The nine-image inventory is treated strictly
  as reported observation. Where it conflicts with source, source wins — which is how VSR-006
  and VSR-007 were classified.
- **`/engineering` mis-route is source-derived, not browser-confirmed end-to-end.** The
  `resolvePath` fallthrough and `replaceState` rewrite were read from source; the address-bar
  rewrite on a direct load was not separately captured.
- **VSR-002's trigger is synthetic.** The 405px figure comes from substituting a 164-char token
  into the live element. No live page was observed overflowing. Recorded as latent, not as an
  observed production overflow. The exact-DOM harness that produced the 414px figure (§5) is a
  reconstruction of the component's structure, not the component itself — it uses the production
  stylesheet and the production class strings, but it is a harness.
- **VSR-001b was measured against the repaired branch, not against production.** Production still
  runs the unfixed `3cd81f76`, so the resize behaviour there is the *original* defect (no reveal at
  all), not this one. VSR-001b is a defect that existed only inside this mission's own first cut.
- **The `ResizeObserver` loop check is a measurement, not a proof.** Zero growth across a 2.5s
  idle window and a stable `scrollLeft` across 8 samples is strong evidence against a feedback
  loop; it does not exhaustively prove one cannot occur under a different layout.
- **Render build logs and metrics were not inspected** (no provider access). No runtime
  explanation is offered for anything beyond the HTTP responses recorded in §1.
- **No keep-alive or polling was performed.** Endpoint reads were limited to the probes recorded
  in §1 and §2.
- **`test_solspire_r1_governance_convergence` and `test_solspire_r3_execution_runtime` failures
  are pre-existing and unowned by this mission.** They were not investigated or repaired.

---

## 10. Boundary compliance

| Constraint | Status |
|---|---|
| No merge, push, or remote branch | ✅ all work on local branch `mission/ark-vsr-2026-10-22` |
| No commit to `main` | ✅ `main` untouched at `3cd81f76` |
| No deploy / Render config / env / secrets | ✅ read-only probes only |
| No production mutation | ✅ |
| Work isolated from `main` | ✅ local branch from a clean tree |
| No destructive git, no user work discarded | ✅ worktree added separately; no reset/clean |
| No secret printed | ✅ only status codes and non-sensitive payload fields recorded |
| No access control weakened | ✅ auth thresholds untouched |
| No second design system / component fork | ✅ repaired the one shared primitive |
| File ownership respected | ✅ `SHARED-CONTRACTS.md` §1 — `Shell.tsx` and `ui.tsx` are shell/shared primitives (Workstream 1); the Workstream-2 page drift was reported, not edited |
| Production acceptance | **NOT CLAIMED** |

---

## 11. Handoff — one next authorized action

**State:** three verified repairs on `mission/ark-vsr-2026-10-22` (`ded3b7ab`, `3f38c942`,
`07c93d6c`), each with a guard proven to fail on the defect it detects; zero regression by node
identity; production confirmed at `3cd81f76`; working tree clean.

**Evidence:** this file. Measurements are reproducible with Playwright + system Chromium against
`https://arkadia-qzu4.onrender.com` and the local preview build.

**Blockers:** none for review. VSR-003 is blocked on Workstream 2 ownership; VSR-004 on a
naming decision.

**Authorized action (one):** a human reviews this package and decides whether to merge
`mission/ark-vsr-2026-10-22`. Merging to `main` **is** a production release here (Render
auto-deploys), so it is explicitly outside agent authority.

**Forbidden actions:** agent merge, push, deploy, or production-acceptance claim; repairing
VSR-003 inside this branch (ownership); adding an `/engineering` alias without a product
decision.

**Completion condition:** the human either merges all three commits, or rejects them with
reasons — and VSR-003/VSR-004 are routed to their owning workstreams.

### Changeset

```
docs/control-plane/evidence/ark-vsr-2026-10-22/EVIDENCE.md   (this file)
tests/test_console_facts_value_overflow_contract.py          8 tests
tests/test_console_mobile_nav_active_reveal.py              12 tests
web/arkadia_console/.gitignore                              ignore dist-verify/
web/arkadia_console/src/components/Shell.tsx                VSR-001 / VSR-001b
web/arkadia_console/src/components/ui.tsx                   VSR-002
```

Two source files, two guard files, one evidence record, one gitignore line. No dependency
changes, no refactors, no formatting churn, no build output tracked.
