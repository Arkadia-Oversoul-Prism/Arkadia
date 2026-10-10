# ADR-016: Single Canonical Reconciled Deployment

**Status:** Accepted — governing invariant
**Date:** 2026-10-10
**Decider:** Flamekeeper (sovereign authority)
**Supersedes:** Any prior document, note, or configuration implying that the Arkadia user interface and the Arkadia backend are independently authoritative production deployments.
**References:** `web/console/README.md` (consolidation), `docs/control-plane/evidence/canonical-render-single-runtime-01/`, `Dockerfile`, `api/frontend_routes.py`, `architecture/runtime_manifest.yaml`

---

## Context

Arkadia accumulated more than one reachable production surface over its history: a Render
backend, a Vercel frontend alias, a root-level Vercel project, historical Render hostnames, and
separate gateway/bot services. Some of these respond to HTTP and some are recorded in
configuration. Responding to a request, appearing in a deployment list, or being named in a
stale document does **not** by itself establish canonical ownership.

This ambiguity is a governance defect, not merely a documentation one. It makes "which system is
Arkadia?" depend on which hostname a reader happens to inspect, and it lets an alternate
deployment become an accidental second source of truth.

This ADR fixes the invariant once so that future work inherits it rather than re-litigating it
per hostname.

---

## Decision

**Arkadia operates as ONE canonical, reconciled deployment.**

The user interface, API, authentication and authorization boundary, shared relational substrate,
execution runtime, evidence systems, and product interfaces belong to one coherently governed
deployment. The interface and runtime may contain distinct modules, services, routes, processes,
or internal components; those implementation boundaries do **not** create independent canonical
deployment authority.

### Governing rules

1. Arkadia has **one** canonical reconciled deployment.
2. Historical frontend/backend separation is **not** the governing architecture.
3. An observed hostname is **not** proof of canonical ownership.
4. A successful HTTP response from an alternate deployment does **not** establish acceptance.
5. All changes must be reconciled with the canonical source and the canonical deployment.
6. Runtime evidence must identify the **actual deployment under examination** (host + revision).
7. Deployment drift must be **reported explicitly**, never smoothed over.
8. No agent may establish, promote, or treat an alternative deployment as canonical without
   explicit sovereign authorization.

### Required distinctions

Every deployment claim must separate these six things; conflating any two is a defect:

| # | Concept | Meaning |
|---|---|---|
| 1 | **Canonical source revision** | The intended commit (`main` HEAD, or an explicitly pinned revision). |
| 2 | **Canonical deployment identity** | The single governed production deployment (service + origin). |
| 3 | **Actual running revision** | What the running deployment actually serves — evidenced, not assumed. |
| 4 | **Internal module/route registration** | Which routers, mounts, and frontend bundles are wired in that build. |
| 5 | **Runtime verification** | Direct observation of the running deployment's behaviour. |
| 6 | **Explicit acceptance** | A human authorization that the verified behaviour is accepted. |

The governance chain is unchanged:

```
IDENTITY → AUTHORITY → AUTHORIZATION → PROPOSAL → APPROVAL → EXECUTION
        → WORK_EVENT → EVIDENCE → VERIFICATION → REVIEW
```

**Specification ≠ implementation. Deployment ≠ verification. Verification ≠ acceptance.**

---

## Observed conflict (recorded, not resolved by this ADR)

Read-only inspection on 2026-10-10 at source `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
observed at least the following reachable surfaces:

| Surface | Observation | Reading |
|---|---|---|
| `arkadia-qzu4.onrender.com` | 287 OpenAPI paths; root serves the primary Prism SPA; `/operator` and `/solariun/*` serve SPAs; bundles reference no external backend (same-origin `/api`) | **Strongest observed unified-runtime candidate** |
| `arkadia-kw64.onrender.com` | 286 OpenAPI paths; root returns JSON, `/operator` 404, `/solariun/*` 404 | Conflicting, apparently older runtime |
| `arkadia-prism.vercel.app` | `/api/heartbeat` returns the SPA shell (HTML), not backend JSON | Legacy split artifact |

**This ADR does not declare which Render service owns which hostname.** That mapping requires
Render management access and remains `UNKNOWN` until inspected. The observation above is the
basis for requiring runtime-identity evidence, not a resolution.

---

## Consequences

- Any configuration that exports the API to an external host, or that treats the frontend and
  backend as separate production deployments, conflicts with this ADR and must be reconciled
  (reported first, then changed only under authorization).
- `architecture/runtime_manifest.yaml` must represent the canonical deployment identity and
  honestly carry `unknown`/`blocked` states rather than inferring liveness.
- A read-only revision endpoint (`GET /api/version`) makes the running revision observable after
  a build containing it is deployed. It cannot prove what an already-running deployment serves.
- A matching revision is **necessary** evidence of source-to-runtime consistency but is **not**
  sufficient proof that the application is functioning correctly.
- No production configuration change, deployment, alias retirement, or resource deletion is
  authorized by this ADR. Those remain separate, explicitly authorized actions.


---

## Reconciliation addendum — 2026-10-10

Render provider metadata identifies the canonical production service as:

- Service: `Arkadia`
- Service ID: `srv-db49jbh42hec73aj84qg`
- Origin: `https://arkadia-qzu4.onrender.com`
- Branch: `main`
- Region: Oregon
- Render SSH address: `srv-db49jbh42hec73aj84qg@ssh.oregon.render.com`
- Live deploy ID: `dep-db54i61rn11c73d7cq10`
- Live deploy commit: `17b931b4fe6dd9b27749894dd0d9b1dc9a2e14f5`

The live deploy commit matches GitHub `main` at the time of inspection. This resolves the prior service-ID/hostname ambiguity at the provider-metadata boundary. The SSH address is a Render connection address, not a private SSH key or a GitHub deploy key; no private key was read or exposed.

A fresh HTTP/OpenAPI and authorization probe is still required before runtime verification and acceptance can be marked complete. The current source includes `GET /api/version` for revision evidence.
