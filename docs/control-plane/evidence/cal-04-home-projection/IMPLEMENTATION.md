# CAL-04 — Home projection implementation

## Status
IMPLEMENTED — review / preview verification required

## Bounded move
Expose one existing deep substrate through the existing Solariun Field/Object grammar: authenticated Personal Codex / identity context.

## Source of truth
`AuthContext` already hydrates `/api/me`, `/api/me/codex`, and `/api/me/identity-spine` for the authenticated node. No new request, persistence layer, API, or identity model is introduced.

## Change
`SolariunHomeCockpit` now consumes the existing `useAuth()` Codex state and renders a compact `Identity context` field using the existing `solspire-object` / Solariun object grammar. The projection is truthful:
- authenticated Codex present → display existing name, role, and soul function fields
- authenticated Codex absent → explicit unavailable/empty state
- no fallback identity or synthetic content

## Boundaries preserved
- No new database or persistence
- No new identity/memory/conversation/project system
- No Oracle/Arcana semantic changes
- No WorkEvent or authorization changes
- No K15/K3 changes
- No production deployment or merge

## Why this move
The Home field was already truthful for live operational state but did not expose an existing deep personal substrate. The Codex is already hydrated by the canonical identity boundary, making this a narrow projection rather than a new integration.

## Verification
Not yet claimed. Build, preview, authenticated runtime, and responsive behavior remain to be verified.

## Next action
Deploy preview, inspect authenticated Solariun Home, verify the Codex projection and regressions, then stop at human review.
