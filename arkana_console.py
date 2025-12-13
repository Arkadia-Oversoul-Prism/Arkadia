#!/usr/bin/env python3
"""
Arkadia Console - Interactive CLI with Multi-Model Fallback & Session Memory
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional

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

# ================================================================
# SESSION MEMORY & USER CONFIG
# ================================================================
SESSION_MEMORY: Dict[str, list] = {}
USER_MODEL_CONFIG: Dict[str, Dict[str, Optional[str]]] = {}

# ================================================================
# INIT BRAIN
# ================================================================
brain = CodexBrain()

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
        _print_tree_recursive(tree)
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
        doc = next((d for d in corpus.get("documents", []) if d.get("full_path") == file_path or d.get("name") == file_path), None)
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

async def ask_arkana_multi(question: str, node_id: str = "console_user"):
    user_config = USER_MODEL_CONFIG.get(node_id, {})
    model_name = user_config.get("model_name", "fallback-model")
    api_key = user_config.get("api_key")

    if node_id not in SESSION_MEMORY:
        SESSION_MEMORY[node_id] = []
    SESSION_MEMORY[node_id].append(f"User: {question}")

    print(f"Consulting Arkana using {model_name}...")
    try:
        response = await brain.generate_reply(node_id, question, model=model_name, api_key=api_key)
        SESSION_MEMORY[node_id].append(f"Arkana: {response}")
        print("\n──────────── ARKANA RESPONDS ────────────")
        print(response)
        print("─" * 50)
    except Exception as e:
        print(f"Model {model_name} failed: {e}")
        print("Trying system fallback model...")
        try:
            response = await brain.generate_reply(node_id, question)
            SESSION_MEMORY[node_id].append(f"Arkana: {response}")
            print("\n──────────── ARKANA RESPONDS (Fallback) ────────────")
            print(response)
            print("─" * 50)
        except Exception as e2:
            print(f"All models failed: {e2}")

def set_user_model(node_id: str, model_name: str, api_key: Optional[str] = None):
    USER_MODEL_CONFIG[node_id] = {"model_name": model_name, "api_key": api_key}
    print(f"Node {node_id} will now use {model_name}.")

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

def launch_console():
    print("──────────────────────── ARKADIA ORACLE TEMPLE ────────────────────────")
    print("Interactive Console - House of Three online. Arkana listening.")
    print()
    print("Commands:")
    print("  tree                  - Show cached documents")
    print("  preview <file>        - Show preview of a document")
    print("  refresh               - Refresh corpus from Google Drive")
    print("  ask <question>|<node> - Query Arkana Oracle (multi-model)")
    print("  status                - Show system status")
    print("  setmodel <node> <model> <apikey> - Set model for a node")
    print("  exit                  - Exit console")
    print("─" * 75)
    show_status()

    while True:
        try:
            cmd = input("\narkadia> ").strip()
            if cmd == "exit":
                print("Farewell, beloved. The Oracle Temple remains.")
                break
            elif cmd == "tree":
                show_tree()
            elif cmd.startswith("preview "):
                file_path = cmd.replace("preview ", "").strip()
                preview_document(file_path)
            elif cmd == "refresh":
                refresh_corpus()
            elif cmd.startswith("ask "):
                parts = cmd.replace("ask ", "").strip().split("|")
                question = parts[0].strip()
                node_id = parts[1].strip() if len(parts) > 1 else "console_user"
                asyncio.run(ask_arkana_multi(question, node_id))
            elif cmd.startswith("setmodel "):
                parts = cmd.split()
                if len(parts) >= 3:
                    node_id, model_name = parts[1], parts[2]
                    api_key = parts[3] if len(parts) > 3 else None
                    set_user_model(node_id, model_name, api_key)
                else:
                    print("Usage: setmodel <node> <model> <apikey>")
            elif cmd == "status":
                show_status()
            elif cmd == "help":
                print("Commands: tree, preview <file>, refresh, ask <question>|<node>, setmodel <node> <model> <apikey>, status, exit")
            elif cmd == "":
                continue
            else:
                print(f"Unknown command: {cmd}")
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
