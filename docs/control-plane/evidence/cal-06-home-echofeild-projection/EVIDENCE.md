# CAL-06 — Personal Echofeild Home Projection

**Move ID:** CAL-06  
**Title:** Project existing Personal Echofeild through Solariun Home field grammar  
**Status:** PREVIEW READY / REVIEW  
**Authority:** Human-authorized bounded projection  
**Branch:** `feat/cal-06-home-echofeild-projection`  
**Base:** `main` at `407ec5ba3b0bc984565af39d8d86a99d388bd629`  
**Head:** `6386eb9c5ee015516f6c2fd65c486c49937365b0`

## Problem

The canonical Solariun Home field already surfaces pulse, workload, WorkEvents, synthesis, proposals, and Personal Codex identity. The existing Personal Echofeild is a deeper authenticated SolSpire/Knowledge OS surface but was not represented in Home.

## Bounded change

Home now reads the existing `getPersonalField()` read model from `/api/me/field` and projects only compact contextual signals:

- authenticated field identity
- existing SolSpire project count
- existing Knowledge OS note count
- existing graph node count
- existing timeline count
- latest existing graph node title when available

No new endpoint, persistence layer, database, ontology, memory system, conversation system, or WorkEvent semantics were introduced.

## Implementation

- `web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx`
- One commit: `6386eb9c5ee015516f6c2fd65c486c49937365b0`
- PR: #70

## Evidence

- Vercel preview deployment created for exact head commit.
- Deployment: `dpl_CMLtPB1RsWuLqUHayyyeqccJaws9`
- Preview: https://arkadia-prism-git-feat-cal-06-home-echofei-c16079-arkadia-prism.vercel.app
- Vercel deployment reached **READY**.
- GitHub combined status for head reports **Vercel: success**.
- Preview root returned HTTP 200 and served the built Vite application.

## Verification limits

Authenticated browser verification of the Personal Echofeild response and rendered Home projection was not performed by this cycle because the available browser connector surface was not exposed. Therefore:

- PREVIEW READY: confirmed
- build/deployment evidence: confirmed
- unauthenticated preview shell response: confirmed
- authenticated runtime/data rendering: UNKNOWN
- production verification: NOT CLAIMED

## Human gate

PR #70 remains open and unmerged.

Required human action:

1. **TEST** authenticated Solariun Home on desktop/mobile.
2. Confirm the Personal field section reflects the authenticated `/api/me/field` response and preserves empty/unavailable truth states.
3. **REVIEW** the bounded change.
4. **MERGE** if accepted.

Production verification remains a separate post-merge step.
