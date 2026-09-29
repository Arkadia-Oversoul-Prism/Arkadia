# AEAS Frontend Brand + Experience Calibration

**STATUS:** AUTHORIZED TRAJECTORY / AUDIT-FIRST  
**MODE:** AEAS · EVIDENCE-DRIVEN · BOUNDED-CREATIVE  
**AUTHORITY:** HUMAN  
**SOURCE OF TRUTH:** CURRENT REPOSITORY + CURRENT RUNTIME  
**PRINCIPLE:** DON'T KNOW IS ALLOWED. EVIDENCE DECIDES.

## Objective

Bring Arkadia's frontend experience into visible alignment with the capability, coherence, and governance already present in the backend.

This is not a cosmetic redesign and not a request to make the interface "more futuristic." The goal is to make the existing system legible, calm, useful, trustworthy, and unmistakably Arkadia.

The frontend must communicate:
- one system rather than a collection of apps;
- continuity across identity, workspace, work, knowledge, authorization, execution, evidence, and verification;
- human authority over consequential action;
- the difference between live state, historical context, projection, and unknown state;
- enough capability to invite real use without exposing the user to the architecture's entire internal vocabulary at once.

## Current hypothesis

Repository inspection shows a mature visual language and substantial frontend composition: Arkadia public landing, Solariun and SolSpire shells, shared object grammar, identity persistence, workspace navigation, Opportunity Radar, Knowledge OS, Weaver visibility, Engineering Lab, Oracle/Arkana, and NovaNet/Nexus surfaces.

The working hypothesis is that the problem is not absence of components. It is experience composition, copy hierarchy, density, navigation hierarchy, visual repetition, and capability legibility.

This hypothesis is not a verdict. Runtime inspection must confirm or contradict it.

## Calibration dimensions

### 1. Brand coherence
Audit typography, semantic color usage, borders, shadows, glass, gradients, sigils, radii, spacing, animation, headings, terminology, empty/loading/error states, and public/authenticated transitions.

Arkadia, Solariun, SolSpire, Arkana, and NovaNet may have distinct roles, but they should still read as one system.

### 2. Content clarity
For every major screen answer:
1. Where am I?
2. What is this for?
3. What can I do here?
4. What is happening now?
5. What is known?
6. What is unavailable or unknown?
7. What is the next useful action?

Symbolic language may enrich atmosphere and meaning, but operational controls must remain plain enough to act on without decoding Arkadian terminology.

### 3. Visual noise
Audit and reduce duplicate navigation, competing headers, excessive micro-labels, repeated metadata, decorative borders without semantic purpose, excessive glow/blur, too many accent colors in one viewport, motion competing with task completion, nested cards without hierarchy, long explanation before the first useful action, and exposed internal IDs that do not help the user.

**Rule: If everything is highlighted, nothing is highlighted.**

### 4. Capability legibility
Audit the visible path:
**Identity → Workspace → Workload → Workstream → Authorization → Execution → WorkEvent → Evidence → Knowledge → Verification**

Do not expose the entire chain as a jargon wall. Progressively reveal the next meaningful state. Show what is active, what can happen next, what has been authorized, what actually ran, and what evidence exists.

### 5. Navigation architecture
Audit public shell, authenticated shell, NovaNet rail, Solariun/SolSpire lenses, secondary More surfaces, mobile navigation, profile/account controls, compatibility routes, and duplicate concepts such as Codex / Knowledge OS / Encyclopedia / Echo Field / Observatory.

Target:
**few stable anchors + contextual navigation + clear return path.**

The user should not need to understand Arkadia's historical evolution to navigate its current product.

### 6. Brand voice
Use a copy hierarchy:

**Layer 1: human action**
Open · Review · Search · Create · Continue · Run · Inspect · Verify

**Layer 2: product meaning**
Personal intelligence workspace · Enterprise operating console · Knowledge substrate · Governed execution · Opportunity intelligence

**Layer 3: Arkadia language**
field · thread · node · weave · continuity · sovereignty

Layer 3 enriches Layers 1–2. It does not replace them.

Avoid unexplained acronym density and internal labels when a shorter user-facing phrase communicates the same thing.

### 7. State honesty
Visually distinguish, where applicable:
live · synced · pending · proposed · authorized · running · ready for review · verified · historical · unavailable · unknown.

Do not use decorative confidence to make an unresolved system feel finished.

### 8. Responsive experience
Audit desktop and mobile separately. Check navigation reachability, first useful action, card density, sticky headers, bottom-navigation collisions, long labels, horizontal rails, object sheets, keyboard/focus states, touch targets, and safe-area spacing.

Mobile is not a compressed desktop.

### 9. Motion
Retain motion that communicates state, continuity, or transition. Reduce motion that exists only as atmosphere. Priority order:
1. state transition
2. navigation transition
3. attention cue
4. ambient decoration

Respect reduced-motion preferences.

### 10. Accessibility
Audit contrast, font size, focus visibility, semantic landmarks, button labels, keyboard navigation, dialog semantics, reduced motion, screen-reader names, and error association.

## Required audit sequence

### Pass A — inventory
Enumerate active frontend routes, shells, navigation systems, major components, and content surfaces. Classify each as public, authenticated, personal, enterprise, operator, legacy/compatibility, or archive.

### Pass B — first-impression audit
For each major entry surface record first visible message, first useful action, visual hierarchy, cognitive load, ambiguous terms, competing elements, and missing capability signals.

### Pass C — runtime observation
Use the actual deployed/current runtime where available. Do not infer visual quality from source alone. Capture desktop, mobile, loading, empty, error, authenticated, populated states, and core navigation transitions. If production cannot be verified, label the conclusion source-level or preview-level.

### Pass D — content calibration
Build:
| Surface | Current copy | User job | Problem | Proposed copy | Confidence |
|---|---|---|---|---|---|

Do not rewrite everything at once. Prioritize orientation, trust, navigation, and first-action copy.

### Pass E — visual calibration
Build:
| Surface | Noise source | Severity | Existing pattern | Recommended treatment | Evidence |
|---|---|---:|---|---|---|

Prioritize systemic fixes over one-off polish.

### Pass F — system-level design tokens
Identify repeated inline styles and visual primitives. Propose a minimal canonical vocabulary for surfaces, borders, text tiers, semantic accents, status states, spacing, radii, shadows, motion, and typography.

Do not introduce a second design system if the current CSS/grammar can be consolidated.

### Pass G — implementation
Only after the audit:
1. fix systemic primitives;
2. fix shell/navigation hierarchy;
3. fix high-traffic content;
4. fix individual surfaces;
5. remove obsolete visual duplication;
6. verify mobile;
7. verify accessibility;
8. verify runtime.

Prefer small compositional changes over wholesale rewrites.

## Acceptance criteria

Calibration is complete only when evidence shows:
- Arkadia reads as one system with distinct purposeful surfaces;
- the first useful action is obvious on major screens;
- navigation is understandable without internal architectural knowledge;
- backend capability is discoverable without unnecessary implementation detail;
- visual noise is materially reduced;
- copy is shorter and more human where action is required;
- symbolic language remains present but subordinate to usability;
- state labels are honest and consistent;
- desktop and mobile both have deliberate hierarchy;
- accessibility and reduced-motion behavior are preserved;
- no private data is exposed;
- no parallel persistence or memory system is introduced;
- source-level claims are not promoted to runtime claims without runtime evidence.

## Weaver operating rule

At every hourly pulse, continue from the highest-impact unresolved UX boundary.

If evidence is sufficient and the change is authorized:
**inspect → change → test → render → verify → record**

If evidence is insufficient:
**inspect → mark UNKNOWN → gather evidence**

If provider/runtime access blocks verification:
**record BLOCKED → preserve handoff → continue on other independently verifiable surfaces**

Never turn visual polish into a reason to weaken architecture, governance, privacy, or evidence boundaries.

## North-star test

A new user should be able to enter Arkadia and understand the product before understanding the mythology.

An experienced user should then discover that the mythology is backed by a real architecture.

**The frontend should not merely decorate the substrate. It should make the substrate intelligible.**
