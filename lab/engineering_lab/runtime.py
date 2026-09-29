"""EL-01 / EL-02 / EL-10 — the Engineering Lab runtime core.

This is the native Arkadia control plane for agentic engineering work. It ties
together the pieces built in this package:

  * bounded sandbox execution   (``sandbox.py``)
  * agent/session/run models    (``models.py``)
  * live event stream           (``events.py``)
  * durable store               (``store.py``)
  * model gateway               (``gateway.py``)

The canonical loop (directive section 13, EL-10):

  DISCOVER -> PLAN -> EXECUTE -> OBSERVE -> EVIDENCE -> PROPOSE
  -> REVIEW -> AUTHORIZE -> VERIFY -> RECORD

A run stops at the human authorization boundary. The runtime can *prepare* a
change set; it can never merge, deploy, or self-authorize. Authorization is
recorded only when it is human-originated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from typing import Any

from .contracts import (
    BoundaryViolation,
    EvidenceRecord,
    assert_operation_allowed,
    utc_now,
)
from .events import get_event_stream
from .gateway import get_gateway
from .models import (
    AGENT_CAPABILITIES,
    AGENT_ROLES,
    ROLE_CAPABILITIES,
    Agent,
    AgentRun,
    AgentSession,
    AgentToolAccess,
)
from .sandbox import Sandbox, SandboxPolicy
from .store import get_store

#: The canonical C09 loop stages, surfaced by the operational view (EL-10).
CANONICAL_LOOP: tuple[str, ...] = (
    "DISCOVER",
    "PLAN",
    "EXECUTE",
    "OBSERVE",
    "EVIDENCE",
    "PROPOSE",
    "REVIEW",
    "AUTHORIZE",
    "VERIFY",
    "RECORD",
)

#: Concrete sandbox operation kinds a bounded task may request.
READ_OPERATIONS: frozenset[str] = frozenset({"read", "list", "run", "git_status"})
WRITE_OPERATIONS: frozenset[str] = frozenset({"write"})


@dataclass(frozen=True)
class BoundedOperation:
    """One inspectable operation inside a bounded task."""

    kind: str  # read | list | run | write | git_status
    target: str = ""
    argv: tuple[str, ...] = ()
    content: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "target": self.target,
            "argv": list(self.argv),
            "description": self.description,
            "has_content": bool(self.content),
        }


@dataclass(frozen=True)
class BoundedTask:
    """A bounded objective with an explicit operation set and evidence recipe.

    This is the AEAS "Move" made concrete and inspectable.
    """

    objective: str
    operations: tuple[BoundedOperation, ...] = ()
    acceptance: tuple[str, ...] = ()
    requires_write: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "operations": [o.to_dict() for o in self.operations],
            "acceptance": list(self.acceptance),
            "requires_write": self.requires_write,
        }


#: The sandbox operation token(s) each agent capability reaches. A capability
#: that is absent (or not in the role ceiling) grants no operation of that kind.
CAPABILITY_OPERATIONS: dict[str, tuple[str, ...]] = {
    "READ": ("read", "list"),
    "EDIT": ("read", "list"),
    "RUN": ("run",),
    "OBSERVE": ("git_status",),
}

#: Operation token -> the loop tool(s) that expose it. Read-only git
#: observation (status and diff) share one authorization token.
OPERATION_TOOLS: dict[str, tuple[str, ...]] = {
    "list": ("filesystem.list",),
    "read": ("filesystem.read",),
    "run": ("terminal.run",),
    "git_status": ("git.status", "git.diff"),
}

_ALL_LOOP_TOOLS: tuple[str, ...] = (
    "filesystem.list", "filesystem.read", "terminal.run", "git.status", "git.diff",
)


def _capability_operations(capabilities: tuple[str, ...]) -> set[str]:
    ops: set[str] = set()
    for capability in capabilities:
        ops.update(CAPABILITY_OPERATIONS.get(capability, ()))
    return ops


def effective_tools(
    *,
    capabilities: tuple[str, ...],
    agent_tools: tuple[str, ...],
    authorization_operations: set[str] | None,
) -> tuple[str, ...]:
    """Derive the effective tool set as the intersection of three layers.

        capability ceiling ∩ agent tool envelope ∩ human authorization

    ``authorization_operations`` of ``None`` means no authorization was linked;
    callers must treat that as the empty set for a consequential run.
    """
    allowed = _capability_operations(capabilities) & set(agent_tools)
    if authorization_operations is not None:
        allowed &= authorization_operations
    return tuple(
        tool for op, tools in OPERATION_TOOLS.items() if op in allowed for tool in tools
    )


class EngineeringLabRuntime:
    """The native Arkadia Engineering Lab runtime.

    Agents are workers. This runtime orchestrates them inside bounded sandboxes
    and records evidence. It does not hold authority.
    """

    def __init__(self, *, store: Any | None = None, stream: Any | None = None) -> None:
        self._store = store or get_store()
        self._stream = stream or get_event_stream()
        self._sandboxes: dict[str, Sandbox] = {}

    # -- EL-09: agent deployment ---------------------------------------------

    def register_agent(
        self,
        *,
        subject_ref: str,
        role: str,
        display_name: str = "",
        capabilities: tuple[str, ...] | None = None,
        write_allowed: bool = False,
        model_ref: str | None = None,
    ) -> dict[str, Any]:
        """Deploy a bounded agent. No deployed agent receives implicit authority."""
        if role not in AGENT_ROLES:
            raise ValueError(f"unknown agent role '{role}'")
        caps = capabilities if capabilities is not None else ROLE_CAPABILITIES[role]
        for cap in caps:
            if cap not in AGENT_CAPABILITIES:
                raise ValueError(f"unknown capability '{cap}'")
            # A capability may not exceed the role's declared ceiling.
            if cap not in ROLE_CAPABILITIES[role]:
                raise BoundaryViolation(
                    f"capability '{cap}' exceeds the ceiling for role '{role}'"
                )
        agent = Agent(
            agent_id=f"AGT-{uuid.uuid4().hex[:12]}",
            role=role,
            display_name=display_name or f"{role.title()} agent",
            capabilities=tuple(caps),
            tool_access=AgentToolAccess(
                tools=("read", "list")
                + (("run",) if "RUN" in caps else ())
                + (("git_status",) if "OBSERVE" in caps else ())
                + (("write",) if write_allowed else ()),
                write_allowed=write_allowed,
            ),
            model_ref=model_ref,
        )
        record = agent.to_dict()
        record["subject_ref"] = subject_ref
        self._store.save_agent(record)
        return record

    # -- EL-01: sessions ------------------------------------------------------

    def open_session(
        self,
        *,
        subject_ref: str,
        workspace_ref: str,
        agent_id: str,
        objective: str,
        repository_ref: str | None = None,
        authorization_ref: str | None = None,
    ) -> dict[str, Any]:
        """Open a bounded session.

        The session is created ``PROPOSED``. If a human-originated
        authorization is supplied and valid for this scope it becomes
        ``AUTHORIZED`` — otherwise it stays ``PROPOSED`` and cannot execute.
        """
        if not subject_ref or not workspace_ref:
            raise ValueError("subject_ref and workspace_ref are required")
        state = "PROPOSED"
        resolved_auth = None
        if authorization_ref:
            auth = self._store.get_authorization(authorization_ref, subject_ref)
            if auth is None:
                raise BoundaryViolation(
                    f"authorization '{authorization_ref}' not found; cannot authorize session"
                )
            resolved_auth = authorization_ref
            state = "AUTHORIZED"
        session = AgentSession(
            session_id=f"SES-{uuid.uuid4().hex[:12]}",
            subject_ref=subject_ref,
            workspace_ref=workspace_ref,
            agent_id=agent_id,
            state=state,
            objective=objective,
            repository_ref=repository_ref,
            authorization_ref=resolved_auth,
        )
        self._store.create_session(session)
        self._emit(
            subject_ref,
            session.session_id,
            "SESSION_CREATED",
            {"objective": objective, "state": state},
        )
        return self.get_session(session.session_id, subject_ref)

    def record_authorization(
        self,
        *,
        subject_ref: str,
        scope_ref: str,
        operations_allowed: tuple[str, ...],
        duration_minutes: int = 60,
        merge: bool = False,
        production: bool = False,
    ) -> dict[str, Any]:
        """Record a human-originated authorization for a bounded scope.

        The substrate cannot originate authority; ``originated_by`` is fixed to
        ``human`` and the store rejects anything else. Merge and production are
        human-only and are recorded as prohibited.
        """
        record = {
            "authorization_id": f"AUTH-{uuid.uuid4().hex[:12]}",
            "originated_by": "human",
            "scope_ref": scope_ref,
            "operations_allowed": list(operations_allowed),
            "duration_minutes": duration_minutes,
            "merge": False if not merge else "PROHIBITED_TO_SUBSTRATE",
            "production": False if not production else "PROHIBITED_TO_SUBSTRATE",
            "merge_prohibited": True,
            "production_prohibited": True,
            "created_at": utc_now(),
        }
        return self._store.record_authorization(record, subject_ref)

    def get_session(self, session_id: str, subject_ref: str) -> dict[str, Any]:
        session = self._store.get_session(session_id, subject_ref)
        if session is None:
            raise KeyError(f"session '{session_id}' not found for subject")
        return session

    def transition(self, session_id: str, subject_ref: str, target: str) -> dict[str, Any]:
        """Transition a session, enforcing AEAS section 5 legality."""
        updated = self._store.transition_session(session_id, subject_ref, target)
        self._emit(
            subject_ref, session_id, "SESSION_TRANSITION", {"state": target}
        )
        return updated

    # -- EL-02 / EL-10: bounded execution ------------------------------------

    def execute_bounded_task(
        self,
        *,
        subject_ref: str,
        session_id: str,
        task: BoundedTask,
        sandbox_policy: SandboxPolicy | None = None,
    ) -> dict[str, Any]:
        """Execute one bounded Move and stop at the human review boundary.

        Stages implemented: PLAN -> EXECUTE -> OBSERVE -> EVIDENCE -> PROPOSE.
        The run ends ``READY_FOR_REVIEW``. It never merges, deploys, or
        self-authorizes.
        """
        session = self.get_session(session_id, subject_ref)
        if session["state"] not in ("AUTHORIZED", "QUEUED"):
            raise BoundaryViolation(
                f"session must be AUTHORIZED or QUEUED to execute "
                f"(currently {session['state']}); SESSION != AUTHORIZATION"
            )
        for op in task.operations:
            if op.kind in WRITE_OPERATIONS and not task.requires_write:
                raise BoundaryViolation(
                    "write operation present but task.requires_write is False"
                )
            if op.kind not in READ_OPERATIONS | WRITE_OPERATIONS:
                raise BoundaryViolation(f"unknown operation kind '{op.kind}'")

        agent = self._find_agent(subject_ref, session["agent_id"])
        run_id = f"RUN-{uuid.uuid4().hex[:12]}"

        # --- PLAN ------------------------------------------------------------
        plan = {
            "task": task.to_dict(),
            "sandbox_policy": self._policy_view(sandbox_policy),
            "forbidden": ["merge", "production_deploy", "self_authorize"],
            "loop_stage": "PLAN",
        }
        run = AgentRun(
            run_id=run_id,
            session_id=session_id,
            agent_id=session["agent_id"],
            state="RUNNING",
            objective=task.objective,
            subject_ref=subject_ref,
            plan=plan,
        )
        self._store.create_run(run)
        self._emit(subject_ref, session_id, "PLAN_PRODUCED", plan, run_id=run_id)

        # --- EXECUTE / OBSERVE ----------------------------------------------
        policy = sandbox_policy or SandboxPolicy(
            root=self._default_workspace_root(),
            write_allowed=task.requires_write and agent.get("tool_access", {}).get("write_allowed", False),
            command_allowlist=("git",),
            enforce_git_read_only=True,
            enforce_command_grammar=True,
        )
        if sandbox_policy is not None:
            policy = replace(policy, enforce_git_read_only=True,
                             enforce_command_grammar=True)
        try:
            sandbox = Sandbox(policy)
        except Exception as exc:
            self._store.update_run(
                run_id, subject_ref, state="BLOCKED", result_state="BLOCKED"
            )
            self._emit(
                subject_ref, session_id, "BLOCKED",
                {"reason": f"sandbox unavailable: {exc}"}, run_id=run_id,
            )
            return self._finish(
                subject_ref, session_id, run_id, state="BLOCKED",
                result_state="BLOCKED", observations=[],
                summary=f"sandbox unavailable: {exc}",
            )

        observations: list[dict[str, Any]] = []
        artifacts: list[dict[str, Any]] = []
        for op in task.operations:
            try:
                observed = self._run_operation(sandbox, op)
            except Exception as exc:
                observed = {"kind": op.kind, "ok": False, "error": str(exc)}
            observations.append(observed)
            self._emit(
                subject_ref, session_id, "SANDBOX_OPERATION",
                {"kind": op.kind, "ok": observed.get("ok", False)}, run_id=run_id,
            )

        # --- EVIDENCE / PROPOSE ---------------------------------------------
        evidence_state = "IMPLEMENTED" if observations and all(
            o.get("ok") for o in observations
        ) else ("BLOCKED" if any(o.get("error") for o in observations) else "NOT_ATTEMPTED")

        if task.requires_write:
            artifact = self._capture_artifact(
                subject_ref, session_id, run_id, "diff",
                f"Proposed change set — {task.objective}",
                {"observations": observations, "note": "prepared, not applied to repository"},
            )
            artifacts.append(artifact)

        evidence = EvidenceRecord(
            evidence_id=f"EVD-{uuid.uuid4().hex[:12]}",
            subject_ref=subject_ref,
            workspace_ref=session["workspace_ref"],
            run_ref=run_id,
            state=evidence_state,
            summary=f"bounded task executed: {task.objective}",
            detail={
                "observations": observations,
                "acceptance": list(task.acceptance),
                "artifact_refs": [a["artifact_id"] for a in artifacts],
                "loop_stages_completed": ["PLAN", "EXECUTE", "OBSERVE", "EVIDENCE", "PROPOSE"],
            },
            timestamp_utc=utc_now(),
            provenance={
                "session_id": session_id,
                "agent_id": session["agent_id"],
                "authorization_ref": session.get("authorization_ref"),
                "sandbox_root": str(sandbox.root),
            },
        )
        self._store.save_evidence(evidence)
        self._emit(
            subject_ref, session_id, "EVIDENCE_RECORDED",
            {"evidence_id": evidence.evidence_id, "state": evidence_state}, run_id=run_id,
        )
        self._emit(
            subject_ref, session_id, "PROPOSAL_PREPARED",
            {"artifact_refs": [a["artifact_id"] for a in artifacts]}, run_id=run_id,
        )
        self._emit(
            subject_ref, session_id, "AUTHORIZATION_REQUIRED",
            {"note": "human review required; the substrate does not merge or deploy"},
            run_id=run_id,
        )

        return self._finish(
            subject_ref, session_id, run_id,
            state="VERIFYING", result_state=evidence_state,
            observations=observations,
            summary=f"bounded task reached review boundary: {task.objective}",
            evidence_refs=(evidence.evidence_id,),
            artifact_refs=tuple(a["artifact_id"] for a in artifacts),
        )

    # -- EL-10: operational surface ------------------------------------------

    def execute_agent_loop(
        self,
        *,
        subject_ref: str,
        session_id: str,
        objective: str,
        provider: str = "ollama",
        model: str | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        max_turns: int = 8,
        require_human_on_terminate: bool = True,
    ) -> dict[str, Any]:
        """GATE L1: run the native agent loop inside a governed Lab session.

        Read-only by construction: the granted tool set contains no mutation
        tool, so the loop cannot edit, commit, or push. On termination the run
        ends ``READY_FOR_REVIEW`` — never COMPLETED, never merged. Consequential
        repository mutation is GATE L2 and must cross PassSpec -> K15 -> K3.
        """
        from .agent_loop import AgentLoop
        from .gateway import get_gateway
        from .tools import ToolRegistry

        session = self.get_session(session_id, subject_ref)
        if session["state"] not in ("AUTHORIZED", "QUEUED"):
            raise BoundaryViolation(
                f"session must be AUTHORIZED or QUEUED to execute "
                f"(currently {session['state']}); SESSION != AUTHORIZATION"
            )
        agent = self._find_agent(subject_ref, session["agent_id"])
        tool_access = agent.get("tool_access", {}) or {}
        capabilities = tuple(agent.get("capabilities", ()))

        # Effective tools = capability ceiling ∩ agent tool envelope ∩ human
        # authorization. CAPABILITY is not AUTHORIZATION: the session must be
        # AUTHORIZED above, its authorization record bounds the operations, and
        # the sandbox policy is the final layer. A session with no linked
        # authorization yields no tools.
        authorization_ops: set[str] | None = None
        if session.get("authorization_ref"):
            auth = self._store.get_authorization(session["authorization_ref"], subject_ref)
            if auth:
                authorization_ops = set(auth.get("operations_allowed", ()))
        effective = effective_tools(
            capabilities=capabilities,
            agent_tools=tuple(tool_access.get("tools") or ()),
            authorization_operations=authorization_ops,
        )

        policy = sandbox_policy or SandboxPolicy(
            root=self._default_workspace_root(),
            write_allowed=False,
            command_allowlist=("git",),
            enforce_git_read_only=True,
            enforce_command_grammar=True,
        )
        if sandbox_policy is not None:
            policy = replace(policy, enforce_git_read_only=True,
                             enforce_command_grammar=True)
        try:
            sandbox = Sandbox(policy)
        except Exception as exc:
            run_id = f"RUN-{uuid.uuid4().hex[:12]}"
            run = AgentRun(run_id, session_id, session["agent_id"], "BLOCKED",
                           objective, subject_ref, plan={"loop_stage": "PLAN"})
            self._store.create_run(run)
            return self._finish(subject_ref, session_id, run_id, state="BLOCKED",
                                result_state="BLOCKED", observations=[],
                                summary=f"sandbox unavailable: {exc}")

        run_id = f"RUN-{uuid.uuid4().hex[:12]}"
        run = AgentRun(
            run_id, session_id, session["agent_id"], "RUNNING", objective, subject_ref,
            plan={"loop_stage": "MODEL", "objective": objective,
                  "provider": provider, "model": model or "(selected)",
                  "effective_tools": list(effective)},
        )
        self._store.create_run(run)
        self._emit(subject_ref, session_id, "RUN_STARTED",
                   {"objective": objective, "provider": provider,
                    "effective_tools": list(effective)}, run_id=run_id)

        registry = ToolRegistry(sandbox, granted=effective)
        gateway = get_gateway()
        descriptor = gateway.describe(provider)
        selection = gateway.select(preferred=provider)

        def on_event(event_type: str, payload: dict[str, Any]) -> None:
            self._emit(subject_ref, session_id, event_type, payload, run_id=run_id)

        loop = AgentLoop(gateway=gateway, tools=registry, provider=provider,
                         model=model or descriptor.model, max_turns=max_turns)
        result = loop.run(objective=objective, on_event=on_event)

        observations = [t.observation for t in result.turns if t.observation]
        result_state = {
            "DONE": "IMPLEMENTED",
            "BLOCKED": "BLOCKED",
            "ERROR": "BLOCKED",
            "HUMAN_AUTHORIZATION_REQUIRED": "BLOCKED",
        }.get(result.state, "BLOCKED")

        evidence = EvidenceRecord(
            evidence_id=f"EVD-{uuid.uuid4().hex[:12]}",
            subject_ref=subject_ref,
            workspace_ref=session["workspace_ref"],
            run_ref=run_id,
            state=result_state,
            summary=f"agent loop terminated {result.state}: {result.reason or 'model completed'}",
            detail={"loop": result.to_dict(), "model_selection": selection.to_dict(),
                    "descriptor": descriptor.to_dict()},
            timestamp_utc=utc_now(),
            provenance={"provider": provider, "model": descriptor.model,
                        "tool_count": len(registry.available()),
                        "effective_tools": list(effective),
                        "mutating_tools": [t["name"] for t in registry.available() if t["mutating"]]},
        )
        self._store.save_evidence(evidence)
        self._emit(subject_ref, session_id, "EVIDENCE_RECORDED",
                   {"evidence_id": evidence.evidence_id, "state": result_state}, run_id=run_id)

        terminal_state = "READY_FOR_REVIEW" if result.state == "DONE" else "BLOCKED"
        if require_human_on_terminate and result.state == "DONE":
            self._emit(subject_ref, session_id, "AUTHORIZATION_REQUIRED",
                       {"run_id": run_id, "reason": "loop terminated DONE"}, run_id=run_id)

        return self._finish(
            subject_ref, session_id, run_id,
            state="VERIFYING" if terminal_state != "BLOCKED" else "BLOCKED",
            result_state=result_state, observations=observations,
            summary=f"agent loop {result.state}",
            evidence_refs=(evidence.evidence_id,),
        ) | {"loop_state": result.state, "turns": [t.to_dict() for t in result.turns]}

    def session_view(self, session_id: str, subject_ref: str) -> dict[str, Any]:
        """Full inspectable state of one session (EL-10 'what is happening')."""
        session = self.get_session(session_id, subject_ref)
        agent = self._find_agent(subject_ref, session["agent_id"])
        runs = self._store.list_runs(session_id, subject_ref)
        events = self._store.list_events(session_id, subject_ref)
        evidence = self._store.list_evidence(subject_ref)
        evidence = [e for e in evidence if e.get("run_ref") in {r["run_id"] for r in runs}]
        artifacts = self._store.list_artifacts(subject_ref, session_id)
        return {
            "session": session,
            "agent": agent,
            "runs": runs,
            "events": events,
            "evidence": evidence,
            "artifacts": artifacts,
            "loop": list(CANONICAL_LOOP),
            "reached_review_boundary": session["state"] in (
                "READY_FOR_REVIEW", "VERIFYING", "REVISION_REQUIRED"
            ),
            "human_decision_required": session["state"] in (
                "READY_FOR_REVIEW", "VERIFYING"
            ),
        }

    def overview(self, subject_ref: str) -> dict[str, Any]:
        """Top-level Lab overview for the C09 operational surface (EL-10)."""
        sessions = self._store.list_sessions(subject_ref)
        return {
            "sessions": sessions,
            "agents": self._store.list_agents(subject_ref),
            "automations": self._store.list_automations(subject_ref),
            "loop": list(CANONICAL_LOOP),
            "gateway": get_gateway().to_dict(),
            "counts": {
                "sessions": len(sessions),
                "active": sum(
                    1
                    for s in sessions
                    if s["state"] in ("AUTHORIZED", "QUEUED", "RUNNING", "VERIFYING")
                ),
                "awaiting_human": sum(
                    1 for s in sessions if s["state"] in ("READY_FOR_REVIEW", "VERIFYING")
                ),
            },
            "authority": {
                "lab_authority_ceiling": 2,
                "autonomous_merge": False,
                "autonomous_deploy": False,
                "human_authorization_required": True,
            },
        }

    # -- internals ------------------------------------------------------------

    def _find_agent(self, subject_ref: str, agent_id: str) -> dict[str, Any]:
        for agent in self._store.list_agents(subject_ref):
            if agent["agent_id"] == agent_id:
                return agent
        raise KeyError(f"agent '{agent_id}' not found for subject")

    def _run_operation(self, sandbox: Sandbox, op: BoundedOperation) -> dict[str, Any]:
        if op.kind == "read":
            text = sandbox.read(op.target)
            return {"kind": "read", "target": op.target, "ok": True, "content": text}
        if op.kind == "list":
            entries = sandbox.list(op.target or ".")
            return {"kind": "list", "target": op.target, "ok": True, "entries": entries}
        if op.kind == "run":
            assert_operation_allowed(op.kind)
            result = sandbox.run(list(op.argv))
            return {"kind": "run", "argv": list(op.argv), **result}
        if op.kind == "git_status":
            result = sandbox.git(["status", "--short"])
            return {"kind": "git_status", "ok": result.get("ok", False), "stdout": result.get("stdout", "")}
        if op.kind == "write":
            result = sandbox.write(op.target, op.content)
            return {"kind": "write", **result, "ok": True}
        raise BoundaryViolation(f"unknown operation kind '{op.kind}'")

    def _capture_artifact(
        self,
        subject_ref: str,
        session_id: str,
        run_id: str,
        kind: str,
        title: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        artifact = {
            "artifact_id": f"ART-{uuid.uuid4().hex[:12]}",
            "session_id": session_id,
            "run_id": run_id,
            "kind": kind,
            "title": title,
            "content": content,
            "created_at": utc_now(),
        }
        self._store.save_artifact(artifact, subject_ref)
        self._emit(
            subject_ref, session_id, "ARTIFACT_CAPTURED",
            {"artifact_id": artifact["artifact_id"], "kind": kind}, run_id=run_id,
        )
        return artifact

    def _finish(
        self,
        subject_ref: str,
        session_id: str,
        run_id: str,
        *,
        state: str,
        result_state: str,
        observations: list[dict[str, Any]],
        summary: str,
        evidence_refs: tuple[str, ...] = (),
        artifact_refs: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        self._store.update_run(
            run_id, subject_ref, state=state, result_state=result_state,
            evidence_refs=list(evidence_refs), artifact_refs=list(artifact_refs),
        )
        # Advance the session through the canonical AEAS state chain rather than
        # collapsing states. A successful run ends READY_FOR_REVIEW; a failed
        # run ends BLOCKED. Neither is COMPLETED — that is a human act.
        target = "READY_FOR_REVIEW" if state != "BLOCKED" else "BLOCKED"
        self._advance(session_id, subject_ref, target)
        self._emit(
            subject_ref, session_id, "RUN_FINISHED",
            {"run_id": run_id, "state": state, "result_state": result_state},
            run_id=run_id,
        )
        return {
            "run_id": run_id,
            "session_id": session_id,
            "state": state,
            "result_state": result_state,
            "summary": summary,
            "observations": observations,
            "evidence_refs": list(evidence_refs),
            "artifact_refs": list(artifact_refs),
            "human_decision_required": target == "READY_FOR_REVIEW",
            "merge": False,
            "deploy": False,
            "self_authorized": False,
        }

    def _advance(self, session_id: str, subject_ref: str, target: str) -> dict[str, Any]:
        """Walk a session to *target* through legal intermediates (AEAS section 5).

        Never collapses states: e.g. RUNNING reaches READY_FOR_REVIEW only via
        CHECKPOINTED and VERIFYING.
        """
        from .contracts import LEGAL_TRANSITIONS

        session = self._store.get_session(session_id, subject_ref)
        if session is None:
            raise KeyError(f"session '{session_id}' not found for subject")
        start = session["state"]
        if start == target:
            return session

        # Breadth-first search for a legal path, preferring the shortest.
        queue: list[list[str]] = [[start]]
        seen: set[str] = {start}
        path: list[str] | None = None
        while queue:
            current = queue.pop(0)
            node = current[-1]
            for nxt in sorted(LEGAL_TRANSITIONS.get(node, frozenset())):
                if nxt in seen:
                    continue
                if nxt == target:
                    path = current + [nxt]
                    break
                seen.add(nxt)
                queue.append(current + [nxt])
            if path:
                break
        if path is None:
            raise BoundaryViolation(
                f"no legal transition path {start} -> {target}"
            )
        for nxt in path[1:]:
            self._store.transition_session(session_id, subject_ref, nxt)
            self._emit(subject_ref, session_id, "SESSION_TRANSITION", {"state": nxt})
        updated = self._store.get_session(session_id, subject_ref)
        assert updated is not None
        return updated

    def _emit(
        self,
        subject_ref: str,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
        run_id: str | None = None,
    ) -> None:
        record = self._stream.emit(
            session_id=session_id, event_type=event_type, payload=payload, run_id=run_id
        ).to_dict()
        try:
            self._store.append_event(record, subject_ref)
        except Exception:
            # The durable append is best-effort; the live event already fired.
            pass

    @staticmethod
    def _default_workspace_root() -> str:
        import os

        return os.environ.get("ENGINEERING_LAB_WORKSPACE_ROOT", ".")

    @staticmethod
    def _policy_view(policy: SandboxPolicy | None) -> dict[str, Any]:
        if policy is None:
            return {"root": "default", "write_allowed": False}
        return {
            "root": policy.root,
            "write_allowed": policy.write_allowed,
            "allow_network": policy.allow_network,
        }


_GLOBAL_RUNTIME: EngineeringLabRuntime | None = None


def get_runtime() -> EngineeringLabRuntime:
    global _GLOBAL_RUNTIME
    if _GLOBAL_RUNTIME is None:
        _GLOBAL_RUNTIME = EngineeringLabRuntime()
    return _GLOBAL_RUNTIME
