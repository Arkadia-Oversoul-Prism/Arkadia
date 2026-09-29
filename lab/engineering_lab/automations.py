"""EL-03 — native automations.

Automation capability lives in Arkadia's own control plane, not an external
scheduler. The automation grammar (directive section 6):

  TRIGGER -> AGENT -> TOOLS -> SANDBOX -> OUTPUT -> EVIDENCE
          -> NOTIFICATION -> HUMAN GATE

An automation may *prepare* consequential actions. It may never independently
authorize them: the final transition is always the human gate.

Deterministic automation state (directive section 6):

  DRAFT -> ENABLED -> RUNNING -> OBSERVED
        -> COMPLETED / FAILED -> AWAITING_HUMAN_ACTION

This module provides the trigger grammar and the deterministic state machine. It
does not add a new scheduler process; the existing goal scheduler / GitHub
Actions cadence remains the timing source (AEAS section 20: cadence, schedule,
dispatch, session, and task are distinct).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .contracts import BoundaryViolation, utc_now

#: Trigger kinds the grammar supports.
TRIGGER_KINDS: tuple[str, ...] = (
    "scheduled",
    "repository_event",
    "pr_event",
    "runtime_health",
    "manual",
    "external_event",
)

#: Deterministic automation states.
AUTOMATION_STATES: tuple[str, ...] = (
    "DRAFT",
    "ENABLED",
    "RUNNING",
    "OBSERVED",
    "COMPLETED",
    "FAILED",
    "AWAITING_HUMAN_ACTION",
)

#: Legal transitions in the automation state machine.
AUTOMATION_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"ENABLED", "AWAITING_HUMAN_ACTION"}),
    "ENABLED": frozenset({"RUNNING", "DRAFT", "AWAITING_HUMAN_ACTION"}),
    "RUNNING": frozenset({"OBSERVED", "FAILED"}),
    "OBSERVED": frozenset({"COMPLETED", "FAILED", "AWAITING_HUMAN_ACTION"}),
    "COMPLETED": frozenset(),
    "FAILED": frozenset({"AWAITING_HUMAN_ACTION", "ENABLED"}),
    "AWAITING_HUMAN_ACTION": frozenset({"DRAFT", "ENABLED"}),
}

#: States that only a human act may leave / enter terminally.
HUMAN_GATED_STATES: frozenset[str] = frozenset({"AWAITING_HUMAN_ACTION", "COMPLETED"})


@dataclass(frozen=True)
class AutomationTrigger:
    """The trigger clause of an automation."""

    kind: str
    detail: str = ""
    schedule: str | None = None  # cron expression when kind == scheduled
    event: str | None = None  # event key when kind is an event kind

    def __post_init__(self) -> None:
        if self.kind not in TRIGGER_KINDS:
            raise ValueError(f"unknown trigger kind '{self.kind}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "detail": self.detail,
            "schedule": self.schedule,
            "event": self.event,
        }


@dataclass
class Automation:
    """A native Arkadia automation definition."""

    automation_id: str
    subject_ref: str
    name: str
    state: str
    trigger: AutomationTrigger
    agent_role: str
    objective: str = ""
    tools: tuple[str, ...] = ()
    sandbox_write_allowed: bool = False
    notification_target: str = "glance"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.state not in AUTOMATION_STATES:
            raise ValueError(f"unknown automation state '{self.state}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "automation_id": self.automation_id,
            "subject_ref": self.subject_ref,
            "name": self.name,
            "state": self.state,
            "trigger": self.trigger.to_dict(),
            "agent_role": self.agent_role,
            "objective": self.objective,
            "tools": list(self.tools),
            "sandbox_write_allowed": self.sandbox_write_allowed,
            "notification_target": self.notification_target,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
            "grammar": [
                "TRIGGER",
                "AGENT",
                "TOOLS",
                "SANDBOX",
                "OUTPUT",
                "EVIDENCE",
                "NOTIFICATION",
                "HUMAN_GATE",
            ],
            "may_authorize": False,
            "human_gate_required": True,
        }


def assert_automation_transition(current: str, target: str) -> None:
    if current not in AUTOMATION_TRANSITIONS:
        raise BoundaryViolation(f"unknown automation state '{current}'")
    if target not in AUTOMATION_TRANSITIONS[current]:
        raise BoundaryViolation(f"illegal automation transition {current} -> {target}")


def make_automation(
    *,
    subject_ref: str,
    name: str,
    trigger: AutomationTrigger,
    agent_role: str,
    objective: str = "",
    tools: tuple[str, ...] = (),
    sandbox_write_allowed: bool = False,
    notification_target: str = "glance",
) -> Automation:
    return Automation(
        automation_id=f"AUT-{uuid.uuid4().hex[:12]}",
        subject_ref=subject_ref,
        name=name,
        state="DRAFT",
        trigger=trigger,
        agent_role=agent_role,
        objective=objective,
        tools=tools,
        sandbox_write_allowed=sandbox_write_allowed,
        notification_target=notification_target,
    )


def grammar_view() -> dict[str, Any]:
    """Describe the automation grammar and the human gate truthfully."""
    return {
        "grammar": [
            "TRIGGER",
            "AGENT",
            "TOOLS",
            "SANDBOX",
            "OUTPUT",
            "EVIDENCE",
            "NOTIFICATION",
            "HUMAN_GATE",
        ],
        "states": list(AUTOMATION_STATES),
        "trigger_kinds": list(TRIGGER_KINDS),
        "may_prepare_consequential_action": True,
        "may_authorize_consequential_action": False,
        "final_transition": "HUMAN_GATE",
    }
