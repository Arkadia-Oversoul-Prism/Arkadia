# GATE-02 — CapabilityChamber union repair 02 (bounded)

**Pass:** gate02 / bounded repair 02
**Date:** 2026-10-01
**BASE_MAIN:** `47e4128b1d1416a9417d9bb33db18a3d269f0200` (PR #166 merged)
**REBASED_ONTO:** `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f` (PR #169 + #173 merged after #166)
**Branch:** `gate02/capability-chamber-union-repair-02`
**Authority required:** human merge only. No merge, no push to `main`, no force-push performed.

---

## 1. Why this branch exists — PR #166 landed the wrong variant

PR #166 (`GATE-02: repair CapabilityChamber merge-loss; verify #163 defect claim`) was
**squash-merged** as `47e4128`. Its head branch
(`gate02/capability-chamber-merge-loss-repair-01`) ended at `6786763`, carrying chamber blob
`20f58649cfac4969ae44087eacaf2f87b63aa84b` (the union). The merged commit, however, carries
chamber blob `5c78fcbcd713057556d7257e51dab295f82888cc` — the content of `0ebb9c4`, the
branch's **oldest** head.

Evidence that the merge took the wrong revision:

```
$ git cat-file -p 47e4128 | head -3
47e4128...                 <- single parent: 0fe6d0d only (not a merge commit)
0fe6d0d...

$ git merge-base --is-ancestor 8000a81 main   -> NO   (the repair commit)
$ git merge-base --is-ancestor d90ed58 main   -> NO   (the Pass 02 evidence commit)

chamber blob per branch commit:
  0ebb9c4  5c78fcbcd...   <- what landed on main
  8000a81  20f58649...   <- the repair
  d90ed58  20f58649...
  6786763  20f58649...   <- final head
```

`47e4128` touched 4 files: `AGENTS.md`, the Pass 02 `EVIDENCE.md` + `WORKSTREAM_STATE.md`,
and `CapabilityChamber.tsx` (2 insertions / 2 deletions).

## 2. What that means for `main` today

`main` `47e4128` carries the *third* chamber variant — neither the merge's hybrid
(`0cde2f782`) nor the union (`20f58649`):

| Revision | `ActivityRuntime` import | mount | SG-03 boundary literal |
|---|---|---|---|
| `0cde2f782` (old `main`) | yes (dangling) | no | no |
| `5c78fcbcd` (**current `main`**) | no | no | no |
| `20f58649` (union, this branch) | yes | yes | yes |

Also lost: `SpiralGrovePage.tsx` from `8000a81` (blob `be992d63`) — the Nexus canonical
header. `main` has the pre-repair version.

## 3. Measured impact of PR #166 on the full suite — net zero

Both runs: `python -m pytest tests/ -q --continue-on-collection-errors -p no:randomly`,
`PYTHONPATH=archive/legacy_python`, compared by **test-node identity**.

| Tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| `main` `0fe6d0d` (before #166) | 20 | 1121 | 15 | 1 |
| `main` `47e4128` (after #166) | 20 | 1121 | 15 | 1 |

`comm -23` (fixed) and `comm -13` (new) are **both empty**. The failing-node sets are
identical. **PR #166 fixed nothing and broke nothing.** It is a no-op on the test suite.

Three SG nodes that the union *does* fix remained failing on `main` after the merge:

- `tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber`
- `tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary`
- `tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header`

## 4. The merged evidence documents are wrong

The `EVIDENCE.md` and `WORKSTREAM_STATE.md` merged by #166 are the **Pass 02** versions.
They claim (a) the inline design is canonical and the mount "falsified (4→6 failures)",
(b) the SG-03 literal is "absent in every revision", and (c) the failing-node delta is
"NONE" with matching sha256 fingerprints. Claims (a) and (b) are refuted by direct
measurement; claim (c) was measured on a pre-merge branch tree and is not true of `main`.

This branch adds a correction banner to both files. Their original bodies are retained
unmodified so the record of what was asserted, and when, stays inspectable.

## 5. Bounded objective

Restore the two files that PR #166 dropped, at the revisions the branch had actually
measured:

- `web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx` -> `20f58649` (union)
- `web/public_prism/src/pages/SpiralGrovePage.tsx` -> `be992d63` (canonical header)

Completion condition: the SG test suite returns to 1 failure (the pre-existing `main`
defect), the full-suite failing-node set drops by exactly 3 with 0 new, architecture stays
11/11, and `api/main.py` stays within budget.

## 6. Variant measurement (the basis for choosing the union)

Measured across `test_spiral_grove_activity_runtime.py` + `test_spiral_grove_chambers.py` +
`test_spiral_grove_frontend_projection.py`:

| Variant | chamber blob | SpiralGrovePage | SG failures |
|---|---|---|---|
| old `main` / merge | `0cde2f782` | pre-repair | 3 |
| current `main` (`#166`) | `5c78fcbcd` | pre-repair | 3 |
| union chamber only | `20f58649` | pre-repair | 2 |
| **union chamber + canonical header** | `20f58649` | `be992d63` | **1** |

The single remaining failure is `test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`,
a **pre-existing `main`** test-side defect (§8).

## 7. Change set

```
web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx | 5 ++++-
web/public_prism/src/pages/SpiralGrovePage.tsx                     | 4 ++--
2 files changed, 6 insertions(+), 3 deletions(-)
```

## 8. Remaining failure — pre-existing on `main`, NOT part of this repair

`tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`
fails on old `main`, current `main`, and this branch alike. The test asserts the expanded
literal `data-testid="activity-surface-<kind>"` while `ActivityRuntime.tsx` renders the
template `` data-testid={`activity-surface-${kind}`} ``. The property holds; the assertion
cannot match its own template. **Test-side defect on `main`.** Deliberately not fixed here —
that would be scope expansion. It needs its own bounded workstream.

## 9. Gates

| Gate | Result |
|---|---|
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line budget | 2531 / 2600 |
| SG suite (3 files) | 1 failed / 29 passed |
| full suite | see §10 |
| `vite build` | not run — registry reachable via `npm ping` but package tarball fetch fails in this environment |

## 10. Full-suite delta

Recorded in the PR comment for this pass, and in `WORKSTREAM_STATE.md`.

## 10b. Re-measured after rebase onto `3e1cd00`

`main` advanced `47e4128..3e1cd00` (PR #169 canonical ingress, PR #173 relational
lineage) after this repair was first measured. Those commits touch `knowledge/*`,
`docs/architecture/*` and two new test files — **no overlap** with the two Spiral Grove
files here. The branch was rebased onto `3e1cd00` and every figure below was re-measured
against the new tip rather than inherited.

| Tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| `main` `3e1cd00` | 22 | 1125 | 15 | 1 |
| this branch (rebased) | **19** | **1128** | 15 | 1 |

Node delta by identity, `3e1cd00` -> branch: **3 FIXED / 0 NEW**

```
sha256(failing nodes, 3e1cd00) = 32a2b51bffa8210079f31d3d25e72741fbd605f1c15677a518b9923334d695aa
sha256(failing nodes, branch)  = 0a64965140978cc2e588fd0a446a18a661168cc6f3538a1dabb356e3c3162f29
```

Blobs remain pinned exactly: `CapabilityChamber.tsx` = `20f58649…`,
`SpiralGrovePage.tsx` = `be992d63…`.

### New defect observed on `main` (NOT this workstream — recorded, not fixed)

`47e4128..3e1cd00` introduced **two** failing nodes that were not failing before:

- `tests/test_relational_lineage.py::test_graph_node_exposes_canonical_capture_provenance`
- `tests/test_relational_lineage.py::test_traversal_preserves_provenance_projection`

```
TypeError: register_source() takes 0 positional arguments but 3 were given
```

`knowledge/capture.py:78` declares `def register_source(*, source_kind, source_ref=None,
title=None, origin_meta=None)` — **keyword-only**. `tests/test_relational_lineage.py:38,82`
call it positionally: `cap.register_source("document", "test:lineage", "Lineage source")`.
The shipped test cannot call the shipped function. Deterministic; reproduces in isolation
(2 failed / 1 passed). Classified as **new `main` debt from PR #173**, owned by that
workstream. Not repaired here — that would be scope expansion under GATE-02.

---

## 11. Authority boundary

Source repair + evidence only. **Not merged.** No push to `main`. No force-push. Merge is
reserved to the human sovereign.
