# P0-D — Identity + Product Narrative — PRODUCTION GREEN

**Start HEAD:** `f1fb29a`  
**End HEAD:** `2026bfa`

## Track A — Identity

**Source:** Firebase Auth → `/api/me` (`build_user_profile`) → AuthContext → PersonalCodex / Echofeild  
**Removed:** Authenticated path no longer loads `/api/codex/personal` (always Zahrune).

**Two-user production verification:**
- User A display_name `arkadia.p0d.alice.*` ≠ User B `arkadia.p0d.bob.*`
- Neither is "Zahrune Nova"
- Cross-user note still 404 (Phase 0C intact)

## Track B — Homepage

**Proposition:** A place to think, remember, and build — with AI that keeps your thread.  
**Primary CTA:** Start free — talk to the Oracle  
**Deployed asset:** `/assets/index-CR3R5F9q.js`

## Regression

P0-B / Phase 0C / Phase 1 / P0-C: PASS (isolation re-probed; CTAs preserved)

## Commits

- `41997d7` feat(identity): Personal Echofeild uses authenticated user, not Zahrune
- `2026bfa` feat(home): public product narrative — think, remember, build
