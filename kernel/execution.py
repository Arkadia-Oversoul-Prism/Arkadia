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

_INT_RE = re.compile(r"\b(\d+)\b")
_AMOUNT_RE = re.compile(
    r"(?:\$|usd|ngn|eur|gbp|₦|€|£)?\s*(\d+(?:[.,]\d+)?)\s*(usd|ngn|eur|gbp|naira|dollars?|euros?)?",
    re.IGNORECASE,
)
_CURRENCY_SYMBOLS = {"$": "USD", "₦": "NGN", "€": "EUR", "£": "GBP"}
_CURRENCY_WORDS = {
    "usd": "USD", "dollar": "USD", "dollars": "USD",
    "ngn": "NGN", "naira": "NGN",
    "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "gbp": "GBP", "pound": "GBP", "pounds": "GBP",
}


def _extract_amount(message: str) -> tuple[float | None, str]:
    m = _AMOUNT_RE.search(message)
    if not m:
        return None, "USD"
    try:
        amount = float(m.group(1).replace(",", "."))
    except ValueError:
        return None, "USD"
    currency = "USD"
    for sym, code in _CURRENCY_SYMBOLS.items():
        if sym in message:
            currency = code
            break
    word = (m.group(2) or "").lower().strip()
    if word in _CURRENCY_WORDS:
        currency = _CURRENCY_WORDS[word]
    return amount, currency


def classify_input(message: str, source: str = "api") -> dict[str, Any]:
    """Map a raw user message into the strict Phase 4 intent envelope.
    Returns {type: None, ...} when the message does not match any of the
    four kernel-handled types — caller should then fall back to Arkana.
    """
    if not isinstance(message, str) or not message.strip():
        return {"type": None, "payload": {}, "source": source}

    lc = message.lower()

    # generate_images — explicit image verbs
    if re.search(r"\b(image|images|picture|pictures|draw|render|visual)\b", lc):
        m = _INT_RE.search(message)
        count = int(m.group(1)) if m else 1
        return {
            "type":    "generate_images",
            "payload": {"count": max(1, count), "prompt": message.strip()},
            "source":  source,
        }

    # log_transaction — money verbs OR currency markers
    if re.search(r"\b(spent|paid|received|transaction|earned|invoice|charged)\b", lc) \
            or any(s in message for s in _CURRENCY_SYMBOLS):
        amount, currency = _extract_amount(message)
        if amount is not None:
            return {
                "type":    "log_transaction",
                "payload": {"amount": amount, "currency": currency, "note": message.strip()},
                "source":  source,
            }

    # update_open_loops — explicit loop / followup vocabulary
    loop_match = re.match(
        r"^(?:open\s+loop|loop|todo|follow(?:[\s-]?up)?|track)\s*[:\-]?\s*(.+)$",
        message.strip(), re.IGNORECASE,
    )
    if loop_match:
        loop_text = loop_match.group(1).strip()
        status = "open"
        if re.search(r"\b(close|done|resolved|complete)\b", lc):
            status = "closed"
        return {
            "type":    "update_open_loops",
            "payload": {"loop": loop_text, "status": status},
            "source":  source,
        }

    # generate_verse — explicit verse / scroll verbs (avoid the bare 'generate')
    if re.search(r"\b(verse|scroll|poem)\b", lc) and \
            re.search(r"\b(generate|write|compose|create)\b", lc):
        return {"type": "generate_verse", "payload": {}, "source": source}

    # No deterministic match — let caller fall through to Arkana.
    return {"type": None, "payload": {}, "source": source}


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
    """Short, human-readable confirmation line for Telegram / chat clients."""
    itype = intent["type"]
    if not success:
        return f"⚠️ {itype}: execution incomplete."

    if itype == "generate_images":
        img = next((r for r in results if r.get("action") == "call_image_agent"), {})
        n = img.get("count", 0)
        return f"🖼  Generated {n} image(s) and stored to Oracle."

    if itype == "log_transaction":
        txn = next((r for r in results if r.get("action") == "write_transaction"), {})
        bal = next((r for r in results if r.get("action") == "update_balance"), {})
        t = txn.get("transaction") or {}
        amt = t.get("amount", 0)
        cur = t.get("currency", "USD")
        bal_line = bal.get("balance", {}).get(cur, amt)
        return f"💱 Logged {amt} {cur}. Balance now {bal_line} {cur}."

    if itype == "update_open_loops":
        loop = next((r for r in results if r.get("action") == "update_open_loops"), {})
        l = loop.get("loop") or {}
        return f"🌀 Open loop '{l.get('loop')}' → {l.get('status')}."

    if itype == "generate_verse":
        v = next((r for r in results if r.get("action") == "generate_verse"), {})
        return v.get("verse") or "🜂 Verse generated."

    return f"✓ {itype} complete."


__all__ = [
    "classify_input", "plan_task", "execute_steps",
    "verify", "execute_intent",
]
