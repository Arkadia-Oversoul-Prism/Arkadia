# ARK-OPS-CONTINUOUS-001 — Continuous Reconciliation & Gap-Closure Contract

**Record status:** the sovereign's operating contract for the recurring reconciliation
automation, recorded here so a cycle can resume without conversational memory.
**This file grants no authority.** It records authority the sovereign already holds and
the bounds the sovereign placed on agents. Where it and a canonical governance document
disagree, the canonical document controls (see *Precedence*).

| field | value |
|---|---|
| `CONTRACT_ID` | `ARK-OPS-CONTINUOUS-001` |
| `REVISION` | 2026-11-22 |
| `SUPERSEDES` | ARKADIA ENGINEERING LAB — WEAVER HOURLY BOUNDED EXECUTION (rev. 2026-10-28) |
| `EXECUTION_MODE` | immediate execution + recurring hourly continuation |
| `CYCLE_CEILING` | 1800 s |
| `AUTHORITY` | human-governed, evidence-bounded, fail-closed |
| `MERGE_AUTHORITY` | **NONE** |
| `DEPLOY_AUTHORITY` | **NONE** |

Starting references, not proof of current state: repository
`Arkadia-Oversoul-Prism/Arkadia`, canonical branch `main`, production origin
`https://arkadia-qzu4.onrender.com` (Render service `arkadia-qzu4`), active app
`web/arkadia_console`, active foundation `lab/engineering_lab/`.
`SOURCE_OF_TRUTH` is live GitHub state, git history, verified test evidence and
governance records. Every identifier above must be re-derived each cycle.

## Precedence

- **Merge execution is human-only.** `AGENTS.md` GOV-03 and
  `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §9 are the canonical statements;
  `weaver/execution_adapter.py::ForbiddenMergeAdapter` is the runtime refusal boundary.
  This record restates that bound and creates no exception to it.
- This record does not amend, weaken or extend any governance document. A governance
  change requires its own review and a human merge.

## Revocations (§0.1 of the contract)

The superseded contract's grant of bounded merge authority is revoked in full. An agent
governed by this contract must not:

- merge any pull request — `main` is connected to production, so a merge is a release
  event;
- push to `main`, force-push, delete or rewrite canonical history, bypass branch
  protection or rulesets, or change production behaviour indirectly;
- treat a PR's approval, green checks, draft status or age as merge authorization;
- open a PR per lane, per hour, or to make the automation appear productive (the former
  four-lane scheme survives only as an edit-ownership boundary);
- claim a merge, deployment, ruleset, capability or remote delivery that live evidence
  does not confirm.

## Standing engineering authority (§2.1)

Within the revocations above, an agent may inspect and analyse the repository, reconstruct
implementation history, identify defects and stale contracts, implement ordinary
corrections within established architecture, refactor where behaviour and governance
boundaries are unchanged, add tests and observability, repair CI failures that are
evidence-supported, create isolated branches, maintain existing OpenHands-owned PRs,
synchronise an isolated branch non-destructively, close an OpenHands-owned PR only when it
is demonstrably obsolete, and continue unfinished work across cycles.

## Standing architectural decisions (§2.2)

Extend existing Arkadia systems rather than adding parallel replacements; preserve the
Engineering Lab and its interfaces; prefer small, composable, reversible changes; prefer
automated capability detection over manual disclosure; preserve existing user workflows
unless a defect is established; introduce no infrastructure, dependency, registry or
abstraction without demonstrated need; create no duplicate governance system; produce no
activity whose only purpose is to appear productive; claim no capability until
implementation and verification establish it. When several safe implementations exist,
choose the smallest maintainable one that closes the verified gap.

## Security and sovereignty (§2.3)

Human authority is final. The contract states that access does not imply authority.
The source directive was truncated at that sentence, so this record deliberately stops
there rather than reconstructing a boundary it did not receive; the canonical security and
sovereignty boundaries remain those in `SECURITY.md`, `AGENTS.md` and the ADRs.

## Cycle protocol

`RECONCILE FIRST → IMPLEMENT SECOND → VERIFY THIRD → PERSIST EVIDENCE FOURTH → REPEAT.`

Each cycle reconstructs live state (canonical `main` SHA, open/closed/merged/draft PRs,
branch ancestry, CI, reviews, governance documents, and any discrepancy between
documentation, implementation, tests and live configuration) before mutating anything. A
conflict between sources is preserved explicitly rather than silently resolved in favour of
whichever source permits progress.

A cycle that finds no new gap must still verify current state, inspect outstanding work and
name the next unresolved blocker. A cycle must not substitute a report for an available safe
implementation.

## Resumability

Every cycle ends with a deterministic next-action block — current state, evidence, blockers,
authorized action, forbidden actions and the exact completion condition — recorded in
`docs/control-plane/evidence/ark-ops-continuous-001-cycle-NN/EVIDENCE.md`. Per-cycle records
are the resumption surface; this file is the stable contract those records cite.
