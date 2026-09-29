# R1 → R4 — Solariun Home Bootstrap / Identity Calibration

**Authorization:** Architect verdict — R1–R4 authorized in parallel  
**Branch:** `cal-r1-r4-home-bootstrap-identity`  
**Base:** `main` at `7370bd84f80e40e185d70797cf3dee80973c8b82`

## Scope

This track repairs the ordering boundary visible in the production Home screenshot without inventing a second workspace, endpoint, persistence layer, or authority path.

### R1 — bootstrap diagnostic
The Home surface now resolves `GET /solspire/workspace` before attempting its five canonical SolSpire reads.

### R2 — bootstrap repair
The existing canonical workspace endpoint is idempotent and provisions the bounded workspace for the authenticated Firebase subject. The frontend now actually invokes that existing substrate instead of assuming the workspace already exists.

### R3 — Home read sequence
Pulse, Workload, WorkEvents, Synthesis, and Proposals are re-read only after workspace bootstrap succeeds. Personal Field remains read from the existing `/api/me/field` surface.

### R4 — identity alignment
Home records a non-authorizing diagnostic alignment between the canonical workspace subject reference and the Personal Field identity uid. The UI reports only the bounded state (`ALIGNED`, `MISMATCH`, or `UNKNOWN`), never fabricating identity.

## Boundaries preserved

- No new backend endpoint.
- No new database or workspace model.
- No K15/K3 changes.
- No authorization or execution semantics.
- No fabricated workload, pulse, event, synthesis, proposal, or identity state.
- Existing truth-state handling remains intact.

## Verification status

Repository implementation is complete on the branch. Authenticated production verification remains a human deployment/runtime gate.
