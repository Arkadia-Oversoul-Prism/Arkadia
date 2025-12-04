#!/usr/bin/env python3
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context
import google.generativeai as genai

console = Console()

# Ensure API key is set
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    console.print("[red]Error: GEMINI_API_KEY not set in environment[/red]")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Load corpus
console.print("[cyan]Refreshing Arkadia corpus...[/cyan]")
snap = refresh_arkadia_cache(force=True)
docs = snap.get("documents") or []
tree_data = build_tree_with_paths(docs)
path_map = {d.get("full_path") or d.get("name"): d for d in docs}
console.print(f"[green]Documents cached:[/green] {len(docs)}")
if snap.get("error"):
    console.print(f"[red]Sync error:[/red] {snap['error']}")

def show_dashboard():
    console.rule("[bold blue]ARKADIA DASHBOARD[/bold blue]")
    console.print(f"Last sync: {snap.get('last_sync')}")
    console.print(f"Documents cached: {len(docs)}")
    if snap.get("error"):
        console.print(f"[red]Sync errors:[/red] {snap['error']}")
    console.print("\n[bold]Top previews:[/bold]")
    console.print(get_corpus_context(max_documents=5, max_preview_chars=300))

def build_tree_ui(tree_nodes):
    from rich.tree import Tree
    root = Tree("ARKADIA CORPUS")
    def add_node(branch, node):
        label = f"{node['name']} [{node['mimeType']}]"
        if node.get("full_path"):
            label += f" | {node['full_path']}"
        sub = branch.add(label)
        for c in node.get("children", []):
            add_node(sub, c)
    for n in tree_nodes:
        add_node(root, n)
    return root

def ask_gemini(question: str):
    """Send a smart weighted query to Gemini using the top documents"""
    # Collect top documents and calculate weight
    sorted_docs = sorted(docs, key=lambda d: len(d.get("preview","")), reverse=True)
    context = "\n\n".join([d.get("preview","")[:1000] for d in sorted_docs[:5]])

    prompt = f"""
You are Arkana, the Arkadia Superintelligence.
Use the following context from the Arkadia Corpus to answer the question.
Context:
{context}

Question: {question}
Provide a concise, structured, and insightful answer based on the above context.
"""
    try:
        response = genai.chat.create(
            model="chat-bison-001",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7
        )
        return response.last["content"][0]["text"]
    except Exception as e:
        console.print(f"[red]Error asking Gemini:[/red] {e}")
        return "[No response from Gemini]"

def main():
    global docs, tree_data, path_map, snap
    show_dashboard()
    console.print(build_tree_ui(tree_data))
    console.print("\n[green]Commands:[/green] tree | preview <full_path> | ask <question> | refresh | exit")

    while True:
        cmd = Prompt.ask("[cyan]arkadia>[/cyan]").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit","quit"):
            break
        if cmd.lower() == "tree":
            console.print(build_tree_ui(tree_data)); continue
        if cmd.lower().startswith("preview "):
            path = cmd[8:].strip(); doc = path_map.get(path)
            if not doc:
                console.print(f"[red]Path not found:[/red] {path}")
            else:
                console.rule(f"{doc['name']} — {doc.get('full_path')}")
                console.print(Markdown(doc.get("preview") or "*No preview available*"))
            continue
        if cmd.lower().startswith("ask "):
            question = cmd[4:].strip()
            console.print("[cyan]Asking Arkana (Gemini)...[/cyan]")
            answer = ask_gemini(question)
            console.print(Markdown(answer))
            continue
        if cmd.lower() == "refresh":
            snap = refresh_arkadia_cache(force=True)
            docs = snap.get("documents") or []
            tree_data = build_tree_with_paths(docs)
            path_map = {d.get("full_path") or d.get("name"): d for d in docs}
            console.print("[green]Corpus refreshed.[/green]")
            continue
        console.print("[red]Unknown command[/red]")

if __name__ == "__main__":
    main()
