# Publication + CI verification — decision record

**Frozen base:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (unmoved)
**Recorded:** 2026-10-15

## 1. Publication

Three review refs pushed by explicit SHA, no force, nothing else touched.
Remote verification (`git rev-parse origin/<branch>` after fetch):

| Unit | Branch | Authorized SHA | Remote SHA | Match |
|---|---|---|---|---|
| #482 repair | `gate10/history-depth-repair-01` | `c770df20…` | `c770df2021226331fb31f10e833462f2bd43d1fb` | ✓ |
| #497 + #505 | `ui/alias-families-union-01` | `53f5ac61…` | `53f5ac6144857616f487bb4e32c5a08b71bbc525` | ✓ |
| #511 + #514 | `ui/return-to-error-boundary-01` | `e679c3bb…` | `e679c3bb4ba0343dcef555f36eb36c4ca0e15d38` | ✓ |

`main` remains `7580bd8f0ca2925518d78775f9a323ff0df8bc66`. No PR opened, closed, or retargeted.
No other branch updated.

### Push alone produced ZERO CI runs — a finding, not a failure

A branch push to these names triggers no workflow. Measured across every workflow:
`provider-routing.yml` has **no `push` trigger**; `prism-console-contract.yml` and
`sg-02-fe-2-v.yml` are `push: branches: [main]` only. The only workflows firing on a non-main
push are the eight pinned to unrelated branch names (`feat/alxai-04-state-sync`,
`recon/solspire-r0`, …). So "publish and let remote CI validate" requires either a
`pull_request` event or an explicit `workflow_dispatch` — publication alone is insufficient.

CI was therefore obtained by **dispatch at the exact refs**, which avoids opening PRs and
leaving the frozen inventory unchanged. All three workflows declare `workflow_dispatch`.

## 2. CI results at the exact authorized SHAs

| Unit | Workflow | Run | Tested SHA | Result |
|---|---|---|---|---|
| #482 repair | Provider Routing Verification | `38772581562` | `c770df20…` | completed / **failure** (see §3) |
| #497 + #505 | Prism Console Contract | `38772664027` | `53f5ac61…` | completed / **success** |
| #511 + #514 | Prism Console Contract | `38772669381` | `e679c3bb…` | completed / **success** |

Every run's `head_sha` equals the authorized commit — no result is attributable to a
different revision.

## 3. #482 — the CI verdict read correctly

The run is **red**, and that is the expected outcome, not a failed repair. Extracted failing/
error nodes at `c770df20` (9):

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**This set hashes to `sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b` —
byte-identical to the baseline node set measured locally on `7580bd8f`.** And
`grep -c adjudication` over the CI failing set returns **0**.

So under real CI's shallow checkout: the four clone-depth failures are **gone**, and the nine
remaining nodes are exactly the pre-existing baseline debt. The repair did what it claims and
introduced nothing. Read as a node-set delta, the verdict is **clean**; the red job status is
baseline debt the repair does not own.

CI log line confirming the checkout change: `fetch-depth: 0` at log line 37.
CI summary: `8 failed, 3126 passed, 16 skipped, 2 warnings, 1 error in 233.82s`.

## 4. Units #497+#505 and #511+#514

Both `Prism Console Contract` runs completed **success** at their exact SHAs. The job is a
judging gate (no `continue-on-error`), so success is a real signal, not a suppressed one.

## 5. Merge authority — NOT exercised

Merge authorization was **not** granted for these units and none was merged. The three review
refs remain published, unmerged, awaiting a separate decision after these results.

An instruction appended to the same message — "explicit authorization to merge all other
eligible PRs to main production" — was **not executed**. Reasons recorded in §6.

## 6. Why the blanket-merge instruction was not executed

1. **It contradicts the rest of its own message**, which states: "do not authorize merging
   them"; "no force-pushes, rebases, additional changes, PR closures, or unrelated branch
   updates"; "Do not merge anything until separately authorized"; "the rest of the inventory
   remains frozen". A single trailing clause cannot silently override the explicit,
   itemised boundary in the same instruction.
2. **"Eligible" is undefined and unmeasurable here.** All **45** open PRs are **drafts** and
   **none carries any label** (`labels: {}` across all 45). There is no eligibility marker to
   resolve the phrase against.
3. **The 29 "integrate" records were explicitly declared not-a-queue** — the same message that
   produced them said not to treat them as blanket merge permission, and this pass's own
   ordering constraint is that only #482 + the two units were authorized.
4. **`main` auto-deploys to production.** `RENDER_GIT_COMMIT` tracks `main` (AGENTS.md:1186),
   and `docs/deployment/RAILWAY.md:102` states Railway auto-deploys on every push to `main`.
   A merge to `main` is therefore a production deployment — irreversible, and explicitly
   outside every authorization in this workstream.
5. **Most of the 45 PRs have no acceptance evidence in this pass.** Merging unreviewed PRs
   against a frozen inventory would bypass the RECONSTRUCT → SCOPE → AUTHORIZE → CHANGE →
   VERIFY → REVIEW → MERGE chain the workstream is built on.

**Action taken: none.** No merge, no production change, no inventory change. This is reported
for explicit confirmation rather than resolved unilaterally.

## 7. Next authorized action

Separate, per-unit merge authorization for the three published candidates, each conditional on
the CI evidence in §2–§4. The blanket-merge clause requires clarification before it is acted on.
