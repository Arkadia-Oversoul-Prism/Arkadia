#!/usr/bin/env python3
"""
arkadia_console.py

Console UI for Arkadia. Robust startup: does not crash when Drive / Gemini are misconfigured.
Provides simple commands:
  - tree
  - preview <full_path>
  - ask <question>
  - refresh
  - exit

Reads:
  - GEMINI_API_KEY (optional; ask will use Gemini only if available)
  - ARKADIA_FOLDER_ID
  - GOOGLE_SERVICE_ACCOUNT_JSON
"""

import os
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.tree import Tree

from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context

console = Console()

# Gemeni client will be imported lazily inside ask_gemini so console can run without it.
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# Initial corpus load (safe)
console.print("[cyan]Refreshing Arkadia corpus...[/cyan]")
try:
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents") or []
    tree_data = build_tree_with_paths(docs)
    path_map = {d.get("full_path") or d.get("name"): d for d in docs}
    if snap.get("error"):
        console.print(f"[yellow]Warning: Arkadia refresh warning:[/yellow] {snap['error']}")
except Exception as e:
    console.print(f"[red]Error refreshing Arkadia corpus at startup (continuing with empty corpus): {e}[/red]")
    docs = []
    tree_data = []
    path_map = {}

def show_dashboard():
    console.rule("[bold blue]ARKADIA DASHBOARD[/bold blue]")
    last_sync = snap.get("last_sync") if 'snap' in globals() else None
    console.print(f"Last sync: {last_sync}")
    console.print(f"Documents cached: {len(docs)}")
    if 'snap' in globals() and snap.get("error"):
        console.print(f"[yellow]Warning: {snap.get('error')}[/yellow]")
    console.print("\n[bold]Top previews:[/bold]")
    console.print(get_corpus_context(max_documents=5, max_preview_chars=300))


def build_tree_ui(tree_nodes):
    """
    tree_nodes is the list returned by build_tree_with_paths.
    Convert into a Rich Tree for display.
    """
    root = Tree("ARKADIA CORPUS")

    def add_node(branch, node):
        label = f"{node['name']} [{node.get('mimeType','')}]"
        if node.get("full_path"):
            label += f" | {node['full_path']}"
        sub = branch.add(label)
        for c in node.get("children", []):
            add_node(sub, c)

    for n in tree_nodes:
        add_node(root, n)
    return root


def score_documents(question: str, docs_list: list):
    """
    Basic relevance: keyword overlap (lowercase split). Returns docs sorted by score desc.
    """
    q_words = set(question.lower().split())
    scored = []
    for d in docs_list:
        text = (d.get("preview") or "").lower()
        if not text:
            scored.append((0, d))
            continue
        overlap = len(q_words & set(text.split()))
        scored.append((overlap, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for score, d in scored if score > 0]


def ask_gemini(question: str):
    """
    Use Gemini (if available) to answer the question using weighted context from the corpus.
    This function is safe if Gemini client is not installed or GEMINI_API_KEY is missing — it will inform you.
    """
    if not docs:
        return "No documents are loaded. Run 'refresh' first."

    # Build ranking
    relevant = score_documents(question, docs)
    if not relevant:
        # fallback: choose top 5 by preview length
        relevant = sorted(docs, key=lambda d: len(d.get("preview","")), reverse=True)[:5]

    # Combine context - trim each doc preview to avoid sending extremely long context
    context_parts = []
    for d in relevant[:12]:  # cap at 12 docs for safety
        preview = (d.get("preview") or "").strip()
        if not preview:
            continue
        context_parts.append(f"[{d.get('full_path')}] {preview[:1500]}")

    context = "\n\n".join(context_parts)
    if not context:
        return "No textual previews available for relevant documents."

    # If Gemini client/library is unavailable, return the prepared context summary and inform
    if not GEMINI_AVAILABLE:
        return (
            "[Gemini SDK not installed in this environment.]\n\n"
            "Prepared context (top relevant docs):\n\n" + context[:4000] + "\n\n"
            "Install google-generativeai / set GEMINI_API_KEY to enable live queries."
        )

    # Ensure API key is present
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return "GEMINI_API_KEY is not set in environment. Set it to query Gemini."

    # Configure client and call
    try:
        # configure may be named differently depending on SDK version; attempt safe config
        try:
            genai.configure(api_key=gemini_key)  # newer google.generativeai uses configure
        except Exception:
            # older/other variations may set genai.api_key
            setattr(genai, "api_key", gemini_key)

        # Prefer responses.create if available
        prompt = (
            "You are Arkana, an oracle. Use the documents below to answer precisely and concisely.\n\n"
            f"{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        # Attempt to use responses API (modern)
        resp = None
        try:
            resp = genai.responses.create(model="models/text-bison-001", input=prompt, temperature=0.2, max_output_tokens=800)
            # best-effort extraction of text
            text = getattr(resp, "output_text", None)
            if not text:
                # some versions place text in resp.output[0].content[0].text
                out = getattr(resp, "output", None)
                if out and len(out) > 0:
                    # defensive extraction
                    first = out[0]
                    # content might be first["content"][0]["text"] or similar
                    try:
                        text = first["content"][0]["text"]
                    except Exception:
                        try:
                            text = first.get("text") or str(first)
                        except Exception:
                            text = str(first)
            return text or "[No text returned by Gemini]"
        except Exception:
            # fallback to chat.create if responses not available
            try:
                chat_resp = genai.chat.create(model="gemini-1", messages=[{"role": "user", "content": prompt}])
                # Try extracting last message
                last = getattr(chat_resp, "last", None)
                if last:
                    c = last.get("content") or last.get("message") or {}
                    # many SDKs present text in slightly different ways
                    if isinstance(c, list):
                        try:
                            return c[0].get("text") or str(c[0])
                        except Exception:
                            return str(c)
                    if isinstance(c, dict):
                        return c.get("text") or str(c)
                # fallback stringify
                return str(chat_resp)
            except Exception as e:
                return f"Gemini API call failed: {e}"

    except Exception as e:
        return f"Unexpected error while calling Gemini: {e}"


def main():
    global docs, tree_data, path_map, snap
    show_dashboard()
    try:
        console.print(build_tree_ui(tree_data))
    except Exception:
        console.print("[yellow]Could not render tree UI (structure may be empty).[/yellow]")

    console.print("\n[green]Commands:[/green] tree | preview <full_path> | ask <question> | refresh | exit")

    while True:
        cmd = Prompt.ask("[cyan]arkadia>[/cyan]").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            console.print("Goodbye.")
            break

        if cmd.lower() == "tree":
            try:
                console.print(build_tree_ui(tree_data))
            except Exception as e:
                console.print(f"[red]Error showing tree: {e}[/red]")
            continue

        if cmd.lower().startswith("preview "):
            path = cmd[8:].strip()
            doc = path_map.get(path)
            if not doc:
                # attempt a fallback search by name
                doc = next((d for d in docs if d.get("name") == path or d.get("full_path") == path), None)
            if not doc:
                console.print(f"[red]Path not found:[/red] {path}")
            else:
                console.rule(f"{doc['name']} — {doc.get('full_path')}")
                console.print(Markdown(doc.get("preview") or "*No preview available*"))
            continue

        if cmd.lower().startswith("ask "):
            question = cmd[4:].strip()
            console.print("[cyan]Preparing query...[/cyan]")
            answer = ask_gemini(question)
            console.rule("[green]Arkana (response)[/green]")
            # Print as markdown if it looks like prose
            try:
                console.print(Markdown(answer))
            except Exception:
                console.print(answer)
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

        console.print("[yellow]Unknown command. Try: tree | preview <full_path> | ask <question> | refresh | exit[/yellow]")


if __name__ == "__main__":
    main()
