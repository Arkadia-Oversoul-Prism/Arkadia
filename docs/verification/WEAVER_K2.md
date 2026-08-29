# WEAVER-K2 — Provider + Key-Pool Orchestration

## Role

Governed model invocation for Weaver. **Not** an authorization layer.

PassSpec.provider → `weaver.provider.invoke_provider` → structured `ProviderResult`

Gemini uses `api.key_pool.acquire_key` / `report_failure` / `report_success` when available.

## Invariants

- Provider failure ≠ successful Weaver execution
- No silent cross-provider fallback
- No secrets in logs/checkpoints/context
- Provider module cannot write/commit/push
- K0.1 lifecycle unchanged

## Outcomes

SUCCESS | RATE_LIMITED | AUTH_FAILURE | PROVIDER_UNAVAILABLE | INVALID_REQUEST | TIMEOUT | CONFIGURATION_ERROR | UNKNOWN_FAILURE
