# SG-04 canonical-header node — merge regression, not a stale assertion

**Workstream:** `gate-hygiene` / SH-02 (`STALE_ASSERTION` migration) → **reclassified**
**Gate:** GATE-01 (canonical authorship) / SG-04 (learning activity runtime)
**Status:** CONTRADICTED — the classification premise for this node is falsified
**Authority:** evidence-only. No merge, no `main` push, no source or test mutation, no
authority-model, identity-boundary, or mutation-path change. Human-merge-only.
**Base main:** `df7a99a` (`Merge pull request #131 … spiral-grove-05`)
**Session:** 2026-09-29, bounded hourly pass

---

## 1. What was assumed

The selected next bounded SH-02 task was:

> Repair `tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header`
> as a **safe standalone `STALE_ASSERTION`** — i.e. the source-level string assertion had
> drifted from *reworded-but-intact* governance behaviour.

That premise is **false**. This node is neither stale nor reworded. It is a **merge
regression** that silently discarded a landed governance fix.

## 2. Live failure (reproduced on `main` @ `df7a99a`)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest \
  tests/test_spiral_grove_activity_runtime.py -q
# 4 failed, 8 passed
```

| node | failing line | assertion |
|---|---|---|
| `::test_spiral_grove_uses_the_nexus_canonical_header` | `:124` | `assert '<h1' not in page` |
| `::test_runtime_is_mounted_by_the_capability_chamber` | `:85` | `assert '<ActivityRuntime activity={activity} />' in chamber` |
| `::test_chamber_preserves_sg03_downstream_boundary` | `:110` | `assert 'Evidence submission, assessment, and capability-state updates remain separate downstream stages.' in chamber` |
| `::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | `:79` | `assert 'data-testid="activity-surface-research"' in runtime` |

The remaining 8 nodes in the same file **pass** on `main`, so this is a partial, not a
wholesale, loss of the SG-04 surface.

## 3. The headline proof (3-commit bisect)

`tests/test_spiral_grove_activity_runtime.py` history and
`web/public_prism/src/pages/SpiralGrovePage.tsx` history intersect at the same commit, which
makes the timeline directly checkable in a detached worktree per commit:

| commit | message | `SpiralGrovePage.tsx` `<h1` count | node result |
|---|---|---|---|
| `c04ee10` | `fix(sg04): remove duplicated Spiral Grove page header` | 1 | (test suite not yet asserting `<h1`) |
| `73b8868` | `fix(sg04): establish canonical Spiral Grove header` | **0** | **PASSED** |
| `ff80b8c` | `Merge branch 'main' into sg-04-learning-activity-runtime` | **1** | **FAILED** |
| `df7a99a` | current `main` | 1 | FAILED |

```
$ for c in 73b8868 ff80b8c; do git worktree add -f /tmp/wt_$c $c >/dev/null 2>&1; \
    (cd /tmp/wt_$c && python -m pytest \
      tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header -q); done
73b8868: 1 passed
ff80b8c: 1 failed
```

`73b8868` is a **1-file** commit (`4 insertions, 32 deletions`) that deliberately removed the
page-local `<h1>The Spiral Grove</h1>`, the `Stat` helper, the now-unused `useEffect`, and the
`groveRootRef`/DOM-suppression hack — establishing the Nexus hub heading as the single
canonical header. The very next non-merge commit that touches the file, merge `ff80b8c`
(`9 insertions, 4 deletions`), **restores all of it**.

This is not "reworded but intact". The governance property went from **enforced** to
**violated**, in a merge, and no test in the protected architecture suite noticed.

## 4. Root cause: a two-location render surface with one canonical header

`SpiralGrovePage` is mounted at **two** locations, only one of which supplies an `<h1>`:

| mount | file | heading supplied by |
|---|---|---|
| `view === 'grove'` | `web/public_prism/src/App.tsx:134` | **page-local `<h1>` (required)** |
| `activeTab === 'university'` | `web/public_prism/src/pages/NexusPage.tsx:909` | `NexusPage.tsx:888` `<h1>` (`activeTab === 'university' ? 'The Spiral Grove'`) |

Because `App.tsx:134` renders the page **outside** `NexusPage`, deleting the page-local header
does not merely de-duplicate — it **strips the `<h1>` entirely on the `grove` route**.

Historical corroboration: commit `7c18b9e` (`test(sg04): lock duplicate Grove header
regression`) and merge `ff80b8c`'s inspector-like DOM suppression (`data-sg-duplicate-header`,
`candidate.style.display = 'none'`, walked from `cursor?.parentElement`) are the *previous*
attempt to reconcile exactly this two-location tension — a runtime DOM probe instead of a
structural fix. `73b8868` superseded that probe and asserted its absence
(`assert "data-sg-duplicate-header" not in page`).

Consequence: the naive remedy ("delete the `<h1>`, trust the Nexus heading", which is what
`73b8868` shipped and what this node's assertion encodes) **is itself a real regression on the
`grove` route**. Conversely, restoring the `<h1>` un-conditionally (what merge `ff80b8c` did)
re-introduces the duplicate under `activeTab === 'university'`. **Both fail.** The page-local
header must be supplied **conditionally on the mount context**, or `App.tsx:134` must supply
its own heading.

This is a **product/UI-architecture decision** — it is explicitly excluded from the
`gate-hygiene` test-only envelope.

## 5. Why this is a HARD STOP for this workstream

1. The node is not a `STALE_ASSERTION`; the classification premise is falsified
   (`CONTRADICTED`).
2. The correct fix is **source** (`SpiralGrovePage.tsx` / `App.tsx` / `NexusPage.tsx`), not
   test-only, and it changes user-visible rendered structure.
3. Choosing between the two locations' heading ownership is a **product decision**, not a
   test-hygiene repair. Editing the assertion to accept `<h1>` would ratify a UI regression and
   discard a landed fix — that is "weaken the gate", which the gate-hygiene workstream forbids.
4. The same merge also broke 3 sibling SG-04 nodes (`:79`, `:85`, `:110`), so this is a
   **cluster-level merge-loss**, not a single drifted literal.

Per contract §05 (PRECONDITION) and §HARD STOPS, this pass **does not patch around it**.

## 6. Sibling cluster: the same merge reverted 3 more nodes

`73b8868` is titled "establish canonical...header" but its content is the **SG-04
canonicalization**; the SG-04 branch tip (`1b63994` / `06ad5f2`) carries all four properties,
`main` carries only the SG-04-03 half.

| property | SG-04 tip | current `main` | failing node |
|---|---|---|---|
| `<ActivityRuntime` mounted in chamber | **1** | import only, **unused** (`:4`) | `::test_runtime_is_mounted_by_the_capability_chamber` |
| SG-03 downstream-boundary literal | present | **absent** | `::test_chamber_preserves_sg03_downstream_boundary` |
| `data-testid="activity-surface-research"` | present | **absent** | `::test_runtime_dispatches_all_eight_kinds…` |
| page-local `<h1>` absent | **0** | 1 | `::test_spiral_grove_uses_the_nexus_canonical_header` |

`CapabilityChamber.tsx` on `main` still contains
`import ActivityRuntime from './ActivityRuntime'` (line 4) with **no** `<ActivityRuntime` usage —
a dangling import, i.e. the mount was removed without the import. That is independent
corroboration that the mount was lost, not deliberately relocated.

Sibling suites that *pass* on `main` (`test_spiral_grove_chambers.py`,
`test_spiral_grove_frontend_projection.py`, `test_spiral_grove_learning_path_projection.py` →
24 passed) assert the SG-04-03 shape only; they do not cover the four properties above.

## 7. Status of the remaining SH-02 `STALE_ASSERTION` scope

Re-measured this pass (excluding `DRIFT`, `SH-08`, product-decision nodes):

| cluster | result | note |
|---|---|---|
| `test_weaver_mvp2_08.py`, `test_weaver_sci_boundary_01.py`, `test_weaver_sci_contract_01.py` | pass | repaired by earlier SH-02 PRs |
| `test_solariun_experience_consolidation_01.py` | pass | repaired |
| `test_prism_pass_c_surface_ownership.py` | pass | repaired (SH-02b) |
| `test_ais_w6_future_skills_challenge.py` | pass | repaired (SH-02 batch 4) |
| `test_spiral_grove_activity_runtime.py` | **4 failed** | this document — **merge regression, out of envelope** |
| `test_steward_filter.py` | **3 failed** | ledger rows 27–29: `test_allows_mythic_with_action`, `test_blocks_identity_claims`, `test_compress_to_choices` — **not yet adjudicated** |

The `test_steward_filter.py` trio is the one remaining candidate cluster plausibly inside the
SH-02 envelope; it needs its own retain/reword/build-to-reality adjudication in a later pass
(it asserts `Steward` compression/identity behaviour and may itself be a governance loss —
the fail-closed guardrail direction must be checked before touching it).

## 8. Provenance

- **Live SHA:** `df7a99a` (`origin/main`), shallow clone — historical commits reachable via
  `git show` / detached worktrees, as used in §3.
- **Reproduction:**
  ```bash
  PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/test_spiral_grove_activity_runtime.py -q
  for c in 73b8868 ff80b8c; do git worktree add -f /tmp/wt_$c $c; \
    (cd /tmp/wt_$c && PYTHONPATH=<repo>/archive/legacy_python python -m pytest \
      tests/test_spiral_grove_activity_runtime.py -q); done
  ```
- **No runtime claim.** No deployment identity, no browser observation — this is repository
  and git-history evidence only. Per the AEAS boundary pulse, this is `VERIFIED` at the
  repository layer and `UNKNOWN` at the deployment/runtime layer; parity is **not** claimed.

## 9. Recommendation (requires sovereign decision)

1. **Restore the SG-04 canonicalization** — re-apply `73b8868`'s header fix **plus** the SG-04
   tip's chamber mount / boundary literal / activity-surface testids, in a **source** PR owned
   by the SG-04 workstream (not `gate-hygiene`).
2. **Resolve the two-mount header ownership** structurally: either give `App.tsx:134` its own
   heading and keep the page-local `<h1>` out, or pass an explicit
   `showHeader` / `headerSuppliedByParent` prop from each mount. No DOM-inspection hack — the
   project already removed one.
3. **Do not** reclassify these 4 nodes as `STALE_ASSERTION` and do not weaken the assertions.
4. **Guard:** add a fitness test that asserts the SG-04 properties on `main` (and ideally that
   the `grove` route retains an `<h1>`) so a future merge cannot silently drop them again.
