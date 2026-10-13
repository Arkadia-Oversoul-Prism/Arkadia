# Opportunity Radar — operator notes rendering

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: render the last declared entry read field the console never
showed — `notes`. The lane's own continuity note (`AGENT-02`) named this as the
next bounded task: *"surface `notes` (excluded from the grid, still unrendered)
**only if** it can be tied to a verified read field and needs no new control."*
It is. Authority: human retains merge, production deployment, and acceptance.
Nothing here claims any of the three.

Successor slice to `prism-opportunity-fact-grid-01` (same branch/PR, PR #492,
draft). It reuses the same surface and the same executed-Node probe; it adds no
transport, no route, no write, and no authority.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, base `main`).
- `origin/main` at the start of this pass:
  `49809f45274f2f81b24e01fefdfb3009e8717495`.
- Branch head before this slice: `6dc3b13c`.
- Environment: node `v24.21.0`, pnpm `10.26.1`.

## 1. The precondition — `notes` is a verified read field (measured)

Before wiring anything, the field was traced end to end:

- `solspire/buyer_recon_router.py` `BuyerReconEntryInput` declares
  `notes: str = ""` (line 63) alongside `why_this_prospect: str = ""`.
- `solspire/buyer_recon.py` `BuyerReconEntry` is a frozen dataclass with
  `notes: str` (line 83) whose `to_dict()` returns `asdict(self)` (line 88), so
  **both** entry reads (`GET /buyer-recon`, `GET /buyer-recon/projects/{id}`)
  return the field.
- The column exists with `notes TEXT NOT NULL DEFAULT ''` (line 224) and
  `update_entry`'s allowlist (`__dataclass_fields__ - {id, board_id, ...}`) lets an
  owner/edit write it — so a note reaches the store through the **same**
  create/edit handlers `ProspectEntryForm` already drives. No new route, no new
  control, no new mutation path.
- The archived Prism radar declared the field (`ProjectOpportunityRadar.tsx:12`,
  interface `notes:string`) and the active console never rendered it.

Display-only. `notes` is asserted about nothing: the copy reports what the board
carries and claims no currency or sufficiency.

## 2. The change

- `ProjectOpportunityRadar.tsx` renders the note **gated on its presence**
  (`entry.notes &&`), testid `opportunity-entry-notes-{id}`, reading `{entry.notes}`
  straight off the entry the board read returned. An entry without a note (backend
  default `""`) emits nothing.

No contract-module change was required: `notes` is excluded from `ENTRY_FACT_FIELDS`
precisely because it has its own UI (asserted by the fact-grid test). It is now that
UI.

## 3. Proof (run in this environment)

- `python -m pytest tests/test_prism_opportunity_entry_flow.py -q -rEf`
  → **81 passed** (was 77 at the branch head; **+4** this pass).
- `python -m pytest tests/test_prism_opportunity_radar_module.py tests/test_prism_console_ci_wiring.py tests/test_buyer_recon_router_board_scope.py -q -rEf`
  → **62 passed** (adjacent Lane 2 guards unchanged).
- `python -m pytest -q $(python scripts/console_contract_domain.py)` (derived
  console-contract domain, 21 files) → **434 passed**.
- `python -m pytest tests/architecture -q` → **11 passed**.
- Frontend: `corepack pnpm install --frozen-lockfile && corepack pnpm build` →
  `✓ built in 1.57s` (`tsc --noEmit` first; `noUnusedLocals` is on).
- CP10 boundary judge: `git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge`
  → **PASS**. `api/main.py` untouched; no `dist/` staged.

### The four tests

1. `test_read_returns_a_recorded_note_verbatim` — create with `notes`, assert the
   create response, the **persisted row**, and the project-board read all carry it.
2. `test_negative_control_an_entry_without_a_note_reads_the_empty_default` — an
   entry created without a note reads `""`; proves the surface must gate on the
   value rather than render the field unconditionally (an unconditional render
   would emit an empty paragraph).
3. `test_notes_read_verbatim_in_the_contract_probe` — the executed-Node probe now
   carries `notes_recorded` / `notes_empty`, so the shape is measured, not assumed.
4. `test_surface_renders_a_recorded_note_gated_on_its_presence` — source pin:
   the gate, the per-entry testid, and `{entry.notes}` off the read entry.

## 4. Remaining uncertainty / not claimed

- No production-runtime observation: repository-source change with a local build,
  not a deployment observation. No merge, deployment, or acceptance.
- The full suite was **not** run twice this pulse (per the time budget); the change
  is attributed by the derived console-contract domain (434) and the targeted
  guards, all of which pass, plus the +4 node increase in the one test file edited.
