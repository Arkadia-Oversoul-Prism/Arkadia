#!/usr/bin/env python3
"""
Arkadia Console - Interactive CLI for the Arkadia Oracle Temple

Commands:
- tree: Show cached documents
- preview <file>: Show preview of a document  
- refresh: Refresh corpus from Google Drive
- ask <question>: Query ArkanaBrain (multi-model support)
- status: Show system status
- exit: Exit console
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from arkadia_drive_sync import get_arkadia_corpus, refresh_arkadia_cache, build_tree_with_paths
from codex_brain import CodexBrain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
#  CONFIG
# ================================================================
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "/run/service_account.json")
ARKADIA_FOLDER_ID = os.getenv("ARKADIA_FOLDER_ID")

# ================================================================
#  SESSION MEMORY & MODEL CONFIG
# ================================================================
class SessionContext:
    """Stores per-user memory and model selection."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.memory: List[Dict[str, str]] = []
        self.models: List[Dict[str, Any]] = []
    
    def add_memory(self, role: str, content: str):
        self.memory.append({"role": role, "content": content})
    
    def load_memory(self) -> List[Dict[str, str]]:
        return self.memory
    
    def configure_models(self, primary: str, api_key: str, fallback: Optional[List[Dict[str, str]]] = None):
        self.models = [{"model": primary, "api_key": api_key}]
        if fallback:
            self.models.extend(fallback)

# ================================================================
#  AI MODEL ADAPTER
# ================================================================
class AIModelAdapter:
    """Handles multi-model fallback and memory continuity."""
    def __init__(self, session: SessionContext):
        self.session = session
    
    async def generate(self, prompt: str) -> str:
        last_error = None
        for model_cfg in self.session.models:
            try:
                # Call the correct API per model
                if "gemini" in model_cfg["model"]:
                    return await self._call_gemini(prompt, model_cfg)
                elif "openai" in model_cfg["model"]:
                    return await self._call_openai(prompt, model_cfg)
                else:
                    return await self._call_local_model(prompt, model_cfg)
            except Exception as e:
                last_error = e
                continue
        raise RuntimeError(f"All models failed: {last_error}")
    
    async def _call_gemini(self, prompt: str, model_cfg: Dict[str, str]) -> str:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_cfg['model']}:generateContent?key={model_cfg['api_key']}"
        payload = {"prompt": prompt, "temperature": 0.7, "maxOutputTokens": 512}
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        output = r.json()
        text = output.get("candidates", [{}])[0].get("content", "")
        self.session.add_memory("assistant", text)
        return text
    
    async def _call_openai(self, prompt: str, model_cfg: Dict[str, str]) -> str:
        import openai
        openai.api_key = model_cfg["api_key"]
        completion = openai.ChatCompletion.create(
            model=model_cfg["model"],
            messages=self.session.load_memory() + [{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.7
        )
        text = completion.choices[0].message.content
        self.session.add_memory("assistant", text)
        return text
    
    async def _call_local_model(self, prompt: str, model_cfg: Dict[str, str]) -> str:
        # Placeholder for local model inference (llama, etc.)
        text = f"[Local {model_cfg['model']}] {prompt[:200]}"
        self.session.add_memory("assistant", text)
        return text

# ================================================================
#  INIT BRAIN
# ================================================================
brain = CodexBrain()

# ================================================================
#  CONSOLE FUNCTIONS
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

def _print_tree_recursive(tree_node: Dict, indent: int = 0):
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

async def ask_arkana(question: str, session: Optional[SessionContext] = None):
    if session is None:
        session = SessionContext("console_user")
        session.configure_models(
            primary=os.getenv("GEMINI_API_KEY_MODEL", "gemini-2.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY")
        )
    adapter = AIModelAdapter(session)
    print("Consulting the Oracle...")
    try:
        response = await adapter.generate(question)
        print("\n──────────── ARKANA RESPONDS ────────────")
        print(response)
        print("─" * 50)
    except Exception as e:
        print(f"Error consulting Arkana: {e}")

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
#  MAIN CONSOLE LOOP
# ================================================================
def launch_console():
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
                if file_path:
                    preview_document(file_path)
                else:
                    print("Usage: preview <file_path>")
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
                print("\nAvailable commands:")
                print("  tree, preview <file>, refresh, ask <question>, status, exit")
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
#  ENTRY POINT
# ================================================================
if __name__ == "__main__":
    launch_console()
