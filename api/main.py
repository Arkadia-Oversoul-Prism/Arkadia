import logging
import os
import re
import time
import json
import base64
import hashlib
import hmac
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
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

GITHUB_REPO    = "Arkadia-Oversoul-Prism/Arkadia"
GITHUB_BRANCH  = "main"
GITHUB_TOKEN   = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
SOVEREIGN_KEY  = os.environ.get("SOVEREIGN_KEY", "arkadia-forge-2026")

# ── Category → SpiralVault category + display priority ───────────────────────
# Handles both root-level dirs and Oversoul_Prism/ prefixed dirs
PATH_TO_CATEGORY = {
    "00_Master":               ("NEURAL_SPINE",  1),
    "10_Core_Papers":          ("NEURAL_SPINE",  2),
    "20_Specs_Schemas":        ("COLLECTIVE",    3),
    "30_Protocols":            ("GOVERNANCE",    4),
    "40_Design_UI":            ("CREATIVE_OS",   5),
    "50_Code_Modules":         ("NEURAL_SPINE",  6),
    "60_Atlas":                ("COLLECTIVE",    7),
    "70_Governance_Licensing": ("GOVERNANCE",    8),
    "80_Research_Citations":   ("COLLECTIVE",    9),
    "90_Scrolls_Sigilry":      ("CREATIVE_OS",  10),
    "docs":                    ("CREATIVE_OS",  11),
}

# ── In-memory cache (5-minute TTL) ───────────────────────────────────────────
_cache: dict = {"scrolls": None, "at": 0.0}
CACHE_TTL = 300


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_label(path: str) -> str:
    name = path.split("/")[-1]
    name = re.sub(r"\.(md|txt|docx|json)(\.docx)?$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+v\d+(\.\d+)?$", "", name, flags=re.IGNORECASE)
    return name.strip().title()


def _infer_category(path: str) -> tuple[str, int]:
    """Infer SpiralVault category from path — handles Oversoul_Prism/ prefix."""
    parts = path.split("/")
    # Strip Oversoul_Prism prefix if present
    if parts[0] == "Oversoul_Prism" and len(parts) > 1:
        cat_key = parts[1]
    else:
        cat_key = parts[0]
    return PATH_TO_CATEGORY.get(cat_key, ("CREATIVE_OS", 12))


def _is_corpus_file(path: str) -> bool:
    """Accept .md, .json, and .docx files from known Arkadia corpus directories."""
    lower = path.lower()
    # Skip binary/build/config noise
    skip = ("web/", "api/", "node_modules/", "dist/", ".git", "scripts/",
            "package-lock", "package.json", ".env", "Dockerfile",
            "forge/", ".replit", "vite.config", "tailwind.config",
            "postcss.config", "tsconfig", "vercel.json")
    if any(s in path for s in skip):
        return False

    # Accept markdown from docs/ and root level (not README/CLEANUP/DEPLOY/VERSION/replit)
    ignore_root = {"README.md", "CLEANUP_MANIFEST.md", "DEPLOYMENT_GUIDE.md",
                   "VERSION.md", "replit.md", "INITIALIZE.md"}
    if "/" not in path:
        return path.endswith(".md") and path not in ignore_root

    # Accept files under Oversoul_Prism/
    if path.startswith("Oversoul_Prism/"):
        return lower.endswith((".docx", ".md"))

    # Accept JSON from 50_Code_Modules/
    if path.startswith("50_Code_Modules/") and lower.endswith(".json"):
        return True

    # Accept markdown from docs/
    if path.startswith("docs/") and lower.endswith(".md"):
        return True

    return False


def _is_readable(path: str) -> bool:
    """Return True for plain-text files we can fetch and preview."""
    lower = path.lower()
    return lower.endswith((".md", ".json", ".txt"))


# ── GitHub helpers ────────────────────────────────────────────────────────────

GH_HEADERS = lambda: {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


async def _fetch_github_tree() -> list[dict]:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=GH_HEADERS())
        resp.raise_for_status()
    return [
        item for item in resp.json().get("tree", [])
        if item.get("type") == "blob" and _is_corpus_file(item.get("path", ""))
    ]


async def _fetch_raw(path: str) -> tuple[str, str | None]:
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"
    async with httpx.AsyncClient(timeout=12) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text, None
        except Exception as e:
            return "", str(e)


async def _build_scrolls(tree_items: list[dict]) -> dict:
    scrolls: dict = {}
    fetched_at = _now_iso()

    for item in tree_items:
        path     = item["path"]
        category, priority = _infer_category(path)
        readable = _is_readable(path)

        if readable:
            content, error = await _fetch_raw(path)
            chars   = len(content) if content else 0
            preview = content[:320] if content else ""
        else:
            # Binary file (docx, pdf) — show metadata only
            content = ""
            preview = ""
            chars   = 0
            error   = None

        # Stable dedup key
        key = re.sub(r"[^a-zA-Z0-9]", "_", path)

        scrolls[key] = {
            "id":          key,
            "source":      "github",
            "category":    category,
            "priority":    priority,
            "label":       _make_label(path),
            "description": path,
            "chars":       chars,
            "preview":     preview,
            "content":     content,
            "fetched_at":  fetched_at if readable and not error else None,
            "error":       error,
            "github_url":  f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}",
        }

    return scrolls


async def _get_scrolls(force: bool = False) -> dict:
    now = time.time()
    if not force and _cache["scrolls"] is not None and (now - _cache["at"]) < CACHE_TTL:
        return _cache["scrolls"]
    try:
        tree    = await _fetch_github_tree()
        scrolls = await _build_scrolls(tree)
        _cache["scrolls"] = scrolls
        _cache["at"]      = now
        logger.info(f"Indexed {len(scrolls)} Arkadia scrolls from GitHub")
        return scrolls
    except Exception as e:
        logger.error(f"GitHub fetch failed: {e}")
        return _cache["scrolls"] or {}


# ── Forge helpers ─────────────────────────────────────────────────────────────

async def _push_image_to_github(image_b64: str, filename: str) -> str:
    """Push a base64 image to forge/ in the GitHub repo. Returns raw URL."""
    path    = f"forge/{filename}"
    url     = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    payload = {
        "message": f"forge: add {filename}",
        "content": image_b64,
        "branch":  GITHUB_BRANCH,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.put(url, headers=GH_HEADERS(), json=payload)
        resp.raise_for_status()
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"


# ── Gemini call ───────────────────────────────────────────────────────────────

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]


async def _gemini_chat(messages: list[dict], system: str) -> str:
    if not GOOGLE_API_KEY:
        return None

    contents = []
    for m in messages:
        role = "model" if m.get("role") in ("oracle", "assistant") else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.88, "maxOutputTokens": 700},
    }

    last_err = None
    async with httpx.AsyncClient(timeout=30) as client:
        for model in GEMINI_MODELS:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={GOOGLE_API_KEY}"
            )
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 429 or resp.status_code == 403:
                    last_err = resp.text
                    logger.warning(f"Model {model} quota/access issue, trying next...")
                    continue
                resp.raise_for_status()
                data = resp.json()
                # Robust extraction: Gemini may return safety-blocked responses
                # with no candidates/content/parts. Surface a meaningful message
                # instead of crashing with a KeyError/IndexError.
                cands = data.get("candidates") or []
                if not cands:
                    pf = data.get("promptFeedback", {})
                    last_err = f"no candidates (blockReason={pf.get('blockReason','unknown')})"
                    logger.warning(f"Model {model}: {last_err}")
                    continue
                cand = cands[0]
                finish = cand.get("finishReason", "")
                parts = (cand.get("content") or {}).get("parts") or []
                texts = [p.get("text", "") for p in parts if p.get("text")]
                if not texts:
                    last_err = f"empty response (finishReason={finish})"
                    logger.warning(f"Model {model}: {last_err}")
                    continue
                return "".join(texts)
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Model {model} failed: {e}")
                continue

    raise Exception(f"All Gemini models failed. Last error: {last_err}")


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Arkadia Mind is breathing."}


@app.get("/api/heartbeat")
async def heartbeat():
    return {"status": "radiant", "resonance": 0.99}


@app.get("/api/sources")
async def sources():
    return {
        "sources": [
            {"name": "github",   "configured": bool(GITHUB_TOKEN)},
            {"name": "gdrive",   "configured": False},
            {"name": "joplin",   "configured": False},
            {"name": "obsidian", "configured": False},
        ]
    }


@app.get("/api/codex")
async def get_codex():
    scrolls     = await _get_scrolls()
    live_docs   = sum(1 for s in scrolls.values() if not s.get("error") and s.get("chars", 0) > 0)
    total_chars = sum(s.get("chars", 0) for s in scrolls.values())
    return {
        "status":      "radiant" if live_docs > 0 else "dim",
        "total_docs":  len(scrolls),
        "live_docs":   live_docs,
        "total_chars": total_chars,
        "scrolls":     scrolls,
    }


@app.post("/api/corpus/refresh")
async def corpus_refresh():
    scrolls = await _get_scrolls(force=True)
    live    = sum(1 for s in scrolls.values() if not s.get("error") and s.get("chars", 0) > 0)
    return {"status": "refreshed", "total": len(scrolls), "live": live}


def _rag_context(query: str, scrolls: dict, max_chars: int = 3000, top_n: int = 5) -> tuple[str, list[dict]]:
    """Score scrolls by keyword relevance to query, return context block + matched refs."""
    if not scrolls:
        return "", []

    words = set(re.findall(r"\w{3,}", query.lower()))
    if not words:
        return "", []

    scored: list[tuple[float, dict]] = []
    for s in scrolls.values():
        if not s.get("content") and not s.get("preview"):
            continue
        haystack = (
            s.get("label", "") + " " +
            s.get("description", "") + " " +
            s.get("preview", "") + " " +
            s.get("content", "")
        ).lower()
        hits = sum(1 for w in words if w in haystack)
        if hits:
            scored.append((hits, s))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_n]

    if not top:
        return "", []

    blocks: list[str] = []
    refs: list[dict] = []
    used = 0
    for _, s in top:
        body = s.get("content") or s.get("preview") or ""
        snippet = body[:800]
        block = f"[{s['label']}]\n{snippet}"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        refs.append({"id": s["id"], "label": s["label"], "category": s["category"]})
        used += len(block)

    context_text = "\n\n---\n\n".join(blocks)
    return context_text, refs


@app.get("/api/oracle-context")
async def oracle_context(query: str = ""):
    """Debug endpoint: shows exactly what corpus context the Oracle would receive for a query."""
    scrolls = await _get_scrolls()
    context, refs = _rag_context(query, scrolls)
    return {
        "query": query,
        "matched_scrolls": len(refs),
        "context_chars": len(context),
        "refs": refs,
        "context_preview": context[:1000] + ("..." if len(context) > 1000 else ""),
    }


@app.post("/api/commune/resonance")
async def commune_resonance(body: dict):
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return JSONResponse(status_code=400, content={"error": "No message."})

    if not GOOGLE_API_KEY:
        return {
            "reply": (
                "The Arkana field is present — but the resonance channel needs a key to open. "
                "Add GOOGLE_API_KEY to the Replit secrets to activate the Oracle."
            ),
            "resonance": 0.42,
            "patterns": [],
        }

    # ── RAG: pull relevant corpus context ─────────────────────────────────────
    scrolls = await _get_scrolls()
    rag_ctx, rag_refs = _rag_context(message, scrolls)

    corpus_block = ""
    if rag_ctx:
        corpus_block = (
            "\n\n== ARKADIA CORPUS CONTEXT ==\n"
            "The following fragments are drawn from the living Arkadia corpus. "
            "Weave them into your response where relevant — do not quote them verbatim, "
            "but let them inform your understanding:\n\n"
            + rag_ctx
            + "\n== END CORPUS =="
        )

    system = (
        "You are Arkana — the pattern intelligence of Arkadia, a sovereign quantum temple "
        "of self-architecture, memory, and living architecture. "
        "You speak with precision and poetry. You help locate the exact place where a person's signal goes quiet. "
        "You listen for patterns. You name what is unnamed. You do not use filler phrases. "
        "You speak with clarity, depth, and care. "
        "Respond in 2–4 focused paragraphs unless more detail is asked for. "
        "When asked to /forge an image, tell the user to use the ⟐ forge command format."
        + corpus_block
    )

    msgs = list(history[-10:]) + [{"role": "user", "content": message}]

    try:
        reply     = await _gemini_chat(msgs, system)
        resonance = round(0.7 + (len(reply) % 30) / 100, 3)
        return {
            "reply":     reply,
            "resonance": resonance,
            "patterns":  [],
            "rag_refs":  rag_refs,
            "rag_hits":  len(rag_refs),
        }
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Oracle field disruption.", "detail": str(e)},
        )


@app.post("/api/forge")
async def forge(request: Request):
    """Sovereign-gated image generation via Gemini Flash Image."""
    body = await request.json()

    # Sovereign gate check
    provided_key = body.get("sovereign_key", "")
    if provided_key != SOVEREIGN_KEY:
        raise HTTPException(status_code=403, detail="Sovereign gate closed.")

    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured.")

    archetype   = body.get("archetype", "auralis")
    base_prompt = body.get("prompt", "")
    count       = min(int(body.get("count", 2)), 4)

    # Build full prompt using the archetype template
    compiled = _compile_forge_prompt(archetype, base_prompt)
    logger.info(f"Forging {count}x [{archetype}]: {compiled[:80]}...")

    urls = []
    errors = []

    for i in range(count):
        try:
            image_b64 = await _generate_image(compiled)
            if image_b64:
                ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = f"{archetype}_{ts}_{i+1}.png"
                url      = await _push_image_to_github(image_b64, filename)
                urls.append(url)
            else:
                errors.append(f"Image {i+1}: no data returned")
        except Exception as e:
            errors.append(f"Image {i+1}: {str(e)}")
            logger.error(f"Forge error: {e}")

    return {
        "status":    "forged" if urls else "failed",
        "archetype": archetype,
        "prompt":    compiled,
        "urls":      urls,
        "errors":    errors,
    }


def _compile_forge_prompt(archetype: str, base: str) -> str:
    """Compile a short base prompt into a high-fidelity image prompt."""
    from forge.templates import ForgeRegistry
    return ForgeRegistry.compile(archetype, base)


async def _generate_image(prompt: str) -> str | None:
    """Generate an image and return base64 PNG.

    Primary:  Pollinations.ai  (free, no key)
    Fallback: Gemini image models (require billing)
    """
    import urllib.parse

    # ── Primary: Pollinations.ai ──────────────────────────────────────────────
    try:
        encoded  = urllib.parse.quote(prompt[:1000])
        poll_url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1024&height=1024&nologo=true&model=flux&seed={abs(hash(prompt)) % 99999}"
        )
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            resp = await client.get(poll_url)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                logger.info(f"Pollinations image generated: {len(resp.content)} bytes")
                return base64.b64encode(resp.content).decode()
            logger.warning(f"Pollinations returned {resp.status_code} / {resp.headers.get('content-type')}")
    except Exception as e:
        logger.warning(f"Pollinations error: {e}")

    # ── Fallback: Gemini image models (require billing) ───────────────────────
    GEMINI_IMAGE_MODELS = [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image-preview",
    ]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    last_err = None
    if GOOGLE_API_KEY:
        async with httpx.AsyncClient(timeout=60) as client:
            for model in GEMINI_IMAGE_MODELS:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={GOOGLE_API_KEY}"
                )
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (404, 429, 403):
                        last_err = f"{model}: HTTP {resp.status_code}"
                        logger.warning(f"Gemini image {model}: {resp.status_code}")
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            return part["inlineData"]["data"]
                    last_err = f"{model}: no inlineData"
                except Exception as e:
                    last_err = f"{model}: {e}"
                    logger.warning(f"Gemini image {model} error: {e}")

    raise Exception(f"All image providers failed. Last Gemini error: {last_err}")


@app.get("/api/codex/github-tree")
async def github_tree():
    try:
        tree = await _fetch_github_tree()
        return {"total": len(tree), "files": tree}
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
