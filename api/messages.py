"""P1-A ReasoMate messaging — authenticated cross-user DM.

Ownership: sender_uid always from auth; recipient validated as non-empty string.
Storage: JSONL under data/messages/{pair_key}.jsonl (deterministic pair ordering).
"""
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import require_auth, normalize_handle, resolve_uid_by_handle, load_user_profile_store

router = APIRouter(tags=["messages"])

_MSG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "messages")


def _pair_key(a: str, b: str) -> str:
    return "__".join(sorted([a, b]))


def _thread_path(a: str, b: str) -> str:
    os.makedirs(_MSG_DIR, exist_ok=True)
    return os.path.join(_MSG_DIR, f"{_pair_key(a, b)}.jsonl")


def _read_thread(a: str, b: str) -> list[dict]:
    path = _thread_path(a, b)
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def _append(a: str, b: str, msg: dict) -> None:
    path = _thread_path(a, b)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg) + "\n")


class SendMessageRequest(BaseModel):
    recipient_uid: str | None = Field(None, min_length=1, max_length=128)
    recipient_handle: str | None = Field(None, min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=8000)


@router.post("/api/messages")
async def send_message(req: SendMessageRequest, user: dict = Depends(require_auth)):
    sender = user["uid"]
    recipient = None
    if req.recipient_handle and str(req.recipient_handle).strip():
        try:
            normalize_handle(req.recipient_handle)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid handle format")
        recipient = resolve_uid_by_handle(req.recipient_handle)
        if not recipient:
            raise HTTPException(status_code=404, detail="User not found")
    elif req.recipient_uid and str(req.recipient_uid).strip():
        recipient = req.recipient_uid.strip()
    if not recipient or recipient == sender:
        raise HTTPException(status_code=400, detail="Invalid recipient")
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Empty message")
    msg = {
        "id": str(uuid.uuid4()),
        "sender_uid": sender,
        "recipient_uid": recipient,
        "content": content,
        "timestamp": int(time.time() * 1000),
    }
    _append(sender, recipient, msg)
    return {"message": msg}


def _peer_handle_for(uid: str) -> str | None:
    stored = load_user_profile_store(uid)
    u = (stored.get("username") or "").strip()
    if not u:
        return None
    try:
        return normalize_handle(u)
    except ValueError:
        return None


@router.get("/api/messages/thread/{peer_uid}")
async def get_thread(peer_uid: str, user: dict = Depends(require_auth)):
    me = user["uid"]
    peer = peer_uid.strip()
    if not peer:
        raise HTTPException(status_code=400, detail="Invalid peer")
    msgs = _read_thread(me, peer)
    out: dict = {"messages": msgs, "peer_uid": peer}
    ph = _peer_handle_for(peer)
    if ph:
        out["peer_handle"] = ph
    return out


@router.get("/api/messages/inbox")
async def inbox(user: dict = Depends(require_auth)):
    """List peers with last message for current user."""
    me = user["uid"]
    os.makedirs(_MSG_DIR, exist_ok=True)
    peers: dict[str, dict] = {}
    for name in os.listdir(_MSG_DIR):
        if not name.endswith(".jsonl"):
            continue
        parts = name[:-6].split("__")
        if me not in parts:
            continue
        peer = parts[0] if parts[1] == me else parts[1]
        msgs = _read_thread(me, peer)
        if not msgs:
            continue
        last = msgs[-1]
        entry = {
            "peer_uid": peer,
            "last_message": last,
            "count": len(msgs),
        }
        ph = _peer_handle_for(peer)
        if ph:
            entry["peer_handle"] = ph
        peers[peer] = entry
    return {"conversations": list(peers.values())}
