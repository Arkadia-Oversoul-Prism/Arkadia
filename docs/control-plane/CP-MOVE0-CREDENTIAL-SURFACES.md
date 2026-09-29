# CP-MOVE0 — Credential Surface Boundary Contract

**Status:** DOCUMENTATION_ONLY / READ_ONLY / NORMATIVE VOCABULARY
**Scope:** Move 0 credential remediation state
**Mechanism:** NOT SELECTED
**Implementation:** NOT AUTHORIZED
**Runtime Mutation:** NONE
**Credential Mutation:** NONE
**History Rewrite:** NONE
**Move 0 Gate:** BLOCKED
**Move 1:** BLOCKED

## 0. Purpose

This contract records the semantic boundary exposed by the Move 0 credential remediation work.

It does not perform remediation, rotate credentials, rewrite history, provision identity, authorize Move 1, or establish a new security mechanism.

Its purpose is narrower:

> To prevent cleanliness at one credential surface from being represented as cleanliness at another credential surface.

The contract therefore distinguishes three materially different credential surfaces:

```text
CURRENT TREE
     ≠
ACTIVE RUNTIME
     ≠
HISTORICAL SURFACE
```

The distinction is architectural and applies independently of the tooling used to remediate each surface.

---

## 1. Three Credential Surfaces

### 1.1 Current Tree

The current repository tree is the set of credential-bearing files, values, references, templates, generated artifacts, and configuration presently reachable from the retained repository state.

Current-tree remediation may include:

- removing credential artifacts;
- removing hardcoded credential material;
- sanitizing templates and documentation;
- adding ignore protections against recurrence.

Current-tree cleanliness means only that the retained present surface has been cleaned to the extent verified.

It does **not** establish that:

- an active runtime credential has been invalidated;
- a provider-side credential has been rotated;
- historical Git objects are clean;
- previously exposed credentials are no longer usable.

### 1.2 Active Runtime

The active runtime surface is the credential state currently relied upon by deployed services and external providers.

Runtime remediation concerns whether credentials currently controlling or authenticating the running system remain valid, exposed, revoked, rotated, or otherwise safe.

A runtime credential may be rotated while historical copies remain in repository history.

Conversely, a historical credential may be removed from the current tree while the active credential remains unchanged.

Therefore:

```text
CURRENT TREE CLEAN
    ≠
ACTIVE RUNTIME SAFE
```

### 1.3 Historical Surface

The historical surface is the retained repository ancestry and object graph through which previously committed credential material may remain reachable.

Historical remediation is therefore distinct from current-tree deletion.

Deleting a file from the current tree does not, by itself, establish removal of the corresponding historical objects.

Therefore:

```text
FILESYSTEM / TREE REMOVAL
        ≠
HISTORY REMOVAL
```

Historical cleanliness requires independent verification of retained history and its reachable objects.

---

## 2. Permanent Invariants

The following distinctions are normative:

```text
CURRENT-TREE CLEANLINESS
        ≠
ACTIVE-CREDENTIAL VALIDITY
        ≠
HISTORICAL-CREDENTIAL CLEANLINESS
```

and:

```text
FILESYSTEM REMOVAL
        ≠
HISTORY REMOVAL
```

and:

```text
CURRENT CREDENTIAL REMOVAL
        ≠
CREDENTIAL INVALIDATION
```

and:

```text
CREDENTIAL ROTATION
        ≠
HISTORICAL EXPOSURE REMEDIATION
```

No one state may silently substitute for another.

---

## 3. Move 0 Remediation State

The current remediation record establishes the following state:

| Surface / condition | State |
|---|---|
| Current IMS credential artifact | CLEANED FROM CURRENT TREE |
| IMS artifact ignore rule | ESTABLISHED |
| IMS source hardcoded passwords | REMOVED |
| Current sovereign credential | ROTATED IN ACTIVE RUNTIME |
| Current `.env.example` credential surface | SANITIZED |
| Current security documentation | SANITIZED |
| Historical IMS credential objects | REMAIN IN HISTORY |
| Historical sovereign-key objects | REMAIN IN HISTORY |
| Historical Gemini-key objects | REMAIN IN HISTORY |
| IMS live-password rotation | PENDING CONTROLLED OPERATOR EXECUTION |
| Gemini provider rotation | PENDING PROVIDER-SIDE ACCESS |
| Safe Git history rewrite | BLOCKED BY AVAILABLE TOOLING |
| Final Move 0 gate | **BLOCKED** |
| Move 1 | **BLOCKED** |

This table records state. It does not grant authority to perform the outstanding operations.

---

## 4. Required Remediation Gates

Move 0 remains blocked until each applicable boundary is independently cleared.

### Gate A — Current Tree

Required condition:

```text
NO KNOWN ACTIVE CREDENTIAL MATERIAL
IN THE RETAINED CURRENT TREE
```

This gate concerns the present repository surface only.

### Gate B — Active Runtime

Required condition:

```text
ALL KNOWN COMPROMISED ACTIVE CREDENTIALS
INVALIDATED OR ROTATED
```

This gate requires the appropriate external provider or controlled operator execution path.

Repository edits alone do not satisfy it.

### Gate C — Historical Surface

Required condition:

```text
NO CREDENTIAL-BEARING OBJECTS OR REFERENCES
REMAIN REACHABLE THROUGH RETAINED HISTORY
```

This requires a safe history-remediation operation that preserves legitimate ancestry and is independently verified afterward.

Current-tree deletion does not satisfy this gate.

### Gate D — Re-audit

After remediation, the three surfaces must be evaluated independently and then together.

The final state must not be inferred from any single surface.

---

## 5. Boundary Decisions Recorded by Move 0

Three operations were deliberately not simulated or falsely completed.

### 5.1 No unsafe Firebase execution channel

The connected environment did not provide a sufficiently controlled execution path for the Firebase Admin credential required to rotate the exposed IMS passwords.

No second credential channel was introduced merely to make the gate appear green.

Required future condition:

```text
CONTROLLED OPERATOR EXECUTION
        ↓
IMS ROTATION
        ↓
INDEPENDENT VERIFICATION
```

### 5.2 No fabricated Gemini rotation

A provider-side credential rotation cannot be represented by replacing a deployment value with an arbitrary string.

The historical credential must be invalidated or rotated at the provider boundary, followed by deployment and runtime verification.

No fabricated replacement is treated as rotation.

### 5.3 No destructive history rewrite

A history-cleanup operation must remove credential-bearing historical objects while preserving legitimate repository ancestry to the extent required by the repository's governance boundary.

A destructive replacement of history that merely makes the visible state appear clean is not accepted as equivalent remediation.

Until a safe history-rewrite path exists, the historical surface remains unresolved.

---

## 6. Constitutional Sequence

The Move 0 boundary remains:

```text
CREDENTIAL REMEDIATION
        ↓
KNOWN-SAFE CREDENTIAL BOUNDARY
        ↓
RE-AUDIT
        ↓
MOVE 0 GATE
        ↓
ONLY IF PASSED
        ↓
ARCHITECT AUTHORIZATION
        ↓
MOVE 1
```

No credential remediation operation establishes Architect identity.

No current-tree cleanup establishes authorization.

No runtime rotation establishes historical cleanliness.

No historical rewrite establishes provider-side credential invalidation.

Each gate remains independently meaningful.

---

## 7. Prohibited Semantic Substitutions

The following substitutions are invalid:

```text
CURRENT TREE CLEAN
    → therefore HISTORY CLEAN
```

```text
RUNTIME ROTATED
    → therefore HISTORY CLEAN
```

```text
FILE DELETED
    → therefore CREDENTIAL INVALIDATED
```

```text
CREDENTIAL INVALIDATED
    → therefore HISTORICAL SURFACE CLEAN
```

```text
HISTORY REWRITTEN
    → therefore PROVIDER CREDENTIAL ROTATED
```

```text
REMEDIATION DOCUMENT EXISTS
    → therefore MOVE 0 PASSED
```

The record is evidence of state and decisions. It is not a substitute for the operations it records.

---

## 8. Relationship to Control Plane Semantics

This contract is intentionally narrow.

It does not create:

- a new identity system;
- a new authority system;
- a new provenance mechanism;
- a new mutation path;
- a runtime controller;
- an execution capability;
- an autonomous remediation agent.

It contributes vocabulary for observing and reasoning about credential boundaries.

The Control Plane may therefore represent:

```text
CURRENT SURFACE
ACTIVE RUNTIME
HISTORICAL SURFACE
```

as separate states without implying that one state proves another.

The contract preserves the broader Control Plane principle:

> A boundary is meaningful only when its state and authority are not silently inherited from an adjacent boundary.

---

## 9. Move 0 Closure Conditions

Move 0 may only advance from BLOCKED after a subsequent re-audit establishes, independently:

1. exposed IMS passwords have been rotated or invalidated through the appropriate controlled execution path;
2. the historical Gemini credential has been invalidated or rotated at the provider boundary;
3. the active runtime has been verified against the intended replacement credentials;
4. credential-bearing historical objects and references have been removed or otherwise remediated through a safe history operation;
5. legitimate repository ancestry required by governance has been preserved;
6. retained history has been independently scanned for credential-bearing material;
7. the current tree remains clean after remediation;
8. runtime authentication and provider-backed paths remain functional after rotation;
9. no outstanding credential boundary is being represented as complete merely because another boundary is clean;
10. the final Move 0 gate is explicitly re-evaluated.

Until those conditions are independently established:

```text
MOVE 0 = BLOCKED
MOVE 1 = BLOCKED
```

---

## 10. Non-Claims

This artifact does not claim:

- that all historical credentials are already removed;
- that all provider credentials are already rotated;
- that Move 0 has passed;
- that Move 1 is authorized;
- that Architect identity exists;
- that a WorkEvent exists;
- that Barnabas data has been ingested;
- that a history rewrite has occurred;
- that any credential mechanism has been selected;
- that the remediation is complete.

It records the opposite where applicable: the unresolved boundaries remain explicitly unresolved.

---

## 11. Authority and Change Boundary

This document is documentation-only.

Its existence does not authorize any credential operation.

Its existence does not authorize history rewriting.

Its existence does not authorize provider access.

Its existence does not authorize Move 1.

Any future operational action remains subject to its own authorization, execution, verification, and audit boundary.

```text
DOCUMENTATION
     ≠
AUTHORIZATION
     ≠
EXECUTION
     ≠
VERIFICATION
```

---

## 12. Source Record

Primary remediation state is recorded in:

`docs/security/MOVE0_CREDENTIAL_REMEDIATION.md`

Repository state recorded for this contract:

```text
HEAD: 2dc3e37568bc673e323ff7abbc1a0f6c0845168e
```

This contract is intentionally authored on an isolated architecture branch and does not itself advance the Move 0 gate.

---

## Final Invariant

> **Current-tree cleanliness does not imply active-credential safety, and active-credential safety does not imply historical cleanliness. Filesystem removal is not history removal.**

The present surface may be clean while the historical surface remains compromised.

The active runtime may be rotated while historical exposure remains unresolved.

A truthful control plane records all three states without collapsing them.

**Move 0 remains BLOCKED until the outstanding boundaries are independently remediated and re-audited.**
