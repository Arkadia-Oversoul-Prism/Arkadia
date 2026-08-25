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

from api.auth import require_auth

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
    recipient_uid: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., min_length=1, max_length=8000)


@router.post("/api/messages")
async def send_message(req: SendMessageRequest, user: dict = Depends(require_auth)):
    sender = user["uid"]
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


@router.get("/api/messages/thread/{peer_uid}")
async def get_thread(peer_uid: str, user: dict = Depends(require_auth)):
    me = user["uid"]
    peer = peer_uid.strip()
    if not peer:
        raise HTTPException(status_code=400, detail="Invalid peer")
    msgs = _read_thread(me, peer)
    # Only participants can read — enforced by pair key including me
    return {"messages": msgs, "peer_uid": peer}


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
        peers[peer] = {
            "peer_uid": peer,
            "last_message": last,
            "count": len(msgs),
        }
    return {"conversations": list(peers.values())}
