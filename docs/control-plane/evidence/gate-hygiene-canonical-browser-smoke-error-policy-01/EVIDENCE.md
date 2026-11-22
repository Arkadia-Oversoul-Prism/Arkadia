# Canonical browser smoke — a 401 is the authentication boundary, not an error

**Workstream:** gate-hygiene
**Base `main`:** `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `gate-hygiene/canonical-browser-smoke-error-policy-01`
**Observed:** 2026-11-22
**Authority:** GOV-03. No merge, deployment, or acceptance is performed or claimed here.

## 1. Defect

`.github/workflows/canonical-render-browser-smoke.yml` drives a real headless
browser against the canonical production origin and decides PASS/FAIL inline:

```js
if (!record.status || record.status >= 400 || record.body_characters === 0
    || errors.length || pageErrors.length || navigationError) report.result = 'FAIL';
```

`errors` collects every console entry of type `error`. The console fires an
anonymous identity probe on every route, and the browser logs the resulting
401 as a console entry:

```
Failed to load resource: the server responded with a status of 401 ()
```

A 401 from an auth-gated endpoint is the **expected** answer for a visitor with
no identity. The console maps it to a first-class state —
`web/arkadia_console/src/lib/useHydration.ts` (`AUTH_REQUIRED` → `auth-required`)
and `App.tsx` renders the sign-in threshold — so the surface is behaving
correctly while the gate records a failure. `errors.length` therefore made the
gate unpassable for an anonymous visit.

### Measured consequence

`gh run list --workflow canonical-render-browser-smoke.yml` at this base:
**13 consecutive failures**, `9ec104b9` (2026-11-06) → `5f40e65c` (2026-11-20),
every `push` to `main` in that window. The same signature is present in the
earliest run of the streak (`42200962696`) and the latest
(`44663630718`), so the cause is stable rather than incidental.

Per-route capture from `44663630718` (7 routes, all `status: 200`):

| route | body characters | console errors | page errors |
|---|---|---|---|
| `/` | 2366 | 2 × `…status of 401 ()` | 0 |
| `/solariun` | 577 | 2 × 401 | 0 |
| `/oracle` | 1165 | 2 × 401 | 0 |
| `/solariun/engineering-lab` | 577 | 2 × 401 | 0 |
| `/operator` | 4211 | 2 × 401 | 0 |
| `/n-atlas-lab` | 443 | 2 × 401 | 0 |
| `/n-atlas-tester` | 443 | 2 × 401 | 0 |

Every route rendered a non-empty body and raised no page error. The gate failed
on the 401s alone.

**Not attributed:** earlier intermittent failures (`f6d165ed`, 2026-11-05) are a
different cause — the readiness step timed out waiting for Render to reach
`GITHUB_SHA` (`42037418422`). They are recorded, not repaired here.

## 2. Repair

The verdict moves out of the heredoc into a testable module so the pass
condition cannot drift again:

- `scripts/canonical_browser_report.py` — `judge_route()` / `judge()` / CLI.
  - a **resource-load** console entry is judged by the status the browser names
    in it: `401` is the authentication boundary and passes; every other status
    fails;
  - any console entry that is *not* the anchored resource-load form is an
    application `console.error` and fails;
  - uncaught page errors, navigation errors, a non-2xx/3xx document, an empty
    body, and a `failed_responses` entry other than 401 all fail;
  - a 401 attributed to a **foreign origin** fails;
  - an empty capture fails, so the gate cannot pass vacuously.
- `.github/workflows/canonical-render-browser-smoke.yml`
  - the Node step now **captures only** (`response` ≥ 400 and `requestfailed`
    are recorded structurally as `failed_responses`, which also names the URL);
  - a new step executes the judge:
    `python3 scripts/canonical_browser_report.py artifacts/…/browser-route-report.json`;
  - the workflow's `push` and `pull_request` filters name the judge and its test,
    because the workflow reads them.

The policy is narrow: `EXPECTED_AUTH_STATUSES == frozenset({401})`. 403 is
deliberately excluded — it means a *known* identity was refused, which an
anonymous visit must never produce.

## 3. Verification

```
python -m pytest tests/test_canonical_browser_report.py -q
28 passed
```

`tests/test_canonical_browser_report.py` carries one control per defect class:

- the observed capture (2 × 401 per route) **passes**;
- the **pre-repair rule is shown to fail that same capture**, so the repair is
  demonstrated against the real shape and not only a synthetic one;
- application console error → FAIL; a console entry that merely *mentions* the
  phrase → FAIL; resource statuses 400/403/404/422/429/500/503 → FAIL; page
  error → FAIL; navigation error → FAIL; empty body → FAIL; document status
  null/404/500 → FAIL; `failed_responses` 500/502/404 → FAIL; foreign-origin
  401 → FAIL; empty capture → FAIL;
- CLI exit codes 0 / 1 / 2 are pinned.

### Live negative controls on the real workflow file

| mutation | result |
|---|---|
| judge step replaced with `echo` | `1 failed, 27 passed` — `test_the_workflow_executes_the_judge` |
| inline pass condition (`errors.length`) restored | `1 failed, 27 passed` — `test_the_workflow_does_not_decide_the_verdict_itself` |

The workflow was restored byte-identically after each control
(`sha256 70cabd5344cc03ef055e3f10225314b1e6da66fca948a2a582d2b835dabccc7e`,
`28 passed`, `yaml.safe_load` OK).

The invocation detector tokenises every `run:` block (block scalars expanded)
and requires `python3`/`python` as the command word with the script as an
argument, so `echo python3 scripts/canonical_browser_report.py` does not satisfy
it — the control above proves exactly that.

## 4. Regression

Failing/error node set compared by identity against a full-suite run of `main`
`034d8879` in this same environment (`-rEf --continue-on-collection-errors`).
Local absolute counts differ from CI because of the installed dependency set;
only node identity is compared. Numbers in §6.

Targeted suites re-run clean on the branch:

```
tests/test_workflow_injection_boundary.py tests/test_ci_gate_trigger_coverage.py
tests/test_ci_suite_collection_continuation.py tests/test_boot_syntax_boundary.py
tests/test_m02a_ci_gate_integrity.py            331 passed
```

CP10 mutation boundary: `PASS` for all three changed/added paths.

## 5. Limitations

- The runtime proof of the repaired gate requires a workflow run. A
  `workflow_dispatch` run on the branch is the evidence that the gate now
  **passes against production**; the local tests prove the policy, not the run.
  Result in §6.
- The repair does not change what the console requests anonymously. Firing an
  identity probe and receiving 401 is how the SPA learns it has no identity; the
  gate, not the client, was wrong.
- `scripts/gate2_browser_observation.py` is a separate, Prism-anchored observer
  and is untouched.
- No assertion here establishes production acceptance.

## 6. Measured results

Full suite, same environment, same command
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`,
`PYTHONPATH=archive/legacy_python`):

| tree | summary | failing/error nodes |
|---|---|---|
| `main` `034d8879` | 87 failed, 3772 passed, 36 skipped, 50 errors | 137 — `sha256 9d9d2c8e790f8c5701fc581347c1a34818f8d43433124cd89a1edbafe47102dc` |
| this branch | 87 failed, 3800 passed, 36 skipped, 50 errors | 137 — same `sha256` |

`comm -3` on the sorted node sets is empty: zero node-set delta. The `+28
passed` is exactly the new test file (28 nodes, measured by running it alone).
Local absolute counts are larger than CI's because this sandbox installs a
different dependency set; only node identity is compared.

The dispatched workflow result is recorded in the PR body.

