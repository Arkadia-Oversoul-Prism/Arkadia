# ARK-01 — Arkana signal producer / schema conformance

Workstream: `gate-hygiene/ark01-signal-schema-conformance-01`
Base: `main` @ `24a00f856a0286cbb464a4b585117dd57a2646fa`
Status: IMPLEMENTED (repository-source claim; not a production observation)

## 1. Defect

`schemas/arkana/signal/1.0/arkana-signal.schema.json` ($id
`arkadia://schemas/arkana/signal/1.0`) is the frozen canonical evidence envelope
for incoming Arkana signals. It is admitted to the CP10 mutation boundary
(`LEGIT`), but before this change **nothing referenced it**:

```
grep -rn "arkana-signal.schema.json" tests/ scripts/ api/   -> 0 matches
```

The merged producer `POST /api/arkana/signal/ingest`
(`api/arkana_signal_routes.py`, mounted from `api/main.py:1094`) emitted objects
that fail that contract for ordinary model output. Two independent violations,
reproduced with the real `jsonschema` validator:

1. **`interpretation.confidence` is a `number`-only map, but the route wrote a
   possibly-`null` value.** The route wrote
   `{"transcript": derived.get("transcript_confidence")}`. When the model omitted
   the confidence — a routine case, the field is optional in the derivation —
   `null` was written into a map whose `additionalProperties` is
   `{"type": "number"}` -> schema violation.
2. **`$defs/candidate` requires `status`, but candidates were forwarded
   verbatim.** `intent_candidates` / `references` were passed through as model
   output. The model prompt asks for intent candidates and does not demand a
   `status`, so an ordinary candidate `{"value": "play the song"}` violated the
   required-property constraint.

A third latent violation: `source.duration_ms` is `integer | null`, but the raw
client value was forwarded, so a non-integer or negative reading was written
straight through.

## 2. Repair

`api/arkana_signal_routes.py` now normalizes model/client input to the contract
before emitting it:

- `_as_confidence()` accepts only a real number (booleans excluded), clamps to
  `[0, 1]`, and returns `None` for anything else.
- The confidence key is **omitted** when no numeric reading exists, rather than
  written as `null`.
- `_as_candidate_list()` / `_as_candidate()` give every candidate the required
  `status`. An omitted or out-of-enum status becomes `unknown` (the sentinel that
  means "not resolved"), not `candidate` (which the contract reserves for an
  explicit model assertion). Non-object entries are dropped.
- `_as_duration_ms()` coerces duration to a non-negative integer or `null`.

Assembly moved into a pure `_build_signal()` so a test can exercise the exact
object the endpoint returns without an HTTP round-trip.

## 3. Evidence

`tests/test_arkana_signal_schema_conformance.py` — **16 passed**.

- Validates the exact emitted object against the **real schema file** (no
  hand-rolled approximation), via both the pure builder and the endpoint handler
  (only the external Gemini HTTP boundary is stubbed).
- Covers: omitted / null / numeric / out-of-range confidence; candidate status
  assignment, preservation, unknown-value rejection, non-object dropping;
  duration coercion.
- **Negative controls** feed the exact pre-fix constructions to the validator and
  assert it reports the violation
  (`interpretation.confidence.transcript`, `interpretation.intent_candidates.0`),
  so the conformance assertions cannot be vacuous.
- **Positive control** proves the validator accepts a valid minimal object.

**Detector proof (not a claim):** reverting the producer to its pre-fix shape in
a scratch copy turned the suite **10 failed / 6 passed**; restoring the repair
returns **16 passed**. The suite is a real detector, measured, not asserted.

**Regression boundary:** the ingest response has no frontend consumer
(`grep -rn "/api/arkana/signal" web/public_prism/src` -> 0 matches), so removing
the `null` confidence key changes no UI path. `SolspireVoice.tsx` reads a
different event shape (`ev.transcript`), not this envelope.

`python -m py_compile api/main.py` and `api/arkana_signal_routes.py` — both
compile. `api/main.py` is untouched by this workstream.

## 4. Dependency

`jsonschema` was absent from `requirements.txt` and no test imported it. Declared
explicitly (with rationale) so the conformance test runs against the real schema.
`jsonschema 4.26.0` is available in the verification environment.

## 5. Remaining uncertainty

- CI workflows install only a per-workflow dependency subset (pytest/pydantic/
  pyyaml), not full `requirements.txt`. The conformance test uses
  `pytest.importorskip("jsonschema")`, so in a workflow that does not install
  `jsonschema` the test **skips** rather than fails. This is a repository-source
  claim; the test does not itself guarantee CI coverage until a workflow installs
  the dependency. Recorded, not silently assumed.
- This is a source conformance repair. It is **not** a production-parity claim:
  no deployment identity or runtime observation is asserted here.

## 6. Authorization

Repository-source change only. Branch -> PR. Merge is reserved to the human
sovereign.
