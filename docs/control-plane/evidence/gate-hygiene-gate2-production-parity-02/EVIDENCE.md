# GATE-02 — Production Parity: deployment identity resolved, build observation BLOCKED

Pass: `gate-hygiene/gate2-production-parity-02`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Repository: `Arkadia-Oversoul-Prism/Arkadia`

## 1. Why this pass exists

Gate 2 was open on **production parity**. The handoff state required that a production
deployment be tied to a specific main SHA and that the resulting runtime behaviour be
independently observed. The previous Gate-2 evidence pass (`46c58fa`,
`gate2-public-runtime-integrity/EVIDENCE.md`) recorded route reachability only and
explicitly declined to claim parity.

This pass advances exactly one boundary: **resolve the deployment identity for current
main** — and then stop at the provider boundary that prevents observing it.

## 2. Deployment identity — RESOLVED (VERIFIED)

Queried via the GitHub Deployments API (the repository's own record of deployments, not
inferred prose):

```
GET /repos/Arkadia-Oversoul-Prism/Arkadia/deployments?environment=production&per_page=10
GET /repos/Arkadia-Oversoul-Prism/Arkadia/deployments/6749238709/statuses
```

The newest Production deployment is bound to **exactly the current main tip**:

| Field | Value |
| --- | --- |
| deployment id | `6749238709` |
| environment | `Production` |
| `ref` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| `sha` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| creator | `vercel[bot]` |
| created_at | `2026-09-30T01:23:16Z` |
| status | `success` |
| `environment_url` | `https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app` |
| status description | `Deployment has completed` |
| status created_at | `2026-09-30T01:23:17Z` |

Corroborating commit status on the main tip:

```
GET /repos/.../commits/002b189dd95e41c9b4f4cca33d08b4121453d289/status
  state: success   total_count: 1
  Vercel   success   2026-09-30T01:23:16Z
```

**Result:** the main→deployment link is now established from provider records.
`ref == sha == current main`. This is the link Gate 2 was missing.

This does **not** establish production parity on its own — it establishes the *identity*
of the deployment produced from current main. Observation is the next link (see §3).

## 3. Deployment build observation — BLOCKED (provider auth boundary)

The deployment-specific URL recorded by Vercel is not publicly readable:

```
GET https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app/
  → HTTP 302
  → https://vercel.com/login?next=/sso-api%3Furl%3D...arkadia-prism-ey2ozd5u4...
```

This is **Vercel Deployment Protection (SSO)**. The deployment is not anonymous-readable,
so its build output (asset manifest) cannot be observed without a Vercel credential that
this run does not hold.

Classification: **BLOCKED** — actionable external boundary (provider authentication).
Per contract this is not a puzzle to route around: no workaround was attempted.

## 4. Production alias — reachable, but does not close the parity chain

```
GET https://arkadia-prism.vercel.app/   → HTTP 200
```

The alias `index.html` references:

- `assets/index-CHFFyuSc.js`
- `assets/index-C2whHMVB.css`

The alias is reachable, but reachability alone cannot bind the alias to the `002b189`
deployment in this pass. Vercel assigns the Production alias to the newest Production
deployment, but that is **provider behaviour, not an observation made here**.

Classification: **UNKNOWN** — the alias→`002b189` binding is not directly observed.

### Asset-hash comparison is not a valid parity oracle

Carried forward from the SH-05 pass and re-affirmed: the build output is
environment-dependent. Injecting `VITE_API_BASE_URL` changes the emitted asset hash
(`index-xiYlcBh3.js` → `index-DIKNxYlc.js`) with no source change. Therefore an
alias-vs-local hash mismatch **must not** be reported as source divergence, and a hash
match would not by itself prove parity either. The oracle is unusable in both directions.

### HTTP 200 on any route is not evidence of application correctness

Root `vercel.json` rewrites `/(.*)` → `/index.html`. Consequently `/api/health` — which
`git log -S` shows never existed as a backend route — returns `200 text/html` (the SPA
shell) exactly as any non-existent path does. Route-level 200 responses on this project
are a property of the rewrite, not of the application. The prior pass's route-reachability
results must be read with this caveat.

## 5. Boundary classification for this pass

| Boundary | State |
| --- | --- |
| current main resolved | **VERIFIED** — `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| main → Production deployment identity | **VERIFIED** — deployment `6749238709`, `ref == sha == main` |
| deployment build output observed | **BLOCKED** — Vercel Deployment Protection (SSO) |
| alias serves the `002b189` deployment | **UNKNOWN** — not directly observed |
| browser-rendered UI correctness | **UNKNOWN** — no browser observation performed |
| production acceptance | **NOT CLAIMED** — human authority |

**Parity is NOT claimed.** The chain is now:

```
main SHA  ✓ VERIFIED
  → deployment SHA  ✓ VERIFIED (provider record, ref == sha)
    → deployment observation  ✗ BLOCKED (provider auth)
      → alias binding  ? UNKNOWN
        → UI/runtime observation  ? UNKNOWN
          → acceptance  — human sovereign
```

## 6. Exact handoff required to close Gate 2

One of:

1. A Vercel credential with access to project `arkadia-prism` — sufficient to read the
   `002b189` deployment's build output and confirm the alias binding; or
2. The Vercel Deployment Protection setting relaxed for this project (so the deployment
   URL becomes anonymous-readable); or
3. A browser/runtime observation performed by a party that holds such access, returning
   the deployment URL, asset manifest, route results and console state.

Absent one of these, no stronger claim than §5 is justified. Repeating this pass cannot
convert `BLOCKED`/`UNKNOWN` into `VERIFIED`.

## 7. Regression boundary

No product code was changed by this pass. This artifact is documentation only.

## 8. Pass 2 — a valid parity oracle found (marker-set lineage)

Added by the next heartbeat on the same branch. The pass-1 conclusion was that asset
**hashes** cannot decide parity. That is correct, but it left the chain with *no* usable
oracle. A usable one exists: **discriminating source-string markers compiled into the
production bundle.**

### 8.1 Method

Extract string literals that are unique to specific source files and therefore must survive
minification (they are runtime data, not identifiers). Then test for them in the deployed
asset with a fixed-string search.

| Marker | Source | Meaning if present |
| --- | --- | --- |
| `separate explicit downstream stages` | `CapabilityChamber.tsx` (SG-03 boundary) | post-SG-03 chamber text |
| `activity-draft.v1:` | `CapabilityChamber.tsx` | SG-03 draft persistence key |
| `learning-activity-work-surface` | `CapabilityChamber.tsx` | SG-03 work surface testid |
| `sg03-contract-boundary` | `CapabilityChamber.tsx` | SG-03 contract boundary testid |
| `solspire-object-summary` | `OpportunityRadarPage.tsx` | radar page rendered |
| `opportunity-radar` | SolSpire lens registry | radar lens registered |

Pre-change control: `separate downstream stages` (the pre-SG-03 wording) → **0 occurrences**.

### 8.2 Result — deployed bundle carries current main's markers

Production asset `https://arkadia-prism.vercel.app/assets/index-CHFFyuSc.js`
(2,025,825 bytes, `last-modified: Wed, 30 Sep 2026 03:27:08 GMT`) tested:

```
separate explicit downstream stages   1      activity-runtime-draft.v1:   0
separate downstream stages            0      learning-activity-work-surface 1
activity-draft.v1:                    1      sg03-contract-boundary      1
solspire-object-summary               3      opportunity-radar           2
```

A clean local build of `002b189` (`pnpm build`, assets `index-C2whHMVB.css` /
`index-xiYlcBh3.js`, 1,941,274 bytes) tested **identically on every marker** — same
presence set, same counts.

**Count convention (read this before comparing against §10).** The counts above are
`grep -c` — *matching lines*, not occurrences. The minified bundle is a handful of very
long lines, so a marker repeated on one line counts once here and several times in the
occurrence-counting harness in §10. The two sets are consistent, not divergent:
`solspire-object-summary` is **3 lines / 6 occurrences** and `opportunity-radar` is
**2 lines / 4 occurrences**. Only the presence/absence contrast is load-bearing (a marker
that must be present vs. the pre-SG-03 control that must be absent); the magnitudes are
reported for reproducibility, so a future pass must not read a count difference between
these two sections as evidence of drift.

### 8.3 What this does and does not establish

**Does establish.** The production deployment serves a build whose source is at or after
the SG-03 chamber revision, and the radar surface is compiled in. Corroborated by
`git log` — **no commit under `web/public_prism/src/` since `2026-09-30T00:23:16Z`**, i.e.
none after the production deployment was created. There is no source divergence window
between `002b189` and the deployed build.

**Does not establish.** The alias→`002b189` *binding* as a Vercel fact (still needs provider
read access), and browser-rendered UI correctness. Marker presence is not visual proof.

**Why the byte difference is expected.** Deployed bundle is 84,551 bytes larger than the
local build. Vercel injects env vars at build time (`VITE_API_BASE_URL` and peers), which
changes content and hash with no source change — exactly the pass-1 caution. Marker-set
equality is robust to this; hash equality would not have been.

### 8.4 Route resolution verified from source (not inferred)

`/solariun/opportunity-radar` is a real route. `App.tsx:51 resolvePath()` matches
`^/solariun(?:/([^/]+))?$`, and `candidate` is accepted only when
`SOLSPIRE_LENSES.has('opportunity-radar')` — the lens registry that the production bundle
contains. The route therefore resolves to the SolSpire shell with the radar lens selected.

### 8.5 Revised boundary classification

| Link | Pass 1 | Pass 2 |
| --- | --- | --- |
| main SHA | VERIFIED | VERIFIED |
| deployment SHA == main | VERIFIED | VERIFIED |
| deployment build observation | BLOCKED (SSO) | **BLOCKED** (unchanged; provider boundary) |
| build↔source lineage | UNKNOWN | **VERIFIED** (marker-set, §8.2) |
| route resolves | UNKNOWN | **VERIFIED** from source (§8.4) |
| alias→SHA binding | UNKNOWN | UNKNOWN |
| browser-rendered UI correctness | UNKNOWN | UNKNOWN |
| production acceptance | not claimed | not claimed |

Gate 2 remains open. §6 is unchanged and still the exact handoff: a Vercel credential (or a
protection relaxation, or a third-party browser observation) is required to close the
remaining links. No repetition of this pass converts the remainder.

## 9. Fingerprint recorded this pass

Measured on `002b189dd95e` in this environment:

| Suite | Result |
| --- | --- |
| `python -m pytest tests/architecture -q` | **11 passed / 0 failed** |
| `python -m pytest tests/test_m02a_ci_gate_integrity.py -q` | **49 passed** |
| `python -m pytest tests/ -q --continue-on-collection-errors` | **20 failed / 1039 passed / 13 skipped / 2 collection errors** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line count | 2519 (budget 2600) |

Failing-node fingerprint (sorted, `sha256 f388a231…ae86e`) — stable at **20**, which is the
low end of pass 1's `20–21` range and therefore **consistent with, not a change from**,
the recorded baseline. The intermittent node described in §2 did not fire this run.

### CI state (full 40-char SHAs)

- `main` `002b189dd95e41c9b4f4cca33d08b4121453d289` → 8 check-runs: **Full-history secret
  scan = success**, browser = success, 6 × `weaver_evolution` = skipped.
- PR #143 head `edea5f9473b154a1f485721191d86713bccf66c5` → **Full-history secret scan =
  success**, Vercel Preview Comments = success.

### SG-04 regression — fingerprint isolated, not fixed

`tests/test_spiral_grove_activity_runtime.py`: **4 failed / 8 passed**, with
`tests/test_spiral_grove_chambers.py` (SG-03) green. Isolated nodes:

```
test_runtime_is_mounted_by_the_capability_chamber
test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
test_chamber_preserves_sg03_downstream_boundary
test_spiral_grove_uses_the_nexus_canonical_header
```

Corroborated by the production bundle: `activity-runtime-draft.v1:` → **0 occurrences**,
while every SG-03 marker → 1. `ActivityRuntime.tsx` is not reached from
`CapabilityChamber.tsx` in the deployed build. The SG-03 rewrite carried to production and
displaced the SG-04 mount.

**Deliberately not fixed in this pass.** §8.2 now binds this to the deployed artifact, which
makes it a real product regression rather than a stale assertion — but repairing the mount
is a product change outside Gate-2 hygiene scope. It stays classified
`gate-hygiene` / SH-02, Gate GATE-01, and remains open.

## 10. Pass 3 — source-lineage closure, and a durable observation harness

Pass 2 (§8.3) bounded the divergence window for `web/public_prism/src/` against the **newest**
deployment only. This pass closes it for **every** candidate deployment, and makes the whole
Gate-2 observation reproducible instead of prose.

### 10.1 The closure argument

`git log -1 -- web/public_prism/ ':!web/public_prism/dist'` resolves the last commit that
touched **any** frontend build input — not just `src/`, so config and lockfiles are included:

```
b377a01a53553fcafdec319851b9c4f8edd8a8d2   2026-09-29 05:18:57 +0100
Merge pull request #2 .../sg-04-3-persistence-hardening
```

Every one of the **12** Production deployments on record (`sha` from the deployments API) is a
**descendant** of `b377a01`:

| deployment SHA | created_at | descendant of `b377a01` |
| --- | --- | --- |
| `002b189dd95e` | 2026-09-30T01:23:16Z | YES |
| `bf93a931c903` | 2026-09-30T01:22:46Z | YES |
| `ecb86f7ec264` | 2026-09-30T01:22:17Z | YES |
| `1b2ba50e85f9` | 2026-09-30T01:21:57Z | YES |
| `f9828ce99250` | 2026-09-30T01:16:13Z | YES |
| `bcf30d62d7bf` | 2026-09-30T01:14:44Z | YES |
| `c2029223fc45` | 2026-09-30T01:14:22Z | YES |
| `b37a54212eda` | 2026-09-30T01:13:54Z | YES |
| `df7a99a06738` | 2026-09-29T15:03:52Z | YES |
| `94afda68f8d3` | 2026-09-29T15:03:23Z | YES |
| `e209b1b8f192` | 2026-09-29T15:03:00Z | YES |
| `3f78b335d6dd` | 2026-09-29T15:01:26Z | YES |

**Consequence.** All twelve candidates compile *byte-identical frontend source*. The deployed
artifact therefore **cannot** discriminate between them. This does not make alias→SHA
observable — it remains `UNKNOWN` as a Vercel fact — but it makes the ambiguity **immaterial to
source lineage**: whichever of the twelve the alias is serving, it is serving `b377a01`'s
frontend, and `b377a01` is an ancestor of `002b189`. The `build ↔ source lineage` claim does
not depend on resolving it.

This is strictly stronger than §8.3, which could only exclude divergence *after* the newest
deployment. It is also the reason the alias→SHA question must **not** be chased further: no
amount of artifact inspection can resolve it, and resolving it would not change the
classification. Stated so a future pass does not re-spend effort here.

### 10.2 Why the artifact cannot carry the binding — provider detail

The deployment-specific host is published on the deployment **status**, not on the deployment
record:

- `GET /repos/.../deployments/6749238709` → `environment_url: null`
- `GET /repos/.../deployments/6749238709/statuses` →
  `environment_url: https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app`

The hostname segment (`ey2ozd5u4`) is a provider-generated hash, **not** derivable from the
deployment id. A pass that constructs the URL as `arkadia-prism-{id}-…vercel.app` gets HTTP
404 and would misread it as "deployment missing". Recorded here because that exact mistake was
made and corrected within this pass.

### 10.3 Durable observation harness

Gate-2 observation was previously a manual sequence repeated each heartbeat. It is now one
read-only command:

```
python scripts/gate2_production_observation.py          # human-readable glance
python scripts/gate2_production_observation.py --json   # machine-readable
```

`scripts/gate2_production_observation.py` holds no Vercel credential, performs no mutation,
uses only the standard library, and never prints a token. It re-derives every link from live
evidence and prints the boundary classification. Two properties matter for trust:

- **The marker list is checked against source every run.** A literal that no longer exists in
  `web/public_prism/src/` is reported as a `stale_list` entry rather than silently counting 0
  and looking like a regression.
- **It asserts the closure argument, not just the marker set.** `source_lineage_closed` is
  computed from live git ancestry, so the §10.1 claim is re-proven each run.

Live output this pass:

```
main SHA                : 002b189dd95e41c9b4f4cca33d08b4121453d289
newest Production deploy: 002b189dd95e  id=6749238709  2026-09-30T01:23:16Z
  ref == sha == main    : True
alias https://arkadia-prism.vercel.app/ -> HTTP 200 (x-vercel-cache: HIT, age: 11010)
  manifest: assets/index-C2whHMVB.css, assets/index-CHFFyuSc.js
  deployment-specific URL -> HTTP 302 (SSO redirect)
local build marker set matches deployed: True
all 12 candidate Production SHAs are descendants of b377a01: True
SG-04: in source True / in deployed artifact 0  => REGRESSION: True
```

### 10.4 Boundary classification after Pass 3

| Link | Pass 1 | Pass 2 | Pass 3 |
| --- | --- | --- | --- |
| main SHA | VERIFIED | VERIFIED | VERIFIED |
| deployment SHA == main | VERIFIED | VERIFIED | VERIFIED |
| deployment build observation | BLOCKED | BLOCKED | **BLOCKED** (provider boundary, unchanged) |
| build↔source lineage | UNKNOWN | VERIFIED (newest only) | **VERIFIED (all 12 candidates, §10.1)** |
| route resolves | UNKNOWN | VERIFIED from source | VERIFIED |
| alias→SHA binding | UNKNOWN | UNKNOWN | **UNKNOWN — and immaterial (§10.1)** |
| browser-rendered UI correctness | UNKNOWN | UNKNOWN | UNKNOWN |
| production acceptance | not claimed | not claimed | not claimed |

Gate 2 remains open. The remaining links need a Vercel credential, a protection relaxation, or
a third-party browser observation — §6 is unchanged. No repetition of this pass converts them.

**Note on the `BLOCKED` link.** It is deliberately left `BLOCKED`, not downgraded. The
divergence argument removes the *consequence* of not observing the deployment-specific URL; it
does not make the observation happen. Collapsing it to `VERIFIED` on the strength of §10.1
would be exactly the substitution the contract forbids.

## 11. Pass 4 — browser-rendered UI observation: UNKNOWN → OBSERVED

Passes 1–3 left exactly one link classified `UNKNOWN` that is *closable by this run*:
**browser-rendered UI correctness**. Pass 3 observed the *served* surface (HTTP status,
marker lineage, alias binding). A 200 with a matching asset marker proves the bundle was
served; it does not prove the app mounted, the router resolved, or the data-bound surfaces
rendered. This pass closes that gap with a real headless browser against the live alias.

The other `UNKNOWN` link — alias→SHA binding — stays `UNKNOWN` and is **not** pursued
(§10.1: it is immaterial to source lineage and unresolvable by artifact inspection). The
`BLOCKED` deployment-observation link is untouched.

### 11.1 Method — source-verified text anchors, not screenshots

A screenshot is not a durable oracle: it cannot be diffed, re-run, or reviewed in a PR. The
oracle used here is **text anchors rendered into the DOM**, each of which is a lowercase
ASCII substring of a literal that exists in `web/public_prism/src`.

Three properties were required before an anchor was accepted:

1. **Source-verified.** The harness re-reads the frontend tree every run and reports any
   anchor that no longer exists as `stale_anchors`. A removed literal fails loudly instead
   of silently matching nothing. Proven by
   `tests/test_gate2_browser_observation.py::test_every_anchor_still_exists_in_frontend_source`.
2. **Case-insensitive.** Deployed text is uppercased by CSS, so case-sensitive matching
   would produce false failures. Proven by `test_anchors_are_lowercase_ascii`.
3. **ASCII-only.** Non-ASCII punctuation (the em/en dashes that appear in Arkadia's display
   strings) does not survive a naive substring match. Proven by the same test.

### 11.2 Anchors and provenance

| Route | Anchor (lowercase ASCII) | Provenance |
| --- | --- | --- |
| `/` | `become one continuous field` | `ArkadiaLandingPage.tsx` |
| `/oracle` | `pattern intelligence`, `guest session` | `ArkanaCommune.tsx:757` |
| `/nexus` | `private reasomate remains separate` | `SocialFieldVerified.tsx:325` |
| `/solariun` | `enter solariun` | `SolariunConsole.tsx` |
| `/solspire` | `enter the enterprise layer` | `EnterpriseConsole.tsx:70` |
| `/spiral-codex` | `living archive of arkadia` | `SpiralCodexFeed.tsx:248` |

`/nexus` is the canonical route — `App.tsx:69` registers `nexus`; `/novanet` is **not** a
registered path. An earlier probe in this workstream used `/novanet` and would have been
misread as a broken route had the source not been checked first. Recorded so a future pass
does not repeat it.

### 11.3 Result — all six routes rendered

```
alias: https://arkadia-prism.vercel.app
  /                OBSERVED  status=200 bodyLen=1918
  /oracle          OBSERVED  status=200 bodyLen=179
  /nexus           OBSERVED  status=200 bodyLen=426
  /solariun        OBSERVED  status=200 bodyLen=115
  /solspire        OBSERVED  status=200 bodyLen=200
  /spiral-codex    OBSERVED  status=200 bodyLen=104036
      - expected-benign console noise: ['/api/codex/categories']
browser-rendered UI: OBSERVED
```

`/spiral-codex` returning **104,036 characters of rendered body text** is the strongest
single result: it is proof of **data-bound rendering**, not merely app mount. A shell that
mounted but failed to load data would render a few hundred characters. (Cross-checked in
this workstream: the page renders 285 real scrolls.)

All six routes: `pageErrors` 0, `failedRequests` 0.

### 11.4 The one console error — diagnosed, expected-benign, and scoped

`/spiral-codex` emits exactly one console error. The browser reports it as
`Failed to load resource: the server responded with a status of 404 ()` — **the URL is not in
the message text**, it is only in `location()`. Matching on `message.text()` alone therefore
does not identify it; the first run of this harness mis-classified it as an unexpected error
for that reason. The harness now matches on `text + location.url`, which is what made the
diagnosis attributable.

Diagnosed cause: `GET /api/codex/categories` → **404**.

- The caller is `web/public_prism/src/pages/SpiralCodexFeed.tsx:91`
  (`apiFetch('/api/codex/categories')`).
- **No handler for this route exists anywhere in this repository.** The codex routes that do
  exist are `/api/codex` (`api/main.py:821`), `/api/codex/github-tree` (`:1648`),
  `/api/codex/upload` (`:1659`), and `/api/codex/personal` + `/api/me/codex`
  (`api/nodes.py`). There is no `categories` route.
- This is a **frontend↔backend contract mismatch**, not a backend outage: the backend is
  alive (root 200, `/api/tts/status` 200) and the route genuinely is not implemented.
- The caller degrades gracefully — `const catsData = catsRes.ok ? await catsRes.json() :
  { categories: [] };` — so the page renders fully, which §11.3 confirms.

Classified **EXPECTED_BENIGN** and recorded as *informational*, not as a failure. The
exemption is keyed to this one route string, and the harness test
`test_benign_exemption_does_not_mask_a_different_404` proves it is scoped: an unrelated 404
on the same host still fails. Without that control the exemption would be a blanket
suppression of every 404, which is exactly the "looks configured but does nothing" failure
mode this workstream has hit before.

The underlying mismatch is **not fixed here** — it is a product/API change outside Gate-2
hygiene scope. It is recorded as an open bounded item (SH-06 candidate) so it is not lost.

### 11.5 Harness teeth

`tests/test_gate2_browser_observation.py` — **14 passed**. It does not require a browser; it
proves the decision logic and the read-only property:

- anchor integrity (not stale, lowercase ASCII, provenance present, critical routes covered);
- negative controls: missing anchor, non-200, `pageerror`, failed request, and unexpected
  console error each produce `FAILED`;
- the benign exemption fires on the understood route and **does not** mask a different 404;
- `test_harness_is_read_only_and_credential_free` asserts the script contains no
  `Authorization` header and no `POST`/`PUT`/`PATCH`/`DELETE` and no `git push`/`git commit`.

### 11.6 Boundary classification after Pass 4

| Link | Pass 1 | Pass 2 | Pass 3 | Pass 4 |
| --- | --- | --- | --- | --- |
| main SHA | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| deployment SHA == main | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| deployment build observation | BLOCKED | BLOCKED | BLOCKED | **BLOCKED** (unchanged) |
| build↔source lineage | UNKNOWN | VERIFIED (newest) | VERIFIED (all 12) | VERIFIED |
| route resolves | UNKNOWN | source | source | **source + rendered** |
| alias→SHA binding | UNKNOWN | UNKNOWN | UNKNOWN (immaterial) | **UNKNOWN** (immaterial, not pursued) |
| **browser-rendered UI correctness** | UNKNOWN | UNKNOWN | UNKNOWN | **OBSERVED** |
| production acceptance | not claimed | not claimed | not claimed | **not claimed** |

**Parity is still NOT claimed.** What changed is that the last *self-closable* link moved
from `UNKNOWN` to `OBSERVED` against live production. The remaining non-`VERIFIED` links are:
the provider-bound deployment observation (`BLOCKED`, needs a Vercel credential per §6) and
the alias→SHA binding (`UNKNOWN`, immaterial per §10.1). Acceptance remains the sovereign's.

### 11.7 Reproduction

```
python scripts/gate2_browser_observation.py --node-path <NODE_PATH with playwright>
```

Read-only, stdlib-only Python driving Playwright/Chromium. Holds no credential. Exits `0`
only when every route is `OBSERVED`, `1` on any `FAILED`, and `2` when the browser dependency
is unavailable (classified `BLOCKED`, never silently passed).

## 12. Pass 5 — backend runtime observation: the third link of the chain

Passes 2–4 closed the chain on the *frontend*: the Vercel bundle's marker-set lineage
(§8, §10) and browser-rendered UI on six routes (§11). The Render service — the actual
application runtime, the Oracle spine, the TTS boundary, the API surface — had not been
observed at all. It is reachable without a credential, so the link

```
main SHA -> backend deployment -> backend runtime observation
```

is testable where the Vercel build-output link is not.

### 12.1 What was observed

| Observation | Value |
| --- | --- |
| main SHA | `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of #141, 2026-09-30 02:22:31 +0100) |
| backend host | `https://arkadia-kw64.onrender.com` |
| `/openapi.json` | HTTP 200, title `Arkadia Mind — Cycle 11`, version `0.1.0` |
| operations | 274 |
| schema digest | `d1797f9c38b5d707d0c7558de20aaa4d888954cd241e753ee4cb2c862b74e30b` |

Liveness floor — every probe answered anonymously with HTTP 200:

| Probe | Status | Bytes |
| --- | --- | --- |
| `/` | 200 | 40 |
| `/api/stellar-cartography` | 200 | 3786 |
| `/api/tts/status` | 200 | 284 |

Required prefixes, each carrying the feature that introduced it, were all present:
`/api/commune` (Oracle/ReasoMate chat spine), `/api/stellar-cartography`
(`kernel/stellar.py`), `/api/tts` (`kernel/tts.py`), `/api/echoes` (Echofeild →
SolSpire/Knowledge OS pipe). Missing: none.

### 12.2 Oracle power is measured, not assumed

A route-set oracle only changes when a route is added, removed, or re-pathed. Most
revisions in this repository differ only in handler bodies, so the oracle is expected to
be *undiscriminating* across them — and equality under an undiscriminating oracle is not
evidence of lineage.

This pass therefore measures discrimination against a negative control drawn from the
same repository. The previous pass recorded that the route-decorator count moved across
older revisions (`9ab26fc` 2 → `d3ead27` 149 → `d48ad0e` 171 → `df7a99a` 171 → `002b189`
171), so `2525811` was used as a candidate expected to differ.

| Revision | Signature digest |
| --- | --- |
| `main:002b189dd95e` | `d1797f9c…e30b` |
| `cand:df7a99a06738` | `d1797f9c…e30b` |
| `cand:2525811` | `846748380cde21badef4…` |

Distinct signatures: **2** ⇒ `discriminating: true`. The deployed schema is byte-identical
to `main`'s and to `df7a99a`'s, and is *separated* from `2525811`. That is the property the
frontend marker-set oracle could not demonstrate, and it is why this result is reported as
`VERIFIED` rather than `VERIFIED (undiscriminating)`.

`cd24bb1` — the P1-A boot-broken commit — failed to import and was **excluded** from the
comparison rather than counted as a distinct signature. A revision that cannot boot must
not be allowed to manufacture discrimination.

### 12.3 A defect found in this harness, and fixed

The first live run reported `/api/stellar-cartography` as a missing required prefix while
its own liveness probe returned HTTP 200 — a self-contradiction inside one report. The
cause: the prefix check read paths out of signature rows (`METHOD path :: summary :: tags`)
using `split(" ", 1)[1]`, which retains the ` :: summary` suffix, so *every* prefix looked
absent. Fixed to `split(" ", 2)[1]`, with a regression test
(`test_required_prefix_check_parses_paths_out_of_signature_rows`).

Recorded because the failure mode is instructive: the check failed *closed* (loudly wrong)
rather than *open* (silently passing), and it was the negative control — not the happy
path — that exposed it.

### 12.4 Boundary classification after this pass

| Link | After pass 5 |
| --- | --- |
| current main resolved | **VERIFIED** — `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| main → backend deployment identity | **UNKNOWN** — Render publishes no source SHA and no route exposes the deploy commit |
| backend runtime observation | **VERIFIED** |
| backend ↔ source lineage | **VERIFIED** — route-set oracle, discriminating (§12.2) |
| Vercel build observation | **BLOCKED** (unchanged — provider credential, §6) |
| Vercel build ↔ source lineage | **VERIFIED** (unchanged, §10) |
| browser-rendered UI | **OBSERVED** (unchanged, §11) |
| production acceptance | **NOT CLAIMED** (human authority) |

**Parity is still not claimed.** This pass closes the backend runtime link and adds the
discrimination the earlier oracle lacked. The one remaining self-closable gap is
`main → backend deployment identity`: Render exposes no deploy-commit record through any
surface reachable here, so that link stays `UNKNOWN` and is not inferred from schema
equality — equality is consistent with the deployed commit, it does not *identify* it.

### 12.5 Reproduction

```
python scripts/gate2_backend_observation.py --compare 2525811
python scripts/gate2_backend_observation.py --json --compare <rev> ...
python -m pytest tests/test_gate2_backend_observation.py -q   # 18 passed
```

Read-only, standard library only, holds no credential, performs no mutation. Import of a
candidate revision happens in a subprocess from a detached worktree, so the caller's
checkout is never disturbed and a non-importable revision is reported rather than fatal.

---

## 13. Pass 5 — branch reconciliation onto `09dd339`; prior claims re-measured

This branch was opened against `002b189`. `main` advanced to
`09dd339fc78b102f4eee1c232928639b60568bb2` (PR #156) while it was open, and the branch
became `CONFLICTING`/`DIRTY`. Passes 1–4 above were measured against `002b189`; their
boundary tables therefore do **not** automatically bind to the reconciled head. This section
records what was re-measured rather than carried forward.

**Rebase:** `git rebase origin/main`, pushed `--force-with-lease` (never plain `--force`).
One conflict, in `AGENTS.md`, where `main` had independently landed an encoding repair for
the same region. Resolved by normalising this branch's side through the cp866 pipeline — not
by a blanket `ours`/`theirs`. `main`'s repair is preserved verbatim; no superseded repair
reintroduced; no evidence or governance content discarded. Post-rebase: `0` Cyrillic
characters, `0` lines of `main`'s `AGENTS.md` missing, no duplicated sections.

### 13.1 Re-measured boundaries

| Boundary | Passes 1–4 (`002b189`) | Pass 5 (`09dd339`) |
| --- | --- | --- |
| current main resolved | VERIFIED | **VERIFIED** — `09dd339` |
| main → deployment identity | VERIFIED | **VERIFIED** — newest prod deployment `sha == main` |
| deployment build output observed | BLOCKED (SSO) | **BLOCKED** (unchanged, provider boundary) |
| alias reachable | VERIFIED | **VERIFIED** — HTTP 200 |
| alias → deployment SHA binding | UNKNOWN | **UNKNOWN** |
| build ↔ source lineage | VERIFIED | **UNKNOWN** — see §13.2 |
| browser-rendered UI correctness | OBSERVED | **BLOCKED** — see §13.3 |
| backend runtime observation | VERIFIED | **VERIFIED** — see §13.4 |
| production acceptance | NOT CLAIMED | **NOT CLAIMED** (human authority) |

### 13.2 build ↔ source lineage does not re-close at the new head

`last_build_input_commit` is now `4a9281be6b9a` (`Add Oracle response provenance`,
2026-10-01 16:18), which is **newer than the production deployment being inspected**
(`09dd339`, 2026-10-01 15:22). Not all candidate production SHAs are descendants of it, so
source-lineage closure is `false`.

The §8/§10 conclusion was sound *at `002b189`*, where every candidate shared the last
build-input commit. It does not transfer to `09dd339`, because the frontend source changed
after the deployment was produced. Recorded as `UNKNOWN`; not carried forward as `VERIFIED`.

### 13.3 browser link — BLOCKED in this sandbox, not converted to a pass

`playwright` is not installed, so `gate2_browser_observation.py` returns exit `2` with
`browser-rendered UI: BLOCKED`. Recorded as `BLOCKED`. The §11 anchors were independently
re-verified against the frontend tree, so the anchor list is not stale — the *instrument* is
missing, not the *anchor*. §11's `OBSERVED` result remains a real observation from when the
browser was available; it simply is not reproduced here.

### 13.4 backend link — a `CONTRADICTED` that was environmental

The first Pass 5 run reported `CONTRADICTED`, with four `/solspire/sources/*` routes present
only in the deployment. This was **not** a source divergence. The mount in `api/key_routes.py`
wraps the import in `try/except` and logs a warning, and `cryptography` was absent from this
sandbox, so `api/source_routes.py` failed to import locally. After installing `cryptography`:

```
ROUTE-SET ORACLE
  main:09dd339fc78b        359677ac7fa906d7e952
  distinct signatures: 1  => discriminating: False

  backend runtime observation      VERIFIED (undiscriminating)
  backend <-> source lineage       VERIFIED (undiscriminating) -- route-set oracle
```

The local route set then matches the deployment exactly. Worth recording as a harness
property: a conditional mount can make a *local* environment deficit look like a deployed
divergence, and the oracle's own classification is what caught it. The
`main → backend deployment identity` link remains `UNKNOWN` — Render publishes no deploy
commit, and schema equality is consistent with the deployed commit without identifying it.

### 13.5 An observation on the deployed artifact, outside the parity chain

The production alias serves a bundle containing the **unrepaired** CapabilityChamber state —
the live counterpart of the defect addressed by PR #166:

```
GET https://arkadia-prism.vercel.app/assets/index-teAQHdtX.js   (825,082 bytes)
  "surfaceMeta" present            1   <- unresolved global; main declares it nowhere
  "activity-runtime-draft" present 0   <- ActivityRuntime absent from the artifact
```

`main` declares `surfaceMeta` nowhere, so the minifier emits the identifier verbatim; a
declared `const` is renamed and disappears. Same discriminator used to verify #166.

This is an **observation**, not a parity claim. The alias→SHA binding is unobserved, the
deployment build output is `BLOCKED`, and this section does not convert either.

### 13.6 Reproduction

```
python scripts/gate2_production_observation.py
python scripts/gate2_backend_observation.py
python scripts/gate2_browser_observation.py     # exit 2 if playwright absent
python -m pytest tests/test_gate2_production_observation.py \
                 tests/test_gate2_backend_observation.py \
                 tests/test_gate2_browser_observation.py -q
```

Read-only; standard library only; holds no credential; performs no mutation.
