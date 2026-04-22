#!/usr/bin/env python3
"""
Push local files to GitHub via the Git Data API.
No git required. Uses GITHUB_PERSONAL_ACCESS_TOKEN from environment.

Usage:
  python3 scripts/github_push.py                        # push all FILES
  python3 scripts/github_push.py --files a.py b.tsx     # push only listed files
  python3 scripts/github_push.py --message "my msg"     # custom commit message
"""
import os
import sys
import argparse
import base64
import httpx

TOKEN  = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
REPO   = "Arkadia-Oversoul-Prism/Arkadia"
BRANCH = "main"
BASE   = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
}

# ── All known files (local_path → repo_path) ─────────────────────────────────
ALL_FILES = {
    "api/main.py":                                             "api/main.py",
    "web/public_prism/.env.production":                        "web/public_prism/.env.production",
    "web/public_prism/package.json":                           "web/public_prism/package.json",
    "web/public_prism/tailwind.config.js":                     "web/public_prism/tailwind.config.js",
    "web/public_prism/vite.config.js":                         "web/public_prism/vite.config.js",
    "web/public_prism/src/App.tsx":                            "web/public_prism/src/App.tsx",
    "web/public_prism/src/index.css":                          "web/public_prism/src/index.css",
    "web/public_prism/src/main.tsx":                           "web/public_prism/src/main.tsx",
    "web/public_prism/src/pages/LivingGate.tsx":               "web/public_prism/src/pages/LivingGate.tsx",
    "web/public_prism/src/pages/LivingGate.css":               "web/public_prism/src/pages/LivingGate.css",
    "web/public_prism/src/pages/CoherenceReset.tsx":           "web/public_prism/src/pages/CoherenceReset.tsx",
    "web/public_prism/src/pages/SpiralCodexFeed.tsx":          "web/public_prism/src/pages/SpiralCodexFeed.tsx",
    "web/public_prism/src/components/ArkadiaNavigation.tsx":   "web/public_prism/src/components/ArkadiaNavigation.tsx",
    "web/public_prism/src/components/ArkanaCommune.tsx":       "web/public_prism/src/components/ArkanaCommune.tsx",
    "web/public_prism/src/components/MoonPhaseRing.tsx":       "web/public_prism/src/components/MoonPhaseRing.tsx",
    "web/public_prism/src/components/ShereSanctuary.tsx":      "web/public_prism/src/components/ShereSanctuary.tsx",
    "web/public_prism/src/components/SpiralVault.tsx":         "web/public_prism/src/components/SpiralVault.tsx",
    "web/public_prism/src/hooks/useArkadiaAuth.ts":            "web/public_prism/src/hooks/useArkadiaAuth.ts",
    "web/public_prism/src/hooks/useSpiralQuantumResonance.ts": "web/public_prism/src/hooks/useSpiralQuantumResonance.ts",
    "web/public_prism/src/lib/firebase.ts":                    "web/public_prism/src/lib/firebase.ts",
    "web/public_prism/src/services/conversationService.ts":    "web/public_prism/src/services/conversationService.ts",
    "forge/templates.py":                                      "forge/templates.py",
    "docs/creative/auralis-dna.md":                            "docs/creative/auralis-dna.md",
    "scripts/github_push.py":                                  "scripts/github_push.py",
}


def api(method, path, **kwargs):
    url = f"{BASE}{path}"
    r = httpx.request(method, url, headers=HEADERS, timeout=30, **kwargs)
    if r.status_code >= 400:
        print(f"  ERROR {r.status_code}: {r.text[:400]}")
        sys.exit(1)
    return r.json()


def create_blob(content_bytes: bytes) -> str:
    data = api("POST", f"/repos/{REPO}/git/blobs", json={
        "content": base64.b64encode(content_bytes).decode(),
        "encoding": "base64",
    })
    return data["sha"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", metavar="FILE",
                        help="Push only these local paths (subset of ALL_FILES)")
    parser.add_argument("--message", default="", help="Commit message")
    args = parser.parse_args()

    if args.files:
        files = {k: v for k, v in ALL_FILES.items() if k in args.files}
        missing = [f for f in args.files if f not in ALL_FILES]
        if missing:
            print(f"WARNING: not in ALL_FILES registry: {missing}")
            for f in missing:
                if os.path.exists(f):
                    files[f] = f
    else:
        files = ALL_FILES

    msg = args.message or "chore: Arkadia Cycle 11 sync"

    print(f"Pushing {len(files)} files to {REPO}@{BRANCH} via GitHub API...\n")

    ref_data    = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    head_sha    = ref_data["object"]["sha"]
    print(f"HEAD: {head_sha}")

    commit_data = api("GET", f"/repos/{REPO}/git/commits/{head_sha}")
    base_tree   = commit_data["tree"]["sha"]
    print(f"Base tree: {base_tree}\n")

    tree_entries = []
    for local_path, repo_path in files.items():
        if not os.path.exists(local_path):
            print(f"  SKIP (not found): {local_path}")
            continue
        with open(local_path, "rb") as f:
            content = f.read()
        blob_sha = create_blob(content)
        tree_entries.append({
            "path": repo_path,
            "mode": "100644",
            "type": "blob",
            "sha":  blob_sha,
        })
        print(f"  ✓ blob: {repo_path}")

    if not tree_entries:
        print("\nNo files to push.")
        return

    print(f"\nCreating tree with {len(tree_entries)} entries...")
    new_tree     = api("POST", f"/repos/{REPO}/git/trees",
                       json={"base_tree": base_tree, "tree": tree_entries})
    new_tree_sha = new_tree["sha"]
    print(f"New tree: {new_tree_sha}")

    new_commit = api("POST", f"/repos/{REPO}/git/commits", json={
        "message": msg,
        "tree":    new_tree_sha,
        "parents": [head_sha],
    })
    new_commit_sha = new_commit["sha"]
    print(f"New commit: {new_commit_sha}")

    api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}",
        json={"sha": new_commit_sha, "force": True})

    print(f"\n✅ Pushed to {BRANCH} successfully!")
    print(f"   Commit: https://github.com/{REPO}/commit/{new_commit_sha}")
    print(f"   Vercel will auto-deploy from https://github.com/{REPO}")


if __name__ == "__main__":
    main()
