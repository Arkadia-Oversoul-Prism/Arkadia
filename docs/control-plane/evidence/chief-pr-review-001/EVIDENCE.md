# ARKADIA-CHIEF-PR-REVIEW-001 — evidence

Canonical task: Arkadia issue #748.
Directive: implement a governed PR-review capability of the **existing** canonical
Chief identity, executed through a dedicated GitHub App worker, reusing the
Engineering Lab authorization / job / evidence / verification contracts.

| Field | Value |
|---|---|
| Base revision | `2fb20d43` (`main`, "fix(knowledge): disclose bounded graph title chips (#679)") |
| Repository | `Arkadia-Oversoul-Prism/Arkadia` |
| Capability id | `chief.pr_review` |
| Owner identity | `ARKADIA-CHIEF-001` (existing; **not** re-created) |
| Execution boundary | `lab/engineering_lab` (layer 2) |
| Rollout state | **IMPLEMENTED** — code complete, tested; **no GitHub App is registered**, so `SHADOW` is not reachable in any deployment yet (see §7) |
| Merge / deploy / release | **not implemented, not enabled, structurally refused** |

Evidence states used below are exactly: `VERIFIED`, `FAILED`, `BLOCKED`,
`UNKNOWN`, `OBSERVED`, `NOT CLAIMED`.

---

## 1. What was built

Five surfaces, all extending existing contracts:

| Surface | Change | Contract it reuses |
|---|---|---|
| `lab/engineering_lab/github_app.py` (new) | Installation-scoped worker: App identity, repository allowlist, least-privilege permission matrix, `HttpGitHubReader` (PR metadata, files+patches, check-runs), webhook HMAC verification, typed failures (`WorkerUnavailable`, `GitHubUnavailable`, `RateLimited`) | none — new *worker*, not a new identity |
| `lab/engineering_lab/pr_review.py` (new) | The capability: action gates, rollout derivation, review engine, findings, evidence builder, grant matcher, retry policy, `CHIEF_CAPABILITY_MAP` | `contracts.EvidenceRecord`, `contracts.BoundaryViolation`, `runtime.authorization_is_usable`, `executive_office/control.py` capability vocabulary |
| `lab/engineering_lab/store.py` | `el_authorizations` (human grants) + `el_pr_review_jobs` + `el_pr_review_deliveries` tables; job/delivery/authorization methods | the canonical shared SQLite store (`data/solspire_projects.db`) |
| `lab/engineering_lab/runtime.py` | `authorization_is_usable()` extracted to module level so the Lab dispatch gate and the PR-review publish path share **one** expiry rule | its own existing `_authorization_is_usable` body, moved not duplicated |
| `api/lab_routes.py` | 8 routes (7 account-authenticated + 1 HMAC webhook), mounted through the existing Lab router | `require_lab_auth`, Lab runtime, Lab store |
| `api/openapi_security.py` | `WEBHOOK_HMAC_PATHS` declared before the account guards, so the webhook is disclosed as `github_webhook_hmac` rather than as a bearer route it does not have | its own existing classification machinery |

`api/main.py` is **untouched**. No new layer, no new package, no `api.nodes`
change.

## 2. Architecture conformance

* **One Chief.** `pr_review.OWNER_PRINCIPAL == "ARKADIA-CHIEF-001"`, the existing
  principal. The module mints no identity, opens no conversation, owns no
  memory store, and holds no database of its own. A source-level guard test
  asserts the absence of `sqlite3`, of a second principal constant, and of a
  store class in the module.
* **One authorization engine.** Grants are rows in the Lab's `el_authorizations`
  table via `EngineeringLabRuntime.record_authorization`. The capability can
  *verify* a grant; it has no method that creates one.
* **One evidence architecture.** Runs are `EvidenceRecord`s saved through
  `EngineeringLabStore.save_evidence` under the caller's verified uid.
* **One policy source.** Path admissibility is the canonical CP10 module
  (`scripts/cp10_mutation_boundary_policy.py`), injected by the API layer. The
  capability never re-implements a policy engine.
* **No envelope widening.** `CHIEF_CAPABILITY_MAP` maps actions onto capability
  names the Chief envelope **already** declares; `requires_envelope_change` is
  `false`, and a test asserts the mapping against the live
  `GRANTABLE_CAPABILITIES` / `RESERVED_CAPABILITIES` sets.

## 3. Action boundaries (separate gates)

| Action | Writes GitHub | Gate |
|---|---|---|
| `READ` | no | stage ≥ `IMPLEMENTED` |
| `GENERATE_FINDINGS` | no | stage ≥ `IMPLEMENTED` |
| `PUBLISH_COMMENT` | yes | `ACTIVATED` + activation ref + `ALLOW_COMMENT` + human grant + unchanged head + independent principal |
| `REQUEST_CHANGES` | yes | same, with `ALLOW_REQUEST_CHANGES` |
| `APPROVE` | yes | same, with `ALLOW_APPROVE` |
| `MERGE` | — | **structurally refused**, before the stage is even read |

`MERGE` is refused unconditionally, and there is no route, no event mapping and
no HTTP call in the capability that can reach a merge, a branch write, a
deployment, a status write, or a secret read. Three tests assert that absence
(route paths, `_post_review` body, publish event map).

## 4. Rollout state — derived, not declared

`GET /api/lab/engineering/pr-review/status` returns a **derived** state:

| Derived state | Condition |
|---|---|
| `IMPLEMENTED` | code present; worker not configured |
| `SHADOW` | worker configured (App id + installation + allowlist + token); read-only |
| `ACTIVATED` | worker configured **and** an activation reference is recorded |

A stage string alone never yields `ACTIVATED`; an unrecognised stage is recorded
as `stage_conflict` and falls back to the most restrictive state. This is
`OBSERVED` behaviour with tests, not a claim about any deployment.

**Current state: `IMPLEMENTED`.** No GitHub App exists for this capability, so
no deployment can reach `SHADOW` yet. That is the honest state, and it is the
state the status endpoint reports for an unconfigured worker.

## 5. Tests

`tests/test_chief_pr_review_capability.py` — **70 tests**, all passing.
They exercise the real gates (no mocks of the boundary), with a negative control
wherever a detector could be trivially true:

| Area | Representative tests |
|---|---|
| identity / no-duplication | `test_capability_is_a_chief_capability_and_declares_its_reuse`, `test_capability_module_creates_no_second_identity_or_persistence`, `test_capability_maps_onto_the_canonical_chief_envelope` |
| separate gates | `test_every_review_action_has_its_own_gate`, `test_shadow_stage_permits_read_and_findings_only`, `test_activated_stage_still_refuses_merge_and_unflagged_actions`, `test_unknown_action_is_refused_rather_than_defaulted`, `test_negative_control_the_gate_can_pass` |
| rollout derivation | `test_rollout_state_without_a_worker_is_implemented_not_shadow`, `test_activated_requires_an_explicit_activation_reference`, `test_unrecognised_stage_is_a_conflict_not_a_default_allow` |
| least privilege | `test_worker_never_borrows_a_pat_or_ambient_credential`, `test_worker_refuses_a_repository_outside_the_allowlist`, `test_worker_refuses_an_installation_mismatch`, `test_permission_matrix_is_least_privilege` |
| webhook security | `test_forged_signature_is_refused`, `test_unsigned_delivery_is_refused_when_no_secret_is_configured`, `test_signed_delivery_for_a_non_allowlisted_repository_is_refused`, `test_signed_delivery_with_a_foreign_installation_is_refused`, `test_delivery_without_an_id_cannot_be_deduplicated`, `test_non_app_delivery_target_is_refused`, `test_unrelated_events_are_ignored_not_reviewed` |
| idempotency / replay / retries | `test_job_claim_is_idempotent_per_key`, `test_delivery_ledger_distinguishes_new_duplicate_and_replay`, `test_retry_policy_is_bounded_and_backed_off`, `test_rate_limit_is_bounded_then_dead_lettered` |
| findings trace to real lines | `test_added_lines_use_post_change_line_numbers`, `test_added_lines_negative_control_without_a_hunk_header`, `test_failing_check_blocks_with_the_real_check_output`, `test_credential_shaped_addition_blocks_at_the_real_line` |
| fail-closed evidence | `test_unobserved_checks_fail_closed`, `test_unobserved_diff_fails_closed`, `test_absent_path_policy_is_recorded_not_assumed_admissible`, `test_path_outside_the_canonical_policy_blocks` |
| current-head / stale | `test_head_change_invalidates_findings`, `test_assert_head_current_refuses_a_moved_head`, `test_approval_scope_changes_when_the_head_changes`, `test_publish_refuses_when_the_head_moved_after_the_grant` |
| grants | `test_revoked_and_consumed_grants_do_not_match`, `test_an_expired_grant_does_not_match`, `test_revoked_grant_does_not_publish`, `test_activated_grant_then_publish_binds_the_exact_tuple` |
| independence | `test_self_review_is_refused_for_writes_and_flagged_for_reads`, `test_publish_refuses_self_approval` |
| no merge / no silent approval | `test_no_route_path_exposes_a_merge_or_deploy_surface`, `test_publish_events_never_include_merge_or_dismiss`, `test_capability_reports_merge_disabled_with_a_reason`, `test_a_green_review_does_not_activate_a_write_action`, `test_request_route_refuses_a_merge_action` |
| evidence contract | `test_evidence_binds_principal_binding_worker_policy_and_actions`, `test_evidence_is_unresolved_when_the_review_is_stale`, `test_evidence_state_names_the_disposition_rather_than_inflating_it`, `test_evidence_is_persisted_through_the_canonical_lab_store` |

Measured (this sandbox, `python -m pytest tests/test_chief_pr_review_capability.py -q`):
`70 passed`; `--collect-only` reports 70 nodes, so the pass count is the file's own
node count rather than an inferred delta.

### Existing guards extended (not bypassed)

* `tests/test_engineering_lab_api.py` — the Lab mutation-boundary inventory
  gained the five new POST paths, and the auth-wrapper test now asserts the
  webhook exemption set is exactly one path and that it bypasses account auth
  while every other Lab route still passes through `require_auth`.
* `tests/test_openapi_security_production_contract.py` — the operation inventory
  pin moved `344 -> 352`, and each new operation is named with its adjudicated
  boundary. The webhook is asserted to be `github_webhook_hmac`, **not**
  `firebase_bearer`: a bearer classification there would disclose a guard the
  route does not have.

## 6. Regression measurement (node identity, not counts)

Same environment, same dependency set, same clone:

| Tree | Result | Failing/error node set |
|---|---|---|
| `main` `2fb20d43` (worktree) | 20 failed, 4255 passed, 22 skipped, 1 error | 21 nodes, sha256 `4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916` |
| branch (pre-openapi-repair run) | 21 failed, 4320 passed, 22 skipped, 1 error | 22 nodes — the **only** extra node was `test_openapi_security_production_contract.py::test_all_composed_operations_have_adjudicated_security_boundaries` (the inventory pin), repaired in §5 |
| branch (post-repair run) | 20 failed, 4324 passed, 22 skipped, 1 error | **identical** 21 nodes, same sha256 |
| branch (final, all edits) | 20 failed, 4325 passed, 22 skipped, 1 error | **identical** 21 nodes, sha256 `4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916` |

`comm -3` on the final pair of node sets is empty. The `+70 passed` is
attributable by node identity: `--collect-only` counts 70 nodes in the new file
and the failing set is unchanged.

The one `ERROR` (`tests/test_autonomy.py`) is the pre-existing, sovereign-reserved
CE-01 `weaver.autonomy` module-vs-package collision — present on `main` in this
same environment and untouched here.

Environment-only failures on `main` that are **not** attributable to this
change: 10 of the 21 nodes require `web/arkadia_console/node_modules/typescript`
(not installed here). They fail identically on both trees.

## 7. Blockers (external, exact)

| Blocker | Evidence | Consequence |
|---|---|---|
| No GitHub App is registered for this capability, and no App installation token exists in this environment | `GitHubAppWorker.from_env().status()` → `{"state": "UNCONFIGURED", ...}`; a request with no worker is dead-lettered with HTTP 503 | `SHADOW` and `ACTIVATED` are **BLOCKED**, not merely unset. Registering the App and installing it on the single allowlisted repository is a human, provider-side act |
| The webhook cannot be delivered until the App exists | the receiver returns 503 without a configured secret, by design | webhook ingress is `BLOCKED` on the same act |
| `POST /api/lab/engineering/pr-review/webhook` is reachable only from a host that can accept GitHub deliveries | ADR-016 makes `https://arkadia-qzu4.onrender.com` the sole canonical origin | pointing the App at any other host would be a boundary regression |

None of these are repository work. The code path that consumes them is complete
and fails closed without them.

## 8. Not claimed

* **Production parity / deployment**: `NOT CLAIMED`. Nothing here was deployed.
* **Live GitHub interaction**: `NOT TESTED`. No App credential exists, so no real
  PR was read and no real review was published. The reader is exercised through
  an injected `GitHubReader`, which is the same seam the production path uses.
* **Shadow operation**: `NOT CLAIMED`. `SHADOW` requires a configured worker.
* **Activation**: `NOT CLAIMED` and **not permitted by this change**. Turning on
  `PUBLISH_COMMENT` / `APPROVE` requires a human activation record plus the
  per-action flag, and is a separate authorization.
* **Merge**: `NOT IMPLEMENTED`. Structurally refused.

## 9. Next authorized action

Human: register the GitHub App with exactly the permissions in
`PERMISSION-MATRIX.md`, install it on `Arkadia-Oversoul-Prism/Arkadia`, set the
six `ARKADIA_PR_REVIEW_*` configuration variables, and point the webhook at
`https://arkadia-qzu4.onrender.com/api/lab/engineering/pr-review/webhook`.

Then a read-only `SHADOW` review of one real PR is the first observable
execution. Publishing a comment remains off until a separate activation record
and a per-action flag exist.

## 10. Operator surface

* `OPERATOR-RUNBOOK.md` — setup, daily operation, dead-letter triage, disable.
* `PERMISSION-MATRIX.md` — requested permissions, capability map, action gates.
* `THREAT-MODEL.md` — 18 threats with the control and the test that proves it,
  plus the residual risks that are stated rather than mitigated.
