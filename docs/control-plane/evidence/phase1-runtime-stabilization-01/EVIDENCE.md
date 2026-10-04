# PHASE 1 · Runtime Stabilization — baseline reconstruction and node classification

**Status:** OBSERVED — classification record (no repair in this artifact)
**Date:** 2026-10-03
**Measured at:** `d798811e6197db8cdb46fe5302f274765cd6f883` (main) and branch
`gate10/cp10-allowlist-arkadia-console-android` (HEAD `8ee8d4b`)
**Gate:** Phase 1 (runtime stabilization) · feeds GATE-10

## 1. Objective

Reconstruct the runtime test baseline from live evidence, classify each failing /
erroring node as *real regression*, *environment*, or *test-side literal defect*,
and reconcile against the recorded baseline node set
(`tests/fixtures/baseline_node_set.txt`, 18 nodes).

This artifact **records** the classification. It repairs nothing beyond the CP10
allowlist omission, which is carried separately on the same branch
(`docs/control-plane/evidence/gate10-cp10-allowlist-arkadia-console-android/EVIDENCE.md`).

## 2. Environment (required for reproduction)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
```

`pyyaml` and the `archive/legacy_python` path are required for full-suite
reproducibility; a bare `pytest tests/` interrupts at the collection error and
under-reports the run. Counts are not a stable oracle — see §5.

## 3. Measured baseline

| | before CP10 repair | after CP10 repair |
|---|---|---|
| result | 30 failed, 1354 passed, 20 skipped, 1 error | 27 failed, 1357 passed, 20 skipped, 1 error |
| failing/error node set | 31 | 28 |
| architecture suite | 11 passed | 11 passed |

The node-set delta is exactly the three `test_m02a_ci_gate_integrity.py` nodes.

## 4. Classification

### 4.1 Repaired by this pass — real, repository-owned defect (3 nodes)

- `test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix`
- `test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
- `test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface`

**Class:** allowlist omission (real). `main` tracks `arkadia-console-android/` and
the CP10 policy does not admit it. Now 55 passed.

### 4.2 Test-side literal / regex defects (10 nodes) — *not* regressions

The recurring class `AGENTS.md` records: the assertion does not match the source's
own template or copy. Measured samples:

| node | measured assertion failure |
|---|---|
| `test_solspire_project_instantiation_ui.py::test_arkana_injects_bounded_project_context_and_scopes_threads` | demands literal `runtime integration is verified separately`; source copy differs |
| `test_solspire_project_instantiation_ui.py::test_project_runtime_context_uses_canonical_spines_without_inventing_project_bindings` | demands expanded `/solspire/projects/${pack.projectId}/tasks`; source emits a template |
| `test_solspire_project_instantiation_ui.py::test_projects_ui_uses_server_owned_template_catalog` | demands `"Project records are data/evidence, not authority."`; near-miss copy |
| `test_solspire_project_templates.py::test_eden_template_declares_living_larder_without_claiming_it_is_live` | literal pin on template copy |
| `test_solspire_p1_experience_01.py::test_p1_1_arkana_context_pack` / `::test_p1_1_not_authorization` | literal pins on the P1 context pack |
| `test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount` | literal pin |
| `test_evidence_verification_boundary.py::test_console_authority_routes_expose_evidence_and_verification_separately` | **superseded boundary assumption**: the intended Console authority routes are present; Option A ruling recorded in `RECONCILED-BOUNDARY-MAP-01.md` |
| `test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record` | regex matched `patches/preview`, not a review route — **false positive** |
| `test_workevent_evidence_boundary.py::test_console_exposes_evidence_verification_but_not_enterprise_walk` | **superseded boundary assumption**: first-class evidence/verification routes are intended; enterprise walk remains unexposed |

**Class:** mixed. The review/preview match is a test-side false positive. The two
evidence/verification nodes encoded an obsolete route-absence assumption. Under
the sovereign's 2026-10-04 Option A ruling, the Console authority bridge is an
intended first-class surface; those tests now assert the declared route contract
and preserve the separate requirement that enterprise lineage traversal remain
unexposed. This does not by itself establish production verification.

### 4.3 `AGENTS.md` encoding adjudication (3 nodes) — known constraint

- `test_agents_md_encoding_adjudication.py::test_live_file_verdict_matches_its_state`
- `::test_cli_summarises_the_oracle_without_crashing`
- `::test_corruption_origin_is_re_derivable`

**Class:** known. `AGENTS.md` is under a standing insertion-only constraint against
oracle revision `6c43218a4`; the live file diverges in ways the audit adjudicates.
Repairing it requires appending corrections, never rewriting oracle lines.

### 4.4 Remaining pre-existing recorded debt (12 nodes)

Recorded in `tests/fixtures/baseline_node_set.txt`: `test_steward_filter` (3),
`test_solspire_r1_governance_convergence` (2), `test_solspire_r2_github_mutation`,
`test_solspire_r3_execution_runtime`, `test_spiral_grove_registry` (2),
`test_authority_api_enterprise_boundary`, `test_ais_w2_living_gate_grove_handoff`,
`test_identity_spine_w1`, `test_m02_reasomate_truth`, plus the
`test_autonomy.py` collection ERROR (`weaver.autonomy` module-vs-package collision —
reserved to the sovereign).

### 4.5 Recorded debt now passing (3 nodes)

- `test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`
- `test_upstream_causal_continuity_01.py::test_api_approval_does_not_create_enterprise_authorization`
- `test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`

**Class:** stale fixture entries. The lazy-schema materialization repair recorded in
`AGENTS.md` (PR #228) and the Solariun thread wiring have landed; the recorded set is
now conservative. No regression.

## 5. Why counts are not the oracle

`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
snapshots global `git status` and is order-dependent under the full suite, so the
*passed* count varies between runs of the same tree. Attribution must use the sorted
node set, not the counts. Measured on this branch the node set is stable at 28.

## 6. Proposed next bounded workstreams (not authorized here)

Each is a candidate **separate** branch/PR; none is a dependency of the CP10 repair:

1. `test-hygiene/frontend-literal-pins-01` — repair §4.2 (10 nodes) by matching the
   assertions to the source templates, with a negative control per repair.
2. `test-hygiene/boundary-regex-false-positives-01` — §4.2 boundary regexes that
   match substrings inside unrelated paths.
3. `gate-hygiene/baseline-node-set-reconciliation-02` — retire the 3 stale entries
   in §4.5 and record the 13-node delta.
4. `weaver/autonomy-module-collision-01` — the collection ERROR; sovereign-reserved.

## 7. Authority boundary

Read-only measurement plus a classification record. No test repaired in this
artifact; no merge; no push to `main`. Human authority is required to merge.

## 8. Integration re-measurement after the CP10 repair (2026-10-03)

PR #240 merged as `444d5cd` (2026-10-03T17:45:33Z). `main` then advanced through
#241 `f206e77`, #242 `7f2d265`, #244 `357fbd8`. Re-measured on `main` @ `357fbd8`
(clean worktree, `PYTHONPATH=archive/legacy_python`, `--continue-on-collection-errors`):

| | value |
|---|---|
| result | **24 failed, 1367 passed, 19 skipped, 1 error** |
| failing/error node set | **25** |
| architecture + CP10 fitness | **66 passed** (`tests/architecture` + `test_m02a_ci_gate_integrity.py`) |
| CP10 judge | `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` -> **RC 0**, PASS |
| `py_compile api/main.py` | OK (2582 lines, budget 2600) |

**Node-set delta from the branch measurement (28 -> 25): exactly the three
`test_m02a_ci_gate_integrity.py` nodes repaired here; nothing added.** The CP10
allowlist is verified integrated on `main`: the judge admits all **1732** tracked
paths and the three fitness nodes pass there.

The three repaired nodes are still listed in `tests/fixtures/baseline_node_set.txt`
and now pass, so the fixture is stale by them — §4.5 is confirmed on `main`, not
only on the branch.

### 8.1 Node-set vs the recorded fixture

`tests/fixtures/baseline_node_set.txt` (18 entries, written at `d798811`) is a
historical baseline, not a live oracle. The current 25-node set splits against it:

- **14** fixture entries still failing;
- **4** fixture entries now passing (stale): `test_agents_md_encoding_adjudication::
  test_exit_code_does_not_call_a_divergent_clean_file_verified`, plus the three
  named in §4.5 (`test_authority_api_enterprise_boundary`,
  `test_upstream_causal_continuity_01`, `test_solariun_thread_navigation_01`);
- **11** failing nodes absent from the fixture — none introduced by this repair
  (all present at `cc95487`, before the CP10 change): `test_steward_filter` x3,
  `test_solspire_project_instantiation_ui` x3, `test_spiral_grove_registry` x2,
  `test_solspire_p1_experience_01` x2, `test_evidence_verification_boundary`,
  `test_verification_review_boundary`, `test_workevent_evidence_boundary`,
  `test_solspire_project_execution_service`, `test_solspire_project_templates`,
  and the `test_autonomy.py` collection ERROR.

Refreshing the fixture is **not** done here; it is workstream 3 in §6.

### 8.2 Withdrawn claims from this pass

Two claims made during this pass were **wrong and are withdrawn**:

1. "The CP10 gate is path-filtered and does not run on `arkadia-console-android/**`
   changes." `sg-02-fe-2-v.yml` does not filter on console paths, so a console-only
   merge such as `444d5cd` is **skipped, not passed** by that workflow. The console
   is covered by its own build gate, `.github/workflows/arkadia-console-android.yml`
   (`gradle assembleDebug`, triggers on `arkadia-console-android/**` for both
   `pull_request` and `push: main`). CP10 is exercised on console merges transitively:
   its trigger list includes `scripts/cp10_mutation_boundary_policy.py` and
   `tests/test_m02a_ci_gate_integrity.py`.
2. "`arkadia-console-android/` was first tracked by PR #237 (`cc95487`)." Measured:
   the tree first appears on `main` at `8806f38`, an ancestor of `cc95487`; the
   allowlist's own prose (PRs #233/#234/#235) is accurate. Path counts are `d798811`
   **1726** and `cc95487` **1727**, so `main`'s "1726 at the console merge" is
   correct for the revision the fixture was written at.

## 9. PR #245 integration evidence (branch `gate10/persist-phase1-runtime-state-01`)

Head `17bf337`. Measured 2026-10-03.

- `validate` (CP10 `sg-02-fe-2-v.yml`) — **pass**, 1m31s. The policy file is inside the
  workflow's path filter, so the delegated judge ran on this PR's diff and returned RC 0.
- `Full-history secret scan` — **pass**, 11s.
- `Vercel – arkadia-prism` — **pass** (preview built).
- `Vercel – console` — **fail**, "Deployment rate limited — retry in 24 hours." This is
  **not** attributable to this PR: the same failure is present on `main`'s merged tip
  `357fbd8` and on `f206e77`, `7f2d265`, `444d5cd`. Provider-side build rate limit.
  This PR touches **no** `arkadia-console-android/` path, so the console gate
  (`arkadia-console-android.yml`, path-filtered to `arkadia-console-android/**`) does not
  run for it at all.

Changed paths (three): `.bootstrap/01_STATE.md`,
`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`,
`scripts/cp10_mutation_boundary_policy.py` (comment-only).

## 10. Authority boundary (this pass)

Read-only measurement plus in-repo state persistence on a dedicated branch. No test
repaired, no merge, no push to `main`. Human authority is required to merge.
