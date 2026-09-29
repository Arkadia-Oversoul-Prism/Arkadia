# WORKSTREAM_STATE — `gate-hygiene` / SH-02e (baseline STALE_ASSERTION rows 1–2)

Reconstructed from live repository evidence, not memory. `main` @
`df7a99a067382401c00de5e7bbaaac0125ba2088` (820 commits; history was deepened since the
`4164573`-era passes).

## Workstream

Repair baseline test failures whose fingerprint is a **stale source-level string assertion**
(`STALE_ASSERTION`) against a removed symbol. Scope is test-only. It does **not** cover
`DRIFT`, `SH-08` governance contradictions, or product-decision nodes.

Classification source of truth:
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
(§11.6 carries this batch's record).

## Baseline fingerprint at `main` @ `df7a99a`

Same interpreter and `PYTHONPATH` as the prior passes:

```
30 failed, 1028 passed, 13 skipped, 2 errors  (108.28s)
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors
```

- architecture: **11/11 passed** (the brief's "10/10" is stale)
- `api/main.py`: **2519 / 2600** lines; `py_compile` clean
- `vite build`: environment-blocked
- pre-existing collection errors: `test_autonomy.py`, `test_render_codex.py`

> **Do not diff this against the brief's `6038989` / `54F / 804P` baseline.** That baseline is
> two deepens old. The current reference is `df7a99a` above.

## This batch (SH-02e)

| row | node | classification | repair |
| --- | --- | --- | --- |
| 1 | `tests/test_agent_run.py` (was `::test_agent_run_writes_and_commits`) | `STALE_ASSERTION` | re-pinned off the removed `weaver.agent.commit_and_push` onto the K0.1 kernel seams; **renamed** to `::test_agent_run_refuses_without_pass_spec` + `::test_agent_run_reaches_terminal_publication_on_the_kernel_seam` |
| 2 | `tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | `STALE_ASSERTION` | removed tagline + dead `button-home-ais-diagnostic` assertion → live headline + `arkadia-home-landing` |

Both verified: **fail on pristine `main`**, **pass after**. Branch
`gate-hygiene/sh02e-agent-run-capability-onboarding-repair` @ `479e8de`, **PR #136**, open,
mergeable, awaiting sovereign merge. CI: secret scan green; CP10 path-filtered (correct —
test-only paths) and verified locally by the mutation-boundary judge instead.

## Delta attribution (the part a future pass must not re-derive wrongly)

- **All 30 live failures are Appendix A rows.** No unexplained regression from this batch.
- **21 Appendix A rows now pass.**
- **8 live failures are absent from Appendix A** — the 4 `test_solspire_r{1,2,3}_*.py` nodes
  (§11.3) and 4 `test_spiral_grove_activity_runtime.py` nodes (§11.2). **Proven pre-existing**:
  they fail identically in a `4164573` worktree (`8 failed, 15 passed in 0.65s`).
  → Appendix A under-counts the baseline set by 8 nodes. **Ledger gap, not a regression.**
  Recorded in §11.6; Appendix A left frozen (`a26af408`-era artefact).

## Open delta — recorded, deliberately NOT fixed

The pre-K0.1 row also asserted `meta['engine_cycle']`. That provenance is **structurally
dropped at the kernel seam**: `weaver.session_kernel.finalize_session` is the only commit path,
never receives `engine_cycle`, and passes `meta={"pass_id": ...}` only. Threading it through
changes what the kernel records for governance → **not test hygiene**. The re-pinned row pins
the invariant (`meta.get("engine_cycle", 5) == 5`), so a legitimate future fix greens it rather
than reddening it.

## Batch ledger (SH-02 series)

| batch | branch / PR | nodes | state |
| --- | --- | --- | --- |
| — | merged #124 / #125 / #127 | SCI-nexus, Solariun consolidation, surface ownership | **merged** |
| 3 | #130 identity spine | identity spine / `ais_profile` | open |
| 4 | #132 future skills | `test_ais_w6_future_skills_challenge.py` | open |
| 5 | #131 spiral grove | `spiral_grove_{chambers,frontend_projection,learning_path_projection}` | open |
| d | `gate-hygiene/sh02d-prism-interior-shell` | `test_prism_interior_shell.py` | **blocked** on ledger-rebase sequencing (see batch-5 WORKSTREAM_STATE) |
| — | #133 | rows 3–8 | open — **not** this batch |
| — | #135 | rows 10–12 | open — **not** this batch |
| e | **#136 (this batch)** | **rows 1–2** | **open, READY FOR SOVEREIGN MERGE** |

No collision: #133 and #135 do not touch rows 1–2.

## Next bounded tasks (proposed, not authorized)

1. Un-rendered version-string assertions noted in batch-5 evidence (candidate SH-02 batch 6).
2. Remaining `STALE_ASSERTION` clusters not owned by open work and not `SH-08` / `DRIFT`.
3. Batch d, once the ledger-rebase sequencing decision is made.

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## CI applicability note (so a future pass does not misread absence as a missing check)

`SG-02-FE.2-V` is **path-filtered** (`web/public_prism/**`, `spiral_grove/**`, `lab/**`,
`api/lab_routes.py`, named test files). PR #136 touches only `tests/test_agent_run.py`,
`tests/test_ais_capability_profile_onboarding.py`, and a docs path → **no `validate` run is
created**, correctly. `security-secret-scan` has an unfiltered `pull_request` trigger and did
run (green).

When querying CI, pass the **full 40-char SHA**; the Actions API silently returns
`total_count: 0` for an abbreviated SHA, which reads as "no runs" when it means "unproven".

## Authority

Human sovereign merge only. Never merge, never push `main`, never force-push.
