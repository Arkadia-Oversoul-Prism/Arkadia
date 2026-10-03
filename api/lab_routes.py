"""Engineering Lab API surface (EL-01 → EL-10).

Mounted through the already-composed ``api.nodes`` router (which is itself
mounted in ``api/main.py``), so this adds **no** lines to the 2600-line
``api/main.py`` budget and introduces no second router hierarchy.

Every endpoint is authenticated via ``api.auth.require_auth`` and scoped to the
verified Firebase uid. None of these endpoints can merge, deploy, or
self-authorize; consequential transitions remain human-only.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_auth
from lab import build_overview
from lab.engineering_lab.adapters import describe_integrations
from lab.engineering_lab.android import android_capability_report, android_session_projection
from lab.engineering_lab.artifacts import canvas_view
from lab.engineering_lab.automations import (
    AutomationTrigger,
    assert_automation_transition,
    grammar_view,
    make_automation,
)
from lab.engineering_lab.contracts import BoundaryViolation
from lab.engineering_lab.gateway import describe_gateway
from lab.engineering_lab.runtime import (
    CANONICAL_LOOP,
    BoundedOperation,
    BoundedTask,
    get_runtime,
)
from lab.engineering_lab.sandbox import SandboxPolicy
from lab.engineering_lab.store import get_store
from lab.engineering_lab.voice import resolve_voice_command, voice_boundary_report

router = APIRouter(prefix="/api/lab", tags=["Engineering Lab"], dependencies=[Depends(require_auth)])


# -- EL-01: read-only substrate overview (existing) ---------------------------

@router.get("/overview")
async def lab_overview() -> dict:
    """Deterministic, authenticated, read-only Engineering Lab snapshot."""
    return build_overview(".")


# -- EL-10: operational surface ----------------------------------------------

@router.get("/engineering/overview")
async def engineering_overview(user: dict = Depends(require_auth)) -> dict:
    """The C09 operational surface: what is running, who, where, and what needs a human."""
    uid = user["uid"]
    runtime = get_runtime()
    overview = runtime.overview(uid)
    overview["loop"] = list(CANONICAL_LOOP)
    overview["integrations"] = describe_integrations()["adapters"]
    overview["android"] = android_capability_report()
    overview["voice"] = voice_boundary_report()
    overview["automation_grammar"] = grammar_view()
    return overview


@router.get("/engineering/loop")
async def engineering_loop() -> dict:
    """The canonical C09 loop stages (EL-10)."""
    return {"loop": list(CANONICAL_LOOP)}


# -- EL-09: agents -----------------------------------------------------------

class AgentCreate(BaseModel):
    role: str
    display_name: str = ""
    capabilities: list[str] | None = None
    write_allowed: bool = False
    model_ref: str | None = None


@router.post("/engineering/agents")
async def create_agent(body: AgentCreate, user: dict = Depends(require_auth)) -> dict:
    try:
        return get_runtime().register_agent(
            subject_ref=user["uid"],
            role=body.role,
            display_name=body.display_name,
            capabilities=tuple(body.capabilities) if body.capabilities else None,
            write_allowed=body.write_allowed,
            model_ref=body.model_ref,
        )
    except (ValueError, BoundaryViolation) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/engineering/agents")
async def list_agents(user: dict = Depends(require_auth)) -> dict:
    return {"agents": get_store().list_agents(user["uid"])}


# -- EL-01 / EL-02: sessions -------------------------------------------------

class SessionCreate(BaseModel):
    workspace_ref: str
    agent_id: str
    objective: str = ""
    repository_ref: str | None = None
    project_ref: str | None = None
    authorization_ref: str | None = None


@router.post("/engineering/sessions")
async def open_session(body: SessionCreate, user: dict = Depends(require_auth)) -> dict:
    if body.project_ref:
        from solspire.project_manager import get_project_manager
        from solspire.workspace_manager import get_workspace_manager
        try:
            project = get_project_manager().load(body.project_ref)
        except KeyError:
            raise HTTPException(status_code=404, detail="Project not found")
        if (project.owner_uid or "").strip() != user["uid"]:
            raise HTTPException(status_code=404, detail="Project not found")
        workspace = get_workspace_manager().get_for_subject(user["uid"])
        if workspace is None or workspace.id != body.workspace_ref:
            raise HTTPException(status_code=409, detail="Canonical workspace binding mismatch")
    try:
        return get_runtime().open_session(
            subject_ref=user["uid"],
            workspace_ref=body.workspace_ref,
            agent_id=body.agent_id,
            objective=body.objective,
            repository_ref=body.repository_ref,
            project_ref=body.project_ref,
            authorization_ref=body.authorization_ref,
        )
    except (ValueError, BoundaryViolation, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/engineering/sessions")
async def list_sessions(user: dict = Depends(require_auth)) -> dict:
    return {"sessions": get_store().list_sessions(user["uid"])}


@router.get("/engineering/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(require_auth)) -> dict:
    try:
        return get_runtime().session_view(session_id, user["uid"])
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")


class AuthorizationCreate(BaseModel):
    operations_allowed: list[str] = ["read", "test"]
    duration_minutes: int = 60


@router.post("/engineering/sessions/{session_id}/authorize")
async def authorize_session(
    session_id: str, body: AuthorizationCreate, user: dict = Depends(require_auth)
) -> dict:
    """Record a human-originated authorization for this session's scope."""
    try:
        runtime = get_runtime()
        session = runtime.get_session(session_id, user["uid"])
        auth = runtime.record_authorization(
            subject_ref=user["uid"],
            scope_ref=session_id,
            operations_allowed=tuple(body.operations_allowed),
            duration_minutes=body.duration_minutes,
        )
        get_store().attach_authorization(session_id, user["uid"], auth["authorization_id"])
        if session["state"] == "PROPOSED":
            runtime.transition(session_id, user["uid"], "AUTHORIZED")
        return {"authorization": auth, "session": runtime.get_session(session_id, user["uid"])}
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))


class ExecuteBody(BaseModel):
    objective: str
    operations: list[dict] = []
    acceptance: list[str] = []
    requires_write: bool = False
    sandbox_root: str | None = None
    command_allowlist: list[str] = ["git"]


@router.post("/engineering/sessions/{session_id}/execute")
async def execute_bounded(
    session_id: str, body: ExecuteBody, user: dict = Depends(require_auth)
) -> dict:
    """Execute one bounded Move and stop at the human review boundary."""
    try:
        task = BoundedTask(
            objective=body.objective,
            operations=tuple(
                BoundedOperation(
                    kind=op.get("kind", "read"),
                    target=op.get("target", ""),
                    argv=tuple(op.get("argv", [])),
                    content=op.get("content", ""),
                    description=op.get("description", ""),
                )
                for op in body.operations
            ),
            acceptance=tuple(body.acceptance),
            requires_write=body.requires_write,
        )
        session = get_runtime().get_session(session_id, user["uid"])
        policy = None
        if session.get("project_ref"):
            if body.requires_write or body.sandbox_root:
                raise HTTPException(status_code=409, detail="Project canvas v0.1 is read-only; its sandbox root is server-managed")
            if any(operation.kind not in {"read", "list"} for operation in task.operations):
                raise HTTPException(status_code=409, detail="Project canvas v0.1 direct operations are read/list only; use the authorized Weaver loop for read-only Git observation")
            policy = _project_canvas_policy(session, user["uid"])
        elif body.sandbox_root:
            policy = SandboxPolicy(
                root=body.sandbox_root,
                write_allowed=body.requires_write,
                command_allowlist=tuple(body.command_allowlist),
            )
        result = get_runtime().execute_bounded_task(
            subject_ref=user["uid"], session_id=session_id, task=task, sandbox_policy=policy
        )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    except (ValueError, BoundaryViolation) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if policy is not None and getattr(policy, "containerized", False):
            import shutil
            shutil.rmtree(os.path.dirname(policy.root), ignore_errors=True)


class TransitionBody(BaseModel):
    target: str


@router.post("/engineering/sessions/{session_id}/transition")
async def transition_session(
    session_id: str, body: TransitionBody, user: dict = Depends(require_auth)
) -> dict:
    try:
        return get_runtime().transition(session_id, user["uid"], body.target)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))


# -- EL-04: artifacts / canvas -----------------------------------------------

@router.get("/engineering/artifacts")
async def list_artifacts(
    session_id: str | None = None, user: dict = Depends(require_auth)
) -> dict:
    artifacts = get_store().list_artifacts(user["uid"], session_id)
    return {"artifacts": artifacts, "count": len(artifacts)}


@router.get("/engineering/canvas/{artifact_id}")
async def get_canvas(artifact_id: str, user: dict = Depends(require_auth)) -> dict:
    artifact = get_store().get_artifact(artifact_id, user["uid"])
    if artifact is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    return canvas_view(artifact)


# -- EL-03: native automations -----------------------------------------------

class AutomationCreate(BaseModel):
    name: str
    trigger_kind: str
    trigger_detail: str = ""
    schedule: str | None = None
    event: str | None = None
    agent_role: str = "WEAVER"
    objective: str = ""
    tools: list[str] = []
    sandbox_write_allowed: bool = False


@router.post("/engineering/automations")
async def create_automation(body: AutomationCreate, user: dict = Depends(require_auth)) -> dict:
    try:
        automation = make_automation(
            subject_ref=user["uid"],
            name=body.name,
            trigger=AutomationTrigger(
                kind=body.trigger_kind,
                detail=body.trigger_detail,
                schedule=body.schedule,
                event=body.event,
            ),
            agent_role=body.agent_role,
            objective=body.objective,
            tools=tuple(body.tools),
            sandbox_write_allowed=body.sandbox_write_allowed,
        )
        return get_store().create_automation(automation.to_dict(), user["uid"])
    except (ValueError, BoundaryViolation) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/engineering/automations")
async def list_automations(user: dict = Depends(require_auth)) -> dict:
    return {
        "automations": get_store().list_automations(user["uid"]),
        "grammar": grammar_view(),
    }


class AutomationStateBody(BaseModel):
    state: str


@router.post("/engineering/automations/{automation_id}/state")
async def set_automation_state(
    automation_id: str, body: AutomationStateBody, user: dict = Depends(require_auth)
) -> dict:
    store = get_store()
    automation = store.get_automation(automation_id, user["uid"])
    if automation is None:
        raise HTTPException(status_code=404, detail="automation not found")
    try:
        assert_automation_transition(automation["state"], body.state)
        return store.set_automation_state(automation_id, user["uid"], body.state)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))


# -- EL-08: model gateway ----------------------------------------------------

@router.get("/engineering/gateway")
async def model_gateway() -> dict:
    return describe_gateway()


# -- EL-05: external integration status --------------------------------------

@router.get("/engineering/integrations")
async def integrations() -> dict:
    return describe_integrations()


# -- EL-06: Android control plane --------------------------------------------

@router.get("/engineering/android")
async def android_control() -> dict:
    return android_capability_report()


@router.get("/engineering/android/session/{session_id}")
async def android_session(session_id: str, user: dict = Depends(require_auth)) -> dict:
    try:
        return android_session_projection(get_runtime().session_view(session_id, user["uid"]))
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")


# -- EL-07: voice adapter ----------------------------------------------------

class VoiceResolveBody(BaseModel):
    transcript: str
    identity_present: bool = True
    workspace_present: bool = True
    authorization_present: bool = False


@router.get("/engineering/voice")
async def voice_boundary() -> dict:
    return voice_boundary_report()


@router.post("/engineering/voice/resolve")
async def voice_resolve(body: VoiceResolveBody, user: dict = Depends(require_auth)) -> dict:
    return resolve_voice_command(
        body.transcript,
        identity_present=body.identity_present,
        workspace_present=body.workspace_present,
        authorization_present=body.authorization_present,
    ).to_dict()


# -- EL-10: PR state (read-only, GitHub remains repository authority) --------

@router.get("/engineering/pr/{number}")
async def pr_state(number: int) -> dict:
    """Read-only PR state. Truthful about unavailability; never fabricates."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("ARKADIA_REPO", "Arkadia-Oversoul-Prism/Arkadia")
    if not token:
        return {"state": "UNAVAILABLE", "detail": "no GITHUB_TOKEN in environment", "pr": None}
    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json

            data = json.loads(resp.read().decode())
        return {
            "state": "AVAILABLE",
            "pr": {
                "number": data.get("number"),
                "title": data.get("title"),
                "state": data.get("state"),
                "draft": data.get("draft"),
                "mergeable_state": data.get("mergeable_state"),
                "html_url": data.get("html_url"),
                "head": (data.get("head") or {}).get("sha"),
                "base": (data.get("base") or {}).get("ref"),
            },
        }
    except urllib.error.HTTPError as exc:
        return {"state": "UNAVAILABLE", "detail": f"http {exc.code}", "pr": None}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"state": "UNAVAILABLE", "detail": str(exc), "pr": None}


def _project_canvas_policy(session: dict, subject_uid: str) -> SandboxPolicy:
    """Resolve a project-owned snapshot; never accept a client-supplied root."""
    project_id = str(session.get("project_ref") or "")
    if not project_id:
        raise HTTPException(status_code=400, detail="Project binding missing")
    from solspire.project_manager import get_project_manager
    from solspire.project_execution_service import (
        assert_container_runtime_ready, create_disposable_workspace,
    )
    try:
        project = get_project_manager().load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    if (project.owner_uid or "").strip() != subject_uid:
        raise HTTPException(status_code=404, detail="Project not found")
    image = os.environ.get("SOLSPIRE_AGENT_IMAGE", "")
    runtime_name = os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker")
    try:
        assert_container_runtime_ready(image=image, runtime=runtime_name)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"isolated project runtime unavailable: {exc}") from exc
    snapshot = create_disposable_workspace(subject_uid, project_id)
    return SandboxPolicy(
        root=snapshot["root"],
        # Writes may create a candidate only in this disposable copy. The runtime
        # still intersects this policy with the human authorization envelope.
        write_allowed=True,
        allowed_paths=tuple(snapshot["seeded_files"]),
        forbidden_paths=(".git",),
        allow_network=False,
        command_allowlist=("git", "echo", "pwd", "true", "false"),
        enforce_git_read_only=True,
        enforce_command_grammar=True,
        containerized=True,
        container_image=os.environ.get("SOLSPIRE_AGENT_IMAGE"),
        container_runtime=os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker"),
        canonical_base_digest=snapshot["canonical_base_digest"],
    )


# -- EL-01: native read-only model/tool loop ---------------------------------

class AgentLoopBody(BaseModel):
    objective: str
    provider: str = "ollama"
    model: str | None = None
    max_turns: int = Field(default=6, ge=1, le=8)


@router.post("/engineering/sessions/{session_id}/run-agent")
async def run_agent_loop(
    session_id: str, body: AgentLoopBody, user: dict = Depends(require_auth)
) -> dict:
    """Run the native agent loop inside an already human-authorized session.

    The runtime intersects role capabilities, agent tool envelope, and the
    linked human authorization. L1 terminal grammar is forced read-only. This
    route cannot edit the repository, merge, or deploy.
    """
    if not body.objective.strip():
        raise HTTPException(status_code=400, detail="objective is required")
    if body.max_turns < 1 or body.max_turns > 8:
        raise HTTPException(status_code=400, detail="max_turns must be between 1 and 8")
    policy = None
    try:
        runtime = get_runtime()
        session = runtime.get_session(session_id, user["uid"])
        policy = _project_canvas_policy(session, user["uid"]) if session.get("project_ref") else None
        result = runtime.execute_agent_loop(
            subject_ref=user["uid"],
            session_id=session_id,
            objective=body.objective.strip(),
            provider=body.provider,
            model=body.model,
            sandbox_policy=policy,
            max_turns=body.max_turns,
        )
        if policy is not None and session.get("project_ref"):
            from solspire.project_execution_service import collect_agent_candidate_patch
            turns = result.get("turns", []) if isinstance(result, dict) else []
            candidate = collect_agent_candidate_patch(
                project_id=str(session["project_ref"]),
                base_digest=str(policy.canonical_base_digest or ""),
                turns=turns, allowed_paths=policy.allowed_paths,
            )
            if isinstance(result, dict):
                result["candidate_patch"] = candidate
            else:
                result = {"execution": result, "candidate_patch": candidate}
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if "policy" in locals() and policy is not None and getattr(policy, "containerized", False):
            import shutil
            shutil.rmtree(os.path.dirname(policy.root), ignore_errors=True)
