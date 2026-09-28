"""Phase 3 — bounded project activity -> canonical WorkEvent projection.

This is a derived translator, not a new activity store.

Source of truth:
    project_events

Projection:
    project_events -> WorkEvent spine

The projection is idempotent by reusing each source project-event UUID as a
stable WorkEvent identity. It only emits events for projects owned by the
authenticated subject and only when that subject already has a canonical
workspace.

Activity is not provenance, authorization, execution, or verification.
"""
from __future__ import annotations

from typing import Any

from solspire.project_manager import get_project_manager
from solspire.project_store import list_events
from solspire.workspace_manager import get_workspace_manager
from solspire.workevent_manager import get_workevent_manager


_EVENT_TYPE_MAP = {
    "conversation_created": "PROJECT_CONVERSATION_CREATED",
    "conversation_message": "PROJECT_CONVERSATION_MESSAGE",
    "file_created": "PROJECT_FILE_CREATED",
    "repo_linked": "PROJECT_REPOSITORY_LINKED",
    "task_created": "PROJECT_TASK_CREATED",
    "memory_added": "PROJECT_MEMORY_ADDED",
    "workflow_run": "PROJECT_WORKFLOW_RECORDED",
    "weaver_analyze": "PROJECT_WEAVER_ANALYZED",
}

# Project events are mutable application activity, so the projection remains
# explicitly recorded rather than VERIFIED. No source event is promoted by
# entering the WorkEvent spine.
_STATUS = "RECORDED"


def _artifact_refs(data: dict[str, Any]) -> list[str]:
    """Return only explicit artifact identifiers already present in the event."""
    refs: list[str] = []
    for key in (
        "conversation_id",
        "thread_uuid",
        "file_id",
        "repository_id",
        "repo_id",
        "task_id",
        "memory_id",
        "execution_id",
    ):
        value = data.get(key)
        if value:
            refs.append(str(value))
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(refs))


def _work_event_id(project_event_id: str) -> str:
    return f"project-event:{project_event_id}"


def project_event_to_workevent(
    *,
    subject_uid: str,
    workspace_id: str,
    project_id: str,
    event: dict[str, Any],
) -> dict[str, Any] | None:
    """Project one project event into WorkEvent, idempotently.

    Returns the existing/new WorkEvent as a dict, or None when the source
    event type is intentionally outside Phase 3's activity vocabulary.
    """
    event_type = _EVENT_TYPE_MAP.get(str(event.get("event_type") or ""))
    if not event_type:
        return None

    source_id = str(event.get("id") or "").strip()
    if not source_id:
        return None

    manager = get_workevent_manager()
    work_event_id = _work_event_id(source_id)
    existing = manager.get(work_event_id, subject_uid)
    if existing is not None:
        return existing.to_dict()

    data = event.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    work_event = manager.create(
        work_event_id=work_event_id,
        subject_ref=subject_uid,
        workspace_ref=workspace_id,
        event_type=event_type,
        occurred_at=float(event.get("created_at") or 0),
        work_ref=project_id,
        scope_ref=source_id,
        artifact_refs=_artifact_refs(data),
        status=_STATUS,
        schema_version="1",
    )
    return work_event.to_dict()


def project_activity_to_workspace(
    subject_uid: str,
    *,
    limit_per_project: int = 100,
) -> dict[str, Any]:
    """Synchronize owned project activity into the subject's WorkEvent spine.

    No workspace is provisioned here. If the canonical workspace does not
    already exist, the projection reports UNAVAILABLE instead of creating
    authority or silently provisioning state.
    """
    uid = (subject_uid or "").strip()
    if not uid:
        return {
            "status": "UNAVAILABLE",
            "reason": "authenticated subject is required",
            "project_events_seen": 0,
            "work_events_created": 0,
            "work_events_reused": 0,
        }

    workspace = get_workspace_manager().get_for_subject(uid)
    if workspace is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "canonical workspace not found",
            "project_events_seen": 0,
            "work_events_created": 0,
            "work_events_reused": 0,
        }

    projects = get_project_manager().list_projects(owner_uid=uid)
    seen = created = reused = projected = 0

    for project in projects:
        events = list_events(project.id, limit=limit_per_project)
        for event in reversed(events):
            mapped = _EVENT_TYPE_MAP.get(str(event.get("event_type") or ""))
            if not mapped:
                continue
            seen += 1
            work_event_id = _work_event_id(str(event.get("id") or ""))
            existing = get_workevent_manager().get(work_event_id, uid)
            result = project_event_to_workevent(
                subject_uid=uid,
                workspace_id=workspace.id,
                project_id=project.id,
                event=event,
            )
            if result is None:
                continue
            projected += 1
            if existing is None:
                created += 1
            else:
                reused += 1

    return {
        "status": "LIVE",
        "workspace_id": workspace.id,
        "projects_scanned": len(projects),
        "project_events_seen": seen,
        "work_events_projected": projected,
        "work_events_created": created,
        "work_events_reused": reused,
    }


__all__ = [
    "project_event_to_workevent",
    "project_activity_to_workspace",
]
