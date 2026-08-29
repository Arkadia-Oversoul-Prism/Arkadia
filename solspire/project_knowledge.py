"""WEAVER-W5 — Project Knowledge OS (composition over existing store).

Derived views only. Not a second memory/graph/vector authority.
"""
from __future__ import annotations

from typing import Any


def _safe_list(fn, *args, default=None):
    try:
        return fn(*args)
    except Exception:
        return default if default is not None else []


def build_knowledge_summary(project_id: str) -> dict[str, Any]:
    from solspire.project_store import (
        list_memory,
        list_files,
        list_repositories,
        list_tasks,
        list_events,
        list_conversations,
    )

    mem = _safe_list(list_memory, project_id)
    files = _safe_list(list_files, project_id)
    repos = _safe_list(list_repositories, project_id)
    tasks = _safe_list(list_tasks, project_id)
    events = _safe_list(list_events, project_id)
    convs = _safe_list(list_conversations, project_id)

    return {
        "project_id": project_id,
        "sources": {
            "memory": len(mem),
            "files": len(files),
            "repositories": len(repos),
            "tasks": len(tasks),
            "events": len(events),
            "conversations": len(convs),
        },
        "items": {
            "repositories": [
                {
                    "id": r.get("id"),
                    "owner": r.get("owner"),
                    "repo": r.get("repo"),
                    "branch": r.get("branch"),
                    "label": r.get("label"),
                    "provenance": "SOURCE-BACKED",
                }
                for r in (repos or [])[:50]
            ],
            "files": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "mime_type": f.get("mime_type"),
                    "provenance": "SOURCE-BACKED",
                }
                for f in (files or [])[:50]
            ],
            "memory": [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "tags": m.get("tags"),
                    "provenance": "SOURCE-BACKED",
                    "epistemic": "OPERATOR_CONTEXT",
                    "note": "Memory is contextual. Not FACT. Not authorization.",
                }
                for m in (mem or [])[:50]
            ],
            "tasks": [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "status": t.get("status"),
                    "provenance": "SOURCE-BACKED",
                }
                for t in (tasks or [])[:50]
            ],
        },
        "embeddings": {
            "status": "NOT_AVAILABLE",
            "note": (
                "No project-scoped embedding/vector store is attached to SolSpire "
                "project_store. Global Knowledge OS embeddings (if any) are not "
                "projected here to avoid cross-scope fabrication."
            ),
            "coverage": None,
            "dimensions": None,
        },
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "note": "Knowledge summary is read-only. Not authorization.",
        },
    }


def build_derived_graph(project_id: str) -> dict[str, Any]:
    """Derived graph from store tables — not a second authoritative graph DB."""
    from solspire.project_store import (
        list_memory,
        list_files,
        list_repositories,
        list_tasks,
        list_events,
        list_conversations,
    )

    nodes: list[dict[str, Any]] = [
        {
            "id": f"project:{project_id}",
            "type": "Project",
            "label": project_id,
            "classification": "SOURCE-BACKED",
        }
    ]
    edges: list[dict[str, Any]] = []

    def add_children(items: list, ntype: str, edge_type: str, label_key: str = "title"):
        for it in items or []:
            iid = it.get("id") or it.get("name")
            if not iid:
                continue
            nid = f"{ntype.lower()}:{iid}"
            label = it.get(label_key) or it.get("name") or it.get("repo") or str(iid)
            nodes.append(
                {
                    "id": nid,
                    "type": ntype,
                    "label": label,
                    "classification": "SOURCE-BACKED",
                }
            )
            edges.append(
                {
                    "from": f"project:{project_id}",
                    "to": nid,
                    "type": edge_type,
                    "classification": "SOURCE-BACKED",
                    "provenance": "project_store",
                }
            )

    add_children(list_repositories(project_id), "Repository", "CONTAINS", "label")
    add_children(list_files(project_id), "File", "CONTAINS", "name")
    add_children(list_memory(project_id), "Memory", "CONTAINS", "title")
    add_children(list_tasks(project_id), "Task", "CONTAINS", "title")
    add_children(list_conversations(project_id), "Conversation", "CONTAINS", "title")
    for ev in list_events(project_id) or []:
        eid = ev.get("id") or f"ev-{len(nodes)}"
        nid = f"event:{eid}"
        nodes.append(
            {
                "id": nid,
                "type": "Event",
                "label": (ev.get("summary") or ev.get("event_type") or "event")[:80],
                "classification": "SOURCE-BACKED",
            }
        )
        edges.append(
            {
                "from": f"project:{project_id}",
                "to": nid,
                "type": "ASSOCIATED_WITH",
                "classification": "SOURCE-BACKED",
                "provenance": "project_store.events",
            }
        )

    return {
        "project_id": project_id,
        "kind": "DERIVED",
        "note": (
            "Derived from project_store tables. Not a second graph authority. "
            "No fabricated semantic edges between unrelated entities."
        ),
        "nodes": nodes,
        "edges": edges,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
        "authorization": {
            "Execution": "LOCKED",
            "note": "Graph view is read-only. Not authorization.",
        },
    }


def build_project_context_for_weaver(project: dict[str, Any]) -> dict[str, Any]:
    """Read-only context envelope. Never authorization."""
    pid = project.get("id")
    summary = build_knowledge_summary(pid) if pid else {}
    return {
        "project_id": pid,
        "project_name": project.get("name"),
        "owner": project.get("owner_uid") or project.get("owner"),
        "status": project.get("status"),
        "knowledge": summary.get("sources"),
        "repositories": (summary.get("items") or {}).get("repositories"),
        "memory_note": "Memory listed in knowledge OS is OPERATOR_CONTEXT, not FACT.",
        "embeddings": summary.get("embeddings"),
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "Mutation path": "K3 ONLY",
            "note": "ProjectContext is context only. Not PassSpec. Not PatchApproval.",
        },
    }
