"""EL-01 / EL-02 — agent, role, session, run, and event models.

These are the native Arkadia Engineering Lab models. They deliberately reuse
canonical primitives rather than inventing parallel ones:

  * identity      -> ``subject_ref`` is the verified Firebase uid, exactly as
                     every other SolSpire primitive stores it.
  * workspace     -> ``workspace_ref`` is an existing SolSpire workspace id
                     (``solspire.workspace_manager.Workspace.id``); this package
                     never defines its own workspace type.
  * events        -> an :class:`AgentEvent` is *lab-internal execution telemetry*,
                     distinct from a SolSpire ``WorkEvent`` (the canonical
                     continuity ledger) and from a Weaver ``OperationalEvent``.
                     A run never writes a WorkEvent on its own authority.

Agents are workers. Agents are never sovereign authorities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import NON_COLLAPSES, utc_now

# -- Roles (directive section 2, AGENT PLANE) ---------------------------------

#: The initial agent roles. Roles may map to the same underlying runtime; this
#: module does not implement separate intelligence stacks.
AGENT_ROLES: tuple[str, ...] = (
    "WEAVER",
    "BUILDER",
    "REVIEWER",
    "VISUALIST",
    "SENTINEL",
    "ARCHIVIST",
)

#: Capability classes. A capability is discovery metadata, never authorization.
AGENT_CAPABILITIES: tuple[str, ...] = (
    "READ",
    "EDIT",
    "RUN",
    "TEST",
    "BROWSE",
    "RENDER",
    "OBSERVE",
    "PROPOSE",
    "OPEN_PR",
)

#: The capability *ceiling* per role. This is descriptive of what the role is
#: for; the authoritative limit remains the task's PassSpec/authorization.
ROLE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "WEAVER": ("READ", "OBSERVE", "PROPOSE"),
    "BUILDER": ("READ", "EDIT", "RUN", "TEST", "PROPOSE"),
    "REVIEWER": ("READ", "OBSERVE", "PROPOSE"),
    "VISUALIST": ("READ", "RENDER", "OBSERVE", "PROPOSE"),
    "SENTINEL": ("READ", "OBSERVE"),
    "ARCHIVIST": ("READ", "OBSERVE", "PROPOSE"),
}


@dataclass(frozen=True)
class AgentCapability:
    """A declared, bounded capability. Discovery metadata — not authorization."""

    name: str
    description: str = ""
    requires_write: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_write": self.requires_write,
        }


@dataclass(frozen=True)
class AgentToolAccess:
    """The tool envelope a run is granted. Mirrors the sandbox policy."""

    tools: tuple[str, ...] = ("read", "list")
    write_allowed: bool = False
    network_allowed: bool = False
    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tools": list(self.tools),
            "write_allowed": self.write_allowed,
            "network_allowed": self.network_allowed,
            "allowed_paths": list(self.allowed_paths),
            "forbidden_paths": list(self.forbidden_paths),
        }


@dataclass(frozen=True)
class Agent:
    """A deployed bounded worker. Reproducible; never receives implicit authority."""

    agent_id: str
    role: str
    display_name: str
    capabilities: tuple[str, ...]
    tool_access: AgentToolAccess
    model_ref: str | None = None
    policy_ref: str | None = None
    created_at: str = field(default_factory=utc_now)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.role not in AGENT_ROLES:
            raise ValueError(f"unknown agent role '{self.role}'")
        for cap in self.capabilities:
            if cap not in AGENT_CAPABILITIES:
                raise ValueError(f"unknown capability '{cap}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "display_name": self.display_name,
            "capabilities": list(self.capabilities),
            "tool_access": self.tool_access.to_dict(),
            "model_ref": self.model_ref,
            "policy_ref": self.policy_ref,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }


@dataclass
class AgentSession:
    """A bounded window of agent activity with a hard stop.

    ``state`` is drawn from the canonical AEAS checkpoint vocabulary. A session
    is the substrate's unit of continuity — it is NOT authorization.
    """

    session_id: str
    subject_ref: str
    workspace_ref: str
    agent_id: str
    state: str
    objective: str = ""
    repository_ref: str | None = None
    project_ref: str | None = None
    authorization_ref: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = "1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "subject_ref": self.subject_ref,
            "workspace_ref": self.workspace_ref,
            "agent_id": self.agent_id,
            "state": self.state,
            "objective": self.objective,
            "repository_ref": self.repository_ref,
            "project_ref": self.project_ref,
            "authorization_ref": self.authorization_ref,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
            "non_collapses": [f"{a} != {b}" for a, b in NON_COLLAPSES],
        }


@dataclass
class AgentRun:
    """A single governed execution within a session."""

    run_id: str
    session_id: str
    agent_id: str
    state: str
    objective: str
    subject_ref: str = ""
    plan: dict[str, Any] = field(default_factory=dict)
    result_state: str | None = None
    evidence_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = "1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "objective": self.objective,
            "plan": self.plan,
            "result_state": self.result_state,
            "evidence_refs": list(self.evidence_refs),
            "artifact_refs": list(self.artifact_refs),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class AgentEvent:
    """Lab-internal execution telemetry for a run.

    Distinct from a SolSpire ``WorkEvent`` (canonical continuity ledger) and a
    Weaver ``OperationalEvent``. This is the live event stream the Lab observes.
    """

    event_id: str
    session_id: str
    run_id: str | None
    event_type: str
    payload: dict[str, Any]
    sequence: int = 0
    timestamp_utc: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "sequence": self.sequence,
            "timestamp_utc": self.timestamp_utc,
        }


#: Canonical AgentEvent types (live execution stream vocabulary).
AGENT_EVENT_TYPES: tuple[str, ...] = (
    "SESSION_CREATED",
    "SESSION_TRANSITION",
    "RUN_STARTED",
    "PLAN_PRODUCED",
    "SANDBOX_OPERATION",
    "ARTIFACT_CAPTURED",
    "EVIDENCE_RECORDED",
    "PROPOSAL_PREPARED",
    "AUTHORIZATION_REQUIRED",
    "BLOCKED",
    "HARD_STOP",
    "RUN_FINISHED",
    # GATE L1: agent-loop telemetry. Additive; the substrate events above are
    # unchanged. These carry a model turn, a tool intent, a tool observation,
    # and the loop's per-turn decision onto the existing live event stream.
    "MODEL_TURN",
    "TOOL_INTENT",
    "TOOL_OBSERVATION",
    "AGENT_DECISION",
)
