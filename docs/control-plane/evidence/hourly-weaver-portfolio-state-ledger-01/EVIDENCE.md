# Hourly Weaver portfolio ledger — the fairness rule now has an artefact

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `cb2841956bcc0397007b9efffbaa8cc6d0801836` (2026-11-26T00:16:37Z)
**Measured:** 2026-11-26, 02:05–02:40 UTC, this workspace
**Authority:** one derived ledger, one authored cursor, one guard, one workflow.
No merge, no push to `main`, no deployment, no acceptance.

---

## 1. The gap

`docs/control-plane/openhands/hourly-weaver/2026-11-21-weekly-closure-directive.md`
(merged as `cb284195`, PR #675) makes the Hourly Weaver a three-repository
portfolio worker and states two requirements that had no artefact:

> Maintain one durable portfolio cursor/ledger in this directive's
> repository-native evidence area, with one row per repository: current
> default/base SHA, active trajectory/phase, active issue/PR, last pulse,
> blockers, next legal task, and CI/device evidence.

> Use deterministic fairness: select the repository with the oldest verified
> `last_progress_at` among repositories that have a legal, unblocked task;
> break ties in this fixed order: Sonata → FSN → Arkadia.

Before this change, `git ls-files | grep -i portfolio` returned no ledger and no
selector. Every pulse started in a fresh sandbox, re-derived all three
repositories from scratch, and left nothing behind. Two consequences:

1. **Fairness was unimplementable.** "Oldest verified `last_progress_at`" is a
   comparison across pulses. With no durable record, the comparison had no
   input, so the worker could only fall back to whatever the session happened to
   look at — in practice Arkadia, which is also the loudest repository.
2. **Starvation was invisible.** `Arkadia-Oversoul-Prism/family-safety-network`
   has had **no repository activity since 2026-11-07T10:15:12Z** (19 days at the
   time of measurement). Nothing in the repository said so.

## 2. Measured portfolio state (the ledger's own content)

`python scripts/portfolio_state_refresh.py --write`, live, 2026-11-26T02:11:07Z:

| repository | default branch | head | open PRs | open issues | last verified progress |
|---|---|---|---|---|---|
| `Arkadia-Oversoul-Prism/sonata` | `feature/sonata-tts-app` | `49691de5b57d` | 1 | 1 | 2026-11-26T00:48:38Z |
| `Arkadia-Oversoul-Prism/family-safety-network` | `main` | `543f52dff3f6` | 1 | 0 | **2026-11-07T10:15:12Z** |
| `Arkadia-Oversoul-Prism/Arkadia` | `main` | `cb2841956bcc` | **62** | 9 | 2026-11-26T01:30:43Z |

Derived selection: **`family-safety-network`** — the oldest verified
`last_progress_at` among unblocked repositories. That is the directive's rule
working, and it is the opposite of what an attention-following worker would do:
Arkadia carries 62 open pull requests and FSN carries one.

## 3. The trap this workstream found and pinned

`Arkadia-Oversoul-Prism/sonata` has `default_branch == "feature/sonata-tts-app"`.
A portfolio tool that assumes `main` — the obvious implementation, and the one
this cycle wrote first — gets:

```
GET /repos/Arkadia-Oversoul-Prism/sonata/commits/main
  -> 422 {"message": "No commit found for SHA: main"}
```

The failure is quiet in exactly the wrong way: the row still exists, still has a
repository name, and still reports success, but carries no head SHA and no
progress timestamp. A repository that cannot be measured disappears from the
fairness comparison while the tool looks healthy. The refresh therefore reads
`default_branch` from the repository record, and
`test_refresh_reads_the_declared_default_branch_not_main` drives the real
`observe()` through a recorded transport to prove the commit request names
`feature/sonata-tts-app` and never `main`.

## 4. Design: derived and authored state are separate files

| file | kind | who writes it |
|---|---|---|
| `portfolio-state.json` | **derived** | only `scripts/portfolio_state_refresh.py` |
| `portfolio-cursor.json` | **authored** | a human or agent, under review |

A derived field a human may edit has no oracle; that is the drift class
`scripts/lane_state_refresh.py` already exists to prevent. Splitting the files
lets the offline guard check the derived file against its own arithmetic —
`last_progress_at` must equal the maximum of `head_committed_at` and
`latest_open_pull.updated_at` — without needing the network. A hand edit to the
fairness input is therefore a CI finding, not a silent change of which
repository the worker visits.

`last_progress_at` is derived from **repository activity only**, never from
"a pulse ran". A pulse that produced nothing did not progress; letting a no-op
pulse reset the clock is precisely how a stalled repository is starved forever.
`test_a_noop_pulse_does_not_reset_fairness` pins that semantics.

## 5. Verification

```
python -m pytest tests/test_portfolio_state_ledger.py -q      -> 17 passed
python scripts/portfolio_state.py --check                     -> PASS (exit 0)
```

Negative controls, each run against the real files and then restored
byte-identically:

| control | mutation | observed |
|---|---|---|
| hardcoded branch | `branch = meta["default_branch"]` → `branch = "main"` | `1 failed, 15 passed` — the default-branch node |
| no blocked check | removed the `if entry.get("blocked")` branch from `select_next` | `1 failed, 15 passed` — the blocked-slot node |
| dropped repository | deleted the `sonata` row from the committed ledger | `--check` → `FINDING state is missing the canonical repository …/sonata`, exit 1 |
| verified row with no head | nulled `sonata.head_sha` while leaving `observation: VERIFIED` | `--check` → `FINDING …/sonata: observation is VERIFIED but head_sha is empty`, exit 1 |

Wiring and boundary suites, run because a new workflow is scanned by several
generic guards:

```
python -m pytest tests/test_ci_gate_trigger_coverage.py \
  tests/test_workflow_injection_boundary.py tests/test_ci_verdict_step_integrity.py \
  tests/test_m02a_ci_gate_integrity.py tests/test_ci_suite_collection_continuation.py \
  tests/architecture -q
  -> 372 passed
```

`printf '<each new path>' | python scripts/cp10_mutation_boundary_policy.py --judge`
→ `PASS` for all added paths.

### 5.1 Full-suite baseline — no node attributable to this change

`main` @ `cb284195`, this workspace, `requirements.txt` installed:

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
  --continue-on-collection-errors
branch: 22 failed, 4275 passed, 22 skipped, 1 error in 282.59s
```

The failing/error set is **23 nodes**. The `main`-side comparison is a targeted
re-run of the same twelve files (the contract allows one full-suite pass per
pulse, so `main` was measured on the files that fail, not in full):

```
main (targeted):  22 nodes
branch (full):    23 nodes
diff: + tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

That single delta is **not attributable to this change**: it **passes in
isolation on the branch** (`2 passed`), no file this change touches is under
`knowledge/` or `vault/`, and it is the order-dependent shared-runtime class
already recorded for this repository and owned by PR #698.

The other 22 nodes are unchanged from `main` and none is in
`tests/test_portfolio_state_ledger.py`:

| failing file | nodes | owner |
|---|---|---|
| `test_mission_lifecycle_adapter_contract.py` | 10 | environment — `web/arkadia_console/node_modules/typescript` absent |
| `test_autonomy.py` (ERROR) | 1 | CE-01 `weaver.autonomy` module-vs-package collision, sovereign-reserved |
| `test_ais_w2_living_gate_grove_handoff.py` | 1 | F-01, awaiting a sovereign decision |
| `test_identity_spine_w1.py`, `test_m02_reasomate_truth.py` | 2 | #700 |
| `test_m01_persistence.py`, `test_m05_files.py` | 2 | #690 |
| `test_prism_w4_lab_pr_state.py` | 2 | #683 |
| `test_solspire_r1_governance_convergence.py` | 2 | #693 |
| `test_solspire_r3_execution_runtime.py` | 1 | #691 |
| `test_gov04_bounded_merge_delegation.py` | 1 | #725 |

## 6. What this does not establish

### 6.1 Hosted automation linkage — inspected, and partially VERIFIED

The directive makes linkage verification a required bootstrap gate and says not to
assume the repository file is wired into the hosted automation. It was inspected
read-only (`GET /api/automation/v1` and `/{id}`), and the result is mixed:

| property | observed | state |
|---|---|---|
| automation exists | `6bc8f514-537d-4ddb-bb3a-758a0a96cad7`, "OpenHands Hourly Weaver — Multi-Repository Bootstrap" | VERIFIED |
| cadence / ceiling | cron `5 * * * *` UTC, `timeout: 1800`, `enabled: true` | VERIFIED |
| prompt | the `ARK-OPS-CONTINUOUS-001` contract text, verbatim | VERIFIED |
| prompt names the portfolio | **no** — no `sonata`, no `family-safety-network`, no `portfolio`, no reference to the 2026-11-21 directive | **NOT LINKED** |

So the *contract* is wired and the *portfolio* is not. The automation is
Arkadia-only by prompt: `REPOSITORY := https://github.com/Arkadia-Oversoul-Prism/Arkadia`.
The three-repository routing and the fairness rule the directive mandates cannot
take effect until the prompt names them — which is a concrete explanation for
why `family-safety-network` has had no activity for 19 days.

**Not modified.** Changing a hosted automation's prompt is a runtime
configuration change; `DEPLOY_AUTHORITY := NONE` and GOV-04 reserve
deployment/provider/configuration decisions to a human. The exact change for the
owner is: append the directive's "Multi-repository portfolio routing" section to
the automation prompt (or a pointer to
`docs/control-plane/openhands/hourly-weaver/2026-11-21-weekly-closure-directive.md`),
and read the next repository from
`python scripts/portfolio_state.py --select` instead of the single `REPOSITORY`
line. Until then this ledger records the correct next repository and nothing acts
on it.

### 6.2 Other limits

- **The live oracle is not wired into CI.** `scripts/portfolio_state_refresh.py`
  needs a token that can read all three repositories; a repository-scoped
  `GITHUB_TOKEN` cannot, so a CI step would be permanently red and would prove
  nothing. Refreshing the ledger stays an operator command, and the ledger
  records its own `derived_at` so staleness is visible in review. This is
  recorded rather than papered over.
- **The cursor's phase labels are judgements**, taken from the directive's own
  phase lists. They are authored, reviewed, and deliberately not derived.
- **No merge, deployment or acceptance.** Selecting a repository is not
  authorising work in it, and this record is not an M1–M13 eligibility
  assessment.

## 7. Next action

1. **Human:** review and merge this PR if eligible. It is a draft; marking it
   ready is the owner's action.
2. **Weaver:** the derived selection is `family-safety-network`, phase F0
   ("integrate and recover CI"). Continuing its existing PR #8 is the next legal
   task under the directive — it is *not* performed in this cycle, which is
   bounded to the ledger.
3. **Human:** decide whether the refresh should gain a cross-repository token so
   the live oracle can be gated. That is a credential decision, so it is not
   taken here.

## 8. Reproduce

```
git rev-parse origin/main
PYTHONPATH=scripts python scripts/portfolio_state_refresh.py      # dry run
python scripts/portfolio_state.py --check                          # offline guard
python -m pytest tests/test_portfolio_state_ledger.py -q
curl -s https://api.github.com/repos/Arkadia-Oversoul-Prism/sonata | jq .default_branch
```

## 9. Post-review repair — cycle 25 (fairness clock pin)

The `portfolio-state` check on this PR's head `45c18566` was **`failure`**: the guard this
PR adds could not pass on its own branch.

```
FAILED tests/test_portfolio_state_ledger.py::test_blocked_repository_does_not_consume_the_slot
AssertionError: assert 'Arkadia-Oversoul-Prism/Arkadia' == 'Arkadia-Oversoul-Prism/sonata'
```

The module was correct; the assertion was not. It pinned `SONATA` as the next-oldest
repository, which held only until the `chore(weaver): refresh …` commit replaced the
recorded timestamps with freshly measured ones and left Arkadia **8 seconds** older than
Sonata. A fairness rule cannot be guarded by an expectation read off live, refreshed data.

Repaired by pinning the clock inside that one node, so it decides the rotation rule while
`test_committed_artefacts_support_their_own_selection` keeps deciding live-data
consistency. `scripts/portfolio_state.py` is unchanged.

Measured: `1 failed, 16 passed` → **`17 passed`**; adjacent suites
(`test_ci_gate_trigger_coverage.py`, `test_workflow_injection_boundary.py`,
`tests/architecture`) **`164 passed`**; live negative control on the real module
(`if entry.get("blocked"):` → `if False:`) reddens exactly the repaired node and restores
byte-identically.

Full record: `docs/control-plane/evidence/ark-ops-continuous-001-cycle-25-portfolio-fairness-clock-pin-01/EVIDENCE.md`.
