#!/usr/bin/env python3
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context
import google.generativeai as genai

console = Console()

# Ensure API key is set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    console.print("[red]Error: GEMINI_API_KEY not set in environment[/red]")
    exit(1)
genai.configure(api_key=GEMINI_API_KEY)

# Load Arkadia corpus
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

def score_documents(question: str, docs_list: list):
    """
    Simple relevance scoring: counts overlapping words between question and document preview.
    Returns documents sorted by score descending.
    """
    q_words = set(question.lower().split())
    scored = []
    for d in docs_list:
        preview_text = d.get("preview","").lower()
        overlap = len(q_words & set(preview_text.split()))
        scored.append((overlap, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for score,d in scored if score > 0]

def smart_query(question: str, docs_list: list):
    """
    Build a prompt including all relevant documents, sorted by relevance.
    """
    relevant_docs = score_documents(question, docs_list)
    if not relevant_docs:
        # fallback to top 5 documents if none match keywords
        relevant_docs = docs_list[:5]

    context_lines = []
    for d in relevant_docs:
        preview = d.get("preview", "")
        full_path = d.get("full_path") or d.get("name")
        context_lines.append(f"[{full_path}]: {preview}")

    context_text = "\n\n".join(context_lines)
    return f"{context_text}\n\nQuestion: {question}\nAnswer concisely based on the documents above."

def main():
    global docs, tree_data, path_map, snap
    show_dashboard()
    console.print(build_tree_ui(tree_data))
    console.print("\n[green]Commands:[/green] tree | preview <full_path> | ask <question> | refresh | exit")
    while True:
        cmd = Prompt.ask("[cyan]arkadia>[/cyan]").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd.lower() == "tree":
            console.print(build_tree_ui(tree_data))
            continue
        if cmd.lower().startswith("preview "):
            path = cmd[8:].strip()
            doc = path_map.get(path)
            if not doc:
                console.print(f"[red]Path not found:[/red] {path}")
            else:
                console.rule(f"{doc['name']} — {doc.get('full_path')}")
                console.print(Markdown(doc.get("preview") or "*No preview available*"))
            continue
        if cmd.lower().startswith("ask "):
            question = cmd[4:].strip()
            if not docs:
                console.print("[red]No documents loaded. Please refresh first.[/red]")
                continue
            prompt_text = smart_query(question, docs)
            console.print("[cyan]Asking Gemini...[/cyan]\n")
            try:
                response = genai.chat.create(
                    model="gemini-1",
                    messages=[{"role": "user", "content": prompt_text}]
                )
                answer = response.last.get("content") or "[No response from Gemini]"
                console.print(Markdown(answer))
            except Exception as e:
                console.print(f"[red]Error querying Gemini:[/red] {e}")
            continue
        if cmd.lower() == "refresh":
            console.print("[cyan]Refreshing Arkadia corpus...[/cyan]")
            snap = refresh_arkadia_cache(force=True)
            docs = snap.get("documents") or []
            tree_data = build_tree_with_paths(docs)
            path_map = {d.get("full_path") or d.get("name"): d for d in docs}
            console.print(f"[green]Documents cached:[/green] {len(docs)}")
            continue
        console.print("[red]Unknown command[/red]")

if __name__ == "__main__":
    main()
