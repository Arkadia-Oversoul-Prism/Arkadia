# CP-MOVE8 — Proposal Execution Preparation

**SCHEMA / NORMATIVE / TECHNOLOGY_NEUTRAL**

No automatic K15 invocation, no K3 transaction, no merge, no deploy, no alternate mutation path.

## Purpose

Close the semantic gap between **human acceptance of a proposal** and **human-authorized execution**.

> **ACCEPTED ≠ AUTHORIZED ≠ EXECUTED.**

Move 7 proved feedback cannot manufacture authorization.  
Move 8 provisions the next **preparation** layer only: explicit human decision on a proposal, and an optional **execution preparation package** that remains locked until a future, separately authorized PassSpec + K15 → K3 path exists and is invoked by the human.

## Distinctions

```
ACCEPTED            ≠ AUTHORIZED
DECLINED            ≠ WITHDRAWN
DECISION            ≠ EXECUTION
PREPARATION         ≠ PASS SPEC
PREPARATION         ≠ PATCH APPROVAL
PREPARATION         ≠ K15 INVOCATION
PREPARATION         ≠ K3 TRANSACTION
authorization_ref   ≠ PassSpec
execution_authorized = false   (always, in this move)
auto_merge          = false
auto_deploy         = false
auto_execute        = false
```

## Allowed state transitions (proposal)

From `UNDER_REVIEW` / `REVISION_REQUESTED` / `REVISED` / `DECISION_PENDING` / `PRESENTED`:

- Human records **ACCEPTED** or **DECLINED** (or **WITHDRAWN**) via authenticated decision endpoint.
- Decision writes `decision_ref` (decision event id) and may set `proposal_status`.
- Decision **must not** set `authorization_ref` to a live PassSpec.
- Decision **must not** set `execution_authorized=true` anywhere.

## Execution preparation package

A preparation record may be created only for a proposal in `ACCEPTED` state, and only for the subject owner.

Fields (vocabulary):

```
preparation_id
proposal_id
proposal_version
subject_ref
workspace_ref
status: PREPARED | SUPERSEDED | WITHDRAWN
execution_authorized: false   # fixed
auto_merge: false             # fixed
auto_deploy: false            # fixed
auto_execute: false           # fixed
pass_spec_ref: null           # Move 8 never binds PassSpec
k15_ref: null
k3_ref: null
notes
created_at
```

**Status PREPARED means “ready for a future human authorization step,” not “authorized to mutate the repository.”**

## Non-goals

- No call into Weaver K15 execution
- No call into K3 plan/implement/verify
- No automatic PassSpec construction
- No PatchApproval synthesis from ACCEPTED
- No Barnabas data ingestion
- No provenance frontier closure

## Gate

Implementation requires Moves 0–7 closed as applicable and explicit human authorization for Move 8.

Verification must prove:

1. Unauth → 401  
2. Decision ACCEPTED does not populate authorization_ref with executable authority  
3. Preparation always has execution_authorized=false  
4. Cross-subject isolation  
5. Prior surfaces intact  
6. No K15/K3 code path invoked by these endpoints  

`AUTHORED → IMPLEMENTED → VERIFIED → MERGED`
