# ARKANA SIGNAL GATE 02 — Runtime Integration

**State:** IMPLEMENTED, pending verification
**Boundary:** Signal Object → existing Arkana Commune runtime
**Authority:** Human authority remains outside the signal layer

## Objective

Prove that the Signal Fabric is not a parallel chatbot. A canonical Signal Object must be able to enter the existing Arkana conversation/runtime seam without replacing the established text path.

## Change

`POST /api/commune/resonance` now accepts optional Signal Fabric fields:

- `signal`: canonical `arkana.signal` object
- `audio_base64`: preserved source audio when available
- `mime_type`: source audio MIME type

When `signal` is absent, the existing text-only runtime is unchanged.

When `signal` is present:

1. normal Arkana history remains available;
2. the Signal Object is appended as derived evidence;
3. raw audio may be appended as source evidence;
4. the runtime receives an explicit epistemic boundary;
5. SOURCE, DERIVED, CANDIDATE, and CONTEXT remain distinct;
6. unresolved values remain unresolved;
7. the response is produced through the existing Arkana Commune route.

## Architectural consequence

The Gate 01 proving ground no longer needs to remain the permanent runtime destination.

```text
VOICE
  ↓
ARKANA SIGNAL OBJECT
  ↓
/api/commune/resonance
  ↓
ARKANA RUNTIME
  ↓
MEMORY / RAG / CONTEXT / TOOLS
  ↓
RESPONSE
```

The old text route remains intact for compatibility.

## Gate 02 exit criteria

- [x] Signal Object accepted by existing Commune route.
- [x] Text-only Commune behavior remains available.
- [x] Raw audio can accompany the Signal Object.
- [x] Derived interpretation is explicitly labeled as evidence, not fact.
- [x] Human authority boundary is preserved.
- [ ] Live device verification.
- [ ] Production deployment verification after Vercel quota window.
- [ ] Regression verification of ordinary Arkana Commune conversation.

## Non-goals

- No autonomous action.
- No replacement of Knowledge OS.
- No replacement of thread/session semantics.
- No emotional profiling.
- No continuous microphone listening.
- No silent conversion of candidates into facts.

Gate 02 is therefore an integration seam, not a new authority path.