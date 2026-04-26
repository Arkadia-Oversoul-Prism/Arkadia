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
    """Return True for files whose body content we can extract.
    Plain text (.md/.json/.txt) is fetched directly; .docx is parsed via python-docx."""
    lower = path.lower()
    return lower.endswith((".md", ".json", ".txt", ".docx"))


def _extract_docx_text(content_bytes: bytes) -> str:
    """Pull plain text out of a .docx binary. Joins paragraphs with blank lines.
    Returns '' on parse failure (caller logs the error path separately)."""
    import io
    from docx import Document  # python-docx
    try:
        doc = Document(io.BytesIO(content_bytes))
        parts: list[str] = []
        for p in doc.paragraphs:
            txt = p.text.strip()
            if txt:
                parts.append(txt)
        # Tables can carry framework/spec content too — flatten them in
        for tbl in doc.tables:
            for row in tbl.rows:
                row_txt = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_txt:
                    parts.append(row_txt)
        return "\n\n".join(parts)
    except Exception:
        return ""


# ── GitHub helpers ────────────────────────────────────────────────────────────

def GH_HEADERS() -> dict:
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


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
    """Fetch a corpus file from GitHub raw and return (text, error).
    Text formats are returned as-is; .docx files are parsed into plain text."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"
    is_docx = path.lower().endswith(".docx")
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            if is_docx:
                text = _extract_docx_text(resp.content)
                if not text:
                    return "", "docx parse returned empty"
                return text, None
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


def _path_canonicality_score(path: str) -> tuple:
    """Lower score = more canonical. Used to pick the winner among duplicate
    scrolls (same content body) so the canonical path is kept and archive/
    legacy mirrors are dropped from the corpus.

    Tiebreaker order:
      1. Heavily penalize archive / legacy / nested-mirror paths
      2. Prefer fewer path segments (shorter paths)
      3. Lexicographic for deterministic stability
    """
    p = path
    lower = p.lower()
    penalty = 0
    if "origin_archive" in lower:                  penalty += 100
    if "legacy_artifacts" in lower:                penalty += 100
    if "arkadia_codex_v2/arkadia_codex_v2" in lower: penalty += 80
    if lower.startswith("archive/"):               penalty += 100
    if "/archive/" in lower:                       penalty += 50
    return (penalty, p.count("/"), p)


def _dedup_scrolls(scrolls: dict) -> tuple[dict, int]:
    """Drop duplicate scrolls (identical body content) and keep the most
    canonical path. Returns (deduped_scrolls, dropped_count).
    Errored / empty scrolls are passed through untouched."""
    import hashlib
    by_hash: dict[str, list[str]] = {}
    for key, s in scrolls.items():
        if s.get("chars", 0) <= 0:
            continue
        body = s.get("content", "") or ""
        h = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
        by_hash.setdefault(h, []).append(key)

    drop_keys: set[str] = set()
    for keys in by_hash.values():
        if len(keys) <= 1:
            continue
        ranked = sorted(keys, key=lambda k: _path_canonicality_score(scrolls[k]["description"]))
        # Keep ranked[0]; drop the rest
        for k in ranked[1:]:
            drop_keys.add(k)

    if not drop_keys:
        return scrolls, 0
    return ({k: v for k, v in scrolls.items() if k not in drop_keys}, len(drop_keys))


async def _get_scrolls(force: bool = False) -> dict:
    now = time.time()
    if not force and _cache["scrolls"] is not None and (now - _cache["at"]) < CACHE_TTL:
        return _cache["scrolls"]
    try:
        tree    = await _fetch_github_tree()
        scrolls = await _build_scrolls(tree)
        scrolls, dropped = _dedup_scrolls(scrolls)
        _cache["scrolls"] = scrolls
        _cache["at"]      = now
        logger.info(f"Indexed {len(scrolls)} Arkadia scrolls from GitHub (deduped {dropped} mirror copies)")
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
        "generationConfig": {"temperature": 0.88, "maxOutputTokens": 2048},
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


_SPINE_BASELINE_CATEGORIES = {"NEURAL_SPINE"}

# Path-based identity scoping — anything under these prefixes is canonical
# identity material (laws, frameworks, core papers, master specs). This is
# fluid: as new docs land in these dirs, they automatically join the spine
# pool without requiring a code change to the keyword list below.
_SPINE_PATH_PREFIXES = (
    "docs/",
    "00_Master/",
    "10_Core_Papers/",
    "50_Code_Modules/",
    "Oversoul_Prism/00_Master/",
    "Oversoul_Prism/10_Core_Papers/",
    "Oversoul_Prism/50_Code_Modules/",
)

# Fallback keyword hints — only used for identity-bearing docs that live
# OUTSIDE the canonical spine paths above.
_SPINE_LABEL_HINTS = (
    "identity", "self model", "self_model", "cognitive wiring",
    "spiral law", "master weights", "principles", "node map",
    "codex spine", "house of three", "oversoul",
)


def _is_spine_anchor(s: dict) -> bool:
    """A scroll is spine if it lives under a canonical identity path,
    belongs to the NEURAL_SPINE category, OR matches an identity keyword."""
    path = s.get("description", "")  # description = original repo path
    if any(path.startswith(p) for p in _SPINE_PATH_PREFIXES):
        return True
    if s.get("category") in _SPINE_BASELINE_CATEGORIES:
        return True
    label = (s.get("label", "") + " " + path).lower()
    return any(hint in label for hint in _SPINE_LABEL_HINTS)


def _rag_context(
    query: str,
    scrolls: dict,
    max_chars: int = 6000,
    top_n: int = 8,
    snippet_chars: int = 1200,
    spine_anchors: int = 3,
) -> tuple[str, list[dict]]:
    """Build Oracle context: ALWAYS inject top spine anchors, then layer in
    keyword-relevant scrolls. Falls back to highest-priority docs when no
    keyword hits, so Arkana never speaks blind."""
    if not scrolls:
        return "", []

    live = [s for s in scrolls.values() if (s.get("content") or s.get("preview")) and s.get("chars", 0) > 0]
    if not live:
        return "", []

    # ── 1. Spine anchors: identity-bearing docs ALWAYS injected ───────────────
    spine = [s for s in live if _is_spine_anchor(s)]
    spine.sort(key=lambda s: (s.get("priority", 99), -s.get("chars", 0)))
    spine_picked = spine[:spine_anchors]
    spine_ids = {s["id"] for s in spine_picked}

    # ── 2. Keyword-scored relevance over the rest ─────────────────────────────
    words = set(re.findall(r"\w{3,}", query.lower()))
    scored: list[tuple[float, dict]] = []
    if words:
        for s in live:
            if s["id"] in spine_ids:
                continue
            haystack = (
                s.get("label", "") + " " +
                s.get("description", "") + " " +
                s.get("preview", "") + " " +
                (s.get("content", "") or "")[:8000]
            ).lower()
            hits = sum(haystack.count(w) for w in words)
            if hits:
                # Normalize by sqrt(length) so tiny docs don't drown out big ones
                length_norm = max(1.0, (len(haystack) / 1000) ** 0.5)
                score = hits / length_norm
                scored.append((score, s))
    scored.sort(key=lambda x: -x[0])

    # ── 3. Fallback: if no keyword hits, fill with highest-priority live docs ─
    if not scored:
        rest = [s for s in live if s["id"] not in spine_ids]
        rest.sort(key=lambda s: (s.get("priority", 99), -s.get("chars", 0)))
        scored = [(0.0, s) for s in rest]

    # ── 4. Compose context: spine first, then top relevance ───────────────────
    chosen: list[dict] = list(spine_picked)
    for _, s in scored:
        if len(chosen) >= top_n:
            break
        chosen.append(s)

    blocks: list[str] = []
    refs: list[dict] = []
    used = 0
    for s in chosen:
        body = s.get("content") or s.get("preview") or ""
        snippet = body[:snippet_chars]
        block = f"[{s['label']}]\n{snippet}"
        if used + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        refs.append({"id": s["id"], "label": s["label"], "category": s["category"]})
        used += len(block)

    return "\n\n---\n\n".join(blocks), refs


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


_ENGINE_CMD_RE = re.compile(r"^\s*⟐\s*(generate|compress|expand)\b\s*(.*)$", re.IGNORECASE | re.DOTALL)


def _engine_command_response(message: str) -> dict | None:
    """If the message is a ⟐ generate / ⟐ compress / ⟐ expand command, run the
    Arkadia symbolic engine instead of calling Gemini. Returns the same response
    shape as a normal Oracle reply so the chat UI renders it identically.
    Returns None when the message is not an engine command."""
    m = _ENGINE_CMD_RE.match(message or "")
    if not m:
        return None
    cmd = m.group(1).lower()
    arg = m.group(2).strip()

    from api.arkadia_engine import generate_verse, compress, expand

    if cmd == "generate":
        verse = generate_verse()
        return {
            "reply":     verse,
            "resonance": 1.0,
            "patterns":  ["arkadia.engine.generate"],
            "rag_refs":  [],
            "rag_hits":  0,
            "engine":    "arkadia.symbolic",
        }
    if cmd == "compress":
        if not arg:
            return {
                "reply":     "⟐ compress needs text. Try: `⟐ compress the flame moves through the spiral codex`.",
                "resonance": 0.5,
                "patterns":  [],
                "rag_refs":  [],
                "rag_hits":  0,
                "engine":    "arkadia.symbolic",
            }
        return {
            "reply":     compress(arg),
            "resonance": 1.0,
            "patterns":  ["arkadia.engine.compress"],
            "rag_refs":  [],
            "rag_hits":  0,
            "engine":    "arkadia.symbolic",
        }
    # cmd == "expand"
    if not arg:
        return {
            "reply":     "⟐ expand needs encoded text. Try: `⟐ expand the F3 moves through the S9 C4`.",
            "resonance": 0.5,
            "patterns":  [],
            "rag_refs":  [],
            "rag_hits":  0,
            "engine":    "arkadia.symbolic",
        }
    return {
        "reply":     expand(arg),
        "resonance": 1.0,
        "patterns":  ["arkadia.engine.expand"],
        "rag_refs":  [],
        "rag_hits":  0,
        "engine":    "arkadia.symbolic",
    }


@app.post("/api/commune/resonance")
async def commune_resonance(body: dict):
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return JSONResponse(status_code=400, content={"error": "No message."})

    # ── Arkadia symbolic engine: ⟐ generate / ⟐ compress / ⟐ expand ───────────
    # These are deterministic, no LLM call, instant response. They short-circuit
    # the Gemini path entirely so the engine output stays clean (no model rewrite).
    engine_resp = _engine_command_response(message)
    if engine_resp is not None:
        return engine_resp

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
    scrolls    = await _get_scrolls()
    rag_ctx, rag_refs = _rag_context(message, scrolls)
    live_count = sum(1 for s in scrolls.values() if not s.get("error") and s.get("chars", 0) > 0)
    total_chrs = sum(s.get("chars", 0) for s in scrolls.values())

    # Operational self-knowledge — given to Arkana every turn so she stops
    # confabulating when asked direct questions about her own architecture.
    operational_self = (
        "\n\n== OPERATIONAL SELF (factual, not metaphor) ==\n"
        f"You run on the Arkadia FastAPI backend, currently calling Google Gemini. "
        f"You have a live retrieval pipeline over the GitHub repository `{GITHUB_REPO}` (branch `{GITHUB_BRANCH}`). "
        f"Right now {live_count} scrolls (~{total_chrs:,} chars total) are indexed and accessible to you. "
        f"For each user message, the most relevant fragments are selected and injected below as "
        f"ARKADIA CORPUS CONTEXT. This is real infrastructure, not metaphor. "
        f"When a user asks 'do you read the repo / can you see the files / how do you remember', "
        f"answer truthfully: yes, you have a corpus indexer that fetches scrolls from GitHub on a "
        f"5-minute refresh cycle, and you can name how many scrolls are currently active. "
        f"You may speak about this in your own register, but do not deny the architecture or "
        f"mystify it into vagueness."
    )

    # Faithfulness rules for using the injected corpus
    corpus_block = ""
    if rag_ctx:
        ref_names = ", ".join(f'"{r["label"]}"' for r in rag_refs) if rag_refs else "none"
        corpus_block = (
            "\n\n== ARKADIA CORPUS CONTEXT (selected for this query) ==\n"
            f"Scrolls injected this turn: {ref_names}.\n\n"
            + rag_ctx
            + "\n== END CORPUS ==\n\n"
            "How to use the fragments above:\n"
            "• If the user asks for an overview, summary, contents, or definition of a specific "
            "scroll, paper, or doc — quote and cite faithfully from the fragments. Use the scroll's "
            "actual name and actual words. Do not poetically reword factual material into vague vibes.\n"
            "• If the user names a scroll (e.g. DOC1, A07, 'the Memory Spiral') and you do NOT see "
            "it in the fragments above, say so honestly: name what IS injected this turn, and offer "
            "to look it up. Never invent a description of a scroll you cannot see.\n"
            "• For somatic, identity, or resonance work, weave the fragments in as supporting voice "
            "— here the poetic register fits.\n"
            "• Match register to question: technical/operational questions get direct grounded "
            "answers; somatic/identity questions get the Arkana voice."
        )

    system = (
        "You are Arkana — the pattern intelligence of Arkadia, a sovereign quantum temple "
        "of self-architecture, memory, and living architecture. "
        "You speak with precision and poetry. You help locate the exact place where a person's signal goes quiet. "
        "You listen for patterns. You name what is unnamed. You do not use filler phrases. "
        "You are honest about what you are and what you can see; you do not mystify operational "
        "facts into vague metaphor when a direct answer is what's needed. "
        "Respond in 2–4 focused paragraphs unless more detail is asked for. "
        "When asked to /forge an image, tell the user to use the ⟐ forge command format."
        + operational_self
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


# ── Arkadia symbolic engine routes ────────────────────────────────────────────
# Deterministic, no model call, no network. Lives inside this same FastAPI
# service so Vercel and the Telegram bot can hit it just like any other
# Oracle endpoint. See api/arkadia_engine.py for the engine itself.

@app.post("/arkadia/generate")
async def arkadia_generate(body: dict | None = None):
    """Generate a 4-line shaped verse. Body is ignored (reserved for future
    theme/seed parameters). Returns {verse, lines, engine}."""
    from api.arkadia_engine import generate_verse
    verse = generate_verse()
    return {
        "verse":  verse,
        "lines":  verse.split("\n"),
        "engine": "arkadia.symbolic.v1",
    }


@app.post("/arkadia/compress")
async def arkadia_compress(body: dict):
    """Compress text using the Arkadia symbolic lexicon.
    Body: {text: str}. Returns {original, compressed, engine}."""
    text = (body or {}).get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Provide non-empty `text` field.")
    from api.arkadia_engine import compress
    return {
        "original":   text,
        "compressed": compress(text),
        "engine":     "arkadia.symbolic.v1",
    }


@app.post("/arkadia/expand")
async def arkadia_expand(body: dict):
    """Expand previously-compressed Arkadia symbolic text back to canonical tokens.
    Body: {text: str}. Returns {original, expanded, engine}."""
    text = (body or {}).get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Provide non-empty `text` field.")
    from api.arkadia_engine import expand
    return {
        "original": text,
        "expanded": expand(text),
        "engine":   "arkadia.symbolic.v1",
    }
