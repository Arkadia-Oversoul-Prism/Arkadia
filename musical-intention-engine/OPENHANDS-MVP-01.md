# OpenHands Directive · MIE MVP-01

PROJECT := MUSICAL INTENTION ENGINE
CODENAME := MIE
MODE := AUTONOMOUS SEQUENTIAL BUILD
PASS := MVP-01
AUTHORITY := HUMAN
AGENT := OPENHANDS

## Objective

Build the first complete experimental MVP of a mobile-first musical-intention instrument inside the Arkadia Prism repository.

North star:

> Build the shortest possible interface between musical intention and manipulable sound.

Core thesis:

> We are not building a smaller DAW. We are investigating what a musical instrument becomes when computation can understand musical intention.

## Existing state

A Gate 01 capture prototype has been exercised on a real Android phone. Observed loop:

HUMAN → HOLD TO CAPTURE → RAW AUDIO CLIP → PLAYBACK → KEEP/CHANGE

The next causal boundary is:

RAW CAPTURE → MUSICAL INTERPRETATION → MUSICAL OBJECT → USER-DIRECTED TRANSFORMATION → AUDIBLE RESULT

## Operating law

Continue autonomously through the authorized gates when the current step has been implemented, tested, evidenced, committed, and the next step is technically eligible.

When uncertain:

INSPECT → MEASURE → IMPLEMENT THE SMALLEST REVERSIBLE OPTION → TEST → RECORD.

Do not fabricate test results, user behavior, provider capability, or verification.

Stop only for a genuine hard stop: missing required credential, destructive scope expansion, impossible dependency/platform constraint, unresolved contradiction, unisolated blocking failure, or violation of a core invariant.

## Mutation boundary

Authorized:
- `musical-intention-engine/`
- relevant MIE Android projection code
- tests
- local fixtures
- model/provider abstraction needed by MIE
- build configuration needed by MIE

Not authorized:
- unrelated Arkadia surfaces
- SolSpire production architecture
- identity/control-plane semantics
- production deployment
- payments/social/marketplace/distribution
- irreversible architectural expansion without a recorded decision

Use Prism's engineering discipline, but do not import its architecture wholesale into MIE.

## Product boundaries

Do not build a social feed, marketplace, publishing system, full DAW timeline/mixer/plugin ecosystem, subscription layer, generative-song feed, or generic AI chat as the primary interaction.

The MVP remains an instrument.

## Architecture

HUMAN
→ INTENTION
→ CAPTURE
→ INTERPRETATION
→ MUSICAL OBJECT
→ TRANSFORMATION
→ RENDERING
→ SOUND

Provider boundary:

MusicalInput → Interpreter → MusicalObject → Transformer → Renderer

The intelligence provider is replaceable.

## Autonomous gate sequence

### MVP-GATE-00 · RECONNAISSANCE

Inspect the repository and locate the current Gate 01 implementation or establish the verified absence of it.

Record:
- framework/runtime
- package manager
- current routes/screens
- capture implementation
- audio handling
- tests
- build commands
- Android integration seam
- existing documentation
- limitations

Update `musical-intention-engine/BUILD-STATE.md`.

Do not rebuild working infrastructure.

### MVP-GATE-01 · CAPTURE HARDENING

Harden the existing capture primitive:
- permission handling
- lifecycle
- cancellation/recovery
- duration
- playback
- errors
- mobile compatibility
- no silent failure

Measure TTCS.

### MVP-GATE-02 · CAPTURE CLASSIFICATION

Investigate:
- melody
- rhythm
- spoken musical instruction
- sustained sound
- ambiguous/mixed

Return type, confidence, and evidence.

### MVP-GATE-03 · MUSICAL OBJECT

Implement the smallest inspectable MusicalObject preserving source, interpretation, representation, provenance, confidence, timestamp, and ancestry.

Update the object specification from evidence.

### MVP-GATE-04 · FIRST TRANSFORMATION

Implement exactly one meaningful transformation selected from evidence.

Preserve the original and provide comparison.

### MVP-GATE-05 · CHANGE LOOP

Implement:

CAPTURE → OBJECT → CHANGE → RESULT → COMPARE → KEEP/REVISE

Do not replace this with a chatbot.

### MVP-GATE-06 · OBJECT CONTINUITY

Implement explicit source/parent/transformation lineage.

Original must remain recoverable.

### MVP-GATE-07 · MOBILE INSTRUMENT

Test on a real Android device. Optimize for thumb reach, large targets, low latency, audio feedback, clear state, interruptions, and headphones/speaker use.

Optimize for actual use, not screenshots.

### MVP-GATE-08 · MEASUREMENT

Establish protocols for:
- TTMI: Time To Musical Idea
- TTCS: Time To Captured Sound
- ITS: Interactions To Sound
- IP: Intent Preservation
- RC: Recovery Cost
- DWM: Depth Without Mode-Switching

Never invent numerical results.

### MVP-GATE-09 · EXPERIMENT RUN

Run:
- hum a melody
- tap a rhythm
- speak a musical instruction
- repeat one idea after transformation

Record input, intention, capture, interpretation, object, transformation, result, failure, recovery, time, actions, observation, and next question.

Use PASS/PARTIAL/FAILED/UNKNOWN honestly.

### MVP-GATE-10 · INTEGRITY REVIEW

Ask:
1. Is this still an instrument?
2. Did we accidentally build a DAW?
3. Did AI become the author?
4. Can the original thought be preserved?
5. Can every transformation be traced?
6. Is interpretation replaceable?
7. Is mobile still primary?
8. Is the loop faster than the conventional workflow being compared?
9. What remains unknown?
10. What should NOT be built next?

## Commit discipline

Each meaningful gate produces implementation, tests, evidence, documentation, and a focused commit.

Do not create one enormous final commit.

Use:
INSPECT → HYPOTHESIS → SMALLEST REVERSIBLE CHANGE → TEST → RUN → OBSERVE → DOCUMENT → COMMIT → CHECK GATE → ADVANCE

## Human boundary

The agent executes implementation and evidence collection.

The human retains authority over authorization, architectural direction, merge, deployment, and product-hypothesis continuation unless an explicit repository control-plane authorization says otherwise.

## Hard-stop record

When blocked, stop mutation and record:
BLOCKER / WHY / VERIFIED / NOT VERIFIED / SAFE OPTIONS / NEXT EXPERIMENT

## Success

MVP-01 succeeds only when a real person can:

have a musical thought → capture it on a phone → hear a representation → manipulate it → hear the change → preserve the original → repeat the loop quickly.

The critical moment:

> "I just hummed/tapped something, and now I can actually play with it."

Begin with MVP-GATE-00.
