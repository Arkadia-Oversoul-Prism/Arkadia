# CP102-G07 — COLLISION REGISTER

**Primary collision:** PassSpec treated as human authorization.

## Grounded state
The repository contains explicit semantics equivalent to **“Human authorization is the PassSpec”** and an execution path in which PassSpec/PatchApproval state can produce approval for the governed plan. This is a semantic collision because it collapses a structural execution envelope into human-origin authority.

## Secondary gaps
| ID | Finding | State |
|---|---|---|
| G07 | PassSpec → human authorization | 🔴 collision |
| G08 | Event-level human-origin provenance absent | 🔴 gap |
| G09 | Deliberate-origin evidence absent | 🔴 gap |
| G10 | First-class provenance state absent | 🔴 gap |
| G11 | Provenance-specific fail-closed boundary absent | 🔴 gap |
| G12 | Authority-event temporal semantics incomplete | 🟡 gap |
| G13 | Delegation lineage incomplete | 🟡 gap |
| G14 | Provenance contradiction semantics incomplete | 🟡 gap |
| G15 | Witness role without event-attestation path | 🟡 gap |
| G01 | Firebase identity boundary exists | 🟢 |
| G02 | Governance role vocabulary exists | 🟢 |
| G03 | Capability registry denies authority status | 🟢 |
| G04 | K15→K3 remains sole mutation route | 🟢 |
| G05 | Structural scope/hash/HEAD controls are strong | 🟢 |
| G16 | No alternate mutation path observed | 🟢 |
| G17 | No competing identity authority observed | 🟢 |

## Falsification state
- **F01 fires:** removing origin evidence would not remove the existing PassSpec authority dependency.
- **F02 would fire:** an additive provenance layer would not resolve the collision while PassSpec remains independently authoritative.
- **F03 remains a guard:** renaming approval semantics as provenance is not resolution.
- **F04 fires:** K3 semantics still contain PassSpec-as-human-authorization language.
- **F05 remains a guard:** successful execution cannot retrospectively create provenance.

## Resolution state
`UNRESOLVED`

No repair, mechanism selection, authorization redesign, or K15/K3 mutation has been performed by this arc.
