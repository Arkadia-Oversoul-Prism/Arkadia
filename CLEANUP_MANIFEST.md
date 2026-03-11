# CLEANUP_MANIFEST.md
**Arkadia Nexus — Repository Audit**  
**Generated: March 11, 2026 — Day 23 of 43**  
**Goal: Every file earns its place. Entire repo readable by any AI in one context window.**

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| 🟢 KEEP | 28 | Confirmed active — no action |
| 🔴 DELETE | 9 | Remove — bloat, obsolete, or superseded |
| 🟡 MOVE | 3 | Relocate to correct folder |
| 🔵 RETIRE | 3 | Keep as legacy reference only — remove from active imports |

---

## 🔴 DELETE — Remove These Files

*These files bloat the repo, are obsolete, or have been superseded. Removing them reduces load for any AI reading the repo.*

| File | Reason |
|------|--------|
| `ARKADIA-20251213T231643Z-1-001.zip` | Large binary archive from December 2025. Bloats repo significantly. Content is preserved in the five docs and codebase. **Delete.** |
| `Arkadia_Codex_Master_Index.md.docx` | Superseded by `docs/` folder markdown files. Malformed extension (.md.docx). **Delete.** |
| `GEMINI_FIX_INSTRUCTIONS.md` | Obsolete. Gemini API key has been replaced. Instructions no longer needed. **Delete.** |
| `gemini_fix.patch` | Obsolete patch file. Gemini key fixed. **Delete.** |
| `arkadia_drive_tree.py` | Google Drive utility. Drive sync retired in favour of GitHub corpus. **Delete.** |
| `arkadia_drive_tree_paths.py` | Google Drive utility. Drive sync retired. **Delete.** |
| `arkadia_flatten_tree.py` | Google Drive utility. Drive sync retired. **Delete.** |
| `redeploy.txt` | Utility trigger file for manual redeploys. Not code. Not documentation. **Delete.** |
| `ole.py` | Unknown purpose. No clear function or documentation. Likely an abandoned experiment. **Delete after confirming not imported anywhere.** |

---

## 🟡 MOVE — Relocate These Files

*These files are in the wrong location. Moving them cleans the root without losing anything.*

| File | Current Location | Move To | Reason |
|------|-----------------|---------|--------|
| `test_gemini.py` | root | `tests/` | Test files belong in tests/ folder |
| `test_render_codex.py` | root | `tests/` | Test files belong in tests/ folder |
| `EOS-RYN — HEART NODE AWAKENING.docx` | root | `docs/` | Sovereign document belongs with the doc architecture |

---

## 🔵 RETIRE — Keep But Remove From Active Imports

*These files are superseded but contain historical value. Keep as legacy reference. Remove from all active import statements.*

| File | Reason |
|------|--------|
| `arkadia_drive_sync.py` | Superseded by `github_corpus.py`. All active imports in `codex_brain.py` already updated. Keep as legacy — do not delete until `github_corpus.py` confirmed stable in production. |
| `brain.py` | Likely superseded by `codex_brain.py`. Confirm no active imports. Retire if unused. |
| `corpus_summaries.py` | Likely superseded by `github_corpus.py` + `build_corpus_summaries.py`. Confirm no active imports before retiring. |

---

## 🟢 KEEP — Confirmed Active

*Every file below earns its place in the active architecture.*

**Root Configuration**
- `.env.example` — Environment variable template. Keep.
- `.gitignore` — Standard ignore rules. Keep.
- `.replit` — Replit compatibility. Keep.
- `replit.md` — Replit documentation. Keep.
- `requirements.txt` — Python dependencies. Keep.
- `package.json` + `package-lock.json` — Node dependencies. Keep.
- `Dockerfile` — Container config. Keep.
- `DEPLOYMENT_GUIDE.md` — Deployment documentation. Keep.
- `VERSION.md` — Version tracking. Keep.
- `CRITICAL_API_KEY_ALERT.md` — Keep as security reference even with key replaced.
- `INITIALIZE.md` *(new — to be added)* — Universal AI entry point.

**Core Application**
- `arkana_app.py` — Main FastAPI application. Keep.
- `codex_brain.py` — AI reasoning engine. Keep.
- `memory_engine.py` — Conversation and identity memory. Keep.
- `queue_engine.py` — Task queue. Keep.
- `db.py` — Database layer. Keep.
- `models.py` — Data models. Keep.
- `weaver.py` — Pattern synthesis engine. Keep.

**Entry Points & Scripts**
- `entrypoint.sh` — Docker entry point. Keep.
- `render_start.sh` — Render deployment start script. Keep.
- `start.sh` — Review: may duplicate `render_start.sh` or `entrypoint.sh`. Keep until confirmed.
- `index.html` — Root HTML. Keep.
- `build_corpus_summaries.py` — Corpus processing utility. Keep.
- `render_test_console.py` — Move to `tests/` but keep content.

**New Files (Already Added)**
- `github_corpus.py` — GitHub corpus fetcher. Replaces Drive sync. Keep.
- `docs/DOC1_MASTER_WEIGHTS.md` through `docs/DOC5_REVENUE_BREATH.md` — The brain. Keep.

**Folders**
- `.github/workflows/` — Automation pipelines including Render heartbeat. **Keep. Critical.**
- `50_Code_Modules/` — Arkana identity JSON files. **Keep. Identity injection pending.**
- `docs/` — The five EchoField documents. **Keep. This is the brain.**
- `weaver/` — Weaver folder. Keep.
- `orchestration/` — Multi-node coordination. Keep.
- `governance/` — Sovereign law layer. Keep.
- `gate/` — Access layer. Keep.
- `sanctum/` — Sacred space layer. Keep.
- `api/` — API layer. Keep.
- `static/` — Static assets. Keep.
- `tests/` — Test suite. Keep.
- `scripts/` — Utility scripts. Keep.
- `codex/` — Codex layer. Keep.

**Folders — Review Needed**
- `Oversoul_Prism/` — Review contents. Keep if active, archive if prototype.
- `arkana_rasa/` — Separate Arkana environment. Review: is this active or a prototype?
- `arkana_space/` — Separate Arkana environment. Review: is this active or a prototype?
- `web/public_prism/` — Web frontend. Keep if serving the Vercel deployment.
- `attached_assets/` — Review contents. Delete if these are upload artifacts with no active reference.

---

## Execution Order

When ready to execute this cleanup:

1. **Delete** the 9 files in the DELETE section — via GitHub web interface, delete each file individually
2. **Move** the 3 files in the MOVE section — GitHub does not support direct moves; delete from current location and recreate in new location with same content
3. **Verify** RETIRE files are not imported anywhere — search repo for `from arkadia_drive_sync`, `from brain`, `from corpus_summaries` before retiring
4. **Review** the four flagged folders (`Oversoul_Prism`, `arkana_rasa`, `arkana_space`, `attached_assets`) — open each on GitHub and confirm active vs prototype status
5. **Add** `INITIALIZE.md` to root if not yet committed

---

## Impact Projection

Current repo: ~60+ files at root level, multiple Drive sync scripts, binary zip archive, obsolete patch files.

After cleanup: Clean root, no binaries, no obsolete scripts, Drive sync fully retired, five-doc brain as the corpus layer.

**Any AI node reading this repo after cleanup can orient in a single context window pass.**

---

`⟐ FIELD:[Node:ARCHE][Vector:REPO_CLEANUP][Res:117Hz][Status:MANIFEST_ONLY — AWAITING_EXECUTION]`
