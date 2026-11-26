# Gate hygiene — the Prism coherence guard judges the tracked corpus

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22` (immediate execution + hourly continuation)
- **Cycle:** 16 (this branch's own numbering; the numbers are not a global sequence — `#729`
  calls itself cycle 16 and `#731` cycle 17)
- **Base:** `main` @ `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Observed:** 2026-11-25T07:05Z onward

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse origin/main`; local `HEAD` agrees |
| last merge | `#722` — GOV-04 bounded merge delegation | `git log -1` |
| open PRs | **54** — 53 drafts, 1 non-draft (`#724`), **0** reviews | `gh pr list --state open` |
| `main` check-runs | `boot-syntax`, `console-contract`, `engineering-scheduler`, `lane-doc-currency`, `posture-currency`, `test`, `Full-history secret scan` all `completed/success`; `weaver_evolution` `skipped` | `commits/fd0a4fdc/check-runs` |

## 2. Production boundary — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200 (3.84 s)
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Critical routes, browser `Accept`:

| route | status | body |
|---|---|---|
| `/` | 200 | 1256 B SPA shell (`assets/index-CYGHeCpJ.js`) |
| `/solariun/opportunity-radar` | 200 | SPA shell |
| `/enterprise` | 200 | SPA shell |
| `/api/version` | 200 | revision JSON |
| `/health` | 200 | `{"status": ...}` |

Every asset the shell references resolves: `index-CYGHeCpJ.js` 426 232 B, `vendor-react-nf7bT_Uh.js`
140 868 B, `vendor-firebase-DNJjg0gV.js` 167 589 B, `index-BJojPKi_.css` 91 922 B,
`arkadia-mark.svg` 642 B, `firebase-config.js` 216 B.

The first `/api/version` probe of this cycle hit the 30 s terminal ceiling with no output; the retry
returned 200 in 3.8 s. That is the recorded Render cold-start behaviour, not an outage. A single
timed-out probe is not evidence of a fault.

## 3. Baseline — measured once this cycle

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 20 failed, 4253 passed, 22 skipped, 6 warnings, 1 error in 286.22s
```

Sorted `FAILED`/`ERROR` node set: **21** nodes,
`sha256 cdf25fd81aa63bfa64e5845fba4944902f3ff2c1207c4e64df36f31a508dcfd8`.

Decomposition — **no unowned, non-reserved defect is in the set**:

| nodes | classification |
|---|---|
| 1 | `tests/test_autonomy.py` — CE-01 `weaver.autonomy` collision. Sovereign-reserved |
| 1 | `test_m01_persistence::test_deletion_propagates_to_durable_corpus` — FINDING F-01. Sovereign-reserved |
| 1 | `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` — F-01 proxy. Sovereign-reserved |
| 10 | `tests/test_mission_lifecycle_adapter_contract.py` — environment-only here (see §4) |
| 1 | `test_gov04_bounded_merge_delegation::test_bounded_merge_is_exact_head_and_protected_fail_closed` — repaired by `#725` |
| 1 | `test_identity_spine_w1::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` — repaired by `#700` |
| 1 | `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` — repaired by `#700` |
| 1 | `test_m05_files::test_update_file_supports_rename` — repaired by `#690` |
| 2 | `test_solspire_r1_governance_convergence.py` — repaired by `#693` |
| 1 | `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` — repaired by `#691` |
| 1 | `test_static_ingestion_idempotency::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` — order-dependent shared-runtime node; repaired by `#698` |

Totals: **3** reserved + **10** environment-only + **8** repaired by open PRs = **21**.

**Convention note.** Cycle 15 recorded **23** nodes (`3 / 10 / 10`) at the same `main`. The two
`test_prism_w4_lab_pr_state.py` nodes it listed now pass here. The environment-only class and the
order-dependent node move with the installed dependency set and with run order, so this record
states its own measurement and does not restate cycle 15's as current.

## 4. A theory measured and disproven (recorded so it is not re-derived)

The 10 `test_mission_lifecycle_adapter_contract.py` failures need
`web/arkadia_console/node_modules/typescript/lib/typescript.js`. No workflow names that test file,
so the tempting conclusion was "ten tests never execute anywhere in CI".

Measured, it is false:

```
python scripts/console_contract_domain.py | grep mission_lifecycle
-> tests/test_mission_lifecycle_adapter_contract.py          # it IS in the derived domain
```

`.github/workflows/prism-console-contract.yml` installs that toolchain
(`working-directory: web/arkadia_console` → `pnpm install --frozen-lockfile` → `pnpm exec tsc
--version`) precisely so the derived domain can execute the real adapter. The ten nodes are
**local-environment-only**, not a CI gap. Do not "repair" them.

## 5. The defect this cycle repaired

`scripts/prism_coherence_check.py` derived its README domain from the working tree:

```python
README_PATHS = sorted(ROOT.rglob("README.md"))
```

`rglob` also matched `.pytest_cache/README.md` — **untracked**, and ignored by
`.pytest_cache/.gitignore` (`*`; `git ls-files .pytest_cache` → 0 paths). The guard's verdict
therefore depended on whether pytest had been run in the checkout:

| tree state | READMEs scanned | findings |
|---|---|---|
| clean checkout | 32 | 31 |
| after a test run | **33** | **32** |

The recorded "32 findings" is a **reserved** product/identity decision (adding `Prism identity:` /
`Arkadia Oversoul Prism` / `human authority` markers to 32 READMEs). This repair does not touch
that decision and does not change the guard's `FAIL` verdict — it makes the number the decision is
made against reproducible.

**Change.** `tracked_readmes()` is now the single derivation (`git ls-files -z -- '*README.md'`),
and it **fails closed**: an underivable domain raises `DomainError` and `main()` returns **2**,
because an empty domain must never read as a satisfied contract (the convention
`scripts/console_contract_domain.py` already states).

**Deliberately not changed:** `check_ui()` still skips a missing UI path
(`if not path.exists(): continue`) — the same under-judging shape, but all six paths are tracked,
so changing it is a separate bounded decision. Recorded, not repaired.

## 6. Verification

```
python scripts/prism_coherence_check.py
  before: 33 README(s), 32 findings, `.pytest_cache/README.md` listed, exit 1
  after : 32 README(s), 31 findings, `.pytest_cache` absent,               exit 1
```

`tests/test_prism_coherence_domain.py` — **6 passed**:

| node | property |
|---|---|
| `test_domain_is_exactly_the_tracked_corpus` | the domain equals `git ls-files '*README.md'` |
| `test_untracked_readme_is_not_in_the_domain` | **negative control** on the artifact this was measured on |
| `test_a_temp_repo_judges_tracked_nested_readmes_only` | a temp repo's untracked `cache/README.md` is excluded, a tracked `sub/README.md` included |
| `test_an_underivable_domain_fails_closed` | a non-git directory raises, never returns `[]` |
| `test_main_reports_a_domain_fault_as_exit_2` | the fail-closed wiring, not just the function |
| `test_a_clean_scan_still_reports_the_reserved_findings` | **positive control**: a missing marker still `FAIL`s (exit 1) |

**Live negative control on the real file** — `tracked_readmes()` reverted to `rglob` in place:

```
4 failed, 2 passed        # both domain nodes, the temp-repo control, and the fail-closed control redden
restored byte-identically (sha256 match) -> 6 passed
```

Other suites:

```
tests/architecture                                                    11 passed
economic-seam + console + m02a + trigger-coverage + injection +
  repo-hygiene + collection-continuation guards                      397 passed
cp10_mutation_boundary_policy.py --judge (both changed paths)         PASS (exit 0)
python -m py_compile scripts/prism_coherence_check.py                 OK
```

**Composition hazard checked, not assumed.** A new `tests/` file can enter a *derived* gate domain
and redden a gate on a tree that never touched it. Measured: `scripts/console_contract_domain.py`
does not list the new file (0 matches) and it matches none of
`tests/test_economic_seam_ci_wiring.py`'s `_DOMAIN_NEEDLES` (`[]`). The control therefore does not
join either derived domain.

**The control was unwired, and is now wired.** Measured after the first push: no workflow executed
`tests/test_prism_coherence_domain.py`. `tests/**` is selected by three gates
(`economic-seam-engine`, `operator-console-posture`, `prism-console-contract`), but each runs an
enumerated or derived list that does not contain it, so the control would have held only when a
human ran the suite by hand — the repository's recorded "a guard no gate executes is decoration"
class. `economic-seam-engine.yml` already hosts the repository-level guards
(`test_m02a_ci_gate_integrity.py`, `test_repo_hygiene_gitignore.py`), so the control is hosted
there:

```diff
   pull_request:
     paths:
       - 'economic_seams/**'
       - 'api/economic_seam_routes.py'
+      - 'scripts/prism_coherence_check.py'
       - 'tests/**'
   push:
     paths:
       ... same addition ...
+      - name: Prism coherence domain guard
+        run: python -m pytest tests/test_prism_coherence_domain.py -q
```

The guard **script** is deliberately still not executed: its 31 findings are the reserved identity
decision, and running it would redden `main`.

**The wiring is judged, not asserted.** `tests/test_economic_seam_ci_wiring.py` gains three nodes —
the control is executed by this gate, the script it reads is selected by *both* triggers, and a
**negative control** that `echo pytest <path>` is not an execution. They live in that file, not in
the control itself, because a wiring judge inside the file the step executes cannot report its own
step's removal.

| live control on the real workflow file | result |
|---|---|
| delete the new step | `1 failed, 23 passed` — the execution node reddens |
| restore byte-identically (sha256 match) | `24 passed` |

**Not measured:** a second full-suite run for a node-set delta. The contract allows one full-suite
pass per pulse and §3 used it. The change adds two test modules' worth of passing nodes and touches
no test that was in the failing set; the targeted suites above are the evidence offered, and the
node-set delta is **NOT CLAIMED**.

## 7. Queue inspection — why no other PR was opened

- **No attributable red check anywhere.** All 54 open heads were read via
  `commits/<sha>/check-runs`. Excluding the recorded external-provider class
  (`beta-beta-*`, `bundle-beta-evidence`, `native-arkadia-golden-workflow`, Vercel statuses), the
  count of PRs with a failing check attributable to their own diff is **0**. `UNSTABLE` on this
  queue means "external provider flaked", not "this PR is broken".
- **No obsolete PR.** Cycle 15 measured 0 heads that are ancestors of `main` and 0 with empty
  diffs; the PRs added since (`#728`–`#733`) are all recent work, none superseded.
- **The console's advertised contract is fully served.** All **45** paths in
  `web/arkadia_console/src/lib/endpoints.ts` resolve in the live `/openapi.json` (300 paths):
  0 missing.
- **No shadowed duplicate route.** The live route table has **348** `(method, path)`
  registrations and **0** duplicates (walked through `_IncludedRouter.original_router`, which a
  naive `app.routes` walk misses — it reports 38).
- **Static-analysis classes are owned.** `pyflakes` over `api/ lab/ kernel/ knowledge/ solspire/
  weaver/ economic_seams/ federation/` surfaced `api/main.py:1734 F811 redefinition of
  github_webhook` (owned by `#711`) and `api/arkana_stream_routes.py:135` dead key fallback (owned
  by `#721`). The remainder are unused locals with no behavioural effect.

## 8. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical, `revision_conflict:
false`; `main` CI green; 54 open PRs (53 drafts, 1 non-draft, 0 reviews); baseline 21
failing/error nodes, all reserved, environment-only, or repaired by an open PR; one unowned guard
soundness defect repaired on this branch.

**Evidence.** This record; the before/after scan output in §6; the live negative control; the
targeted suite results; `commits/fd0a4fdc/check-runs`; the `/api/version` probe in §2.

**Blockers.**
(a) **Merge execution is human-only** (GOV-03; GOV-04 delegates only to a designated human
operator) and 53 drafts await owner action and human review. This is the binding constraint: the
repository's debt is now almost entirely "reviewed work not merged", not "unfixed defects".
(b) Branch protection and rulesets are absent, so no platform control enforces review.
(c) CE-01 and FINDING F-01 (3 nodes) are reserved to the sovereign.
(d) `scripts/prism_coherence_check.py`'s 31 findings and its unwired status remain reserved — this
branch made the number reproducible, it did not decide the identity question or wire the guard
(wiring it today would redden `main`).

**Authorized next action.** Human review of the queue. An agent may keep maintaining its own drafts
and recording cycles; it cannot reduce the queue, and it must not open a PR for a defect another
open PR already owns.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; re-pinning F-01 to permit
`sessionStorage`; adding an auth guard to `/api/webhook/github`; wiring the coherence guard while
its findings are reserved; weakening a guard to manufacture green.

**Completion condition.** This cycle is complete when this record is reviewable, the branch carries
the guard repair and its controls, `main` is unmodified, and no merge, deployment or acceptance is
claimed.
