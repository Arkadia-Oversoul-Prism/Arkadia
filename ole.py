[1mdiff --git a/.github/workflows/auto-commit-corpus.yml b/.github/workflows/auto-commit-corpus.yml[m
[1mdeleted file mode 100644[m
[1mindex b9ea701..0000000[m
[1m--- a/.github/workflows/auto-commit-corpus.yml[m
[1m+++ /dev/null[m
[36m@@ -1,38 +0,0 @@[m
[31m-name: Auto-Commit Arkadia Corpus Map[m
[31m-on:[m
[31m-  workflow_dispatch:[m
[31m-  push:[m
[31m-    branches: [ main ][m
[31m-  schedule:[m
[31m-    - cron: "0 */6 * * *"[m
[31m-[m
[31m-jobs:[m
[31m-  commit-corpus:[m
[31m-    runs-on: ubuntu-latest[m
[31m-    steps:[m
[31m-      - uses: actions/checkout@v4[m
[31m-        with:[m
[31m-          persist-credentials: true[m
[31m-      - name: Setup Python[m
[31m-        uses: actions/setup-python@v4[m
[31m-        with:[m
[31m-          python-version: "3.11"[m
[31m-      - name: Install deps (fast, best-effort)[m
[31m-        run: |[m
[31m-          pip install --no-cache-dir -r requirements.txt || true[m
[31m-      - name: Run flatten & refresh (if script exists)[m
[31m-        run: |[m
[31m-          if [ -f ./arkadia_flatten_tree.py ]; then[m
[31m-            python ./arkadia_flatten_tree.py || true[m
[31m-          fi[m
[31m-      - name: Commit and push if changed[m
[31m-        run: |[m
[31m-          git config user.name "arkadia-bot"[m
[31m-          git config user.email "bot@arkadia.local"[m
[31m-          if ! git diff --quiet; then[m
[31m-            git add arkadia_corpus_map.json[m
[31m-            git commit -m "[auto] refresh arkadia_corpus_map.json"[m
[31m-            git push origin HEAD:main[m
[31m-          else[m
[31m-            echo "No changes to commit"[m
[31m-          fi[m
[1mdiff --git a/arkadia_console.py b/arkadia_console.py[m
[1mold mode 100755[m
[1mnew mode 100644[m
[1mindex 0a1e93b..05dc6be[m
[1m--- a/arkadia_console.py[m
[1m+++ b/arkadia_console.py[m
[36m@@ -1,2 +1,109 @@[m
 #!/usr/bin/env python3[m
[31m-# (paste the full arkadia_console.py content from the previous block here)[m
[32m+[m[32m# -*- coding: utf-8 -*-[m
[32m+[m
[32m+[m[32mimport os[m
[32m+[m[32mimport sys[m
[32m+[m[32mimport json[m
[32m+[m[32mfrom arkadia_drive_sync import refresh_arkadia_cache, build_tree_with_paths, get_corpus_context[m
[32m+[m
[32m+[m[32mtry:[m
[32m+[m[32m    import google.generativeai as genai[m
[32m+[m[32mexcept ModuleNotFoundError:[m
[32m+[m[32m    print("WARNING: google.generativeai module not installed. 'ask' feature will fail.")[m
[32m+[m
[32m+[m[32m# Globals[m
[32m+[m[32msnap = None[m
[32m+[m[32mdocs = [][m
[32m+[m[32mtree_data = {}[m
[32m+[m[32mpath_map = {}[m
[32m+[m
[32m+[m[32m# Environment variables[m
[32m+[m[32mARKADIA_FOLDER_ID = os.environ.get("ARKADIA_FOLDER_ID")[m
[32m+[m[32mSERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_FILE")[m
[32m+[m[32mGEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")[m
[32m+[m
[32m+[m[32mif GEMINI_API_KEY:[m
[32m+[m[32m    genai.configure(api_key=GEMINI_API_KEY)[m
[32m+[m
[32m+[m[32mdef refresh_corpus():[m
[32m+[m[32m    global snap, docs, tree_data, path_map[m
[32m+[m[32m    snap = refresh_arkadia_cache(force=True)[m
[32m+[m[32m    docs = snap.get("documents", [])[m
[32m+[m[32m    tree_data, path_map = build_tree_with_paths(docs)[m
[32m+[m[32m    print(f"Documents cached: {len(docs)}")[m
[32m+[m[32m    return snap[m
[32m+[m
[32m+[m[32mdef display_dashboard():[m
[32m+[m[32m    print("──────────────────────── ARKADIA DASHBOARD ────────────────────────")[m
[32m+[m[32m    print(f"Last sync: {snap.get('last_sync') if snap else 'never'}")[m
[32m+[m[32m    print(f"Documents cached: {len(docs)}\n")[m
[32m+[m[32m    print("Top previews:")[m
[32m+[m[32m    for d in docs[:5]:[m
[32m+[m[32m        print(f"- {d.get('full_path')} | {d.get('mimeType')}")[m
[32m+[m[32m    print("\nCommands: tree | preview <ful