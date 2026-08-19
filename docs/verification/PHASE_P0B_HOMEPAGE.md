# P0-B — Homepage / First 5 Minutes

## Inspection (pre-change)

Existing surface (`web/public_prism`):

- **Home** in `App.tsx` — dense portal grid, primary CTA was “5-Minute Reset” → LivingGate
- **LivingGate** — long diagnostic / IMS flow (not a 30s value moment)
- **ArkanaCommune** — Oracle works as guest
- **Login** — IMS-framed (“Already a node?”), password + magic link
- No public self-serve signup UI (acceptable for beta; private memory behind sign-in)

## Intended first-session journey

1. Land on Home → understand what Arkadia is in one line  
2. ≤ 30s: **Talk to the Oracle** (guest)  
3. Optional: 5-minute reset  
4. Optional: Sign in for private memory / ownership  
5. Do **not** require diagnostic or IMS before first Oracle reply  

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Primary CTA is Oracle, not diagnostic | ✅ |
| 2 | Plain-language value prop on Home | ✅ |
| 3 | Guest path explicit | ✅ |
| 4 | Sign-in framed as private memory, not “node membership only” | ✅ |
| 5 | Secondary path still reaches LivingGate | ✅ |
| 6 | No auth/architecture redesign | ✅ |
| 7 | Phase 0/1 backend gates untouched | ✅ |

## Change set

- `web/public_prism/src/App.tsx` Home hero + CTAs only  
- Primary: `Talk to the Oracle` → `commune`  
- Secondary: `Begin Your 5-Minute Reset` → `gate`  
- Sign-in label: `Sign in for private memory`

## Out of scope (hold)

- Public registration flow  
- LivingGate rewrite  
- Mobile polish pass  
- Onboarding checklist after login  

## Production visual/smoke (2026-08-19)

Host: `https://arkadia-prism.vercel.app`  
Bundle asset: `/assets/index-CCsBWWI-.js` (post-`2144910`)

| # | Check | Result |
|---|--------|--------|
| 1 | Plain-language value prop visible | ✅ "Talk to Arkana. Capture notes… not the public corpus." |
| 2 | Dominant CTA = Talk to the Oracle | ✅ teal primary button |
| 3 | Guest mode copy visible | ✅ "Guest mode works now…" |
| 4 | Secondary 5-Minute Reset present | ✅ gold secondary button |
| 5 | Sign-in framed as private memory | ✅ in deployed bundle |
| 6 | Path hint first 5 minutes | ✅ on page |
| 7 | Guest Oracle API without auth | ✅ `POST /api/commune/resonance` → 200 |

**P0-B → 🟢 PRODUCTION VERIFIED**
