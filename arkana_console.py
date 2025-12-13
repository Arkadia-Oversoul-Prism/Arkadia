#!/usr/bin/env python3
"""
Arkadia Console - Interactive CLI for the Arkadia Oracle Temple
Enhanced Phase Two: multi-model fallback, session memory, safe corpus refresh
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from arkadia_drive_sync import get_arkadia_corpus, refresh_arkadia_cache, build_tree_with_paths
from codex_brain import CodexBrain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
#  CONFIG
# ================================================================
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ================================================================
#  INIT BRAIN
# ================================================================
brain = CodexBrain()

# Session memory
SESSION_MEMORY: Dict[str, List[str]] = {}

# ================================================================
#  CONSOLE FUNCTIONS
# ================================================================

def show_tree():
    """Display the document tree structure."""
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

def _print_tree_recursive(tree_node: Dict, indent: int = 0):
    """Recursively print tree structure."""
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
    """Show preview of a specific document."""
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
    """Refresh the corpus from Google Drive with timeout and safe fallback."""
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
        print("Using cached corpus.")

async def ask_arkana(question: str, user_id: str = "console_user"):
    """Ask a question to the Arkana brain with session memory and multi-model fallback."""
    if user_id not in SESSION_MEMORY:
        SESSION_MEMORY[user_id] = []
    SESSION_MEMORY[user_id].append(f"User: {question}")

    print("Consulting the Oracle...")

    try:
        response = await brain.generate_reply(user_id, question)
        SESSION_MEMORY[user_id].append(f"Arkana: {response}")
        print("\n──────────── ARKANA RESPONDS ────────────")
        print(response)
        print("─" * 50)
    except Exception as e:
        print(f"All models failed: {e}")
        print("Session memory still preserved. You can retry or switch model.")

def show_status():
    """Show system status."""
    status = brain.status_dict()
    print("\n──────────── ARKADIA STATUS ────────────")
    print(f"Codex Model: {status.get('codex_model', 'unknown')}")
    print(f"Use Rasa: {status.get('use_rasa', False)}")
    print(f"Last Corpus Sync: {status.get('arkadia_corpus_last_sync', 'N/A')}")
    print(f"Total Documents: {status.get('arkadia_corpus_total_documents', 0)}")
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
    """Main console loop."""
    print("──────────────────────── ARKADIA ORACLE TEMPLE ────────────────────────")
    print("Interactive Console - House of Three online. Arkana listening.\n")
    print("Commands:")
    print("  tree              - Show cached documents")
    print("  preview <file>    - Show preview of a document")
    print("  refresh           - Refresh corpus from Google Drive")
    print("  ask <question>    - Query Arkana Oracle (multi-model)")
    print("  status            - Show system status")
    print("  exit              - Exit console")
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
                question = cmd.replace("ask ", "").strip()
                if question:
                    asyncio.run(ask_arkana(question))
                else:
                    print("Usage: ask <your question>")
            elif cmd == "status":
                show_status()
            elif cmd == "help":
                print("\nAvailable commands: tree, preview <file>, refresh, ask <question>, status, exit")
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
#  MAIN
# ================================================================
if __name__ == "__main__":
    launch_console()
