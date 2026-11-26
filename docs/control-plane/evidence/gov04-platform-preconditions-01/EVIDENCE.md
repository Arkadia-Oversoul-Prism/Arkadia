# GOV-04 condition 2 names platform controls that no surface measured

- **Contract:** `ARK-OPS-CONTINUOUS-001`, rev `2026-11-22`
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no provider mutation, no acceptance claimed.
- **Change:** one classifier script, two guard files (one with controls), one workflow, this
  record. No application code, no governance document, no authority surface.

---

## 1. Reconstructed state (measured, not inherited)

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse origin/main`; local `HEAD` agreed at pass start |
| newest main commit | `fd0a4fdc` — "governance(GOV-04): bounded merge delegation with exact-head safeguards (#722)" | `git log -1` |
| open PRs | **47**, **46** draft | `GET /repos/.../pulls?state=open` |
| `main` check-runs | `boot-syntax`, `console-contract`, `lane-doc-currency`, `posture-currency`, `test`, `engineering-scheduler`, `Full-history secret scan` — all `success` | `GET /commits/fd0a4fdc.../check-runs` |
| production `source_revision` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`, `revision_source: RENDER_GIT_COMMIT`, `revision_conflict: false` | `GET https://arkadia-qzu4.onrender.com/api/version` (repeated) |
| production root / health | `/` -> `200` with a browser `Accept`; `/health` -> `{"status":"radiant"}` | `curl` |
| console build | `pnpm build` exit **0**, 170 modules, `dist/assets/index-CYGHeCpJ.js` 425.15 kB | `corepack pnpm install --frozen-lockfile` + `build` in `web/arkadia_console` |

Source↔runtime consistency: **VERIFIED** (the deployed revision is sha-identical to `main`).
That is consistency evidence. It is **not** application correctness and **not** acceptance.

## 2. Baseline debt is fully owned — so this cycle looked past the failing nodes

Full suite at `main` `fd0a4fdc`:

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 20 failed, 4253 passed, 22 skipped, 6 warnings, 1 error in 283.44s
```

**21** failing/error nodes; outcomes sha256
`4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916`, node-set sha256
`cdf25fd81aa63bfa64e5845fba4944902f3ff2c1207c4e64df36f31a508dcfd8`. The outcomes value agrees
exactly with the one PR #725's own evidence recorded for the same revision — two independent
measurements of one tree.

Every one of those 21 nodes is owned, measured by `GET /pulls/<n>/files` across all 47 open PRs:

| node(s) | owner |
|---|---|
| `tests/test_gov04_bounded_merge_delegation.py::test_bounded_merge_is_exact_head_and_protected_fail_closed` | **#725** |
| `tests/test_identity_spine_w1.py::...`, `tests/test_m02_reasomate_truth.py::...` | **#700** |
| `tests/test_m01_persistence.py::...`, `tests/test_m05_files.py::...` | **#690** |
| `tests/test_solspire_r1_governance_convergence.py` (2) | **#693** |
| `tests/test_solspire_r3_execution_runtime.py::...` | **#691** |
| `tests/test_static_ingestion_idempotency.py::...` | **#698** |
| `ERROR tests/test_autonomy.py` | CE-01, sovereign-reserved |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | F-01, deliberately failing pending a sovereign call |

Ten further nodes (`tests/test_mission_lifecycle_adapter_contract.py`) are **environment-only**,
not debt: they assert the repository's TypeScript compiler exists. After
`corepack pnpm install --frozen-lockfile` in `web/arkadia_console` the file is **10 passed**
(measured this pass). CI already installs it in `prism-console-contract.yml`, which derives its
domain from `scripts/console_contract_domain.py` — that domain contains this file.

So there was **no unowned failing node**, and adding another test-repair PR would have competed
with five existing ones. The docs/console/privacy lanes are likewise covered by #704–#723.

## 3. The defect: a precondition that cannot fail, and nothing that measures it

GOV-04 (merged 35 minutes before this pass, `fd0a4fdc`) authorises a bounded merge delegation.
Its condition 2 reads:

> All required checks pass; required reviews/CODEOWNERS approvals are present; branch
> protections and merge queue are satisfied.

Every clause names a **platform-enforced** control. Measured live:

```
GET /repos/Arkadia-Oversoul-Prism/Arkadia/branches/main/protection
  -> 404 {"message":"Branch not protected"}
GET /repos/Arkadia-Oversoul-Prism/Arkadia/rulesets
  -> []
```

`main` carries **no branch protection and no ruleset**. No required status check, no required
review, no merge queue. Condition 2 is therefore **vacuously satisfiable**: nothing is required,
so nothing can fail, and the clause reads as a safeguard while constraining nothing.

The measurement gap is separate from the platform state, and it is the part this change closes.
Across the whole repository, nothing read those two endpoints:

```
grep -rln "branch protection\|branch_protection\|rulesets" tests/ scripts/ .github/
  -> tests/test_gov04_bounded_merge_delegation.py     (reads the document's wording)
  -> tests/__pycache__/...pyc                          (build artifact)
```

`tests/test_gov04_bounded_merge_delegation.py` asserts that the authorization **document**
contains certain phrases. It never asks the platform anything. No open PR adds such a surface:
#725 pins two document literals, #724 records the activation. Neither measures.

This is the class the repository has recorded repeatedly — a field written but never judged, a
guard that prints a verdict and does not act on it. Here the precondition is *named* in a
governance record and measured nowhere.

## 4. What was built, and what it deliberately does not do

`scripts/gov04_platform_preconditions.py` is a pure classifier over the two REST payloads:

| verdict | meaning |
|---|---|
| `ENFORCED` | positive evidence of a control a merge can fail: required status checks, required reviews, or an **active** ruleset carrying `required_status_checks` / `pull_request` / `required_deployments` / `merge_queue` |
| `VACUOUS` | measured absence of every such control, so condition 2 cannot fail |
| `UNKNOWN` | the evidence could not be read, or contradicts itself — never promoted to `ENFORCED` |

`protection_state` separates a **measured absence** (`absent`, the REST 404) from an
**unreadable** one (`unknown`). They need opposite responses — `VACUOUS` is a fact about the
platform, `UNKNOWN` is a fact about the measurement — so they never share a verdict.

Three deliberate non-functions:

1. **A `VACUOUS` verdict does not fail a gate.** Enabling branch protection is a sovereign /
   provider configuration decision. A gate that reddened CI for the operator's choice would
   report a decision as repository debt, and would make `main` permanently red for something no
   agent may change. The teeth are on the classifier instead.
2. **The classifier never touches the network.** `--measure` does the read-only fetch; the
   classifier is pure, so the guard runs offline with only `pytest` + `pyyaml` installed. A
   dependency gap cannot be misreported as a classifier regression.
3. **`--measure` prints no credential**, and refuses with exit 2 and no output when
   `GITHUB_TOKEN` is unset.

Live result of the tool itself:

```
$ GITHUB_TOKEN=... python scripts/gov04_platform_preconditions.py --measure
{"classification": {"detail": "no branch protection and no ruleset is configured, ...",
                    "required_checks": [], "required_reviews": 0,
                    "ruleset_rules": [], "verdict": "VACUOUS"},
 "evidence": {"protection_state": "absent", "protection_status_code": 404,
              "ruleset_count": 0}, ...}
```

## 5. Verification

### 5.1 The guards

```
python -m pytest tests/test_gov04_platform_preconditions.py \
                 tests/test_gov04_platform_preconditions_ci_wiring.py -q
-> 26 passed
```

Porcelain down to its two files: `13 passed` (classifier + controls) and `13 passed` (wiring).

Classifier controls, each of which fails if the classifier is weakened:

- positive: protected branch with two contexts and two required reviews -> `ENFORCED`, contexts
  read;
- status checks declared as `checks[]` objects are read as well as `contexts[]`;
- negative: measured absence -> `VACUOUS` (**this is the live state**);
- protection present but carrying only `enforce_admins`/`restrictions` -> still `VACUOUS` (those
  gate a push, not a merge);
- an `evaluate`-mode ruleset is not a control;
- an active ruleset whose rules are `deletion` only is not a control;
- an active ruleset carrying `required_status_checks` **is** a control;
- unreadable evidence (unknown protection, `null` rulesets) -> `UNKNOWN`, never `ENFORCED`;
- contradictory evidence ("present" with no payload) -> `UNKNOWN`;
- an unrecognised `protection_state` raises rather than guessing;
- CLI round-trip, malformed-input rejection, and `--measure` refusing without a credential.

### 5.2 Live negative controls (real files mutated, then restored byte-identically)

Wiring, on `.github/workflows/gov04-platform-preconditions.yml` (baseline sha256
`bbbd87be7ade8b2426af93707e62e61de9494ba46c5ce9a3bdb0f747a4779806`):

| mutation | result |
|---|---|
| executing step replaced with `echo pytest <guards>` | **8 failed, 5 skipped** |
| `scripts/gov04_platform_preconditions.py` dropped from the filters | **2 failed, 11 passed** |
| job-level `continue-on-error: true` added | **2 failed, 11 passed** |
| restored | sha256 identical, **13 passed** |

Classifier, on `scripts/gov04_platform_preconditions.py` (baseline sha256
`96f5a3767e34bf561e39dd9d9b0d37489a8976f4f5894c33e605495c07361e95`):

| mutation | result |
|---|---|
| fail-closed branch disabled (`UNKNOWN` falls through) | **2 failed, 11 passed** — exactly `test_unreadable_evidence_is_unknown_and_never_enforced` and `test_contradictory_evidence_fails_closed` |
| every input counted as a control | **5 failed, 8 passed** |
| restored | sha256 identical, **13 passed** |

### 5.3 Wiring

`tests/test_gov04_platform_preconditions_ci_wiring.py` states six properties over **every**
workflow that *names* a guard as a pytest target, so a second wiring is judged by the same rule.
`pytest tests/` is deliberately **not** counted as wiring: it also reaches the guard, but only a
file-targeted gate re-runs it deterministically. This matters here — the first draft of the guard
counted directory targets and reddened on `provider-routing.yml` and `sg-02-fe-2-v.yml`, which are
pre-existing non-judging surfaces; the correction is recorded rather than worked around.

Controls inside the guard file cover: a mention (`echo pytest ...`) is not an execution; a
directory target is not wiring; job-level `continue-on-error`; step-level `if: false`; a filter
that omits the classifier; a filter that omits the workflow's own file.

### 5.4 Adjacent gates

```
python -m pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py \
                 tests/test_ci_suite_collection_continuation.py \
                 tests/test_m02a_ci_gate_integrity.py tests/architecture -q
-> 343 passed
```

The three generic workflow-scanning suites gain passing nodes by construction from one new
workflow file, so a `+N passed` there is not evidence of coverage.

### 5.5 CP10 admission

`printf '<path>\n' | python scripts/cp10_mutation_boundary_policy.py --judge` accepts every
added path (verified before authoring): `scripts/gov04_platform_preconditions.py`, both guard
files, the workflow, and this record.

### 5.6 Regression: attributed by node identity, not by counts

Two full-suite runs, in the same environment, with `GITHUB_TOKEN`/`GH_TOKEN` absent:

| tree | result |
|---|---|
| `main` `fd0a4fdc` | **20 failed / 4253 passed / 22 skipped / 1 error** in 283.44s |
| branch | **10 failed / 4296 passed / 22 skipped / 1 error** in 293.77s |

Sorted failing/error node sets:

- `main` — 21 nodes, outcomes sha256 `4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916`
- branch — 11 nodes, outcomes sha256 `753e8931de40863d0e2b5b8592368243c4e56d51f5ecb8de9160ebffbfd9ee03`

**Nodes only on the branch: 0.** The 10 nodes only on `main` are exactly the
`tests/test_mission_lifecycle_adapter_contract.py` group, which now passes because this pass
installed `web/arkadia_console/node_modules` — a toolchain change in the measurement environment,
not a source change in the branch.

The passed delta is **not** evidence of coverage, and it decomposes:

| contribution | nodes | how measured |
|---|---|---|
| the two new guard files | **26** | `--collect-only` on the two files |
| nodes the generic workflow-scanner suites gain from one new workflow file | **12** | `--collect-only` over `tests/` grep `gov04-platform-preconditions.yml` |
| environment-dependent nodes that now pass | **10** | node-set difference above |
| branch collection total | **4327** | `pytest tests/ --collect-only` |

**A measurement-artifact correction, recorded rather than hidden.** A first branch run in this
pass reported two *extra* failures, `tests/test_prism_w4_lab_pr_state.py::test_handler_emits_the_keys_the_projection_reads`
and `::test_projection_reads_the_handler_output`, putting a misleading 2-node delta in the branch
column. Cause: an earlier `--measure` invocation in the same shell session exported
`GITHUB_TOKEN`, so `api/lab_routes.pr_state` could authenticate and returned `AVAILABLE` where the
guards' premise is a *no-token* read. The file is **19 passed** with the token removed and
**17 passed, 2 failed** with it present — reproduced both ways. That is the premise PR #683
("enforce the Lab PR-state guard's no-token premise") exists to pin, and it is not attributable to
this change. Two runs are therefore reported: the token-bearing one (13 nodes, 2 branch-only) and
the token-free one (11 nodes, 0 branch-only), and only the token-free comparison carries the
regression claim.

## 6. Limitations — stated, not papered over

- **`main` remains unprotected and this change does not change that.** Enabling branch protection,
  required checks, required reviews, or a merge queue is a provider/configuration decision
  reserved to the sovereign. This record measures the state; it does not propose to alter it
  silently, and the classifier makes the state legible rather than fixing it.
- **The gate executes the guards, not a credentialed read.** The Actions `GITHUB_TOKEN` cannot
  read `branches/{branch}/protection` without administration permission, so measuring in CI would
  report `UNKNOWN` for reasons of token scope rather than platform state — the exact conflation
  the verdict split exists to prevent. The live measurement is recorded here with its revision and
  its command, and is re-derivable by anyone holding a read credential.
- **A `VACUOUS` verdict is not a finding against the repository.** It is a true statement about
  the platform at `fd0a4fdc`. It becomes a repository concern only if a governance record
  continues to describe those clauses as satisfied safeguards without recording the measurement.
- **The evidence binds to `fd0a4fdc`.** If `main` moves, the measurement is stale until re-run;
  the verdict is a property of a revision, not of the repository in perpetuity.

## 7. Next authorized action

**State.** `main` is `fd0a4fdc`, green on all seven check-runs, and deployed sha-identically.
All 21 live failing/error nodes are owned by five open PRs or reserved to the sovereign. The one
new verified gap this cycle — GOV-04 condition 2's vacuity and the absence of any surface that
measured it — is closed by this branch.

**Evidence.** Sections 1–6 above; fingerprints reproducible with the commands as written.

**Blocker.** Review and merge of 47 open PRs, 46 of them drafts. That is a human-only action
under GOV-03/GOV-04, and it is not a gap an agent can close by writing code.

**Authorized action now.** Keep this branch's PR a draft; update it with any review findings; do
not merge it.

**Forbidden.** Merging any PR; pushing to `main`; enabling or altering branch protection,
rulesets, required checks, or reviews; deploying; claiming production acceptance.

**Completion condition.** The PR is human-reviewed and human-merged; or the sovereign decides
the measurement belongs elsewhere and this branch is closed unmerged.
