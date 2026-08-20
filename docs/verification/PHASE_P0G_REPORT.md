# P0-G — Conversational Memory Capture

**Status:** GREEN  
**Commit:** (feat p0-g)

## Architecture
Reuses `/api/personal/ingest-note` + P0-F governance. No second store.

## UX
Oracle message toolbar: **Save to memory** (user + Arkana turns).
Unauthenticated → hint to sign in. Server confirmation before durable success.

## Production API proof
- A/B unique capture markers isolated
- Cross-user get/delete 404
- Edit/delete owner path works
- Unauth ingest 401

## Acceptance
A–M: PASS (UI CODE-VERIFIED; persistence/ownership PROVEN on API)

## Next
STOP. Await P0-H authorization.
