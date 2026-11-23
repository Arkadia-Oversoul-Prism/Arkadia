# Runtime revision identity — a gate on every `main` push

**Workstream:** `runtime-revision-identity-gate-01`
**Observed at:** `main` `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-23)
**Authority:** read-only. No merge, no deployment, no acceptance. Draft PR only.

---

## 1. The gap, measured

The canonical runtime is Render (`arkadia-qzu4.onrender.com`, ADR-016) and it reports
the revision it is running:

```
GET /api/version
{"schema":"arkadia.version/v1", ..., "source_revision":"bb19aabda34d59594615b0279a45e9cbd3d8204d",
 "revision_source":"RENDER_GIT_COMMIT", "revision_conflict":false, ...}
```

That single field is the only direct evidence binding a deployment to a source revision.
Five workflows mention `/api/version`, and **none of them runs on every push to `main`**:

| workflow | when it runs | exact-SHA assertion |
|---|---|---|
| `canonical-render-runtime-probe.yml` | push to `main` touching `api/**`, `web/arkadia_console/**`, `web/console/**`, `Dockerfile`, `architecture/runtime_manifest.yaml`, or itself | yes (`production_runtime_probe.py` exits 3) |
| `canonical-render-acceptance.yml` | push to `main` touching **itself only** | yes (inline poll) |
| `codex-cold-warm-acceptance-probe.yml` | push to `main` touching **itself only** | yes (inline poll) |
| `canonical-render-browser-smoke.yml` | push to `main` touching `web/**`, `api/frontend_routes.py`, `Dockerfile`, or itself | no |
| `authenticated-canonical-render-acceptance.yml` | `workflow_dispatch` only | yes (needs Firebase inputs) |

So a commit that lands on `main` touching, for example, `solspire/**`, `kernel/**`,
`lab/**` or `tests/**` deploys a new revision that **no workflow identifies**. The link
`main SHA -> deployment SHA` is then unobserved, and an unobserved link is
indistinguishable from a broken one.

Measured: `grep -rln version_reconciliation .github/workflows/` returned **nothing**
before this change, so the dedicated oracle (`scripts/version_reconciliation.py`, with
`MATCH`/`MISMATCH`/`UNKNOWN`/`BLOCKED`/`CONFLICT` and per-verdict exit codes) was
executed by no workflow at all.

## 2. What changed

| file | change |
|---|---|
| `scripts/version_reconciliation.py` | extracted `classify_evidence()`; added `await_revision()` and `--wait`/`--interval` |
| `tests/test_version_reconciliation.py` | 4 new tests (convergence, never-lands negative control, single-shot, conflict) |
| `.github/workflows/runtime-revision-identity.yml` | new gate: `push` to `main` **unfiltered**, PR validates shape only, dispatch |
| `tests/test_runtime_revision_identity_ci_wiring.py` | new wiring judge over the real workflow file, with one negative control per defect form |

### 2.1 The wait is bounded and cannot manufacture a match

A provider reports the **previous** revision until its build finishes, so a single read
classifies a healthy rollout as `MISMATCH`. `await_revision()` re-reads until the
deadline; the **final reading decides**, and `--wait 0` still performs exactly one read.

The negative control is load-bearing: a loop that returned its first reading, or that
treated "no answer yet" as success, would convert genuine drift into a pass — the exact
direction the oracle exists to catch.

```python
def test_await_revision_negative_control_a_deploy_that_never_lands_stays_mismatch():
    ...
    assert verdict == MISMATCH
    assert attempts > 1, "the wait must actually re-read before giving up"
```

### 2.2 The gate cannot probe production from a pull request

A PR is not deployed, so a probe from one measures a different revision and reports a
false drift. The probe job carries `if: github.event_name != 'pull_request'`; the PR job
runs the guard and its wiring judge instead.
`tests/test_runtime_revision_identity_ci_wiring.py` asserts this over the real file, with
a negative control that re-guards the job as `github.event_name == 'push'` and requires
the detector to report it.

### 2.3 The wait timeout is 60 s because the instance sleeps — measured

```
$ curl -s -o /dev/null -w "HTTP %{http_code} time=%{time_total}s\n" \
    --max-time 90 https://arkadia-qzu4.onrender.com/api/version
HTTP 200 time=35.350401s
```

The same deployment, read with the script's 15 s default, is reported as unreachable:

```
$ python scripts/version_reconciliation.py --base-url https://arkadia-qzu4.onrender.com \
    --expected bb19aabd...
verdict:          BLOCKED
EXIT=3
$ python scripts/version_reconciliation.py --base-url https://arkadia-qzu4.onrender.com \
    --expected bb19aabd... --timeout 60
reported revision: bb19aabd...
verdict:          MATCH
EXIT=0
```

A 15 s default would therefore ring on a *sleeping but healthy* instance — the same
false-failure class the Gate-2 alias observation had to repair. The gate passes
`--timeout 60`.

## 3. Verification actually run

| command | result |
|---|---|
| `python -m pytest -q tests/test_version_reconciliation.py tests/test_runtime_revision_identity_ci_wiring.py` | **57 passed** |
| `python -m pytest -q tests/test_ci_gate_trigger_coverage.py tests/test_ci_verdict_step_integrity.py tests/test_ci_suite_collection_continuation.py tests/test_workflow_injection_boundary.py tests/test_m02a_ci_gate_integrity.py tests/test_gate_filter_selection.py tests/architecture` | **424 passed** |
| `python -m pytest -q tests/architecture` | **11 passed** |
| `printf '<each new path>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS` (exit 0) |
| live reconciliation at `bb19aabd` with `--timeout 60` | `MATCH`, exit 0 |

The generic workflow judges are the ones that would redden a malformed gate
(`test_ci_gate_trigger_coverage` self-selection and filter symmetry,
`test_ci_verdict_step_integrity` masked verdicts, `test_ci_suite_collection_continuation`
aborting broad-suite steps, `test_workflow_injection_boundary` untrusted interpolation).
All pass with the new file present.

## 4. What this does not claim

- **A `MATCH` is not deployment acceptance.** It is necessary evidence that the runtime
  corresponds to the source revision; acceptance remains a human act, and the script
  prints that note on every run.
- **This does not close the Gate-2 boundary.** `main -> deployment identity` in
  `scripts/gate2_production_observation.py` still reads the GitHub deployments API, which
  publishes no Production record for Render. That harness is owned by PR #687 and PR #681;
  a third change to the same file would be a guaranteed conflict, so this gate is a
  separate surface rather than an edit to theirs.
- **No production behaviour changes.** The workflow issues one `GET /api/version` per
  read. No credential, no mutation, no deploy, no routing change.
- **The wait was not exercised against a real rollout.** It is proven by unit tests with
  an injected clock and fetch; a live `MISMATCH -> MATCH` transition was not staged.
- **`push` is deliberately unfiltered**, so every `main` commit runs the gate. If Render
  stops deploying a class of commits, the gate goes red — which is the drift it exists to
  report, not a defect in the gate. This was checked: `main` `bb19aabd` is a *test-only*
  commit and production reports exactly `bb19aabd`, so Render does deploy
  non-build-input commits.
- **Three workflows already carry inline exact-SHA polling** (`canonical-render-acceptance.yml`,
  `codex-cold-warm-acceptance-probe.yml`, and the probe script). This gate adds no fourth
  copy: it calls the tested oracle, which is where the wait belongs.

## 5. Next permitted action

Human review of the draft PR. Merge execution is human-only under GOV-03; nothing here
deploys, accepts, or changes production. This gate touches neither
`scripts/gate2_production_observation.py` nor its test, so it is composition-neutral with
PR #687 and PR #681.
