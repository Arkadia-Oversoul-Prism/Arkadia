# ARK-OPS-CONTINUOUS-001 — cycle 21: production parity holds, and the queue's red signal is one external provider

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`
**Measured:** 2026-11-25, this workspace, 12:06-12:30 UTC
**Authority:** read-only against GitHub and production. No merge, no push to `main`, no deployment,
no acceptance. No new pull request was opened: the queue already carries 57, and section 0.1
forbids adding one to appear productive.

## 1. What this cycle verified

Cycle 20 answered *"does the queue compose?"* and left a three-item human handoff. It did not
answer *"is the deployed system the repository's revision?"* nor *"why are 22 of the open pull
requests red?"* — and the second question decides whether a human triaging 57 PRs is looking at
repository debt or at something else. Both are measured here.

### 1.1 Source to runtime consistency — VERIFIED

```
GET https://arkadia-qzu4.onrender.com/api/version
  source_revision   fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source   RENDER_GIT_COMMIT
  revision_conflict false
```

`/health` returns `200`. `/` with a browser `Accept` header returns `200`, 1256 bytes (the SPA
shell).

The deployed revision equals `main`. Per ADR-016 and the runtime probe's own `verification_note`,
this is **necessary** evidence of source-to-runtime consistency and is **not** proof that the
application behaves correctly, nor production acceptance. Labelled `VERIFIED` for the
*revision-identity* boundary only; application acceptance stays `NOT CLAIMED`.

### 1.2 Queue inventory — 57 open, 0 reviewed, 0 merged in about 19 h

- 57 open pull requests, all authored by `Arkadia-Oversoul-Prism`.
- **56 drafts, 1 ready** (`#724`, the GOV-04 activation record).
- `reviewDecision` on the sample inspected: `none`. No merge has landed since
  `2026-11-24T17:30:03Z` (`#722`), about 19 hours at measurement time.
- Every one of the 57 heads has at least one check-run, so the queue is not silently untested.

### 1.3 Why 22 of 57 are red — 21 are one workflow, 1 is a named dependency

Sweeping `commits/<head>/check-runs` for all 57 heads:

| Failing check | PRs | Owning workflow |
| --- | --- | --- |
| `beta-beta-01-english`, `beta-beta-02-hausa`, `bundle-beta-evidence`, `native-arkadia-golden-workflow` | **21** | `.github/workflows/n-atlas-external-beta.yml` |
| `Build MIE / Sonata debug APK` | **1** (`#716`) | `.github/workflows/mie-android-build.yml` |

The 21 are not 21 independent defects. They are **four check names from a single workflow**, which
fans out as `beta` then `{native-golden, bundle}`. A PR is red there when either the matrix job or
the golden job fails.

**The workflow runs on every pull request to `main` and has no `paths:` filter:**

```yaml
on:
  push:
    branches: [feat/n-atlas-developer-lab]
  pull_request:
    branches: [main]        # no paths: — every PR to main
  workflow_dispatch:
```

It exercises a **live third-party Hugging Face Space**
(`https://koladeodunope-ednai-natlas-runtime.hf.space`). So its outcome is a function of an
external provider's availability, not of the pull request's diff.

**Cause verified on a sampled run, not inferred.** PR `#709` head `f5f311fc`, run `45296370125`,
job `beta-beta-02-hausa`:

```json
"status": "FAILED",
"errors": []
```
```
RUN_FAILED: external runtime did not return usable inference
```

`status: FAILED` with an **empty** collected-error list and a `RUN_FAILED` reason of *"external
runtime did not return usable inference"* is the signature already recorded for this provider: the
Space emitted no usable data rather than the request being rejected. It is evidence about the
provider. It is not evidence about `#709`'s diff, which is a docs change
(`docs/deployment-guide-truth-01`).

### 1.4 The one attributable red — `#716` depends on `#719`

`#716` (`gate-hygiene/root-doc-deployment-host-currency-01`) fails `Build MIE / Sonata debug APK`.
The open PR `#719` (`gate-hygiene/mie-android-unit-test-classpath-01`) exists to fix exactly that
gate ("give the JVM unit tests a real org.json so the Sonata APK gate can pass"). This is a
**merge-order dependency inside the queue**, of the same class as the recorded `#329`/`#342`
strict-xfail pair: `#716` cannot go green until `#719` lands, and neither is wrong alone.

## 2. What this does and does not establish

**Established:** production serves `main` `fd0a4fdc` with no revision conflict; the queue is 57
open / 1 ready / 0 merged in about 19 h; 21 of the 22 red PRs fail on one external-provider
workflow that has no `paths:` filter; the 22nd has a named in-queue dependency.

**Not established:** merge eligibility, M1-M13, review sufficiency, or acceptance. A green check is
not eligibility, and a red check here is not a defect in the PR.

**Not measured:** whether the Space is currently up. A single sampled run is evidence about that
run's minute, not a current availability claim — and the provider's admission rule is recorded as
`NOT TESTED` for this class.

## 3. Proposed, not executed — reserved for human authority

Two changes would convert the queue's red signal from provider noise into repository signal. Both
change **what gates `main`**, which is an approval-enforcement / provider-configuration decision
reserved to the sovereign, so they are recorded here and **not implemented**:

1. **Scope `n-atlas-external-beta.yml` with a `paths:` filter** naming every input it actually
   exercises — `tests/test_natlas_developer_lab.py`, `lab/engineering_lab/**`,
   `api/lab_routes.py`, `deploy/n-atlas-server/**`, `requirements.txt`, and the workflow itself.
   This is the same rule the repository already applies to every other gate: *a workflow's
   `paths:` filter must name every input its guards read*. Here the inverse holds — it currently
   runs when it reads nothing from the diff.
2. **Report provider unavailability as `BLOCKED`, not as a failed check.** The vocabulary and the
   forensics precedent (`ENVIRONMENTAL` vs `ATTRIBUTABLE`) already exist in this repository; the
   external-beta job does not use it.

Neither is a repair an agent may make unilaterally: (1) narrows when a check that gates `main`
runs, and (2) changes a gate's verdict semantics. Discovery does not authorize execution.

## 4. Next action

1. **Human:** the three textual conflicts and two semantic composition defects handed off by cycle
   20 remain open and unchanged — `main` has not moved since `fd0a4fdc`, so that handoff is
   **current**, not stale.
2. **Human:** decide the two proposals in section 3 (gate scoping; provider-unavailability
   reporting).
3. **Human:** merge order for the `#716` / `#719` dependency.
4. **Weaver:** the standing blocker is **human merge authority**, not repository work. The queue is
   composable in 53 of 56 cases (cycle 20) and its red signal is dominated by one external
   provider. Further engineering will not advance the queue; only merges will.

## 5. Negative control — the same commit, the same workflow, opposite outcomes

Recorded after the cycle-21 evidence commit (`109bae7b`) had itself been pushed and its checks
had reported. On that **docs-only** tree, in a **single run of a single workflow**:

```
beta-beta-01-english    success
beta-beta-02-hausa      failure
native-arkadia-golden-workflow  skipped   (needs: beta == success)
bundle-beta-evidence    in_progress
Full-history secret scan        success
provider-forensics              success
```

This is the control the earlier sampled run could not supply. A documentation-only diff cannot make
one matrix leg of a live-provider job pass and its sibling fail: both legs read the same tree, the
same prompt harness, and the same workflow, and differ only in `language` and `prompt`. The
divergence therefore lies in the provider's response, not in the commit.

It also rules out the two remaining innocent explanations for the 21 red PRs:

- **not branch content** — the tree here changes only `docs/control-plane/evidence/**`;
- **not a broken workflow definition** — the same definition produced `success` on one leg.

The `Full-history secret scan` and `provider-forensics` checks passing on the same commit show the
repository-facing jobs are unaffected.

## 6. Local verification of this change

```
printf 'docs/control-plane/evidence/ark-ops-continuous-001-cycle-21/EVIDENCE.md\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge
-> Mutation boundary PASS   (exit 0)

python -m pytest tests/test_m02a_ci_gate_integrity.py -q
-> 76 passed
```

The new evidence path is admitted by the existing `docs/…` rule; no allowlist edit was required.
