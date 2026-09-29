# M02A follow-on — CP10 range evaluation + boundary self-coverage

**Gate:** GATE-10 (Governed Execution) · M02A follow-on
**Supersedes rationale in:** `docs/control-plane/evidence/m02a-ci-gate-integrity/EVIDENCE.md`
**Branch:** `gate10/cp10-range-evaluation`
**Base:** `main`

## Defect 1 — the boundary judged only the tip commit

The M02A step ran `git diff --name-only HEAD^ HEAD`. On a pull-request run the
checkout is the head commit, so that range is the PR's **last commit only**. Any
path introduced in an earlier PR commit shows no change there and can never fail.

This is not theoretical. PR #110 (`feat/opportunity-radar-capture-mvp`) added
`opportunity_radar/SAPZ_CAPTURE_STATE.md`, which no allowlist surface admitted.
The gate reddened on the merge (run 36514924096, job 109234968163) and then went
green on the next merge **without the surface being admitted** — the offender was
masked, not resolved. The allowlist gap was closed separately in PR #111; this
change closes the range defect that would mask any future earlier-commit offender.

The same blind spot applied to the constitutional `forbid` stage: a
`SolSpireExperienceV2/V3` implementation added in an earlier PR commit and
followed by any unrelated commit was diffed as "no change".

## Repair

- `scripts/cp10_mutation_boundary_policy.py` gains `resolve_range_endpoint()` —
  a tested, single source of truth for the guarded range:
  `pull_request.base.sha` → `push.before` → `HEAD^` (fallback) → **undeterminable**.
  An all-zero `before` (branch-creation push) falls back to `HEAD^`.
  When no range can be determined the function returns `None` and the caller
  **fails** — it does not silently pass.
- The workflow diffs `"$base" HEAD` for the allowlist scan, the V2 forbid scan,
  and the workflow-automation scan, and fetches with `fetch-depth: 0` (was `2`,
  which only reached `HEAD^`).
- The workflow trigger `paths` now include the boundary's own contract surfaces
  (`scripts/cp10_mutation_boundary_policy.py`, `tests/test_m02a_ci_gate_integrity.py`)
  so the gate is judged by the policy it rewrites instead of being self-exempt.

## Runtime evidence — full CI step, real git objects

The **verbatim** workflow step was executed against a purpose-built repository
(offender added in commit 1, unrelated legitimate commit 2) with
`GITHUB_EVENT_PATH` carrying `pull_request.base.sha`. The step body was extracted
from the workflow YAML, so the assertion surface is the shipped code, not a
re-implementation.

```
SCENARIO 1 - masked offender (multi-commit PR)
  NEW (base..HEAD)         exit=1  "Unexpected path outside legitimate repository surfaces: secret-backdoor/bin"
  OLD (HEAD^ HEAD)         exit=0  "Mutation boundary PASS"
  -> NEW catches what OLD masked.

SCENARIO 2 - legitimate multi-commit PR (web/, api/, docs/)
  NEW (base..HEAD)         exit=0  PASS
  -> no false positive on ordinary multi-commit product work.

SCENARIO 3 - SolSpireExperienceV3 added in an EARLIER PR commit, unrelated commit after
  NEW (base..HEAD)         exit=1
  -> the constitutional forbid stage also sees earlier-commit offenders.
```

## Tests

```
python -m pytest -q tests/test_m02a_ci_gate_integrity.py   -> 44 passed   (baseline 32)
python -m pytest -q tests/architecture                      -> 11 passed
python -m py_compile api/main.py                            -> OK (2519 lines, under budget)
```

Baseline vs changed full suite: **identical failing set** (47 failed / 12 skipped
/ 2 collection errors), `+12 passed`. No regression attributable to this change.

## Remaining uncertainty

- `fetch-depth: 0` clones the full history on a large repository. Correctness of
  the range is chosen over checkout cost; if clone time becomes material the range
  could be bounded by the PR commit count instead.
- `resolve_range_endpoint` is exercised against constructed repos; the CI event
  payload shape for `push` is asserted by unit test, not by a live push run.

## Authority

No merge by automation. No M03. Human merge required.
