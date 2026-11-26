# ARK-PR-BACKLOG-RECONCILIATION-001 — open-PR backlog inventory, dispositions, and merge ledger

Observed **2026-11-26**, `main` = `68db6619ee438ade7d8c32786076aab877e308a5`
("feat(lab): governed Chief PR-review capability (ARKADIA-CHIEF-PR-REVIEW-001) (#749)").

**Nothing in this pass merged, closed, deployed, retagged, or changed branch
protection.** Every action was read-only inspection plus local composition in
throwaway worktrees. The dispositions below are *recommendations for the
sovereign*; the report is not an authorization for any of them.

---

## 1. Scope and method

| Step | How |
|---|---|
| Inventory | `GET /repos/…/pulls?state=open` → **65** open PRs, then per PR `GET /pulls/{n}`, `/pulls/{n}/files`, `/commits/{head}/check-runs`, `/commits/{head}/status` |
| Head resolution | every head fetched locally (`git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'`) so conflict and staleness are computed from real objects, not API guesses |
| Conflict | `git merge-tree --write-tree --name-only origin/main pr/<n>` per PR (64 clean, 1 conflicting) |
| Staleness | `git rev-list --count head..origin/main` (behind) and `origin/main..head` (ahead) |
| Overlap | changed-path intersection across all 65 PRs |
| Review | the merged `chief.pr_review` capability (§6) |
| Composition | batch A and the `api/main.py` quartet merged in detached worktrees, full suite executed on the composed trees |

Environment: Python 3.13, dependencies from `requirements.txt` plus `pyyaml`,
`PYTHONPATH=<repo>/archive/legacy_python`, suite run as
`pytest tests/ -q -rEf --continue-on-collection-errors`, `GITHUB_TOKEN` unset
(two `test_prism_w4_lab_pr_state.py` nodes assert `UNAVAILABLE` and fail when the
variable is present).

---

## 2. Backlog shape

| Fact | Measurement |
|---|---|
| Open PRs | **65** |
| Draft | **65 / 65** — drafts need owner action to become ready; no silent conversion (GOV-04) |
| Green on their own head | **41** |
| Green except the proven-intermittent external N-ATLaS jobs | **22** |
| Attributable check failure | **2** (#716, #744) |
| Textual conflict with `main` | **1** (#686, `AGENTS.md`) |
| Behind `main` | **all 65** (3–9 commits); **0 / 65** are based on current `main` |
| Distinct paths touched | 282 |
| Paths touched by more than one open PR | **14** |
| Changed paths rejected by the canonical CP10 policy | **0** (no PR needs an allowlist change) |
| Added lines matching the capability's credential shapes | **0** across 298 files |

Because no PR is based on current `main`, **every green check is green against an
older base**. A green head is a statement about that tree, not about the tree
`main` will become. That is why composition is measured here rather than inferred.

### The 14 contended paths

| Paths | PRs | Consequence |
|---|---|---|
| `api/main.py` | #701, #711, #717, #729 | 2600-line budget + shared handler surfaces |
| `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py` | #681, #687 | ordered pair (app identity → cold start) |
| `scripts/lane_state_refresh.py` | #682, #684 | ordered pair |
| `docs/control-plane/parallel-ui/lane-state.json` | #684, #747 | snapshot currency |
| `.github/workflows/canonical-render-browser-smoke.yml` | #689, #728 | ordered pair |
| `.github/workflows/prism-console-contract.yml` | #707, #728 | ordered pair |
| `web/arkadia_console/src/lib/endpoints.ts` | #692, #704 | ordered pair |
| `solspire/console_router.py` | #710, #713 | ordered pair |
| `api/arkana_stream_routes.py` | #717, #721 | ordered pair |
| `.github/workflows/economic-seam-engine.yml` | #718, #734 | ordered pair |
| `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md` | #693, #716 | root-doc edits |

---

## 3. Findings that change how the queue should be handled

**F1 — The merged Chief review capability refuses all 65 PRs, correctly.**
`review_pull_request` returned `REFUSED:WorkerUnavailable` for **65 / 65**:
*"GitHub App worker is not configured: missing ARKADIA_PR_REVIEW_APP_ID,
ARKADIA_PR_REVIEW_INSTALLATION_ID, ARKADIA_PR_REVIEW_INSTALLATION_TOKEN."*
The capability is on `main` but `SHADOW` is unreachable until a GitHub App is
registered and installed. Its refusal is the honest state, not a defect. Backlog
review in this pass therefore rests on direct read-only evidence, with the
capability's finding engine exercised separately (§6).

**F2 — `main` moving invalidated an open PR's recorded inventory.**
`#711` records the webhook surface exactly (`RECORDED_WEBHOOK_OPERATIONS`, two
entries). Composing #749 (merged today) with #711 makes
`tests/test_github_webhook_surface_inventory.py::test_live_webhook_surface_matches_the_recorded_inventory`
fail with *"POST /api/lab/engineering/pr-review/webhook is a webhook operation
absent from the recorded inventory"*. Measured on the composed tree, not
predicted. #711 needs one entry added and its "exactly two" test renamed:

```python
("post", "/api/lab/engineering/pr-review/webhook"): {
    "classification": "github_webhook_hmac",
    "runtime_guard": "X-Hub-Signature-256",
    "security": (("GitHubWebhookHMAC",),),
},
```

This is the "a content-derived guard domain cannot be validated by the branch
that adds a member to it" class, now with a second instance: the member was
added by a **merge**, not by a sibling branch.

**F3 — The four `api/main.py` PRs compose textually and within budget, but one
of them goes red on the composed tree.** #701 + #711 + #717 + #729 merge with
zero conflicted files; the composed `api/main.py` is **2589 lines** (budget
2600, headroom 11 — `main` is 2597, so the quartet *shrinks* the file). The full
suite on that composed tree reports **21 failed** against `main`'s **20**, the
extra node being F2's inventory assertion. So the quartet is blocked by a
one-line inventory refresh in #711, not by the budget.

**F4 — Two PRs fail for reasons that are not their diffs.**
* #716 fails `Build MIE / Sonata debug APK` because it edits
  `sonata-android/README.md`, which selects the MIE gate, and that gate is red on
  `main` for the classpath defect **#719** repairs (measured: #719's own head
  passes the same check; #716's only Android change is markdown).
* #744 fails its own new `portfolio-state` guard on its own head (step
  *"Execute the portfolio ledger guard"*) — attributable, so REVISE.

**F5 — The external N-ATLaS jobs are intermittent and are not evidence about a
tree.** `n-atlas-external-beta.yml` produced `native-arkadia-golden-workflow`,
`beta-beta-01-english`, `beta-beta-02-hausa`, `bundle-beta-evidence`; **11 of its
last 12 runs succeeded** across unrelated heads, and the failing log shows the
Hausa Gradio app raising `gr.Error`, i.e. the provider. 22 PRs are "red" only
through this class. They are counted as green-with-known-external-flake, and the
report says so rather than silently rounding them to green.

**F6 — Three PRs build overlapping read-only PR-queue tooling.**
#694 (`scripts/open_pr_inventory.py`), #733 (`scripts/pr_batch_reconcile.py`),
#736 (`scripts/pr_wave_dry_run.py`). Each is green, none conflicts, and together
they are three implementations of one idea. Merging all three converts a
reconciliation fix into maintenance debt. #694 is recommended; #733 and #736 are
HUMAN_REVIEW for a "keep one" decision.

**F7 — No live work is superseded, but the queue has a staleness floor.**
`git cherry origin/main pr/<n>` reports ≥1 unapplied commit for all 65 PRs, so no
PR's change is already on `main` by patch equivalence. The staleness floor is
3 commits (#743, #744, #745, #747), the ceiling 9 (#680).

---

## 4. Dispositions (65 / 65)

`MERGE_CANDIDATE 51 · HUMAN_REVIEW 10 · REVISE 3 · BLOCKED 1 · SUPERSEDED 0`

"Review engine" is the merged capability's deterministic finding stage (§6):
GREEN = no diff/check finding, RED = a failing check run present. It is evidence,
**not** merge authorization — a GREEN engine verdict appears next to several PRs
this report does not recommend merging now.

| PR | Title | Risk | Behind | Checks on head | Review engine | Disposition | Reason |
|---|---|---|---|---|---|---|---|
| #680 | Lane 4: bind the details scanner to a nesting control | LOW | 9 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | batch A: composed + full suite verified, zero new nodes |
| #681 | fix(gate2): bind the marker oracle to the app the serve... | MED | 8 | 10/13 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; first half of the #681->#687 pair |
| #682 | Lane 1: bind the advertised-contract control to its det... | MED | 8 | 11/11 pass | GREEN | **MERGE_CANDIDATE** | green; precedes #684 (shared `lane_state_refresh.py`) |
| #683 | Lane 4: enforce the Lab PR-state guard's no-token premise | LOW | 8 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | batch A: composed + full suite verified, zero new nodes |
| #684 | fix(lane-currency): judge snapshot completeness, not on... | MED | 6 | 11/11 pass | GREEN | **MERGE_CANDIDATE** | green; follows #682 and precedes #747 (shared `lane-state.json`) |
| #685 | fix(console): stop the shared placeholder calling a ser... | MED | 8 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; frontend + one contract test, no contention |
| #686 | fix(weaver): redact remote userinfo before the context ... | HIGH | 5 | 16/16 pass | GREEN | **REVISE** | conflicts on `AGENTS.md` (insert-only governed file); `weaver/` authority surface |
| #687 | fix(gate2): stop calling a warming deployment an unreac... | MED | 8 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | green; second half of the #681->#687 pair |
| #688 | fix(hygiene): sandbox the Engineering Lab event log ins... | LOW | 8 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | green; `.gitignore` + `conftest.py` + one guard |
| #689 | fix(gate): stop the canonical browser smoke failing on ... | MED | 8 | 12/13 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; precedes #728 (shared browser-smoke workflow) |
| #690 | test(hygiene): call the project-file store with its sco... | LOW | 8 | 9/10 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; two test files |
| #691 | fix(test): bind the R3 mutation refusal to its canonica... | MED | 8 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green; one workflow + one test file |
| #692 | feat(console): read the served proposal ledger instead ... | MED | 8 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; precedes #704 (shared `endpoints.ts`) |
| #693 | test(hygiene): drop five repaired nodes from the record... | LOW | 8 | 8/11 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; changes the baseline fixture, so re-measure after batch A |
| #694 | test(hygiene): judge open-PR composition, not only each... | MED | 6 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | green; the one PR-queue tooling PR to keep (F6) |
| #695 | fix(ci): stop CP10 reporting a masked step as a verdict | MED | 6 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green; `sg-02-fe-2-v.yml` + one guard |
| #696 | ci(gate): execute the api/main.py line budget on the su... | MED | 6 | 11/14 pass; red: beta-beta-01-english, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; new `architecture-budget.yml`, compose before merging |
| #697 | gate(ops): identify the deployed revision on every push... | MED | 6 | 13/14 pass | GREEN | **MERGE_CANDIDATE** | green; new `runtime-revision-identity.yml` |
| #698 | test(hygiene): give the K5 round-trip test its own orac... | LOW | 6 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | batch A: composes clean and **repairs one pre-existing failure** |
| #699 | gate(hygiene): execute the lane aggregate-PR guard in t... | MED | 6 | 12/13 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; `lane-doc-currency.yml` |
| #700 | test(hygiene): recover the archived A.I.S node-formatio... | LOW | 6 | 7/10 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; archived source + two pinned tests |
| #701 | fix(corpus): read the public GitHub corpus anonymously ... | HIGH | 6 | 18/18 pass | GREEN | **HUMAN_REVIEW** | `api/main.py` + credential-fallback path - authority surface, reserved human decision |
| #702 | gate(hygiene): make every pull-request pytest gate disp... | MED | 6 | 17/17 pass | GREEN | **MERGE_CANDIDATE** | green; six workflows, no contention |
| #703 | docs(gate2): measure the #681/#687 composition instead ... | LOW | 6 | 5/6 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | batch A: docs-only |
| #704 | feat(console): surface ReasoMate direct threads over th... | MED | 6 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; after #692 |
| #705 | docs(control-plane): record ARK-OPS-CONTINUOUS-001, its... | LOW | 6 | 6/6 pass | GREEN | **MERGE_CANDIDATE** | batch A: docs-only (15 files, purely additive) |
| #706 | test(hygiene): judge prose route claims in the console ... | MED | 6 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; console operator data + one guard |
| #707 | test(hygiene): judge the Prism UI inventory against the... | MED | 6 | 12/12 pass | GREEN | **MERGE_CANDIDATE** | green; precedes #728 (shared contract workflow) |
| #708 | fix(console): stop the Opportunity Radar claiming a rep... | MED | 6 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; console contract module + guard |
| #709 | docs(deploy): stop the deployment guide describing an a... | LOW | 6 | 7/10 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; `DEPLOYMENT_GUIDE.md` + guard |
| #710 | fix(solspire): refuse a mutation plan as a governed 403... | MED | 6 | 14/14 pass | GREEN | **MERGE_CANDIDATE** | green; precedes #713 (shared `console_router.py`) |
| #711 | test(hygiene): bind the GitHub push-webhook surface to ... | HIGH | 6 | 17/17 pass | GREEN | **REVISE** | recorded webhook inventory is stale after merged #749 (F2): one entry + one test rename |
| #712 | fix(lab): run the PR-state read off the event loop, and... | HIGH | 6 | 17/20 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **HUMAN_REVIEW** | `api/lab_routes.py` - Lab authority surface, reserved human decision |
| #713 | fix(solspire): run blocking console routes in the threa... | MED | 6 | 16/16 pass | GREEN | **MERGE_CANDIDATE** | green; after #710 |
| #714 | docs(readme): stop the front door linking a frontend th... | MED | 6 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green; new `root-doc-link-integrity.yml` |
| #715 | docs(map): judge table rows, the architecture maps, and... | MED | 6 | 12/13 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; root docs + new module-map gate |
| #716 | fix(docs): stop the operational documents naming a reti... | MED | 6 | 17/18 pass; red: Build MIE / Sonata debug APK | RED | **BLOCKED** | MIE red from the pre-existing classpath defect #719 repairs; its only Android change is markdown |
| #717 | fix(gemini): give every Gemini text surface one fallbac... | HIGH | 6 | 19/19 pass | GREEN | **HUMAN_REVIEW** | 13 files spanning `api/main.py`, commune/CEO/stream routes - authority + provider routing |
| #718 | Repair the Knowledge OS 5xx error contract and guard it... | MED | 6 | 12/15 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; precedes #734 (shared workflow) |
| #719 | fix(mie): give the JVM unit tests a real org.json so th... | MED | 6 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green **including** the MIE APK build; unblocks #716 |
| #720 | fix(research): execute the Oversoul Prism conformance h... | MED | 6 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green; new conformance gate |
| #721 | fix(arkana): drop the streaming route's dead key fallba... | MED | 6 | 9/12 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; after #717 (shared stream routes) |
| #723 | test(gate): read a guide row as an endpoint only when i... | LOW | 6 | 9/10 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; one guard |
| #725 | test(gate): bind the GOV-04 auto-merge and post-merge p... | LOW | 5 | 7/10 pass; red: beta-beta-01-english, bundle-beta-evidence | RED | **HUMAN_REVIEW** | changes GOV-04 approval-enforcement evidence - reserved human decision |
| #726 | test(gate): make GOV-04's platform precondition decidab... | MED | 5 | 12/13 pass; red: native-arkadia-golden-workflow | RED | **HUMAN_REVIEW** | adds a GOV-04 platform-precondition gate - governance surface |
| #727 | docs(gate): measure the repair-wave composition and rec... | LOW | 5 | 6/6 pass | GREEN | **MERGE_CANDIDATE** | batch A: docs-only |
| #728 | Make the canonical browser smoke score the route it act... | MED | 5 | 12/13 pass; red: native-arkadia-golden-workflow | RED | **MERGE_CANDIDATE** | external-flake only; **last** in the #689->#707->#728 chain |
| #729 | fix(api): stop eight 5xx handlers echoing the exception... | HIGH | 5 | 13/17 pass; red: beta-beta-01-english, beta-beta-02-hausa, bundle-beta-evidence | RED | **HUMAN_REVIEW** | `api/main.py` + a new HTTP-failure contract - authority surface |
| #730 | test(hygiene): bind seven always-true assertions to rea... | LOW | 5 | 7/10 pass; red: beta-beta-01-english, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; nine test files, no contention |
| #731 | fix(auth): declare the identity five thread routes and ... | HIGH | 5 | 13/13 pass | GREEN | **HUMAN_REVIEW** | `api/openapi_security.py` + `api/commune_threads.py` - authorization declaration |
| #733 | feat(recon): add read-only batch PR evidence packet | MED | 5 | 9/10 pass; red: native-arkadia-golden-workflow | RED | **HUMAN_REVIEW** | duplicate purpose with #694/#736 (F6) |
| #734 | Judge the Prism coherence README domain from the tracke... | MED | 5 | 12/12 pass | GREEN | **MERGE_CANDIDATE** | green; after #718 |
| #735 | fix(api): stop the source-sync 502 returning the caught... | MED | 5 | 15/15 pass | GREEN | **MERGE_CANDIDATE** | green; `api/source_routes.py` + new error-contract gate |
| #736 | feat(recon): compose the open-PR queue instead of assum... | MED | 5 | 13/13 pass | GREEN | **HUMAN_REVIEW** | duplicate purpose with #694/#733 (F6) |
| #737 | Record the served asset manifest, not only the revision | MED | 5 | 14/14 pass | GREEN | **MERGE_CANDIDATE** | green; runtime probe + new manifest script |
| #738 | test(gate): assert every fail-open router mount carries... | LOW | 5 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | batch A: composed + full suite verified, zero new nodes |
| #739 | fix(gate2): scope the browser observation oracle to the... | MED | 5 | 10/10 pass | GREEN | **MERGE_CANDIDATE** | green; `gate2_browser_observation.py` (distinct from #681/#687) |
| #740 | gate(hygiene): select the GOV-04 conformance guard's in... | MED | 5 | 13/13 pass | GREEN | **HUMAN_REVIEW** | GOV-04 conformance gate wiring - governance surface |
| #741 | Arkadia One: coherent operating environment (Phase 1 ba... | LOW | 4 | 3/6 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | batch A: docs-only; read before merging (strategic baseline) |
| #742 | fix(console): stop the home portal grid printing five l... | MED | 4 | 13/16 pass; red: beta-beta-02-hausa, bundle-beta-evidence | RED | **MERGE_CANDIDATE** | external-flake only; `HomePage.tsx` + guard |
| #743 | fix(distribution): stop the upload route letting a clie... | MED | 3 | 15/15 pass | GREEN | **MERGE_CANDIDATE** | green; `api/distribution.py` + new contract gate |
| #744 | feat(weaver): give the portfolio fairness rule a durabl... | MED | 3 | 12/13 pass; red: portfolio-state | RED | **REVISE** | its own new `portfolio-state` guard fails on its own head (F4) |
| #745 | fix(plan): stop /api/plan/run echoing the caught except... | MED | 3 | 12/12 pass | GREEN | **MERGE_CANDIDATE** | green; `api/plan_routes.py` + guard |
| #746 | test(gate): execute the stellar contract, and hold the ... | MED | 3 | 13/13 pass | GREEN | **MERGE_CANDIDATE** | green; new stellar-contract gate |
| #747 | fix(lane-currency): drop a merged PR from the unassigne... | LOW | 3 | 7/7 pass | GREEN | **MERGE_CANDIDATE** | green; merge after #684 (shared `lane-state.json`) |

---

## 5. Proposed merge batch A — smallest safe batch, exact order

Eight PRs. All are LOW risk, file-disjoint, conflict-free, and green on their own
head except the two whose only failure is the proven-intermittent external
N-ATLaS workflow. Six of the eight cannot change runtime behaviour at all
(docs-only or docs + one guard). None touches an authority surface, `api/main.py`,
or a *gate definition* that judges other PRs.

| Order | PR | Head SHA | Files | Why this position |
|---|---|---|---|---|
| 1 | #727 | `f3d10739644ddc173514c9435bbb3c4b172224b1` | `docs/…/repair-wave-composition-01/EVIDENCE.md` | docs-only, records the baseline this batch is measured against |
| 2 | #705 | `2732b81a05d2cb8bc25ce93841f6d97ff4264f51` | 15 files, `docs/control-plane/evidence/ark-ops-continuous-001/**` | docs-only, largest additive documentation block |
| 3 | #741 | `b9898141c99628ef1ee7acbef44301a1af407027` | `docs/…/ark-one-implement-001-phase1-baseline/EVIDENCE.md` | docs-only; strategic baseline the sovereign should read |
| 4 | #703 | `3b2e5b73d3d96257da13f8e068f7ce117c003ac6` | `docs/…/gate2-open-pr-composition-01/EVIDENCE.md` | docs-only |
| 5 | #680 | `0023c7813eda7aa90221c176ace9e8f3d7df2a76` | evidence + `tests/test_lab_repository_surface_contract.py` | guard-only; no runtime path |
| 6 | #698 | `91e73dfd8deabf9becd243e733c52b236e8ad325` | evidence + `tests/test_static_ingestion_idempotency.py` | guard-only; **repairs** a pre-existing failure |
| 7 | #738 | `4ede192898f535f8090681ff4ec453941c423ab3` | evidence + new `tests/test_router_mount_completeness.py` | guard-only, additive test file |
| 8 | #683 | `4c9261cf7f28d612ca59f77c551a39cf90d9bbf5` | evidence + `tests/test_prism_w4_lab_pr_state.py` | guard-only; asserts the no-token premise |

Order is deterministic but not load-bearing for files (they are disjoint). It is
ascending risk of touch: pure docs → docs + one existing guard → docs + one new
guard. Any subset merged in this order was also composes cleanly, because no two
of them share a path.

### Composition evidence for batch A

Composed in a detached worktree on `main` `68db6619`, merging the eight heads in
the order above: **zero conflicted files**, tree `e9de9fe7`.

| Measurement | `main` `68db6619` | batch A composed `e9de9fe7` |
|---|---|---|
| Full suite | **20 failed / 4325 passed / 22 skipped / 1 error** | **19 failed / 4335 passed / 22 skipped / 1 error** |
| Failing/error node set | 21 nodes, sha256 `4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916` | 20 nodes, sha256 `143891ac5880a9e756f1e4ccc1192780869d40c0e1ef2308f7afbd8686124f39` |
| Nodes only on the composed tree | — | **none** (`comm -13` empty) |
| Node only on `main` | `tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | absent — **repaired by #698** |

So the batch is not merely "not worse": it removes one pre-existing failure and
adds none. The `+10 passed` is the new guard nodes from #680/#683/#738/#698.

**Batch A is safe to merge; it is not authorized by this report.** All eight are
drafts, so each requires an owner action to become ready, then a GOV-04 eligible
merge at the exact heads above. If any head moves, discard this measurement and
re-measure.

---

## 6. The merged Chief review capability, used honestly

Two measurements, both against live data:

**Authorized entrypoint** — `pr_review.review_pull_request(...)` over all 65 PRs:
**65 / 65 `REFUSED:WorkerUnavailable`**
(*"missing ARKADIA_PR_REVIEW_APP_ID, ARKADIA_PR_REVIEW_INSTALLATION_ID,
ARKADIA_PR_REVIEW_INSTALLATION_TOKEN"*). The capability cannot review without a
GitHub App installation, and no worker borrowed the ambient connector
credential to pretend otherwise. This is the capability working as designed, and
it is the standing blocker for `SHADOW`.

**Finding engine** — with the canonical CP10 policy injected
(`scripts.cp10_mutation_boundary_policy.evaluate_changed_paths`) and observed
diffs/check-runs as input: **41 GREEN / 24 RED**, every RED caused by
`CHECK_FAILED`. Two additional results worth keeping:

* `CREDENTIAL_SHAPED_ADDITION`: **0** across 298 changed files — no open PR adds
  a credential-shaped line.
* `PATH_OUTSIDE_POLICY`: **0** — every changed path in the queue is admitted by
  the canonical mutation-boundary policy, so no PR needs an allowlist edit.

Per doctrine: **GREEN ≠ merge authorization.** #701, #717 and #731 are GREEN by
the engine and still HUMAN_REVIEW here, on authority-surface grounds the engine
does not judge.

---

## 7. Ordered dependency ledger

`→` means "merge/land before". These are the only ordering constraints the
measurements justify.

```
#682 → #684 → #747                     (lane_state_refresh.py, lane-state.json)
#681 → #687 → #703(documentary)        (gate2_production_observation.py)
#692 → #704                            (web/arkadia_console/src/lib/endpoints.ts)
#710 → #713                            (solspire/console_router.py)
#718 → #734                            (economic-seam-engine.yml)
#717 → #721                            (api/arkana_stream_routes.py)
#707 → #689 → #728                     (prism-console-contract.yml, canonical-render-browser-smoke.yml)
#719 → #716                            (MIE APK: #716 is red until #719 repairs the classpath)
#749(merged) → #711 (REVISE)           (webhook inventory must record the pr-review route)
#701, #717, #729 → then #711           (same stale-inventory constraint if #711 lands later)
```

Batch A participates in none of these chains.

---

## 8. Explicitly not done

| Not done | Why |
|---|---|
| No merge, no merge queue, no auto-merge | the directive; GOV-04 leaves execution to the designated operator at an exact head |
| No PR closed, no PR marked ready | drafts require owner action; closing would destroy the evidence trail |
| No branch-protection / ruleset / CODEOWNERS change | reserved; also `main` has no protection to change |
| No deployment, no `Vercel`/Render interaction | ADR-016; nothing here is a deployment claim |
| No new PR opened | the directive; the report is committed to a reconciliation branch only |
| No push to any existing PR branch | #686/#711/#716/#744 need *their owners'* bounded changes; recording the exact remediation is in scope, performing it is not |
| No claim that a green check means mergeable | F1/F3/F5 exist precisely because that inference failed |

Environment note: this sandbox was re-provisioned during the pass (dependencies
absent at start). `pip install -r requirements.txt pyyaml pyflakes` was run, and
the baseline reproduced byte-identically (`4118e2ff…`), so the measurements above
are from a reproducible environment, not an inferred one.

---

## 9. Next-action ledger (deterministic)

| # | Action | Owner | Precondition | Completion condition |
|---|---|---|---|---|
| 1 | Read batch A, then mark #727, #705, #741, #703, #680, #698, #738, #683 ready and merge in that order at the heads in §5 | Human (GOV-04 operator) | heads unchanged since 2026-11-26; if any head moved, re-run §5 composition | composed tree still reports 20 nodes / no new failures after the last merge |
| 2 | Re-derive the baseline after batch A, then review #693 (baseline fixture) | Human | batch A merged | fixture matches measured debt |
| 3 | Ask #711's owner to add the pr-review webhook entry (F2) and re-run its guard | PR owner | #749 merged | `test_live_webhook_surface_matches_the_recorded_inventory` green on a fresh head |
| 4 | Ask #744's owner to fix the `portfolio-state` guard on its own head | PR owner | none | `portfolio-state` green on the PR's head |
| 5 | Merge #719, then re-run #716 | Human | #719 merged | MIE APK green on #716's re-run |
| 6 | Resolve #686's `AGENTS.md` conflict by append-only edit, then authority review | PR owner + sovereign | insert-only rule | `merge-tree` clean and audit `alterations=0` |
| 7 | Decide one of #694 / #733 / #736 and close or fold the others | Sovereign | none | exactly one PR-queue tool remains open |
| 8 | Review the authority quartet #701 / #717 / #729 / #731 as a set (composition measured: 2589 lines, clean, one inventory failure traced to #711) | Sovereign | #711 repaired | decision recorded per PR |
| 9 | Compose wave 2 before merging it: #690, #700, #709, #723, #730, #697, #714, #715, #735, #743, #745, #746 | Human | batch A merged | full suite on the composed tree adds no node |
| 10 | Register the GitHub App so `chief.pr_review` can reach `SHADOW` | Human | permissions in `chief-pr-review-001/PERMISSION-MATRIX.md` | one real PR reviewed read-only, evidence `EVD-*` recorded |

Stop conditions for the next pass: a merged head that moves, a check that is
`BLOCKED` on a provider credential, or a governance contradiction (`GOV-04`
eligibility vs. an authority-surface change) — record and stop, do not
self-authorize.

---

## 10. Reproduction

```bash
git fetch origin main '+refs/pull/*/head:refs/remotes/pr/*'
# inventory + dispositions were derived from GitHub REST reads:
#   /pulls?state=open, /pulls/{n}, /pulls/{n}/files, /commits/{head}/check-runs
# conflict per PR:
git merge-tree --write-tree --name-only origin/main pr/<n>
# staleness:
git rev-list --count pr/<n>..origin/main ; git rev-list --count origin/main..pr/<n>
# already-applied oracle:
git cherry origin/main pr/<n>
# composition (batch A):
git worktree add --detach /tmp/wt-batch origin/main
cd /tmp/wt-batch && for n in 727 705 741 703 680 698 738 683; do git merge --no-edit pr/$n; done
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

---

## 11. Execution pre-flight for batch A (re-measured 2026-11-26, after §5)

The report above was written against `main` `68db6619`. This section is the
re-verification required before any merge, and it **corrects one thing in §5**.

### 11.1 What is unchanged

| Fact | Re-measured |
|---|---|
| `main` | `68db6619ee438ade7d8c32786076aab877e308a5` — **unchanged** |
| Batch A heads | **all 8 unchanged** (`f3d10739`, `2732b81a`, `b9898141`, `3b2e5b73`, `0023c781`, `91e73dfd`, `4ede1928`, `4c9261cf`) |
| Base ref / mergeability | all 8 `base=main`, `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN` |
| Batch A composition (§5) | still valid — no head and no base moved |

### 11.2 Correction: M6 admits no exemption, so §5's batch is two PRs wider than is eligible

`docs/control-plane/evidence/residual-recovery-2026-10-27-01/EVIDENCE.md` §8.12
is the repository's own precedent for the retained M1–M13 rubric, and its M6
reads: *"checks: … the criterion admits no exemption"* — a pre-existing,
environmental, or someone-else's-debt failure does **not** satisfy M6. GOV-01's
preserved boundaries also forbid waiving M1–M13.

Applying M6 as written splits batch A:

| Group | PRs | Checks on head | M6 |
|---|---|---|---|
| **Eligible as measured** | #727, #705, #680, #698, #738, #683 | 6/6, 6/6, 10/10, 10/10, 10/10, 10/10 | PASS |
| **Not eligible as measured** | #741, #703 | 3/6 and 5/6 — `beta-beta-02-hausa`, `bundle-beta-evidence`, `native-arkadia-golden-workflow` | **FAIL** |

The two failures are still the external N-ATLaS jobs (§F5), and they are still
not evidence about those diffs. But "not the branch's fault" is not an M6
exemption, so #741 and #703 must either collect a green re-run of those jobs or
stay open. **They are moved out of the executable batch**; the order of the
remaining six is unchanged.

### 11.3 Two preconditions that only a human can clear

**Draft state.** All six eligible PRs are `draft: true`, authored by
`Arkadia-Oversoul-Prism`. GOV-04: *"Drafts must be explicitly made ready by
their owner; no silent draft conversion."* No agent may flip that bit.

**Branch protection is unreadable with this credential.**
`GET /repos/…/branches/main/protection` returns **403 "Resource not accessible
by integration"** and `/rulesets` returns `0`. So "branch protections and merge
queue are satisfied" (GOV-04 condition 2) cannot be *affirmatively verified by an
agent here* — it is `UNKNOWN`, not `PASS` and not `FAIL`. Only GitHub's own
enforcement at merge time settles it. Recorded rather than assumed in either
direction: the earlier "`main` has no protection" note was a **404**, and a 403 is
a different observation.

### 11.4 Eligibility assessment — first in sequence, #727

Exact head `f3d10739644ddc173514c9435bbb3c4b172224b1`, base `main` `68db6619`.

| criterion | state | evidence |
|---|---|---|
| M1 canonical target | PASS | `base.ref == main`, canonical repository |
| M2 provenance | PASS | head unchanged since the inventory; single commit `f3d10739` |
| M3 scope | PASS | 1 new file, `docs/…/gate-hygiene-repair-wave-composition-01/EVIDENCE.md`, +144/−0; CP10 judge → *Mutation boundary PASS* |
| M4 governance | PASS | docs-only evidence record; no authority, identity, approval, K15/K3, deployment or acceptance surface |
| M5 reviews | UNKNOWN | `reviewDecision` empty, 0 reviews; no required-review configuration readable (protection 403) |
| M6 checks | PASS | 6/6 `completed/success` on the exact head, no pending, no skipped-required |
| M7 tests | PASS | the file is documentation; batch-A composed suite (§5) is the regression evidence |
| M8 conflicts/freshness | PASS | `MERGEABLE`/`CLEAN` vs `68db6619`; `merge-tree` clean |
| M9 dependencies | PASS | none; first in the order, disjoint from every other batch path |
| M10 regression boundary | PASS | composed-tree node set adds nothing (§5) |
| M11 merge method | PASS (would be) | PR merge at expected head only; no direct push, no force-push |
| M12 authorization | **HUMAN_AUTHORITY_REQUIRED** | draft owner action + per-PR human merge authorization |
| M13 final revalidation | NOT REACHED | blocked at M5/M12 |

**Disposition: NOT YET ELIGIBLE — fail-closed at M5/M12.** Nothing about the diff
is in question; the two blockers are platform state (draft bit) and the
authorization boundary, both reserved to the human.

### 11.5 Per-PR execution protocol (to be repeated after every merge)

For PR *n* in the order:
1. re-fetch `main`; if it moved, re-run the composition measurement before proceeding;
2. confirm `pulls/<n>.head.sha` equals the recorded head, else discard the disposition;
3. re-read check-runs on that exact head and require `completed/success` for all (M6);
4. require owner action to clear the draft bit, then human merge authorization for that PR;
5. merge through the protected merge API with `sha=<recorded head>`;
6. after the merge, verify the resulting `main` SHA and that the intended diff landed;
7. reconcile PR *n+1* against the new `main` — the earlier composition is no longer proof.
