# Provider Routing Forensic Audit Baseline

Status: FROZEN
Repository: Arkadia-Oversoul-Prism/Arkadia
Branch baseline: main
Audit mode: read-only source inspection
Date: 2026-10-02

## Existing primitives

- Gemini key pool: api/key_pool.py with round-robin acquisition and cooldown/report_success/report_failure.
- Multi-provider credential store: api/provider_key_store.py for gemini/openai/claude/deepseek plus environment fallbacks.
- Provider registry: providers/router.py registers gemini, claude, gpt, deepseek and local Ollama adapters.
- Provider capability interface: providers/base.py exposes authenticate, send, stream, models, capabilities and health.
- Governed Weaver boundary: weaver/provider.py exposes ProviderRequest/ProviderResult/invoke_provider and preserves PassSpec governance in weaver/agent.py.
- Queue/job substrate: kernel/jobs.py and kernel/planner.py provide queued work and task metadata.
- Existing K2/key-pool tests cover key distribution, cooldown, reset, empty-pool behavior and governed provider failure.

## Gaps frozen for implementation

- Provider registry selection is static priority plus capability/authentication checks.
- Provider selection is not task-aware.
- Queue signals are not connected to provider selection.
- Weaver's governed invocation path does not use providers/router.py for non-Gemini calls.
- weaver/llm.py advertises provider names that do not all have callable implementations there.
- Invalid provider responses are not represented as a distinct governed outcome.

## Non-goals

- No change to authorization semantics.
- No automatic cross-provider fallback for explicitly selected providers.
- No replacement of Gemini key-pool behavior.
- No provider-specific performance claims.
- No production deployment or merge as part of the implementation pass.

This document is the frozen baseline for the task-aware provider-routing change.
