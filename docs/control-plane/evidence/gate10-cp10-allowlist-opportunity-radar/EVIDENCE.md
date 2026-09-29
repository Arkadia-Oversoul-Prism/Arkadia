# GATE-10 · CP10 mutation-boundary allowlist — `opportunity_radar/` admission

Continuation of `gate10/cp10-allowlist-root-docs` (PR #105, merged). That PR restored `main`'s CP10
gate for root docs, `knowledge/`, `spiral_grove/` and `conftest.py`. This pass closes the one
still-unresolved omission and records *why* it was not already closed.

## 1. Objective

Admit `opportunity_radar/` — a tracked top-level surface merged on `main` — to the CP10
mutation-boundary allowlist, so the gate stops depending on merge topology to stay green.

## 2. What was actually wrong (provenance)

`opportunity_radar/SAPZ_CAPTURE_STATE.md` on `origin/main` is tracked (`git ls-files`) but rejected
by the policy allowlist. The tracked tree has **75 top-level entries / 1398 paths**; this is the
**only** tracked surface the allowlist omits.

The omission was introduced by `ae740b8` ("feat(opportunity-radar): persist SAPZ capture state"),
merged via **PR #110** (`e345bfc`, merged 2026-09-29T02:56:34Z).

| Evidence | Value |
| --- | --- |
| PR | #110 (`feat(opportunity-radar): persist SAPZ capture and expose R…`) |
| Merge commit | `e345bfc` |
| Head commit | `1b5eac5` |
| `validate` check-run | **failure** (`109234968163`) |
| Run / job | `36514924096` / `109234968163` |
| `browser` check-run | success (`109234968034`) |
| `weaver_evolution` | skipped (`109235967935`) |

Failure annotation: `Unexpected path outside legitimate repository surfaces:` →
`opportunity_radar/SAPZ_CAPTURE_STATE.md`, step exit 1.

**Why the next merge was green anyway.** The `CP10 mutation boundary` step diffs the tip commit
against its *first parent only* (`git diff --name-only HEAD^ HEAD`). On a merge commit whose first
parent already contains the path, the diff reports no change, so the offender can never reappear to
fail. #110 went red; the following merge (`e5e2e42`) went green without the surface ever being
admitted. That is **masking, not resolution**: the next non-merge commit touching `opportunity_radar/`
can redden `main` again.

**Corollary finding (recorded).** `docs/phase1/CONTINUATION_LEDGER.md` is itself rejected by the
allowlist on the current tree and is *not* within the tracked-surface guard's scope today. It is
reachable only through the `[^/]+[.]md$` rule's tree topology and the tip-parent diff. Same latent
hazard class; logged below as the next bounded task rather than fixed here.

## 3. Change

| File | Change |
| --- | --- |
| `scripts/cp10_mutation_boundary_policy.py` | `opportunity_radar/` added to `LEGIT`; stale inventory counts corrected (74/1393 → 75/1398) |
| `.github/workflows/sg-02-fe-2-v.yml` | mirrored `legit` literal updated to stay byte-equivalent |
| `tests/test_m02a_ci_gate_integrity.py` | 3 new regression/guard tests; drift corpus extended |

No change to `api/main.py` (boot code untouched). No new mutation path, no new authorization path,
no new infrastructure — one enumeration entry in the existing policy and its existing mirror.

## 4. Verification

```
python -m pytest tests/test_m02a_ci_gate_integrity.py -q   -> 32 passed
python -m pytest tests/architecture -q                     -> 11 passed
```

New guards:

- `test_opportunity_radar_surface_is_legitimate` — the exact path that failed the #110 merge.
- `test_shipped_opportunity_radar_changeset_passes_policy` — the full #110 file set.
- `test_allowlist_admits_every_tracked_top_level_prefix` — generalizes to *any* future omitted
  prefix, so this defect class cannot silently recur. `vault/` is excluded because it is
  *deliberately* outside the boundary (asserted by `test_personal_vault_surface_is_still_rejected`).

Policy/workflow equivalence was checked exhaustively rather than on a sample: **0 drift across all
1398 tracked paths**, with adversarial paths (`secret-backdoor/bin/x`, `vault/Ideas/x.md`) rejected by
both and `opportunity_radar/x.md` now admitted by both.

`python -m py_compile scripts/cp10_mutation_boundary_policy.py api/main.py` clean; workflow parses as
YAML.

## 5. Baseline comparison (regression boundary)

| Surface | Before | After |
| --- | --- | --- |
| `tests/test_m02a_ci_gate_integrity.py` | 1 failed, 31 passed | **32 passed** |
| `tests/architecture` | 11 passed | 11 passed |
| Grove contracts | 3 failed, 27 passed | 3 failed, 27 passed |

The Grove 3-failure set
(`test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence`,
`test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication`,
`test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream`) was
reproduced byte-identically on a clean `origin/main` worktree. It is **baseline debt, unattributed
to this change**, and not fixed here (`BASELINE DEBT` rule: do not fix unrelated debt inside an
architectural gate).

## 6. Composability risk (recorded, not resolved)

The gate couples two copies of one policy: the inline `legit`/`forbid` regexes in the workflow and
`scripts/cp10_mutation_boundary_policy.py`. Only a test forces agreement; an edit to one silently
diverges from the other. This pass keeps them equivalent and widens the drift assertion, but the
structural fix — the workflow executing the tested module instead of duplicating its regexes, with
the shell literal surviving only as a mirror assertion — remains the recommended next bounded task.
Deliberately **not** done here: it changes how the gate executes.

## 7. Remaining uncertainty

- The allowlist's completeness is now enforced by `test_allowlist_admits_every_tracked_top_level_prefix`,
  but the *tip-parent diff* itself is unchanged. The next non-merge commit to `continuation_ledger`
  or another late-admitted surface is the next exposure; a truth-table comparison of the two
  execution paths (tip-parent diff vs PR-range diff) is the bounded task that closes the class.
- Baseline failures beyond Grove (full suite) were not re-audited this pass; the prior classification
  in `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/` stands.
- `pnpm build` not run — the change does not touch `web/`.

## 8. Authorization required

Sovereign review and merge only. No consequential external action taken; no merge performed.
