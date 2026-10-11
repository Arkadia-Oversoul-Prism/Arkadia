# Arkadia — Bounded Technical Portfolio

**Status:** Portfolio draft; claims are intentionally limited to evidence currently preserved.  
**Canonical production origin:** https://arkadia-qzu4.onrender.com  
**Repository:** https://github.com/Arkadia-Oversoul-Prism/Arkadia  
**Evidence checkpoint:** 2026-10-11  
**Accepted source revision:** `36df0ea8169087802e4fc34ae96496058a380d05`

## Project in one paragraph

Arkadia is an actively developed, human-governed AI and execution architecture. Its engineering direction connects identity and workspace boundaries to authorization, bounded execution, work events, evidence, verification, and operational projections. Its core design principle is that model capability does not itself confer authority: authorization, execution, verification, and acceptance are distinct states. This is a description of the architecture and development intent, not a claim that every subsystem or interface has completed production acceptance.

## Demonstrable now

### 1. One canonical production deployment

- Production origin: [Arkadia on Render](https://arkadia-qzu4.onrender.com)
- Production is designated as Render-only; this portfolio does not present Vercel as a production target.
- Acceptance workflow waits for `/api/version` to report the exact workflow source revision before it performs acceptance probes.

### 2. Authenticated Engineering Lab acceptance at an exact SHA

- [GitHub Actions run 38159464567](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38159464567)
- Target and live source revision: `36df0ea8169087802e4fc34ae96496058a380d05`
- Render deployment observed for that revision: `dep-db5s9i0u01pc73evsrjg`
- Workflow decision: **ACCEPTED**, with no recorded blockers or critical failures.
- Redacted evidence artifact: `authenticated-canonical-render-acceptance`
- Artifact SHA-256: `6d72b9a6d5204317d154cdedf4c826727681d029056d0cff936bae9117a1d8e1`
- The artifact was configured to expire on **2026-11-10 17:24:56 UTC**. Preserve a controlled copy before expiry if it is needed for a longer-lived portfolio record.

The workflow demonstrated these specific assertions:

| Assertion | Observed result |
|---|---|
| Anonymous request to `GET /api/lab/overview` | HTTP 401 — expected denial |
| Firebase-authenticated request to `GET /api/lab/overview` | HTTP 200 — permitted low-privilege read |
| Ordinary Firebase user to `/api/operator/security-verification` | HTTP 403 — expected denial |
| Canonical `/login` route | HTTP 200 |
| Firebase browser sign-in and authenticated Engineering Lab journey | Passed |
| Browser console errors / uncaught page errors during that journey | 0 / 0 |
| Disposable Firebase identity cleanup | Passed |
| Live SHA equals target SHA | Exact match |
| Credential/config values persisted in evidence | No; report records presence, not values |

This is a bounded acceptance result for the tested endpoints and the authenticated Engineering Lab journey. It is not a certification of the entire application.

## Architecture under active development

The repository describes the intended substrate as:

`Identity → Workspace → Workload → Workstream → Authorization → Execution → WorkEvent → Evidence → Knowledge → Verification → Operational projection`

Relevant implementation areas include:

- `api/` and `solspire/` — API and operating substrate
- `weaver/` and `lab/engineering_lab/` — execution and Engineering Lab surfaces
- `knowledge/` — Knowledge OS
- `web/public_prism/` — frontend
- `docs/control-plane/evidence/` — engineering evidence records

These are repository navigation pointers, not assertions that each area has independently passed current production acceptance.

## Explicitly not yet established

Do **not** use this portfolio to claim any of the following as complete:

1. **All-operation authorization correctness.** The OpenAPI document and runtime authorization boundary still require fresh, operation-by-operation reconciliation. Schema declarations alone are not runtime proof.
2. **Complete route reconciliation.** Current source declarations, mounted runtime routes, and live operations require a fresh exact-revision inventory and a disposition for every mismatch.
3. **Every major UI workflow.** The acceptance evidence covers the Engineering Lab journey described above. Solariun/Canvas, Operator Console, Arkana chat/streaming, and N-ATLAS session completion require separate functional browser journeys.
4. **Complete deployment and integration cleanup.** Account-level confirmation of legacy Vercel disconnection/deletion, Render-to-GitHub integration identity, and active legacy-origin callers remains outstanding.

## Next release checkpoint

The portfolio should be upgraded only after these steps have evidence tied to the exact live SHA:

1. Capture the current production `/openapi.json` and live `/api/version`; reconcile every operation's effective security requirement against actual runtime behavior, with justified public exceptions documented.
2. Rebuild the source/runtime/live route inventory. Resolve or explicitly disposition each unmatched route and preserve the machine-readable report.
3. Review and disposition security-relevant pull requests, including [#449](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/449), [#451](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/451), and [#432](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/432). Merge only after diff, tests, dependency/overlap, and required-check review.
4. Run targeted browser journeys for each major surface and record positive and negative controls.
5. Verify deployment/integration cleanup from authoritative account or runtime evidence.
6. Repeat production acceptance against the exact deployed SHA after changes; preserve redacted evidence and its checksum.

## Claiming rules

- Link each material claim to a commit, workflow run, evidence artifact, or reproducible test.
- Label architecture intent separately from implementation and acceptance.
- Distinguish a passing test from production deployment, and deployment from production acceptance.
- Do not expose credentials, tokens, private user data, or raw authentication artifacts in the public portfolio.
- If evidence is missing, stale, or tied to another revision, state that limitation instead of carrying the claim forward.

## Current claim boundary

**Defensible today:** Arkadia has a canonical Render deployment and a successful exact-SHA authenticated Engineering Lab acceptance record with redacted evidence.

**Not defensible today:** that all operations have correct authorization metadata and runtime enforcement, all routes reconcile, all major UI workflows pass, or every deployment/integration cleanup task is complete.
