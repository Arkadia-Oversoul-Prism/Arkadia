# ARKADIA FRONTEND SEAM MAP + EXPERIENCE HIERARCHY MATRIX

**Status:** DIAGNOSIS ONLY · NO IMPLEMENTATION AUTHORIZED BY THIS ARTIFACT  
**Branch:** `aeas/frontend-brand-calibration`  
**Scope:** Solariun, SolSpire, Projects, Weaver, Engineering Lab, global/public shells, legacy compatibility, navigation, responsive composition  
**Evidence basis:** supplied mobile screenshots + current repository source + existing architecture/evidence records  
**Principle:** `DON'T KNOW IS ALLOWED. EVIDENCE DECIDES.`

---

## 0. Executive finding

The frontend's primary problem is **hierarchy collision**, not component quality.

The repository contains a substantial canonical architecture and, in several places, explicit prior reconciliation work intended to collapse duplicate shells. The current experience nevertheless exposes multiple layers of that architecture simultaneously.

The dominant pattern is:

```
global identity
  ↓
global/product switching
  ↓
workspace shell
  ↓
context/breadcrumb
  ↓
page/lens identity
  ↓
object/project context
  ↓
content
  ↓
persistent navigation
```

The target experience should instead behave like:

```
one shell
  ↓
one current location
  ↓
one dominant purpose
  ↓
one primary action set
  ↓
optional context
  ↓
progressive evidence / architecture
```

### Core diagnosis

> **Arkadia is exposing architectural layers as interface layers instead of compressing those layers into a coherent human experience.**

The frontend therefore feels larger than the product needs to feel.

---

# 1. Evidence baseline

## 1.1 Strongly observed from supplied screenshots

### Solariun Home

Observed simultaneously:

- identity/header chrome
- NovaNet / Solariun / SolSpire product rail
- Solariun header
- breadcrumb
- page kicker
- page title
- field heading
- workspace state
- identity context
- personal field
- attention
- active world
- current signal
- continuity
- synthesis
- decisions
- thread explanation
- Weaver destination
- Engineering Lab destination
- Knowledge OS destination
- persistent bottom navigation

### Engineering Lab

Observed simultaneously:

- page identity
- architectural description
- aggregate counts
- historical trajectory
- structural signals
- reference architecture
- authority/governance statements
- current runtime state
- agents
- model gateway
- external integrations
- assisted control plane
- multiple diagnostic cards

### Mobile condition

The narrow viewport makes the accumulated hierarchy visible as vertical cost. The issue is not only responsive styling. The mobile viewport exposes an underlying information-architecture problem.

---

## 1.2 Repository evidence

### Canonical shell intent already exists

Existing architecture evidence states that the outer experience should not own a duplicate navigation system and that the canonical Solariun shell should be the only workspace shell.

Relevant repository evidence:

- `docs/control-plane/evidence/solariun-x01-x12-canonical-recovery/EVIDENCE.md`
- `docs/control-plane/evidence/solariun-x01-x12-canonical-recovery/MAPPING.md`

That prior intent is important because the current diagnosis is **not proposing a new consolidation theory from scratch**. It is identifying where the current rendered/source composition still leaks seams.

### Current source still exposes multiple navigation constructs

`SolSpireExperience.tsx` currently defines:

- canonical header
- global Prism doors
- desktop sidebar
- mobile bottom navigation
- context bar
- search
- Arkana action
- identity display

`PrismInteriorShell.tsx` also defines a primary navigation rail with primary and secondary surfaces.

This creates a source-level seam between:

> **canonical workspace navigation**

and:

> **outer/product navigation**

even before individual screens are considered.

### Current application routing still contains historical vocabulary

`App.tsx` contains a large historical `View` union and compatibility mappings such as:

- `/codex` → knowledge
- `/knowledge-os` → knowledge
- `/loops` → tasks
- `/dashboard` → overview
- `/personal-echofeild` → observatory
- `/echofeild-matrix` → observatory
- `/settings` → settings
- `/account` → settings

This is good compatibility engineering, but it should not automatically become visible product taxonomy.

### SolariunConsole retains explicit legacy mapping

`SolariunConsole.tsx` contains:

```
LegacySection
LEGACY_MAP
field
codex
loops
projects
encyclopedia
goals
releases
jobs
traces
tools
system
```

Again, this can remain as migration infrastructure while disappearing from the human-facing hierarchy.

### Project Dashboard contains 11 peer tabs

Current project tabs:

1. Overview
2. Weaver
3. Knowledge
4. Conversations
5. Files
6. Repos
7. Tasks
8. Workflows
9. Memory
10. Events
11. Settings

The list mixes work, resources, execution, evidence/history and configuration in one navigation plane.

### Weaver is architecturally contextual

Repository evidence explicitly places `WeaverPanel` inside `ProjectDashboard`.

This supports the diagnosis that Weaver is better understood as a governed work mode within project/work context than as a competing top-level product destination.

### Engineering Lab is read-mostly/observational by design

Repository documentation describes Engineering Lab as an intelligence/observation layer over the existing substrate.

The UI therefore does not need to surface every observed substrate fact at equal prominence.

---

# 2. Experience hierarchy model

The frontend should have exactly one owner for each layer.

| Layer | Meaning | Current owner(s) | Diagnosis | Desired owner |
|---|---|---|---|---|
| L0 | Identity / account | global identity + Solariun identity | duplicated | global shell |
| L1 | Product family | Prism rail + global doors + outer shell | collision | global/product shell |
| L2 | Workspace | Solariun / SolSpire | partly clear | workspace shell |
| L3 | Current lens | Home / Projects / Knowledge / etc. | duplicated by nav + breadcrumb + heading | lens header |
| L4 | Object context | Project / workload / work item | nested | object context |
| L5 | Action | Create / Review / Run / Search / Continue | often below explanation | content surface |
| L6 | Evidence | events / provenance / architecture | overexposed | inspector/progressive disclosure |
| L7 | Configuration | Settings / account | mixed with activity | dedicated configuration path |

### Rule

**One layer, one owner.**

If two components claim the same layer, one is probably redundant.

---

# 3. Seam map

## S1 · Global shell + workspace shell

**Collision:** Arkadia/Prism identity with Solariun identity.

**Observed result:** multiple top headers.

**Severity:** CRITICAL.

**Failure mode:** user spends vertical space determining where the application begins.

**Disposition:** MERGE.

**Boundary rule:** the outer shell should establish identity and product family once. Solariun should establish workspace context once. Neither should repeat the other's job.

---

## S2 · Product rail + workspace navigation + bottom rail

**Collision:** three navigation taxonomies.

**Observed result:** user can reach the same conceptual destinations through multiple paths.

**Severity:** CRITICAL.

**Disposition:** MERGE / CONTEXTUALIZE.

**Rule:** one canonical primary navigation model. Secondary destinations belong behind context or progressive disclosure.

---

## S3 · Product taxonomy + architectural taxonomy

**Collision:** NovaNet, Solariun, SolSpire, Weaver, Engineering Lab, Knowledge OS, Radar, Projects etc. appear as peers.

**Observed result:** architectural concepts are mistaken for navigation destinations.

**Severity:** CRITICAL.

**Disposition:** CONTEXTUALIZE.

**Rule:** architecture should explain relationships between product surfaces, not become the product's entire navigation tree.

---

## S4 · Backend schema + UI hierarchy

**Collision:** workspace, workload, signal, continuity, synthesis, decisions, evidence and knowledge each become visible blocks.

**Observed result:** Home reads like a database schema rendered as cards.

**Severity:** CRITICAL.

**Disposition:** MERGE / PROGRESSIVE DISCLOSURE.

**Rule:** render user-relevant state first. Expose object/substrate details only when they help a decision.

---

## S5 · Truthful empty states + repeated empty-state cards

**Collision:** epistemic honesty with presentation density.

**Observed result:** many truthful “nothing recorded” messages combine into a visual impression of system emptiness.

**Severity:** HIGH.

**Disposition:** MERGE.

**Rule:** aggregate related empty conditions into one honest workspace state. Never fabricate activity.

---

## S6 · Mythology + operational language

**Collision:** Arkadia symbolic vocabulary with action vocabulary.

**Observed result:** users must decode terms before acting.

**Severity:** HIGH.

**Disposition:** CONTEXTUALIZE.

**Rule:** human action language first. Arkadia language enriches the experience beneath it.

---

## S7 · Operator audience + everyday user audience

**Collision:** architecture operator and product user share the same visual layer.

**Observed result:** both audiences receive too much and not enough simultaneously.

**Severity:** CRITICAL.

**Disposition:** PROGRESSIVE DISCLOSURE.

**Rule:** default surface answers the user's task. Operator evidence remains inspectable.

---

## S8 · Current architecture + legacy architecture

**Collision:** canonical routes with compatibility vocabulary.

**Observed result:** archaeological feeling.

**Severity:** HIGH.

**Disposition:** HIDE / ARCHIVE from primary UI.

**Rule:** compatibility routes remain resolvable but should not define current navigation labels.

---

## S9 · Workspace navigation + project navigation

**Collision:** Solariun navigation followed by project header followed by project tab rail.

**Observed result:** nested application inside workspace.

**Severity:** CRITICAL.

**Disposition:** MERGE / CONTEXTUALIZE.

**Rule:** project context should replace, not stack on top of, workspace orientation where appropriate.

---

## S10 · Weaver as destination + Weaver as work mode

**Collision:** Weaver appears as a peer destination while repository architecture places it inside ProjectDashboard.

**Observed result:** work execution feels like another application.

**Severity:** HIGH.

**Disposition:** CONTEXTUALIZE.

**Rule:** Weaver belongs where work is being governed/executed. It can have a strong identity without being an independent top-level navigation taxonomy.

---

## S11 · Engineering Lab observability + architecture documentation

**Collision:** runtime state, historical explanation, structural analysis and governance all appear together.

**Observed result:** Engineering Lab becomes an audit report.

**Severity:** HIGH.

**Disposition:** MERGE / PROGRESSIVE DISCLOSURE.

**Rule:** first viewport = current operational observation. Deep architecture = inspection layers.

---

## S12 · Semantic styling + decoration

**Collision:** meaningful color/sigil system with decorative density.

**Observed result:** everything appears highlighted.

**Severity:** HIGH.

**Disposition:** CALIBRATE.

**Rule:** semantic color should indicate state or action. Decorative use should not compete with semantic use.

---

## S13 · Mobile viewport + desktop information architecture

**Collision:** desktop density compressed onto narrow screens.

**Observed result:** excessive vertical cost and stacked navigation.

**Severity:** CRITICAL.

**Disposition:** MERGE / HIDE / CONTEXTUALIZE.

**Rule:** mobile receives a deliberate hierarchy, not a shrunken desktop.

---

## S14 · Evidence identifiers + human objects

**Collision:** IDs and technical metadata displayed alongside ordinary object names.

**Observed result:** product surfaces feel like admin/database consoles.

**Severity:** MEDIUM-HIGH.

**Disposition:** PROGRESSIVE DISCLOSURE.

**Rule:** IDs belong in inspectors, details, copy actions and evidence views unless they are required for the current task.

---

## S15 · Configuration + activity navigation

**Collision:** Settings appears as a peer beside work resources.

**Observed result:** configuration contaminates the work navigation plane.

**Severity:** MEDIUM.

**Disposition:** CONTEXTUALIZE.

**Rule:** settings should be available without competing with active work.

---

## S16 · “What matters now?” + complete subsystem inventory

**Collision:** prioritization promise with exhaustive state report.

**Observed result:** Home does not actually prioritize.

**Severity:** CRITICAL.

**Disposition:** MERGE / PROGRESSIVE DISCLOSURE.

**Rule:** Home must prioritize attention, work and next actions. The substrate inventory belongs elsewhere.

---

# 4. Experience Hierarchy Matrix

## 4.1 Solariun Home

| Surface | Current role | Evidence | Classification | Intended role |
|---|---|---|---|---|
| Identity header | identity | screenshot/source | MERGE | global identity |
| Product rail | product switching | screenshot/source | MERGE | global/product shell |
| Solariun header | workspace identity + actions | screenshot/source | KEEP, simplify | workspace shell |
| Breadcrumb | orientation | screenshot/source | KEEP, compress | current context |
| “What matters now?” | prioritization | screenshot | KEEP | primary purpose |
| Workspace bootstrap | state | screenshot | MERGE | one workspace status |
| Identity Context | identity | screenshot | PROGRESSIVE DISCLOSURE | context inspector |
| Personal Field | workspace state | screenshot | MERGE | current workspace summary |
| Attention | open-loop state | screenshot | MERGE | attention summary |
| Active World | workload | screenshot | MERGE | active work summary |
| Current Signal | signal | screenshot | MERGE | current signal |
| Continuity | activity | screenshot | MERGE | recent activity |
| Synthesis | synthesis | screenshot | PROGRESSIVE DISCLOSURE | optional insight |
| Decisions | proposals | screenshot | MERGE | action-needed state |
| Follow the Thread | architecture | screenshot | PROGRESSIVE DISCLOSURE | inspectable architecture |
| Weaver card | destination | screenshot | CONTEXTUALIZE | current work entry |
| Engineering Lab card | destination | screenshot | CONTEXTUALIZE | system inspection entry |
| Knowledge OS card | destination | screenshot | CONTEXTUALIZE | knowledge entry |
| Bottom navigation | primary navigation | screenshot/source | MERGE | one canonical mobile rail |

### Home target

```
HOME

What matters now?

[dominant current state]

[1–3 primary actions]

[active work, if any]

[recent continuity, if useful]

[inspect architecture]
```

The Home page should not enumerate every substrate primitive merely because each primitive exists.

---

# 5. Solariun global shell

## Current layers

1. outer identity
2. Prism/product doors
3. Solariun canonical header
4. sidebar or mobile rail
5. context bar
6. page heading

### Diagnosis

The existence of these layers is not inherently wrong. The problem is that several layers currently perform overlapping orientation functions.

### Classification

- Outer identity: KEEP, reduce
- Product doors: CONTEXTUALIZE or reduce to global switcher
- Solariun header: KEEP
- Sidebar: KEEP on desktop if it remains canonical
- Mobile rail: KEEP as the single mobile primary rail
- Context bar: KEEP, but remove redundant return/orientation content
- Page heading: KEEP
- Duplicate outer navigation: HIDE

---

# 6. Project experience

## Current architecture

```
Solariun shell
  ↓
Project selection
  ↓
Project header
  ↓
11-tab project navigation
  ↓
project panel
```

### Core problem

The project tab bar treats fundamentally different categories as peers:

**Work:** Weaver, Tasks, Workflows  
**Resources:** Files, Repos, Knowledge, Conversations  
**Evidence:** Events  
**State/history:** Memory  
**Configuration:** Settings  
**Summary:** Overview

This is a flattened ontology.

### Classification matrix

| Project surface | Current | Classification |
|---|---|---|
| Overview | primary summary | KEEP |
| Weaver | governed work mode | CONTEXTUALIZE |
| Knowledge | work resource | KEEP |
| Conversations | work resource | KEEP |
| Files | work resource | KEEP |
| Repos | work resource | KEEP |
| Tasks | work execution | KEEP |
| Workflows | work execution | KEEP |
| Memory | knowledge/context | MERGE with appropriate knowledge context |
| Events | evidence/history | PROGRESSIVE DISCLOSURE |
| Settings | configuration | MOVE OUT OF ACTIVITY NAV |

### Desired conceptual grouping

```
PROJECT

Overview
Work
  Weaver
  Tasks
  Workflows

Resources
  Knowledge
  Conversations
  Files
  Repos

Evidence
  Activity / Events

Settings
  Project configuration
```

This is not a proposal to add a new hierarchy. It is a proposal to stop pretending eleven unlike things are one kind of thing.

---

# 7. Weaver

## Architectural fact

Repository evidence places `WeaverPanel` inside `ProjectDashboard`.

That is the correct architectural anchor.

## Current experience problem

Weaver is visually promoted into the broader navigation taxonomy.

This creates a false implication:

> Weaver is another application.

The deeper truth is:

> Weaver is a governed work mode.

### Classification

- Weaver capability: KEEP
- Weaver project context: KEEP
- Weaver as peer global destination: HIDE / CONTEXTUALIZE
- Operator execution detail: PROGRESSIVE DISCLOSURE
- Authorization state: KEEP where decision-relevant
- Raw execution machinery: INSPECTOR

### Primary Weaver question

The surface should answer:

> **What work is being proposed, authorized, executed or verified?**

before answering:

> Which agent, gateway or internal mechanism is involved?

---

# 8. Engineering Lab

## Current conceptual layers

### Layer A: current system observation
- what exists
- what is running
- active agents
- gateway
- integrations

### Layer B: architecture history
- how the system arrived here
- structural signals
- patterns

### Layer C: governance
- authority boundary
- evidence
- control-plane relationship

All three are valid.

They should not be visually equal.

### Classification

| Surface | Classification |
|---|---|
| Current runtime | KEEP, primary |
| Active runs | KEEP, primary |
| Current substrate | KEEP, secondary |
| Structural signals | PROGRESSIVE DISCLOSURE |
| Historical trajectory | PROGRESSIVE DISCLOSURE |
| Governance boundary | KEEP, concise |
| Agent inventory | SECONDARY |
| Model gateway | SECONDARY |
| External integrations | SECONDARY |
| Full architecture evidence | INSPECTOR |
| Long diagnostic cards | COLLAPSE / PROGRESSIVE DISCLOSURE |

### Engineering Lab target

```
ENGINEERING LAB

Observe Arkadia's running substrate.

[Current state]
[Active work]
[Signals]

Inspect:
  Runtime
  Agents
  Architecture
  Governance
  Evidence
```

The Lab should feel like an instrument panel, not a printed forensic report.

---

# 9. Navigation taxonomy

## Current taxonomy collision

### Product level

- NovaNet
- Solariun
- SolSpire
- other Prism doors

### Solariun level

- Home
- Projects
- Commercial
- Opportunity Radar
- Knowledge
- Files
- Conversations
- Tasks
- Memory
- Weaver
- Observatory
- Engineering Lab
- Settings

### Project level

- Overview
- Weaver
- Knowledge
- Conversations
- Files
- Repos
- Tasks
- Workflows
- Memory
- Events
- Settings

### Legacy level

- Codex
- Loops
- Dashboard
- Knowledge OS
- Echo Field
- etc.

The problem is not that these concepts exist.

The problem is that the user is exposed to too many of these taxonomies at once.

---

# 10. Canonical navigation ownership

Freeze this as the architectural question before implementation:

| Navigation layer | Canonical owner | Non-owner |
|---|---|---|
| Product switching | global shell | Solariun |
| Workspace navigation | Solariun/SolSpire shell | outer wrapper |
| Project context | Project experience | global shell |
| Work execution | project/work context | global shell |
| Evidence inspection | contextual inspector | primary rail |
| Settings | configuration context | activity rail |
| Legacy compatibility | router | visible taxonomy |

### Rule

**No surface may introduce a second navigation system merely because it is technically capable of doing so.**

---

# 11. Visual hierarchy matrix

## Current hierarchy

```
EVERYTHING
  = important
```

This is produced by:

- gold labels
- teal labels
- violet labels
- uppercase micro-headings
- borders
- glow
- sigils
- status pills
- monospace metadata
- cards
- repeated headings

## Desired hierarchy

### Tier 1 · Primary

- current page
- dominant state
- primary action

### Tier 2 · Supporting

- current work
- relevant context
- recent state

### Tier 3 · Inspectable

- evidence
- architecture
- IDs
- internal states
- provenance
- implementation detail

### Tier 4 · Ambient

- Arkadia visual language
- sigils
- atmospheric motion
- decorative metadata

The current interface often renders Tier 3 and Tier 4 with the visual weight of Tier 1.

---

# 12. Typography hierarchy

## Current issue

Too many text roles compete:

- page title
- kicker
- architectural kicker
- state label
- metadata label
- object label
- category label
- question
- descriptive copy
- monospace state
- badge
- sigil

### Classification

**MERGE** typography roles.

Target should have approximately:

1. Page title
2. Section title
3. Body / action text
4. Metadata / state
5. Inspector / technical detail

The exact token implementation is secondary. The hierarchy is primary.

---

# 13. Iconography matrix

## Current observed vocabulary

- Unicode geometry
- sigils
- emoji
- letters
- custom marks
- text symbols
- arrows

### Problem

The same visual category is being represented by different icon grammars.

### Classification

| Icon use | Action |
|---|---|
| Primary product mark | KEEP |
| Semantic state indicators | KEEP, standardize |
| Navigation icons | MERGE into one icon grammar |
| Decorative sigils | REDUCE |
| Emoji as system icons | HIDE / replace |
| Legacy Unicode icons | ARCHIVE progressively |

### Principle

A symbol should either:

1. communicate meaning, or
2. establish brand atmosphere.

It should not pretend to be both when the user needs reliable navigation.

---

# 14. Copy hierarchy

## Current copy failure

The interface frequently explains the architecture before telling the user what they can do.

### Current pattern

```
architecture explanation
↓
state explanation
↓
metadata
↓
action
```

### Desired pattern

```
action / current need
↓
short explanation
↓
optional evidence
↓
deep architecture
```

### Copy rule

**Human action language is the default. Arkadia language is the enrichment layer.**

Examples:

| Internal | Primary UI | Inspector |
|---|---|---|
| WORKSPACE · LIVE | Workspace connected | LIVE / canonical workspace |
| CURRENT SIGNAL | Current signal | signal state/details |
| WORKEVENT | Activity / recorded event | WorkEvent |
| EVIDENCE | Evidence | evidence state/details |
| AUTHORITY | Who can approve | authorization boundary |

This preserves precision without forcing the user to decode the control plane.

---

# 15. Empty-state composition

## Current

Many separate statements:

- no attention
- no workload
- no signal
- no continuity
- no synthesis
- no decisions

## Target

One truthful aggregate state:

> **Nothing requires attention right now.**
>
> Workspace connected. No active workload, open decision or recent execution evidence is currently recorded.

Then actions:

- Open Projects
- Search Knowledge
- Review Weaver

Then optional:

> Inspect workspace state

This is **compression, not fabrication**.

---

# 16. Legacy surface disposition

Compatibility routes should remain functional where required, but their historical names should not continue to compete with canonical product vocabulary.

| Legacy concept | Current canonical destination | UI disposition |
|---|---|---|
| Codex | Knowledge | HIDE |
| Knowledge OS | Knowledge | MERGE / HIDE as competing label |
| Loops | Tasks | HIDE |
| Dashboard | Solariun Home | HIDE |
| Personal Echo Field | Observatory | HIDE |
| Echo Field Matrix | Observatory | HIDE |
| Account | Settings | MERGE |
| System | Settings / Engineering context | CONTEXTUALIZE |
| Jobs | Observatory / relevant work context | CONTEXTUALIZE |
| Traces | Observatory / evidence | CONTEXTUALIZE |
| Tools | Observatory / tools context | CONTEXTUALIZE |

Compatibility is infrastructure.

It is not automatically information architecture.

---

# 17. Screen-level hierarchy contract

Every canonical screen should answer these questions in order:

### 1. WHERE AM I?
One visible answer.

### 2. WHY AM I HERE?
One short sentence.

### 3. WHAT MATTERS NOW?
One dominant state.

### 4. WHAT CAN I DO?
One to three primary actions.

### 5. WHAT HAS HAPPENED?
Relevant recent state only.

### 6. WHAT CAN I INSPECT?
Evidence / architecture / identifiers.

If a screen cannot answer these without reading multiple cards, its hierarchy is not finished.

---

# 18. Keep / Merge / Contextualize / Progressive Disclosure / Hide / Archive matrix

## KEEP

- Arkadia visual identity
- Solariun / SolSpire distinction
- canonical workspace shell
- Home
- Projects
- Knowledge
- Files
- Conversations
- Tasks
- governed Weaver capability
- Engineering Lab capability
- Opportunity Radar
- truthful state model
- evidence model
- architecture inspector capability
- responsive design
- accessible interaction

## MERGE

- duplicate shell headers
- duplicate navigation layers
- repeated workspace status
- repeated identity context
- repeated empty states
- overlapping project/work metadata
- Memory where it duplicates Knowledge context
- account/settings navigation

## CONTEXTUALIZE

- Weaver
- Engineering Lab
- architecture language
- project resources
- WorkEvent
- evidence
- product switching
- Arkadia mythology
- object-level technical metadata

## PROGRESSIVE DISCLOSURE

- provenance
- IDs
- structural signals
- architecture history
- runtime internals
- agent details
- gateway details
- external integrations
- deep governance evidence
- historical compatibility

## HIDE FROM PRIMARY NAVIGATION

- Codex
- Loops
- Dashboard as a duplicate Home label
- Knowledge OS as a competing top-level label
- Echo Field legacy labels
- duplicate project/settings paths
- legacy product terminology

## ARCHIVE

- obsolete visual treatments
- duplicate navigation primitives proven to be superseded
- legacy labels no longer needed for user orientation
- decorative symbols that have no semantic role

---

# 19. Severity model

| Severity | Meaning |
|---|---|
| S0 | blocks understanding of the product |
| S1 | creates major navigation or hierarchy confusion |
| S2 | significant cognitive/visual noise |
| S3 | localized inconsistency |
| S4 | cosmetic refinement |

Current highest-priority seams:

### S0 / S1
- duplicate shell/navigation ownership
- Solariun Home hierarchy
- project nested navigation
- mobile navigation density
- operator/user audience collision
- legacy/current taxonomy collision

### S2
- typography proliferation
- iconography inconsistency
- metadata exposure
- repeated state labels
- visual decoration competing with semantics

### S3/S4
- individual spacing
- isolated icon polish
- micro-copy refinements
- animation tuning

**Do not start at S3/S4 while S0/S1 remains unresolved.**

---

# 20. What this means for implementation order later

This document does **not authorize implementation**.

When implementation is authorized, the sequence should be:

```
1. navigation ownership
2. shell consolidation
3. Home hierarchy
4. project hierarchy
5. Weaver contextualization
6. Engineering Lab hierarchy
7. mobile composition
8. typography/iconography reduction
9. copy calibration
10. progressive disclosure / inspectors
11. accessibility
12. final runtime verification
```

Not:

```
change colors
→ tweak cards
→ add animations
→ polish icons
→ discover navigation is still broken
```

---

# 21. Acceptance conditions for the future calibration pass

A screen is not considered calibrated merely because it looks cleaner.

It must demonstrate:

- one clear current location
- one canonical navigation owner
- one dominant purpose
- one clear primary action set
- no duplicate shell ownership
- no legacy vocabulary competing with canonical vocabulary
- backend capability remains discoverable
- architecture remains inspectable
- state remains epistemically honest
- empty states are compressed, not fabricated
- technical IDs are contextual
- mobile has deliberate hierarchy
- desktop does not expose unnecessary implementation topology
- operator detail is available without becoming default user chrome
- visual identity supports rather than competes with task completion
- no second persistence or memory system
- no invented runtime state
- no private data leakage

---

# 22. North star

> ## ARKADIA SHOULD FEEL SMALLER THAN IT ACTUALLY IS.
>
> The architecture may be enormous.
>
> The user's next decision should not be.

And:

> **The frontend should not merely decorate the substrate. It should make the substrate intelligible.**

The final test:

> **A new user should understand what Arkadia is before understanding Arkadia's mythology. An experienced user should then discover that the mythology is backed by a real architecture.**

---

# 23. Current diagnosis

### CONFIRMED

- hierarchy collision
- duplicated/overlapping navigation ownership
- excessive mobile vertical cost
- Home schema leakage
- project navigation flattening
- operator/user audience collision
- Engineering Lab report gravity
- legacy vocabulary leakage
- visual semantic overload

### STRONGLY INDICATED

- shell consolidation has not fully translated into perceived consolidation
- current canonical navigation taxonomy is not sufficiently singular
- progressive disclosure is underused
- visual identity has become too frequently explicit

### STILL REQUIRES RUNTIME INSPECTION

- actual interaction conflicts
- keyboard/focus behavior
- menu reachability
- hydration/runtime console behavior during navigation
- exact mobile touch-target failures
- scroll locking
- sticky-header collisions under every lens
- screen-reader hierarchy
- reduced-motion behavior
- loading/error state composition
- authenticated vs unauthenticated shell transitions

### NOT CLAIMED

This document does not claim that any individual component is technically defective merely because the composition is poor.

The current evidence points primarily to **composition and hierarchy**, not wholesale component invalidity.

---

## Final seam statement

Arkadia does not need more interface.

It needs **fewer competing explanations of the interface**.

The substrate is already large.

The next architectural act is compression.

**KEEP THE DEPTH.  
REMOVE THE ECHOES.  
MAKE ONE SYSTEM FEEL LIKE ONE SYSTEM.**

¯\\_(ツ)_/¯

**DON'T KNOW IS ALLOWED.  
BUT WE CAN FIND OUT.**
