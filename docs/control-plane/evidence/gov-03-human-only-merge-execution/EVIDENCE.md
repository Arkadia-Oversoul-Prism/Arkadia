# GOV-03 — Human-only merge execution

**Status:** Proposed governance reconciliation; not effective until human-reviewed and human-merged.
**Authorization:** Explicit human authorization in the ChatGPT conversation dated 2026-11-16.
**Base branch:** `main` at branch creation; revalidate exact base/head before review.
**Scope:** governance documents, worker contract schema/instance, and regression tests only.
**Non-goal:** no merge, deployment, auto-merge activation, branch-protection mutation, or product acceptance.

## Decision

All merge execution is human-only. Weaver retains the ability to assess candidate PR eligibility against the existing M1–M13 rubric and prepare exact-head evidence. That assessment is advisory; it is not permission, approval, or execution.

## Reconciliation

- Supersedes GOV-01/GOV-02 language to the extent it implies conditional delegated merge execution.
- Preserves M1–M13 as Weaver's assessment rubric.
- Aligns `AGENTS.md`, `SHARED-CONTRACTS.md` §9, the overnight directive, and the worker contract.
- Preserves `ForbiddenMergeAdapter` as the runtime refusal boundary.
- Encodes separate fields: `merge=human_only`, `merge_assessment=weaver_eligibility_only`, `merge_execution=human_only`.
- Defines non-collapsing report states: `ELIGIBLE_TO_MERGE`, `HUMAN_AUTHORITY_REQUIRED`, and `MERGED` (only after GitHub confirms a human merge).

## Verification plan

The updated `tests/test_weaver_merge_authority_contract.py` asserts:
1. governance sources agree on human-only execution;
2. Weaver retains assessment but not execution;
3. worker contract schema and instance encode separate assessment/execution fields;
4. runtime merge/deploy adapters continue to refuse;
5. reserved human decisions and lane ownership remain intact;
6. this governance PR cannot self-authorize its merge.

The worker contract regression suite `tests/test_m09_worker_contract.py` must also pass after schema/instance changes.

**Execution status:** NOT RUN in this remote preparation pass. The repository connector can create and inspect GitHub artifacts but does not execute the project's local pytest environment. No test pass is claimed. CI and/or a local checkout must run both focused test files before human review.

## Safety and non-claims

No PR was merged. No branch protection or provider setting was changed. No merge-capable runtime was added. No deployment or acceptance is claimed. The proposal takes effect only after a human reviews and merges this dedicated PR.
