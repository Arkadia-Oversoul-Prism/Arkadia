# GATE-10 — CI verdict-step integrity

**Branch:** `gate10/ci-verdict-step-integrity-01`
**Base:** `main` @ `850216fc99b0eab66a66f8a8290c0db33823b681`
**Class:** guard-execution gap (recurring: "a guard no workflow executes is decoration")

## 1. Defect

Two distinct ways a CI verdict step can be unable to report failure.

**1a. An unresolvable `steps.<id>.outcome` reference substitutes to empty.**
`.github/workflows/sg-02-fe-2-v.yml` echoed `${{ steps.grove.outcome }}` while the
`Grove contracts` step declared **no `id`**. GitHub substitutes an unknown step
reference with the empty string, so the emitted line became `echo "Grove contracts: "`.

**1b. A blocking step's exit status destroyed by a pipe.**
`Grove contracts` carries **no** `continue-on-error` (it is enforced), and its body was

```
python -m pytest ... -q 2>&1 | tee cp10-grove.log
```

Without `pipefail` the step's status is `tee`'s, so the step cannot fail.

## 2. Runtime evidence (measured, not inferred)

Run **`38150620847`** — `event=push`, `head_sha=56ada9dd1511c788ade4a461b152a6d9ab6f6029`,
`conclusion=success`.

- `56ada9dd` is a **`main` ancestor** (`git merge-base --is-ancestor` → true), and
  `git diff 56ada9dd 850216fc -- .github/workflows/sg-02-fe-2-v.yml` is **empty**, so the
  workflow under examination is byte-identical to `main`'s.
- The substituted line in the log is
  `echo "Grove contracts: "^[[0m` — the outcome value is **empty** (1a, observed).
- In the same run the `lab` step printed `2 failed, 9 passed`, yet the terminal
  enforcement step printed `test 'success' = success` for **all 16** assertions
  (`grep -c` → 17 matches = 16 assertion lines + 1 `##[group]Run` header).
  A guard that cannot fail is decoration.

## 2.1 Runtime verification of the repair (post-change, on the PR head)

Run **`38186300846`** (`event=pull_request`, head `7cb7789a398132d44260426628143d9edfa72cec`):

| Observation | Pre-change (`38150620847`) | Post-change (`38186300846`) |
| --- | --- | --- |
| `CP10 evidence summary` line | `echo "Grove contracts: "` — **empty** | `echo "Grove contracts: success"` |
| Grove step command | `python -m pytest … \| tee cp10-grove.log` | `set -o pipefail` + the same pipeline |

All **10** check-runs on `7cb7789a` are `completed/success`, including the new
`verdict-step-integrity` gate and `validate`. The fix is therefore proven at runtime, not
only in source: the previously-empty outcome now resolves, and the grove step can fail.

## 3. Change

| File | Change |
| --- | --- |
| `.github/workflows/sg-02-fe-2-v.yml` | declare `id: grove`; `set -o pipefail`; enforce via `test '${{ steps.grove.outcome }}' = success` |
| `tests/test_ci_verdict_step_integrity.py` | NEW — pure-source guard, 13 tests |
| `tests/test_ci_verdict_step_integrity_ci_wiring.py` | NEW — wiring guard, 12 tests |
| `.github/workflows/ci-verdict-step-integrity.yml` | NEW — executable surface for the guard |

The grove step is a **blocking** step (unlike its `continue-on-error` siblings), so it is
held to the outcome-based enforcement form those siblings already use. Repairing the step
and enforcing it are the **same** change: a step that can fail and is not checked is still
decoration.

The guard is **pure source**: it parses `.github/workflows/*.yml` and needs no application
dependency beyond `pytest` and `pyyaml`, so a dependency gap cannot be misreported as a
verdict-integrity defect.

`masked` is defined as **enforced AND destroys its own status**. An unmasked masked-pipe
(a `continue-on-error` step piping to `tee`) is not reported — the verdict already survives
via `outcome`.

## 4. Verification

Measured in this environment, `PYTHONPATH=archive/legacy_python`.

### 4.1 Regression — node identity, not counts

| Tree | Result | Node set sha256 |
| --- | --- | --- |
| `main` `850216fc` | 17F / 2644P / 20S / 1E (18 nodes) | `7eaa2c116c12b9e0a3993229db647bb76655c95983534db58a6fb171ceed6f6c` |
| branch | 17F / 2674P / 20S / 1E (18 nodes) | `7eaa2c116c12b9e0a3993229db647bb76655c95983534db58a6fb171ceed6f6c` |

`comm -3` on the sorted node lists is **empty**. Zero regression.

### 4.2 The `+30 passed` is fully attributed

Per-file `--collect-only` diff (2680 → 2710 collected):

| File | Δ |
| --- | --- |
| `tests/test_ci_verdict_step_integrity.py` | +13 |
| `tests/test_ci_verdict_step_integrity_ci_wiring.py` | +12 |
| `tests/test_ci_gate_trigger_coverage.py` | +3 |
| `tests/test_ci_suite_collection_continuation.py` | +1 |
| `tests/test_workflow_injection_boundary.py` | +1 |

The last three enumerate `.github/workflows/*.yml` and gain nodes **by construction** from
one new workflow file. No unexplained delta.

### 4.3 The repair is required, not optional — the guard fails on unpatched `main`

Run against `origin/main` @ `850216fc` with only the guard test file added:

```
1 failed, 12 passed
FAILED test_no_workflow_references_an_undeclared_step_id
  sg-02-fe-2-v.yml [validate] step 'CP10 evidence summary' -> steps.grove
```

`main` echoes `${{ steps.grove.outcome }}` in `CP10 evidence summary` while no step
declares `id: grove`. The guard is therefore **red on main** and green only with this
change: the repair and the guard are one coupled unit.

### 4.4 Live negative controls (on the real file, not a synthetic fixture)

Composed tree in a real worktree (`origin/main` + PR #458 patch + this patch).

| Mutation of `.github/workflows/sg-02-fe-2-v.yml` | Result |
| --- | --- |
| (none) | **25 passed** |
| remove `id: grove` | 1F — `test_no_workflow_references_an_undeclared_step_id`, naming **both** reference sites (`CP10 evidence summary`, `Enforce CP10 executable gates`) |
| remove `set -o pipefail` | 1F — `test_masked_enforced_steps_are_the_registered_set`, `[('sg-02-fe-2-v.yml','grove')]` |

Restored byte-identically (`sha256` prefix `1cdc02158659011d`) → **25 passed**.

### 4.5 The detector catches a live defect in an open PR — PR #432

PR **#432** (`feat/prism-next2-04-run-evidence-trace`, head `e4b555ca`, **draft**,
`CONFLICTING`) introduces a step in `sg-02-fe-2-v.yml` at line 240:

```yaml
      - name: CP10-C Workstream 4 read surfaces
        id: w4_surfaces
        working-directory: .
        run: |
          python -m pytest \
            tests/test_prism_w4_lab_read_model.py \
            ...
            -q 2>&1 | tee cp10-w4.log
```

It is **blocking** (no `continue-on-error`), the pipeline is **continuation-folded**, and
there is **no `pipefail`**, so its exit status is `tee`'s. Measured on #432's own tree
(`850216fc` + #432's patch; only `AGENTS.md` conflicts, and that is #432's known state):

```
2 failed, 11 passed
FAILED test_no_workflow_references_an_undeclared_step_id
FAILED test_masked_enforced_steps_are_the_registered_set
  enforced verdict steps that destroy their own exit status and are not
  recorded: [('sg-02-fe-2-v.yml', 'w4_surfaces')]
```

This is **evidence, not scope**. #432 is a draft owned by another workstream; the repair
belongs to #432, not here. Recorded so the detector's value is demonstrated on live code
rather than only on synthetic fixtures.

### 4.6 Composition with the open PR that shares this file

PR **#458** (`gate10/gate-filter-selection-01`, head `30c87f26`, `MERGEABLE`/`CLEAN`) also
edits `sg-02-fe-2-v.yml`, at the `paths:` filters (~line 26 / ~57). This change edits the
grove step (~190) and the enforcement step (~565). `git apply --3way` of #458 then of this
patch applies **cleanly**, no `UU`, and both are present — `id: grove` (190), `pipefail`
(194), `steps.grove.outcome` (531, 565), and #458's nine new filter paths (210).

Different hunks in one file is a **textual** result. The load-bearing claim is that the
composed tree passes the guard — measured above (25 passed on that tree).

### 4.7 Protected surfaces

- Architecture fitness: **11 passed**.
- `tests/test_m02a_ci_gate_integrity.py`: **68 passed**.
- CP10 mutation boundary judge: **PASS** for all four changed paths.
- `python -m py_compile api/main.py`: clean. Budget **2505 / 2600** (`api/main.py` untouched).

## 5. Scope and authority boundary

- 4 files. No application code, no `api/main.py`, no authority surface, no identity
  boundary, no new mutation path.
- **No merge, no production deployment, no acceptance.** Human sovereign authority is final.

## 6. Remaining uncertainty

- PR #432 is now a **draft** and `CONFLICTING` with `main`; its head moved after the first
  composition check (`e4b555ca`). The earlier #432 composition result is therefore
  **superseded** and is not cited as current evidence. #432 is not a blocker for this
  change: the only shared file is `sg-02-fe-2-v.yml`, and the composition proven here is
  with #458, the other live PR on that file. #432's `w4_surfaces` finding (§4.5) is
  reported as evidence about #432's own tree, not as work for this change.
- The guard's domain is the tracked workflow corpus. A workflow added in a **sibling**
  branch composes into the domain without entering this gate's `paths` filter unless that
  branch also touches a selected path. This is the same content-derived-domain hazard
  recorded in `gate10-prism-console-contract-domain-completion-01`; the wiring guard here
  asserts the gate selects the **whole corpus** and itself, which bounds the drift for
  workflows but is not a general solution. Recorded, not repaired — widening an execution
  surface is a separate bounded workstream.
- `w4_surfaces` is flagged as a masked enforced verdict step. Registering it in
  `REGISTERED_MASKED_VERDICT_STEPS` requires the *measured reason* for its masking; that
  measurement is **not** in this change's scope and is not claimed here.
