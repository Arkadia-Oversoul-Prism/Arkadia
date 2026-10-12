# Opportunity Radar — project pipeline strip (per-status counts)

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: reconcile the archived Prism **per-status pipeline strip** into
the active console's `ProjectOpportunityRadar` — the board read already computes
`byStatus` (`opportunityRadarContract.ts::summarize`) but no surface rendered it.
Authority: human retains merge, production deployment, and acceptance. Nothing
here claims any of the three.

This is the successor slice to `prism-opportunity-entry-flow-01` (PR #430, which
added the create/edit entry flow). It reuses the same module and the same
executed-Node probe; it adds no transport, no route, and no authority.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR opened this pass).
- `origin/main` at the start of this pass: `49809f45274f2f81b24e01fefdfb3009e8717495`
  (`Merge pull request #490 ... gate10/natlas-selfhost-wiring-execution-01`).
- PR #430 (the predecessor slice) was **closed unmerged** on the live queue, so
  this slice does not reopen it — a new bounded PR branches from live `main`,
  per the lane rule.

## 1. The reconciliation gap (measured, not assumed)

The archived product — `archive/frontend/arkadia-prism/web/public_prism/src/components/solspire/ProjectOpportunityRadar.tsx`
— rendered a **column per status** with a count, computed from its own `columns`
array via `columns.reduce`. The active console computes the same counts
(`summarize` → `byStatus`, keyed on the backend's `BUYER_RECON_STATUSES`) but the
landed surface rendered only a per-entry list and a single actionable tally. The
per-status structure was dead data.

## 2. The display defect it exposes (MEASURED DEFECT 3, pinned not repaired)

`solspire/buyer_recon.py::update_entry` validates `status.upper()` against
`STATUSES` and then persists the value it was sent (the `patch.items()` loop reads
`patch`, never the reassigned local — see
`tests/test_prism_opportunity_entry_flow.py::test_update_does_not_normalize_a_lowercase_status`).
A row can therefore carry a status **outside** the declared vocabulary.

`byStatus` is keyed on the declared tuple, so such an entry has no column. A naive
per-status strip would therefore **silently under-count** the board — the counts
would not sum to `total`. The fix is display-side and does not touch the backend:

- `summarize` now counts such entries in `offVocabulary` instead of dropping them,
  so `sum(byStatus) + offVocabulary === total` always reconciles (test:
  `test_strip_states_the_off_vocabulary_stray_instead_of_dropping_it`), with a
  negative control (`test_negative_control_the_stray_would_be_dropped_without_the_counter`)
  proving the counter is load-bearing.

Repairing defect 3 itself is a backend change outside this lane's grant
(`SHARED-CONTRACTS` §1/§7.1); it stays pinned.

## 3. What changed

| File | Change |
|---|---|
| `web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts` | `OpportunitySummary.offVocabulary`; the stray counter in `summarize`; `statusColumns()` (ordered columns derived from `BUYER_RECON_STATUSES`) |
| `web/arkadia_console/src/components/opportunities/ProjectOpportunityRadar.tsx` | renders the pipeline strip (`data-testid="opportunity-pipeline"`), one cell per declared status; renders the off-vocabulary note when `offVocabulary > 0` |
| `tests/test_prism_opportunity_entry_flow.py` | +7 tests; Node probe extended with `statusColumns`/`summarize` cases |

Terminal outcomes `EXECUTED`/`SETTLED` are **counted** (the archived strip showed
every column) but remain **unsendable** — the write ceiling `SETTABLE_STATUSES` is
untouched, so a terminal status still cannot reach the wire from the form.

## 4. Proof (run in this environment)

- `python -m pytest tests/test_prism_opportunity_entry_flow.py -q -rEf`
  → **55 passed** (was 48; +7 this pass).
- `python -m pytest -q $(python scripts/console_contract_domain.py)` (the derived
  CI domain the gate executes, 21 files) → **408 passed**.
- `python -m pytest tests/test_prism_opportunity_radar_module.py tests/test_prism_console_ci_wiring.py -q -rEf`
  → **55 passed** (adjacent Lane 2 guards unchanged).
- `python -m pytest tests/architecture -q` → **11 passed**.
- Frontend: `corepack pnpm install --frozen-lockfile && corepack pnpm build` →
  `✓ built` (the first build **caught** an unused `NO_EVIDENCE` import and was
  fixed; `noUnusedLocals` is on, so the build is load-bearing here).
- `api/main.py` untouched (this slice is frontend + test only); no `dist/` staged
  (`web/arkadia_console/.gitignore` covers it).

Failing/error node baseline is unchanged and out of scope; no new failure was
introduced (the touched files' own suites are green above).

## 5. Remaining uncertainty / not claimed

- No production deployment, no merge, no acceptance — human authority.
- MEASURED DEFECT 3 (backend status normalization on `update_entry`) is recorded
  and **not** repaired; it is a separate bounded change.
- Backend arity and one-board-per-subject defects named in the lane charter were
  already repaired and merged in earlier passes; nothing here duplicates them.
