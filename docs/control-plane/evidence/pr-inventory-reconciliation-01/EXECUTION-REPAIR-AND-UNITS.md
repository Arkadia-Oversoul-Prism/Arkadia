# Bounded repair and validation — execution record

**Frozen base:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (unchanged throughout)
**Authority:** bounded repair + validation only. No merge, push, deploy, close, or retarget.
**Executed:** 2026-10-15

Three resolution commits were produced on isolated local branches. **None is pushed**
(`git branch -r --contains <sha>` → empty for all three). They exist for the acceptance
decision, not as landed changes.

| Unit | Branch | Resolution commit | Sources |
|---|---|---|---|
| #482 repair | `gate10/history-depth-repair-01` | `c770df2021226331fb31f10e833462f2bd43d1fb` | #482 `0cc7c9e7` |
| #497 + #505 | `ui/alias-families-union-01` | `53f5ac6144857616f487bb4e32c5a08b71bbc525` | `a14d3fa9` + `8cb030c0` |
| #511 + #514 | `ui/return-to-error-boundary-01` | `e679c3bb4ba0343dcef555f36eb36c4ca0e15d38` | `7af66444` + `e48cbf26` |

---

## 1. #482 — history-depth repair

**True diff** (`merge-base ee684fff` → `0cc7c9e7`, +987/-0): `provider-routing.yml` +22,
`AGENTS.md` +72, `docs/…/gate10-history-depth-ci-wiring-01/EVIDENCE.md` +346,
`tests/test_history_depth_ci_wiring.py` +547. `provider-routing.yml` is byte-identical between
#482's base `ee684fff` and `main` `7580bd8f`, so the patch applies without adaptation.

| Check | Command | Result |
|---|---|---|
| Guard suite | `pytest -q tests/test_history_depth_ci_wiring.py` | **17 passed** |
| Adjudication, full clone | `pytest -q tests/test_agents_md_encoding_adjudication.py` | **21 passed, 2 skipped** |
| **Shallow clone (CI condition)** | `git clone --depth 1` then the same file | **4 failed, 13 passed, 6 skipped** |
| **Same clone, `git fetch --unshallow`** | the same file | **18 passed, 5 skipped** |
| Negative control | remove `fetch-depth: 0` → guard | **1 failed, 16 passed** (`…fetches_full_history[provider-routing.yml]`) |
| Restore | `git checkout --` → guard | **17 passed**; md5 matches #482's blob (`3ad90109…`) |
| Full gate | `pytest tests/ -q -rEf --continue-on-collection-errors` | **8 failed, 3125 passed, 17 skipped, 1 error** |
| Baseline (same command, `7580bd8f`) | — | **8 failed, 3108 passed, 17 skipped, 1 error** |

**Node-set comparison.** The failing/error node *set* is **identical** on both trees —
9 nodes, `sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b` for each;
`comm -3` is empty. The `+17 passed` is exactly the new guard file.

**Why the local node set does not show the 4 adjudication nodes.** This workspace is a **full**
clone (`git rev-parse --is-shallow-repository` → `false`), so the oracle revision resolves and
those nodes pass locally *on the unpatched baseline too*. The defect is only visible under a
shallow checkout, which is what CI does. It was therefore reproduced directly:

```
shallow clone,  main tree            → 4 failed, 13 passed, 6 skipped
same tree,      git fetch --unshallow → 18 passed, 5 skipped
```

This is the decisive evidence for the repair: the failure is clone depth, and full history
resolves it. The local-vs-CI node-set delta is a *measurement environment* difference, not a
repository difference.

**AGENTS.md constraint.** The 72-line addition is insertion-only —
`scripts/agents_md_encoding_audit.py` → `insertions-only inserted=1415 alterations=0
reproduced=True`, Cyrillic `0 -> 0`. No oracle-carried line was rewritten.

## 2. #497 + #505 — alias-family union

Conflict: `tests/test_console_shell_nav_contract.py` (both append to one alias list);
`router.ts` merges cleanly. Resolution: **union of both alias lists**, no assertion weakened.
Measured **38 passed**.

## 3. #511 + #514 — return-to + error boundary

Conflict: `web/arkadia_console/src/App.tsx` `Shell` render. Not an ancestor chain
(`git merge-base --is-ancestor 7af66444 e48cbf26` → false). Resolution: keep #511's
`onNavigate={handleNavigate}` **and** wrap the body in #514's `ErrorBoundary` keyed by surface.
Measured **38 passed** across the three suites.

Frontend production build: **success** — `dist/assets/index-CtN--z6-.js` 129.84 kB
(gzip 33.77). Bundle markers present: `surface-error-boundary`, `surface-error-message`,
`surface-error-reload`, `surface-error-home`, `arkadia.returnTo` (1 occurrence each).
Negative control: a build of **`main`** produces `index-CDg7ghfL.js` with **0** occurrences of
each — so the markers discriminate the change, and the bundle is not a stale artifact.

## 4. #525 — capability deliverability experiment

#525's true diff (`merge-base 3ca8582ab3cb` → `daef33c4`, +154): `LabWorkLoop.tsx` +59,
`tests/test_prism_w4_lab_read_model.py` +92, `WeaverPage.tsx` +3. (Its PR base is
`3ca8582ab3cb`, an ancestor of `main` — **not** `49809f45` as earlier recorded.)

Four arrangements were built and measured:

| # | Arrangement | `ExecutionLoop` render sites | render-integrity | #525's own tests |
|---|---|---|---|---|
| A | `main` (status quo) | 1 (`EngineeringLabPage`) | **7 passed** | 6 failed, 32 passed |
| B | #525 as authored | **2** (+`LabWorkLoop`) | **1 failed, 6 passed** | — |
| C | `LabWorkLoop` as sole render site, mounted twice | 1 (`LabWorkLoop`) | **3 failed, 4 passed** | — |
| D | Weaver read model renders its own list; `ExecutionLoop` stays on the Lab page | **1** (`EngineeringLabPage`) | **7 passed** | **38 passed** |

**Arrangement D is a genuine result and a genuine caveat.** It shows the *capability*
(a canonical work-loop projection on the Weaver surface, hydrated from
`endpoints.labEngineeringOverview`) can coexist with exactly one `ExecutionLoop` mount. Both
suites pass simultaneously: 7 passed and 38 passed.

It is **not** a drop-in resolution, and must not be presented as one:

- D re-implements the stage list inline instead of reusing `ExecutionLoop`; that duplicates
  presentation that #525 intended to share. Whether that duplication is acceptable is a design
  call, not a mechanical one.
- #525's `test_recovered_capability_is_no_longer_orphaned` asserts `ExecutionLoop` is imported
  by *some* module. On `main` it passes (the Lab page imports it); in D it also passes for the
  same reason. D satisfies the letter of that guard without D being why it holds.
- D was measured in a scratch worktree. It is **not** committed, and no branch carries it.

So the honest statement is: **the hold is not proven permanent — a single-mount delivery looks
reachable — but it is also not proven correct.** Arrangement C's failure (3 failed) shows that
naively centralising the render site is *worse*, because two tests pin the Lab page as the
canonical consumer. The capability gap and the invariant can plausibly both be satisfied, but
only by a deliberate re-authoring that the sovereign should review. **Hold stands.**

## 5. #501 / #503 — closure records

| Artifact | `main` `7580bd8f` | #535 `8b6eadd7` | #501 `31d66332` |
|---|---|---|---|
| `docs/…/prism-w4-canonical-loop-mount-01/EVIDENCE.md` | ABSENT | ABSENT | PRESENT |
| `tests/test_prism_w4_canonical_loop_mount.py` | PRESENT | PRESENT | PRESENT |

#501's mount code and its test are on `main`; only the 84-line evidence document is absent from
both `main` and #535. Disposition unchanged: **partially superseded — evidence gap retained.**

| Artifact | `main` | #535 | #503 `37e89b4a` |
|---|---|---|---|
| `.github/workflows/eaa-base-baseline.yml` | ABSENT | PRESENT | PRESENT |

#503's workflow is carried by #535 and absent from `main`. Disposition: **accounted for through
#535**, ownership/dependency tracking unresolved.

## 6. Safety declaration

- No merge, push, deploy, close, retarget, or rebase. All three commits are local-only.
- `main` unchanged at `7580bd8f`; #535 unchanged at `8b6eadd7` (draft).
- EAA/dispatch PRs #502, #503, #508, #500, #499, #496 not advanced.
- No assertion weakened, no guard removed, no policy edited. The only negative controls were
  run in scratch worktrees and restored byte-identically (verified by md5).
- No credentials, tokens, or secrets were printed.

## 7. Next authorized action

Sovereign acceptance decision on the three resolution commits. #525 and #539 remain held;
#535 remains unchanged.
