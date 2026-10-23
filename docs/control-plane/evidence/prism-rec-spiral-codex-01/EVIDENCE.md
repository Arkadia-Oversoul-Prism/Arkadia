# PRISM-REC-SPIRAL-CODEX-01 — surface the shared public corpus

**Build ID:** `prism-rec-spiral-codex-01`
**Parent build:** `prism-rec-voice-readaloud-01` (PR #559, commit `0b0e0cd3`, still OPEN)
**Base SHA:** `68403b9ea8e2ba16ade0d1b08418453a79b9dcb7` (`origin/main`, 0 ahead / 0 behind)
**Branch:** `feat/prism-rec-spiral-codex-01` — branched from `main`, **not stacked on #559** (§4.1)
**Classification:** `UNSURFACED` → `CONNECTED` (read-only journey)
**Authority:** Human retains merge, production-deployment, and acceptance authority.
No merge, deployment, or acceptance is claimed by this document.

---

## 1. What was asked, and what the evidence said

The mandate directed the next slice to **NovaNet ownership reconciliation**. Recon
falsified the premise and redirected the slice. Both findings are recorded because
the second only exists because the first was measured.

### 1.1 The mandate's premise was stale

| Claim | Measurement |
|---|---|
| "PR #492 … is building" a NovaNet surface | `pulls/492` → `merged: true`, merge commit `7030ccb2` |
| NovaNet needs building | `pages/NovaNetPage.tsx` + `components/novaNet/*` already read `/api/transmissions` and `/api/echoes` through the registry |
| A competing surface may be forming | `grep -iE 'novanet\|transmission\|social'` over all **19** open PRs' file lists → **0 matches** |

NovaNet is `CONNECTED`. Building there would have created the competing surface the
ownership rule exists to prevent. Re-derived rather than trusted.

### 1.2 The gap that replaced it

`GET /api/codex` on the canonical deployment: **200, no identity required**, serving
**661 documents / 4,413,059 characters** (5,128,422 bytes). The archived Prism built
**two whole routes** on it — `/encyclopedia` (`NexusSpiralCodex`, `initialMode="scrolls"`)
and `/spiral-codex` (`SpiralCodexFeed`) — plus `SpiralVault`, `ShereSanctuary`,
`PersonalCodex`, and `dashboardApi.codex()`.

The console referenced it **nowhere** (`grep -rn 'endpoints.codex\|/api/codex' src/` → 0
substantive). The registry's `codex` key is `/api/me/codex` — the **personal** corpus, a
different contract. The public corpus had no registry entry at all.

---

## 2. The endpoint inventory instrument

The assessment asked for the 130-endpoint figure to stay bound to its set definitions.
That qualification was correct, and it changed the number.

`scripts/prism_endpoint_inventory.py` derives three sets at run time:

* `legacy` — paths referenced by `archive/frontend/arkadia-prism/web/public_prism/src`
* `served` — paths in the real route table (`app.openapi()`, not a source grep)
* `console` — paths referenced by `web/arkadia_console/src`

Measured on `main` `68403b9e` and on this branch (both with the instrument in place):

| normalization | tree | legacy | served | console | **gap (legacy ∩ served)** | gap (served only) |
|---|---|---|---|---|---|---|
| `id` (params → `{id}`) | `main` | 127 | 262 | 46 | **73** | 234 |
| `id` | branch | 127 | 262 | 48 | **72** | 233 |
| `raw` (literal) | `main` | 127 | 262 | 51 | **72** | 237 |
| `raw` | branch | 127 | 262 | 53 | **71** | 236 |

**The reconciliation target moves by exactly −1 in both normalizations**, which is the one
capability this slice connects. That is the measurement the instrument exists to produce: a
change to the console's reach is *observable as a delta on a re-derived set*, not as a
prose claim.

The earlier **130** was method-dependent and is superseded. It scanned a narrower console
tree; the live tree yields 46–53 depending on normalization. The mission-relevant figure —
capabilities the archived product actually used and the console does not reach — is the
`gap (legacy ∩ served)` column, which is stable across normalization (moves by 1) and is
the number to quote. `gap (served only)` is a coverage figure and varies by 3–4 with the
definition, so it is **not** a reconciliation target.

The instrument always prints its variant, because a count quoted without its definition is
not reproducible. `--matrix` prints every variant together. The `console` column is derived
from `git ls-files`, so a **newly added but uncommitted** file is not yet counted — the
branch figures above are the post-commit state.

---

## 3. Capability-to-surface graph

| Field | Value |
|---|---|
| Capability ID | `SPIRAL-CODEX-CORPUS` |
| User-facing purpose | Read the shared public document corpus (Encyclopedia Galactica) |
| Legacy routes | `/encyclopedia`, `/spiral-codex` (`App.tsx:134-135`) |
| Legacy components | `NexusSpiralCodex.tsx`, `SpiralCodexFeed.tsx`, `SpiralVault.tsx` |
| Current canonical surface | `novanet`, lens `codex` |
| Contract | `GET /api/codex` — public read, verified `200` |
| Identity / authority | **None required.** Read-only; no mutation wired |
| Service | `api/main.py::get_codex` → `_get_scrolls()` |
| State change | None (read) |
| Tests | `tests/test_console_spiral_codex_contract.py` (21) |
| Classification | `UNSURFACED` → `CONNECTED` |
| Confidence | High — route table + live probe + payload shape all measured |

### 3.1 The port is not a copy — a measured 404 proves it

`SpiralCodexFeed.tsx:90-91` fetches `/api/codex/categories` in parallel with the corpus.

```
route table:  /api/codex/categories → ABSENT
production:   /api/codex/categories → 404 {"detail":"Route not found"}
```

A faithful port would have fired a request that can never succeed. Categories are instead
derived from each document's own `category` field, which the payload already carries.

### 3.2 A false statement in the console's own copy, corrected

`NovaNetPage.tsx` told the reader the hub sub-views' contracts were "either unverified or
sovereign-key gated, which the authenticated client cannot satisfy".

| Endpoint | Measured | Claim |
|---|---|---|
| `/api/ims/inquiries` | `403 Sovereign key required` | **true** |
| `/api/codex` | `200`, open read, 661 docs | **false** |

The blanket claim is replaced by the measured reasons, and the corpus is now surfaced on
its own lens rather than described as unavailable.

---

## 4. Changed paths

| Path | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | +`publicCodex: "/api/codex"` (one entry) |
| `web/arkadia_console/src/components/novaNet/spiralCodexContract.ts` | new — shape + derivation |
| `web/arkadia_console/src/components/novaNet/SpiralCodexPanel.tsx` | new — the lens panel |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | +`codex` lens, corrected hub note |
| `tests/test_console_spiral_codex_contract.py` | new — 21 tests |
| `tests/test_console_legacy_route_coverage.py` | disposition for `/encyclopedia`, `/spiral-codex` (was "no console surface") |
| `scripts/prism_endpoint_inventory.py` | new — the inventory instrument |
| `docs/control-plane/evidence/prism-rec-spiral-codex-01/` | this record |

**Not changed:** `api/main.py` (no backend work), `lib/surfaces.ts` (no new surface),
`lib/router.ts` (no new alias — see §6).

### 4.1 Branched from `main`, not stacked on PR #559

This slice was authored on the prior slice's branch (`feat/prism-rec-voice-readaloud-01`,
PR #559) and then **re-based onto `main` `68403b9e` as an independent branch**, because the
two slices would otherwise share one PR diff.

Measured independence:

| Check | Result |
|---|---|
| Files #559 touches | `ReadAloud.tsx`, `lib/voice.ts`, `lib/endpoints.ts`, `ArkanaPage.tsx`, its evidence + test |
| Overlap with this slice | **`lib/endpoints.ts` only**, in a **disjoint region** |
| This slice references any #559 file | **no** (`grep` for `ScrollListenButton`/`voice.ts`/`endpoints.tts` → 0) |
| `endpoints.ts` diff on this branch | `publicCodex` entry only — #559's `tts*` entries are absent |

So the two can merge in **either order**; if `endpoints.ts` conflicts it is a trivial
adjacent-hunk resolution, not a semantic one. Stacking would have made this slice's PR
unreviewable against its own scope, so the branch was re-cut from `main` and the full suite
re-run on the resulting tree (§7.6).

### 4.2 Composition with PR #556 — measured, not assumed

`lib/endpoints.ts` is touched by **three** open branches (#556, #559, and this one), so
textual cleanliness was verified *and then* the composed tree was actually exercised.

| Step | Result |
|---|---|
| `git apply --3way --check` of this slice's `endpoints.ts` onto #556's head | **applies cleanly** |
| #556 head vs `main` | **behind** — `test_console_legacy_route_coverage.py` absent there |
| composed tree = #556 head + `main` merged + this slice applied | merge clean, patches apply clean |
| composed test run (5 relevant guard files) | **89 passed** |
| composed `corepack pnpm build` | **clean**, `✓ built in 1.77s` |

The third row is the reason the first two are not enough: #556's own head is behind `main`,
so applying this slice directly onto it produced two failures that were **artifacts of the
stale base**, not of the composition (`test_console_legacy_route_coverage.py` does not exist
there). Merging `main` in first resolved it. A `git apply --check` exit code would have
reported success throughout — **textual composability is not semantic compatibility.**

---

## 5. Honest presentation

* **Bounded list.** 661 documents / ~5 MB are not rendered whole. `CODEX_DISPLAY_LIMIT`
  bounds the list and `data-testid="codex-truncation"` states the subset. A silent subset
  would present a truncated corpus as the complete one.
* **Distinct states.** Loading, empty-corpus, no-match, and failure are four different
  messages. The empty-corpus copy explicitly says "This is an empty corpus, not an
  unreachable one", so an empty result cannot read as an outage.
* **Facet provenance stated.** The panel says facets are derived because the contract
  serves no categories route — a reader is not left guessing.
* **Search is explainable.** Search covers `label`/`description`/`preview`, the three
  fields the list displays. `content` is deliberately **not** searched: the payload carries
  every body, so matching it would let a document match on text the reader cannot see.
* **No mutation.** No upload control; the archive's `POST /api/codex/upload` is a write and
  belongs in its own slice with its own authority review.

---

## 6. Deliberately not done

* **No `/encyclopedia` or `/spiral-codex` alias.** The alias table maps one path segment to
  a *surface*; these legacy paths need a *default lens*, which is a different mechanism.
  Both currently fall through to `home`. Adding a default-lens alias means changing
  `resolvePath`'s return shape — a shared seam. The legacy-route coverage test now records
  the reconciled disposition so the gap is explicit rather than silently claimed closed.
* **No `/api/solspire/*` repair.** `SolSpirePage.tsx:43-46` declares four `NotYetWired`
  contracts on an `/api/solspire/*` prefix that does not exist (real paths are
  `/solspire/{workloads,proposals,pulses}`; production answers `401` for the two probed).
  **PR #556 owns that file** and its diff replaces exactly those lines. Repairing it here
  would conflict with reviewed work.
* **No `/api/scrolls`, no Knowledge OS coupling, no upload.** Separate slices.
* **`lane-state.json` untouched.** Contended by #553/#555; the `base_main` moving-target
  defect remains owned by them.

---

## 7. Verification

Commands run and their measured results are recorded in §7.1–7.5.

### 7.1 Contract tests

`python -m pytest tests/test_console_spiral_codex_contract.py -q` → **21 passed**.
With the legacy-route guard: **29 passed**.

The derived helpers are **imported and executed** through Node's native TypeScript support,
so the assertions observe the shipped module rather than a regex-stripped copy. An earlier
draft regex-stripped the annotations and failed to run; that approach is abandoned.

### 7.2 Live negative controls (real files, not fixtures)

Each control mutates the **actual** source, asserts the mutation applied, runs the guard,
and restores byte-identically:

| Control | Mutation | Result |
|---|---|---|
| registry bypass | `endpoints.publicCodex` → `"/api/codex"` | **1 failed, 20 passed** — bites |
| dead path | re-add `fetch("/api/codex/categories")` | **3 failed, 18 passed** — bites |
| honesty copy | empty-corpus copy → "The backend is unreachable right now." | **1 failed, 20 passed** — bites |

The third control **did not bite on its first attempt** — the `sed` did not match because
JSX wraps the sentence across two lines. That is the same class of defect the `_flat()`
normalisation fixes, and it is recorded rather than quietly corrected.

Two further detector defects were found and fixed during development, both real:

1. **A doc comment that names the forbidden path was reported as a request.** The panel's
   header comment explains *why* `/api/codex/categories` is not called, and the detector
   matched that prose. Fixed by running source detectors on **comment-stripped** source;
   the control now asserts the detector stays silent on a prose-only mention.
2. **An exact substring pin over JSX prose fails on correct copy.** Fixed by
   whitespace-normalising before the assertion.

### 7.3 Frontend build

`corepack pnpm build` → **clean**, 101 modules, `✓ built in 2.08s`. TypeScript compiles.

### 7.4 Live contract evidence

| Probe | Result |
|---|---|
| `GET /api/codex` (production) | `200`, 661 docs, 4,413,059 chars |
| `GET /api/codex/categories` (production) | `404 Route not found` |
| `GET /api/ims/inquiries` (production) | `403 Sovereign key required` |
| `/api/codex` in `app.openapi()` | present |
| `/api/codex/categories` in `app.openapi()` | absent |

### 7.4.1 Browser journey (the complete user path, not rendering)

Dev server on `:5175` proxying `/api` to the canonical origin, so the browser exercises the
**real backend**. Every step below was observed, not inferred:

| Step | Observed |
|---|---|
| Load `/novanet/codex` | lens strip shows **Encyclopedia Galactica**; route resolves |
| Corpus facts | `status radiant`, `documents 661`, `live 661`, `characters 4,469,876`, `facets 1` |
| Document list | real titles + char counts + real `github.com/.../blob/main/...` URLs |
| Truncation | "Showing 24 of 661 matching documents — the remainder is not rendered on this surface." |
| Search `security` | 661 → **14 matches**, all genuinely security-related (`SECURITY.md`, `ADR-013-phase0-security-hardening.md`, security evidence docs) |
| Read toggle | button → **Collapse**, `<pre>` renders the real `SECURITY.md` body |
| Facet `CREATIVE_OS` | filter applies and the count tracks the filtered set |

The corpus is reachable **anonymously** (`Not signed in` in the header throughout), which is
the contract's own property — no identity is required for this read.

### 7.4.2 The new guard enters the CI gate without editing it

`scripts/console_contract_domain.py` derives the console-contract guard domain from
`git ls-files` **at test time**. Verified:

| Check | Result |
|---|---|
| `python scripts/console_contract_domain.py` on `main` `68403b9e` | **45** guards |
| same with this slice's guard tracked | **46**, includes `test_console_spiral_codex_contract.py` |
| `tests/test_prism_console_ci_wiring.py` | **30 passed** |
| `.github/workflows/prism-console-contract.yml` `paths` | `tests/**` — selects this guard |

This is the derived-inventory repair from PR #439 working as designed: a new console guard is
executed by the gate **without an edit**, which is precisely the class that had composed into
a red `main` at `17988afd` when the inventory was hand-maintained.

### 7.5 Regression

Both trees measured in the **same environment**, in the same session: the branch in place,
base `68403b9e` in a detached worktree. Command on both:

```
PYTHONPATH=archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

`-rEf` is required: `-rf` alone suppresses pytest's `ERROR` summary lines and yields a
**subset** fingerprint that looks well-formed.

### 7.6 Measured regression result

| Tree | Result |
|---|---|
| base `68403b9e` (`main`) | 8 failed / 3357 passed / 17 skipped / 1 error |
| branch `feat/prism-rec-spiral-codex-01` | 8 failed / **3378** passed / 17 skipped / 1 error |

Sorted failing/error **node set** — 9 nodes on both:

```
sha256 215e4308371a01f5b0b73f1e2b5dca5bba30f6578f65bb7c8af6eca67bc8b741
```

`comm -3` between the two node sets is **empty**: zero regression, zero newly introduced
node. The failures are identical on both sides and are pre-existing `main` debt
(`test_autonomy` collection error, `test_engineering_lab_api` ×2, `test_solariun`/`r1`/`r3`
governance pins, `test_ais_w2`, `test_identity_spine_w1`, `test_m02_reasomate_truth`).

**Attribution of `+21 passed`** — `3378 − 3357 = 21`, which is exactly this slice's new
file (`--collect-only` on `tests/test_console_spiral_codex_contract.py` → **21**). Because
the slice is branched from `main` rather than stacked on PR #559, no other file contributes:
the count is the new guard's node count and nothing else.

`tests/test_prism_console_ci_wiring.py` stays at **30** on both sides. Its parametrize IDs
**changed content** — the ID embeds the derived guard domain, which is **45** on `main` and
**46** once this slice's guard is tracked — so a naive text diff reports nodes as "lost" and
"gained". Grouping by test *name* rather than ID shows `LOST test names: {}`: they are
**renames in place**, not losses. Counting by ID would have misreported a phantom
regression here.

---

## 8. Unresolved / limitations

1. **ElevenLabs** — unrelated to this slice; unchanged from the prior record.
2. **`/api/ims/*` and `/api/distribution/*`** — only `/api/ims/inquiries` was probed
   (`403`). The rest of those clusters are `UNKNOWN`, not classified.
3. **The lens-vs-surface decision** — the corpus is a NovaNet lens because `surfaces.ts` is
   a shared seam and a new top-level surface is a larger change than this slice needs. A
   product decision to promote it is open.
4. **Legacy deep links** — `/encyclopedia` and `/spiral-codex` still resolve to `home`.
   Recorded in the disposition table; closing it needs the default-lens mechanism (§6).
5. **No production observation** — production runs `main` `68403b9e`, which does not
   contain this change. `OBSERVED` is claimed for the *contract* (§7.4), not the new UI.
   Render auto-deploys `main`, so a merge is a production release — human authority.

## 9. Rollback

Revert the branch. Additive only: one registry entry, two new files, one page edit, one
test-disposition edit, one new script and test. No backend change, no migration, no
existing behaviour removed.
