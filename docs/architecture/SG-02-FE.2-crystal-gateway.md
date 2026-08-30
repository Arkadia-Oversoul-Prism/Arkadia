# SG-02-FE.2 — Crystal Gateway / Grove Chamber Interaction

## Purpose

Recover the strongest interaction mechanics from the archived Encyclopedia Galactica without restoring its mythic knowledge authority.

## Reused interaction primitives

- spatial gateway as the primary exploration surface;
- domain nodes arranged around a central Grove locus;
- explicit exploration state;
- persistent local exploration state;
- entry from domain → capability detail;
- return path to the broader capability map.

## Deliberately not restored

- mythic 12-chamber ontology;
- Encyclopedia Galactica as a knowledge authority;
- historical chamber content as canonical curriculum;
- autonomous generation of exercises or evidence;
- replacement of Knowledge OS source authority.

## Current mapping

```text
Crystal Gateway        → Spiral Grove Gateway
Crystal chamber        → A.I.S. capability domain
Chamber state           → Grove domain exploration state
Historical Codex        → Knowledge OS (canonical authority)
Historical progression  → LearnerCapabilityState
```

## State contract

The gateway currently persists only the selected domain's exploration state under:

`arkadia.spiral-grove.domain-state.v1`

Allowed gateway states:

- `dormant`
- `exploring`
- `integrated`

No learner evidence is written by this UI. `LearnerCapabilityState` remains the typed progression projection supplied by the capability layer.

## SG-02 boundary

This pass is interaction and navigation only. It does not create LearningPath, Exercise, or Evidence orchestration. Those remain downstream work for SG-03 and subsequent evidence architecture.
