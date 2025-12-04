#!/usr/bin/env python3
"""
arkadia_console.py
Unified console + server bootstrap for Arkadia.

Behavior:
- If running with a TTY (interactive), run the console UI.
- If NOT running with a TTY (Render / Docker), start the ASGI server
  (uvicorn -> arkana_app:app) after refreshing corpus.

Depends on:
- arkadia_drive_sync: refresh_arkadia_cache, build_tree_with_paths, get_corpus_context
- brain: ArkanaBrain
- arkana_app:app (FastAPI ASGI app)
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional

# use rich if available for prettier console output
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.tree import Tree
except Exception:
    Console = None
    Markdown = None
    Tree = None

logger = logging.getLogger("arkadia_console")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s: %(message)s")

# Import Arkadia helpers (drive sync, tree builder, corpus context)
try:
    from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context
except Exception as e:
    logger.exception("Failed to import arkadia_drive_sync helpers: %s", e)
    # rethrow so user sees the import issue immediately
    raise

# ArkanaBrain wraps Gemini / fallback logic
try:
    from brain import ArkanaBrain
except Exception as e:
    logger.exception("Failed to import ArkanaBrain from brain.py: %s", e)
    ArkanaBrain = None  # handle later

# FastAPI app (for server mode)
# We will import uvicorn lazily inside run_server to avoid hard dependency in interactive mode
ASGI_APP_PATH = "arkana_app:app"

# Console instance
console = Console() if Console else None

# ---------- Core helpers ----------

def get_docs_snapshot(force: bool = False) -> Dict[str, Any]:
    """
    Refresh and return the current Arkadia corpus snapshot.
    """
    try:
        snap = refresh_arkadia_cache(force=force)
        logger.info("%s documents cached", len(snap.get("documents") or []))
        return snap
    except Exception as e:
        logger.exception("Failed to refresh Arkadia cache: %s", e)
        return {"last_sync": None, "documents": [], "error": str(e)}

def build_tree_and_map(docs: List[Dict[str, Any]]):
    """
    Returns (tree_nodes, path_map) where path_map maps full_path->doc
    """
    tree_nodes = build_tree_with_paths(docs) if docs else []
    path_map = { (d.get("full_path") or d.get("name") or d.get("id")): d for d in docs }
    return tree_nodes, path_map

# ---------- Arkana / Gemini wrapper ----------
class ArkanaAgent:
    def __init__(self):
        self.brain = ArkanaBrain() if ArkanaBrain else None

    async def ask(self, sender: str, question: str, history: Optional[List[Dict[str,str]]] = None) -> str:
        if not self.brain:
            return "ArkanaBrain not available. 'ask' feature disabled."
        try:
            # ArkanaBrain.generate_reply is async
            return await self.brain.generate_reply(sender=sender, message=question, history=history)
        except Exception as e:
            logger.exception("Arkana ask failed: %s", e)
            return f"Arkana generation error: {e}"

# ---------- Console UI (interactive) ----------
def show_dashboard(snap: Dict[str, Any]):
    docs = snap.get("documents") or []
    last_sync = snap.get("last_sync")
    err = snap.get("error")
    header = "ARKADIA DASHBOARD"
    if console:
        console.rule(f"[bold blue]{header}[/bold blue]")
        console.print(f"Last sync: {last_sync}")
        console.print(f"Documents cached: {len(docs)}")
        if err:
            console.print(f"[red]Sync errors:[/red] {err}")
        console.print("\n[bold]Top previews:[/bold]")
        console.print(get_corpus_context(max_documents=5, max_preview_chars=300))
    else:
        print("──────────────────────── ARKADIA DASHBOARD ────────────────────────")
        print("Last sync:", last_sync)
        print("Documents cached:", len(docs))
        if err:
            print("Sync errors:", err)
        print("\nTop previews:\n")
        print(get_corpus_context(max_documents=5, max_preview_chars=300))

def build_tree_ui(tree_nodes):
    if Tree is None:
        # fallback simple list string
        lines = []
        for n in tree_nodes:
            lines.append(n.get("full_path") or n.get("name"))
        return "\n".join(lines)
    root = Tree("ARKADIA CORPUS")
    def add_node(branch, node):
        name = node.get("name") or "<unnamed>"
        mime = node.get("mimeType","")
        path = node.get("full_path") or name
        label = f"{name} [{mime}]"
        if path:
            label += f" | {path}"
        sub = branch.add(label)
        for c in node.get("children", []):
            add_node(sub, c)
    for n in tree_nodes:
        add_node(root, n)
    return root

# ---------- Non-interactive server runner ----------
def run_server():
    """Start ASGI server (uvicorn) for arkana_app:app"""
    try:
        import uvicorn
    except Exception as e:
        logger.exception("uvicorn not installed: %s", e)
        raise

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", os.environ.get("RENDER_PORT", 5005)))
    logger.info("Starting Arkadia ASGI server on %s:%s", host, port)
    # This will block — intended in non-interactive container
    uvicorn.run(ASGI_APP_PATH, host=host, port=port, log_level="info", access_log=False)

# ---------- Interactive main loop ----------
def interactive_loop(agent: ArkanaAgent):
    # refresh corpus and show dashboard
    snap = get_docs_snapshot(force=True)
    docs = snap.get("documents") or []
    tree_nodes, path_map = build_tree_and_map(docs)
    show_dashboard(snap)

    if console and Tree:
        console.print(build_tree_ui(tree_nodes))
    else:
        print("\n".join([n.get("full_path") or n.get("name") for n in tree_nodes[:200]]))

    print("\nCommands: tree | preview <full_path> | ask <question> | refresh | exit")

    # simple in-memory conversation history per session (not persisted here)
    conversation_history: List[Dict[str,str]] = []

    while True:
        try:
            prompt = "arkadia> "
            if console:
                # rich prompt fallback: just use input for simplicity
                cmd = input(prompt).strip()
            else:
                cmd = input(prompt).strip()
        except EOFError:
            print("\nExiting Arkadia Console.")
            break
        except KeyboardInterrupt:
            print("\nExiting Arkadia Console (keyboard interrupt).")
            break

        if not cmd:
            continue
        lower = cmd.lower()

        if lower in ("exit", "quit"):
            print("Exiting Arkadia Console.")
            break

        if lower == "tree":
            # rebuild tree in case refreshes happened
            snap = get_docs_snapshot(force=False)
            docs = snap.get("documents") or []
            tree_nodes, path_map = build_tree_and_map(docs)
            if console and Tree:
                console.print(build_tree_ui(tree_nodes))
            else:
                for n in tree_nodes:
                    print(n.get("full_path") or n.get("name"))
            continue

        if lower.startswith("preview "):
            path = cmd[len("preview "):].strip()
            doc = path_map.get(path)
            if not doc:
                print(f"Path not found: {path}")
            else:
                title = doc.get("name")
                fp = doc.get("full_path") or title
                print(f"\nName: {title}\nFull Path: {fp}\nMIME Type: {doc.get('mimeType')}\n\nPreview:\n")
                preview = doc.get("preview") or "*No preview available*"
                if Markdown and console:
                    console.rule(f"{title} — {fp}")
                    console.print(Markdown(preview))
                else:
                    print(preview)
            continue

        if lower == "refresh":
            snap = get_docs_snapshot(force=True)
            docs = snap.get("documents") or []
            tree_nodes, path_map = build_tree_and_map(docs)
            print("Refreshed. Documents cached:", len(docs))
            continue

        if lower.startswith("ask "):
            question = cmd[len("ask "):].strip()
            # prepare brief context: top N previews
            context_entries = [d.get("preview","")[:800] for d in docs[:6]]
            try:
                # run ArkanaBrain ask
                ans = asyncio.run(agent.ask(sender="El'Zahar", question=question, history=conversation_history))
            except Exception as e:
                logger.exception("ask failed: %s", e)
                ans = f"Error running Arkana: {e}"
            print("\nArkana Answer:\n")
            print(ans)
            # append to local history
            conversation_history.append({"role":"user","content":question})
            conversation_history.append({"role":"assistant","content":ans})
            continue

        # Unknown command
        print("Unknown command. Available: tree | preview <full_path> | ask <question> | refresh | exit")

# ---------- Bootstrap ----------
def main_interactive():
    agent = ArkanaAgent()
    interactive_loop(agent)

def main_server_mode():
    # Refresh corpus once, then start server
    try:
        snap = get_docs_snapshot(force=True)
        logger.info("%s documents cached", len(snap.get("documents") or []))
    except Exception:
        logger.exception("Failed refreshing corpus for server mode")
    run_server()

if __name__ == "__main__":
    # Decide mode: interactive if stdin is a TTY
    interactive = sys.stdin.isatty()
    if interactive:
        logger.info("Interactive TTY detected — starting interactive console.")
        main_interactive()
    else:
        logger.info("No TTY detected — starting as service (non-interactive).")
        main_server_mode()
