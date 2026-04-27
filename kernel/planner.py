"""SolSpire Phase 7 — LLM planner + multi-tool chain executor.

Adds a reasoning layer ABOVE the Phase 6 tool registry. Nothing in Phase 4
(deterministic kernel) or Phase 6 (tool registry) changes — the planner
just chooses *which* registered tools to run, in *what order*, with what
inputs. When the LLM is unavailable or returns garbage, we fall back to
Phase 6 deterministic routing.

Pipeline:
    user_input
        │
        ▼
    generate_plan ─── Gemini ──▶ {"steps": [{"tool", "input"}, ...]}
        │                              │ invalid JSON / no key / unknown tool
        │ valid                        ▼
        ▼                          fallback → classify_input → single tool
    validate_plan
        │
        ▼
    execute_plan (chain with $ref context propagation)
        │
        ▼
    format_response (sync text summary)

Hard limits (Step 8 of the spec):
  • MAX_STEPS = 5             — caps blast radius per plan
  • single-pass execution     — no recursion, no re-planning mid-run
  • per-tool exception capture — one bad step won't crash the chain
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import httpx

from kernel.tools import TOOL_REGISTRY, list_tools

logger = logging.getLogger("arkadia.planner")

# Phase 8: optional context block injected into the planner prompt
# when the Oracle has signal to share. Kept in JSON for token economy.
_CONTEXT_INSTRUCTION = (
    "\nSystem memory (use only if relevant; do NOT hallucinate fields not present):\n"
    "{context_json}\n"
)

# ── Hard constraints ────────────────────────────────────────────────────────
MAX_STEPS = 5
PLANNER_TIMEOUT_S = 20.0
PLANNER_MODELS = (
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
)

# Reference syntax inside step inputs:  "$step_0.field" or "$tool_name.field"
_REF_RE = re.compile(r"^\$([a-zA-Z0-9_]+)(?:\.([a-zA-Z0-9_.]+))?$")


# ── Step 1: planner LLM call ────────────────────────────────────────────────

def _build_planner_system_prompt(tools: list[dict[str, Any]],
                                  context: dict[str, Any] | None = None) -> str:
    tool_lines = []
    for t in tools:
        schema = t.get("payload_schema") or {}
        schema_str = ", ".join(f"{k}: {v}" for k, v in schema.items()) or "(no fields)"
        tool_lines.append(f"  • {t['name']} — {t['description']}\n      input: {schema_str}")
    tool_block = "\n".join(tool_lines) if tool_lines else "  (no tools registered)"

    # Phase 8: optional memory injection. Only included when there is real
    # signal — empty memory just wastes tokens.
    from kernel.memory import has_signal
    context_block = ""
    if has_signal(context):
        try:
            context_block = _CONTEXT_INSTRUCTION.format(
                context_json=json.dumps(context, ensure_ascii=False, default=str)[:2000],
            )
        except Exception:  # noqa: BLE001
            context_block = ""

    return (
        "You are a planning engine for the Arkadia execution kernel.\n"
        "You MUST return a single valid JSON object — no prose, no code fences, no commentary.\n"
        "\n"
        "Available tools:\n"
        f"{tool_block}\n"
        f"{context_block}"
        "\n"
        "Rules:\n"
        f"- Return at most {MAX_STEPS} steps.\n"
        "- Use ONLY tools from the list above. Inventing tool names is forbidden.\n"
        "- Each step must include `tool` (string) and `input` (object).\n"
        "- To pass an output from an earlier step into a later step, set the input value to "
        "  the string \"$<step_id>.<field>\" (e.g. \"$step_0.verse\"). The step_id is "
        "  \"step_0\" for the first step, \"step_1\" for the second, etc.\n"
        "- Prefer the smallest plan that satisfies the request. One step is often enough.\n"
        "- If system memory is provided, use it to avoid redundant work and to keep "
        "  decisions consistent with prior state. Never invent values not in memory.\n"
        "\n"
        "Output format (exact):\n"
        "{\n"
        '  "steps": [\n'
        '    {"tool": "<tool_name>", "input": { ... }}\n'
        "  ]\n"
        "}\n"
    )


def _strip_code_fence(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json fences despite instructions."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _gemini_plan(user_input: str, system_prompt: str) -> str | None:
    """Synchronous Gemini call (the worker thread is sync). Returns raw text
    or None on every-model failure. Tries each fallback model in order."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — planner will fallback")
        return None

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_input}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }

    last_err: str | None = None
    with httpx.Client(timeout=PLANNER_TIMEOUT_S) as client:
        for model in PLANNER_MODELS:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            try:
                resp = client.post(url, json=payload)
                if resp.status_code in (429, 403):
                    last_err = f"{model}: HTTP {resp.status_code}"
                    continue
                resp.raise_for_status()
                data = resp.json()
                cands = data.get("candidates") or []
                if not cands:
                    last_err = f"{model}: no candidates"
                    continue
                parts = (cands[0].get("content") or {}).get("parts") or []
                texts = [p.get("text", "") for p in parts if p.get("text")]
                if not texts:
                    last_err = f"{model}: empty"
                    continue
                return "".join(texts)
            except Exception as e:  # noqa: BLE001
                last_err = f"{model}: {e}"
                continue

    logger.warning("planner gemini failed: %s", last_err)
    return None


def generate_plan(user_input: str,
                  context: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Turn raw input into a structured plan. Returns None on planner failure;
    caller should drop to deterministic fallback.

    Phase 8: `context` is an optional memory dict from kernel.memory.
    When provided and non-empty, it's injected into the system prompt
    so the LLM can plan with awareness of prior state.
    """
    if not isinstance(user_input, str) or not user_input.strip():
        return None

    system = _build_planner_system_prompt(list_tools(), context=context)
    raw = _gemini_plan(user_input.strip(), system)
    if raw is None:
        return None

    try:
        plan = json.loads(_strip_code_fence(raw))
    except (ValueError, TypeError) as e:
        logger.warning("planner returned non-JSON: %s | raw=%s", e, raw[:200])
        return None

    if not isinstance(plan, dict) or "steps" not in plan:
        logger.warning("planner JSON missing 'steps': %s", str(plan)[:200])
        return None
    return plan


# ── Step 2: validation ──────────────────────────────────────────────────────

def validate_plan(plan: Any) -> tuple[bool, str]:
    """Reject any plan that references an unregistered tool, exceeds the step
    cap, or has malformed step shape. Returns (ok, reason)."""
    if not isinstance(plan, dict):
        return False, "plan is not an object"
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return False, "plan.steps must be a non-empty list"
    if len(steps) > MAX_STEPS:
        return False, f"plan exceeds MAX_STEPS={MAX_STEPS} (got {len(steps)})"
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return False, f"step {i} is not an object"
        tool_name = step.get("tool")
        if not isinstance(tool_name, str) or not tool_name:
            return False, f"step {i} missing string `tool`"
        if tool_name not in TOOL_REGISTRY:
            return False, f"step {i} uses unknown tool '{tool_name}'"
        if "input" not in step:
            step["input"] = {}
        if not isinstance(step["input"], dict):
            return False, f"step {i} `input` must be an object"
    return True, "ok"


# ── Step 3: chain execution with $ref context propagation ───────────────────

def _resolve_ref(value: Any, context: dict[str, Any]) -> Any:
    """If `value` is a "$ref" string, pull from context. Recurses into
    dicts/lists so nested refs resolve too. Unknown refs pass through."""
    if isinstance(value, str):
        m = _REF_RE.match(value)
        if not m:
            return value
        key, path = m.group(1), m.group(2)
        if key not in context:
            return value  # leave as-is; tool may treat it as a literal
        node = context[key]
        if not path:
            return node
        for segment in path.split("."):
            if isinstance(node, dict) and segment in node:
                node = node[segment]
            else:
                return value
        return node
    if isinstance(value, dict):
        return {k: _resolve_ref(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_ref(v, context) for v in value]
    return value


def execute_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Run validated steps in order. Each step's result is added to the
    context under both its step_id and its tool name so later steps can
    reference either. One failed step short-circuits the chain.

    Phase 8: every step records to the metrics ledger (success + duration)
    and carries timing in its trace record.
    """
    from kernel import metrics  # local to avoid import cycles

    context: dict[str, Any] = {}
    step_results: list[dict[str, Any]] = []
    success = True
    failed_at: int | None = None

    for i, step in enumerate(plan["steps"]):
        step_id = f"step_{i}"
        tool = TOOL_REGISTRY[step["tool"]]
        resolved_input = _resolve_ref(step.get("input") or {}, context)

        started = time.time()
        try:
            envelope = tool.run(resolved_input)
        except Exception as e:  # noqa: BLE001 — chain must capture, not crash
            logger.exception("plan step %s (%s) raised", step_id, tool.name)
            envelope = {
                "success": False,
                "results": [{"status": "failed", "action": tool.name, "error": str(e)}],
                "summary": f"Tool '{tool.name}' raised: {e}",
                "tool_used": tool.name,
            }
        duration_ms = round((time.time() - started) * 1000, 2)
        metrics.record_tool_call(
            tool.name,
            success=bool(envelope.get("success")),
            duration_ms=duration_ms,
        )

        step_record = {
            "step_id":     step_id,
            "tool":        tool.name,
            "input":       resolved_input,
            "envelope":    envelope,
            "started_at":  started,
            "duration_ms": duration_ms,
        }
        step_results.append(step_record)

        # Make this step's result addressable by both step_id and tool name.
        context[step_id]   = envelope
        context[tool.name] = envelope

        if not envelope.get("success"):
            success = False
            failed_at = i
            break

    return {
        "success":   success,
        "steps":     step_results,
        "context":   context,
        "failed_at": failed_at,
    }


# ── Step 6: response synthesis (deterministic; LLM optional later) ─────────

def format_response(execution: dict[str, Any]) -> str:
    """Produce a short human-readable line summarising a chain run."""
    steps = execution.get("steps") or []
    if not steps:
        return "No steps executed."
    if execution.get("success"):
        if len(steps) == 1:
            return steps[0]["envelope"].get("summary") or "✓ Done."
        head = " → ".join(s["tool"] for s in steps)
        return f"✓ Plan complete ({len(steps)} steps): {head}"
    failed = execution.get("failed_at")
    if failed is None:
        return "⚠️ Plan failed."
    bad = steps[failed]
    summary = bad["envelope"].get("summary") or "no detail"
    return f"⚠️ Plan failed at step {failed} ({bad['tool']}): {summary}"


# ── Step 5: deterministic fallback ──────────────────────────────────────────

def _fallback_plan(user_input: str) -> dict[str, Any] | None:
    """When the LLM is unavailable or returned an invalid plan, drop to
    Phase 4's regex classifier and wrap the matched intent as a single-step
    plan. Returns None if even the classifier doesn't match."""
    from kernel.execution import classify_input

    intent = classify_input(user_input, source="planner")
    itype = intent.get("type")
    if not itype or itype not in TOOL_REGISTRY:
        return None
    return {
        "steps": [{"tool": itype, "input": intent.get("payload") or {}}],
        "fallback": True,
    }


# ── Top-level orchestrator ──────────────────────────────────────────────────

def plan_or_fallback(user_input: str, *,
                     with_context: bool = True) -> dict[str, Any]:
    """End-to-end: retrieve memory → plan → validate → execute. On any
    planner failure, retry once with the deterministic fallback. The
    return shape is stable for the API and worker callers.

    Phase 8: `with_context=True` (the default) enriches the planner prompt
    with a slice of Oracle state. Set False to plan blind (test/debug).
    """
    from kernel import memory, metrics

    if not isinstance(user_input, str) or not user_input.strip():
        return {
            "success":   False,
            "plan":      None,
            "source":    "none",
            "summary":   "Empty input.",
            "execution": None,
            "context":   None,
        }

    ctx = memory.retrieve_context(user_input) if with_context else None

    plan_source = "llm"
    plan = generate_plan(user_input, context=ctx)
    if plan is not None:
        ok, reason = validate_plan(plan)
        if not ok:
            logger.warning("planner produced invalid plan: %s", reason)
            plan = None

    if plan is None:
        plan = _fallback_plan(user_input)
        plan_source = "fallback" if plan else "none"

    if plan is None:
        metrics.record_plan(success=False, source="none")
        return {
            "success":   False,
            "plan":      None,
            "source":    "none",
            "summary":   "No plan could be produced (LLM unavailable and no deterministic match).",
            "execution": None,
            "context":   ctx,
        }

    ok, reason = validate_plan(plan)
    if not ok:
        metrics.record_plan(success=False, source=plan_source)
        return {
            "success":   False,
            "plan":      plan,
            "source":    plan_source,
            "summary":   f"Plan rejected: {reason}",
            "execution": None,
            "context":   ctx,
        }

    execution = execute_plan(plan)
    metrics.record_plan(success=execution["success"], source=plan_source)
    return {
        "success":   execution["success"],
        "plan":      plan,
        "source":    plan_source,
        "summary":   format_response(execution),
        "execution": execution,
        "context":   ctx,
    }


__all__ = [
    "MAX_STEPS",
    "generate_plan",
    "validate_plan",
    "execute_plan",
    "format_response",
    "plan_or_fallback",
]
