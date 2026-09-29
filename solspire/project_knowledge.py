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


def build_knowledge_summary(project_id: str, embedding_provider=None) -> dict[str, Any]:
    from solspire.project_store import (
        list_memory,
        list_files,
        list_repositories,
        list_tasks,
        list_events,
        list_conversations,
    )
    from solspire.embedding_provider import get_embedding_provider

    mem = _safe_list(list_memory, project_id)
    files = _safe_list(list_files, project_id)
    repos = _safe_list(list_repositories, project_id)
    tasks = _safe_list(list_tasks, project_id)
    events = _safe_list(list_events, project_id)
    convs = _safe_list(list_conversations, project_id)
    provider = embedding_provider or get_embedding_provider()

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
        "embeddings": provider.describe(project_id=project_id),
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "note": "Knowledge summary is read-only. Not authorization.",
        },
    }


def build_derived_graph(project_id: str) -> dict[str, Any]:
    """Compatibility wrapper for the bounded semantic graph projection."""
    from solspire.semantic_graph import build_bounded_semantic_graph
    return build_bounded_semantic_graph(project_id)


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
