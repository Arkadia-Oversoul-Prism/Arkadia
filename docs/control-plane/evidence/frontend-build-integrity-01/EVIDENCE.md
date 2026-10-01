# Frontend build integrity — the canonical Vite config was shadowed and unbuildable

Workstream: GATE-00 / gate-hygiene (pre-gate engineering envelope)
Branch: `gate-hygiene/frontend-build-verification-01`
Base: `002b189` (merge of PR #141)
Status: IMPLEMENTED — build proven, architecture green, no regression. Sovereign review required.

## 1. What was believed

Repo memory (`AGENTS.md`) recorded: *"`vite build` is environment-blocked (no npm registry
access), so changes are inspection-verified only unless the sandbox has `node_modules`."*

This pass disproves the blocker and, in doing so, surfaces a defect the blocker was hiding.

## 2. Registry probe — the blocker is not real

```
$ curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://registry.npmjs.org/
200 0.08s
```

`pnpm install` and `pnpm build` both complete. The "environment-blocked" claim is stale.

## 3. The defect: `vite.config.js` shadows `vite.config.ts`

`web/public_prism/` tracks **two** Vite configs. Vite resolves config file extensions in the
order `.js` → `.mjs` → `.ts` → … (`DEFAULT_CONFIG_FILES`), so the tracked `vite.config.js`
**wins** and `vite.config.ts` is never read.

The two files are divergent. `vite.config.ts` carries the real build configuration —
`chunkSizeWarningLimit: 2000` and `manualChunks` vendor splitting; `vite.config.js` carries a
bare config with none of it.

The loser is the file Vite actually reads, and it is the *less* capable one.

### 3.1 Consequence — every build silently bypassed vendor chunking

The `dist/` in the working tree at pass start was a single 1,939 kB `index-*.js` with **no
vendor chunks at all** — the fingerprint of a build that ran under `vite.config.js`. Nothing
in the repository recorded that the intended config was dead.

### 3.2 The canonical config was itself unbuildable

Fixing the shadow alone is not sufficient. With `vite.config.js` removed, the build **fails**:

```
✓ 3438 modules transformed.
x Build failed in 6.20s
[commonjs--resolver] Failed to resolve entry for package "firebase".
The package may have incorrect main/module/exports specified in its package.json:
Missing "." specifier in "firebase" package
```

Root cause, verified against the installed package rather than assumed:

```
$ python3 -c "import json;d=json.load(open('node_modules/firebase/package.json'));print(d['version'],d.get('main'),list(d['exports'])[:4])"
12.16.0 None ['./analytics', './app', './auth', ...]
```

Firebase 12.x removed the root `"."` export and exposes only subpaths. `manualChunks` named
the bare specifier `"firebase"`, which can no longer resolve. Application code imports
`firebase/app`, `firebase/auth`, `firebase/firestore` — never the root.

Both defects had to be fixed together: removing the shadow exposes an unbuildable canonical
config, and repairing the canonical config is invisible while the shadow exists.

## 4. The change

| File | Change |
|---|---|
| `web/public_prism/vite.config.ts` | `"vendor-firebase": ["firebase"]` -> `["firebase/app", "firebase/auth", "firebase/firestore"]` |
| `web/public_prism/vite.config.js` | **deleted** — shadowed the canonical config |
| `web/public_prism/dist/index.html` | **deleted** — stale orphan, see §5 |
| `web/public_prism/vite.config.js.timestamp-*.mjs` | **deleted** — Vite's generated config shadow, see §6 |
| `web/public_prism/.gitignore` | ignore `vite.config.js.timestamp-*.mjs` |

## 5. `dist/index.html` was a broken pointer

`dist/index.html` was tracked while the bundle files it references were not:

```
$ git show HEAD:web/public_prism/dist/index.html | grep -oE 'assets/[A-Za-z0-9.-]+\.(js|css)'
assets/index-CStL2fKK.js
assets/index-BdjOfkks.css
$ git ls-files --error-unmatch web/public_prism/dist/assets/index-CStL2fKK.js
MISSING assets/index-CStL2fKK.js
MISSING assets/index-BdjOfkks.css
```

Both referenced assets are absent from the tree. The tracked file was a permanently broken
pointer to bundles that do not exist. It is also **already ignored** — the nested
`web/public_prism/.gitignore` line 2 is `dist/`, so the file could only have entered the tree
via a force-add.

Verified that nothing depends on it being in version control:
- `grep -rn "public_prism/dist" tests/` -> no matches
- `api/main.py:384` mounts `../static`, not `dist`
- `scripts/serve-gate.sh` serves the repo root for the Gate UI
- both `vercel.json` files declare `outputDirectory` and build it at deploy time

## 6. The timestamp shadow

`web/public_prism/vite.config.js.timestamp-1782984120975-51bd045e4144f.mjs` is Vite's
generated config shadow. Its own first line is `// vite.config.js` and it imports from
absolute `file:///home/runner/workspace/...` paths — a dev-container artifact that cannot
resolve anywhere else. A generated file sitting in a `.js`-ordered slot is a live hazard for
the same reason as §3, so it is now ignored.

## 7. Evidence

### 7.1 Build — canonical config, clean tree

```
$ cd web/public_prism && rm -rf dist && pnpm build
vite v5.4.21 building for production...
✓ 3438 modules transformed.
dist/index.html                             1.33 kB │ gzip:   0.61 kB
dist/assets/index-C2whHMVB.css             85.72 kB │ gzip:  16.15 kB
dist/assets/vendor-react-r_h-a3X5.js        0.08 kB │ gzip:   0.08 kB
dist/assets/ProjectOverview-WP5gyuZp.js     4.89 kB │ gzip:   1.64 kB
dist/assets/ProjectDashboard-vDMBZf3p.js   58.71 kB │ gzip:  14.13 kB
dist/assets/vendor-d3-CVfkS1ff.js         114.12 kB │ gzip:  37.75 kB
dist/assets/vendor-motion-BjZNH5Hw.js     137.11 kB │ gzip:  45.26 kB
dist/assets/vendor-firebase-DT8xquho.js   427.79 kB │ gzip: 113.71 kB
dist/assets/vendor-recharts-C6lrG4n3.js   433.62 kB │ gzip: 128.12 kB
dist/assets/index-Dy4iXaHY.js             820.85 kB │ gzip: 223.98 kB
✓ built in 7.11s
BUILD_EXIT=0
```

Vendor chunking is now real, and the entry bundle drops **1,939.32 kB -> 820.85 kB**
(-58%). Firebase, recharts, d3 and framer-motion are split into separately cacheable
chunks instead of being inlined into one monolith.

### 7.2 Regression — full-suite fingerprint unchanged

```
$ PYTHONPATH=archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
20 failed, 1041 passed, 11 skipped, 2 warnings, 2 errors in 110.71s
```

Identical to the fingerprint captured before any mutation this pass. **Zero new failures.**
The 22 failing nodes (20 failed + 2 collection errors) are pre-existing baseline debt and are
attributed to nothing in this change.

### 7.3 Architecture fitness

```
$ python -m pytest tests/architecture -q
11 passed in 1.73s
```

Note: the task contract states "expect 10/10". Live evidence is 11 tests. The contract's
count is stale; live evidence wins.

### 7.4 CP10 mutation boundary

```
$ git diff --name-only HEAD | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
CP10_EXIT=0
```

## 8. Remaining uncertainty

- **`optimizeDeps.include` names an absent package.** `vite.config.ts` lists `es-toolkit` and
  `es-toolkit/compat`, but `es-toolkit` is not in `package.json` and `grep -rl es-toolkit src/`
  returns nothing. Harmless today (dev-only pre-bundling of an unimported package), but it is
  dead configuration. **Not fixed** — out of the bounded scope, recorded here for a future pass.
- **Duplicate lockfiles.** Both `package-lock.json` and `pnpm-lock.yaml` are tracked. The
  package manager is pinned to pnpm via `packageManager`, and both `vercel.json` files use
  `pnpm install --frozen-lockfile`, so the npm lockfile is unused. **Not fixed** — removal
  would be a separate bounded decision.
- **`AGENTS.md` stale claims.** Line 220's "environment-blocked" statement and the stale
  "10/10" architecture count are now contradicted by evidence. **Not fixed here** — PR #150
  rewrites the whole file and PRs #143/#147/#151/#152/#155 are adjudicating it; editing it
  from this branch would collide with an in-flight workstream.

## 9. Authority boundary

Deletion of tracked files and a build-config repair. No merge, no push to `main`, no
governance, identity, or authority-path change. **Sovereign merge required.**
