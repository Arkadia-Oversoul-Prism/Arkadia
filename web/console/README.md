# Arkadia Console (`web/console/`)

> **Prism identity:** Operational and governance inspection surface. It is part of the **Arkadia Oversoul Prism**, not a separate Arkadia intelligence, authority path, or competing source of truth.
>
> **Canonical principle:** One human-governed intelligence architecture. Many expressions. One coherent substrate.
>
> **Authority boundary:** Capability does not confer authority. Human authority remains the decision boundary, and implementation claims must remain bounded by evidence.


The operator console **derived** from three sources — not a redesign:

1. the existing Arkadia UI (`web/public_prism`) — what Arkadia intended to communicate;
2. the derived backend console (`relational-substrate/web`) — what the backend exposed when no UI was imposed;
3. `RECONCILED-BOUNDARY-MAP-01.md` — what the system can now actually prove.

`RECONCILED-CONSOLE-ARCHITECTURE-01.md` records the derivation and the
interaction model. The map has veto power: where it says a boundary is not
enforced, not deployed, or not provisioned, the console says so.

## Scope — foundation only

Implementation Gate is **OPEN for the console foundation only**. This is not the
whole application and not a dashboard. It establishes:

1. the flow × posture primitive (`src/lib/posture.ts`);
2. the boundary grammar (`src/lib/grammar.ts`);
3. the Boundary Inspector;
4. truthful authority / unprovisioned states (`src/lib/authority.ts`);
5. provenance / evidence representation;
6. the operator verbs See / Distinguish / Authorize / Inspect / Verify.

The first complete boundary instance is **APPROVAL ≠ EXECUTION**
(`src/data/approvalNotExecution.ts`) — chosen because it is machine-enforced and
covered by tests that demonstrate the distinction. Expansion goes outward from
this verified unit, not from ten screens around an unverified abstraction.

## Commands

- `npm install`
- `npm run dev` — dev server on port 5174 (`ARKADIA_BACKEND` selects the proxy target, default `http://localhost:8080`)
- `npm run typecheck` — `tsc -b`
- `npm run build` — `tsc -b && vite build` into `dist/`

## The two-axis primitive

A boundary carries `mechanism` (`ENFORCED` / `ENFORCED_UNTESTED` / `DECLARED`)
and a four-rung `deployment` ladder (`implemented` / `tested` / `deployed` /
`productionVerified`). Green is reserved for the top rung. An enforced mechanism
that is not production-verified renders as **unverified**, never as settled.

## Surfaces

| Route | Surface |
|---|---|
| `/` | 01 · Spine — the causal grammar (cycle with a causal spine) |
| `/inspector` | 02 · Boundary Inspector — forensic view |
| `/work` | 03 · Work / Consequence — operational view (shape only; not yet wired to the substrate) |
| `/authority` | 04 · Authority — sovereign control; `UNPROVISIONED` shown, never simulated |
| `/boundary/:id` | a boundary instance (the primary unit) |

Standing non-claims (Render UNVERIFIED, Flamekeeper UNPROVISIONED,
AUTHORITY-CLOSURE-01 PRE-PRODUCTION, NOT DEPLOYED) render persistently in the
shell. They are not dismissible.

## Deployment (canonical Render runtime)

Arkadia's production application is served from one Render web service:
`https://arkadia-qzu4.onrender.com` (Render service `Arkadia`, repository branch
`main`, root `Dockerfile`). The Docker image builds both frontend applications
and the FastAPI backend together.

| Path | Surface |
|---|---|
| `/` and existing public app routes | Primary Arkadia experience: Solariun, Arkana, Canvas, and existing user-facing surfaces |
| `/operator/` | Reconciled governance/operator console |
| `/n-atlas-lab`, `/n-atlas-tester` | Focused N-ATLaS Lab compatibility routes |
| `/api/*`, `/solspire/*`, `/health` | Existing backend APIs on the same origin |

The primary frontend's build output is served at the origin root. The operator
console is built with the `/operator/` asset base so its bundle cannot collide
with the primary app's `/assets/*`. The existing N-ATLaS direct routes load the
same operator bundle without creating a second service.

## Legacy deployment boundary

`web/public_prism` is retained as source for the existing Solariun/Arkana and
Canvas experience during this consolidation. It is **not** intended to remain a
separate production deployment. Do not archive or delete this source directory
until the required screens and routes have been migrated or their continued
ownership is explicitly decided. The former Vercel alias is not the canonical
runtime; decommissioning external aliases and dormant Render static sites is a
separate retirement step after route and runtime verification.

## Verification boundary

A successful Docker build proves packaging, not full production parity. Before
retiring legacy deployment targets, verify the root UI, Solariun Canvas routes,
Arkana interaction, operator routes, N-ATLaS direct routes, same-origin API calls,
authentication boundaries, and emitted Gate-2 evidence. Browser inspection blocked
by deployment protection remains `BLOCKED`; unobserved behavior remains
`UNKNOWN`; human acceptance remains `NOT CLAIMED`.
