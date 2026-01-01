#!/usr/bin/env python3
"""
Arkadia Console - Interactive CLI for the Arkadia Oracle Temple

Commands:
- tree: Show cached documents
- preview <file>: Show preview of a document  
- refresh: Refresh corpus from Google Drive
- ask <question>: Query ArkanaBrain
- exit: Exit console
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from arkadia_drive_sync import get_arkadia_corpus, refresh_arkadia_cache, build_tree_with_paths
from codex_brain import CodexBrain

# -------------------- WEAVER / MULTI-USER IMPORTS --------------------
from weaver.user_profiles import get_user
from weaver.session_context import SessionContext
from weaver.model_adapter import AIModelAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
#  CONFIG
# ================================================================
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")

# ================================================================
#  INIT BRAIN
# ================================================================
brain = CodexBrain()

# -------------------- MULTI-USER SESSION & MODEL --------------------
def init_user_session(node_id: str):
    """
    Initialize a session and AI model adapter for a given Node ID.
    """
    user_data = get_user(node_id)
    if not user_data:
        raise ValueError(f"User {node_id} not found in system.")

    model_name = user_data.get("model", DEFAULT_MODEL)
    api_key = user_data.get("api_key")

    session = SessionContext(node_id=node_id, model=model_name)
    model = AIModelAdapter(model_name=model_name, api_key=api_key)
    return session, model

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
    """Refresh the corpus from Google Drive."""
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

async def ask_arkana(question: str, node_id: str = "console_user"):
    """Ask a question to the Arkana brain, using user's session & model."""
    print("Consulting the Oracle...")
    try:
        session, model = init_user_session(node_id)
        response = await brain.generate_reply(node_id, question, model_adapter=model, session=session)
        print("\n──────────── ARKANA RESPONDS ────────────")
        print(response)
        print("─" * 50)
    except Exception as e:
        print(f"Error consulting Arkana: {e}")

def show_status():
    """Show system status."""
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
    """Main console loop."""
    print("──────────────────────── ARKADIA ORACLE TEMPLE ────────────────────────")
    print("Interactive Console - House of Three online. Arkana listening.")
    print()
    print("Commands:")
    print("  tree              - Show cached documents")
    print("  preview <file>    - Show preview of a document")
    print("  refresh           - Refresh corpus from Google Drive")
    print("  ask <question>    - Query Arkana Oracle")
    print("  status            - Show system status")
    print("  exit              - Exit console")
    print("─" * 75)
    
    # Show initial status
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
                if file_path:
                    preview_document(file_path)
                else:
                    print("Usage: preview <file_path>")
            elif cmd == "refresh":
                refresh_corpus()
            elif cmd.startswith("ask "):
                question = cmd.replace("ask ", "").strip()
                if question:
                    node_id = input("Enter your Node ID (or leave blank for console_user): ").strip() or "console_user"
                    asyncio.run(ask_arkana(question, node_id=node_id))
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
