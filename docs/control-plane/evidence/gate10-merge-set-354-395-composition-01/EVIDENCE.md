# GATE-10 · merge-set composition — PR #354 + PR #395

**Workstream:** gate10/merge-set-354-395-composition-01
**Base:** `main` `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Observation time:** 2026-10-10
**Status:** EVIDENCE-ONLY. No product, workflow, test, authority, or `AGENTS.md` change.
No merge. No authorization.

## 1. Why this is net-new

Every prior gate-hygiene composition record covers pairs drawn from the **debt-repair
cluster** (`#354, #355, #356, #357, #363, #365, #347, #384, #388`) or the **backbone**
`#388 × #390` pair:

- `#358 / #361 / #375 / #376 / #377 / #385 / #386` — the debt cluster, retracted/superseded
  incrementally; `#394` re-derives the cluster at the live tip `f9ced6b6`.
- `#391` — the `#354 ↔ #384` duplicate pair (byte-identical files, order-independent).
- `#393` — `#388 × #390`.

**`#395` is in none of them**, and no record composes the **recommended merge set**
`#354 + #395`. `#395`'s own §4b composes it with `#390` (a *third* PR), not with `#354`.
This pass measures the pair a sovereign is most likely to merge — the `deploy/` allowlist
repair (`#354`) and the browser-asset **gate wiring** (`#395`) — as a real merge.

## 2. What #354 and #395 add (complementary, non-overlapping)

| surface | #354 (`b6eec36b`) | #395 (`941a02b3`) |
|---|---|---|
| `scripts/cp10_mutation_boundary_policy.py` | additive `deploy/` LEGIT rule | — |
| `web/public_prism/public/firebase-config.js` | committed default asset | — |
| `tests/test_frontend_script_assets_resolve.py` | the guard | — (carried via #384) |
| `.github/workflows/sg-02-fe-2-v.yml` | — | two guard steps + trigger-filter entries |
| `tests/test_frontend_script_asset_ci_wiring.py` | — | wiring guard |
| `AGENTS.md` | append-only lesson | — |

**Zero shared files.** #354 owns the *repair and its asset*; #395 owns the *gate that runs
the guard*. They are the two halves of the `/firebase-config.js` fix.

## 3. Stacking relation, measured

- PR #395's **base ref** is `gate10/frontend-script-asset-resolution-01`, base sha
  `f744e36b78a28661017cf32942568c34e9b6cd2d` (= PR #384 head). `git merge-base --is-ancestor
  pr384 pr395` → **true**. #395 is *stacked on #384*.
- `git merge-base --is-ancestor pr354 pr395` → **false**.
- `origin/main` is an ancestor of all three.

**Consequence not recorded elsewhere:** #395's tooling base is **#384** — the branch
**#354 supersedes** (§#354's own note; #391 proves the #354/#384 files byte-identical).
If #354 merges and #384 closes, #395's branch is never rebuilt against the superseding
tree. Its *code* still composes — `#384`'s two files are byte-identical to `#354`'s, so
applying #395's own diff onto #354 yields the same change set — but a reviewer reading
#395's "stacked on #384 / merge #384 first" instruction is pointed at the superseded PR.

## 4. Composition, measured (real apply, not a patch prediction)

Isolated worktree at `origin/pr354` (`b6eec36b`), then `#395`'s **own** diff
(`git diff origin/main pr395` restricted to its two code files) applied with
`git apply --3way`:

```
$ git worktree add --detach /tmp/w354 pr354
$ git diff origin/main pr395 -- .github/workflows/sg-02-fe-2-v.yml \
      tests/test_frontend_script_asset_ci_wiring.py > pr395.patch   # 270 lines
$ git apply --3way pr395.patch
Applied patch to '.github/workflows/sg-02-fe-2-v.yml' cleanly.
Falling back to direct application...            # the new file; expected
APPLY RC=0
```

| check | result |
|---|---|
| `git apply --3way` of #395 onto #354 | **clean, RC 0** — no conflict (disjoint files) |
| `yaml.safe_load(sg-02-fe-2-v.yml)` on the composed tree | **OK** |
| composed files present | `test_frontend_script_assets_resolve.py`, `test_frontend_script_asset_ci_wiring.py`, `web/public_prism/public/firebase-config.js` |
| `pytest test_frontend_script_assets_resolve.py test_frontend_script_asset_ci_wiring.py -q` | **10 passed** |

Both halves of the fix are present in the composed tree and the wired guards pass on it.
Order does not matter: the two diffs touch disjoint files, so either merge order yields the
same tree.

## 5. Runtime corroboration (live CI, per head — not a composed-tree run)

| PR | head | run | job | result |
|---|---|---|---|---|
| #354 | `b6eec36b` | `37969546325` (`SG-02-FE.2-V`, `pull_request`) | `validate` | **success** |
| #354 | `b6eec36b` | `37969546423` (`security-secret-scan`) | — | **success** |
| #395 | `941a02b3` | `38044755982` (`SG-02-FE.2-V`, `pull_request`) | `validate` | **success** |

#354's head runs **9/9 check-runs `success`**, including `validate`, `Build canonical
Render image`, and `Full-history secret scan`. This **supersedes #354's own §"Remaining
uncertainty"**, which said the CP10 browser step "can only be confirmed green on a fresh
CI run of this head (launched on push)". The run exists; `validate` is green.

On #395's head the `validate` job's steps of interest are all `success`:

| step | name | conclusion |
|---|---|---|
| 11 | Frontend script asset gate wiring | success |
| 31 | CP10 browser route verification | success |
| 37 | Enforce CP10 executable gates | success |

`main` `f9ced6b6` is red on exactly one check-run, `validate`, whose failing step is the
`browser` route verification. Both repair PRs' heads are green on that same job.

## 6. Remaining uncertainty

- This is a **repository-source composition** claim plus **per-head CI** corroboration.
  No single CI run exists of the composed `#354 + #395` tree. `main` cannot be shown green
  until a post-merge run of `SG-02-FE.2-V` executes on the merged tree.
- §9 proposes, and does **not** execute, a separate gate-integrity repair.

## 7. Authorization required

**Human only.** Recommended merge set: **#354 then #395** (or #395 then #354 — order-free;
disjoint files). Close **#384** as superseded by #354 (§3) and retarget #395's instruction
from "#384" to "#354". Do not merge duplicates in parallel.

## 8. Files changed by this PR

- `docs/control-plane/evidence/gate10-merge-set-354-395-composition-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate10-merge-set-354-395-composition-01/WORKSTREAM_STATE.md`

## 9. Proposed (unowned) finding — `lab` / `backend` enforcement assertions are constant-true

Recorded here as **discovery**, not executed (NO SELF-EXPANSION; repairing it would
redden `main`, so it is a sovereign-scope decision, not an agent one).

The `Enforce CP10 executable gates` step tests, among others
(`.github/workflows/sg-02-fe-2-v.yml`):

```
test '${{ steps.lab.outcome }}' = success
test '${{ steps.backend.outcome }}' = success
```

Both referenced steps are:

```
- name: CP10-A Lab tests
  id: lab
  continue-on-error: true
  run: python -m pytest ... -q 2>&1 | tee cp10-lab.log
- name: CP10-B broader backend regression
  id: backend
  continue-on-error: true
  run: python -m pytest tests/ -q 2>&1 | tee cp10-backend.log
```

Neither declares `set -o pipefail`, so the step exit code is `tee`'s (`0`) and the pytest
failures are swallowed. `continue-on-error: true` then renders the step **conclusion**
`success`; `${{ steps.<id>.outcome }}` is also `success` because the `run` block exited 0.
The assertion is therefore not merely masked — it is **constant-true**: it can never fail
for any pytest result. (Compare `solspire_runtime` and `browser`, which *do* declare
`set -o pipefail` and therefore surface real failures — measured: `main` `f9ced6b6`, the
`browser` step is the one failing gate.)

This is the **corrected** version of the `AGENTS.md` "self-satisfying" claim (PR #388
established the *substitution* is real; this narrows the claim to the two `tee`-without-
`pipefail` assertions). Because `main` currently carries 15 failing full-suite nodes, adding
`set -o pipefail` to `lab`/`backend` would flip both assertions to `failure` and redden the
job on top of the existing browser failure. Repairing it is therefore **not** a
consequential-free change and must be a separate bounded workstream with sovereign sign-off.
Not in scope of this PR.
