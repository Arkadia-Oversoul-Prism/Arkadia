"""SolSpire Phase 4 — strict intent contract for the Execution Kernel.

Phase 4 deliberately narrows the intent surface to FOUR canonical types.
Anything outside this set falls through to the existing Arkana / Gemini
response path — Phase 4 does not try to handle every possible message,
only the ones it can complete deterministically end-to-end.
"""
from __future__ import annotations

import re
from typing import Any

ALLOWED_TYPES = {
    "generate_images",
    "log_transaction",
    "update_open_loops",
    "generate_verse",
    # Phase 7 — meta-intent that delegates to the LLM planner + chain
    # executor. Payload shape: {"input": "raw user text"} OR
    # {"plan": {"steps": [...]}} for a pre-built plan.
    "__plan__",
}

ALLOWED_SOURCES = {"telegram", "web", "api", "internal"}


def empty_intent(source: str = "api") -> dict[str, Any]:
    return {
        "type":    None,
        "payload": {},
        "source":  source if source in ALLOWED_SOURCES else "api",
    }


def normalize(intent: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, dict):
        return empty_intent()
    itype = intent.get("type")
    if itype not in ALLOWED_TYPES:
        itype = None
    payload = intent.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    source = intent.get("source", "api")
    if source not in ALLOWED_SOURCES:
        source = "api"
    return {"type": itype, "payload": payload, "source": source}


# ── Phase 4 message classifier ──────────────────────────────────────────────
#
# classify_input lives here (in the intent-contract leaf module) rather than
# in kernel.execution so that kernel.planner can import it without forming a
# kernel.planner ↔ kernel.execution import cycle. execution re-exports it to
# preserve its existing public contract.

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

    # generate_images — ONLY fires on explicit forge commands or unambiguous
    # image-creation requests. The previous broad match on "image / visual /
    # render / draw" was firing on any pasted scroll or corpus document that
    # happened to contain those words. Now requires either the ⟐ forge slash
    # command OR a clear action+object phrase ("generate an image of ...").
    # The web forge slash command (⟐ forge <archetype> <scene>) is the primary
    # surface; this kernel path handles explicit plain-language requests only.
    if re.match(r"^\s*[⟐/]\s*forge\b", message) or \
       re.search(r"\b(generate|create|make|draw)\s+(an?\s+)?(image|picture|photo|illustration)\b", lc):
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


__all__ = [
    "ALLOWED_TYPES", "ALLOWED_SOURCES", "empty_intent", "normalize",
    "classify_input",
]
