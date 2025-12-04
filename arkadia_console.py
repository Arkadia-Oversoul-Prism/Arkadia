#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    print("WARNING: google.generativeai module not installed. 'ask' feature will fail.")

# Globals
snap = None
docs = []
tree_data = {}
path_map = {}

# Environment variables
ARKADIA_FOLDER_ID = os.environ.get("ARKADIA_FOLDER_ID")
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_FILE")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def refresh_corpus():
    global snap, docs, tree_data, path_map
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents", [])
    tree_data, path_map = build_tree_with_paths(docs)
    print(f"Documents cached: {len(docs)}")
    return snap

def display_dashboard():
    print("──────────────────────── ARKADIA DASHBOARD ────────────────────────")
    print(f"Last sync: {snap.get('last_sync') if snap else 'never'}")
    print(f"Documents cached: {len(docs)}\n")
    print("Top previews:")
    for d in docs[:5]:
        print(f"- {d.get('full_path')} | {d.get('mimeType')}")
    print("\nCommands: tree | preview <full_path> | ask <question> | refresh | exit")

def cmd_tree():
    for path in tree_data:
        print(f"- {path}")

def cmd_preview(full_path):
    doc = path_map.get(full_path)
    if not doc:
        print(f"Document not found: {full_path}")
        return
    print(json.dumps({
        "name": doc.get("name"),
        "full_path": doc.get("full_path"),
        "mimeType": doc.get("mimeType"),
        "preview": doc.get("preview", "")
    }, indent=2))

def cmd_ask(question):
    context_docs = get_corpus_context(max_documents=10)
    context_text = "\n".join([d.get("preview","") for d in context_docs])
    try:
        response = genai.chat(
            model="chat-bison-001",
            messages=[
                {"role": "system", "content": "You are Arkadia Codex AI."},
                {"role": "user", "content": f"{question}\nContext:\n{context_text}"}
            ]
        )
        answer = response.last or response.get("content", "")
    except Exception as e:
        answer = f"Gemini call failed: {e}"

    print(json.dumps({
        "question": question,
        "answer": answer,
        "context": context_text
    }, indent=2))

def main():
    global snap, docs
    snap = refresh_corpus()
    display_dashboard()
    while True:
        try:
            cmd = input("arkadia>: ").strip()
        except EOFError:
            print("\nExiting Arkadia Console.")
            break

        if cmd.lower() == "exit":
            break
        elif cmd.lower() == "refresh":
            snap = refresh_corpus()
        elif cmd.lower() == "tree":
            cmd_tree()
        elif cmd.lower().startswith("preview "):
            _, path = cmd.split(" ", 1)
            cmd_preview(path)
        elif cmd.lower().startswith("ask "):
            _, question = cmd.split(" ", 1)
            cmd_ask(question)
        else:
            print("Unknown command. Available: tree | preview <full_path> | ask <question> | refresh | exit")

if __name__ == "__main__":
    main()
