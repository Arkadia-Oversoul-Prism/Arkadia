"""SolSpire Console — FastAPI Router.

Exposes all Milestone 1 kernel capabilities via clean REST endpoints.
Mounted at /solspire in the main Oracle FastAPI app.

Endpoints:
  POST /solspire/run              — end-to-end: request → plan → execute → results
  GET  /solspire/providers        — list providers + active
  POST /solspire/providers/select — switch active provider
  GET  /solspire/projects         — list all projects
  POST /solspire/projects         — create project
  GET  /solspire/projects/{id}    — load project
  POST /solspire/projects/{id}/archive
  GET  /solspire/executions       — list executions
  GET  /solspire/executions/{id}  — get execution status
  POST /solspire/executions/{id}/pause
  POST /solspire/executions/{id}/resume
  POST /solspire/executions/{id}/cancel
  POST /solspire/tools/fs/read    — read file
  POST /solspire/tools/fs/write   — write file
  POST /solspire/tools/fs/list    — list directory
  POST /solspire/tools/github/repos
  POST /solspire/tools/github/tree
  GET  /solspire/status           — kernel status + metrics
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/solspire", tags=["SolSpire Console"])


# ── Request models ─────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    request: str
    provider: str | None = None

class SelectProviderRequest(BaseModel):
    name: str

class CreateProjectRequest(BaseModel):
    name: str
    metadata: dict[str, Any] = {}

class FsReadRequest(BaseModel):
    path: str

class FsWriteRequest(BaseModel):
    path: str
    content: str

class FsListRequest(BaseModel):
    path: str = "."

class GithubReposRequest(BaseModel):
    owner: str

class GithubTreeRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"

class GithubReadRequest(BaseModel):
    owner: str
    repo: str
    path: str
    branch: str = "main"

class GithubCommitRequest(BaseModel):
    owner: str
    repo: str
    path: str
    content: str
    message: str = ""
    branch: str = "main"

class AddKeyRequest(BaseModel):
    provider: str
    label: str = ""
    key: str

class SetActiveKeyRequest(BaseModel):
    key_id: str

class SetModelRequest(BaseModel):
    provider: str
    model: str

class SetFallbackRequest(BaseModel):
    enabled: bool


# ── End-to-end run ─────────────────────────────────────────────────────────

@router.post("/run")
async def run_request(body: RunRequest) -> dict[str, Any]:
    """Route a natural language request through the full kernel pipeline."""
    from solspire.provider_manager import get_manager
    from solspire.intent_router import get_router
    from solspire.planner import get_planner
    from solspire.execution_runtime import get_runtime

    started = time.time()

    # Optional provider switch
    if body.provider:
        try:
            get_manager().select_provider(body.provider)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Classify → Plan → Execute
    intent = get_router().classify(body.request)
    plan = get_planner().create_plan(body.request, intent)
    valid = get_planner().validate_plan(plan)
    if not valid:
        raise HTTPException(status_code=422, detail="Planner produced an invalid plan")

    execution = get_runtime().execute(plan)

    # Wait for completion (max 60s for Milestone 1 sync flow)
    deadline = time.time() + 60
    while time.time() < deadline:
        from solspire.execution_runtime import ExecutionStatus
        if execution.status not in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED):
            break
        time.sleep(0.25)

    return {
        "ok": execution.status.value == "completed",
        "intent": intent.value,
        "plan": plan.to_dict(),
        "execution": execution.to_dict(),
        "elapsed_ms": round((time.time() - started) * 1000),
    }


# ── Providers ──────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers() -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    return {"providers": m.list_providers(), "active": m.active_provider(), "token_usage": m.token_usage()}


@router.post("/providers/select")
async def select_provider(body: SelectProviderRequest) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        get_manager().select_provider(body.name)
        return {"ok": True, "active": body.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Projects ───────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects(status: str | None = None) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    projects = get_project_manager().list_projects(status=status)
    return {"projects": [p.to_dict() for p in projects], "count": len(projects)}


@router.post("/projects")
async def create_project(body: CreateProjectRequest) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    try:
        p = get_project_manager().create(body.name, body.metadata)
        return {"ok": True, "project": p.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    try:
        p = get_project_manager().load(project_id)
        return {"project": p.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/projects/{project_id}/archive")
async def archive_project(project_id: str) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    try:
        get_project_manager().archive(project_id)
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


# ── Executions ─────────────────────────────────────────────────────────────

@router.get("/executions")
async def list_executions() -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    execs = get_runtime().list_executions()
    return {"executions": execs, "active": get_runtime().active_count()}


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    ex = get_runtime().get(execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution": ex.to_dict()}


@router.post("/executions/{execution_id}/pause")
async def pause_execution(execution_id: str) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    try:
        get_runtime().pause(execution_id)
        return {"ok": True, "status": "paused"}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/executions/{execution_id}/resume")
async def resume_execution(execution_id: str) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    try:
        get_runtime().resume(execution_id)
        return {"ok": True, "status": "running"}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    try:
        get_runtime().cancel(execution_id)
        return {"ok": True, "status": "cancelled"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── File System Tools ──────────────────────────────────────────────────────

@router.post("/tools/fs/read")
async def fs_read(body: FsReadRequest) -> dict[str, Any]:
    from solspire.tools_fs import read_file
    return read_file(body.path)


@router.post("/tools/fs/write")
async def fs_write(body: FsWriteRequest) -> dict[str, Any]:
    from solspire.tools_fs import write_file
    return write_file(body.path, body.content)


@router.post("/tools/fs/list")
async def fs_list(body: FsListRequest) -> dict[str, Any]:
    from solspire.tools_fs import list_directory
    return list_directory(body.path)


# ── GitHub Tools ───────────────────────────────────────────────────────────

@router.post("/tools/github/repos")
async def github_repos(body: GithubReposRequest) -> dict[str, Any]:
    from solspire.tools_github import list_repos
    return list_repos(body.owner)


@router.post("/tools/github/tree")
async def github_tree(body: GithubTreeRequest) -> dict[str, Any]:
    from solspire.tools_github import get_tree
    return get_tree(body.owner, body.repo, body.branch)


@router.post("/tools/github/read")
async def github_read(body: GithubReadRequest) -> dict[str, Any]:
    from solspire.tools_github import read_file
    return read_file(body.owner, body.repo, body.path, body.branch)


@router.post("/tools/github/commit")
async def github_commit(body: GithubCommitRequest) -> dict[str, Any]:
    from solspire.tools_github import commit_file
    return commit_file(body.owner, body.repo, body.path, body.content, body.message, body.branch)


# ── Provider Key Management ─────────────────────────────────────────────────

@router.get("/providers/keys")
async def list_provider_keys(provider: str | None = None) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    return {
        "keys": m.list_keys(provider),
        "models": m.get_models(),
        "auto_fallback": m.get_auto_fallback(),
    }


@router.post("/providers/keys")
async def add_provider_key(body: AddKeyRequest) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        key_id = get_manager().add_key(body.provider, body.label, body.key)
        return {"ok": True, "key_id": key_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/providers/keys/{key_id}")
async def delete_provider_key(key_id: str) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    removed = get_manager().remove_key(key_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"ok": True}


@router.post("/providers/keys/{key_id}/activate")
async def activate_provider_key(key_id: str) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    # Find provider for this key
    all_keys = m.list_keys()
    entry = next((k for k in all_keys if k["id"] == key_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Key not found")
    ok = m.set_active_key(entry["provider"], key_id)
    return {"ok": ok}


@router.post("/providers/model")
async def set_provider_model(body: SetModelRequest) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        get_manager().set_model(body.provider, body.model)
        return {"ok": True, "provider": body.provider, "model": body.model}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/providers/fallback")
async def set_auto_fallback(body: SetFallbackRequest) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    get_manager().set_auto_fallback(body.enabled)
    return {"ok": True, "auto_fallback": body.enabled}


# ── Status ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def console_status() -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    from solspire.execution_runtime import get_runtime
    from solspire.project_manager import get_project_manager

    runtime = get_runtime()
    pm = get_manager()

    projects = get_project_manager().list_projects(status="active")
    executions = runtime.list_executions()

    return {
        "version": {
            "console": "1.0",
            "kernel":  "0.1",
            "codex_app": "0.4",
            "publishing_app": "0.2",
            "research_app": "0.1",
        },
        "providers": {
            "active": pm.active_provider(),
            "available": pm.list_providers(),
            "token_usage": pm.token_usage(),
        },
        "projects": {
            "active_count": len(projects),
        },
        "executions": {
            "total": len(executions),
            "active": runtime.active_count(),
            "by_status": _count_by_status(executions),
        },
        "milestone": 1,
        "phase": 1,
    }


# ── Project Sub-Resources ──────────────────────────────────────────────────────

class UpdateProjectRequest(BaseModel):
    name: str | None = None
    status: str | None = None
    description: str | None = None

class CreateConversationRequest(BaseModel):
    title: str = "Untitled"

class AppendMessageRequest(BaseModel):
    role: str = "user"
    content: str

class CreateFileRequest(BaseModel):
    name: str
    content: str = ""
    mime_type: str = "text/plain"

class UpdateFileRequest(BaseModel):
    content: str
    name: str | None = None

class LinkRepoRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"
    label: str = ""

class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    assigned_to: str = ""
    priority: str = "normal"

class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    assigned_to: str | None = None
    priority: str | None = None

class AddMemoryRequest(BaseModel):
    title: str
    content: str
    tags: list[str] = []

class UpdateMemoryRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None

class ProjectRunRequest(BaseModel):
    request: str
    provider: str | None = None


@router.put("/projects/{project_id}")
async def update_project(project_id: str, body: UpdateProjectRequest) -> dict[str, Any]:
    import time, sqlite3, os
    db_path = os.environ.get("SOLSPIRE_PROJECTS_DB", "data/solspire_projects.db")
    fields, vals = [], []
    if body.name is not None:
        fields.append("name=?"); vals.append(body.name.strip())
    if body.status is not None:
        fields.append("status=?"); vals.append(body.status)
    if body.description is not None:
        import json
        from solspire.project_manager import get_project_manager
        p = get_project_manager().load(project_id)
        p.metadata["description"] = body.description
        fields.append("metadata=?"); vals.append(json.dumps(p.metadata))
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    fields.append("updated_at=?"); vals.append(time.time()); vals.append(project_id)
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id=?", vals)
    return {"ok": True}


@router.get("/projects/{project_id}/conversations")
async def project_list_conversations(project_id: str) -> dict[str, Any]:
    from solspire.project_store import list_conversations
    items = list_conversations(project_id)
    return {"conversations": items, "count": len(items)}


@router.post("/projects/{project_id}/conversations")
async def project_create_conversation(project_id: str, body: CreateConversationRequest) -> dict[str, Any]:
    from solspire.project_store import create_conversation
    return create_conversation(project_id, body.title)


@router.delete("/projects/{project_id}/conversations/{conv_id}")
async def project_archive_conversation(project_id: str, conv_id: str) -> dict[str, Any]:
    from solspire.project_store import archive_conversation
    archive_conversation(conv_id)
    return {"ok": True}


@router.post("/projects/{project_id}/conversations/{conv_id}/messages")
async def project_append_message(project_id: str, conv_id: str, body: AppendMessageRequest) -> dict[str, Any]:
    from solspire.project_store import append_message
    return append_message(conv_id, body.role, body.content)


@router.get("/projects/{project_id}/files")
async def project_list_files(project_id: str) -> dict[str, Any]:
    from solspire.project_store import list_files
    return {"files": list_files(project_id)}


@router.post("/projects/{project_id}/files")
async def project_create_file(project_id: str, body: CreateFileRequest) -> dict[str, Any]:
    from solspire.project_store import create_file
    return create_file(project_id, body.name, body.content, body.mime_type)


@router.get("/projects/{project_id}/files/{file_id}")
async def project_get_file(project_id: str, file_id: str) -> dict[str, Any]:
    from solspire.project_store import get_file
    f = get_file(file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return f


@router.put("/projects/{project_id}/files/{file_id}")
async def project_update_file(project_id: str, file_id: str, body: UpdateFileRequest) -> dict[str, Any]:
    from solspire.project_store import update_file
    return update_file(file_id, body.content, body.name)


@router.delete("/projects/{project_id}/files/{file_id}")
async def project_delete_file(project_id: str, file_id: str) -> dict[str, Any]:
    from solspire.project_store import delete_file
    if not delete_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"ok": True}


@router.get("/projects/{project_id}/repositories")
async def project_list_repos(project_id: str) -> dict[str, Any]:
    from solspire.project_store import list_repositories
    return {"repositories": list_repositories(project_id)}


@router.post("/projects/{project_id}/repositories")
async def project_link_repo(project_id: str, body: LinkRepoRequest) -> dict[str, Any]:
    from solspire.project_store import link_repository
    return link_repository(project_id, body.owner, body.repo, body.branch, body.label)


@router.delete("/projects/{project_id}/repositories/{repo_id}")
async def project_unlink_repo(project_id: str, repo_id: str) -> dict[str, Any]:
    from solspire.project_store import unlink_repository
    if not unlink_repository(repo_id):
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"ok": True}


@router.get("/projects/{project_id}/tasks")
async def project_list_tasks(project_id: str, status: str | None = None) -> dict[str, Any]:
    from solspire.project_store import list_tasks
    return {"tasks": list_tasks(project_id, status)}


@router.post("/projects/{project_id}/tasks")
async def project_create_task(project_id: str, body: CreateTaskRequest) -> dict[str, Any]:
    from solspire.project_store import create_task
    return create_task(project_id, body.title, body.description, body.assigned_to, body.priority)


@router.put("/projects/{project_id}/tasks/{task_id}")
async def project_update_task(project_id: str, task_id: str, body: UpdateTaskRequest) -> dict[str, Any]:
    from solspire.project_store import update_task
    return update_task(task_id, title=body.title, description=body.description,
                       status=body.status, assigned_to=body.assigned_to, priority=body.priority)


@router.delete("/projects/{project_id}/tasks/{task_id}")
async def project_delete_task(project_id: str, task_id: str) -> dict[str, Any]:
    from solspire.project_store import delete_task
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.get("/projects/{project_id}/memory")
async def project_list_memory(project_id: str, q: str = "") -> dict[str, Any]:
    from solspire.project_store import list_memory
    return {"memory": list_memory(project_id, q)}


@router.post("/projects/{project_id}/memory")
async def project_add_memory(project_id: str, body: AddMemoryRequest) -> dict[str, Any]:
    from solspire.project_store import add_memory
    return add_memory(project_id, body.title, body.content, body.tags)


@router.put("/projects/{project_id}/memory/{mem_id}")
async def project_update_memory(project_id: str, mem_id: str, body: UpdateMemoryRequest) -> dict[str, Any]:
    from solspire.project_store import update_memory
    return update_memory(mem_id, body.title, body.content, body.tags)


@router.delete("/projects/{project_id}/memory/{mem_id}")
async def project_delete_memory(project_id: str, mem_id: str) -> dict[str, Any]:
    from solspire.project_store import delete_memory
    if not delete_memory(mem_id):
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"ok": True}


@router.get("/projects/{project_id}/events")
async def project_list_events(project_id: str, event_type: str | None = None) -> dict[str, Any]:
    from solspire.project_store import list_events
    return {"events": list_events(project_id, event_type)}


@router.post("/projects/{project_id}/run")
async def project_run(project_id: str, body: RunRequest) -> dict[str, Any]:
    """Run an intent in the context of a project — logs an event on completion."""
    import time as _time
    from solspire.provider_manager import get_manager
    from solspire.intent_router import get_router
    from solspire.planner import get_planner
    from solspire.execution_runtime import get_runtime, ExecutionStatus
    from solspire.project_store import log_event

    started = _time.time()
    if body.provider:
        try:
            get_manager().select_provider(body.provider)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    intent = get_router().classify(body.request)
    plan = get_planner().create_plan(body.request, intent)
    if not get_planner().validate_plan(plan):
        raise HTTPException(status_code=422, detail="Invalid plan")

    execution = get_runtime().execute(plan)
    deadline = _time.time() + 60
    while _time.time() < deadline:
        if execution.status not in (ExecutionStatus.RUNNING, ExecutionStatus.PAUSED):
            break
        _time.sleep(0.25)

    elapsed = round((_time.time() - started) * 1000)
    log_event(project_id, "workflow_run",
              f"⟐ {intent.value}: {body.request[:80]}",
              {"status": execution.status.value, "elapsed_ms": elapsed})

    return {
        "ok": execution.status.value == "completed",
        "intent": intent.value,
        "plan": plan.to_dict(),
        "execution": execution.to_dict(),
        "elapsed_ms": elapsed,
    }


def _count_by_status(execs: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ex in execs:
        s = ex.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


__all__ = ["router"]
