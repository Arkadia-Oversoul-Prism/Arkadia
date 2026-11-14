# Arkadia Executive Office — Chief Agent Foundation

**Status:** PROPOSED / NOT COMMISSIONED  
**Identity:** `ARKADIA-CHIEF-001`  
**Target office:** Chief Executive Operating Agent  
**Authority:** Human-delegated, policy-bounded; no authority is active by virtue of this scaffold.

This is a repository-native foundation for a persistent, model-independent operating agent. It is an extension of Arkadia's existing substrate, not a second intelligence spine, identity system, authorization service, memory store, or execution plane.

## Canonical integration constraints

Before implementing runtime behavior, reconcile with the existing:
- `api/oracle_spine.py` — canonical intelligence spine.
- `knowledge/context_engine.py` — contextual memory/retrieval.
- `api/approval_routes.py` and existing tool-run approval checks — approval lifecycle and separation of decision from execution.
- Weaver / Engineering Lab authorization, WorkEvent and Evidence contracts.
- Existing identity, workspace, workload and workstream models.

Do not create parallel versions of these systems. Reuse their contracts through explicit adapters after inspection and tests.

## Initial scope

1. Stable service identity and versioned operating charter.
2. Explicit capability/authority policy with fail-closed defaults.
3. Read-only institutional assessment and evidence-backed reporting.
4. Human-approved, bounded execution through existing Arkadia authorization paths.
5. Provider- and hosting-independent runtime design.

## Not included in this foundation

- No production agent runtime or autonomous scheduler.
- No live credentials, tokens, keys, or secrets.
- No direct writes to canonical `main`, production deployment, payments, contracting, hiring, or external binding commitments.
- No authority self-modification, self-approval, or self-provisioning.
- No claim of 24/7 uptime. Continuous availability requires monitored, funded compute and durable storage.

## Commissioning gate

The agent remains **uncommissioned** until a human authority explicitly approves a versioned policy, service identity, installation scope, runtime environment, data retention policy, and test evidence. A merge of this proposal is not an authorization to activate it.
