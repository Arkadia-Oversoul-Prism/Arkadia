#!/usr/bin/env python3
"""
Arkadia Console – Primary UI for Arkana (Gemini Oracle Intelligence)
Fully compatible with Termux using HTTP requests to Gemini.
"""

import os
import sys
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.tree import Tree

# -------------------------
# Configuration
# -------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("[red]Error: GEMINI_API_KEY not set in environment[/red]")
    sys.exit(1)

ARKADIA_FOLDER_ID = os.environ.get("ARKADIA_FOLDER_ID")  # optional folder ID

console = Console()


# -------------------------
# Gemini API helper
# -------------------------
def ask_gemini(prompt: str, temperature: float = 0.7, max_tokens: int = 500):
    """
    Send a prompt to Gemini API via HTTP and return the response text.
    """
    url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate"
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    payload = {
        "prompt": {"text": prompt},
        "temperature": temperature,
        "maxOutputTokens": max_tokens
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("candidates", [{}])[0].get("content", "[No text returned]")
        else:
            return f"[Error {response.status_code}]: {response.text}"
    except Exception as e:
        return f"[Exception calling Gemini]: {e}"


# -------------------------
# Corpus helpers
# -------------------------
def refresh_arkadia_cache(force: bool = False):
    """
    Dummy placeholder: refresh corpus. Replace with real sync logic if available.
    """
    return {
        "documents": [],
        "last_sync": "never",
        "error": None
    }


def build_tree_with_paths(docs):
    """
    Build a hierarchical tree from a flat list of documents.
    Each doc should have: name, mimeType, full_path, children
    """
    def add_node(branch, node):
        label = f"{node.get('name', 'Unnamed')} [{node.get('mimeType', 'unknown')}]"
        if node.get("full_path"):
            label += f" | {node['full_path']}"
        sub = branch.add(label)
        for c in node.get("children", []):
            add_node(sub, c)
    root = Tree("ARKADIA CORPUS")
    for n in docs:
        add_node(root, n)
    return root


def get_corpus_context(max_documents=3, max_preview_chars=300):
    """
    Return short previews of documents in the corpus.
    """
    return "\n\n".join([d.get("preview", "")[:max_preview_chars] for d in docs[:max_documents]])


# -------------------------
# Initialize
# -------------------------
console.print("[cyan]Refreshing Arkadia corpus...[/cyan]")
snap = refresh_arkadia_cache(force=True)
docs = snap.get("documents") or []
tree_data = build_tree_with_paths(docs)
path_map = {d.get("full_path") or d.get("name"): d for d in docs}

console.print(f"[green]Documents cached:[/green] {len(docs)}")
if snap.get("error"):
    console.print(f"[red]Sync error:[/red] {snap['error']}")


# -------------------------
# Console UI
# -------------------------
def show_dashboard():
    console.rule("[bold blue]ARKADIA DASHBOARD[/bold blue]")
    console.print(f"Last sync: {snap.get('last_sync')}")
    console.print(f"Documents cached: {len(docs)}")
    if snap.get("error"):
        console.print(f"[red]Sync errors:[/red] {snap['error']}")
    console.print("\n[bold]Top previews:[/bold]")
    console.print(get_corpus_context(max_documents=5, max_preview_chars=300))


def main():
    global docs, tree_data, path_map, snap
    show_dashboard()
    console.print(build_tree_with_paths(docs))
    console.print("\n[green]Commands:[/green] tree | preview <full_path> | ask <question> | refresh | exit")
    
    while True:
        cmd = Prompt.ask("[cyan]arkadia>[/cyan]").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            break
        elif cmd.lower() == "tree":
            console.print(build_tree_with_paths(docs))
        elif cmd.lower().startswith("preview "):
            path = cmd[8:].strip()
            doc = path_map.get(path)
            if not doc:
                console.print(f"[red]Path not found:[/red] {path}")
            else:
                console.rule(f"{doc.get('name')} — {doc.get('full_path')}")
                console.print(Markdown(doc.get("preview") or "*No preview available*"))
        elif cmd.lower().startswith("ask "):
            question = cmd[4:].strip()
            context = get_corpus_context(max_documents=3, max_preview_chars=800)
            console.print("[cyan]Asking Arkana (Gemini)...[/cyan]")
            answer = ask_gemini(f"Context: {context}\n\nQuestion: {question}")
            console.print(f"[bold green]Arkana:[/bold green] {answer}")
        elif cmd.lower() == "refresh":
            console.print("[cyan]Refreshing corpus...[/cyan]")
            snap = refresh_arkadia_cache(force=True)
            docs = snap.get("documents") or []
            tree_data = build_tree_with_paths(docs)
            path_map = {d.get("full_path") or d.get("name"): d for d in docs}
            console.print("[green]Corpus refreshed[/green]")
        else:
            console.print(f"[red]Unknown command:[/red] {cmd}")


if __name__ == "__main__":
    main()
