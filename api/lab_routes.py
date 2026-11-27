"""Engineering Lab API surface (EL-01 → EL-10).

Mounted through the already-composed ``api.nodes`` router (which is itself
mounted in ``api/main.py``), so this adds **no** lines to the 2600-line
``api/main.py`` budget and introduces no second router hierarchy.

Every endpoint is authenticated via ``api.auth.require_auth`` and scoped to the
verified Firebase uid. None of these endpoints can merge, deploy, or
self-authorize; consequential transitions remain human-only.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import replace
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import mint_natlas_tester_token, require_auth
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
from lab.engineering_lab.contracts import BoundaryViolation, EvidenceRecord, utc_now
from lab.engineering_lab.gateway import ModelUnavailable, describe_gateway, get_gateway
from lab.engineering_lab.events import get_event_stream
from lab.engineering_lab.repository import observe_repository
from lab.engineering_lab.runtime import (
    CANONICAL_LOOP,
    BoundedOperation,
    BoundedTask,
    get_runtime,
    workspace_root,
)
from lab.engineering_lab.sandbox import SandboxPolicy
from lab.engineering_lab.store import get_store
from lab.engineering_lab.voice import resolve_voice_command, voice_boundary_report
from lab.engineering_lab.github_app import (
    GitHubAppWorker,
    GitHubUnavailable,
    HttpGitHubReader,
    RateLimited,
    WebhookRejected,
    WorkerUnavailable,
    verify_webhook_delivery,
)
from lab.engineering_lab.pr_review import (
    APPROVE,
    GENERATE_FINDINGS,
    PUBLISH_COMMENT,
    REQUEST_CHANGES,
    SCHEMA as PR_REVIEW_SCHEMA,
    PrReviewRequest,
    RetryPolicy,
    ReviewPolicy,
    StaleHead,
    approval_scope,
    assert_action_permitted,
    assert_grant_matches,
    assert_head_current,
    assert_independent,
    attach_evidence,
    build_evidence,
    capability_manifest,
    review_pull_request,
    rollout_state,
)

_PUBLIC_NATLAS_PATHS = {
    "/api/lab/engineering/n-atlas/catalog",
    "/api/lab/engineering/n-atlas/test-session",
}

#: The GitHub App webhook receiver. It is not an account-authenticated route:
#: its authentication is the HMAC signature over the raw body plus the
#: installation/repository binding, both verified inside the handler. A delivery
#: that fails verification is refused before any state is written.
_PUBLIC_WEBHOOK_PATHS = {"/api/lab/engineering/pr-review/webhook"}


async def require_lab_auth(request: Request) -> None:
    """Keep the Lab authenticated by default, with narrow declared exemptions."""
    if request.url.path in _PUBLIC_NATLAS_PATHS:
        return None
    if request.url.path in _PUBLIC_WEBHOOK_PATHS:
        return None
    await require_auth(request)


router = APIRouter(prefix="/api/lab", tags=["Engineering Lab"], dependencies=[Depends(require_lab_auth)])


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


# -- AEAS-01 P0.3: read-only repository & change inspection -------------------

@router.get("/engineering/repository")
async def engineering_repository(user: dict = Depends(require_auth)) -> dict:
    """Observe branch, source revision, working-tree changes, and the real diff.

    This is the Lab's inspectable-engineering-output reading: what the tree
    actually contains right now, observed through the bounded read-only git
    boundary. It observes the same workspace bounded execution runs against
    (``workspace_root()``), never a client-supplied path, and performs no
    repository mutation of any kind — the response's ``boundary`` field states
    the envelope it stayed inside.
    """
    return observe_repository(workspace_root())


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
        runtime = get_runtime()
        session = runtime.get_session(session_id, user["uid"])
        policy = None
        if session.get("project_ref"):
            _require_session_scoped_project_authorization(runtime, session, session_id, user["uid"])
            if body.requires_write or body.sandbox_root:
                raise HTTPException(status_code=409, detail="Project canvas v0.1 is read-only; its sandbox root is server-managed")
            if any(
                operation.kind not in {"read", "list", "test"}
                for operation in task.operations
            ):
                raise HTTPException(status_code=409, detail="Project canvas v0.1 direct operations are read/list/test only; 'test' runs the allowlisted suite inside the container boundary and 'run' stays with the authorized Weaver loop for read-only Git observation")
            policy = _project_canvas_policy(session, user["uid"])
        elif body.sandbox_root:
            # A caller-selected filesystem root is never honoured. The sandbox
            # root is server-managed: a session without a project binding runs
            # against the server's own workspace, and a write still requires a
            # usable session-scoped authorization naming 'write'.
            raise HTTPException(
                status_code=409,
                detail=(
                    "sandbox_root is server-managed; a client-supplied root is "
                    "refused. Bind the session to a project for a project-owned "
                    "snapshot."
                ),
            )
        result = runtime.execute_bounded_task(
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


class NAtlasRunBody(BaseModel):
    session_id: str
    prompt: str = Field(min_length=1, max_length=12000)
    model: str | None = None


@router.post("/engineering/n-atlas/test-session")
async def n_atlas_test_session() -> dict:
    """Create a minimal, anonymous external tester session for N-ATLaS only.

    No Arkadia account is created and no general application authorization is
    issued. The returned capability is a 30-minute, run-only credential bound
    to this exact session.
    """
    from solspire.workspace_manager import get_workspace_manager

    uid = f"natlas-tester-{uuid.uuid4().hex[:16]}"
    workspace = get_workspace_manager().get_or_create(
        uid, display_name="N-ATLaS External Test Workspace"
    )
    store = get_store()
    runtime = get_runtime()
    agent = runtime.register_agent(
        subject_ref=uid,
        role="BUILDER",
        display_name="N-ATLaS External Tester",
        capabilities=("READ", "TEST"),
        write_allowed=False,
        model_ref="N-ATLaS",
    )

    session = runtime.open_session(
        subject_ref=uid,
        workspace_ref=workspace.id,
        agent_id=agent["agent_id"],
        objective="External N-ATLaS developer test",
    )
    authorization = runtime.record_authorization(
        subject_ref=uid,
        scope_ref=session["session_id"],
        operations_allowed=("read", "test"),
        duration_minutes=30,
    )
    store.attach_authorization(
        session["session_id"], uid, authorization["authorization_id"]
    )
    session = runtime.transition(session["session_id"], uid, "AUTHORIZED")
    descriptor = get_gateway().describe("n_atlas")
    if descriptor.status != "AVAILABLE":
        raise HTTPException(
            status_code=503,
            detail={"state": descriptor.status, "detail": descriptor.detail},
        )

    tester_token = mint_natlas_tester_token(
        session_id=session["session_id"], subject_ref=uid, ttl_seconds=30 * 60
    )
    return {
        "session_id": session["session_id"],
        "state": session["state"],
        "model": descriptor.model,
        "expires_in_minutes": 30,
        "tester_token": tester_token,
        "scope": ["n_atlas:run"],
    }


@router.get("/engineering/n-atlas/catalog")
async def n_atlas_catalog() -> dict:
    """Truthful N-ATLAS integration status and capability descriptor."""
    gateway = get_gateway()
    descriptor = gateway.describe("n_atlas")
    return {
        "provider": "n_atlas",
        "descriptor": descriptor.to_dict(),
        "golden_workflow": ["RUN", "INSPECT", "EVALUATE", "EVIDENCE", "VERIFY"],
        "live_boundary": "hosted access remains unverified unless the configured endpoint is authorized and reachable",
    }


@router.post("/engineering/n-atlas/run")
async def n_atlas_run(body: NAtlasRunBody, user: dict = Depends(require_auth)) -> dict:
    """Run one governed N-ATLAS interaction and record evidence."""
    runtime = get_runtime()
    try:
        session = runtime.get_session(body.session_id, user["uid"])
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    if session["state"] not in ("AUTHORIZED", "QUEUED"):
        raise HTTPException(status_code=409, detail=f"session must be AUTHORIZED or QUEUED (currently {session['state']})")

    # Gate 2 — this route drives a model call directly, so it must pass the
    # same dispatch gate as every other execution path: a usable, session-scoped
    # human grant that names 'run', plus the executive delegation contract. A
    # session-state check alone would let a revoked delegation keep executing.
    try:
        runtime.assert_session_dispatchable(session, user["uid"], "run")
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    gateway = get_gateway()
    descriptor = gateway.describe("n_atlas")
    if descriptor.status != "AVAILABLE":
        raise HTTPException(status_code=503, detail={"state": descriptor.status, "detail": descriptor.detail, "provider": "n_atlas"})

    run_id = f"RUN-{uuid.uuid4().hex[:12]}"
    from lab.engineering_lab.models import AgentRun
    run = AgentRun(
        run_id=run_id,
        session_id=body.session_id,
        agent_id=session["agent_id"],
        state="RUNNING",
        objective="N-ATLAS developer-lab golden workflow",
        subject_ref=user["uid"],
        plan={"provider": "n_atlas", "model": body.model or descriptor.model},
    )
    get_store().create_run(run)
    get_event_stream().emit(session_id=body.session_id, run_id=run_id, event_type="RUN_STARTED",
                            payload={"provider": "n_atlas", "model": body.model or descriptor.model})

    prompt_hash = hashlib.sha256(body.prompt.encode("utf-8")).hexdigest()
    try:
        response = gateway.generate(
            provider="n_atlas",
            model=body.model or descriptor.model,
            messages=[{"role": "user", "content": body.prompt}],
        )
    except ModelUnavailable as exc:
        get_store().update_run(run_id, user["uid"], state="BLOCKED", result_state="BLOCKED")
        get_event_stream().emit(session_id=body.session_id, run_id=run_id, event_type="BLOCKED",
                                payload={"provider": "n_atlas", "reason": str(exc)})
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response_hash = hashlib.sha256(response.text.encode("utf-8")).hexdigest()
    evaluation = {
        "name": "non_empty_response",
        "passed": bool(response.text.strip()),
        "rules": ["response must contain non-whitespace text"],
    }
    result_state = "IMPLEMENTED" if evaluation["passed"] else "BLOCKED"

    get_event_stream().emit(
        session_id=body.session_id, run_id=run_id, event_type="MODEL_TURN",
        payload={"provider": response.provider, "model": response.model,
                 "prompt_sha256": prompt_hash, "response_sha256": response_hash,
                 "finish_reason": response.finish_reason},
    )

    evidence = EvidenceRecord(
        evidence_id=f"EVD-{uuid.uuid4().hex[:12]}",
        subject_ref=user["uid"],
        workspace_ref=session["workspace_ref"],
        run_ref=run_id,
        state=result_state,
        summary="N-ATLAS golden workflow execution",
        detail={
            "provider": response.provider,
            "model": response.model,
            "prompt_sha256": prompt_hash,
            "response_sha256": response_hash,
            "evaluation": evaluation,
            "usage": response.usage,
            "integration": f"{os.environ.get('N_ATLAS_PROTOCOL', 'openai_compatible')} N-ATLaS runtime adapter",
        },
        timestamp_utc=utc_now(),
        provenance={"session_id": body.session_id,
                    "authorization_ref": session.get("authorization_ref"),
                    "provider_status": descriptor.status},
    )
    get_store().save_evidence(evidence)
    get_store().update_run(run_id, user["uid"], state="VERIFYING",
                           result_state=result_state, evidence_refs=(evidence.evidence_id,))
    get_event_stream().emit(session_id=body.session_id, run_id=run_id, event_type="EVIDENCE_RECORDED",
                            payload={"evidence_id": evidence.evidence_id, "state": result_state})
    get_event_stream().emit(session_id=body.session_id, run_id=run_id, event_type="RUN_FINISHED",
                            payload={"state": "VERIFYING", "result_state": result_state})

    return {
        "run_id": run_id,
        "provider": response.provider,
        "model": response.model,
        "response": response.text,
        "finish_reason": response.finish_reason,
        "usage": response.usage,
        "evaluation": evaluation,
        "evidence": evidence.to_dict(),
        "reproduction": {"provider": "n_atlas", "model": response.model, "prompt_sha256": prompt_hash, "protocol": os.environ.get("N_ATLAS_PROTOCOL", "openai_compatible")},
    }


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

def _read_json_url(req: urllib.request.Request, timeout: float) -> dict:
    """Blocking GET. Callers must offload it — the server runs one event loop."""
    import json

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


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
        data = await asyncio.to_thread(_read_json_url, req, 10)
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


def _require_session_scoped_project_authorization(
    runtime, session: dict, session_id: str, subject_uid: str
) -> None:
    """Project execution may use only an authorization bound to this exact session."""
    if not session.get("project_ref"):
        return
    authorization_ref = session.get("authorization_ref")
    if not authorization_ref:
        raise HTTPException(status_code=403, detail="Project execution requires explicit session-scoped human authorization")
    authorization = runtime.get_authorization(authorization_ref, subject_uid)
    if not authorization or authorization.get("scope_ref") != session_id:
        raise HTTPException(status_code=403, detail="Authorization scope does not match this project session")


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
        # Candidate proposals never write to the workspace; the runtime still
        # intersects this capability with explicit human authorization.
        write_allowed=False,
        candidate_proposals_allowed=True,
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
        if session.get("project_ref"):
            _require_session_scoped_project_authorization(runtime, session, session_id, user["uid"])
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


# -- ARKADIA-CHIEF-PR-REVIEW-001: governed PR review --------------------------
#
# A capability of the existing canonical Chief identity (ARKADIA-CHIEF-001),
# executed through this Lab boundary. It reuses the Lab's evidence
# (``el_evidence``), its human grant store (``el_authorizations``) and its
# durable job ledger (``el_pr_review_jobs``). It creates no second identity,
# conversation, memory store, workspace, authorization engine or evidence path.
#
# Rollout: read-only shadow review. Every GitHub-writing action has its own gate
# and refuses unless the active policy has *reached* that stage AND carries the
# named flag AND a human grant binds the exact repository/PR/head/action. Merge
# is refused unconditionally — a GREEN review is never merge authorization.

#: Owner of webhook-enqueued ingress records. It is not an identity: it is the
#: installation-scoped subject an account-unauthenticated delivery is recorded
#: under. The review that runs from such a job is attributed to the *operator's*
#: verified principal, never to this string.
PR_REVIEW_SYSTEM_SUBJECT = "service:chief-pr-review"


class PrReviewRequestBody(BaseModel):
    repository: str = Field(min_length=3)
    pr_number: int = Field(gt=0)
    base_sha: str = Field(min_length=7)
    head_sha: str = Field(min_length=7)
    installation_id: int | None = None
    event_id: str | None = None
    action: str = GENERATE_FINDINGS


class PrReviewGrantBody(BaseModel):
    """Record a human grant for one GitHub-writing action on one exact tuple."""

    action: str
    duration_minutes: int = Field(default=30, ge=1, le=120)


class PrReviewPublishBody(BaseModel):
    action: str
    authorization_ref: str = Field(min_length=3)


def _review_retry_policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=int(os.environ.get("ARKADIA_PR_REVIEW_MAX_ATTEMPTS", "3") or 3),
        base_backoff_seconds=int(os.environ.get("ARKADIA_PR_REVIEW_BACKOFF_SECONDS", "15") or 15),
    )


def _review_replay_window_seconds() -> int:
    return int(os.environ.get("ARKADIA_PR_REVIEW_REPLAY_WINDOW_SECONDS", "600") or 600)


def _review_policy() -> ReviewPolicy:
    """Resolve the active policy. The worker's allowlist is the default one."""
    policy = ReviewPolicy.from_env()
    if not policy.repositories:
        policy = replace(policy, repositories=GitHubAppWorker.from_env().repositories)
    return policy


def _canonical_path_policy():
    """The canonical mutation-boundary policy, injected rather than reimplemented.

    ``scripts.cp10_mutation_boundary_policy`` is the single source of the
    repository's path-admission decision — the same module the CP10 gate
    executes. The Lab consumes it; it does not carry a second copy.
    """
    from scripts.cp10_mutation_boundary_policy import evaluate_changed_paths

    def judge(paths):
        return evaluate_changed_paths(list(paths))

    return judge


def _review_reader(worker: GitHubAppWorker):
    return HttpGitHubReader(worker)


def _count_states(jobs: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        state = str(job.get("state") or "UNKNOWN")
        counts[state] = counts.get(state, 0) + 1
    return counts


def _job_view(job: dict) -> dict:
    return {
        "job_id": job.get("job_id"),
        "state": job.get("state"),
        "repository": job.get("repository_ref"),
        "pr_number": job.get("pr_number"),
        "base_sha": job.get("base_sha"),
        "head_sha": job.get("head_sha"),
        "action": job.get("action"),
        "attempts": job.get("attempts"),
        "delivery_id": job.get("delivery_id"),
        "event_id": job.get("event_id"),
        "deduplicated": job.get("deduplicated"),
        "failure_reason": job.get("failure_reason"),
        "retry_after_seconds": job.get("retry_after_seconds"),
        "next_attempt_at": job.get("next_attempt_at"),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "result": job.get("result"),
        "markdown": job.get("markdown"),
    }


def _load_review_job(job_id: str, subject_uid: str) -> dict:
    """Load a job the caller may act on.

    Owner-scoped, with one declared exception: an ingress job recorded under the
    capability's system subject is an installation-scoped record on an
    allowlisted repository, carries no user data, and may be run by any
    authenticated operator — the run is attributed to that operator.
    """
    store = get_store()
    job = store.get_pr_review_job(job_id, subject_uid)
    if job is None:
        job = store.get_pr_review_job(job_id, PR_REVIEW_SYSTEM_SUBJECT)
    if job is None:
        raise HTTPException(status_code=404, detail="review job not found")
    return job


def _execute_review_job(
    job: dict,
    *,
    principal: str,
    subject_ref: str,
    worker: GitHubAppWorker,
    policy: ReviewPolicy,
) -> dict:
    """Run one review and persist its outcome. Shared by request and run paths."""
    store = get_store()
    retry = _review_retry_policy()
    attempts = int(job.get("attempts") or 0) + 1
    store.update_pr_review_job(
        job["job_id"], job["subject_ref"], state="RUNNING", attempts=attempts
    )

    request = PrReviewRequest(
        subject_ref=subject_ref,
        principal=principal,
        repository=str(job["repository_ref"]),
        pr_number=int(job["pr_number"]),
        base_sha=str(job.get("base_sha") or ""),
        head_sha=str(job["head_sha"]),
        installation_id=job.get("installation_id"),
        event_id=str(job.get("event_id") or ""),
        requested_action=str(job.get("action") or GENERATE_FINDINGS),
        job_id=str(job["job_id"]),
        work_event_ref=job.get("work_event_ref"),
    )

    try:
        result = review_pull_request(
            request,
            reader=_review_reader(worker),
            policy=policy,
            worker=worker,
            path_policy=_canonical_path_policy(),
        )
    except RateLimited as exc:
        if retry.should_retry(attempts):
            updated = store.update_pr_review_job(
                job["job_id"],
                job["subject_ref"],
                state="RETRY_WAIT",
                attempts=attempts,
                retry_after_seconds=exc.retry_after_seconds,
                next_attempt_at=str(time.time() + exc.retry_after_seconds),
                failure_reason=str(exc),
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "reason": str(exc),
                    "retry_after_seconds": exc.retry_after_seconds,
                    "attempts": attempts,
                    "state": "RETRY_WAIT",
                    "job": _job_view(updated or job),
                },
            ) from exc
        updated = store.update_pr_review_job(
            job["job_id"],
            job["subject_ref"],
            state="DEAD_LETTER",
            attempts=attempts,
            failure_reason=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail={
                "reason": str(exc),
                "state": "DEAD_LETTER",
                "attempts": attempts,
                "job": _job_view(updated or job),
            },
        ) from exc
    except (WorkerUnavailable, GitHubUnavailable, BoundaryViolation) as exc:
        # Every one of these is a fail-closed refusal: an unverified worker, an
        # unreadable repository, or a boundary violation. The job is dead-lettered
        # with its reason rather than retried into a fabricated result.
        updated = store.update_pr_review_job(
            job["job_id"],
            job["subject_ref"],
            state="DEAD_LETTER",
            attempts=attempts,
            failure_reason=str(exc),
        )
        status = 503 if isinstance(exc, WorkerUnavailable) else 409
        raise HTTPException(
            status_code=status,
            detail={
                "reason": str(exc),
                "state": "DEAD_LETTER",
                "job": _job_view(updated or job),
            },
        ) from exc

    evidence = build_evidence(
        result, workspace_ref=str(job.get("workspace_ref") or "engineering-lab")
    )
    saved = store.save_evidence(evidence)
    result = attach_evidence(result, saved["evidence_id"])
    payload = result.to_dict()
    markdown = result.to_markdown()
    updated = store.update_pr_review_job(
        job["job_id"],
        job["subject_ref"],
        state="COMPLETED",
        attempts=attempts,
        result=payload,
        markdown=markdown,
        evidence_ref=saved["evidence_id"],
        status=result.status,
    )
    return {
        "job": _job_view(updated or job),
        "result": payload,
        "markdown": markdown,
        "evidence": saved,
        "deduplicated": False,
    }


@router.get("/engineering/pr-review/status")
async def pr_review_status(user: dict = Depends(require_auth)) -> dict:
    """Rollout state, worker identity, permission matrix and job ledger health.

    The rollout state is *derived* from configuration evidence, never asserted:
    a worker that is not configured cannot report SHADOW.
    """
    worker = GitHubAppWorker.from_env()
    policy = _review_policy()
    jobs = get_store().list_pr_review_jobs(user["uid"], limit=200)
    return {
        "schema": PR_REVIEW_SCHEMA,
        "capability": capability_manifest(),
        "rollout": rollout_state(policy, worker),
        "worker": worker.status(),
        "permissions": worker.permissions(),
        "policy": policy.to_dict(),
        "retry": _review_retry_policy().to_dict(),
        "replay_window_seconds": _review_replay_window_seconds(),
        "jobs": {
            "count": len(jobs),
            "by_state": _count_states(jobs),
            "dead_letters": [
                job["job_id"] for job in jobs if job.get("state") == "DEAD_LETTER"
            ],
        },
        "merge": {
            "enabled": False,
            "reason": "merge is human-only and structurally refused by this substrate",
        },
        "non_collapses": [
            "REVIEW != APPROVAL",
            "APPROVAL != MERGE",
            "GREEN != MERGE AUTHORIZATION",
            "SHADOW != ACTIVATED",
        ],
    }


@router.post("/engineering/pr-review/request")
async def pr_review_request(
    body: PrReviewRequestBody, user: dict = Depends(require_auth)
) -> dict:
    """Request a shadow review of an exact head. Read-only; idempotent per head."""
    worker = GitHubAppWorker.from_env()
    policy = _review_policy()
    event_id = (body.event_id or "").strip() or f"REQ-{uuid.uuid4().hex[:12]}"
    idempotency_key = "|".join(
        [
            str(body.installation_id),
            body.repository,
            str(body.pr_number),
            body.head_sha,
            event_id,
            body.action,
        ]
    )
    store = get_store()
    job = store.claim_pr_review_job(
        {
            "job_id": f"PRR-{uuid.uuid4().hex[:12]}",
            "idempotency_key": idempotency_key,
            "repository_ref": body.repository,
            "pr_number": int(body.pr_number),
            "base_sha": body.base_sha,
            "head_sha": body.head_sha,
            "installation_id": body.installation_id,
            "action": body.action,
            "event_id": event_id,
            "state": "QUEUED",
            "attempts": 0,
            "workspace_ref": "engineering-lab",
        },
        user["uid"],
    )
    if job.get("deduplicated") and job.get("result"):
        return {
            "job": _job_view(job),
            "result": job["result"],
            "markdown": job.get("markdown"),
            "deduplicated": True,
        }
    if job.get("deduplicated") and job.get("state") in {"RUNNING", "COMPLETED"}:
        # A concurrent or completed run owns this key; report it instead of
        # starting a second review of the same head.
        return {"job": _job_view(job), "result": job.get("result"), "deduplicated": True}

    try:
        return _execute_review_job(
            job, principal=user["uid"], subject_ref=user["uid"], worker=worker, policy=policy
        )
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/engineering/pr-review/jobs/{job_id}/run")
async def pr_review_run_job(job_id: str, user: dict = Depends(require_auth)) -> dict:
    """Execute a queued ingress job. Bounded retries; dead letters stay visible."""
    job = _load_review_job(job_id, user["uid"])
    if job.get("state") == "COMPLETED":
        return {"job": _job_view(job), "result": job.get("result"), "deduplicated": True}
    worker = GitHubAppWorker.from_env()
    policy = _review_policy()
    try:
        return _execute_review_job(
            job,
            principal=user["uid"],
            subject_ref=job["subject_ref"],
            worker=worker,
            policy=policy,
        )
    except BoundaryViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/engineering/pr-review/jobs")
async def pr_review_list_jobs(
    state: str | None = None, user: dict = Depends(require_auth)
) -> dict:
    """List this subject's review jobs, including dead letters."""
    jobs = get_store().list_pr_review_jobs(user["uid"], state=state, limit=100)
    return {
        "jobs": [_job_view(job) for job in jobs],
        "by_state": _count_states(jobs),
        "dead_letters": [job["job_id"] for job in jobs if job.get("state") == "DEAD_LETTER"],
    }


@router.get("/engineering/pr-review/jobs/{job_id}")
async def pr_review_get_job(job_id: str, user: dict = Depends(require_auth)) -> dict:
    """One job with its findings, evidence and report."""
    job = _load_review_job(job_id, user["uid"])
    evidence = get_store().list_evidence(job["subject_ref"], run_ref=job["job_id"])
    return {"job": _job_view(job), "evidence": evidence}


@router.post("/engineering/pr-review/jobs/{job_id}/grant")
async def pr_review_grant(
    job_id: str, body: PrReviewGrantBody, user: dict = Depends(require_auth)
) -> dict:
    """Record a human grant binding one exact repository/PR/head/action tuple.

    Recording a grant is a human act, and it is *not* the action itself: the
    publish path re-fetches the head, re-checks independence, re-checks the
    grant, and consumes it once.
    """
    job = _load_review_job(job_id, user["uid"])
    policy = _review_policy()
    worker = GitHubAppWorker.from_env()
    try:
        assert_action_permitted(body.action, policy)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if body.action not in (PUBLISH_COMMENT, REQUEST_CHANGES, APPROVE):
        raise HTTPException(
            status_code=400,
            detail=f"'{body.action}' is not a grantable review action",
        )

    binding = PrReviewRequest(
        subject_ref=user["uid"],
        principal=user["uid"],
        repository=str(job["repository_ref"]),
        pr_number=int(job["pr_number"]),
        base_sha=str(job.get("base_sha") or ""),
        head_sha=str(job["head_sha"]),
        installation_id=job.get("installation_id"),
        event_id=str(job.get("event_id") or ""),
    ).binding()

    result = job.get("result") or {}
    author = ((result.get("snapshot") or {}).get("author")) or ""
    try:
        assert_independent(user["uid"], author)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        assert_head_current(_review_reader(worker), binding)
    except StaleHead as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitHubUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    authorization = get_runtime().record_authorization(
        subject_ref=user["uid"],
        scope_ref=approval_scope(binding, body.action),
        operations_allowed=(body.action,),
        duration_minutes=int(body.duration_minutes),
    )
    return {
        "authorization_ref": authorization["authorization_id"],
        "authorization": authorization,
        "binding": binding.to_dict(),
        "action": body.action,
        "consequences": (
            "This grant permits exactly one "
            f"'{body.action}' on {binding.repository}#{binding.pr_number} at head "
            f"{binding.head_sha}. It expires after {body.duration_minutes} minutes, is "
            "single-use, is revocable, and is invalidated by any head change."
        ),
    }


@router.post("/engineering/pr-review/jobs/{job_id}/publish")
async def pr_review_publish(
    job_id: str, body: PrReviewPublishBody, user: dict = Depends(require_auth)
) -> dict:
    """Perform one GitHub-writing review action, under every gate at once.

    Requires: the stage gate, the action's policy flag, an exact-tuple human
    grant, an unchanged head, and independent review. Refuses by default.
    """
    job = _load_review_job(job_id, user["uid"])
    policy = _review_policy()
    worker = GitHubAppWorker.from_env()
    try:
        assert_action_permitted(body.action, policy)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if body.action not in (PUBLISH_COMMENT, REQUEST_CHANGES, APPROVE):
        raise HTTPException(
            status_code=400, detail=f"'{body.action}' is not a publishable review action"
        )

    binding = PrReviewRequest(
        subject_ref=user["uid"],
        principal=user["uid"],
        repository=str(job["repository_ref"]),
        pr_number=int(job["pr_number"]),
        base_sha=str(job.get("base_sha") or ""),
        head_sha=str(job["head_sha"]),
        installation_id=job.get("installation_id"),
        event_id=str(job.get("event_id") or ""),
    ).binding()

    result = job.get("result") or {}
    if not result:
        raise HTTPException(status_code=409, detail="the job has no review result to publish")
    if result.get("stale"):
        raise HTTPException(
            status_code=409,
            detail="the review is stale for its head; rerun before publishing",
        )

    author = ((result.get("snapshot") or {}).get("author")) or ""
    try:
        assert_independent(user["uid"], author)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    authorization = get_runtime().get_authorization(body.authorization_ref, user["uid"])
    try:
        assert_grant_matches(authorization, binding, body.action)
    except BoundaryViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    reader = _review_reader(worker)
    try:
        assert_head_current(reader, binding)
    except StaleHead as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitHubUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    consumed = get_store().consume_authorization(body.authorization_ref, user["uid"])
    if consumed is None:
        raise HTTPException(
            status_code=409,
            detail="the grant was already consumed or revoked; record a fresh grant",
        )

    event_map = {
        PUBLISH_COMMENT: "COMMENT",
        REQUEST_CHANGES: "REQUEST_CHANGES",
        APPROVE: "APPROVE",
    }
    body_text = str(result.get("markdown") or "") or f"Chief review: {result.get('status')}"
    try:
        response = _post_review(
            worker, binding.repository, binding.pr_number, event_map[body.action], body_text
        )
    except RateLimited as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GitHubUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "action": body.action,
        "github_event": event_map[body.action],
        "binding": binding.to_dict(),
        "authorization_ref": body.authorization_ref,
        "consumed_at": consumed.get("consumed_at"),
        "github_response": response,
        "note": (
            "A published review is not a merge, not an approval of the change for "
            "merge, and not production acceptance."
        ),
    }


def _post_review(
    worker: GitHubAppWorker, repository: str, pr_number: int, event: str, body: str
) -> dict:
    """Submit one review through the App worker credential. Never a PAT."""
    import json as _json

    token = worker.credential()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/pulls/{int(pr_number)}/reviews",
        data=_json.dumps({"event": event, "body": body}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = _json.loads(response.read().decode("utf-8") or "{}")
        return {
            "id": payload.get("id"),
            "state": payload.get("state"),
            "html_url": payload.get("html_url"),
        }
    except urllib.error.HTTPError as exc:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if exc.code in (403, 429) and retry_after and str(retry_after).isdigit():
            raise RateLimited(
                "GitHub rate limit on review submission", retry_after_seconds=int(retry_after)
            ) from exc
        raise GitHubUnavailable(f"GitHub review submission failed: http {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise GitHubUnavailable(f"GitHub review submission failed: {exc.reason}") from exc


@router.post("/engineering/pr-review/webhook")
async def pr_review_webhook(request: Request) -> dict:
    """GitHub App delivery ingress: verify, deduplicate, enqueue. Never execute.

    Authentication here is the HMAC signature plus the server-side installation
    and repository binding — not an account session. The receiver performs no
    GitHub read or write, so a forged or replayed body cannot cause work beyond
    a refused request.
    """
    worker = GitHubAppWorker.from_env()
    raw = await request.body()
    try:
        delivery = verify_webhook_delivery(
            headers={key: value for key, value in request.headers.items()},
            body=raw,
            worker=worker,
        )
    except WebhookRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc

    if not delivery.accepted:
        return {
            "status": "IGNORED",
            "reason": delivery.reason,
            "delivery_id": delivery.delivery_id,
        }

    claim = get_store().claim_pr_review_delivery(
        delivery.delivery_id,
        installation_id=delivery.installation_id,
        repository_ref=delivery.repository,
        payload_digest=delivery.payload_digest,
        window_seconds=_review_replay_window_seconds(),
        now_epoch=time.time(),
    )
    if claim == "replay":
        raise HTTPException(
            status_code=409,
            detail=(
                f"delivery {delivery.delivery_id} was first seen outside the replay "
                "window; a replayed delivery is refused"
            ),
        )
    if claim == "duplicate":
        return {
            "status": "DUPLICATE",
            "delivery_id": delivery.delivery_id,
            "reason": "this delivery was already accepted; no second job was created",
        }

    if delivery.pr_number is None or not delivery.head_sha or not delivery.base_sha:
        raise HTTPException(
            status_code=400,
            detail="a verified delivery must name a pull request and both SHAs",
        )

    idempotency_key = "|".join(
        [
            str(delivery.installation_id),
            delivery.repository,
            str(delivery.pr_number),
            delivery.head_sha,
            delivery.delivery_id,
            GENERATE_FINDINGS,
        ]
    )
    job = get_store().claim_pr_review_job(
        {
            "job_id": f"PRR-{uuid.uuid4().hex[:12]}",
            "idempotency_key": idempotency_key,
            "repository_ref": delivery.repository,
            "pr_number": int(delivery.pr_number),
            "base_sha": delivery.base_sha,
            "head_sha": delivery.head_sha,
            "installation_id": delivery.installation_id,
            "action": GENERATE_FINDINGS,
            "event_id": delivery.delivery_id,
            "delivery_id": delivery.delivery_id,
            "state": "QUEUED",
            "attempts": 0,
            "workspace_ref": "engineering-lab",
        },
        PR_REVIEW_SYSTEM_SUBJECT,
    )
    return {
        "status": "QUEUED",
        "delivery_id": delivery.delivery_id,
        "job": _job_view(job),
        "deduplicated": bool(job.get("deduplicated")),
    }
