# Chief Agent — Founding Implementation Plan

**Target:** staged commissioning  
**Budget decision:** build on free/current infrastructure first; introduce paid persistent compute when revenue or an explicit budget permits.  
**Deployment decision:** hybrid — dedicated module in this repository, integrated with existing Arkadia Console and backend.

## Gate 0 — Repository and contract reconnaissance

- [x] Inspect current identity and workspace subject model.
- [x] Inspect `api/oracle_spine.py` and provider routing.
- [x] Inspect Knowledge OS persistence and retrieval contracts.
- [x] Inspect approval request/decision/consumption lifecycle.
- [x] Inspect Weaver and Engineering Lab authorization, execution, WorkEvent and Evidence contracts.
- [x] Inspect repository deployment topology, environment references and health-check contracts; provider-side storage/plan details remain unverified.
- [x] Inspect Console navigation and API client conventions.
- [x] Record reusable interfaces, blockers and unverified provider-side facts in `INTEGRATION_MAP.md`; no runtime-health inference.

**Exit:** a source-linked integration map and explicit list of missing contracts.

## Gate 1 — Identity and governance

**Design documents prepared:** `IDENTITY_ACCESS_AND_REVOCATION.md`; identity and authority YAML aligned to it. All remain proposed/inactive.

- [ ] Human-review and approve the identity record, charter, identity/access ADR and exact authority-policy digest.
- [ ] Select and verify a hosting-supported runtime-to-broker authentication mechanism; do not assume Render workload identity exists.
- [ ] Implement the separate Executive Identity Broker and short-lived asymmetric machine tokens; do not extend Firebase human auth to accept arbitrary machine JWTs.
- [ ] Implement durable delegation registry, append-only events, credential epoch and Founder-only grant/suspend/revoke controls.
- [ ] Bind the Founder UID from a verified Firebase session to one existing canonical SolSpire workspace; no client-supplied UID and no automatic workspace creation.
- [ ] Implement explicit project/resource and record-family allowlists; private conversations, personal Codex, secrets and unrelated personal records remain denied.
- [ ] Implement curated Knowledge OS retrieval; broad Founder-UID retrieval is prohibited for the agent.
- [ ] Create a dedicated GitHub App with repository-only, read-first permissions only if/when repository access is needed; it is not the API identity.
- [ ] Enforce expiry/revocation of enterprise Authorizations at the Weaver dispatch boundary and invalidate outstanding authorizations on delegation revoke.
- [ ] Add negative tests for token validation, cross-owner/workspace access, private-note access, self-approval, self-escalation, stale policy, revoke-during-queue and restart recovery.

**Exit:** the machine principal can authenticate only through the broker, can read only explicitly granted resources in one Founder-owned workspace, and is immediately denied on suspension/revocation. No write or execution authority exists unless separately and explicitly commissioned.

## Gate 2 — Read-only intelligence

- [ ] Implement an adapter to the canonical intelligence spine.
- [ ] Implement read-only repository/project inventory tools.
- [ ] Implement evidence-linked state report generation.
- [ ] Persist reports using existing Knowledge OS contracts.
- [ ] Add source timestamps, confidence/epistemic state and stale-data markers.

**Exit:** reproducible Executive State of Arkadia report; no external side effects.

## Gate 3 — Bounded execution

- [ ] Register each tool with explicit schema, capability, scope and risk.
- [ ] Route consequential actions through existing approval and execution boundaries.
- [ ] Add idempotency keys, timeouts, rate limits and retry policy.
- [ ] Permit isolated tests and pull-request preparation only after review.
- [ ] Keep protected-branch merge and production deployment human-controlled.

**Exit:** test evidence proves each allowlisted action and denied action behaves as specified.

## Gate 4 — Durable operation

- [ ] Select orchestration framework after runtime/dependency review.
- [ ] Configure durable checkpoints and recovery semantics.
- [ ] Add event triggers and scheduled jobs with deduplication.
- [ ] Add health/readiness, structured logs, audit events and alerting.
- [ ] Back up state and test restore and credential revocation.
- [ ] Establish service budget and operational owner before claiming continuous service.

**Exit:** restart/recovery and failure-injection tests pass; documented service objectives.

## Gate 5 — Scoped L3 commissioning

- [ ] Founder approves a finite list of L3 capabilities and limits.
- [ ] Define permitted projects, repositories, data classes, budget, duration and external communication scope.
- [ ] Define mandatory escalation conditions and review cadence.
- [ ] Test kill switch and founder override.
- [ ] Record commissioning decision and policy digest.

**Exit:** agent operates only within the approved delegation. All unlisted capabilities remain denied.

## First assignment after read-only commissioning

Produce an Executive State of Arkadia report covering:
- current architecture and deployed surfaces;
- active projects and unfinished work;
- technical debt and reliability risks;
- security and authorization gaps;
- commercial opportunities with evidence quality;
- top five priorities ranked by impact, urgency, cost and reversibility;
- unknowns requiring human investigation.

The report is an assessment, not authority to execute its recommendations.
