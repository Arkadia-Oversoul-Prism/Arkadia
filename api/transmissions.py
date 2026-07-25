"""
Arkadia Transmissions — Social feed persistence layer.
Stores human posts (transmissions) in data/transmissions.json.
"""
import json
import logging
import os
import time
import uuid
from fastapi import APIRouter

logger = logging.getLogger("arkadia")
router = APIRouter()

DATA_DIR  = os.environ.get("SOLSPIRE_DATA_DIR", "data")
DATA_FILE = os.path.join(DATA_DIR, "transmissions.json")


def _load() -> list[dict]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save(posts: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


@router.get("/api/transmissions")
async def list_transmissions(limit: int = 50, offset: int = 0):
    posts = _load()
    posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    page = posts[offset : offset + limit]
    return {"transmissions": page, "total": len(posts)}


@router.post("/api/transmissions")
async def create_transmission(body: dict):
    if not body.get("content", "").strip():
        return {"error": "content is required"}, 400
    posts = _load()
    post: dict = {
        "id": str(uuid.uuid4()),
        "author": body.get("author", {
            "id": "anon", "name": "Anonymous", "avatar": "◈", "role": "Node"
        }),
        "content": body["content"].strip(),
        "timestamp": int(time.time() * 1000),
        "reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0},
        "comments": [],
        "reposts": 0,
        "resonance": 50,
    }
    posts.insert(0, post)
    _save(posts)
    logger.info(f"[TRANSMISSIONS] New post by {post['author'].get('name','?')}: {post['id'][:8]}")
    return {"transmission": post}


@router.post("/api/transmissions/{post_id}/react")
async def react_to_transmission(post_id: str, body: dict):
    posts = _load()
    reaction_type = body.get("type", "heart")
    valid = {"heart", "fire", "star", "mind"}
    if reaction_type not in valid:
        return {"error": f"invalid reaction type; must be one of {valid}"}
    for p in posts:
        if p["id"] == post_id:
            if reaction_type in p.get("reactions", {}):
                p["reactions"][reaction_type] += 1
            _save(posts)
            return {"reactions": p["reactions"]}
    return {"error": "post not found"}


@router.post("/api/transmissions/{post_id}/comment")
async def comment_on_transmission(post_id: str, body: dict):
    if not body.get("content", "").strip():
        return {"error": "content is required"}
    posts = _load()
    comment = {
        "id": str(uuid.uuid4()),
        "author": body.get("author", {
            "id": "anon", "name": "Anonymous", "avatar": "◈", "role": "Node"
        }),
        "content": body["content"].strip(),
        "timestamp": int(time.time() * 1000),
    }
    for p in posts:
        if p["id"] == post_id:
            p.setdefault("comments", []).append(comment)
            _save(posts)
            return {"comment": comment}
    return {"error": "post not found"}


@router.delete("/api/transmissions/{post_id}")
async def delete_transmission(post_id: str):
    posts = _load()
    before = len(posts)
    posts = [p for p in posts if p["id"] != post_id]
    if len(posts) == before:
        return {"error": "post not found"}
    _save(posts)
    return {"deleted": post_id}
