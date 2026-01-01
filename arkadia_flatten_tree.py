"""
arkadia_flatten_tree.py
Flatten Arkadia Drive tree into path → document map
"""
import json
from arkadia_drive_tree_paths import build_tree_with_paths
from arkadia_drive_sync import refresh_arkadia_cache

def flatten_tree(tree):
    flat_map = {}
    def _flatten(node):
        if node["mimeType"] != "application/vnd.google-apps.folder":
            flat_map[node["full_path"]] = {
                "id": node["id"],
                "name": node["name"],
                "mimeType": node["mimeType"],
                "preview": node["preview"]
            }
        for child in node.get("children", []):
            _flatten(child)
    for root in tree:
        _flatten(root)
    return flat_map

if __name__ == "__main__":
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents") or []
    tree = build_tree_with_paths(docs)
    flat_map = flatten_tree(tree)
    print(f"Total documents flattened: {len(flat_map)}")
    # Save to arkadia_corpus_map.json
    with open("arkadia_corpus_map.json", "w", encoding="utf-8") as f:
        json.dump(flat_map, f, ensure_ascii=False, indent=2)
    print("✅ arkadia_corpus_map.json updated with full paths")
