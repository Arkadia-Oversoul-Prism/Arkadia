# Arkana Signal Fabric v1.0

**Status:** ARCHITECTURAL CONTRACT  
**State:** Frozen for implementation planning  
**Scope:** Arkana input/capture boundary, multimodal evidence objects, provenance, routing, and generated-media lineage  
**Authority:** Human sovereign decision remains outside the signal layer

## 1. Purpose

The Arkana Signal Fabric defines a canonical boundary between incoming information and the Arkana runtime.

The governing rule is:

> **Deriving meaning must never destroy the signal from which that meaning was derived.**

Arkana therefore does not receive only a prompt. It receives a machine-readable evidence package containing, where available:

1. the preserved source signal or a durable reference to it,
2. normalized streams derived from that source,
3. interpretations with explicit uncertainty,
4. contextual candidates and references,
5. provenance describing how each derivative was produced,
6. routing metadata describing what the runtime is permitted to consume for a particular operation.

MIE is the first experimental precedent for this contract.

---

## 2. Architectural boundary

The canonical flow is:

```text
CAPTURE
   ↓
NORMALIZE
   ↓
INTERPRET
   ↓
ROUTE
   ↓
ARKANA RUNTIME
   ↓
REASON / MEMORY / TOOLS
   ↓
GENERATE
   ↓
TEXT / VOICE / AUDIO / OTHER MEDIA
```

The signal layer is not the reasoning engine, memory system, or autonomous authority layer.

It is an evidence boundary.

### 2.1 Capture

Acquire the source event as faithfully as practical.

Examples:

- microphone audio,
- typed text,
- image/frame,
- uploaded file,
- device event,
- tool result,
- application state change.

Capture must preserve enough information to establish what entered the system.

### 2.2 Normalize

Convert source-specific formats into canonical machine-readable structures without replacing the source.

Normalization may add:

- timestamps,
- duration,
- hashes,
- sample metadata,
- segmentation,
- modality labels,
- stable IDs.

### 2.3 Interpret

Derive useful machine-readable meaning.

Interpretation may include:

- transcript,
- language,
- speech segments,
- pitch/prosody,
- acoustic features,
- visual detections,
- entities,
- intent candidates,
- references,
- semantic candidates.

Interpretation is never silently upgraded into fact.

### 2.4 Route

Select the evidence relevant to the current operation.

Routing is an information-access decision, not an evidence rewrite.

A route may expose a subset of streams while retaining a pointer to the complete event.

---

## 3. Canonical Arkana Signal Object

The canonical object is modality-neutral at the envelope level.

```json
{
  "schema": "arkana.signal",
  "schema_version": "1.0",

  "id": "sig_...",
  "session_id": "session_...",
  "created_at": "2026-10-05T00:00:00Z",

  "source": {
    "type": "microphone",
    "modality": "audio",
    "format": "audio/wav",
    "duration_ms": 2840
  },

  "raw": {
    "asset_ref": "asset_...",
    "sha256": "...",
    "sample_rate": 48000,
    "channels": 1
  },

  "streams": {
    "speech": {},
    "prosody": {},
    "acoustic": {},
    "timing": {},
    "language": {}
  },

  "interpretation": {
    "transcript": {},
    "intent_candidates": [],
    "entities": [],
    "references": [],
    "confidence": {}
  },

  "context": {
    "candidate_refs": [],
    "context_refs": []
  },

  "provenance": {
    "derived_from": [],
    "processor": "processor-id",
    "processor_version": "version",
    "model": "model-id",
    "model_version": "version"
  },

  "integrity": {
    "raw_preserved": true,
    "interpretation_is_derived": true
  }
}
```

### 3.1 Required invariants

Every valid signal object must satisfy:

- `id` is stable and unique.
- `session_id` identifies the interaction/session context.
- `created_at` is an explicit timestamp.
- `source` identifies the originating modality.
- A source object must have either a durable `raw.asset_ref` or an explicit reason why raw preservation is impossible.
- Derived information is distinguishable from source evidence.
- Every model-produced interpretation records provenance.
- Confidence values do not imply truth.
- Unknown or unresolved values remain unknown.
- Derivatives retain linkage to their source object.

---

## 4. Evidence versus interpretation

The fabric distinguishes four epistemic classes:

| Class | Meaning | Example |
|---|---|---|
| SOURCE | directly captured/received | WAV asset, uploaded image |
| DERIVED | mechanically or model-derived | transcript, pitch contour |
| CANDIDATE | unresolved possibility | intent candidate, target candidate |
| CONTEXT | separately retrieved information | project/file/thread reference |

These classes must not collapse into one another.

### 4.1 Uncertainty rule

A field that cannot be established must not be fabricated.

Preferred representation:

```json
{
  "target": {
    "status": "unknown",
    "value": null,
    "candidates": [
      {"ref": "audio_001", "confidence": 0.42},
      {"ref": "audio_002", "confidence": 0.31}
    ]
  }
}
```

Not:

```json
{"target": "audio_001"}
```

unless the evidence actually resolves that target.

This is the signal-layer application of the Arkadia rule:

> **Where evidence stops, the claim stops.**

---

## 5. Confidence semantics

Confidence is attached to a proposition or derivative, not to the person.

Examples:

- transcript confidence,
- segment confidence,
- language classification confidence,
- intent-candidate confidence,
- entity-link confidence,
- reference-resolution confidence.

The system must not encode inferred emotional state as a factual user attribute.

If acoustic/prosodic analysis produces an emotion-like signal, its schema must make the epistemic status explicit:

```json
{
  "valence_candidate": {
    "value": 0.31,
    "confidence": 0.28,
    "status": "uncertain_derived_signal"
  }
}
```

No downstream component may silently rewrite this as:

```text
"user is happy"
```

---

## 6. Signal Fabric

The Signal Fabric is the collection and routing layer around Signal Objects.

### 6.1 Initial modalities

```text
VOICE
TEXT
VISION
FILE
TOOL_RESULT
SYSTEM_EVENT
DEVICE_EVENT
APPLICATION_STATE
```

### 6.2 Example expansion

```text
                    ARKANA SIGNAL FABRIC
                             │
          ┌──────────────────┼──────────────────┐
          ↓                  ↓                  ↓
        HUMAN             ARTIFACT           SYSTEM
          │                  │                  │
     voice / text       files / images      tasks / apps
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
                       SIGNAL OBJECT
                             ↓
                         ROUTER
                             ↓
                       ARKANA RUNTIME
```

The fabric does not require every modality to exist at once.

A modality may be absent, unavailable, or intentionally withheld.

---

## 7. Routing contract

Routing produces an evidence package for a specific runtime operation.

A route must preserve:

- source object ID,
- selected stream IDs,
- provenance,
- confidence,
- unresolved states,
- access restrictions.

A route may omit raw payload bytes for efficiency while retaining a durable reference to the raw source.

The route must never convert:

```SOURCE → FACT
```

or:

```CANDIDATE → RESOLVED
```

merely because a downstream model cannot reason conveniently over uncertainty.

---

## 8. Agent reasoning boundary

Arkana receives an evidence package, then reasons over it.

Conceptually:

```text
SIGNAL OBJECT
     │
     ├── source evidence
     ├── derived streams
     ├── candidate interpretations
     ├── context references
     └── provenance
             │
             ↓
        ARKANA RUNTIME
             │
       ┌─────┼─────┐
       ↓     ↓     ↓
    reason memory tools
```

The runtime may ask for additional context.

Additional retrieval creates new evidence/context references. It does not mutate the original signal object.

---

## 9. Generated media is also an object

Arkana output is not merely an ephemeral string.

Generated artifacts should eventually follow the same lineage model:

```text
INPUT SIGNAL
     │
     └── interpretation
            │
            └── reasoning
                   │
                   └── generation intent
                          │
              ┌───────────┼───────────┐
              ↓           ↓           ↓
            TEXT        VOICE       AUDIO
```

A generated-media object should record at minimum:

- `id`
- `derived_from[]`
- `generation_intent`
- `content_ref` or asset reference
- `processor`
- `model`
- `created_at`
- relevant generation parameters
- provenance links

This generalizes the MIE lineage pattern:

```text
ORIGINAL
   │
   └── OCTAVE UP
          │
          └── REVISED
```

into agentic media lineage.

---

## 10. Audio generation model

Voice, music, and sound are sibling output modalities.

A future audio-generation request can use a canonical intent envelope:

```json
{
  "schema": "arkana.audio_generation",
  "schema_version": "1.0",
  "id": "gen_...",
  "derived_from": ["sig_..."],
  "intent": "spoken_response",
  "voice": {
    "identity": "arkana",
    "style": "conversational",
    "energy": 0.62,
    "pace": 0.94
  },
  "content": "...",
  "layers": [],
  "provenance": {
    "reasoning_ref": "reason_...",
    "processor": "audio-generator",
    "model": "model-id",
    "model_version": "version"
  }
}
```

The first implementation does not require music generation.

The contract simply prevents speech, music, and sound from becoming unrelated architectures later.

---

## 11. Thread/session relationship

A signal object belongs to a session but is not itself a conversation message.

This distinction matters.

```text
SESSION
 ├── SIGNAL 001
 ├── SIGNAL 002
 ├── TOOL EVENT
 ├── SIGNAL 003
 └── GENERATED RESPONSE
```

Conversation/thread views may reference these objects.

The evidence layer remains independently addressable.

This allows Arkana to inspect the underlying event graph without forcing every event into chat-message semantics.

---

## 12. Human authority and governance

The Signal Fabric has no autonomous authority.

It may:

- capture,
- normalize,
- derive,
- classify,
- preserve,
- route,
- expose uncertainty.

It may not independently establish consequential authority.

Human authority remains upstream of consequential commitments and downstream of interpretation where a human decision is required.

The canonical governance rule remains:

> **Human decides. Nodes execute.**

The signal layer must therefore distinguish:

```interpretation ≠ authorization
capability ≠ permission
candidate ≠ fact
prediction ≠ decision
```

---

## 13. Privacy and retention boundary

Raw signal can be highly sensitive.

The architecture therefore treats raw preservation as a capability subject to explicit retention/access policy, not as permission to harvest everything.

Required design constraints:

- raw assets need durable identity and access control,
- derived streams inherit source sensitivity unless explicitly downgraded,
- emotional/prosodic inference must not become a hidden user profile,
- retention must be inspectable,
- deletion must propagate to derived artifacts according to policy,
- provenance must survive without unnecessarily retaining sensitive payloads.

The system should prefer references and hashes over unnecessary duplication of raw media.

---

# ARKANA SIGNAL GATE 01

## Objective

Prove the smallest complete end-to-end signal path.

### Input

Speak into a supported device microphone.

### Capture

Persist the original audio asset.

### Derivation

Produce:

- transcript,
- timestamp,
- duration,
- speech segments,
- pitch/prosody data where available,
- confidence values,
- intent candidates.

### Object

Create one valid `arkana.signal` object.

### Agent

Provide Arkana:

1. raw audio reference,
2. structured interpretation,
3. provenance,
4. unresolved values.

### Response

Produce:

- text response,
- generated voice response where a verified generation provider is available.

### Provenance

Record:

```text
input
  ↓
signal object
  ↓
interpretation
  ↓
context/reasoning
  ↓
generation
  ↓
response artifact
```

## Gate exit criteria

Gate 01 is closed only when all of the following are device-verifiable:

- [ ] original audio is actually captured,
- [ ] original audio remains retrievable,
- [ ] one canonical Signal Object is created,
- [ ] transcript is linked to the Signal Object,
- [ ] at least one non-text stream is represented,
- [ ] confidence is represented explicitly,
- [ ] unresolved references remain unresolved,
- [ ] Arkana receives structured signal data rather than transcript-only input,
- [ ] Arkana can produce a response from that evidence package,
- [ ] generated voice is actually produced and playable,
- [ ] response lineage points back to the input Signal Object,
- [ ] raw evidence and interpretation can be inspected separately.

## Explicit non-goals for Gate 01

Do not require:

- vision,
- live continuous listening,
- wake-word infrastructure,
- autonomous actions,
- music generation,
- ambient generation,
- emotional-state claims,
- long-term profiling,
- cross-device synchronization.

Gate 01 proves the boundary, not the whole platform.

---

# Implementation order

1. Freeze this contract.
2. Add the machine-readable schema.
3. Add runtime validation.
4. Identify the current Arkana voice/capture boundary.
5. Adapt capture to emit Signal Objects before transcript-only routing.
6. Pass structured signal packages into the existing Arkana runtime.
7. Add generated-voice output as a lineage-bearing artifact.
8. Device-verify Gate 01.
9. Only then generalize the fabric to text, vision, files, and system events.

**Important:** MIE remains an experimental sensor laboratory. Its DAW trajectory is paused at this architectural boundary; its capture, object, provenance, and lineage patterns are retained as precedent rather than duplicated into a second unrelated subsystem.
