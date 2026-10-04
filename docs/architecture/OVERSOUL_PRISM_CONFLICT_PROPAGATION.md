# Oversoul Prism Conflict Propagation and Resolution Boundaries

## Status

Research prototype. Non-governing. No production execution.

## Question

Once branch convergence identifies a contradiction, can that unresolved conflict travel through later lattice transformations without being silently normalized into a fact?

## Boundary model

`CONFLICT` is a first-class unresolved state. Later transformations may:

- preserve the conflict unchanged;
- add provenance about where the conflict was observed;
- attach new evidence without declaring the conflict resolved;
- make a resolution explicit only when a defined resolution operation has sufficient evidence and authority.

Later transformations may not:

- collapse competing values into one canonical fact;
- treat branch agreement as proof of truth;
- convert `CONFLICT` to `RESOLVED` merely by passing through another node;
- convert inference into evidence;
- create authorization or consequential side effects.

## Resolution boundary

Resolution is a separate operation from propagation.

Before resolution:

`claim → CONFLICT → UNKNOWN verification`

After a valid resolution:

`CONFLICT → RESOLVED + resolution evidence + provenance + explicit resolver`

The prototype deliberately does not define who may resolve a conflict in production. That authority remains UNKNOWN.

## Experiment

The probe creates a contradiction between two branch values, propagates it through later A01/A02/A03 layer transformations, and asserts that:

1. the conflict survives;
2. the competing values remain distinguishable;
3. verification remains UNKNOWN;
4. provenance records the propagation path;
5. no canonical claim is synthesized;
6. no authority is created;
7. an explicit resolution operation can change state only when resolution evidence is supplied.

## Architectural consequence

The lattice can carry unresolved disagreement as state. This makes conflict preservation a safety invariant rather than an error-handling afterthought.

**Propagation changes representation. Resolution changes epistemic state, and therefore requires an explicit boundary.**