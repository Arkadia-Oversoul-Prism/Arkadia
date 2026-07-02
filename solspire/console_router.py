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


def _count_by_status(execs: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ex in execs:
        s = ex.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


__all__ = ["router"]
