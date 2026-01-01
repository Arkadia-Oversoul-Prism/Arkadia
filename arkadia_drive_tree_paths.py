"""
arkadia_drive_tree_paths.py
Generates a fully nested folder + document tree from Arkadia Drive snapshot,
reconstructing full paths for each file/folder.
"""
import json
from arkadia_drive_sync import refresh_arkadia_cache

def build_tree_with_paths(docs):
    """Build fully nested tree and reconstruct full paths."""
    id_to_node = {}
    for d in docs:
        node = {
            "id": d.get("id"),
            "name": d.get("name"),
            "mimeType": d.get("mimeType"),
            "preview": (d.get("preview") or "")[:200],
            "children": [],
            "parents": d.get("parents") or [],
            "full_path": None  # will be populated
        }
        id_to_node[d["id"]] = node

    # Build tree structure
    root_nodes = []
    for node in id_to_node.values():
        if node["parents"]:
            for p in node["parents"]:
                parent_node = id_to_node.get(p)
                if parent_node and parent_node["mimeType"] == "application/vnd.google-apps.folder":
                    parent_node["children"].append(node)
        else:
            root_nodes.append(node)

    # Helper to reconstruct full paths recursively
    def set_full_path(node, parent_path=""):
        node["full_path"] = f"{parent_path}/{node['name']}" if parent_path else f"/{node['name']}"
        for child in node["children"]:
            set_full_path(child, node["full_path"])

    for root in root_nodes:
        set_full_path(root)

    return root_nodes

if __name__ == "__main__":
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents") or []
    tree = build_tree_with_paths(docs)
    print(json.dumps(tree, indent=2, ensure_ascii=False))
