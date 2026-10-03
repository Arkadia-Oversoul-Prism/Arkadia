"""SolSpire Console — FastAPI Router.

Exposes all Milestone 1 kernel capabilities via clean REST endpoints.
Mounted at /solspire in the main Oracle FastAPI app.

Endpoints:
  POST /solspire/run              — end-to-end intent → plan → execute
  GET  /solspire/providers        — list providers + active
  POST /solspire/providers/select — switch active provider
  GET  /solspire/projects         — list projects
  POST /solspire/projects         — create project
  GET  /solspire/projects/{id}    — load project
  POST /solspire/projects/{id}/archive
  GET  /solspire/workspace        — resolve canonical workspace for authenticated subject
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

import re
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.auth import require_auth

from solspire.workevent_router import router as workevent_router
from solspire.workload_router import router as workload_router
from solspire.pulse_router import router as pulse_router
from solspire.synthesis_router import router as synthesis_router
from solspire.proposal_router import router as proposal_router
from solspire.enterprise_router import router as enterprise_router
from solspire.buyer_recon_router import router as buyer_recon_router

# Pass 01R: every /solspire route requires a verified Firebase identity.
# require_auth rejects unauthenticated requests before any handler runs.
router = APIRouter(
    prefix="/solspire",
    tags=["SolSpire Console"],
    dependencies=[Depends(require_auth)],
)

# Compose Move 2–7 surfaces as siblings under /solspire:
# /workspace, /workevents, /workloads, /pulses, /syntheses, /proposals
router.include_router(workevent_router)
router.include_router(workload_router)
router.include_router(pulse_router)
router.include_router(synthesis_router)
router.include_router(proposal_router)
router.include_router(enterprise_router)
router.include_router(buyer_recon_router)


async def require_project_owner(project_id: str, user: dict = Depends(require_auth)) -> dict:
    """FastAPI dependency: resolve the project and enforce caller ownership.

    Ownership is derived exclusively from the authenticated Firebase uid.
    Missing, legacy (NULL owner), and cross-owner projects all return 404 so
    existence is never leaked across users.
    """
    from solspire.project_manager import get_project_manager
    try:
        project = get_project_manager().load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    owner = (project.owner_uid or "").strip()
    if not owner or owner != user["uid"]:
        raise HTTPException(status_code=404, detail="Project not found")
    return user


# ── Request models ─────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    request: str
    provider: str | None = None

class SelectProviderRequest(BaseModel):
    name: str

class CreateProjectRequest(BaseModel):
    name: str
    template_id: str = "enterprise"
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

def _execute_run(body: RunRequest, user: dict[str, Any]) -> dict[str, Any]:
    """Single canonical SolSpire run pipeline (provider → classify → plan → validate → execute → wait)."""
    from solspire.provider_manager import get_manager
    from solspire.intent_router import get_router
    from solspire.planner import get_planner
    from solspire.execution_runtime import get_runtime, ExecutionStatus

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

    execution = get_runtime().execute(plan, owner_uid=user["uid"])

    # Wait for completion (max 60s for Milestone 1 sync flow)
    deadline = time.time() + 60
    while time.time() < deadline:
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


@router.post("/run")
async def run_request(body: RunRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Route a natural language request through the full kernel pipeline."""
    return _execute_run(body, user)


# ── Providers ──────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    return {"providers": m.list_providers(), "active": m.active_provider(), "token_usage": m.token_usage()}

@router.post("/providers/select")
async def select_provider(body: SelectProviderRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        get_manager().select_provider(body.name)
        return {"ok": True, "active": body.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Projects ───────────────────────────────────────────────────────────────

@router.get("/project-templates")
async def get_project_templates(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Expose server-owned project templates without granting runtime authority."""
    from solspire.project_templates import list_project_templates
    return {"templates": list_project_templates()}


@router.get("/projects")
async def list_projects(status: str | None = None, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    projects = get_project_manager().list_projects(status=status, owner_uid=user["uid"])
    return {"projects": [p.to_dict() for p in projects], "count": len(projects)}

@router.post("/projects")
async def create_project(body: CreateProjectRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.project_templates import instantiate_project_metadata
    try:
        metadata = instantiate_project_metadata(body.template_id, body.metadata)
        p = get_project_manager().create(body.name, metadata, owner_uid=user["uid"])
        return {"ok": True, "project": p.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/projects/instantiate-eden")
async def instantiate_eden_project(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Idempotently instantiate Eden for the authenticated sovereign owner.

    The endpoint is deliberately owner-bound: the authenticated Firebase uid
    is the project owner. It creates no alternate Eden database and delegates
    operational behavior to the generic project runtime.
    """
    import json
    from solspire.project_manager import get_project_manager
    from solspire.project_store import list_files, list_memory, list_tasks
    from solspire.project_templates import instantiate_project_metadata
    from solspire.eden_seed import EDEN_SEED_VERSION, seed_eden_project

    pm = get_project_manager()
    owned = pm.list_projects(owner_uid=user["uid"])
    eden = next(
        (
            p for p in owned
            if p.name.strip().lower() == "eden food systems"
            and (p.metadata or {}).get("project_runtime", {}).get("template_id") == "eden-food-systems"
        ),
        None,
    )
    created = False
    if eden is None:
        metadata = instantiate_project_metadata(
            "eden-food-systems",
            {
                "description": "Eden Food Systems — From Source to Market.",
                "sovereign_role": "Zahrune ID",
                "seed_version": EDEN_SEED_VERSION,
            },
        )
        eden = pm.create("Eden Food Systems", metadata, owner_uid=user["uid"])
        created = True

    runtime = dict((eden.metadata or {}).get("project_runtime") or {})
    seed_version = (eden.metadata or {}).get("seed_version")
    seeded = seed_version == EDEN_SEED_VERSION

    if not seeded:
        seed_result = seed_eden_project(eden.id)
        updated_metadata = dict(eden.metadata or {})
        updated_metadata["seed_version"] = EDEN_SEED_VERSION
        updated_metadata["seed_result"] = seed_result
        pm.apply_fields(
            eden.id,
            ["metadata=?", "updated_at=?"],
            [json.dumps(updated_metadata), __import__("time").time(), eden.id],
        )
        eden = pm.load(eden.id)
    else:
        seed_result = (eden.metadata or {}).get("seed_result") or {
            "seed_version": EDEN_SEED_VERSION,
            "files": len(list_files(eden.id)),
            "memory": len(list_memory(eden.id)),
            "tasks": len(list_tasks(eden.id)),
        }

    return {
        "ok": True,
        "created": created,
        "project": eden.to_dict(),
        "seed": seed_result,
        "owner_binding": {
            "owner_uid": user["uid"],
            "authority": "authenticated sovereign account",
        },
        "runtime": runtime,
        "operating_model": {
            "weaver": "generic project-level runtime",
            "arkana": "generic project-scoped conversational interface",
            "domain": "living_larder projection; live capability remains separately verified",
        },
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    try:
        p = get_project_manager().load(project_id)
        return {"project": p.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")

@router.post("/projects/{project_id}/archive")
async def archive_project(project_id: str, user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    try:
        get_project_manager().archive(project_id)
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


# ── Canonical SolSpire Workspace ────────────────────────────────────────────

@router.get("/workspace")
async def get_canonical_workspace(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Resolve the single canonical workspace bound to the authenticated subject.

    Resolution is idempotent: an existing workspace is returned unchanged;
    otherwise the bounded canonical workspace is provisioned for the verified
    Firebase uid. No client-supplied subject or authority fields are accepted.
    """
    from solspire.workspace_manager import get_workspace_manager
    try:
        workspace = get_workspace_manager().get_or_create(user["uid"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "workspace": workspace.to_dict(),
        "canonical": True,
        "subject_binding": "authenticated_firebase_uid",
    }


# ── Executions ─────────────────────────────────────────────────────────────

def _owned_execution(execution_id: str, uid: str):
    """Load an execution and enforce ownership. Raises 404 on miss or cross-owner."""
    from solspire.execution_runtime import get_runtime
    ex = get_runtime().get(execution_id, owner_uid=uid)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex


@router.get("/executions")
async def list_executions(user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    execs = get_runtime().list_executions(owner_uid=user["uid"])
    active = sum(1 for ex in execs if ex["status"] in ("running", "paused"))
    return {"executions": execs, "active": active}

@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    return {"execution": _owned_execution(execution_id, user["uid"]).to_dict()}

@router.post("/executions/{execution_id}/pause")
async def pause_execution(execution_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    _owned_execution(execution_id, user["uid"])
    try:
        get_runtime().pause(execution_id)
        return {"ok": True, "status": "paused"}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/resume")
async def resume_execution(execution_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    _owned_execution(execution_id, user["uid"])
    try:
        get_runtime().resume(execution_id)
        return {"ok": True, "status": "running"}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.execution_runtime import get_runtime
    _owned_execution(execution_id, user["uid"])
    try:
        get_runtime().cancel(execution_id)
        return {"ok": True, "status": "cancelled"}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Filesystem tools ───────────────────────────────────────────────────────

@router.post("/tools/fs/read")
async def fs_read(body: FsReadRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_fs import read_file
    return read_file(body.path)

@router.post("/tools/fs/write")
async def fs_write(body: FsWriteRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_fs import write_file
    return write_file(body.path, body.content)

@router.post("/tools/fs/list")
async def fs_list(body: FsListRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_fs import list_directory
    return list_directory(body.path)


# ── GitHub tools ───────────────────────────────────────────────────────────

@router.post("/tools/github/repos")
async def github_repos(body: GithubReposRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_github import list_repos
    return list_repos(body.owner)

@router.post("/tools/github/tree")
async def github_tree(body: GithubTreeRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_github import get_tree
    return get_tree(body.owner, body.repo, body.branch)

@router.post("/tools/github/read")
async def github_read(body: GithubReadRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_github import read_file
    return read_file(body.owner, body.repo, body.path, body.branch)

@router.post("/tools/github/commit")
async def github_commit(body: GithubCommitRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.tools_github import commit_file
    return commit_file(body.owner, body.repo, body.path, body.content, body.message, body.branch)


# ── Provider key management ────────────────────────────────────────────────

@router.get("/providers/keys")
async def list_provider_keys(provider: str | None = None, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    return {
        "keys": m.list_keys(provider),
        "models": m.get_models(),
        "auto_fallback": m.get_auto_fallback(),
    }

@router.post("/providers/keys")
async def add_provider_key(body: AddKeyRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        key_id = get_manager().add_key(body.provider, body.label, body.key)
        return {"ok": True, "key_id": key_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/providers/keys/{key_id}")
async def delete_provider_key(key_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    removed = get_manager().remove_key(key_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"ok": True}

@router.post("/providers/keys/{key_id}/activate")
async def activate_provider_key(key_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    m = get_manager()
    # Find provider for this key
    entry = next((k for k in m.list_keys() if k["id"] == key_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Key not found")
    ok = m.set_active_key(entry["provider"], key_id)
    return {"ok": ok}

@router.post("/providers/model")
async def set_provider_model(body: SetModelRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    try:
        get_manager().set_model(body.provider, body.model)
        return {"ok": True, "provider": body.provider, "model": body.model}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/providers/fallback")
async def set_auto_fallback(body: SetFallbackRequest, user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    get_manager().set_auto_fallback(body.enabled)
    return {"ok": True, "auto_fallback": body.enabled}


# ── Project runtime context -------------------------------------------------
@router.get("/projects/{project_id}/runtime-context")
async def project_runtime_context(
    project_id: str,
    user: dict = Depends(require_project_owner),
) -> dict[str, Any]:
    """Return the canonical, bounded control-plane context for a project.

    This is a projection, not a second memory/event/task system. Project-owned
    records come from project_store; Daily Pulse, Workload, and WorkEvents are
    reported from their existing SolSpire spines with their actual binding
    state. Missing project bindings remain UNKNOWN instead of being inferred.
    """
    from datetime import datetime, timezone
    from solspire.project_manager import get_project_manager
    from solspire.project_store import list_events, list_files, list_memory, list_repositories, list_tasks
    from solspire.workspace_manager import get_workspace_manager
    from solspire.pulse_manager import get_pulse_manager
    from solspire.workload_manager import get_workload_manager
    from solspire.workevent_manager import get_workevent_manager
    from solspire.project_knowledge import build_derived_graph, build_project_context_for_weaver

    project = get_project_manager().load(project_id)
    workspace = get_workspace_manager().get_for_subject(user["uid"])

    project_events = list_events(project_id, limit=20)
    project_tasks = list_tasks(project_id)
    project_files = list_files(project_id)
    project_memory = list_memory(project_id)
    project_repositories = list_repositories(project_id)

    pulse = None
    workload = None
    work_events: list[dict[str, Any]] = []
    if workspace is not None:
        pulse = get_pulse_manager().get_for_subject_date(
            user["uid"],
            workspace.id,
            datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        workload = get_workload_manager().get_for_subject(user["uid"], workspace.id)
        work_events = [
            event.to_dict()
            for event in get_workevent_manager().list(user["uid"], workspace.id, 100)
            if event.scope_ref == project_id or event.work_ref == project_id
        ]

    project_payload = project.to_dict()
    project_payload["owner_uid"] = user["uid"]
    arkana_context = build_project_context_for_weaver(project_payload)
    try:
        knowledge_graph = build_derived_graph(project_id)
        graph_state = "PROJECT_STORE_BOUND"
    except Exception as exc:
        knowledge_graph = {"state": "UNAVAILABLE", "detail": f"{type(exc).__name__}: {exc}"}
        graph_state = "UNAVAILABLE"

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "owner_uid": user["uid"],
            "runtime_contract": (project.metadata or {}).get("project_runtime"),
        },
        "arkana_context": arkana_context,
        "knowledge_graph": knowledge_graph,
        "project_store": {
            "tasks": project_tasks[:20],
            "files": project_files[:20],
            "memory": project_memory[:20],
            "events": project_events[:20],
            "repositories": project_repositories[:20],
        },
        "control_plane": {
            "workspace": workspace.to_dict() if workspace else None,
            "daily_pulse": pulse.to_dict() if pulse else None,
            "workload": workload.to_dict() if workload else None,
            "work_events": work_events[:50],
        },
        "binding_state": {
            "daily_pulse": "SUBJECT_WORKSPACE_BOUND" if pulse else "UNKNOWN",
            "workload": "SUBJECT_WORKSPACE_BOUND_NOT_PROJECT_BOUND" if workload else "UNKNOWN",
            "workevents": "PROJECT_SCOPED_MATCHES" if work_events else "UNKNOWN",
            "knowledge_os": "PROJECT_STORE_BOUND",
            "knowledge_graph": graph_state,
            "weaver": "ENGINEERING_LAB_PROJECT_BOUND",
            "arkana": "PROJECT_CONTEXT_CAPABLE",
            "living_larder": "PROJECT_BOUND" if any(
                event.get("event_type") == "living_larder_order_bound" for event in project_events
            ) else "UNKNOWN",
        },
        "epistemic_boundary": (
            "Project records are data/evidence, not authority. A missing project "
            "binding is UNKNOWN; this endpoint does not infer one."
        ),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Governed project execution, integrations and domain bindings ────────────

class CandidatePatchReviewRequest(BaseModel):
    expected_base_digest: str
    changes: list[dict[str, str]]
    allowed_paths: list[str]


class ApplyReviewedPatchRequest(CandidatePatchReviewRequest):
    approved_patch_digest: str
    work_ref: str | None = None


@router.post("/projects/{project_id}/patches/preview")
async def preview_project_patch(
    project_id: str, body: CandidatePatchReviewRequest,
    user: dict = Depends(require_project_owner),
) -> dict[str, Any]:
    from solspire.project_execution_boundary import BoundaryError, safe_relative_path
    from solspire.project_execution_service import canonical_base_digest, candidate_patch_digest
    from solspire.project_store import list_files
    try:
        observed = canonical_base_digest(project_id)
        if observed != body.expected_base_digest:
            raise HTTPException(status_code=409, detail="Canonical base changed; refresh the candidate review")
        names = {str(row.get("name") or "") for row in list_files(project_id)}
        allowed = {safe_relative_path(path) for path in body.allowed_paths}
        paths = [safe_relative_path(str(change.get("path") or "")) for change in body.changes]
    except BoundaryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not paths or any(path not in allowed or path not in names for path in paths):
        raise HTTPException(status_code=400, detail="Patch paths must be existing canonical files inside the explicit allowlist")
    digest = candidate_patch_digest([{"path": path, "content": change.get("content", "")}
                                     for path, change in zip(paths, body.changes)])
    return {"project_id": project_id, "base_digest": observed,
            "candidate_patch_digest": digest, "changed_paths": paths,
            "requires_explicit_human_approval": True,
            "persistence": "NOT_APPLIED"}


@router.post("/projects/{project_id}/patches/apply")
async def apply_project_patch(
    project_id: str, body: ApplyReviewedPatchRequest,
    user: dict = Depends(require_project_owner),
) -> dict[str, Any]:
    from solspire.project_execution_boundary import BoundaryError
    from solspire.project_execution_service import apply_reviewed_project_patch
    try:
        return apply_reviewed_project_patch(
            subject_uid=user["uid"], project_id=project_id,
            expected_base_digest=body.expected_base_digest,
            approved_patch_digest=body.approved_patch_digest,
            changes=body.changes, allowed_paths=body.allowed_paths,
            work_ref=body.work_ref,
        )
    except BoundaryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/integration-health")
async def project_integration_health_route(
    project_id: str, user: dict = Depends(require_project_owner),
) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.integration_health import project_integration_health
    project = get_project_manager().load(project_id)
    return project_integration_health(subject_uid=user["uid"], project=project.to_dict())


@router.post("/projects/{project_id}/living-larder/orders/{order_id}/bind")
async def bind_living_larder_order(
    project_id: str, order_id: str,
    user: dict = Depends(require_project_owner),
) -> dict[str, Any]:
    """Explicitly bind an existing Larder order to this project; never auto-associate."""
    import json
    import os
    import time
    from pathlib import Path
    from solspire.project_store import log_event
    from solspire.workspace_manager import get_workspace_manager
    from solspire.workevent_manager import get_workevent_manager
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace missing; refusing unrecorded domain binding")
    order_path = Path(os.environ.get("LIVING_LARDER_ORDERS_FILE", "data/orders.json"))
    try:
        raw = json.loads(order_path.read_text(encoding="utf-8"))
        orders = raw if isinstance(raw, list) else raw.get("items", [])
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Living Larder order store unavailable")
    except (OSError, ValueError, AttributeError) as exc:
        raise HTTPException(status_code=503, detail=f"Living Larder order store unreadable: {exc}")
    order = next((item for item in orders if str(item.get("order_id") or "") == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Living Larder order not found")
    snapshot = {
        "order_id": order_id,
        "status": str(order.get("status") or "UNKNOWN"),
        "created_at": order.get("created_at"),
        "subtotal": order.get("subtotal"),
        "delivery_fee": order.get("delivery_fee"),
        "total": order.get("total"),
        "item_count": len(order.get("items") or []),
        "source": "living_larder_orders",
    }
    from hashlib import sha256
    snapshot_digest = sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    log_event(project_id, "living_larder_order_bound",
              f"Living Larder order explicitly bound: {order_id}",
              {**snapshot, "snapshot_digest": snapshot_digest, "bound_by": user["uid"]})
    event = get_workevent_manager().create(
        subject_ref=user["uid"], workspace_ref=workspace.id,
        event_type="LIVING_LARDER_ORDER_BOUND", occurred_at=time.time(),
        work_ref=project_id, scope_ref=project_id, actor_ref=user["uid"],
        artifact_refs=[f"living-larder-order:{order_id}"],
        state_after_ref=f"sha256:{snapshot_digest}",
        decision_ref=f"human-project-binding:{project_id}:{order_id}",
        witness_ref=f"sha256:{snapshot_digest}", status="RECORDED",
    )
    return {"ok": True, "project_id": project_id, "order": snapshot,
            "snapshot_digest": snapshot_digest, "work_event": event.to_dict()}


# ── Status ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def console_status(user: dict = Depends(require_auth)) -> dict[str, Any]:
    from solspire.provider_manager import get_manager
    from solspire.execution_runtime import get_runtime
    from solspire.project_manager import get_project_manager

    runtime = get_runtime()
    pm = get_manager()
    projects = get_project_manager().list_projects(status="active", owner_uid=user["uid"])
    executions = runtime.list_executions(owner_uid=user["uid"])

    return {
        "version": {
            "console": "1.0",
            "kernel": "0.1",
            "codex_app": "0.4",
            "publishing_app": "0.2",
            "research_app": "0.1",
        },
        "providers": {
            "active": pm.active_provider(),
            "available": pm.list_providers(),
            "token_usage": pm.token_usage(),
        },
        "projects": {"active_count": len(projects)},
        "executions": {
            "total": len(executions),
            "active": sum(1 for ex in executions if ex["status"] in ("running", "paused")),
            "by_status": _count_by_status(executions),
        },
        "milestone": 1,
        "phase": 1,
    }


# ── Project detail endpoints ───────────────────────────────────────────────

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
async def update_project(project_id: str, body: UpdateProjectRequest,
                         user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    import time
    from solspire.project_manager import get_project_manager
    fields, vals = [], []
    if body.name is not None:
        fields.append("name=?"); vals.append(body.name.strip())
    if body.status is not None:
        fields.append("status=?"); vals.append(body.status)
    if body.description is not None:
        import json
        p = get_project_manager().load(project_id)
        p.metadata["description"] = body.description
        fields.append("metadata=?"); vals.append(json.dumps(p.metadata))
    if not fields:
        raise HTTPException(status_code=400, detail="Nothing to update")
    fields.append("updated_at=?"); vals.append(time.time()); vals.append(project_id)
    get_project_manager().apply_fields(project_id, fields, vals)
    return {"ok": True}


@router.get("/projects/{project_id}/conversations")
async def project_list_conversations(project_id: str,
                                     user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_conversations
    items = list_conversations(project_id)
    return {"conversations": items, "count": len(items)}


@router.post("/projects/{project_id}/conversations")
async def project_create_conversation(project_id: str, body: CreateConversationRequest,
                                      user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import create_conversation
    return create_conversation(project_id, body.title)


@router.delete("/projects/{project_id}/conversations/{conv_id}")
async def project_archive_conversation(project_id: str, conv_id: str,
                                       user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import archive_conversation
    archive_conversation(conv_id)
    return {"ok": True}


@router.post("/projects/{project_id}/conversations/{conv_id}/messages")
async def project_append_message(project_id: str, conv_id: str, body: AppendMessageRequest,
                                 user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.conversation_bridge import (
        ConversationBridgeError,
        append_conversation_turn,
    )
    try:
        return append_conversation_turn(
            project_id=project_id,
            conv_id=conv_id,
            role=body.role,
            content=body.content,
            user_id=user["uid"],
        )
    except ConversationBridgeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/projects/{project_id}/files")
async def project_list_files(project_id: str,
                             user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_files
    return {"files": list_files(project_id)}


@router.post("/projects/{project_id}/files")
async def project_create_file(project_id: str, body: CreateFileRequest,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import create_file
    return create_file(project_id, body.name, body.content, body.mime_type)


@router.get("/projects/{project_id}/files/{file_id}")
async def project_get_file(project_id: str, file_id: str,
                           user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import get_file
    f = get_file(file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return f


@router.put("/projects/{project_id}/files/{file_id}")
async def project_update_file(project_id: str, file_id: str, body: UpdateFileRequest,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import update_file
    return update_file(file_id, body.content, body.name)


@router.delete("/projects/{project_id}/files/{file_id}")
async def project_delete_file(project_id: str, file_id: str,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import delete_file
    if not delete_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"ok": True}


@router.post("/projects/{project_id}/files/{file_id}/copy")
async def project_copy_file(project_id: str, file_id: str,
                            user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import get_file, copy_file
    existing = get_file(file_id)
    if not existing or existing.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        return copy_file(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/files/upload")
async def project_upload_file(project_id: str, request: Request,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("multipart/form-data"):
        raise HTTPException(status_code=400, detail="Expected multipart/form-data")
    body = await request.body()
    boundary = content_type.split("boundary=")[-1].strip('"')
    file_name = "upload"
    raw: bytes = b""
    for part in body.split(("--" + boundary).encode()):
        if b"Content-Disposition" not in part:
            continue
        hdr_end = part.find(b"\r\n\r\n")
        if hdr_end == -1:
            continue
        headers = part[:hdr_end].decode("utf-8", errors="ignore")
        content = part[hdr_end + 4:]
        if content.endswith(b"\r\n"):
            content = content[:-2]
        if 'filename="' in headers:
            fm = re.search(r'filename="([^"]+)"', headers)
            if fm:
                import urllib.parse
                file_name = urllib.parse.unquote(fm.group(1))
            raw = content
    if not raw:
        raise HTTPException(status_code=400, detail="No file provided")
    from kernel.doc_extract import extract_text, make_label
    extracted_text, mime_type = extract_text(file_name, raw)
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded file.")
    from solspire.project_store import create_file
    stored = create_file(project_id, file_name, extracted_text, mime_type)
    try:
        from knowledge.pipeline import ingest
        ingest(
            title=make_label(file_name),
            content=extracted_text,
            note_type="document",
            tags=["solspire", "project", "file", project_id],
            auto_tag=True,
            auto_embed=True,
            auto_link=True,
            user_id=user["uid"],
        )
    except Exception:
        pass
    return {
        "ok": True,
        "file": stored,
        "file_name": file_name,
        "chars": len(extracted_text),
        "message": f"'{file_name}' attached to the project and ingested into Knowledge OS.",
    }


@router.get("/projects/{project_id}/repositories")
async def project_list_repos(project_id: str,
                             user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_repositories
    return {"repositories": list_repositories(project_id)}


@router.post("/projects/{project_id}/repositories")
async def project_link_repo(project_id: str, body: LinkRepoRequest,
                            user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import link_repository
    return link_repository(project_id, body.owner, body.repo, body.branch, body.label)


@router.delete("/projects/{project_id}/repositories/{repo_id}")
async def project_unlink_repo(project_id: str, repo_id: str,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import unlink_repository
    if not unlink_repository(repo_id):
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"ok": True}


@router.get("/projects/{project_id}/tasks")
async def project_list_tasks(project_id: str, status: str | None = None,
                             user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_tasks
    return {"tasks": list_tasks(project_id, status)}


@router.post("/projects/{project_id}/tasks")
async def project_create_task(project_id: str, body: CreateTaskRequest,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import create_task
    return create_task(project_id, body.title, body.description, body.assigned_to, body.priority)


@router.put("/projects/{project_id}/tasks/{task_id}")
async def project_update_task(project_id: str, task_id: str, body: UpdateTaskRequest,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import update_task
    return update_task(
        task_id,
        title=body.title,
        description=body.description,
        status=body.status,
        assigned_to=body.assigned_to,
        priority=body.priority,
    )


@router.delete("/projects/{project_id}/tasks/{task_id}")
async def project_delete_task(project_id: str, task_id: str,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import delete_task
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.get("/projects/{project_id}/memory")
async def project_list_memory(project_id: str, q: str = "",
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_memory
    return {"memory": list_memory(project_id, q)}


@router.post("/projects/{project_id}/memory")
async def project_add_memory(project_id: str, body: AddMemoryRequest,
                             user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import add_memory
    return add_memory(project_id, body.title, body.content, body.tags)


@router.put("/projects/{project_id}/memory/{mem_id}")
async def project_update_memory(project_id: str, mem_id: str, body: UpdateMemoryRequest,
                                user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import update_memory
    return update_memory(mem_id, body.title, body.content, body.tags)


@router.delete("/projects/{project_id}/memory/{mem_id}")
async def project_delete_memory(project_id: str, mem_id: str,
                                user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import delete_memory
    if not delete_memory(mem_id):
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"ok": True}


@router.get("/projects/{project_id}/events")
async def project_list_events(project_id: str, event_type: str | None = None,
                              user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_events
    return {"events": list_events(project_id, event_type)}


@router.post("/projects/{project_id}/run")
async def project_run(project_id: str, body: RunRequest,
                      user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    """Run an intent in the context of a project — logs an event on completion."""
    from solspire.project_store import log_event

    result = _execute_run(body, user)
    log_event(project_id, "workflow_run",
              f"⟐ {result['intent']}: {body.request[:80]}",
              {"status": result["execution"]["status"], "elapsed_ms": result["elapsed_ms"]})
    return result


def _count_by_status(execs: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ex in execs:
        s = ex.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts



# ── W4: Project Weaver (read-only bridge; project access ≠ mutation auth) ─────

class WeaverAnalyzeRequest(BaseModel):
    objective: str
    affected_paths: list[str] | None = None
    symbols: list[str] | None = None


@router.get("/projects/{project_id}/weaver/capabilities")
async def project_weaver_capabilities(project_id: str,
                                      user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.weaver_bridge import project_capabilities
    return project_capabilities()


@router.get("/projects/{project_id}/weaver/context")
async def project_weaver_context_route(project_id: str,
                                       user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_weaver_context
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_weaver_context(p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__))


@router.post("/projects/{project_id}/weaver/analyze")
async def project_weaver_analyze(project_id: str, body: WeaverAnalyzeRequest,
                                 user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_analyze
    from solspire.project_store import log_event
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    pdata = p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
    result = project_analyze(pdata, body.objective, affected_paths=body.affected_paths, symbols=body.symbols)
    try:
        log_event(project_id, "weaver_analyze", f"Weaver analyze: {(body.objective or '')[:80]}",
                  {"executed": False, "execution": "LOCKED", "scope": (result.get("scope") or {}).get("status")})
    except Exception:
        pass
    return result


@router.get("/projects/{project_id}/weaver/validation")
async def project_weaver_validation(project_id: str, scenario: str | None = None,
                                    user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.weaver_bridge import project_validation
    return project_validation(scenario_id=scenario)


@router.get("/projects/{project_id}/weaver/knowledge-summary")
async def project_weaver_knowledge_summary(project_id: str,
                                           user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_memory, list_files, list_repositories, list_tasks, list_events
    mem = list_memory(project_id)
    files = list_files(project_id)
    repos = list_repositories(project_id)
    tasks = list_tasks(project_id)
    events = list_events(project_id)
    return {
        "project_id": project_id,
        "knowledge_os": {
            "memory_items": len(mem),
            "files": len(files),
            "repositories": len(repos),
            "tasks": len(tasks),
            "events": len(events),
        },
        "graph": {
            "status": "NOT_A_SEPARATE_STORE",
            "note": "No second knowledge graph introduced. Use existing project relations via store tables.",
        },
        "embeddings": {
            "status": "NOT_A_SEPARATE_STORE",
            "note": "No second embedding store introduced in W4.",
        },
        "authorization": {
            "PassSpec": "NONE",
            "PatchApproval": "NONE",
            "Execution": "LOCKED",
            "note": "Knowledge summary is read-only project metadata.",
        },
    }


@router.get("/projects/{project_id}/knowledge")
async def project_knowledge_os(project_id: str,
                               user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_knowledge import build_knowledge_summary
    return build_knowledge_summary(project_id)


@router.get("/projects/{project_id}/knowledge/graph")
async def project_knowledge_graph(project_id: str,
                                  user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_knowledge import build_derived_graph
    return build_derived_graph(project_id)


@router.get("/projects/{project_id}/knowledge/embeddings")
async def project_knowledge_embeddings(project_id: str,
                                       user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_knowledge import build_knowledge_summary
    s = build_knowledge_summary(project_id)
    return {"project_id": project_id, "embeddings": s.get("embeddings"), "authorization": s.get("authorization")}


@router.post("/projects/{project_id}/knowledge/search")
async def project_knowledge_search(project_id: str, body: dict[str, Any],
                                   user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_store import list_memory, list_files, list_tasks
    q = str((body or {}).get("q") or "").strip().lower()
    hits = []
    if not q:
        return {"project_id": project_id, "q": q, "hits": [], "note": "empty query"}
    for m in list_memory(project_id) or []:
        if q in f"{m.get('title','')} {m.get('content','')}".lower():
            hits.append({"type": "memory", "id": m.get("id"), "title": m.get("title"), "classification": "SOURCE-BACKED"})
    for f in list_files(project_id) or []:
        if q in str(f.get("name") or "").lower():
            hits.append({"type": "file", "id": f.get("id"), "name": f.get("name"), "classification": "SOURCE-BACKED"})
    for t in list_tasks(project_id) or []:
        if q in f"{t.get('title','')} {t.get('description','')}".lower():
            hits.append({"type": "task", "id": t.get("id"), "title": t.get("title"), "classification": "SOURCE-BACKED"})
    return {
        "project_id": project_id,
        "q": q,
        "hits": hits[:50],
        "note": "Keyword search over project_store. Not semantic vector retrieval.",
        "authorization": {"Execution": "LOCKED"},
    }


class WeaverPassSpecRequest(BaseModel):
    patch: dict[str, Any]
    pass_id: str | None = None
    objective: str | None = None
    allowed_paths: list[str] | None = None
    required_tests: list[str] | None = None


class WeaverApprovalRequest(BaseModel):
    patch: dict[str, Any]
    pass_spec: dict[str, Any]
    approved: bool = True


class WeaverExecuteRequest(BaseModel):
    patch: dict[str, Any]
    pass_spec: dict[str, Any]
    approval: dict[str, Any]
    run_k3: bool = False


class WeaverReadinessRequest(BaseModel):
    patch: dict[str, Any] | None = None
    pass_spec: dict[str, Any] | None = None
    approval: dict[str, Any] | None = None


@router.post("/projects/{project_id}/weaver/execution/readiness")
async def project_weaver_execution_readiness(project_id: str, body: WeaverReadinessRequest,
                                             user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_execution_readiness
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    pdata = p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
    return project_execution_readiness(pdata, body.patch, pass_spec=body.pass_spec, approval=body.approval)


@router.post("/projects/{project_id}/weaver/execution/pass-spec")
async def project_weaver_bind_pass_spec(project_id: str, body: WeaverPassSpecRequest,
                                        user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_bind_pass_spec
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    pdata = p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
    return project_bind_pass_spec(
        pdata, body.patch,
        pass_id=body.pass_id,
        objective=body.objective,
        allowed_paths=body.allowed_paths,
        required_tests=body.required_tests,
    )


@router.post("/projects/{project_id}/weaver/execution/approval")
async def project_weaver_bind_approval(project_id: str, body: WeaverApprovalRequest,
                                       user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_bind_patch_approval
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    pdata = p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
    return project_bind_patch_approval(pdata, body.patch, body.pass_spec, approved=body.approved)


@router.post("/projects/{project_id}/weaver/execution/execute")
async def project_weaver_execute(project_id: str, body: WeaverExecuteRequest,
                                 user: dict = Depends(require_project_owner)) -> dict[str, Any]:
    from solspire.project_manager import get_project_manager
    from solspire.weaver_bridge import project_execute_governed
    p = get_project_manager().load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    pdata = p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
    return project_execute_governed(pdata, body.patch, body.pass_spec, body.approval, run_k3=bool(body.run_k3))

__all__ = ["router"]
