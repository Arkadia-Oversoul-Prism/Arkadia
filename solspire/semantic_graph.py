"""MVP2-05 — bounded semantic graph projection.

The graph is a derived view over explicit project-store relationships.
It is not an authoritative graph database and never authorizes execution.
"""
from __future__ import annotations

import json
from typing import Any


_REF_KEYS = {
    "file_id": "file",
    "repository_id": "repository",
    "task_id": "task",
    "memory_id": "memory",
    "conversation_id": "conversation",
}


def build_bounded_semantic_graph(project_id: str) -> dict[str, Any]:
    """Add only semantic edges explicitly recorded in project event data.

    No text similarity, embeddings, LLM inference, or guessed relationships are
    used. Invalid/missing references are omitted rather than inferred.
    """
    from solspire.project_store import (
        list_conversations,
        list_events,
        list_files,
        list_memory,
        list_repositories,
        list_tasks,
    )

    sources = {
        "file": list_files(project_id) or [],
        "repository": list_repositories(project_id) or [],
        "task": list_tasks(project_id) or [],
        "memory": list_memory(project_id) or [],
        "conversation": list_conversations(project_id) or [],
    }

    nodes: dict[str, dict[str, Any]] = {
        f"project:{project_id}": {
            "id": f"project:{project_id}",
            "type": "Project",
            "label": project_id,
            "classification": "SOURCE-BACKED",
        }
    }
    for kind, items in sources.items():
        for item in items:
            iid = item.get("id")
            if not iid:
                continue
            label = item.get("title") or item.get("name") or item.get("label") or item.get("repo") or str(iid)
            nodes[f"{kind}:{iid}"] = {
                "id": f"{kind}:{iid}",
                "type": kind.title(),
                "label": label,
                "classification": "SOURCE-BACKED",
            }

    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in list_events(project_id) or []:
        raw = event.get("data") or {}
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        event_id = event.get("id")
        for key, kind in _REF_KEYS.items():
            target_id = data.get(key)
            if not target_id:
                continue
            target = f"{kind}:{target_id}"
            if target not in nodes:
                continue
            source = f"event:{event_id}" if event_id else None
            if not source:
                continue
            nodes.setdefault(
                source,
                {
                    "id": source,
                    "type": "Event",
                    "label": event.get("summary") or event.get("event_type") or "event",
                    "classification": "SOURCE-BACKED",
                },
            )
            edge_key = (source, target, "REFERENCES")
            if edge_key in seen:
                continue
            seen.add(edge_key)
            edges.append(
                {
                    "from": source,
                    "to": target,
                    "type": "REFERENCES",
                    "classification": "SOURCE-BACKED",
                    "provenance": "project_store.events.data",
                    "evidence_id": event_id,
                }
            )

    return {
        "project_id": project_id,
        "kind": "DERIVED_BOUNDED_SEMANTIC",
        "nodes": list(nodes.values()),
        "edges": edges,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
        "limitations": [
            "Only explicit event-data references are promoted to semantic edges.",
            "No embeddings, similarity, or inferred relationships are used.",
            "This is not an authoritative graph store.",
        ],
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "note": "Graph projection is read-only and cannot authorize mutation.",
        },
    }
