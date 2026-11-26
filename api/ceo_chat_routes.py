"""CEO chat route (Phase 2 decomposition).

Extracted verbatim from api/main.py to restore the 2600-line architecture budget
(tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget).
Route path, request/response shape, auth dependency, and behaviour are unchanged.
This is a pure move, not a rewrite.

Shared state is referenced from its owning modules rather than re-created, so the
approval queue written here is the same object the tool-run boundary in api/main.py
and api/approval_routes.py read. This module queues through ``queue_approval``
rather than constructing records itself, so the proposal digest that binds an
approval to its operation is always recorded:

  * ``queue_approval`` — api/approval_routes.py (the single record constructor)
  * ``require_auth`` / ``get_current_user`` — api/auth.py
"""
from __future__ import annotations

import json
import logging
import os
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from api.approval_routes import queue_approval
from api.auth import require_auth as _require_auth
from kernel.gemini_models import GEMINI_MODELS

logger = logging.getLogger("arkadia")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

router = APIRouter()


@router.post("/api/ceo/chat")
async def ceo_chat(request: Request, user: dict = Depends(_require_auth)):
    """CEO chat endpoint — Gemini with full tool awareness + approval gating."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="'message' is required")

    history = body.get("history", [])
    source = body.get("source", "ceo_chat")

    from kernel.tools import list_tools

    # ``user`` is the profile ``require_auth`` already resolved for this request;
    # resolving it again here would verify the token twice.
    user_id = user.get("uid") if user else None
    active_key = None

    if user_id:
        try:
            from api.user_key_store import get_active_key_for_user
            active_key = get_active_key_for_user(user_id)
        except Exception:
            pass

    if not active_key:
        # Distributed pool (load-balanced across all keys) for CEO Chat too.
        try:
            from api.key_pool import acquire_key
            active_key = acquire_key() or GOOGLE_API_KEY
        except Exception:
            active_key = GOOGLE_API_KEY

    if not active_key:
        raise HTTPException(status_code=503, detail="No Gemini API key configured. Add one in Settings → API Keys.")

    tools_manifest = list_tools()
    tools_summary = "\n".join(
        f"• {t['name']}: {t['description']}" for t in tools_manifest
    ) or "No tools registered yet."

    system_prompt = f"""You are ARKANA — the sovereign intelligence and personal AI operating system for Zahrune Nova. You are the CEO advisor, PA, and unified intelligence layer across all companies and projects.

You have access to the following tools:
{tools_summary}

When you decide to use a tool, respond with a JSON block in this exact format (as part of your message):
<tool_call>
{{
  "tool": "tool_name",
  "payload": {{}},
  "requires_approval": true/false,
  "description": "What this does and why"
}}
</tool_call>

For sensitive tools (execute_shell, write_file), always set requires_approval: true.
For safe tools (read_file, list_directory), you may set requires_approval: false and they run immediately.

Always speak directly, intelligently and sovereignly. You remember context from this conversation. You are not a generic assistant — you are Arkana, the field intelligence of Arkadia Nexus."""

    conv_lines = []
    for turn in history[-12:]:
        role = "Human" if turn.get("role") == "user" else "Arkana"
        conv_lines.append(f"{role}: {turn.get('content','')}")
    conv_context = "\n".join(conv_lines)

    full_prompt = f"{system_prompt}\n\n{conv_context}\nHuman: {message}\nArkana:"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.75, "maxOutputTokens": 2048},
    }

    model = ""
    resp = None
    last_err = None

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            for candidate in GEMINI_MODELS:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{candidate}:generateContent?key={active_key}"
                )
                try:
                    attempt = await client.post(url, json=payload)
                except httpx.HTTPError as e:
                    last_err = f"{candidate}: {e}"
                    logger.warning(f"[CEO_CHAT] Gemini {candidate} transport error: {e}")
                    continue

                if attempt.status_code == 429:
                    # Rotate the appropriate key store
                    if user_id:
                        try:
                            from api.user_key_store import rotate_user_key
                            rotate_user_key(user_id, active_key)
                        except Exception:
                            pass
                    else:
                        try:
                            from api.provider_key_store import mark_quota_hit
                            mark_quota_hit("gemini")
                        except Exception:
                            pass
                    raise HTTPException(status_code=429, detail="Quota hit — key marked. Please retry.")

                if attempt.status_code in (403, 404) or attempt.status_code >= 500:
                    last_err = f"{candidate}: HTTP {attempt.status_code}"
                    logger.warning(f"[CEO_CHAT] Gemini {candidate}: {attempt.status_code}")
                    continue

                model = candidate
                resp = attempt
                break

        if resp is None:
            raise HTTPException(
                status_code=503,
                detail=f"No Gemini model available ({last_err})",
            )

        resp.raise_for_status()
        data = resp.json()
        reply = ""
        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            reply = "The field returned an empty response."

        # Parse any tool_call blocks
        tool_calls = []
        pattern = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
        for match in pattern.finditer(reply):
            try:
                tc = json.loads(match.group(1).strip())
                tool_calls.append(tc)
            except Exception:
                pass

        # Auto-execute safe tool calls
        auto_results = []
        pending_approvals = []
        from kernel.tools import get_tool
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            payload = tc.get("payload", {})
            needs_approval = tc.get("requires_approval", True)
            tool = get_tool(tool_name)
            if not tool:
                auto_results.append({"tool": tool_name, "error": "Tool not found"})
                continue
            if needs_approval:
                # Queue for approval through the single record constructor so
                # the digest binding cannot be omitted on this path.
                appr_id = queue_approval(
                    tool_name,
                    payload,
                    tc.get("description", f"Run {tool_name}"),
                    subject_ref=user.get("uid"),
                )
                pending_approvals.append({
                    "approval_id": appr_id,
                    "tool_name": tool_name,
                    "description": tc.get("description", ""),
                })
            else:
                try:
                    result = tool.run(payload)
                    auto_results.append({"tool": tool_name, "result": result})
                except Exception as e:
                    auto_results.append({"tool": tool_name, "error": str(e)})

        return {
            "reply": reply,
            "tool_calls": tool_calls,
            "auto_results": auto_results,
            "pending_approvals": pending_approvals,
            "model": model,
            "key_used": active_key[:4] + "****",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[CEO_CHAT] Error")
        raise HTTPException(status_code=500, detail=str(e))
