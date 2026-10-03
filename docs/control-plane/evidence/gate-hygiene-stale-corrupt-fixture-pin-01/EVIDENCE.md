# gate-hygiene: stale corrupt-fixture pin — clone-depth dependence of the adjusted-instrument guards

Pass 7. Reconstructs the gate-hygiene PR cluster (#215–#220), isolates the
clone-depth dependence that keeps the cluster `[UNSTABLE]`, and closes the
latent fixture-pin defect #218 left on the very node it did not touch.

## 1. Live state (reconstructed, not inherited)

- Base: `main` = `162f574`. Every PR below shares `162f574` as merge-base.
- Open, non-draft, all `[UNSTABLE]`: **#215 #216 #217 #218 #219**.
  Draft / HOLD: **#220** (`gate-hygiene/stale-gate-fixture-retirement-01`).
- Head SHAs: #215 `0c18fbb`, #216 `4747e4c`, #217 `3b5e4cd`, #218 `54e2e98`,
  #219 `58d8cdf`/`c3ddf61`/`d4a8ff9`, #220 draft.
- #218 contains neither #217 nor #216; it is not stacked (`git merge-base
  --is-ancestor pr/217 pr/218` → false). The three PRs touch
  `tests/test_agents_md_encoding_adjudication.py` at disjoint hunks.

## 2. The clone-depth dependence is real and is a **tier-1** (reachable) defect

`test_agents_md_encoding_adjudication.py` resolves historical fixtures by SHA.
`GATE2_PARENT_REV = 7d79f38…` is reachable from **no branch of this repository**
(`git branch -a --contains 7d79f38` → empty). It was fetched locally once via a
PR-head ref, so it exists in a developer clone but **not** in the CI checkout.

Reproduced in a clean, single-branch CI-shaped clone
(`git clone --no-local --single-branch --branch main`, no PR refs):

| tree | `7d79f38` object | adjudication file |
|---|---|---|
| `main` `162f574` | absent | **2 failed, 17 passed, 4 skipped** |
| #215 | absent | **1 failed, 17 passed, 5 skipped** |
| #216 | absent | **2 failed, 17 passed, 4 skipped** |
| #217 | absent | **1 failed, 18 passed, 4 skipped** |
| #218 | absent | **2 failed, 17 passed, 4 skipped** |
| #219 | absent | **2 failed, 17 passed, 4 skipped** |

The PRs' own local figures (using a full clone that holds `7d79f38`) are
17–18 passed. The gap is one node —
`test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` — which
dereferences `GATE2_PARENT_REV` and therefore *fails* (rather than skipping) when
the object is unreachable. Every currently-open PR is red on CI for this reason.

A genuine `--depth=1` clone is a **separate, stronger dependency**: it also drops
`CORRUPTION_COMMIT` (`e0dde9ad`) and `ORACLE_REV` (`6c43218a`), so the skip guards
cannot fire (they call `_rev()` before the guard) and the file reports 5 failed.
This is not the CI acquisition shape but should be noted; a shallow CI checkout
would redden the same file more broadly.

## 3. Latent defect in #218 — the superseded-fixture pattern, reproduced

#217 and #218 each claim to replace the moving-branch premise
`_rev("AGENTS.md", "origin/main")` with the pinned `CORRUPTION_COMMIT`. They are
**siblings, not the same node**: #217 fixes
`test_exit_code_does_not_call_a_divergent_clean_file_verified`; #218 fixes
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`. **#218
left the sibling node's `origin/main` premise untouched** (line 435:
`corrupted = live if cyrillic_count(live) else _rev("AGENTS.md", "origin/main")`).

Proven in the CI-shaped clone, where the repaired `main` tip is present but
`7d79f38` is not:

- #218 head (`54e2e98`): **2 failed** —
  `test_shadow_adjudication…` *and*
  `test_exit_code_does_not_call_a_divergent_clean_file_verified`.
- #217 head (`3b5e4cd`): **1 failed** — only `test_shadow_adjudication…`.
  #217's fix to the `test_exit_code` node holds; #218's does not.

This also contradicts #218's own recorded evidence ("composed tree is 21P/2S"):
in a **full** clone #218's head measures **1 failed, 20 passed, 2 skipped** — the
`test_exit_code` node is red even where `7d79f38` is available. The 21P/2S figure
was not reproducible from #218's tree.

## 4. Bounded fix

On a dedicated branch cut from #218's head `54e2e98`, apply #217's already-proven
pin to the sibling node in `tests/test_agents_md_encoding_adjudication.py`:
read the corrupted fixture off `CORRUPTION_COMMIT` (with a skip guard) rather than
off the moving branch `origin/main`. One hunk; same semantics #217 introduced.

Measured:

| tree | full clone (`7d79f38` present) | CI-shaped clone (`7d79f38` absent) |
|---|---|---|
| #218 `54e2e98` | 1 failed, 20 passed, 2 skipped | 2 failed, 17 passed, 4 skipped |
| **fix** (this branch) | **21 passed, 2 skipped** | **1 failed, 18 passed, 4 skipped** |

The residual `test_shadow_adjudication…` failure is the `7d79f38` reachability
issue (§2) and is **not** in scope for this fix; closing it requires making the
pinned revision reachable (or redesigning the fixture), a separate bounded item.

## 5. Composed cluster (true remote heads, corrected)

Composed in the CI-shaped clone in merge order **#215, #216, #217, #218+fix, #219**:
zero conflicts (the only textual overlap is #217/#218 on the shared comment
preceding the identical code change — both sides apply the same edit). Result:
**36 passed, 0 failed, 5 skipped** across `test_agents_md_encoding_adjudication.py`
+ `test_baseline_fingerprint.py`; architecture **11 passed**. No baseline node-set
delta.

## 6. Superseded-fingerprint origin (#219 vs the docs guard)

#219's evidence (`WORKSTREAM_STATE_PASS6.md:26`) republishes
`4d84e7eb…` (21 nodes) as the *current live `main`* fingerprint. #216 declares
`4d84e7eb…` a **superseded** value — the recorded set **plus** the depth-dependent
sibling — and pins `SUPERSEDED_OUTCOMES_FINGERPRINTS` against it. The values are
not contradictory: `4d84e7eb…` is what a bare clone reports when the sibling
fails instead of skipping; the canonical clone-depth-stable value is `a578a766…`.

#219's fingerprint is recorded in an **evidence doc**, which is outside
`FINGERPRINT_DOCS` (`.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`,
`docs/phase1/CONTINUATION_LEDGER.md`), so the doc-agreement guard does not read
it and the cluster does not red for this. It is a recording-convention hazard, not
a test failure: if the `main` fingerprint migrates into a guarded doc it must be
`a578a766…`/`8036fc06…`, never `4d84e7eb…`.

## 7. #220 vs #216

#220 is branched from `162f574`, not from #216 (`git merge-base --is-ancestor
pr/216 pr/220` → false). `CLONE_DEPENDENT_SIBLING_NODE` is **absent on `main`**,
so #216 and #220 each introduce the same symbol independently → a real content
conflict on `tests/test_baseline_fingerprint.py`. #220 additionally renames the
recorded set to an 18-node `SUPERSEDED_NODE_SET` (retiring two archived-surface
nodes) where #216 keeps the 20-node set. That retirement is a **separate
workstream** and #220 is a draft marked HOLD for sovereign call; it should not be
merged with this cluster.

## 8. Merge order

`#217 → #218 → #215 → #216 → #219` satisfies every filename overlap that exists.
#218's residual node is closed by this branch, so #218 may be merged whole (or this
branch merged after #218). Do **not** merge #220 with this cluster.

## 9. Non-goals

- No `AGENTS.md` rewrite; no architecture-debt reclassification; no boot code.
- Not touching the `7d79f38` reachability defect itself (§2), the #220 retirement,
  nor any baseline debt.
- No merge. Human authority remains final.

## 10. Reproduce

```
# CI acquisition shape (drops unreferenced PR-head revisions)
git clone --no-local --single-branch --branch main <repo> ci && cd ci
git fetch <repo> <head>:refs/tmp/n && git merge refs/tmp/n
python -m pytest tests/test_agents_md_encoding_adjudication.py -q
# guard needs PYTHONPATH=<repo>/archive/legacy_python (pyyaml + legacy modules)
```
