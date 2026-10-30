# Arkana Provider Contract 01

**Status:** Proposed provider-neutral contract. Repository inspection verifies a Gemini conversational path and shared key pool, not Arkana multi-provider routing.

## 1. Current state

`api/main.py::commune_resonance` calls the Gemini chat path (or signal-specific Gemini path) using a user key when available, otherwise the shared `api.key_pool`/environment resolution. `api/key_pool.py` distributes Gemini keys and cools failing keys. Other repository components may use additional providers, but their existence does not establish that Arkana routes requests among them. The Arkana response currently does not consistently identify an actual model/provider in its public response.

## 2. Contract goals

- Provider implementations are replaceable behind a stable server-side interface.
- Capability claims come from adapter declarations and runtime results.
- Provider selection is deterministic enough to explain and test.
- Credentials remain server-side and use existing Arkadia key management boundaries.
- Failures are normalized without leaking secrets or raw private diagnostics.
- Streaming and cancellation support are explicit capabilities, not assumed.

## 3. Proposed capability declaration

```typescript
interface ProviderCapabilities {
  modalities: Array<"text" | "image" | "audio" | "video">;
  streaming: boolean;
  cancellation: "native" | "best_effort" | "unsupported";
  tools: boolean;
  structuredOutput: boolean;
  maxInputTokens?: number;
  modelIds: string[];
}
```

Backend equivalents should be typed in the project's language and provider SDK. Declare only capabilities verified for the selected model and configuration. Capability may vary by model, account or request.

## 4. Proposed request and event boundary

A normalized request contains system instructions, canonical server-loaded conversation turns, bounded context segments with provenance, modality payload references, requested output format, user preference and server-side policy limits. It does not accept arbitrary user identity or unbounded client history as authority.

Provider output is a normalized stream of text deltas, usage metadata, finish reason and provider-scoped errors. Tool calls are proposals to the Arkana runtime; they do not grant execution permission.

## 5. Gemini-first rollout

1. Wrap the existing Gemini invocation behind the smallest adapter seam that preserves current model/key behavior and response compatibility.
2. Add explicit provider/model metadata sourced from actual invocation.
3. Test key-pool integration, rate-limit cooldown, timeouts, malformed/empty responses and normalized errors.
4. Implement and verify streaming/cancellation only if the actual Gemini client and deployment transport support them.
5. Add another provider only after credential storage, model capability, privacy, cost controls, rate limits, telemetry and failure semantics are decided and tested.

Do not introduce OpenAI, Anthropic or other provider packages as part of architectural documentation. Do not claim automatic routing or multi-model synthesis until it is implemented and measured.

## 6. Routing policy (future)

A router may consider requested capability, model suitability, context window, modality, tools, availability, latency, cost and explicit user preference. Auto-selection should explain the chosen provider at a useful level. Fallback is allowed only when the alternative is compatible with the task and the UI discloses the fallback. Critical tasks may use comparison/review only when the product has a defined synthesis/evaluation policy; parallel calls alone do not establish higher accuracy.

## 7. Governance and trust

- Model output is untrusted, including structured output and tool-call arguments.
- Provider selection does not change authorization.
- Tool execution must route through existing Arkadia authorization and execution systems.
- Provider credentials never reach the browser.
- Provider/model usage, failures and fallback are logged with privacy-aware metadata, never secret values or raw private prompts by default.
- Provenance from retrieval is distinct from provider identity and must not be inferred from a provider response.

## 8. Acceptance gates for a new adapter

Adapter contract tests; declared capability truth; authenticated owner-scoped prompt context; secret isolation; streaming ordering/cancellation tests where supported; normalized timeout/rate-limit/provider errors; explicit fallback behavior; usage/cost accounting; no regressions to shared Oracle consumers; and evidence that the adapter actually handled the request. Until these gates pass, the provider remains proposed/unavailable in Arkana's user-facing selector.