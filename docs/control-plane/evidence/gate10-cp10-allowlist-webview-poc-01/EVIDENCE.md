# gate10/cp10-allowlist-webview-poc-01 — admit `arkadia-webview-poc/` to the CP10 boundary

**Status:** IMPLEMENTED — repair proven locally, PR open, human merge required.
**Branch:** `gate10/cp10-allowlist-webview-poc-01`
**Base:** `main` @ `f2a7158f11ade7edeaaa297cef2769a82c6f7ebc`

## 1. Defect (measured, not inferred)

`scripts/cp10_mutation_boundary_policy.py` is the CP10 mutation-boundary allowlist, and its
completeness is asserted against the live tracked corpus by
`tests/test_m02a_ci_gate_integrity.py`. Every path in `git ls-files` must be admitted, or the
gate rejects the next ordinary commit touching an omitted tree.

`arkadia-webview-poc/` is tracked on `main` (9 files) and is omitted from the allowlist. It was
introduced by PR #608 (merge `e67c1faf0a`), which added the Android WebView POC and its build
workflow `.github/workflows/arkadia-android-webview-poc.yml`.

Measured on `main` @ `f2a7158f11`:

```
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
```

`AssertionError: allowlist omits tracked top-level prefixes, so a non-merge commit touching
them fails CP10: arkadia-webview-poc`

This is the documented GATE-10 allowlist-omission class (prior instances: `deploy/` #354/#352,
`growth/` #399, `reconciliation/` #182, `opportunity_radar/` #118, `economic_seams/`,
`musical-intention-engine/`, `research/`+`schemas/`, `federation/`).

### 1.1 Why it landed silently

The gate is **path-filtered**. `sg-02-fe-2-v.yml` selects `web/arkadia_console/**`,
`spiral_grove/**`, `lab/**`, `api/lab_routes.py` and named test files; the
`economic-seam-engine` gate selects `tests/**`. PR #608 touched neither, so **no gate executed
the completeness invariant at `e67c1faf0a`**, and `main` went red without any check reporting
it. Confirmed from live check-runs: `main` @ `f2a7158f11` carries only
`weaver_evolution (skipped)`, `lane-doc-currency (success)`, `Full-history secret scan (success)`
— the CP10 gate did not run.

The defect surfaced on PR #614 only because that PR touches `tests/**` (a Lane 1 guard file),
which selects `economic-seam-engine`; the gate then executed `test_m02a_ci_gate_integrity.py`
and failed on the pre-existing `main` omission. **The failure is not caused by PR #614's own
diff**, which touches only Lane 1 owned paths
(`docs/control-plane/parallel-ui/AGENT-01-SHELL.md`, `lane-state.json`,
`tests/test_console_legacy_route_coverage.py`).

## 2. Repair

One line added to `LEGIT` in `scripts/cp10_mutation_boundary_policy.py`:

```
r"|arkadia-webview-poc/"
```

The trailing slash keeps it from over-admitting lookalike roots
(`arkadia-webview-poc-evil/`, `arkadia-webview-pocx/`). `arkadia-webview-poc/` is a
first-class product surface — a companion Android client with its own build workflow — so it is
enumerated rather than left to the generic rules, matching the treatment of
`arkadia-console-android/`.

Plus four companion pin tests in `tests/test_m02a_ci_gate_integrity.py`, following the
`federation/` convention: the surface is legitimate, the exact shipped change set passes, the
admission is not overbroad (lookalikes rejected), and the delegated CLI reaches the same verdict.

## 3. Verification

| check | result |
|---|---|
| `tests/test_m02a_ci_gate_integrity.py` before | 3 failed / 65 passed |
| `tests/test_m02a_ci_gate_integrity.py` after | **72 passed** |
| `--collect-only` delta | 68 -> 72 (+4 = exactly the new pins) |
| judge CLI on `arkadia-webview-poc/README.md` | PASS, exit 0 |
| `tests/architecture` | **11 passed** |
| `tests/test_ci_gate_trigger_coverage.py` + `tests/test_gate_filter_selection.py` | **146 passed** |
| full suite (once, `-q -rEf --continue-on-collection-errors`) | 11 failed / 3828 passed / 1 error |

### 3.1 Live negative control

Removing `r"|arkadia-webview-poc/"` from the real policy module and re-running the guard:

```
FAILED ...::test_webview_poc_surface_is_legitimate
FAILED ...::test_shipped_webview_poc_changeset_passes_policy
FAILED ...::test_delegated_verdict_admits_webview_poc_and_rejects_lookalikes
FAILED ...::test_allowlist_admits_every_tracked_top_level_prefix
FAILED ...::test_allowlist_covers_every_tracked_surface
FAILED ...::test_delegated_verdict_admits_every_tracked_surface
6 failed, 66 passed
```

Exactly the three new pins plus the three completeness invariants redden — the detector reads
the real file and the pins are not vacuous. The file was restored byte-identically
(sha256 `b1a4342f...` before and after) and the suite returned to **72 passed**.

## 4. Baseline debt (recorded, not repaired)

Full-suite failing/error node set at `main` @ `f2a7158f11` — 12 nodes,
sha256 `06fe4438aaddbbb8cf83da0343123057c3680a1d831ce911ceb0ac38e310d4aa`:

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

This change removes exactly the three `test_m02a_ci_gate_integrity.py` nodes. The other nine are
pre-existing and unowned; they are recorded, not repaired. (`tests/test_autonomy.py` is the
CE-01 `weaver.autonomy` module-vs-package collision reserved to the sovereign.)

## 5. Scope

Touched: `scripts/cp10_mutation_boundary_policy.py`, `tests/test_m02a_ci_gate_integrity.py`,
this evidence record. No `api/main.py` change (budget untouched). No governance, identity,
authority-model, or constitutional surface altered — the repair *admits a tracked product tree*
and does not weaken the `forbid` stage or the unknown-root rejection. Not a deployment, not an
acceptance.

## 6. Related

- PR #614 (Lane 1, `feat/prism-l1-nexus-subview-disposition-01`) is **not** the cause. Its
  `test` check fails because it selects the economic-seam gate, which fails on this pre-existing
  `main` debt. PR #614's own diff is untouched and unblocked once this lands.
- Recorded follow-on (not executed): the CP10 completeness invariant is only executed by gates
  whose path filters reach `tests/**`. A revision touching a tracked tree that appears in no
  gate's filter can still introduce an allowlist omission silently, as #608 did. Widening a
  workflow's trigger set is a bounded workstream for sovereign review; discovery does not
  authorize execution.
