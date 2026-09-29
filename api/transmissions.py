"""Arkadia Transmissions — public social feed persistence layer.

Human posts only. Public author identity is projected from the canonical user
profile store when a post is read or written. Private memory never becomes a
transmission implicitly.
"""
import json
import logging
import os
import time
import uuid
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("arkadia")
router = APIRouter()
DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
DATA_FILE = os.path.join(DATA_DIR, "transmissions.json")

try:
    from api.auth import get_current_user as _get_current_user
except Exception:
    async def _get_current_user(request):
        return None


def _load() -> list[dict]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            pass
    return []


def _save(posts: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def _profile_identity(uid: str | None) -> dict | None:
    if not uid:
        return None
    try:
        from api.auth import load_user_profile_store
        p = load_user_profile_store(uid) or {}
        username = (p.get("username") or "").strip()
        if not username and not p.get("display_name") and not p.get("avatar_url"):
            return None
        return {
            "id": uid,
            "username": username or None,
            "handle": f"@{username}" if username else None,
            "name": (p.get("display_name") or username or "Node").strip(),
            "avatar_url": (p.get("avatar_url") or "").strip() or None,
        }
    except Exception:
        return None


def _author_block(body_author: dict | None, uid: str | None) -> dict:
    """Use verified profile identity when available; client identity is advisory."""
    a = body_author or {}
    current = _profile_identity(uid)
    if current:
        return {
            "id": uid,
            "username": current["username"],
            "handle": current["handle"],
            "name": current["name"],
            "avatar": current["avatar_url"] or (a.get("avatar") or "◈"),
            "avatar_url": current["avatar_url"],
            "role": (a.get("role") or "Node").strip() or "Node",
        }
    return {
        "id": uid or "anon",
        "name": (a.get("name") or "Anonymous").strip() or "Anonymous",
        "avatar": (a.get("avatar") or "◈").strip() or "◈",
        "role": (a.get("role") or "Node").strip() or "Node",
    }


def _hydrate_post(post: dict) -> dict:
    owner = post.get("owner_uid")
    current = _profile_identity(owner)
    if not current:
        return post
    author = dict(post.get("author") or {})
    author.update({
        "id": owner,
        "username": current["username"],
        "handle": current["handle"],
        "name": current["name"],
        "avatar_url": current["avatar_url"],
        "avatar": current["avatar_url"] or author.get("avatar") or "◈",
    })
    post["author"] = author
    return post


@router.get("/api/transmissions")
async def list_transmissions(limit: int = 50, offset: int = 0):
    posts = [_hydrate_post(p) for p in _load()]
    posts.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    return {"transmissions": posts[offset:offset + limit], "total": len(posts)}


@router.post("/api/transmissions")
async def create_transmission(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    posts = _load()
    post = {
        "id": str(uuid.uuid4()),
        "author": _author_block(body.get("author"), uid),
        "owner_uid": uid,
        "content": content,
        "timestamp": int(time.time() * 1000),
        "reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0},
        "comments": [], "reposts": 0, "resonance": 50,
    }
    posts.insert(0, post)
    _save(posts)
    return {"transmission": _hydrate_post(post)}


@router.patch("/api/transmissions/{post_id}")
async def edit_transmission(post_id: str, request: Request):
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
    return {"transmission": _hydrate_post(target)}


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
            p.setdefault("reactions", {}).setdefault(reaction_type, 0)
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
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    posts = _load()
    comment = {"id": str(uuid.uuid4()), "author": _author_block(body.get("author"), uid), "owner_uid": uid, "content": content, "timestamp": int(time.time() * 1000)}
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
    if target.get("owner_uid") != uid:
        raise HTTPException(status_code=403, detail="only the author can delete this post")
    _save([p for p in posts if p["id"] != post_id])
    return {"deleted": post_id}


@router.delete("/api/me")
async def delete_my_server_profile(request: Request):
    """Remove known server-owned social identity and shared social artifacts.

    Firebase account deletion remains the client authentication boundary. This
    route removes the server-side profile, username reservation, authored
    transmissions, and ReasoMate message threads owned by the account.
    """
    user = await _get_current_user(request)
    uid = user.get("uid") if user else None
    if not uid:
        raise HTTPException(status_code=401, detail="authentication required")

    try:
        from api.auth import _profiles_dir, _load_username_index, _save_username_index, load_user_profile_store
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

    _save([p for p in _load() if p.get("owner_uid") != uid])

    # ReasoMate threads are the shared relational memory. Removing the account
    # removes its server-side conversation threads too. No parallel memory store
    # is introduced.
    msg_dir = os.path.join(os.path.dirname(__file__), "..", "data", "messages")
    try:
        if os.path.isdir(msg_dir):
            for name in os.listdir(msg_dir):
                if not name.endswith(".jsonl"):
                    continue
                participants = name[:-6].split("__")
                if uid in participants:
                    try:
                        os.remove(os.path.join(msg_dir, name))
                    except OSError:
                        logger.warning("[ACCOUNT] could not remove message thread %s", name)
    except Exception:
        logger.exception("[ACCOUNT] message cleanup failed for %s", uid)

    return {"deleted": True, "uid": uid}
