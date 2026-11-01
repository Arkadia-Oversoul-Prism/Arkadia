# GOV-01 — Conditional Weaver Merge Authority

**Status:** Proposed governance amendment; not effective until human-reviewed and merged.
**Authorization source:** Explicit human authorization in the ChatGPT conversation on 2026-11-02.
**Authorization revision:** ARKADIA ENGINEERING LAB — WEAVER HOURLY BOUNDED EXECUTION CONTRACT, RECONCILIATION EDITION, revision date 2026-10-28.
**Effective date:** On human merge of this dedicated governance PR. No retroactive authority is claimed.
**Base:** `fb1d03e454853157561a86e2ed2e0c01df6c869d` (live `main` at branch creation).
**Branch:** `governance/weaver-conditional-merge-authority-01`.

## Scope authorized

- Amend `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` to establish conditional Weaver merge authority under M1–M13.
- Amend `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` to distinguish routine delegated merges from human-only decisions.
- Amend `AGENTS.md` to remove contradictory blanket prohibitions and bind agents to GOV-01.
- Add regression tests preventing reintroduction of blanket prohibitions or loss of retained safeguards.

## Preserved boundaries

No direct push to `main`; no force-push or protection bypass; required checks/reviews/approvals remain mandatory; no waiver of M1–M13; no OpenHands merge authority; no merge of this governance amendment by Weaver; no deployment/configuration change; no product or production acceptance; no lane ownership change; no change to the one-open-PR-per-lane constraint.

## Policy summary

Weaver may merge an existing PR targeting canonical `main` only when all applicable M1–M13 criteria are freshly and affirmatively verified immediately before merge. Unknown, stale, contradictory, or missing evidence means no merge. Human-only authority remains over constitutional, identity, authority-model, K15/K3, approval-enforcement, scope-expansion, sovereign security/privacy, deployment/configuration, and acceptance decisions.

This record documents authorization and intended scope. It is not evidence of test execution, merge, deployment, or acceptance.
