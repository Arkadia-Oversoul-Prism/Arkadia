# Phase 1 — Corpus Synchronisation Design

**Status:** Design complete. Awaiting approval before implementation.  
**Date:** 2026-07-24  
**Workstream:** C — Corpus Synchronisation

---

## Problem Statement

`github_corpus.py` fetches the **entire repository tree** on every sync invocation:

```python
# Current behaviour (simplified):
tree = fetch_github_tree(repo, branch)   # GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
for item in tree:
    if should_ingest(item):
        content = fetch_file(item["url"])
        ingest(content)
```

Problems:
1. **No state** — every sync re-fetches every eligible file, regardless of whether it changed.
2. **No SHA comparison** — files are re-ingested even when content is identical.
3. **No pagination** — GitHub tree API returns all items in one payload; large repos hit API limits.
4. **No resumability** — if sync crashes mid-run, it restarts from the beginning.
5. **No rate-limit awareness** — `requests` calls with no retry/backoff.
6. **Root cause of "downloads too much"** — there is no incremental state at all.

Adding a `limit=100` parameter does not fix the architecture — it just caps damage.

---

## Design Goals

1. **Incremental** — only fetch files whose SHA has changed since the last sync.
2. **Persistent sync state** — store the tree SHA and per-file SHAs between runs.
3. **Resumable** — if a sync is interrupted, the next run picks up where it left off.
4. **Rate-limit safe** — exponential backoff, respect `X-RateLimit-Remaining`.
5. **Paginated** — use the GitHub Trees API correctly; handle truncated responses.
6. **No architecture change to the ingest pipeline** — `ingest()` is called with the same arguments; only the sync driver changes.

---

## Sequence Diagram

```
Sync Driver                   GitHub API              Sync State (SQLite)
     │                             │                        │
     │── load_sync_state() ────────────────────────────────►│
     │◄── {tree_sha: "abc123",                              │
     │     file_shas: {path: sha, ...}} ───────────────────│
     │                             │                        │
     │── GET /git/trees/{branch}?recursive=1 ──────────────►│
     │◄── {sha: "def456", tree: [...], truncated: false} ───│
     │                             │                        │
     │ if tree_sha == "def456":    │                        │
     │   return (no changes)       │                        │
     │                             │                        │
     │ for each item in tree:      │                        │
     │   if item.sha == known_sha[item.path]:               │
     │     skip (unchanged)        │                        │
     │   else:                     │                        │
     │── GET /contents/{path} ─────►                        │
     │◄── {content: base64...} ────│                        │
     │                             │                        │
     │   ingest(content, path)     │                        │
     │   save_file_state(path, sha) ──────────────────────► │
     │                             │                        │
     │── save_sync_state(tree_sha) ──────────────────────── ►│
     │                             │                        │
```

---

## Persistent Sync State Schema

Two new tables in `data/runtime.db` (the Phase 1 SQLite database):

```sql
-- Tracks the last-seen tree SHA for the whole repo
CREATE TABLE IF NOT EXISTS corpus_sync_state (
    key        TEXT PRIMARY KEY,   -- e.g. "Arkadia-Oversoul-Prism/Arkadia:main"
    tree_sha   TEXT NOT NULL,      -- last successful tree SHA
    synced_at  REAL NOT NULL,      -- unix timestamp of last successful sync
    file_count INTEGER NOT NULL DEFAULT 0
);

-- Tracks per-file SHAs for change detection
CREATE TABLE IF NOT EXISTS corpus_file_state (
    repo_key   TEXT NOT NULL,      -- FK to corpus_sync_state.key
    path       TEXT NOT NULL,      -- e.g. "docs/ARKADIA_SPEC_v3.md"
    file_sha   TEXT NOT NULL,      -- git blob SHA
    ingested_at REAL NOT NULL,     -- when this version was ingested
    PRIMARY KEY (repo_key, path)
);
```

---

## Incremental Sync Algorithm

```python
def incremental_sync(repo: str, branch: str, token: str | None) -> SyncResult:
    repo_key = f"{repo}:{branch}"
    state = load_sync_state(repo_key)              # from SQLite

    # Step 1: fetch current tree SHA (cheap — just the tree root)
    current_tree = fetch_tree_root(repo, branch, token)  # GET /git/trees/{sha}
    if current_tree.sha == state.tree_sha:
        return SyncResult(changed=0, skipped=0, reason="tree_unchanged")

    # Step 2: fetch full tree (recursive)
    tree_items = fetch_full_tree(repo, current_tree.sha, token)
    # Handle truncated=true by falling back to /contents/ recursive listing

    # Step 3: compare SHAs
    known_shas = load_file_shas(repo_key)          # {path: sha} from SQLite
    to_ingest = [
        item for item in tree_items
        if should_ingest(item) and known_shas.get(item.path) != item.sha
    ]

    # Step 4: fetch and ingest changed files only
    changed = 0
    for item in to_ingest:
        try:
            content = fetch_file_content(item, token)  # with retry + backoff
            ingest_document(content, item.path)
            save_file_sha(repo_key, item.path, item.sha)  # checkpoint per file
            changed += 1
        except RateLimitError:
            break  # resume next run from checkpoint
        except Exception:
            log_warning(item.path)  # skip; retry on next run
            continue

    # Step 5: save new tree SHA only if all files processed
    if changed == len(to_ingest):
        save_sync_state(repo_key, current_tree.sha, changed)

    return SyncResult(changed=changed, skipped=len(tree_items) - len(to_ingest))
```

**Resumability:** Each file's SHA is saved immediately after ingestion. If the sync crashes after ingesting 40 of 60 changed files, the next run will find those 40 already at their new SHA and skip them — only the remaining 20 are fetched.

---

## Rate-Limit Handling

```python
def fetch_with_backoff(url: str, token: str | None, max_retries: int = 3) -> requests.Response:
    for attempt in range(max_retries):
        resp = requests.get(url, headers=_headers(token), timeout=30)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 403:
            remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
            reset_at = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            if remaining == 0:
                wait = max(0, reset_at - time.time()) + 1
                logger.warning("GitHub rate limit hit — waiting %.0fs", wait)
                time.sleep(min(wait, 300))  # cap at 5 min
                continue
        if resp.status_code == 404:
            raise FileNotFoundError(url)
        backoff = 2 ** attempt
        time.sleep(backoff)
    resp.raise_for_status()
```

---

## Migration Path

| Step | Change | Deployable? |
|---|---|---|
| 1 | Add `corpus_sync_state` and `corpus_file_state` tables to `data/runtime.db` | Yes |
| 2 | Add `github_corpus_incremental.py` alongside existing `github_corpus.py` | Yes |
| 3 | Test incremental sync in isolation (unit tests + manual run) | Yes |
| 4 | Switch `/api/sync` endpoint to call incremental sync | Yes |
| 5 | After two stable sync cycles: remove `github_corpus.py` legacy code | Yes |

The old `github_corpus.py` remains callable throughout migration. It is not deleted until the incremental version is proven stable.

---

## What This Does NOT Do

- Does not change the `ingest()` API or the corpus schema
- Does not introduce webhooks (a GitHub push webhook would eliminate polling entirely — a Phase 2 option)
- Does not introduce async HTTP (the sync runs in a background job — synchronous is fine)
- Does not add authentication beyond the existing `GITHUB_PERSONAL_ACCESS_TOKEN`

---

*All Workstream C deliverables are complete.*
