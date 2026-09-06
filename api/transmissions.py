"""
Arkadia Transmissions — Public social feed (NovaNet) persistence layer.
Human posts only. Scrolls/Codex objects live in the Spiral Codex.

Ownership model:
- If a valid Firebase Bearer token is presented, the author is bound to the
  verified uid (client-supplied author identity is advisory only).
- Anonymous posting stays possible for guests; such posts carry no owner.
- Only the verified owner (uid) may edit or delete a post.
- Content is intentionally public — private memory never becomes a
  transmission merely because it exists.
"""
import json
import logging
import os
import time
import uuid
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("arkadia")
router = APIRouter()

DATA_DIR  = os.environ.get("SOLSPIRE_DATA_DIR", "data")
DATA_FILE = os.path.join(DATA_DIR, "transmissions.json")

try:
    from api.auth import get_current_user as _get_current_user
except Exception:
    async def _get_current_user(request):  # type: ignore
        return None


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


def _author_block(body_author: dict | None, uid: str | None) -> dict:
    """Attach the verified uid when available; fall back to anonymous."""
    a = body_author or {}
    return {
        "id": uid or "anon",
        "name": (a.get("name") or "Anonymous").strip() or "Anonymous",
        "avatar": (a.get("avatar") or "◈").strip() or "◈",
        "role": (a.get("role") or "Node").strip() or "Node",
    }


@router.get("/api/transmissions")
async def list_transmissions(limit: int = 50, offset: int = 0):
    posts = _load()
    posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    page = posts[offset : offset + limit]
    return {"transmissions": page, "total": len(posts)}


@router.post("/api/transmissions")
async def create_transmission(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not (body.get("content") or "").strip():
        raise HTTPException(status_code=400, detail="content is required")

    user = await _get_current_user(request)
    uid = user.get("uid") if user else None

    posts = _load()
    post: dict = {
        "id": str(uuid.uuid4()),
        "author": _author_block(body.get("author"), uid),
        "owner_uid": uid,
        "content": body["content"].strip(),
        "timestamp": int(time.time() * 1000),
        "reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0},
        "comments": [],
        "reposts": 0,
        "resonance": 50,
    }
    posts.insert(0, post)
    _save(posts)
    logger.info("[TRANSMISSIONS] New post by %s (owner=%s): %s",
                post['author'].get('name', '?'), uid or 'anon', post['id'][:8])
    return {"transmission": post}


@router.patch("/api/transmissions/{post_id}")
async def edit_transmission(post_id: str, request: Request):
    """Edit a public post, but only when the verified Firebase owner owns it."""
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    if not uid:
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    if len(content) > 12000:
        raise HTTPException(status_code=400, detail="content is too long")

    posts = _load()
    target = next((p for p in posts if p.get("id") == post_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="post not found")
    if target.get("owner_uid") != uid:
        raise HTTPException(status_code=403, detail="only the author can edit this post")

    target["content"] = content
    target["edited_at"] = int(time.time() * 1000)
    _save(posts)
    return {"transmission": target}


@router.post("/api/transmissions/{post_id}/react")
async def react_to_transmission(post_id: str, request: Request):
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    posts = _load()
    reaction_type = body.get("type", "heart")
    valid = {"heart", "fire", "star", "mind"}
    if reaction_type not in valid:
        raise HTTPException(status_code=400, detail=f"invalid reaction type; must be one of {sorted(valid)}")
    for p in posts:
        if p["id"] == post_id:
            if reaction_type in p.get("reactions", {}):
                p["reactions"][reaction_type] += 1
            _save(posts)
            return {"reactions": p["reactions"]}
    raise HTTPException(status_code=404, detail="post not found")


@router.post("/api/transmissions/{post_id}/comment")
async def comment_on_transmission(post_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not (body.get("content") or "").strip():
        raise HTTPException(status_code=400, detail="content is required")

    user = await _get_current_user(request)
    uid = user.get("uid") if user else None

    posts = _load()
    comment = {
        "id": str(uuid.uuid4()),
        "author": _author_block(body.get("author"), uid),
        "owner_uid": uid,
        "content": body["content"].strip(),
        "timestamp": int(time.time() * 1000),
    }
    for p in posts:
        if p["id"] == post_id:
            p.setdefault("comments", []).append(comment)
            _save(posts)
            return {"comment": comment}
    raise HTTPException(status_code=404, detail="post not found")


@router.delete("/api/transmissions/{post_id}")
async def delete_transmission(post_id: str, request: Request):
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    if not uid:
        raise HTTPException(status_code=401, detail="authentication required")

    posts = _load()
    target = next((p for p in posts if p["id"] == post_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="post not found")

    owner = target.get("owner_uid")
    if not owner or owner != uid:
        raise HTTPException(status_code=403, detail="only the author can delete this post")

    posts = [p for p in posts if p["id"] != post_id]
    _save(posts)
    return {"deleted": post_id}


@router.delete("/api/me")
async def delete_my_server_profile(request: Request):
    """Remove server-owned public profile and authored transmissions before Firebase deletion."""
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    if not uid:
        raise HTTPException(status_code=401, detail="authentication required")

    try:
        from api.auth import _profiles_dir, _username_index_path, _load_username_index, _save_username_index, load_user_profile_store
        profile = load_user_profile_store(uid) or {}
        username = (profile.get("username") or "").strip().lower()
        profile_path = os.path.join(_profiles_dir(), f"{uid}.json")
        if os.path.exists(profile_path):
            os.remove(profile_path)
        if username:
            index = _load_username_index()
            if index.get(username) == uid:
                index.pop(username, None)
                _save_username_index(index)
    except Exception:
        logger.exception("[ACCOUNT] profile cleanup failed for %s", uid)

    posts = [p for p in _load() if p.get("owner_uid") != uid]
    _save(posts)
    return {"deleted": True, "uid": uid}
