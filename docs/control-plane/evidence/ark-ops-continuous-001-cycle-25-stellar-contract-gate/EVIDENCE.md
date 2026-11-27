# ARK-OPS-CONTINUOUS-001 — cycle 25: the stellar contract has a guard, and now a gate

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `cb2841956bcc0397007b9efffbaa8cc6d0801836` (observed 2026-11-26T06:06Z)
**Head:** `gate-hygiene/stellar-contract-gate-01`
**Authority:** implementation, tests and evidence only. No merge, no deployment, no
acceptance, no push to `main`.

---

## 1. The defect

`kernel/stellar.py` computes the readout served at `GET /api/stellar-cartography` and
rendered as the console star-date header. It is also a **second implementation of the
Ark Date**, and it says so in its own docstring:

```
Mirrors api.main._ark_date exactly; duplicated here to avoid a circular
import through api.main's heavy dependency tree.
```

Two facts were measured against `main` @ `cb284195`.

**1.1 The stated equivalence was enforced nowhere.** The only test naming the pair,
`tests/test_stellar_cartography.py::test_ark_date_in_stellar_matches_canonical_shape`,
asserts the *shape* of the stellar copy (`ark_year >= 1`, `ark_total_years == 8`,
`"Y" in display`, `"Birthday Seal" in epoch`). It never imports `api.main` and never
compares the two implementations, so a change to either epoch, duration, rounding, or
coordinate format would leave the two copies disagreeing with every test green — and
the disagreement is user-visible, because the same coordinate is rendered in the header
and served elsewhere in the API.

**1.2 No workflow selected the engine at all.**

```
$ grep -rn "kernel" .github/workflows/
.github/workflows/phase6-persistent-execution.yml:6:      - 'kernel/jobs.py'
.github/workflows/phase6-persistent-execution.yml:7:      - 'kernel/worker.py'
.github/workflows/phase6-persistent-execution.yml:14:      - 'kernel/jobs.py'
.github/workflows/phase6-persistent-execution.yml:15:      - 'kernel/worker.py'
```

`kernel/stellar.py` is named by no `paths:` filter, and no gate executes
`tests/test_stellar_cartography.py`. A change to the engine — or to the parity claim
above — ran no gate. This is the class this repository already records: **a guard no
workflow executes is decoration.** (The engine is still reached by the whole-suite step
on `provider-routing.yml`, but that workflow is path-filtered to `weaver/**`,
`providers/**`, two named test files and one doc, so a `kernel/**`-only change selects
it nowhere.)

Neither half is owned by an open pull request. The one open PR that touches the file,
`#730` (`test-hygiene/vacuous-assertion-binding-01`), binds the file's vacuous
`assert "api.main" not in sys.modules or True` to a real AST import scan. That is a
different property (the engine must not import the app) and it adds **no workflow**, so
it closes neither gap above.

---

## 2. The change

Four files, all additive; no existing behaviour is modified.

| Path | Purpose |
|---|---|
| `scripts/stellar_contract_domain.py` | The single derivation of the guard domain. `derive_domain()` scans tracked `tests/**/test_*.py` for the engine's import spellings; `--json` and one-path-per-line CLI; **fails closed** (exit 2) on a git fault or an empty domain. |
| `tests/test_stellar_ark_date_parity.py` | The parity guard. Compares `kernel.stellar._ark_date()` with `api.main._ark_date()` field by field at four pinned instants with the clock frozen, and asserts the two constants agree. |
| `.github/workflows/stellar-cartography-contract.yml` | The gate. Runs `python -m pytest -q $(python scripts/stellar_contract_domain.py)` — a **derived** inventory, so a guard added to the domain is executed without editing the workflow. |
| `tests/test_stellar_contract_ci_wiring.py` | The wiring judge. Imports `derive_domain` from the same script, so gate and judge cannot disagree. |

The gate and the judge derive from one source, mirroring `scripts/console_contract_domain.py`
and `tests/test_prism_console_ci_wiring.py` rather than inventing a second convention.

### 2.1 Why the clock is frozen rather than the code being duplicated

`_ark_date()` reads `datetime.now(timezone.utc)` in both modules. The guard replaces
that module attribute with a frozen instant in each module and then calls both real
implementations — the logic under test is the shipped logic; only the clock is pinned.
A textual source comparison would not catch a behavioural divergence, and would pass on
two different expressions that happen to look alike.

### 2.2 The gate's trigger filter

`kernel/stellar.py`, `api/main.py` (the other half of the invariant),
`scripts/stellar_contract_domain.py`, `tests/**` and the workflow itself — identical for
`pull_request` and `push: main`, plus `workflow_dispatch`.

`tests/**` is selected rather than an enumerated guard list for the reason recorded on
the console gate: a guard **added** to the derived domain must also trigger the judge
that would otherwise never run to report it unexecuted. The judge asserts every derived
guard is selected, so narrowing the filter reddens it.

`fetch-depth: 0` is set for the same reason the console gate sets it: the domain is
derived and grows, and a guard that resolves a revision with `git cat-file -e` would
fail inside a depth-1 checkout as a *wiring* defect that reads as a stellar defect.

---

## 3. Verification

### 3.1 The gate command, run exactly as CI runs it

```
$ python scripts/stellar_contract_domain.py --json
{
  "domain": [
    "tests/test_stellar_ark_date_parity.py",
    "tests/test_stellar_cartography.py",
    "tests/test_stellar_contract_ci_wiring.py"
  ],
  "count": 3
}

$ python -m pytest -q $(python scripts/stellar_contract_domain.py)
32 passed in 1.65s
```

The wiring judge is a member of the domain it derives (it names the engine), so the
gate executes the judge that judges the gate.

### 3.2 Live negative controls — the detectors bite on the **real** files

Each mutation below was applied to the real file, the suite re-run, and the file
restored byte-identically (`sha256sum -c` OK in every case).

| Mutation (real file) | Measured |
|---|---|
| `stellar-cartography-contract.yml`: replace the derived invocation with a fixed inventory (`pytest tests/test_stellar_cartography.py`) | `1 failed, 12 passed, 2 errors` |
| `stellar-cartography-contract.yml`: drop `api/main.py` from the `pull_request` filter | `2 failed, 13 passed` |
| `stellar-cartography-contract.yml`: `continue-on-error: true` on the executing step | `2 failed, 13 passed` |
| `kernel/stellar.py`: shift `ARK_EPOCH` by one day | `5 failed, 2 passed` |

The last row is the decisive one: the parity guard fails on a genuine divergence in the
shipped source, so it is not a comparison that passes on two identical constants.

### 3.3 The guard's own control was vacuous on the first attempt — recorded

The first `test_negative_control_a_shifted_epoch_is_reported` shifted
`api.main.ARK_EPOCH` by one day and compared at the epoch instant. It reported **no
mismatch**, because both implementations clamp `max(1, delta.days + 1)`: at (or before)
the epoch a one-day shift is absorbed by the clamp. The control was measuring the
clamp, not the comparison. It now compares at a mid-Ark instant and shifts the epoch to
a date that cannot coincide with the shipped one (`2025-01-01`), so it stays valid under
any future epoch choice.

### 3.4 Regression: the failing/error node set

Full suite, same environment, `-rEf --continue-on-collection-errors`, both trees:

| Tree | Result | Failing/error node set |
|---|---|---|
| `main` @ `cb284195` (before) | `22 failed, 4251 passed, 22 skipped, 1 error` | 23 nodes, `sha256 d3ec2007…` |
| branch (after) | `22 failed, 4280 passed, 22 skipped, 1 error` | 23 nodes, `sha256 d3ec2007…` |

```
$ comm -3 nodes-main.txt nodes-branch.txt     # sorted FAILED/ERROR node lists
                                              # (no output: the sets are identical)
```

**Zero node drift.** The `+29 passed` is fully attributed, not inferred from the delta:
`--collect-only` over the two new files reports **22** tests, and the four generic
workflow-scanning suites gain **7** nodes by construction from the one new workflow file
(`test_ci_gate_trigger_coverage.py` ×3, `test_workflow_injection_boundary.py` ×1,
`test_ci_suite_collection_continuation.py` ×2, `test_gate_filter_selection.py` ×1), each
parametrized on `stellar-cartography-contract.yml`. 22 + 7 = 29.

Totals alone are not the comparison: the passed count moves with the dependency set and
with nodes gained by construction. Node identity is.

### 3.5 Repository meta-guards this change touches

```
$ python -m pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py \
    tests/test_ci_suite_collection_continuation.py tests/test_m02a_ci_gate_integrity.py \
    tests/test_gate_filter_selection.py tests/architecture -q -rEf
395 passed in 4.80s

$ printf '%s\n' .github/workflows/stellar-cartography-contract.yml scripts/stellar_contract_domain.py \
    tests/test_stellar_ark_date_parity.py tests/test_stellar_contract_ci_wiring.py \
    | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

`tests/test_console_stellar_cartography_contract.py` (the console half of the readout,
already executed by `prism-console-contract.yml`) is untouched and still `13 passed`.

### 3.6 The wiring is runtime-proven, not source-asserted

The judge asserts the gate *executes* the domain; the run proves it. On PR #746 head
`19de1804`, run **`45768508248`** (`event=pull_request`, `conclusion=success`) carries
the new check-run `stellar-contract`, and its step log reads:

```
Run the derived stellar contract
32 passed in 2.44s
```

Read from the step log rather than the job conclusion: a job can be green while its
step executed nothing, which is a recorded failure mode in this repository. The count
matches the local derivation exactly (3 guards, 32 nodes).

All **12** checks on that head are `completed/success` (plus the `skipping` Arkadia
Genesis Agent), and the PR is `MERGEABLE` / `CLEAN`. It stays a **draft**: this
contract authorizes no merge, and a green branch is not a merge.

---

## 4. What this cycle did not do, and why

- **No repair of any failing node.** All 23 failing/error nodes measured on `main` are
  owned by an open PR, environment-only, or sovereign-reserved:
  `test_autonomy.py` (CE-01), `test_gov04_*` (`#725`), `test_m01_persistence` /
  `test_m05_files` (`#690`), `test_solspire_r3` (`#691`), `test_solspire_r1` (`#693`),
  `test_static_ingestion_idempotency` (`#698`), `test_identity_spine_w1` /
  `test_m02_reasomate_truth` (`#700`), `test_prism_w4_lab_pr_state` (`#683`),
  `test_mission_lifecycle_adapter_contract` (10 nodes — `web/arkadia_console/node_modules`
  is not installed in this sandbox; the guard asserts the repository TypeScript compiler
  exists), and `test_ais_w2_living_gate_grove_handoff` (a recorded governance decision:
  re-pinning it would loosen a persistence boundary).
- **No repair of the `prism_coherence_check.py` verdict.** It reports `FAIL` on 31
  tracked READMEs; the domain defect is `#734`'s scope and the findings are a reserved
  identity decision.
- **No repair of `GET /api/codex/github-tree` → 502.** Measured live in this cycle (§6)
  and fully owned: `#701` supplies the anonymous credential fallback in the fetch path,
  `#729` removes the exception text from the 502 body.
- **No new `api/main.py` line.** It stays at 2597/2600.
- **No draft conversion, no merge, no deployment, no acceptance.**

---

## 5. Next-action block

**Current state.** `main` = `cb2841956bcc0397007b9efffbaa8cc6d0801836`. Production
`source_revision` = `cb284195…` (`GET /api/version`, `revision_source:
RENDER_GIT_COMMIT`, `revision_conflict: false`) — **VERIFIED for revision identity
only**; production acceptance is **NOT CLAIMED**. 64 open PRs: 63 drafts, 1 ready.

**Evidence.** §1 (defect, with the `grep` transcript), §2 (four additive files), §3.1
(the gate command and its derived domain), §3.2 (four live negative controls), §3.3
(the control that was vacuous and why), §3.4–§3.5 (node-set and meta-guard results),
§6 (live production observations).

**Blocker.** Human, unchanged: nothing merges until a human reviews a candidate
(`#679` is the only ready one, `CLEAN`, 16/16 checks) or makes another draft ready. This
is not an engineering gap and no agent may cross it.

**Authorized action for the next cycle.** Re-derive `main`, the production revision and
the queue (one read each); re-run the failing-node set and re-classify by owner; re-run
the duplicate added-path scan before trusting the queue; re-assess any newly-ready
candidate. Record the result in the cycle-26 record. Do **not** open a PR unless a
defect is found that is neither reserved nor owned.

**Forbidden.** Merge execution, draft conversion, push to `main`, force-push,
protection/check bypass, deployment, provider configuration, acceptance, and any claim of
production parity beyond revision identity.

**Completion condition.** State re-derived; the node set re-classified by identity with
zero drift; one unowned gap closed with a guard that fails on the defect and passes on
its absence; the guard executed by a gate that selects every input it reads; the human
blocker named.

---

## 6. Live production observations (2026-11-26)

Read-only, canonical origin `https://arkadia-qzu4.onrender.com`.

| Observation | Result |
|---|---|
| `GET /api/version` | `200`, `source_revision` `cb284195…`, `revision_conflict false` |
| `GET /health` | `200` |
| `GET /api/stellar-cartography` | `200`, 3800 B |
| `GET /api/tts/status`, `/api/tts/voices` | `200` |
| `GET /api/codex` | `200`, 722 docs (served from the local fallback — see below) |
| `GET /api/echoes` | `200`, 400 KB |
| `GET /openapi.json` | `200`, 274 KB |
| All 15 declared console surfaces (`web/arkadia_console/src/lib/surfaces.ts`) | `200`, SPA shell (`id="root"` present) on every one |
| `python scripts/production_runtime_probe.py` | 344 operations inventoried, 344/344 source match; 39 reachable, 105 protected, **1 failing**, 6 resource-404, 9 shape-422 |

The single failing operation is `GET /api/codex/github-tree` → `502`, body
`{"error":"Client error '401 Unauthorized' for url 'https://api.github.com/repos/…/git/trees/main?recursive=1'…"}`.
Root cause verified independently: the repository is **public**
(`GET /repos/Arkadia-Oversoul-Prism/Arkadia` anonymously → `200`, `"private": false`) and
the identical anonymous tree read returns `200` with 3216 entries, so the failure is a
**refused credential with no anonymous fallback**, not a missing permission. Owned by
`#701` (fallback) and `#729` (exception text in the body); recorded here, not repaired.

The first `/api/version` attempt timed out at 25 s (Render cold start) and succeeded on
retry in 2.1 s — recorded so a later cycle does not read a cold start as an outage.
