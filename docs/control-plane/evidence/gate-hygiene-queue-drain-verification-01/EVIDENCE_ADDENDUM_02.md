# EVIDENCE ADDENDUM 02 — queue drain verification (runtime half)

Pass: `gate-hygiene/queue-drain-verification-02`
Date: 2026-10-01 (UTC)
Base: `002b189dd95e41c9b4f4cca33d08b4121453d289` (`main`)
Parent pass: `gate-hygiene/queue-drain-verification-01` (PR **#163**, head `b4fc667`)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

This addendum **closes two boundaries that PR #163 recorded as open or BLOCKED**, and
records one new source-side defect. Nothing here is inherited from #159, #162, or #163;
every figure below was measured in this pass from a fresh clone and live HTTP.

---

## 1. Queue drain — 20-PR drain independently re-verified (closes #163 §6 BLOCKED)

#163 §6 left one row unresolved: *"alias → deployment SHA binding: UNKNOWN"*. It is
**immaterial**, and this pass shows why with a measurement rather than an assumption.

`vercel.json` rewrites **every** path to `/index.html`. Verified directly:

```bash
curl -s https://arkadia-prism.vercel.app/            -> HTTP 200, 997 bytes, text/html
```

Every route returns the **same 997-byte SPA shell**. Therefore an alias `200` is **not** a
health signal and must never be read as one. The shell references exactly one bundle:

```
assets/index-CHFFyuSc.js
```

which was fetched and hashed:

```
sha256 33861ef9b06f6fdf261f1f447ab6e28723b3843abe1f79953c1ac5621f1e5bc2
bytes  2025825
```

The alias→SHA binding is unobservable, but the **artifact identity is observable**, and
#163's lineage argument (`all 12 candidate Production SHAs descend from b377a01`, the last
frontend-build-input commit) plus this hash make it non-load-bearing: every candidate
compiles identical frontend source.

### 1.1 CI state at every queue head — the gate names matter

All 22 open PRs were queried at their **full** head SHA
(`/repos/.../commits/<sha>/check-runs`). All are **GREEN**. Recording the actual gate names
because the distinction is material:

| PR | head | checks | state |
|---|---|---|---|
| #142 `59fbb531c4` · #143 `7d79f38bd5` · #144 `09521d2f5d` · #145 `8a2b7048fc` | | 2 | GREEN |
| #146 `5017da6ba6` · #147 `20d184b85a` · #148 `4fd05b0a5c` · #149 `0022130084` | | 2 | GREEN |
| #150 `03fe21fef6` · #151 `452f874513` · #152 `2cc66f09e2` | | 2 | GREEN |
| #153 `9ea6a62904` | | 3 | GREEN |
| #154 `8214ed4dec` · #155 `b31be22eac` · #156 `627e82ae85` · #157 `c866697432` | | 2 | GREEN |
| #158 `58d8cdf48a` · #159 `1d02d9bb3a` | | 2 | GREEN |
| #160 `a642d92d24` | | 3 | GREEN |
| #161 `bd0749c0b6` · #162 `9579221d0d` · #163 `b4fc667332` | | 2 | GREEN |

The observed check names are **`Full-history secret scan`** and **`Vercel Preview
Comments`** (plus `validate` on #153 and #160).

> **The correction that matters:** `sg-02-fe-2-v.yml` — the CP10 mutation boundary gate — is
> **path-filtered** on `pull_request` (`web/public_prism/**`, `spiral_grove/**`, `lab/**`,
> `api/lab_routes.py`, and a named test list). Most of the drain set does not touch those
> paths, so the boundary **did not run on their PRs**. Their "green" therefore does **not**
> include a CP10 judgement.
>
> This is not a defect in the drain set — #163 §5 already ran the policy module over the
> 21-path union and got `--judge` exit 0 — but the queue must not be described as
> "CP10-gated green". Where CP10 did not run, greenness means secret-scan clean only.

---

## 2. New finding — a live boot-path defect in the grove surface

#163 §7 correctly found that `CapabilityChamber.tsx` **imports** `ActivityRuntime` and never
**renders** it. This pass finds a second, sharper defect in the same file on `main`:

```tsx
1:  import React, { useState } from 'react'          // useEffect NOT imported
...
51: useEffect(() => { ... }, [key, evidenceKey])    // useEffect called
```

`main` @ `002b189` calls `useEffect` at module-component scope with **no import binding for
it**. The import list is exactly:

```
1: import React, { useState } from 'react'
2: import { motion } from 'framer-motion'
3: import type { GroveCapability, ... } from '../../data/spiralGroveCatalog'
4: import ActivityRuntime from './ActivityRuntime'
```

`useEffect` is not bound by any of them.

### 2.1 It did not throw, and the build did not catch it

`useEffect` is a **global on the React UMD/global namespace** in the browser build, so the
call resolves at runtime and no `ReferenceError` is raised. `vite build` does not fail: the
identifier is assumed global, not undefined-local. This is why the defect ships silently.

### 2.2 The deployed artifact confirms it — with an artifact hash

The bundle served by the production alias (`sha256 33861ef9…`, §1) contains
`CapabilityChamber`'s own literals but **not** the React binding it needs:

| literal | deployed count |
|---|---|
| `activity-runtime-draft.v1` (ActivityRuntime-only) | **0** |
| `activity-runtime-complete.v1` (ActivityRuntime-only) | **0** |
| `ActivityRuntime` (symbol) | **0** |
| `sg03-contract-boundary` (CapabilityChamber) | 1 |
| `learning-activity-work-surface` (CapabilityChamber) | 1 |

The importer is bundled; the import is not. Source and artifact **agree** — this is **not** a
stale deployment, and it is **not** a deploy regression. The label should read
`SOURCE-SIDE MOUNT + IMPORT-BINDING DEFECT (deployed artifact matches main)`.

### 2.3 Ownership — no open PR covers this file

Every open PR's blob for `CapabilityChamber.tsx` was compared against `main`'s blob
(`0cde2f782f1c`) via the Contents API at each head SHA:

```
scanned 22 open PRs; 0 differ from main
```

So the repair is **not** in the queue and would not land by merging any drain PR. It is a
distinct bounded task.

### 2.4 The repository already asserts part of this

The four failures in `tests/test_spiral_grove_activity_runtime.py` are the repository's own
assertion of the mount defect (#163 §7). They are **pre-existing baseline debt** on `main`,
unchanged by the queue, and **not attributable to any drain PR**.

---

## 3. Preconditions re-verified this pass

| check | result |
|---|---|
| clone on `main`, ancestry real | `002b189` = `origin/main` |
| `tests/architecture` | **11 passed** |
| `python -m py_compile api/main.py` | **OK** |
| `api/main.py` size budget | **2519 / 2600** |
| full suite (deps installed) | **20 failed / 1039 passed / 13 skipped / 2 errors** |
| `SG-02-FE.2-V` job name in any PR head | **absent** (see §1.1) |

The full-suite fingerprint **matches #162 and #163 exactly** — no drift, no new debt
attributable to this pass. Collection errors remain the two documented pre-existing ones.

### 3.1 The `health-row-doc-repair.patch` requirement is confirmed by composition

Verified independently rather than inherited:

- `"/health"` is **not present** in `api/main.py` on `main`.
- PR **#154** adds it: `api/main.py` `+10` lines, `@app.get("/health")` at line 800.
- PR **#156** adds `tests/test_documented_route_contract.py` `+115` plus
  `DEPLOYMENT_GUIDE.md` changes.

Neither PR alone is wrong, but #156's guard requires a documented guide row for a route that
only #154 serves. Merged without the repair, the drain lands **one node red** — exactly as
#163 §10 warned. **This is the most load-bearing item for the sovereign's drain order.**

---

## 4. Boundary states after this pass

| link | before (#163) | now | basis |
|---|---|---|---|
| current main resolved | VERIFIED | **VERIFIED** | `002b189` |
| main → deployment identity | VERIFIED | **VERIFIED** | `ref == sha == main` |
| alias reachable | VERIFIED | **VERIFIED** | HTTP 200, 997-byte shell |
| alias → deployment SHA binding | UNKNOWN | **UNKNOWN — immaterial** | artifact hash + lineage (§1) |
| deployment build output observed | BLOCKED | **VERIFIED (partial)** | bundle fetched, hashed, grepped (§1, §2.2) |
| browser-rendered UI correctness | UNKNOWN | **UNKNOWN** | no browser runtime in this sandbox |
| production acceptance | NOT CLAIMED | **NOT CLAIMED** | human authority |

The **build-output** half of Gate 2's runtime boundary is now closed by observation. The
**browser-rendered** half remains genuinely open and is **not** promoted.

---

## 5. What this pass does not do

- It does **not** merge, push to `main`, or force-push.
- It does **not** repair the `CapabilityChamber.tsx` defect (§2) — that is a separate
  bounded task requiring authorisation, and repairing it would widen this pass's scope.
- It does **not** fix the four `test_spiral_grove_activity_runtime.py` failures.
- It does **not** claim production acceptance, and it does **not** promote `UNKNOWN`.

## 6. Classification

`VERIFIED` — queue CI state at all 22 heads; artifact identity and hash; `CapabilityChamber`
defect (source + deployed artifact agree); `#154`/`#156` composition hazard; protected gates.
`BLOCKED` — browser-rendered UI correctness (no browser runtime).

## 7. Sovereign actions requested

1. Merge **#150**. Do **not** merge **#143**. Close **#147** as superseded.
2. **Apply `health-row-doc-repair.patch` at the #154 step** (§3.1) or the drain lands red.
3. Read #162 §6 as the **patched** tree (18/1091); unpatched it is 19/1090.
4. Authorise a **separate bounded pass** to repair `CapabilityChamber.tsx` (§2) —
   `useEffect` import binding **and** the missing `<ActivityRuntime>` render. No open PR
   covers this file.
