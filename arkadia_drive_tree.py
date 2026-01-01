"""
arkadia_drive_tree.py
Generates a fully nested folder + document tree from Arkadia Drive snapshot.
"""
import json
from arkadia_drive_sync import refresh_arkadia_cache

def build_recursive_tree(docs):
    """Build fully nested tree using parent info from Drive snapshot."""
    tree = {}
    id_to_node = {}
    # Prepare nodes
    for d in docs:
        node = {
            "id": d.get("id"),
            "name": d.get("name"),
            "mimeType": d.get("mimeType"),
            "preview": (d.get("preview") or "")[:200],
            "children": []
        }
        id_to_node[d["id"]] = node

    # Map children to parents
    root_nodes = []
    for d in docs:
        parents = d.get("parents") or []
        if parents:
            for p in parents:
                parent_node = id_to_node.get(p)
                if parent_node and parent_node["mimeType"] == "application/vnd.google-apps.folder":
                    parent_node["children"].append(id_to_node[d["id"]])
        else:
            # Top-level nodes
            root_nodes.append(id_to_node[d["id"]])

    return root_nodes

if __name__ == "__main__":
    snap = refresh_arkadia_cache(force=True)
    docs = snap.get("documents") or []
    tree = build_recursive_tree(docs)
    print(json.dumps(tree, indent=2, ensure_ascii=False))
