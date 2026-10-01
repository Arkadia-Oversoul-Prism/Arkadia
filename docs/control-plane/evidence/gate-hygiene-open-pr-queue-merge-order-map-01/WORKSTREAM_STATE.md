# WORKSTREAM STATE — `gate-hygiene/open-pr-queue-merge-order-map-01`

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Status: **IMPLEMENTED** (evidence complete; no code/test change; sovereign review only)

## What this pass did

Bounded evidence pass. Adds **one** file. Answers three merge-preparation questions against
the 16-PR open queue — overlap, real composability, merge order — and reconciles two stale
ledger entries. No source, test, `AGENTS.md`, or governance byte changed.

## Current state (derived from live evidence, not prose)

| item | value |
|---|---|
| `main` | `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of #141) |
| open PRs | **16** (#142–#157), all `mergeable=True`, only **#147** stacked |
| architecture suite | **11 passed** |
| `api/main.py` | **2519 / 2600** lines; `py_compile` OK |
| CP10 mutation boundary | `--judge` exit 0 |
| full suite | see §Baseline (run recorded below) |

## Findings (all re-derived post-unshallow — see §Method)

1. **Queue is almost entirely disjoint.** Only `AGENTS.md` (#143/#147/#150) and `api/main.py`
   (#153/#154) have >1 writer. `#153`/`#154` overlap is **non-conflicting** (hunks ~450 lines
   apart, clean in both orders).
2. **The only real conflict is `AGENTS.md`.** `#143 × #150` conflicts symmetrically, in both
   orders. Already adjudicated by #155/#151: **#150 is the correct repair**, #143 is
   double-encoded, #147 `CONTRADICTED`.
3. **13 non-`AGENTS.md` PRs + #150 merge clean as one sequence** (verified end-to-end).
4. **`SH-02b` is already on `main`** — repair commits `82ce2a83`, `157da8d1` are ancestors of
   `main`; target test 9/9 passes; branch deleted. The ledger's "next bounded task" pointer is
   **stale**.
5. **`SH-07` and `SH-09` are correctly classified as non-bounded** — reproduced and
   fingerprinted, **no edit taken**, escalated as product/architecture decisions.

## Method — the trap that must not be repeated

**The automation clone is SHALLOW.** `git rev-parse --is-shallow-repository` → `true`,
`git rev-list --count origin/main` → `1`. In a shallow clone, three-dot diffs and
`git merge-base` return **silently wrong** results (PR #142 reported zero changed files and an
empty merge-base before unshallowing).

**Precondition for any future pass on this queue:**

```bash
git fetch --unshallow origin
for p in $(seq 142 157); do git fetch origin pull/$p/head:pr$p -f -q; done
```

Also: test whether a task's **commits** are ancestors of `main`
(`git merge-base --is-ancestor <sha> origin/main`), never whether a branch **name** exists —
a deleted branch is not evidence of unmerged work. This is the exact error that made `SH-02b`
look live.

## Baseline fingerprint

- Live, measured on this pass's base (`002b189`):
  **21 failed / 1038 passed / 13 skipped / 2 collection errors**, architecture **11 passed**.
- Both documented fingerprints are **stale**: the contract's `804 / 54 / 12 / 2` and the
  ledger's `1008 / 20 / 13`. Record the live numbers above as the new baseline.
- Collection requires **both** `PYTHONPATH=archive/legacy_python` **and**
  `--continue-on-collection-errors`; without the flag pytest aborts at the 2 known errors and
  reports **nothing** (which reads as "no suite ran", not "suite ran and here are counts").
- Pre-existing collection debt: `tests/test_autonomy.py`, `tests/test_render_codex.py`.
- The 21 failures cluster on **live in-flight gate-hygiene work**, and two of them *are* the
  escalated nodes: `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`
  (**`SH-07`**) and `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
  (**`SH-09`**). Also failing: `test_steward_filter.py` (3),
  `test_spiral_grove_activity_runtime.py` (4), `test_spiral_grove_registry.py` (2),
  `test_solspire_r1_governance_convergence.py` (2), `test_engineering_scheduler_bootstrap.py` (2),
  `test_solspire_r2_github_mutation.py`, `test_solspire_r3_execution_runtime.py`,
  `test_gate_status.py`, `test_gate_serve_script.py`, `test_engineering_lab_agent_loop.py`,
  `test_ais_w2_living_gate_grove_handoff.py`.
- **Recorded, not fixed** — fixing them here would be the exact scope creep this pass is
  bounded against. They become their own bounded workstream(s).
- This pass changes **two docs files only**, so it cannot move any count by construction.
- This pass makes **no production-parity claim** — git objects only.

## Merge-order recommendation (advisory; merge is HUMAN)

- **Wave 1 (any order):** #157, #156, #155, #151, #152, #153, #154, #142, #144, #145, #146,
  #148, #149 — all single-writer, measured clean as one sequence.
- **Wave 2:** **#150** — the correct `AGENTS.md` repair (single writer).
- **Wave 3 (disposition):** #147 **do not merge as-is** (`CONTRADICTED`); #143 **do not merge
  its `AGENTS.md`** (double-encoded).

## Next bounded task

**None created by this pass** (no self-expansion). Candidates the sovereign may bound, in
dependency order:

1. **Drain Wave 1 + #150** — pure merge actions, human authority.
2. **Adjudicate `#143`'s non-`AGENTS.md` Gate-2 parity content** — separate from its encoding
   damage.
3. **`SH-07`** — wire `arkanaSessionId` through `ArkanaCommune` (architectural gate, not a
   test repair).
4. **`SH-09`** — `NodeEntry.tsx` copy/coupling (product presentation decision).

## Open PR boundary

This pass is its own branch and its own PR. It does **not** widen #157 or any other PR.
Human-sovereign merge only; no merge, no `main` push, no force-push from this workstream.
