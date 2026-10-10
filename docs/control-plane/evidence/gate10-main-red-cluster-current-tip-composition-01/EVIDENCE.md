# Main-red cluster — current-tip composition measurement (GATE-10 / phase-1)

**Base:** `main` @ `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Branch:** `gate10/main-red-cluster-current-tip-composition-01`
**Environment:** Python 3.13 · pytest · git · `PYTHONPATH=<repo>/archive/legacy_python`
**Mutation:** none to product, test, workflow, or authority surfaces — evidence + one read-only
source-level guard. This PR does not merge and does not authorize.

This record answers the one question the phase-1 workstream left open: **what does the open
`main`-red debt-repair cluster actually compose to on the *current* tip?** Every prior
composition record (#358/#361/#375/#376/#377) sits on a base that is now behind `main`; this
pass re-derives the measurement against live `main` `f9ced6b6` and records the per-PR
merge-order inventory.

---

## 1. Live reconstruction (this pass)

| item | value |
|---|---|
| BASE_MAIN | `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` |
| full-suite failing/error nodes | **16** (15 failed, 1 error) |
| outcomes fingerprint | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` |
| ids fingerprint | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |
| architecture suite | **11 passed** |
| `api/main.py` | **2450** lines (budget 2600) — `python -m py_compile` OK |
| `AGENTS.md` mojibake (U+0400–U+04FF) | **0** |

The 16-node set and both fingerprints are byte-identical to the values recorded by
#361/#375/#391 — re-derived here independently from a fresh full-suite run, not inherited.

## 2. The cluster composes to 2 nodes on the current tip

Owner cluster (9 PRs): **#347, #354, #355, #356, #357, #363, #365, #384, #388**, plus the
evidence PR #391. Merged in recommended order onto a detached worktree at `f9ced6b6`:

```
$ git worktree add --detach /tmp/compose f9ced6b6
$ for n in 384 354 347 356 363 365 388 357 355; do git merge --no-edit pr$n; done
```

| tree | failing/error nodes | outcomes fingerprint | ids fingerprint |
|---|---|---|---|
| `main` `f9ced6b6` | **16** (15F/1E) | `bfcfe592…` | `ed5e4714…` |
| composed cluster (9 PRs) | **2** (1F/1E) | `f607dffd1abda8bc667897a4366c6afe1498ae6e5b02635ff682cbc6daeb2ad1` | `48e2b758b3194bd267e7babf13609b3467ff46985a879c72a55ad5201f44b3a9` |

The composed node set is a **strict subset** of the `main` node set — i.e. **zero
newly-introduced failures**. The two survivors are exactly the two nodes no PR targets:

- `tests/test_autonomy.py` — CE-01 module-vs-package collision, **reserved to the sovereign**.
- `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` —
  sovereign-decision placeholder (F-01).

On the composed tree: `tests/architecture` → **11 passed**; `scripts/cp10_mutation_boundary_policy.py
--judge` over the composed diff → **Mutation boundary PASS (exit 0)**; `api/main.py` compiles.

**14 of the 16 `main`-red nodes are repaired by the 9-PR cluster with no regression.**

## 3. Per-PR merge-order / mergeability inventory

Measured against live API (2026-10-10). `main_is_ancestor` = `git merge-base --is-ancestor origin/main <head>`.

| PR | base | head | mergeable | main_is_ancestor | files | role |
|---|---|---|---|---|---|---|
| #384 | `f9ced6b6` | `f744e36b` | true/unstable | **YES** | 2 | CP10 browser-asset repair |
| #354 | `f9ced6b6` | `b6eec36b` | true/unstable | **YES** | 6 | CP10 `deploy/` allowlist; **composes #384** |
| #388 | `f9ced6b6` | `63b3ce9b` | true/unstable | **YES** | 3 | CP10 enforcement-step truthfulness |
| #391 | `f9ced6b6` | `c5a63b01` | true/clean | **YES** | 4 | #354↔#384 duplicate-file merge order |
| #347 | `af3a3541` | `3f3024d9` | true/unstable | no (stale) | 3 | landing-headline re-pin |
| #355 | `f96d5fd2` | `73104fdf` | true/clean | no (stale) | 1 | n-atlas workflow trigger file |
| #356 | `f96d5fd2` | `1bfbcc4f` | **false/dirty** | no (stale) | 4 | Lab boundary guard |
| #357 | `f96d5fd2` | `4c3d8fb8` | **false/dirty** | no (stale) | 5 | SolSpire R1/R3 re-pin |
| #363 | `24a00f85` | `aa77f364` | **false/dirty** | no (stale) | 6 | standalone stale pins + NodeEntry |
| #365 | `24a00f85` | `d8679b49` | true/unstable | no (stale) | 4 | steward filter substring defects |
| #376 | `a47ea928` | `5e21d96e` | true/clean | no (stale) | 2 | evidence-only (composition verify) |
| #377 | `a47ea928` | `8b632449` | true/clean | no (stale) | 2 | evidence-only (branch mergeability) |

### 3.1 Conflict inventory (real merge, not `git apply`)

Merging the cluster sequentially produced **only** `AGENTS.md` tail-append conflicts (every
workstream appends a lesson block). No product/test/workflow file conflicted, and no shared
**load-bearing** file is independently edited by two PRs except the recorded #354 ⊇ #384
duplicate pair (byte-identical blobs — see §4). Resolving the `AGENTS.md` conflicts as a union
of both appended blocks yields a coherent tree; the composed measurement in §2 uses that tree.

### 3.2 Mergeability note

`mergeable=false/dirty` for #356, #357, #363 is a **GitHub-side mergeability projection**, not
a semantic conflict with any sibling PR: the composition above merged all three cleanly. It
reflects their stale base (`f96d5fd2` / `24a00f85`) relative to `main` `f9ced6b6`. A sovereign
decision to merge them should rebase first so the recorded head is a `main` descendant.

## 4. #354 ↔ #384: a duplicate, not a conflict (independently re-verified)

PR #354 deliberately composes #384's CP10 browser-asset repair, so both carry
`web/public_prism/public/firebase-config.js` and `tests/test_frontend_script_assets_resolve.py`.
Blob SHAs fetched live from both heads:

| file | #384 `f744e36b` | #354 `b6eec36b` | identical |
|---|---|---|---|
| `web/public_prism/public/firebase-config.js` | `d9973c17ad63e8411926d8bbce294ca0c2931551` | `d9973c17ad63e8411926d8bbce294ca0c2931551` | yes |
| `tests/test_frontend_script_assets_resolve.py` | `17be550d18b34392baecbdbe40dead112e658096` | `17be550d18b34392baecbdbe40dead112e658096` | yes |

A **real** `git merge pr354` into a worktree at `pr384` reports *"Merge made by the 'ort'
strategy"* with zero conflicts and lists only #354's unique files
(`AGENTS.md`, `scripts/cp10_mutation_boundary_policy.py`, the two evidence docs). Either order
yields the same tree — the pair is order-independent. Recommended sequence: **#384 first**,
then **#354** (its embedded copies then become no-ops).

Confirming #391's independent record: this pass re-derives the same blob SHAs and re-runs the
real merge; the values match byte-for-byte. #391 remains the carrier of that specific record.

## 5. #376 / #377 are evidence-only and now base-stale

Both are two-file, documentation-only PRs based on `a47ea928` (7 commits behind `main`). Their
subject is the *then-current-tip* composition. Against live `main` `f9ced6b6` their numbers are
superseded by §2 of this record. They are not merge candidates on their own merits; a sovereign
may close them as superseded. They introduce no product change.

## 6. What this record does NOT claim

- **No production parity.** This is a repository-source measurement only (Gate-2 remains
  BLOCKED on provider observation for the newest Production deploy).
- **No merge authorization.** Merge order in §3.1/§4 is a recommendation; the sovereign decides.
- **No CANDIDATE-vs-BASELINE idealization.** §2's composed run is on a *local union-resolved*
  tree; the sovereign's actual merge will follow the PR-by-PR sequence, and the GitHub
  projection (`dirty`) may require rebases before it matches this tree.

## 7. Next bounded task

Rebase sequence for the stale-base owner PRs (#355/#356/#357/#363) so each recorded head is a
`main` descendant, then re-measure §2 after the first post-`f9ced6b6` merge. Unowned drift is
**zero**: every `main`-red node is either repaired by the cluster or sovereign-reserved.
