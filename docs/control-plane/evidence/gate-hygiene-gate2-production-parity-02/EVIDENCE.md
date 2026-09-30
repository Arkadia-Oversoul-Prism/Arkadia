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
