# Chief Agent — Founding Implementation Plan

**Target:** staged commissioning  
**Budget decision:** build on free/current infrastructure first; introduce paid persistent compute when revenue or an explicit budget permits.  
**Deployment decision:** hybrid — dedicated module in this repository, integrated with existing Arkadia Console and backend.

## Gate 0 — Repository and contract reconnaissance

- [ ] Inspect current identity and workspace subject model.
- [ ] Inspect `api/oracle_spine.py` and provider routing.
- [ ] Inspect Knowledge OS persistence and retrieval contracts.
- [ ] Inspect approval request/decision/consumption lifecycle.
- [ ] Inspect Weaver and Engineering Lab authorization, execution, WorkEvent and Evidence contracts.
- [ ] Inspect current deployment topology, environment variables, health checks, and persistent storage.
- [ ] Inspect Console navigation and API client conventions.
- [ ] Record existing reusable interfaces and gaps; do not infer runtime health from historical documents.

**Exit:** a source-linked integration map and explicit list of missing contracts.

## Gate 1 — Identity and governance

- [ ] Human-review and approve the identity record and charter.
- [ ] Human-review and approve an exact authority-policy version.
- [ ] Create a dedicated GitHub App with repository-only, read-first permissions.
- [ ] Define service principal mapping in the existing identity system.
- [ ] Define expiry, rotation, revocation and emergency suspension.
- [ ] Add negative tests for self-approval, self-escalation, reserved actions and stale policy.

**Exit:** identity can authenticate but has no write or execution authority until separately allowlisted.

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
