# ARKADIA-CHIEF-PR-REVIEW-001 — threat model

Scope: a Chief capability that reads a pull request, produces findings, and —
only behind separate gates — may write a review to GitHub.

Assets: repository integrity, branch protection / CODEOWNERS / required
reviews, the Chief identity, the Lab's evidence chain, and the human authority
boundary.

| # | Threat | Vector | Control | Test |
|---|---|---|---|---|
| T1 | Forged delivery | Attacker posts a body to the webhook URL | HMAC-SHA256 over the raw body, constant-time compare; no secret configured means the endpoint refuses (503) rather than accepting unsigned | `test_forged_signature_is_refused`, `test_unsigned_delivery_is_refused_when_no_secret_is_configured` |
| T2 | Replayed delivery | Attacker replays a captured signed body | Durable delivery ledger: a first presentation is `new`, a repeat inside the window is `duplicate`, a repeat outside it is `replay` and is refused | `test_delivery_ledger_distinguishes_new_duplicate_and_replay` |
| T3 | Signed delivery for a foreign repository | A valid signature from an installation that does not cover the target | Server-side installation + repository allowlist verified after the signature | `test_signed_delivery_for_a_non_allowlisted_repository_is_refused` |
| T4 | Signed delivery from a foreign installation | Same, via installation id | Installation id must equal the configured one | `test_signed_delivery_with_a_foreign_installation_is_refused` |
| T5 | Credential substitution | Operator has a PAT in the environment; the worker "just uses it" | `credential()` refuses and names the sources it declined to borrow | `test_worker_never_borrows_a_pat_or_ambient_credential` |
| T6 | Stale approval reused after a head change | Approve at head A, push head B, publish the A approval | The head is encoded in the grant scope; publish re-fetches the head and re-checks the grant | `test_head_change_invalidates_findings`, `test_publish_refuses_when_the_head_moved_after_the_grant`, `test_approval_scope_changes_when_the_head_changes` |
| T7 | Self-approval | Author approves their own change | `assert_independent` refuses at grant and publish; the review flags `SELF_REVIEW` as AMBER | `test_publish_refuses_self_approval`, `test_self_review_is_refused_for_writes_and_flagged_for_reads` |
| T8 | GREEN read as merge authorization | "The review is green, so merge" | `MERGE` is structurally refused; GREEN is a review status, and the published payload states the non-collapse | `test_publish_cannot_be_asked_to_merge`, `test_a_green_review_does_not_activate_a_write_action` |
| T9 | Stage inferred rather than declared | Someone sets `ARKADIA_PR_REVIEW_STAGE=ACTIVATED` and writes become live | Activation also needs an activation reference *and* the per-action policy flag; an unrecognised stage is a recorded conflict | `test_activated_requires_an_explicit_activation_reference`, `test_unrecognised_stage_is_a_conflict_not_a_default_allow` |
| T10 | Duplicate work / review storms | Provider redelivers, or an operator retries | Unique idempotency key `installation|repository|pr|head|event|action` in the canonical Lab store | `test_job_claim_is_idempotent_per_key`, `test_webhook_route_enqueues_and_deduplicates` |
| T11 | Provider rate limit | GitHub returns 429/403 | Bounded retries with declared backoff, `RETRY_WAIT` then `DEAD_LETTER`, both visible in the job list | `test_rate_limit_is_bounded_then_dead_lettered`, `test_retry_policy_is_bounded_and_backed_off` |
| T12 | Fabricated test claims | A finding cites a check that never ran | Findings are built from observed check runs only; an unread check set is `CHECKS_UNOBSERVED` (AMBER), and a required check with no run is `REQUIRED_CHECK_MISSING` (RED) | `test_unobserved_checks_fail_closed`, `test_required_check_that_never_ran_blocks`, `test_failing_check_blocks_with_the_real_check_output` |
| T13 | Path-policy bypass | A PR touches a surface the repository forbids | The canonical CP10 policy module is injected and its verdict becomes a blocking finding | `test_path_outside_the_canonical_policy_blocks` |
| T14 | Credential committed in a diff | A token lands in an added line | Added lines are mapped to real post-change line numbers and matched against credential shapes; a hit is blocking and cites the line | `test_credential_shaped_addition_blocks_at_the_real_line` |
| T15 | Revoked authority still usable | Grant revoked mid-flight | Publish re-reads the grant and refuses a revoked or consumed one; the store's consume is atomic | `test_revoked_grant_does_not_publish`, `test_revoked_and_consumed_grants_do_not_match` |
| T16 | Silent degradation | GitHub unreachable; the review reports GREEN with no data | An unreadable PR is AMBER (`PR_UNREADABLE`); an unobserved diff or check set is AMBER; GREEN requires complete observation | `test_request_route_fails_closed_without_a_worker`, `test_unobserved_diff_fails_closed` |
| T17 | Scope creep in the worker | Someone adds a merge or deploy call | `_post_review` targets only `POST /pulls/{n}/reviews`; a source guard asserts no merge/deploy/refs/statuses endpoint appears | `test_publish_events_never_include_merge_or_dismiss`, `test_no_route_path_exposes_a_merge_or_deploy_surface` |
| T18 | Second identity or second store | A parallel agent/memory/authorization system appears | Module-source guard: no `sqlite3`, no second principal id, no store class; the manifest declares its reuse | `test_capability_module_creates_no_second_identity_or_persistence` |

## Residual risks (stated, not mitigated)

* **The webhook receiver is unauthenticated at the account layer by design.** Its
  security rests on the HMAC secret and the binding checks. If the secret leaks,
  an attacker can enqueue jobs — but not cause a GitHub write, because the
  receiver performs no GitHub call and every write needs a human grant.
* **The installation token is read from the process environment.** Rotation is
  the operator's responsibility; the capability re-reads it on every call, so a
  rotated value is picked up without a restart.
* **Findings are heuristics where they are not check output.** Credential-shape
  matching can flag a fixture. That is why it blocks *review* (a human
  adjudicates) rather than blocking merge by itself.
* **Branch protection, CODEOWNERS and required reviews are GitHub's.** This
  capability reads them; it never bypasses them, and it cannot: the token has no
  administration scope and merge is structurally refused.
