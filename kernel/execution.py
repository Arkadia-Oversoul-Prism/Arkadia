"""SolSpire Phase 4 — Execution Kernel.

The brainstem. Single entry point: execute_intent(intent) -> dict.

Pipeline (per scroll spec):
    1. classify_input  — natural language → strict intent dict
    2. plan_task       — intent → ordered steps (deterministic, no LLM)
    3. execute_steps   — run each step, collect results
    4. verify          — check every result has a success-shaped status
    5. wrap response   — {success, intent, steps, results}

No LLM in the kernel itself. No retries. No magic. The Phase 3 task
engine is the higher-autonomy path; this kernel is the reliable spine.
"""
from __future__ import annotations

import re
from typing import Any

from kernel import agents
from kernel.intent_types import ALLOWED_TYPES, normalize


# ── Step 1: classify a raw user message into a strict intent ────────────────
#
# classify_input and its private helpers live in kernel.intent_types (the
# intent-contract leaf) so kernel.planner can import them without forming a
# kernel.planner ↔ kernel.execution import cycle. Re-exported here to keep
# execution.classify_input as the historical public entry point.

from kernel.intent_types import (
    classify_input,
    _extract_amount,
    _INT_RE,
    _AMOUNT_RE,
    _CURRENCY_SYMBOLS,
    _CURRENCY_WORDS,
)


# ── Step 2: plan ────────────────────────────────────────────────────────────

def plan_task(intent: dict[str, Any]) -> list[dict[str, Any]]:
    intent = normalize(intent)
    itype = intent.get("type")

    if itype == "generate_images":
        return [
            {"action": "call_image_agent"},
            {"action": "store_asset"},
            {"action": "log_event"},
        ]
    if itype == "log_transaction":
        return [
            {"action": "write_transaction"},
            {"action": "update_balance"},
        ]
    if itype == "update_open_loops":
        return [
            {"action": "update_open_loops"},
            {"action": "log_event"},
        ]
    if itype == "generate_verse":
        return [
            {"action": "generate_verse"},
            {"action": "log_event"},
        ]
    return []


# ── Step 3: execute ─────────────────────────────────────────────────────────

def execute_steps(steps: list[dict[str, Any]], payload: dict[str, Any],
                  intent_type: str | None = None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    last_image_result: dict[str, Any] | None = None
    for step in steps:
        action = step.get("action")
        try:
            if action == "call_image_agent":
                r = agents.call_image_agent(payload)
                last_image_result = r

            elif action == "store_asset":
                r = agents.store_asset(payload, last_image_result or {})

            elif action == "write_transaction":
                r = agents.write_transaction(payload)

            elif action == "update_balance":
                r = agents.update_balance(payload)

            elif action == "update_open_loops":
                r = agents.update_open_loops(payload)

            elif action == "generate_verse":
                r = agents.generate_verse(payload)

            elif action == "log_event":
                r = agents.log_event(
                    payload, {"kind": intent_type or "kernel_event"},
                )

            else:
                r = {"status": "failed", "error": f"unknown action: {action}"}

        except Exception as e:  # noqa: BLE001
            r = {"status": "failed", "error": str(e), "action": action}

        r["action"] = action
        results.append(r)
    return results


# ── Step 4: verify ──────────────────────────────────────────────────────────

_OK_STATUSES = {"success", "written", "ok"}


def verify(results: list[dict[str, Any]]) -> bool:
    if not results:
        return False
    for r in results:
        if r.get("status") not in _OK_STATUSES:
            return False
    return True


# ── Step 6: master function ─────────────────────────────────────────────────

def execute_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """End-to-end execution kernel. Returns:
        {success, intent, steps, results, summary, tool_used, handled}

    Phase 6: dispatch goes through the tool registry. The legacy
    plan_task / execute_steps pair is kept for introspection and
    backward compatibility — callers can still invoke them directly,
    but the master pipeline now flows through tools.select_tool.
    """
    from kernel.tools import select_tool  # local import avoids circular

    intent = normalize(intent)

    if intent.get("type") not in ALLOWED_TYPES:
        return {
            "success":   False,
            "intent":    intent,
            "steps":     [],
            "results":   [],
            "summary":   "No kernel-handled intent. Pass through to Arkana.",
            "tool_used": None,
            "handled":   False,
        }

    # Phase 7 meta-intent: route through the planner + chain executor
    # instead of a single tool. Keeps the kernel envelope shape stable so
    # the worker, /api/job/{id}, and the bot all keep working unchanged.
    if intent["type"] == "__plan__":
        return _execute_planner_intent(intent)

    tool = select_tool(intent)
    if tool is None:
        return {
            "success":   False,
            "intent":    intent,
            "steps":     [],
            "results":   [],
            "summary":   f"No tool registered for intent type '{intent['type']}'.",
            "tool_used": None,
            "handled":   True,
        }

    payload = intent.get("payload") or {}
    try:
        envelope = tool.run(payload)
    except Exception as e:  # noqa: BLE001
        return {
            "success":   False,
            "intent":    intent,
            "steps":     plan_task(intent),
            "results":   [{"status": "failed", "action": tool.name, "error": str(e)}],
            "summary":   f"Tool '{tool.name}' raised: {e}",
            "tool_used": tool.name,
            "handled":   True,
        }

    # Re-attach the Phase 4 contract fields so Phase 5 workers and the
    # bot's kernel rendering keep working without modification.
    envelope["intent"]  = intent
    envelope["handled"] = True
    envelope.setdefault("steps", plan_task(intent))
    envelope.setdefault("tool_used", tool.name)
    return envelope


def _execute_planner_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """Phase 7 bridge: turn a __plan__ intent into a planner run wrapped in
    the standard kernel envelope. Accepts either a raw `input` string (LLM
    plans on the fly) or a pre-built `plan` dict (skips planning, just
    validates + executes)."""
    from kernel.planner import (
        execute_plan, format_response, plan_or_fallback, validate_plan,
    )

    payload = intent.get("payload") or {}
    user_input = payload.get("input")
    prebuilt   = payload.get("plan")

    if isinstance(prebuilt, dict):
        ok, reason = validate_plan(prebuilt)
        if not ok:
            return {
                "success":   False,
                "intent":    intent,
                "steps":     [],
                "results":   [],
                "summary":   f"Plan rejected: {reason}",
                "tool_used": "__plan__",
                "handled":   True,
                "plan":      prebuilt,
                "plan_source": "user",
            }
        execution = execute_plan(prebuilt)
        return {
            "success":     execution["success"],
            "intent":      intent,
            "steps":       execution["steps"],
            "results":     [s["envelope"] for s in execution["steps"]],
            "summary":     format_response(execution),
            "tool_used":   "__plan__",
            "handled":     True,
            "plan":        prebuilt,
            "plan_source": "user",
            "execution":   execution,
        }

    if not isinstance(user_input, str) or not user_input.strip():
        return {
            "success":   False,
            "intent":    intent,
            "steps":     [],
            "results":   [],
            "summary":   "__plan__ payload requires `input` (str) or `plan` (object).",
            "tool_used": "__plan__",
            "handled":   True,
        }

    outcome = plan_or_fallback(user_input)
    execution = outcome.get("execution") or {}
    return {
        "success":     outcome["success"],
        "intent":      intent,
        "steps":       execution.get("steps", []),
        "results":     [s["envelope"] for s in execution.get("steps", [])],
        "summary":     outcome["summary"],
        "tool_used":   "__plan__",
        "handled":     True,
        "plan":        outcome.get("plan"),
        "plan_source": outcome.get("source"),
        "execution":   execution or None,
    }


def _summarize(intent: dict[str, Any], results: list[dict[str, Any]],
               success: bool) -> str:
    """Short, human-readable confirmation line for Telegram / chat clients.

    Moved to kernel.tools to break the kernel.tools ↔ kernel.execution import
    cycle; re-exported here for any caller that imports it from execution.
    """
    from kernel.tools import _summarize as _tools_summarize
    return _tools_summarize(intent, results, success)


__all__ = [
    "classify_input", "plan_task", "execute_steps",
    "verify", "execute_intent",
]
