# EVIDENCE — gate07 chain integration (scheduler → trajectory → router → attention)

Pass: `gate07/chain-integration-evidence-01`
Reconstructed: 2026-10-06 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769` (#317)

## Objective

Measure the **composed** effect of the open Gate-07 hourly-loop repair chain — PRs #319,
#320, #321, #322, #323 — on the live hourly scheduler failure. Each PR was verified
individually; none of them carries the composition result, and the contract requires
reviewing integration rather than individual PRs in isolation.

## Artifact-only boundary

This pass **changes no runtime code**. It adds this evidence file and its
`WORKSTREAM_STATE.md`. Every claim below is a measurement of the existing branch trees.
The four runtime PRs remain independent, human-mergable units; this artifact exists so the
merge order carries its own justification.

## Composition

`#321` is **stacked** on `#319` (`git merge-base --is-ancestor` → true; #321's parent chain
is `3d1829d → e611edd`). `#320`, `#322`, `#323` are based on `main` and apply cleanly onto
`#319`+`#321` with `git apply --3way` — **no textual conflict** in the composed tree:

| PR | files | applies on #319+#321 |
|---|---|---|
| #320 | `.gitignore`, `tests/test_repo_hygiene_gitignore.py` | clean |
| #322 | `.github/workflows/weaver-mvp2-validation.yml`, `weaver/engineering_router.py` | clean |
| #323 | `weaver/attention_bus.py` | clean |

## The decisive measurement

Hourly loop, dry-run, trajectory `docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`,
`EngineeringWorker(...).run()`:

| tree | `status` | `blockers` | attention `event_type` / severity |
|---|---|---|---|
| `main` `451e41a` | `FAILED` | `invalid trajectory structure` | `WEAVER_BLOCKED` / HIGH |
| #319 head `3d1829d` (conformance only) | `NO_LEGAL_MOVE` | `no legal pending move (all complete or dependencies unresolved)` | `WEAVER_STATE_CHANGED` / **INFO (silent)** |
| **composed** #319+#320+#321+#322+#323 | `NO_LEGAL_MOVE` | `unrecognized move status: G12-A ('merged_acceptance_pending'), G12-C ('merged_acceptance_pending') — cannot route; expected one of accepted, completed, in_progress, merged, pending, revision_required` | `WEAVER_BLOCKED` / **HIGH (surfaced)** |

**Interpretation.** #319 alone converts a loud crash (`FAILED`) into a clean stop whose
`blockers` string is *generic* and whose attention event is `INFO` — i.e. it makes the
hourly stop **silent**. The composed chain converts that same stop into a **typed,
HIGH-severity** `WEAVER_BLOCKED` that names the two unresolved frontier moves (G12-A,
G12-C). The three runtime PRs are therefore load-bearing *together*: #319 removes the
crash, #322 names the unrecognized status, #323 pushes it to the sovereign.

Merging #319 without #322/#323 would leave the loop **truthful but mute** on the G12
frontier. That is the integration fact no single PR states.

## Schema / trajectory coherence

The corrected trajectory's move statuses (`merged_acceptance_pending` ×2, `in_progress` ×1,
`pending` ×3) all fall inside the #321 `trajectory.schema.json` enum
(`pending, revision_required, in_progress, merged_acceptance_pending, completed, accepted,
merged, blocked, failed, aborted`) — **empty** out-of-enum set. #321 is the schema half of
the same G12-A status divergence #319 corrects at the file level; they agree.

## Guard suite on the composed tree

`tests/test_scheduler_trajectory_conformance.py`,
`tests/test_trajectory_schema_conformance.py`,
`tests/test_engineering_router_status_truthfulness.py`,
`tests/test_attention_truthfulness.py` — **all pass** composed.

`tests/test_repo_hygiene_gitignore.py::test_no_module_resolves_the_repository_canonical_store`
fails in this sandbox on both `main` and the composed tree — **environment-blocked**:
`solspire/enterprise_router.py:21 ModuleNotFoundError: No module named 'fastapi'`. Not
attributable to the composed change. Recorded, not worked around.

## CI state at reconstruction (measured)

| PR | head | triggered checks |
|---|---|---|
| #319 | `3d1829d` | engineering-scheduler ✓, Full-history secret scan ✓, Vercel Preview Comments ✓ |
| #320 | `d5adcba` | Full-history secret scan ✓ |
| #321 | `e611edd` | engineering-scheduler ✓, Full-history secret scan ✓ |
| #322 | `9d0f1ce` | mvp2-validation ✓, provider-routing **✗** |
| #323 | `cd749ea` | mvp2-validation ✓, provider-routing **✗** |

`provider-routing` on #322 and #323 fails at the **pre-existing CE-01 collection error**
(`ERROR tests/test_autonomy.py` → `Interrupted: 1 error during collection`), measured in
run `37395288765` / job `112049692748` on #323's head. The same error is present on `main`;
it is baseline debt, not a regression of this chain.

## Classification

`IMPLEMENTED` — composition verified by measurement; the runtime PRs carry their own
per-PR proof. Merge remains human-only.

## Next bounded task (proposed, not executed)

1. **Merge the chain in order: #319 → #320 → #321 → #322 → #323.** #321 is stacked on
   #319, so #319 must merge first. No agent merges.
2. After merge, the hourly loop's `WEAVER_BLOCKED` (HIGH) surfaces the G12-A / G12-C
   `merged_acceptance_pending` frontier to the sovereign — the correct stop, since
   production acceptance is a human decision. Resolving that frontier is a **separate**
   bounded workstream.
