# SG-02-FE.1A — Prism Route & Historical Architecture Recovery

## Current route topology

```text
Prism App shell
  └── view: nexus
       └── NexusPage
            ├── horizontal Nexus tab strip
            │    └── id: university / label: Spiral Grove
            └── activeTab === university
                 └── AISUniversity (legacy inline implementation)
```

The visible NovaNet/Nexus horizontal Spiral Grove tab is therefore **not** the standalone `SpiralGrovePage` route. The earlier SG-02-FE work updated the standalone page but did not replace the Nexus tab target.

## Canonical frontend target

`web/public_prism/src/pages/SpiralGrovePage.tsx`

This is the SG-02 capability-map implementation and is the intended canonical Grove surface.

## Historical Encyclopedia Galactica recovery

Historical commit `7849e5f09d2964418f9dfcde64b17e23abd86de0` introduced the Crystal Gateway model. The recovered implementation established:

- a dodecahedron/crystal as primary navigation;
- 12 chamber destinations;
- full-screen chamber worlds rather than dashboard cards;
- chamber progression states: `dormant`, `explored`, `integrated`;
- persisted chamber state in `localStorage`.

Historical commit `58611c75807a259dbd6c92084a6855449bf19b29` subsequently added reading progress, keyboard navigation, richer typography, and chapter indexing.

The mythic 12-chamber Encyclopedia was later deliberately archived in commit `d00767cb478bfb70e4e9695527513a46a582db9c`. The canonical Encyclopedia surface became the Knowledge/scrolls surface instead.

## Architectural decision

Do **not** restore the mythic Encyclopedia as the semantic authority. Reuse its interaction precedent only:

```text
EG Crystal Gateway / chamber interaction
                ↓
        Spiral Grove Map
                ↓
        A.I.S Capability Registry
                ↓
        Knowledge OS source authority
                ↓
        Learning Path Engine (SG-03)
                ↓
        Exercise → Evidence → LearnerCapabilityState
```

The Encyclopedia is historical interface precedent. Knowledge OS remains the canonical knowledge authority. The Capability Registry remains the canonical capability authority.

## Required authoritative integration

The Nexus tab must become:

`Nexus → Spiral Grove → recovered Grove interaction model → Capability Registry`

No second capability catalogue, no second route-specific registry, and no SG-03 learning-path logic should be introduced in this pass.

## Current implementation note

The repository currently contains the legacy inline `AISUniversity` implementation inside `NexusPage.tsx`. SG-02-FE.1A identifies this as the precise integration seam. The standalone `SpiralGrovePage` must replace this render target before the pass can be considered complete.
