#!/usr/bin/env python3
"""
Dual-mode Arkadia console:

- Interactive REPL when run in a TTY (your Termux/dev machine).
- FastAPI HTTP server when no TTY is attached (Render / container deployments).

Endpoints:
  GET  /                 -> basic HTML status page
  GET  /tree             -> JSON tree of corpus
  GET  /preview?path=... -> JSON { name, full_path, preview, mimeType }
  POST /ask              -> JSON { question } -> { answer, context }
  POST /refresh          -> triggers refresh and returns status

Env:
  GEMINI_API_KEY
  ARKADIA_FOLDER_ID
  GOOGLE_SERVICE_ACCOUNT_JSON
"""

import os
import sys
import json
import asyncio
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown

from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context

console = Console()

# Lazy gemini import flag — we'll attempt to import when needed
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# ---------------------------------------------------------------------
# Safe initial corpus load (non-fatal)
# ---------------------------------------------------------------------
def safe_initial_load():
    try:
        snap_local = refresh_arkadia_cache(force=True)
        docs_local = snap_local.get("documents") or []
        tree_local = build_tree_with_paths(docs_local)
        path_map_local = {d.get("full_path") or d.get("name"): d for d in docs_local}
        err = snap_local.get("error")
        if err:
            console.print(f"[yellow]Warning during initial refresh:[/yellow] {err}")
        return snap_local, docs_local, tree_local, path_map_local
    except Exception as e:
        console.print(f"[red]Initial refresh failed (continuing empty corpus): {e}[/red]")
        return {"last_sync": None, "documents": [], "error": str(e)}, [], [], {}

# module-level state
snap, docs, tree_data, path_map = safe_initial_load()

# ---------------------------------------------------------------------
# Reuse ask_gemini from before, but as an async-friendly function
# ---------------------------------------------------------------------
def score_documents(question: str, docs_list: list):
    q_words = set(question.lower().split())
    scored = []
    for d in docs_list:
        text = (d.get("preview") or "").lower()
        if not text:
            scored.append((0, d)); continue
        overlap = len(q_words & set(text.split()))
        scored.append((overlap, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for score, d in scored if score > 0]

def ask_gemini_sync(question: str) -> dict:
    """
    Return: { 'answer': str, 'context': str, 'error': Optional[str] }
    """
    global docs
    if not docs:
        return {"answer": "No documents loaded. Run /refresh.", "context": "", "error": None}

    relevant = score_documents(question, docs)
    if not relevant:
        relevant = sorted(docs, key=lambda d: len(d.get("preview","")), reverse=True)[:5]

    context_parts = []
    for d in relevant[:12]:
        preview = (d.get("preview") or "").strip()
        if not preview:
            continue
        context_parts.append(f"[{d.get('full_path')}] {preview[:1500]}")
    context = "\n\n".join(context_parts)

    if not context:
        return {"answer": "No preview text available for relevant documents.", "context": "", "error": None}

    # If Gemini lib not installed, return prepared context
    if not GEMINI_AVAILABLE:
        return {
            "answer": "[Gemini SDK not installed in this environment. Prepared context returned instead.]",
            "context": context[:4000],
            "error": "gemini_not_installed"
        }

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return {"answer": "GEMINI_API_KEY is not set in environment.", "context": context[:4000], "error": "no_key"}

    # configure genai safely and call
    try:
        try:
            genai.configure(api_key=gemini_key)
        except Exception:
            setattr(genai, "api_key", gemini_key)

        prompt = (
            "You are Arkana, an oracle. Use the documents below to answer precisely and concisely.\n\n"
            f"{context}\n\nQuestion: {question}\n\nAnswer:"
        )

        # Try the modern responses API then fallback to chat
        try:
            resp = genai.responses.create(model="models/text-bison-001", input=prompt, temperature=0.2, max_output_tokens=800)
            text = getattr(resp, "output_text", None)
            if not text:
                out = getattr(resp, "output", None)
                if out and len(out) > 0:
                    try:
                        text = out[0]["content"][0]["text"]
                    except Exception:
                        text = str(out[0])
            return {"answer": text or "[No text returned by Gemini]", "context": context[:4000], "error": None}
        except Exception:
            # fallback chat
            chat_resp = genai.chat.create(model="gemini-1", messages=[{"role": "user", "content": prompt}])
            last = getattr(chat_resp, "last", None)
            if last:
                c = last.get("content") or last.get("message") or {}
                if isinstance(c, list):
                    try:
                        return {"answer": c[0].get("text") or str(c[0]), "context": context[:4000], "error": None}
                    except Exception:
                        return {"answer": str(c), "context": context[:4000], "error": None}
                if isinstance(c, dict):
                    return {"answer": c.get("text") or str(c), "context": context[:4000], "error": None}
            return {"answer": str(chat_resp), "context": context[:4000], "error": None}

    except Exception as e:
        return {"answer": f"Gemini call failed: {e}", "context": context[:4000], "error": str(e)}

# ---------------------------------------------------------------------
# Interactive REPL (TTY) mode
# ---------------------------------------------------------------------
def interactive_repl():
    # declare globals up-front (required before any use)
    global snap, docs, tree_data, path_map

    from rich.prompt import Prompt
    console.print("\n[green]Interactive Arkadia console (TTY mode).[/green]")
    console.print("Commands: tree | preview <full_path> | ask <question> | refresh | exit")
    while True:
        try:
            cmd = Prompt.ask("[cyan]arkadia>[/cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("Goodbye.")
            break
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd.lower() == "tree":
            try:
                console.print(build_tree_with_paths(docs))
            except Exception as e:
                console.print(f"[red]Error rendering tree: {e}[/red]")
            continue
        if cmd.lower().startswith("preview "):
            path = cmd[8:].strip()
            doc = path_map.get(path) or next((d for d in docs if d.get("full_path")==path), None)
            if not doc:
                console.print(f"[red]Path not found:[/red] {path}")
            else:
                console.rule(f"{doc['name']} — {doc.get('full_path')}")
                console.print(Markdown(doc.get("preview") or "*No preview available*"))
            continue
        if cmd.lower().startswith("ask "):
            q = cmd[4:].strip()
            console.print("[cyan]Preparing query...[/cyan]")
            res = ask_gemini_sync(q)
            console.rule("[green]Arkana (response)[/green]")
            try:
                console.print(Markdown(res.get("answer") or str(res)))
            except Exception:
                console.print(res.get("answer") or str(res))
            continue
        if cmd.lower() == "refresh":
            console.print("[cyan]Refreshing Arkadia corpus...[/cyan]")
            snap = refresh_arkadia_cache(force=True)
            if snap.get("error"):
                console.print(f"[yellow]Refresh warning:[/yellow] {snap.get('error')}")
            docs = snap.get("documents") or []
            tree_data = build_tree_with_paths(docs)
            path_map = {d.get("full_path") or d.get("name"): d for d in docs}
            console.print(f"[green]Documents cached:[/green] {len(docs)}")
            continue
        console.print("[yellow]Unknown command[/yellow]")

# ---------------------------------------------------------------------
# FastAPI HTTP server mode (non-TTY)
# ---------------------------------------------------------------------
def start_http_server(host="0.0.0.0", port: int = 5005):
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse, HTMLResponse
        import uvicorn
    except Exception as e:
        console.print(f"[red]FastAPI/uvicorn are not installed: {e}[/red]")
        console.print("[yellow]Install fastapi and uvicorn to run HTTP server mode.[/yellow]")
        return

    app = FastAPI(title="Arkadia Console (HTTP)")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        docs_count = len(docs)
        last = snap.get("last_sync") if snap else None
        html = f"""
        <html>
          <head><title>Arkadia Console</title></head>
          <body>
            <h2>Arkadia Console</h2>
            <p>Documents cached: {docs_count}</p>
            <p>Last sync: {last}</p>
            <p>Endpoints:</p>
            <ul>
              <li>GET /tree</li>
              <li>GET /preview?path=&lt;full_path&gt;</li>
              <li>POST /ask  (JSON: {{ "question": "..." }})</li>
              <li>POST /refresh</li>
            </ul>
          </body>
        </html>
        """
        return HTMLResponse(content=html)

    @app.get("/tree")
    async def get_tree():
        return JSONResponse(content=tree_data)

    @app.get("/preview")
    async def get_preview(path: Optional[str] = None):
        if not path:
            return JSONResponse(status_code=400, content={"error": "missing 'path' query parameter"})
        doc = path_map.get(path) or next((d for d in docs if d.get("full_path")==path or d.get("name")==path), None)
        if not doc:
            return JSONResponse(status_code=404, content={"error": "not found", "path": path})
        return JSONResponse(content={"name": doc.get("name"), "full_path": doc.get("full_path"), "mimeType": doc.get("mimeType"), "preview": doc.get("preview")})

    @app.post("/ask")
    async def post_ask(req: Request):
        body = await req.json()
        question = body.get("question") or body.get("q")
        if not question:
            return JSONResponse(status_code=400, content={"error": "missing question in JSON body"})
        # Run ask in thread to avoid blocking event loop for long gemini call
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, ask_gemini_sync, question)
        return JSONResponse(content=res)

    @app.post("/refresh")
    async def post_refresh():
        global snap, docs, tree_data, path_map
        snap = refresh_arkadia_cache(force=True)
        if snap.get("error"):
            return JSONResponse(status_code=500, content={"error": snap.get("error")})
        docs = snap.get("documents") or []
        tree_data = build_tree_with_paths(docs)
        path_map = {d.get("full_path") or d.get("name"): d for d in docs}
        return JSONResponse(content={"status": "ok", "docs_cached": len(docs), "last_sync": snap.get("last_sync")})

    console.print(f"[green]Starting Arkadia HTTP server on {host}:{port}[/green]")
    uvicorn.run(app, host=host, port=port, log_level="info")

# ---------------------------------------------------------------------
# Entrypoint: choose mode based on TTY
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # If stdin is attached to a TTY --- run the interactive REPL.
    if sys.stdin and sys.stdin.isatty():
        interactive_repl()
    else:
        # non-interactive: run HTTP server (Render)
        port = int(os.getenv("PORT", os.getenv("RENDER_PORT", "5005")))
        start_http_server(host="0.0.0.0", port=port)
