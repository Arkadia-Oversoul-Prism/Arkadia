---
name: Spawn Oracle Routing
description: How /api/agent/spawn handles oracle-type agents — bypasses kernel worker, calls Gemini directly.
---

## The problem

`/api/agent/spawn` creates kernel jobs. The kernel worker calls `execute_intent()` from `kernel/execution.py`, which only handles 4 types: `generate_images`, `log_transaction`, `update_open_loops`, `generate_verse`. Any other type (including `oracle`) produces a null/empty result. The Telegram bot called spawn with `agent: "oracle"`, got an empty result, tried to send it — Telegram rejected with "message text is empty" (400).

## The fix (api/main.py, spawn endpoint)

When `agent == "oracle"`, the spawn endpoint now:
1. Resolves the Gemini API key (key store → env var fallback)
2. Calls `_gemini_chat(msgs, oracle_system)` directly — synchronous, no job queue
3. Creates a completed job immediately for audit trail/dashboard visibility
4. Returns `{job_id, status: "completed", reply: text, text: text}` — bot can use either key

Non-oracle agents still follow the original path: `store.create()` → background worker.

## Bot integration note

The Telegram bot should read `.reply` or `.text` from the spawn response. It does NOT need to poll `/api/job/{job_id}` for oracle-type requests since status is `"completed"` immediately.

## System prompt used

Lightweight Oracle identity (no RAG, no personal context, mobile-optimised for Telegram). Conversation history passed via `context.history` (last 8 turns).
