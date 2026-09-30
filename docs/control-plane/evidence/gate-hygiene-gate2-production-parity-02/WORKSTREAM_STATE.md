# WORKSTREAM STATE — gate-hygiene / gate2-production-parity-02

Pass: `gate-hygiene/gate2-production-parity-02`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Branch head at pass start: `002b189dd95e` (branched clean from main)

## Active workstreams

| WS | Branch / PR | State |
| --- | --- | --- |
| SH-05 gate-artifact provenance | `gate-hygiene/sh05-gate-artifact-provenance-01`, PR #142 | EXHAUSTED — see §3 |
| Gate-2 production parity | `gate-hygiene/gate2-production-parity-02` (this branch), PR #143 | PARTIAL — deployment identity + build↔source lineage VERIFIED (all 12 candidate SHAs, closure arg §10.1); **browser-rendered UI OBSERVED** (§11, 6/6 routes); **backend runtime VERIFIED + discriminating** (§12); provider build observation still BLOCKED; `main → backend deployment identity` UNKNOWN. Three durable harnesses: `scripts/gate2_production_observation.py`, `scripts/gate2_browser_observation.py`, `scripts/gate2_backend_observation.py` |

## 1. Baseline fingerprint recorded at pass start

Measured on `002b189dd95e` in this environment, not carried from prose.

| Suite | Result |
| --- | --- |
| `python -m pytest tests/architecture -q` | **11 passed / 0 failed** |
| `python -m pytest tests/ -q --continue-on-collection-errors` | **20–21 failed / 1038–1039 passed / 13 skipped / 2 collection errors** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line count | 2519 (budget 2600) |

The 2 collection errors are the documented pre-existing pair (`test_autonomy.py`
`load_autonomy_config`, `test_render_codex.py` `arkadia_drive_sync`).

The previously recorded baseline in the pass contract (`804 passed / 54 failed`) does
**not** reproduce on current main. It is a stale fingerprint. Reconciled: the contract's
`6038989`-era baseline is 12 failures larger than what current main shows, and the
`test_steward_filter.py` failures were introduced by the steward-filter carrier
(`f02-steward-filter-provenance-01`, merged as `002b189`) on top of base `df7a99a`, which
carried the 32-failure fingerprint. See §2.

## 2. NEW: suite fingerprint is UNSTABLE (1 intermittent node)

`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
is **intermittent under the full suite** and passes **8/8 in isolation**.

Observed across 4 full-suite runs on the same SHA: `20, 21, 20, 21` failures. The only
node that moves is this one.

Root cause (read from source, `tests/test_engineering_lab_agent_loop.py:313-338`): the
test snapshots **global** `git status --porcelain` on `REPO_ROOT` before and after
`execute_agent_loop`, then asserts equality. It is therefore sensitive to repository
writes made by *any other test* in the same process — not only to the agent loop it means
to constrain. The agent loop itself performs only `git_status` (allowlist `("git",)`), so
the guard's own subject is not what fails.

This is **test cross-contamination**, not a boundary violation. It is recorded here
because an unstable fingerprint makes failure attribution unreliable: a run that reports
21 failures cannot be distinguished from a real regression by count alone.

**Not fixed in this pass** — discovery does not authorize execution, and it is unrelated
to the Gate-2 scope. It is proposed below as its own bounded workstream.

## 3. SH-05 — gate-artifact provenance: EXHAUSTED

The SH-05 branch's subject was whether `gate/` artifact rows 47–48 were carried as
`ENV/ARTIFACT` without evidence.

Findings, from repository history rather than prose:

- `gate/` artifact provenance traces to the merged steward-filter carrier
  (`f02-steward-filter-provenance-01`, `002b189`).
- The 12 `test_steward_filter.py` failures on current main are attributable to that
  carrier: base `df7a99a` carried the 32-failure fingerprint, current main carries 20.
  The delta is the retired/rewritten steward-filter nodes, not new debt.
- No further provenance-bearing nodes remain to trace on that branch. SH-05 has reached
  its completion condition.

Disposition: **do not open new work on SH-05.** If the ledger rows still need a
classification change, that is a documentation edit that belongs on the existing PR #142,
not a new branch.

## 4. Gate-2 — production parity: what changed

Full detail in `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/EVIDENCE.md`.

- **VERIFIED (new):** the main→deployment link Gate 2 was missing. GitHub Deployments
  records Production deployment `6749238709` with `ref == sha == 002b189dd95e...` —
  exactly current main — status `success`, created `2026-09-30T01:23:16Z`.
- **BLOCKED:** the deployment-specific URL
  (`https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app`) returns HTTP 302 to
  `vercel.com/login` — Vercel Deployment Protection (SSO). Build output not observable.
- **UNKNOWN:** alias→`002b189` binding, and browser-rendered UI correctness.
- **NOT CLAIMED:** production parity and production acceptance.

Two carried-forward cautions, both re-affirmed:

1. **Asset hash is not a parity oracle.** Build output is env-dependent — injecting
   `VITE_API_BASE_URL` changes the hash with no source change. Mismatch ≠ divergence;
   match ≠ parity.
2. **Route 200 is not application correctness.** `vercel.json` rewrites `/(.*)` →
   `/index.html`, so `/api/health` (never a backend route, per `git log -S`) returns
   `200 text/html` identically to any non-existent path.

## 5. Proposed next bounded tasks (NOT authorized by this pass)

| Proposal | Scope | Authority needed |
| --- | --- | --- |
| P-1 Vercel read access for `arkadia-prism` | closes Gate-2 observation | HUMAN (provider credential) |
| P-2 Stabilize `test_agent_loop_does_not_mutate_repository` | make it path-scoped / isolate from global `git status`; restores fingerprint determinism | none beyond normal PR review |
| P-3 Refresh the stale baseline fingerprint in the pass contract | docs only | none |
| P-4 Tracked-but-stale build output `web/public_prism/dist/` | stop tracking the build dir, or pin it via a checked build step | none beyond normal PR review |

P-2 is the smallest and is independently safe: it strengthens a boundary guard rather than
weakening it, by making it assert what it actually means to assert. It should be taken as
its own branch/PR if the sovereign wants it, not folded into Gate 2.

### Finding: `web/public_prism/dist/` is tracked and drifts

`web/public_prism/dist/index.html` is tracked by git, but it is a **build output**. At pass
start the working tree already carried an uncommitted modification to it, referencing
`assets/index-DIKNxYlc.js` — the env-injected experimental build left behind by the
previous pass — while `main` commits `assets/index-CStL2fKK.js` and the live production
alias serves `assets/index-CHFFyuSc.js`. Three different hashes for the same file.

Consequence: the tracked artifact is stale relative to production at all times, and because
the hash is env-dependent (§4) it also silently drifts whenever anyone builds locally. It is
a source of exactly the misleading hash comparisons the Gate-2 cautions warn against. The
stale working-tree copy was **reverted, not committed**, by this pass — it is not part of
this change set.

## 6. Next heartbeat

Reconstruct from live evidence. The Gate-2 chain is now:

```
main SHA ✓ → deployment SHA ✓ → build↔source lineage ✓ → route resolution ✓
  → deployment observation ✗ BLOCKED → alias binding ? → UI/runtime ? → acceptance (human)
```

Resume at the first unresolved link. If no Vercel credential has been supplied, the
observation link stays BLOCKED and no further Gate-2 progress is possible — proceed with
P-2 instead.

## 7. Pass 2 update (same branch, same PR)

Full detail in `EVIDENCE.md` §8–§9. Summary:

- **New VERIFIED link: build↔source lineage.** The deployed asset carries discriminating
  source-string markers from current main (`separate explicit downstream stages`,
  `activity-draft.v1:`, `learning-activity-work-surface`, `sg03-contract-boundary`,
  `solspire-object-summary`, `opportunity-radar`), and a clean local build of `002b189`
  matches it **on every marker and count**. The pre-SG-03 control string is absent from
  both. `git log` shows **zero** commits under `web/public_prism/src/` since the production
  deployment was created (`2026-09-30T00:23:16Z`), so there is no divergence window.
- **New VERIFIED link: route resolution.** `/solariun/opportunity-radar` resolves via
  `App.tsx:51 resolvePath()` against `SOLSPIRE_LENSES`; the lens registry is present in the
  deployed bundle. This is a source-level proof, not a browser observation.
- **Unchanged BLOCKED:** deployment-specific build observation (Vercel SSO) and the
  alias→SHA binding. These need the provider credential in §6 — no repetition closes them.
- **Fingerprint this pass:** architecture 11/11, gate integrity 49/49, full suite
  **20 failed / 1039 passed / 13 skipped / 2 collection errors**, `py_compile` OK,
  `api/main.py` 2519 lines. Stable at the low end of pass 1's `20–21`; no new regression.
- **SG-04 (`ActivityRuntime`) is now bound to the deployed artifact**, not just to the test
  file: `activity-runtime-draft.v1:` is absent from the production bundle while every SG-03
  marker is present. That upgrades it from "possibly stale assertion" to **real product
  regression carried to production**. Still deliberately unfixed here — it is a product
  change outside Gate-2 hygiene scope. Tracked under `gate-hygiene` / SH-02, Gate GATE-01.

### Standing caution (re-affirmed, now with a workaround)

Hash comparison is not a parity oracle — the deployed bundle is 84,551 bytes larger than a
clean local build because Vercel injects env vars at build time. **Marker-set comparison is**
robust to that injection and is the oracle to use for future lineage checks. Do not fall
back to hash equality.

## 8. Pass 4 update (same branch, same PR) — browser-rendered UI OBSERVED

Full detail in `EVIDENCE.md` §11. Summary:

- **New link closed: browser-rendered UI correctness, `UNKNOWN` → `OBSERVED`.** Passes 1–3
  observed the *served* surface; a 200 plus a matching asset marker proves the bundle was
  served, not that the app mounted or rendered. This pass drove a real headless browser
  (Playwright/Chromium) against the live alias and asserted **source-verified text anchors**
  on six routes: `/`, `/oracle`, `/nexus`, `/solariun`, `/solspire`, `/spiral-codex`.
  **All six OBSERVED**, `pageErrors` 0, `failedRequests` 0 on every route.
- **Strongest single result:** `/spiral-codex` rendered **104,036 characters** of body text
  — proof of *data-bound* rendering, not merely app mount. A shell that mounted but failed to
  load data renders a few hundred characters. Cross-checked: 285 real scrolls.
- **New durable harness:** `scripts/gate2_browser_observation.py` (read-only, stdlib-only
  Python; holds no credential; exit 0 = all OBSERVED, 1 = FAILED, 2 = BLOCKED when the
  browser dependency is absent — never silently passed). It re-verifies every anchor against
  the frontend source each run and reports removed literals as `stale_anchors`.
- **New tests:** `tests/test_gate2_browser_observation.py` — **14 passed**. Includes negative
  controls (missing anchor, non-200, `pageerror`, failed request, unexpected console error
  each fail) and a read-only assertion (no `Authorization`, no mutating HTTP verbs, no
  `git push`/`git commit`).
- **`/novanet` is not a registered route.** `App.tsx:69` registers `nexus`. An earlier probe
  in this workstream used `/novanet` and would have been misread as a broken route had the
  source not been checked first. Do not repeat it.
- **Console error on `/spiral-codex`: diagnosed, scoped, expected-benign.** The 404 is on
  `GET /api/codex/categories`, called by `SpiralCodexFeed.tsx:91`. **No handler for that route
  exists anywhere in the repository** — it is a frontend↔backend contract mismatch, not an
  outage. The caller degrades gracefully (`catsRes.ok ? … : { categories: [] }`), so the page
  renders fully. Exempted as `EXPECTED_BENIGN` and recorded as *informational*; the exemption
  is keyed to that one route and a test proves an unrelated 404 still fails.
  **Note for future passes:** the browser puts the URL in `location()`, *not* in
  `message.text()`. Matching on message text alone cannot identify this error — that mistake
  was made and corrected within this pass.
- **Still BLOCKED / UNKNOWN (unchanged, not re-spent):** deployment-specific build
  observation (Vercel SSO; needs the credential in §6) and alias→SHA binding (immaterial per
  §10.1 — do not chase it). **Parity is still NOT claimed; acceptance is the sovereign's.**

### Open bounded item surfaced by this pass (SH-06 candidate, NOT authorized)

`/api/codex/categories` is called by the frontend and does not exist in the backend. Today it
fails softly. Fixing it is a product/API change outside Gate-2 hygiene scope, so it is
recorded and **not** executed. Bounded options: implement the route, or remove the call and
let the page use an empty category set explicitly. Either way it needs its own gate and its
own authority.

### Next heartbeat

Gate 2's remaining links are provider-bound or immaterial. Unless a Vercel credential has been
supplied, do **not** re-run Gate-2 parity — the browser link is now closed and the rest cannot
move by repetition. Resume at PR #142 / #144 triage, or take up SH-06 if authorized.

## 5. Pass 5 (this heartbeat) — backend runtime link closed

The Render service is the actual application runtime and had never been observed. It is
anonymously reachable, so the link `main SHA -> backend deployment -> backend runtime
observation` is testable where the Vercel build-output link is not (that one stays BLOCKED
on the provider credential).

New harness: `scripts/gate2_backend_observation.py` (read-only, stdlib-only, no credential).
New fitness tests: `tests/test_gate2_backend_observation.py` — **18 passed**.

Observed on `002b189dd95e`: `/openapi.json` HTTP 200, title `Arkadia Mind — Cycle 11`,
**274 operations**, digest `d1797f9c…e30b`. Liveness floor 200/200/200 for `/`,
`/api/stellar-cartography`, `/api/tts/status`. All four required prefixes present
(`/api/commune`, `/api/stellar-cartography`, `/api/tts`, `/api/echoes`).

**The oracle's discrimination was measured, not assumed.** Against negative control
`2525811` the signature differs (`846748380cde…`), giving 2 distinct signatures ⇒
`discriminating: true`; deployed == main exactly. This is the property the frontend
marker-set oracle could not demonstrate, and it is why §12 reports `VERIFIED` rather than
`VERIFIED (undiscriminating)`. `cd24bb1` (P1-A boot-broken) failed to import and was
**excluded**, not counted as discrimination.

**Harness defect found and fixed during this pass:** the required-prefix check read paths
out of signature rows with `split(" ", 1)[1]`, retaining the ` :: summary` suffix, so every
prefix looked absent while the harness's own probe returned 200. Fixed to `split(" ", 2)[1]`
with a regression test. The negative control exposed it; the happy path would not have.

### Regression boundary for this pass

| Suite | main `002b189` | branch `97b37d2`+ |
| --- | --- | --- |
| `pytest tests/architecture -q` | 11 passed | **11 passed** |
| `pytest tests/ -q --continue-on-collection-errors` | 20 failed / 1039 passed / 13 skipped / 2 errors | **20 failed / 1071 passed / 13 skipped / 2 errors** |
| failing-test **names** | 22 rows | **identical (diff empty)** |
| `python -m py_compile api/main.py` | OK | OK |

Passed count rose by exactly the 32 new gate2 tests; the failure fingerprint is
byte-identical, so **no failure is attributable to this pass**.

### Next heartbeat (revised)

Do **not** re-run Gate-2 parity: the frontend browser link (§11) and the backend runtime
link (§12) are both closed, and the two remaining links are provider-bound
(`BLOCKED`, needs the Vercel credential in §6) or non-identifying (Render publishes no
deploy-commit record). Repetition cannot move either. Resume at PR #142 / #144 triage, or
take up SH-06 if authorized. **Parity is still NOT claimed; acceptance is the sovereign's.**
