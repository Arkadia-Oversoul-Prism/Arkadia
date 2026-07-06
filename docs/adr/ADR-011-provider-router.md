# ADR-011: Provider Router — AI Providers as Replaceable Adapters

**Status:** Accepted  
**Date:** 2026-07-06  
**Supersedes:** Direct Gemini calls scattered across api/*.py

---

## Context

Gemini API calls were previously embedded directly in:
- `api/ims_products.py`
- `api/pulse.py`
- `kernel/planner.py`

This means switching or adding a provider requires changes across the entire codebase.
It also means business logic (context assembly, persona selection, knowledge retrieval)
is coupled to provider-specific SDK behaviour.

---

## Decision

Implement a **Provider Router** at `providers/` with a strict interface:

```python
class BaseProvider(ABC):
    def authenticate(self) -> bool
    def send(messages, system_prompt, temperature, max_tokens) -> ProviderResponse
    def stream(messages, system_prompt, temperature) -> AsyncIterator[str]
    def history(thread_id) -> list[dict]
    def attachments(file_path) -> Optional[dict]
    def models() -> list[str]
    def capabilities() -> list[str]
    def health() -> dict
```

**Rules:**
1. Business logic NEVER lives inside a provider adapter
2. Adapters implement ONLY the interface above
3. The router selects providers by capability and priority
4. The Knowledge OS (`/api/knowledge/providers/send`) assembles context BEFORE calling the router
5. Integrating a new provider = implement BaseProvider + register in `providers/router.py`

**Why:**
- The Genesis Protocol demands providers are interchangeable
- LAW IV: Oracle retrieves knowledge. Providers generate language.
- A provider outage must never corrupt knowledge or break architecture

---

## Provider Interface Contract

```
authenticate() → bool          # Are credentials available and valid?
send()         → ProviderResponse  # Synchronous chat
stream()       → AsyncIterator     # Streaming chat
history()      → list[dict]    # Thread history (stateless: return [])
attachments()  → Optional[dict]# File upload/reference
models()       → list[str]     # Available model IDs
capabilities() → list[str]     # ["chat","stream","embed","vision",...]
health()       → dict          # {"status":"ok","model":str,"latency_ms":int}
```

---

## Registered Providers

| Name | Adapter | Status | Priority |
|------|---------|--------|----------|
| gemini | `providers/gemini.py` | Active | 10 |
| claude | `providers/claude.py` | Stub | 20 |
| gpt | `providers/gpt.py` | Stub | 30 |
| deepseek | `providers/deepseek.py` | Stub | 40 |
| grok | `providers/grok.py` | Stub | 50 |
| local | `providers/local.py` | Stub | 99 |

---

## Consequences

- Existing Gemini calls in `api/*.py` should be migrated to `providers.router.send()` over time
- Persona system prompt resolution is handled by the router (from SQLite personas table)
- No provider-specific SDK import should appear outside `providers/*.py`
