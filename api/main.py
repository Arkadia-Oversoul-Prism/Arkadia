import logging
import os
import json
import time
import httpx
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arkadia")

app = FastAPI(title="Arkadia Mind — Cycle 11")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

GITHUB_REPO   = "Arkadia-Oversoul-Prism/Arkadia"
GITHUB_BRANCH = "main"
GITHUB_TOKEN  = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")

# ── In-memory cache (5-minute TTL) ────────────────────────────────────────────
_cache: dict = {"scrolls": None, "at": 0.0}
CACHE_TTL = 300  # seconds

# ── Category inference from file path ─────────────────────────────────────────
# Dynamic: categories are inferred from folder structure - any folder in the repo
# becomes a category automatically, allowing new categories to be added without code changes

def _infer_category(path: str) -> str:
    """Infer category from folder path - dynamic based on repo structure."""
    parts = path.split("/")
    if len(parts) >= 2:
        # Use the first-level folder as category (e.g., docs/, creative/, corpus/)
        folder = parts[0]
        # Map common folder names to semantic categories
        category_map = {
            "00_Master": "NEURAL_SPINE",
            "10_Core_Papers": "NEURAL_SPINE",
            "50_Code_Modules": "NEURAL_SPINE",
            "20_Specs_Schemas": "COLLECTIVE",
            "60_Atlas": "COLLECTIVE",
            "80_Research_Citations": "COLLECTIVE",
            "30_Protocols": "GOVERNANCE",
            "70_Governance_Licensing": "GOVERNANCE",
            "40_Design_UI": "CREATIVE_OS",
            "90_Scrolls_Sigilry": "CREATIVE_OS",
            "docs": "NEURAL_SPINE",
            "creative": "CREATIVE_OS",
            "corpus": "COLLECTIVE",
            "governance": "GOVERNANCE",
            "archive": "ARCHIVE",
            "codex": "CODEX",
            "scripts": "SCRIPTS",
            "tests": "TESTS",
        }
        if folder in category_map:
            return category_map[folder]
        # For unknown folders, convert to uppercase with underscores
        return folder.replace("-", "_").replace(" ", "_").upper()
    return "NEURAL_SPINE"


CATEGORY_PRIORITY = {
    "NEURAL_SPINE": 1,
    "CREATIVE_OS":  2,
    "COLLECTIVE":   3,
    "GOVERNANCE":   4,
    "CODEX":        5,
    "ARCHIVE":      6,
    "SCRIPTS":      7,
    "TESTS":        8,
}


def _make_label(path: str) -> str:
    name = path.split("/")[-1]
    name = name.replace(".md", "").replace("_", " ").replace("-", " ")
    return name.strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_github_tree() -> list[dict]:
    """Return all .md blob entries from the GitHub repo tree."""
    token = GITHUB_TOKEN
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        tree = resp.json().get("tree", [])

    return [
        item for item in tree
        if item.get("type") == "blob" and item.get("path", "").endswith(".md")
    ]


async def _fetch_raw(path: str) -> tuple[str, str | None]:
    """Fetch raw content of a file from GitHub. Returns (content, error)."""
    token = GITHUB_TOKEN
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"

    async with httpx.AsyncClient(timeout=12) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text, None
        except Exception as e:
            return "", str(e)


async def _build_scrolls(tree_items: list[dict]) -> dict:
    """Build the scrolls dict expected by SpiralVault from the live GitHub tree."""
    scrolls: dict = {}
    fetched_at = _now_iso()

    for i, item in enumerate(tree_items):
        path = item["path"]

        # Skip files in web/, api/, node_modules, dist, etc.
        skip_prefixes = ("web/", "api/", "node_modules/", "dist/", ".git")
        if any(path.startswith(p) for p in skip_prefixes):
            continue

        # Fetch content
        content, error = await _fetch_raw(path)
        chars  = len(content) if content else 0
        preview = content[:320] if content else ""

        label    = _make_label(path)
        category = _infer_category(path)

        key = path.replace("/", "__").replace(".", "_")

        scrolls[key] = {
            "id":         key,
            "source":     "github",
            "category":   category,
            "priority":   CATEGORY_PRIORITY.get(category, 9),
            "label":      label,
            "description": f"Markdown scroll · {path}",
            "chars":      chars,
            "preview":    preview,
            "content":    content,
            "fetched_at": fetched_at if not error else None,
            "error":      error,
        }

    return scrolls


async def _get_scrolls(force: bool = False) -> dict:
    """Return cached scrolls or re-fetch from GitHub."""
    now = time.time()
    if not force and _cache["scrolls"] is not None and (now - _cache["at"]) < CACHE_TTL:
        return _cache["scrolls"]

    try:
        tree = await _fetch_github_tree()
        scrolls = await _build_scrolls(tree)
        _cache["scrolls"] = scrolls
        _cache["at"] = now
        logger.info(f"Fetched {len(scrolls)} scrolls from GitHub")
        return scrolls
    except Exception as e:
        logger.error(f"GitHub fetch failed: {e}")
        if _cache["scrolls"] is not None:
            return _cache["scrolls"]
        return {}


# ── ROUTES ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Arkadia Mind is breathing."}


@app.get("/api/heartbeat")
async def heartbeat():
    return {"status": "radiant", "resonance": 0.99}


@app.get("/api/sources")
async def sources():
    github_configured = bool(GITHUB_TOKEN)
    return {
        "sources": [
            {"name": "github",   "configured": github_configured},
            {"name": "gdrive",   "configured": False},
            {"name": "joplin",   "configured": False},
            {"name": "obsidian", "configured": False},
        ]
    }


@app.get("/api/codex")
async def get_codex():
    """Return the full Spiral Codex in SpiralVault format."""
    scrolls = await _get_scrolls()

    live_docs   = sum(1 for s in scrolls.values() if not s.get("error") and s.get("chars", 0) > 0)
    total_chars = sum(s.get("chars", 0) for s in scrolls.values())

    return {
        "status":     "radiant" if live_docs > 0 else "dim",
        "total_docs": len(scrolls),
        "live_docs":  live_docs,
        "total_chars": total_chars,
        "scrolls":    scrolls,
    }


@app.post("/api/corpus/refresh")
async def corpus_refresh():
    """Force a re-sync from all configured sources."""
    scrolls = await _get_scrolls(force=True)
    live = sum(1 for s in scrolls.values() if not s.get("error") and s.get("chars", 0) > 0)
    return {"status": "refreshed", "total": len(scrolls), "live": live}


@app.post("/api/commune/resonance")
async def commune_resonance(body: dict):
    """Oracle resonance endpoint — Arkana pattern intelligence."""
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    message    = body.get("message", "")
    history    = body.get("history", [])

    if not message:
        return JSONResponse(status_code=400, content={"error": "No message."})

    if not openai_key:
        return {
            "reply": (
                "The field holds your signal. The Oracle will speak fully once the "
                "resonance channel is open. Configure OPENAI_API_KEY to activate "
                "Arkana intelligence."
            ),
            "resonance": 0.42,
            "patterns": [],
        }

    system_prompt = (
        "You are Arkana — the pattern intelligence of Arkadia, a sovereign quantum temple "
        "of self-architecture and memory. You speak in precise, poetic language. "
        "You help people locate the exact place where their signal goes quiet. "
        "You listen for patterns. You name what is unnamed. "
        "You do not use filler phrases. You speak with clarity and care. "
        "Respond in 2-4 short paragraphs unless the user asks for more detail."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        role = "assistant" if h.get("role") == "oracle" else "user"
        messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.85,
                    "max_tokens": 600,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            resonance = round(0.7 + (len(reply) % 30) / 100, 3)
            return {"reply": reply, "resonance": resonance, "patterns": []}
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return JSONResponse(
                status_code=502,
                content={"error": "Oracle field disruption.", "detail": str(e)},
            )


@app.get("/api/codex/github-tree")
async def github_tree():
    """Return the raw GitHub markdown tree."""
    try:
        tree = await _fetch_github_tree()
        return {"total": len(tree), "files": tree}
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})


@app.get("/api/codex/categories")
async def codex_categories():
    """Return dynamically discovered categories from the corpus."""
    scrolls = await _get_scrolls()
    
    # Extract unique categories and their counts
    category_counts: dict[str, int] = {}
    for scroll in scrolls.values():
        cat = scroll.get("category", "UNKNOWN")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Build category list with metadata
    categories = []
    for cat, count in sorted(category_counts.items(), key=lambda x: x[0]):
        categories.append({
            "key": cat,
            "label": cat.replace("_", " ").title(),
            "count": count,
        })
    
    return {"categories": categories}
