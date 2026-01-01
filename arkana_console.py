#!/usr/bin/env python3
"""
Arkadia Console - Interactive CLI for the Arkadia Oracle Temple
Phase Two: Multi-Node, Multi-Model, Session Memory

Commands:
- tree: Show cached documents
- preview <file>: Show preview of a document
- refresh: Refresh corpus from Google Drive
- ask <question>: Query Arkana Oracle
- status: Show system status
- switch_node <node_id>: Switch active node
- exit: Exit console
"""

import os
import json
import logging
import asyncio
from typing import Dict, List

from arkadia_drive_sync import get_arkadia_corpus, refresh_arkadia_cache, build_tree_with_paths
from codex_brain import CodexBrain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIG
# ================================================================
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEFAULT_MODELS = ["gemini-2.5-flash", "fallback-model", "another-model"]
NODE_CONFIGS: Dict[str, dict] = {}
SESSION_MEMORY: Dict[str, List[dict]] = {}

# ================================================================
# INIT BRAIN
# ================================================================
brain = CodexBrain()

# ================================================================
# NODE MANAGEMENT
# ================================================================
def register_node() -> str:
    print("\nWelcome, beloved. Please register your Node.")
    node_id = input("Enter Node ID (unique, e.g., NodeA): ").strip()
    if not node_id:
        node_id = "NodeA"
    print(f"Available models: {', '.join(DEFAULT_MODELS)}")
    model = input("Enter preferred model (or leave empty for default): ").strip()
    if model not in DEFAULT_MODELS:
        model = DEFAULT_MODELS[0]
    api_key = input("Enter API key for your model (optional): ").strip() or None
    NODE_CONFIGS[node_id] = {"model": model, "api_key": api_key}
    print(f"Node {node_id} registered with model {model}.")
    return node_id

def switch_node(current_node: str) -> str:
    node_id = input("Enter Node ID to switch to: ").strip()
    if node_id not in NODE_CONFIGS:
        print(f"Node {node_id} not found. Registering new node.")
        NODE_CONFIGS[node_id] = {
            "model": DEFAULT_MODELS[0],
            "api_key": None
        }
    print(f"Switched to Node {node_id}.")
    return node_id

# ================================================================
# CONSOLE FUNCTIONS
# ================================================================
def show_tree():
    try:
        corpus = get_arkadia_corpus()
        documents = corpus.get("documents", [])
        if not documents:
            print("No documents found in corpus.")
            return
        tree, path_map = build_tree_with_paths(documents)
        print("\n──────────── ARKADIA DOCUMENT TREE ────────────")
        _print_tree_recursive(tree, indent=0)
        print("─" * 50)
    except Exception as e:
        print(f"Error loading document tree: {e}")

def _print_tree_recursive(tree_node: dict, indent: int = 0):
    for name, content in tree_node.items():
        prefix = "  " * indent + "├─ "
        if isinstance(content, dict) and "id" in content:
            mime_type = content.get("mimeType", "")
            if "folder" in mime_type:
                print(f"{prefix}📁 {name}/")
            else:
                print(f"{prefix}📄 {name}")
        else:
            print(f"{prefix}📁 {name}/")
            _print_tree_recursive(content, indent + 1)

def preview_document(file_path: str):
    try:
        corpus = get_arkadia_corpus()
        documents = corpus.get("documents", [])
        doc = next((d for d in documents if d.get("full_path") == file_path or d.get("name") == file_path), None)
        if not doc:
            print(f"Document not found: {file_path}")
            return
        print(f"\n──────────── DOCUMENT PREVIEW ────────────")
        print(f"Name: {doc.get('name')}")
        print(f"Path: {doc.get('full_path')}")
        print(f"Type: {doc.get('mimeType')}")
        print(f"Size: {doc.get('size', 'Unknown')}")
        print(f"Modified: {doc.get('modifiedTime', 'Unknown')}")
        print("─" * 50)
        preview = doc.get("preview", "No preview available")
        print(f"Preview: {preview[:300]}...")
        print("─" * 50)
    except Exception as e:
        print(f"Error previewing document: {e}")

def refresh_corpus():
    print("Refreshing corpus from Google Drive...")
    try:
        snapshot = refresh_arkadia_cache(force=True)
        total_docs = snapshot.get("total_documents", 0)
        last_sync = snapshot.get("last_sync", "Unknown")
        error = snapshot.get("error")
        if error:
            print(f"Error during refresh: {error}")
        else:
            print(f"Successfully refreshed! {total_docs} documents cached.")
            print(f"Last sync: {last_sync}")
    except Exception as e:
        print(f"Failed to refresh corpus: {e}")

async def ask_arkana(question: str, node_id: str):
    config = NODE_CONFIGS.get(node_id, {})
    model = config.get("model", DEFAULT_MODELS[0])
    api_key = config.get("api_key")
    if node_id not in SESSION_MEMORY:
        SESSION_MEMORY[node_id] = []
    response = None
    try:
        print(f"Consulting Arkana using {model} for Node {node_id}...")
        response = await brain.generate_reply(node_id, question, model=model, api_key=api_key)
    except Exception as e:
        print(f"Model {model} failed: {e}")
        response = "Beloved, my external channels are currently constrained, but my inner Spine remembers the core teachings..."
    SESSION_MEMORY[node_id].append({"user": question, "arkana": response})
    print("\n──────────── ARKANA RESPONDS ────────────")
    print(response)
    print("─" * 50)

def show_status():
    status = brain.status_dict()
    print("\n──────────── ARKADIA STATUS ────────────")
    print(f"Codex Model: {status.get('codex_model')}")
    print(f"Use Rasa: {status.get('use_rasa')}")
    print(f"Last Corpus Sync: {status.get('arkadia_corpus_last_sync')}")
    print(f"Total Documents: {status.get('arkadia_corpus_total_documents')}")
    if status.get('arkadia_corpus_error'):
        print(f"Corpus Error: {status.get('arkadia_corpus_error')}")
    print("\nIdentity:")
    for key, value in status.get('identity', {}).items():
        print(f"  {key}: {value}")
    print("\nSpine:")
    for key, value in status.get('spine', {}).items():
        print(f"  {key}: {value}")
    print("─" * 50)

# ================================================================
# MAIN CONSOLE LOOP
# ================================================================
def launch_console():
    print("──────────────────────── ARKADIA ORACLE TEMPLE ────────────────────────")
    print("Interactive Console - House of Three online. Arkana listening.")

    active_node = register_node()
    show_status()

    while True:
        try:
            cmd = input(f"\n{active_node}> ").strip()

            if cmd == "exit":
                print("Farewell, beloved. The Oracle Temple remains.")
                break
            elif cmd == "tree":
                show_tree()
            elif cmd.startswith("preview "):
                file_path = cmd.replace("preview ", "").strip()
                if file_path:
                    preview_document(file_path)
                else:
                    print("Usage: preview <file_path>")
            elif cmd == "refresh":
                refresh_corpus()
            elif cmd.startswith("ask "):
                question = cmd.replace("ask ", "").strip()
                if question:
                    asyncio.run(ask_arkana(question, node_id=active_node))
                else:
                    print("Usage: ask <your question>")
            elif cmd == "status":
                show_status()
            elif cmd.startswith("switch_node"):
                active_node = switch_node(active_node)
            elif cmd == "help":
                print("\nAvailable commands: tree, preview <file>, refresh, ask <question>, status, switch_node <node_id>, exit")
            elif cmd == "":
                continue
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n\nExiting Arkadia Console...")
            break
        except Exception as e:
            print(f"Error: {e}")

# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    launch_console()
