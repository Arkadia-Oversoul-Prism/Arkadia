# gate10 · a pull-request gate that cannot be dispatched has no execution at an arbitrary revision

**Branch:** `gate-hygiene/dispatchable-pr-gates-01`
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T18:23:48+01:00, PR #678)
**Disposition:** IMPLEMENTED, draft. Merge execution is human-only (GOV-03); no
deployment, no production claim, no acceptance.

## 1. The defect

Four workflows declare a `pull_request` trigger with a `paths:` filter, run `pytest`,
and carry **no** `workflow_dispatch`. A path-filtered gate has no execution at a
revision that touches none of its paths, and dispatch is the only trigger that does
not depend on a change landing. So for each of them:

- the gate's evidence binds to whichever revisions happened to select it;
- the gate cannot be re-run against an exact revision when a contract question is
  asked; and
- the *absence* of a run cannot be distinguished from a revision the filter excluded.

Measured over the live corpus (45 workflows, `yaml.safe_load` + `_trigger_block`):

| workflow | runs pytest | `pull_request` | `paths` filter | `workflow_dispatch` |
| --- | --- | --- | --- | --- |
| `alxai-conformance.yml` | yes (`tests/conformance/test_alxai04.py`) | yes | yes | **no** |
| `arkana-signal-conformance.yml` | yes (two jobs) | yes | yes | **no** |
| `openapi-security-metadata.yml` | yes (two steps) | yes | yes | **no** |
| `phase6-persistent-execution.yml` | yes | yes | yes | **no** |

The other **24** workflows that run pytest on `pull_request` are already dispatchable,
so this is an omission against an established convention, not a new policy. Two of the
four are contract gates whose own headers describe the "decoration" risk they exist to
close: `arkana-signal-conformance.yml` states that "a frozen schema that nothing
validates against is not a contract", and `openapi-security-metadata.yml` pins the
authorization metadata of `api/**`.

## 2. The change

### 2.1 The invariant

`tests/test_ci_gate_trigger_coverage.py` already states, generically over every
workflow that runs pytest, that (1) a gate is selected by its own file, (2) `push` and
`pull_request` filters agree, and (3) the architecture suite is selected by the tests it
judges. This pass adds the fourth:

> **4.** A workflow that runs pytest on `pull_request` must also be dispatchable.

The detector is a pure function of the parsed workflow,
`_dispatch_defect(workflow) -> str | None`, so the invariant itself is provable rather
than only asserted against live files.

### 2.2 The repair

One line per workflow — `workflow_dispatch:` added to the `on:` block. No `paths`,
`branches`, job, step, permission or secret changes; `pull_request` and `push`
behaviour is unchanged.

## 3. Proof, bound to this tree

**Pre-repair (live negative control on the real corpus).** The invariant, run against
the unrepared workflows, fails on exactly the four measured names and nothing else:

```
FAILED tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_dispatchable[alxai-conformance.yml]
FAILED tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_dispatchable[arkana-signal-conformance.yml]
FAILED tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_dispatchable[openapi-security-metadata.yml]
FAILED tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_dispatchable[phase6-persistent-execution.yml]
4 failed, 131 passed
```

**Post-repair.** `python -m pytest tests/test_ci_gate_trigger_coverage.py -q`
→ **135 passed**.

**Live negative control on a repared file** (mutation, then byte-identical restore):

```
cp .github/workflows/openapi-security-metadata.yml /tmp/keep.yml   # sha256 c46c1431…
<delete the `  workflow_dispatch:` line>
1 failed, 134 passed        # exactly test_pr_pytest_workflow_is_dispatchable[openapi-security-metadata.yml]
cp /tmp/keep.yml back      # sha256 c46c1431… (identical)
135 passed
```

**Detector controls** (in the same file, so the invariant cannot be disarmed by editing
the detector):

- `test_dispatch_defect_flags_a_gate_that_cannot_be_run_on_demand` — a synthetic
  pull-request pytest gate without dispatch is reported.
- `test_dispatch_defect_stays_silent_outside_its_domain` — three positive controls:
  the same gate **with** dispatch, a workflow that runs no pytest (a pipeline), and a
  workflow with no `pull_request` trigger are all silent.
- `test_trigger_block_reads_the_yaml_boolean_on_key` — PyYAML parses the bare `on` key
  as boolean `True`; a detector reading only the string key would see no trigger at all
  and pass every live workflow.
- `test_the_pytest_workflow_domain_is_not_empty` — a domain that resolved to nothing
  would make every parametrised invariant vacuously green.

**Parsed trigger blocks after repair:**

```
alxai-conformance.yml            -> ['pull_request', 'push', 'workflow_dispatch']
arkana-signal-conformance.yml    -> ['pull_request', 'push', 'workflow_dispatch']
openapi-security-metadata.yml    -> ['pull_request', 'push', 'workflow_dispatch']
phase6-persistent-execution.yml  -> ['pull_request', 'push', 'workflow_dispatch']
```

**The gate that executes the guard judges this change.** `ci-gate-trigger-coverage.yml`
selects `tests/test_ci_gate_trigger_coverage.py` **and** `.github/workflows/**`, so a
commit that edits either the guard or these workflows runs the guard — the repair is
selected by the surface it edits.

```
python -m pytest tests/test_ci_gate_trigger_coverage.py \
    tests/test_ci_gate_trigger_coverage_ci_wiring.py \
    tests/test_gate_filter_selection.py -q
193 passed
```

**No collateral regression in the workflow-scanning suites:**

```
python -m pytest tests/test_workflow_injection_boundary.py \
    tests/test_ci_suite_collection_continuation.py \
    tests/test_m02a_ci_gate_integrity.py \
    tests/test_gate_filter_selection.py tests/architecture -q
289 passed
```

**CP10 mutation boundary.** Every changed path is admitted by
`scripts/cp10_mutation_boundary_policy.py --judge` (the four workflows, the guard, and
this record).

**Full-suite node comparison (same machine, same interpreter).** The load-bearing
invariant is the sorted `FAILED`/`ERROR` **node set**, not the totals.

```
branch (this tree) : 21 failed, 4268 passed, 38 skipped, 1 error   -> 22 nodes
                     sha256 828d330f6d73ae7c1ed39bfbf4a3498eba040a1090ab4ce3f57ed720bb673b75
main   (bb19aabd)  : 28 failed, 4228 passed, 35 skipped, 1 error   -> 29 nodes
                     sha256 92206d03ae744926bc2bbd34d7b6d91529523cc4677fd8e95b43b5e1c24914e3

comm -13 (only on branch) : 0
comm -23 (only on main)   : 7
```

**Zero** failing/error nodes appear only on the branch. The 7 nodes that appear only on
`main` are environment, not tree: the `main` run preceded `pip install pytest-asyncio`
in this sandbox, so five `test_arkana_signal_schema_*` nodes failed with "async def
functions are not natively supported" rather than judging the producer, and two further
nodes (`test_authority_api_enterprise_boundary`, the live-provider
`test_natlas_developer_lab`) are environment/network dependent. The remaining 22 nodes
are pre-existing debt already carried by open PRs or reserved to the sovereign (the
CE-01 `weaver.autonomy` collection error).


## 4. Non-claims

- No merge, no deployment, no production observation, no acceptance.
- This is a repository-source claim about *dispatchability*, not evidence that any of
  the four gates has been dispatched or is green at any revision.
- `arkadia-console-android.yml` is also non-dispatchable but runs no pytest (a Gradle
  APK build), so it is outside this invariant's domain and was deliberately left
  unchanged rather than widened into scope.
- The four gates' own subject matter (ARK-01 schema conformance, OpenAPI security
  metadata, Phase 6 persistence, AL-XAI-04 conformance) was not re-examined.

## 5. Next permitted action

Human review of the draft PR. If the invariant is accepted, the follow-on question it
raises is whether *every* path-filtered workflow should be dispatchable (including
build pipelines such as `arkadia-console-android.yml`); that is a policy decision, not
a defect repair, and is recorded here rather than implemented.
