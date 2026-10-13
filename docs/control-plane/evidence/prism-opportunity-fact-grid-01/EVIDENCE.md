# Opportunity Radar — captured reconnaissance fact grid

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: reconcile the archived Prism radar's **captured reconnaissance
grid** into the active console's `ProjectOpportunityRadar`. The board read already
delivers ~22 declared facts per entry (`BuyerReconEntryInput`), but the console
rendered only three of them (`buyer_price`, `landed_cost`, `expected_gross_margin`),
so a recorded location, commodity, quantity, supplier, delivery window, payment
terms, capital, or margin was invisible. Authority: human retains merge, production
deployment, and acceptance. Nothing here claims any of the three.

Successor slice to `prism-opportunity-pipeline-strip-01` (same branch/PR, PR #492,
draft). It reuses the same module and the same executed-Node probe; it adds no
transport, no route, no write, and no authority.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, base `main`).
- `origin/main` at the start of this pass:
  `49809f45274f2f81b24e01fefdfb3009e8717495`
  (`Merge pull request #490 ... gate10/natlas-selfhost-wiring-execution-01`).
- Environment: node `v24.21.0`, pnpm `10.26.1`.

## 1. The reconciliation gap (measured, not assumed)

The archived product —
`archive/frontend/arkadia-prism/web/public_prism/src/components/solspire/ProjectOpportunityRadar.tsx`
— rendered the whole captured grid (Location, Commodity, Quantity, Buyer price,
Delivery, Window, Supplier, Landed, …). The active console rendered three
commercial fields and dropped the rest of the declared field set on the floor.
For a reconnaissance board whose entire value is the *recorded facts*, an invisible
fact is a missing capability, not a stylistic choice.

## 2. The change (display-only, no write, no authority)

- `opportunityRadarContract.ts` gains:
  - `EntryFact`, `ENTRY_FACT_FIELDS`, `entryFactLabel(field)`, `entryFacts(entry)`.
  - The field set is **derived** from the contract's own `DESCRIPTIVE_FIELDS` +
    `COMMERCIAL_FIELDS` (which mirror the handler's `BuyerReconEntryInput`), minus
    the fields that already have their own UI (`why_this_prospect`, `notes`) and the
    fields that are not a fact to display (`prospect`, `status`, `evidence_status`,
    `evidence`). Deriving it means the display cannot drift from the contract.
  - Every value passes through the existing `fact()`, so an unverified commercial
    fact reads as the backend's `UNKNOWN` sentinel rather than a blank.
- `ProjectOpportunityRadar.tsx` replaces the three-field `<dl>` with the derived
  grid: `entryFacts(entry).map(...)`, testid `opportunity-entry-facts-{id}`.

This is read-only rendering over data the read endpoint already returns. It adds no
control, so `test_surface_strip_asserts_no_execution_authority` (the existing
authority guard) still holds.

## 3. Proof (run in this environment)

- `python -m pytest tests/test_prism_opportunity_entry_flow.py -q -rEf`
  → **77 passed** (was 72 at the branch head; **+5** this pass: coverage, sentinel
  read, verbatim value, negative control, surface pin).
- `python -m pytest tests/test_prism_opportunity_radar_module.py tests/test_prism_console_ci_wiring.py -q -rEf`
  → **55 passed** (adjacent Lane 2 guards unchanged).
- `python -m pytest tests/architecture -q` → **11 passed**.
- Frontend: `corepack pnpm install --frozen-lockfile && corepack pnpm build` →
  `✓ built in 1.55s` (`tsc --noEmit` runs first; `noUnusedLocals` is on, so the
  build is load-bearing — it caught no error this pass).
- CP10 boundary judge: `git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge`
  → **PASS**.
- `api/main.py` untouched (frontend + test only); no `dist/` staged.

### Negative control (proves `fact()` is load-bearing)

`test_negative_control_an_empty_string_fact_reads_as_the_sentinel`: an entry whose
stored `landed_cost` is `""` (the handler's default for a non-commercial text field)
must read as `UNKNOWN`, not a blank cell. Under a raw passthrough (`entry[field]`) it
would render `""`; the measured row is `UNKNOWN`, and the test asserts both the
sentinel and the divergence from the blank the naive path would have produced.

## 4. Remaining uncertainty / not claimed

- No production-runtime observation: this is a repository-source change with a
  local build, not a deployment observation.
- `notes` is excluded from the grid and is still not rendered anywhere; surfacing it
  is a separate bounded slice.
