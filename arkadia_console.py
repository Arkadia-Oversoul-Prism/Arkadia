#!/usr/bin/env python3
import os
import sys
import logging
from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
ARKADIA_FOLDER_ID = os.environ.get("ARKADIA_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_JSON_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_FILE")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not ARKADIA_FOLDER_ID:
    raise ValueError("ARKADIA_FOLDER_ID environment variable not set")
if not GOOGLE_SERVICE_ACCOUNT_JSON_FILE:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON_FILE environment variable not set")

# Attempt to import generative AI module for ask feature
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    ASK_ENABLED = True
    logger.info("google.generativeai available. 'ask' feature enabled.")
except ImportError:
    ASK_ENABLED = False
    logger.warning("google.generativeai module not installed. 'ask' feature disabled.")

# Global corpus cache
snap, docs, tree_data, path_map = None, [], {}, {}

def refresh_corpus():
    global snap, docs, tree_data, path_map
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents", [])
    tree_data, path_map = build_tree_with_paths(docs)
    logger.info(f"{len(docs)} documents cached")
    return snap

def main():
    global snap, docs, tree_data, path_map
    snap = refresh_corpus()
    print(f"Documents cached: {len(docs)}")
    print(f"Last sync: {snap.get('last_sync')}")
    print("──────────────────────── ARKADIA DASHBOARD ────────────────────────")
    print("Commands: tree | preview <full_path> | refresh | ask <question> | exit")

    while True:
        try:
            cmd = input("arkadia>: ").strip()
        except EOFError:
            print("\nExiting Arkadia Console.")
            break

        if cmd == "tree":
            for path in tree_data:
                print(path)
        elif cmd.startswith("preview "):
            _, path = cmd.split(" ", 1)
            doc = path_map.get(path)
            if doc:
                print(f"Name: {doc.get('name')}")
                print(f"Full Path: {doc.get('full_path')}")
                print(f"MIME Type: {doc.get('mimeType')}")
                preview_text = doc.get("preview") or "No preview available."
                print(f"Preview:\n{preview_text}")
            else:
                print(f"No document found at path: {path}")
        elif cmd == "refresh":
            snap = refresh_corpus()
            print(f"Documents cached: {len(docs)}")
            print(f"Last sync: {snap.get('last_sync')}")
        elif cmd.startswith("ask "):
            if not ASK_ENABLED:
                print("Ask feature is disabled (google.generativeai module not installed).")
                continue
            _, question = cmd.split(" ", 1)
            # Build context from top 5 documents by default
            context = get_corpus_context()
            try:
                response = genai.chat(messages=[{"role": "user", "content": question}], temperature=0.2)
                print(f"Answer: {response.last}")
                print(f"Context:\n{context}")
            except Exception as e:
                print(f"Gemini call failed: {e}")
        elif cmd == "exit":
            print("Exiting Arkadia Console.")
            break
        else:
            print("Unknown command. Available: tree | preview <full_path> | refresh | ask <question> | exit")

if __name__ == "__main__":
    main()
