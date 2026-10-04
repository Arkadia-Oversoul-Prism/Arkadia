# EVIDENCE — gate-hygiene/post-merge-verification-05

Bounded objective: re-derive, from live evidence, whether the `main` movement that
followed the sovereign merge of PRs **#262–#266** is behaviour-preserving, and record
what that movement did to the Gate-2 production-parity boundary.

This pass is **evidence only**. No source, test, or policy change. No merge. No push to
`main`.

## 1. Provenance

| Item | Value |
| --- | --- |
| Repository | `Arkadia-Oversoul-Prism/Arkadia` |
| Observation time (UTC) | 2026-10-04T21:06–21:40 |
| BASE_MAIN (previous pass) | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| MERGED_MAIN (this pass) | `296d741b838a33c18f25cbd898dea3792c23cc9b` |
| LIVE_MAIN (this pass) | `ca67b006e57c0247d1db0f9d337ed34cc0a51cce` |
| Branch | `gate-hygiene/post-merge-verification-05` @ `ca67b006e57c` |
| Working tree at branch point | clean (`git status --porcelain` empty) |

`origin/main` was re-fetched during the pass. `main` advanced **6 commits** past
BASE_MAIN: 5 merge commits (#262–#266) plus 5 direct pushes of MIE/Prism work.

### Merge commits landed (all parents verified via API)

| Merge | SHA | First parent |
| --- | --- | --- |
| #262 | `fe24ecd80f11` | `1b7c089f` |
| #263 | `13de2c29df49` | `fe24ecd8` |
| #264 | `55284d361e8e` | `13de2c29` |
| #265 | `87f936332a2c` | `55284d36` |
| #266 | `296d741b838a` | `87f93633` |

The chain is linear and each merge's first parent is the previous merge — the cluster
landed in the documented order, so the PR #267 evidence (`base 1b7c089`) remains bound
to a real ancestor of live main.

## 2. Baseline test-debt fingerprint (node set unchanged)

Full suite, `-q -rEf --continue-on-collection-errors`, `PYTHONPATH=<repo>/archive/legacy_python`:

| Tree | Result | Nodes |
| --- | --- | --- |
| `1b7c089` (BASE_MAIN) | 9 failed, 1413 passed, 21 skipped, 1 error | 10 |
| `296d741` (MERGED_MAIN) | 9 failed, 1422 passed, 21 skipped, 1 error | 10 |
| `ca67b00` (LIVE_MAIN) | 9 failed, 1422 passed, 21 skipped, 1 error | 10 |

```
outcomes fingerprint: 9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38
ids fingerprint     : 124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f
```

Node-set comparison, by identity (never by count):

- `296d741` vs `ca67b00` — **identical** (`True`)
- `1b7c089` vs `ca67b00` — **identical** (`True`); added `[]`, removed `[]`

**Classification: no regression introduced by the post-merge movement.** The passed
count rose 1413 → 1422 (+9) because the merged cluster's own guard tests are now
collected; the failing/error node set is unchanged.

## 3. Merged-cluster guard nodes are collected and pass

Collected-ID diff of exactly **+9 / -0** (matches the PR #267 prediction: #263×3,
#264×1, #265×5). All nine nodes were confirmed present in `--collect-only` at
`ca67b00`, and the guard files pass in isolation:

```
tests/test_gate2_production_observation.py
tests/test_nodes_composition_seam.py
tests/test_baseline_fingerprint.py
-> 47 passed
```

## 4. Protected surfaces

| Surface | Result |
| --- | --- |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line budget | 2582 / 2600 |
| `pytest tests/architecture -q` | **11 passed** (11/11) |
| `pytest tests/test_m02a_ci_gate_integrity.py -q` | **55 passed** (CP10 policy vs live tracked corpus) |
| CP10 judge on the new evidence paths | PASS (exit 0) |

## 5. Gate-2 production-parity boundary — two links flipped

`python scripts/gate2_production_observation.py --json` at `ca67b00`:

| Boundary | PR #267 (at `296d741`) | This pass (at `ca67b00`) |
| --- | --- | --- |
| current main resolved | VERIFIED | VERIFIED |
| **main → deployment identity** | **STALE** | **VERIFIED** |
| deployment build output observed | BLOCKED | BLOCKED |
| alias reachable | VERIFIED | VERIFIED |
| alias → deployment SHA binding | UNKNOWN | UNKNOWN |
| build ↔ source lineage | VERIFIED | **UNKNOWN** |
| browser-rendered UI correctness | UNKNOWN | UNKNOWN |
| production acceptance | NOT CLAIMED | NOT CLAIMED |

**`main → deployment identity` is now VERIFIED.** The newest Production deployment is
`id=6847041502`, `sha=ref=ca67b006e57c0247d1db0f9d337ed34cc0a51cce`, state `success`,
created `2026-10-04T21:34:49Z` — i.e. a Production build exists at the exact live main
SHA. The blocker PR #267 recorded is closed by a deployment, as predicted.

**`build ↔ source lineage` moved VERIFIED → UNKNOWN, and this is a corrected
over-claim, not a regression.** The classifier at
`scripts/gate2_production_observation.py:160-176` requires *every* candidate Production
SHA to be a descendant of `last_build_input_commit()`. That helper resolves with
`git log -1 --format=… -- <BUILD_INPUTS>`, and its first record at `ca67b00` is the
**newest** build-input commit, `ca67b006e57c` itself ("fix(mie): bind history repeat
control"). A commit cannot be a strict ancestor of itself, so `ca67b00` reports
`descendant=False` and closure is `False`. The script then appends
`"UNKNOWN (immaterial: all candidates share frontend source)"`, so the flip is a
property of the classifier at a main tip that *is* the last build input — the older
`VERIFIED` reading was produced when the last build input was an earlier commit.

## 6. MIE/Prism direct-push commits — behaviour-preservation check

`296d741..ca67b00` changed only frontend and docs paths (no `tests/`, `api/`, `weaver/`,
`kernel/`, `knowledge/`):

```
web/public_prism/src/pages/MusicalIntentionEngine.tsx
web/public_prism/public/mie-lab/index.html
web/console/src/components/Layout.tsx
```

CI on the direct pushes (runs API, `branch=main`): each of `e3b89f2`, `58b981d`,
`a5adf9f`, `0eae7f0`, `ca67b00` triggered **`SG-02-FE.2-V` = success** and
`security-secret-scan` = success. `SG-02-FE.2-V` is path-filtered on
`web/public_prism/**`, which the MIE commits touch, so the CP10 mutation boundary **was
enforced** on these pushes despite being direct pushes to `main`.

### Finding (classified, not executed): the MIE React page is orphaned

- `web/public_prism/src/pages/MusicalIntentionEngine.tsx` exists but **nothing imports
  it** — `git grep -n "MusicalIntentionEngine" ca67b00` returns only its own
  declaration line; `git log --all -S "MusicalIntentionEngine" -- web/public_prism/src`
  returns only `58b981d`. There is no `import.meta.glob` registry.
- The live alias bundle `assets/index-DjdkOyYh.js` (fetched from
  `https://arkadia-prism.vercel.app/`) contains **0** occurrences of `mie-lab`,
  `MusicalIntentionEngine`, `Musical Intention Engine`, `musical-intention`, and
  `Prism Web Lab`, while SG-03/SG-04 controls remain present
  (`opportunity-radar` → 3, `activity-runtime-draft.v1:` → 1).
- The static route **is** live and reachable: `GET https://arkadia-prism.vercel.app/mie-lab/`
  → **HTTP 200**, `text/html`, `<title>ARKADIA · Musical Intention Engine</title>`,
  served from `web/public_prism/public/mie-lab/index.html` (Vite copies `public/` verbatim).

Conclusion: the reachable MIE surface is the static `public/mie-lab/` page. The TSX page
is dead code. This is recorded as a **classified finding**, deliberately not repaired
here (no-scope-expansion rule). Proposed, not executed:
`feat/mie-react-page-route-01`.

## 7. Open PR inventory at live main

| PR | Head | Base | Mergeable | State | Scope |
| --- | --- | --- | --- | --- | --- |
| #268 | `ab427481d40f` | `296d741` | **true** | unstable | docs only (`+100` `OVERNIGHT-BUILD.md`) |
| #267 | `51b0a3f42e84` | `296d741` | **true** | unstable | evidence only (`+230`, 2 files) |

Both bases are ancestors of live main, so neither is a semantic conflict; both are
`mergeable=true` with `Full-history secret scan` = success. `state=unstable` reflects
only the Vercel preview comments check, which reports `success`.

## 8. Classification

- Repository work: **VERIFIED** — no regression; protected surfaces green; the
  merged cluster is present and its guards pass.
- Gate-2 `main → deployment identity`: **VERIFIED**.
- Gate-2 `deployment build output observed`: **BLOCKED** — the deployment-specific URL
  `https://arkadia-prism-pe0tgtrdh-arkadia-prism.vercel.app/mie-lab/` → **302** to
  `vercel.com/sso-api` (Vercel Deployment Protection). Unchanged boundary.
- Gate-2 `build ↔ source lineage`: **UNKNOWN** — classifier artifact at a main tip that
  is itself the last build-input commit (§5). Not a regression.
- `production acceptance`: **NOT CLAIMED** — human authority.

## 9. Authorization boundary

- No merge. No push to `main`. No force-push. No baseline-debt repair.
- The MIE orphaned-page finding is **proposed, not executed**.
- Sovereign action available: review/merge **#267** and **#268**.

## 10. Completion condition

This evidence PR is reviewed and merged by the sovereign. Next heartbeat reconstructs
from live evidence, re-derives the fingerprint, and confirms the node set is unchanged.
