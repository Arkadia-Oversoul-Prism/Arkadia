# Phase 4C — Boundary Experiments (Production)

**Status:** RUN — findings recorded for the consolidation decision
**Run against:** `arkadia-kw64.onrender.com` (production, commit `55f5ae8`)
**Method:** API-testable experiments executed via the proven `/api/commune/resonance`
spine with fresh `session_id`s per experiment. No fabrication — each result is the
actual production response. Experiments requiring an authenticated browser UI
(4, 5, 6, 7) are marked UNTESTABLE, not faked.

These experiments exist to *find where the architecture actually fails before
coding the surface consolidation*. The point is observed friction, not a
speculative build.

---

## Results

### EXP 1 — The Seed (capture → leave → retrieve) — ✅ PASS
- Capture: "I'm exploring whether AI data companies have a growing demand for
  specialised African-language datasets."
- Recall (same session, different surface context):
  `notes_retrieved: 1`, reply contained `african` + `data`.
- **Meaning:** the spine captures real work and retrieves it across surfaces.
  This is system memory, not interface memory.

### EXP 2 — Cross-Surface Continuity (Oracle → ReasoMate) — ✅ PASS
- Oracle anchor `AFRI-DATA-247`.
- ReasoMate (different surface context, same `session_id`):
  `notes_retrieved: 1`, `thread_id: 2`, anchor surfaced in reply.
- **Meaning:** re-confirms the Gate A thread jump. Continuity is
  interface-independent.

### EXP 3 — Knowledge Graph Formation — ⚠️ PARTIAL (the real finding)
- Three related captures in one thread: AI data market research, an
  African-language dataset idea (Hausa/Yoruba/Igbo), and a potential buyer.
- Then asked: "what connects these three?"
- **Retrieval surface:** `notes_retrieved: 1`, Arkana's reply referenced all
  three concepts (research, dataset, buyer) — so Arkana *inferred* the link
  from the retrieved text and synthesized it in prose. ✅ as a conversation.
- **Graph surface — the honest gap:** `/api/knowledge/graph` returned 39 nodes
  and 79 edges, but **0 edges touch any of the 6 conversation nodes** created
  by this experiment. The captures exist as isolated `note_type=conversation`
  nodes; the K3-C graph enrichment links documents/projects, not ad-hoc
  conversational captures.
- **Meaning:** the Knowledge Graph does NOT automatically connect work objects
  captured through conversation. Arkana can synthesize a link in prose from
  retrieved text, but the *structural* relationship is not materialized in the
  graph. This is the precise friction point for a Personal Echofeild projection:
  if work is captured conversationally, it will not form the graph edges needed
  to project "what connects to this."
- **Implication for 4D:** before a Personal Echofeild can render connected
  work, either (a) conversational captures that name Work Objects must be
  promoted to real graph nodes with typed edges, or (b) capture must go through
  a path that creates edges (document/project ingestion). The smallest fix is
  TBD — do not build a graph rewriter; first observe which capture path the
  daily loop actually uses.

### EXP 8 — Content Derivation (research → publishable idea) — ✅ PASS (partial)
- Captured a research note; asked "is there a publishable idea hidden in this?"
- `notes_retrieved: 1`, reply proposed a content opportunity (publish/content
  signal true).
- **Meaning:** Arkana can derive a content opportunity from real work via the
  spine. This is the Growth OS content loop working at the conversation layer.
  Note: the derivation is in-prose, not yet a structured Content Object — that
  is correctly deferred until usage shows whether structured capture is needed.

### EXP 9 — Decision Memory (no-build decision → recall) — ✅ PASS
- Told Arkana: "we will NOT build a CRM during Phase 4C."
- Later asked: "what architectural things did we explicitly decide NOT to build?"
- `notes_retrieved: 1`, reply contained `crm`.
- **Meaning:** operational decisions captured conversationally are recalled
  with provenance. This is the seed of "institutional memory," not just
  conversational history.

### EXP 4, 5, 6, 7 — ⏸ UNTESTABLE by API (honestly)
- **Exp 4 (Project → Personal Echofeild):** requires the Personal Echofeild
  surface, which does not yet exist as a route. The SolSpire project exists, but
  the projection feed does not.
- **Exp 5 (Private boundary):** requires an authenticated browser session and
  an authorization-scoped query path. The spine's `session_id` is per-device
  (localStorage); there is no authenticated `user_id` gating Knowledge OS
  reads (see Runtime Contract §1 — `user_id` is NOT YET IMPLEMENTED). So a
  hard private/public boundary cannot be API-tested today.
- **Exp 6 (Public/Private separation):** same blocker — no auth-gated read path
  to verify public knowledge vs private strategy separation.
- **Exp 7 (Encyclopedia vs Personal):** same blocker — Encyclopedia vs Personal
  Echofeild separation depends on the private read boundary.

These are not failures to hide; they are the precise boundaries that must be
built (with an authenticated `user_id`) before Phase 4D's Personal Echofeild
can be proven. Per the directive: do not build speculatively — the absence of
an auth-gated read path is the observed blocker, and it is the right *first*
implementation slice for 4D.

---

## What the experiments proved

- ✅ The conversational spine is a real, usable capture+recall mechanism for
  research, decisions, and content opportunities.
- ✅ Cross-surface continuity is robust (Exp 1, 2, 9 all pass).
- ✅ Content derivation from real work works in-prose (Exp 8).
- ⚠️ **The Knowledge Graph does not materialize edges for conversational
  captures.** This is the single most important structural finding: a Personal
  Echofeild built on the current graph would render isolated conversation
  nodes, not connected work. This is the candidate "smallest consolidation
  that removes observed friction."
- ⏸ The private/public boundary (Exp 5/6/7) is **not yet provable** because
  there is no authenticated read path. This is the correct *next* build
  prerequisite — not a CRM, not a UI, but the `user_id` + auth-gated read that
  the Runtime Contract already flagged as NOT YET IMPLEMENTED.

---

## Recommended next slice (Phase 4D candidate — NOT to build blindly)

From observed friction, the smallest high-value consolidation is:

1. **Auth-gated read path (the `user_id` gap).** The private boundary
   experiments (5/6/7) cannot pass until a Knowledge OS read can be scoped to
   an authenticated human rather than a per-device `session_id`. This is the
   prerequisite for Personal Echofeild and for the public/private separation
   that the target architecture requires.

2. **Conversational-capture → graph-edge promotion (the Exp 3 gap).** When a
   conversational capture explicitly names a Work Object (idea, research,
   lead, relationship, decision), the smallest fix is to promote that capture
   into a real graph node with a typed edge, so the graph — not just Arkana's
   prose — represents the relationship. This is what makes a Personal
   Echofeild able to render connected work.

Both are *gates*, not features: they unblock the surface consolidation the
target architecture describes, without building Personal Echofeild speculatively.

---

## Adherence to the directive

- No code was changed. This is a findings record.
- No experiments were faked. Untestable ones are labelled.
- The friction surfaced is from real production behaviour, not imagination.
- The next slice is *recommended from observed friction*, matching the
  directive: "Run the ten-minute experiments. Find where the architecture
  actually fails. Then make the smallest consolidation that removes the
  observed friction."
