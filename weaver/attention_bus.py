"""Governed human-attention bus for Weaver state changes.

Arkadia remains canonical. This module only converts an already-produced
state/event into bounded human-facing delivery intents.

Delivery is downstream of governance:
  Arkadia state -> AttentionEvent -> policy router -> Tasks/Keep/Push/Studio.

No adapter is allowed to authorize, execute, merge, deploy, or promote evidence.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from weaver.engineering_router import CLEAN_STOP_BLOCKER

CHANNELS = ("tasks", "keep", "push", "workspace_studio")
DEFAULT_KEEP_FEED = "ARKANA // FIELD FEED"
DEFAULT_TASK_LIST = "@default"


@dataclass(frozen=True)
class AttentionEvent:
    event_id: str
    event_type: str
    source: str
    subject: str
    severity: str = "INFO"
    previous_state: str | None = None
    current_state: str | None = None
    claim: str | None = None
    evidence_refs: tuple[str, ...] = ()
    action_required: bool = False
    human_authority_required: bool = False
    task_delivery: bool = False
    keep_delivery: bool = True
    push_delivery: bool = False
    workspace_studio_delivery: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeliveryPlan:
    event_id: str
    channels: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_event(event: AttentionEvent) -> DeliveryPlan:
    channels: list[str] = []
    if event.task_delivery:
        channels.append("tasks")
    if event.keep_delivery:
        channels.append("keep")
    if event.push_delivery:
        channels.append("push")
    if event.workspace_studio_delivery:
        channels.append("workspace_studio")

    if event.human_authority_required:
        reason = "human authority boundary"
    elif event.severity in {"CRITICAL", "HIGH"}:
        reason = "high-salience state change"
    elif event.action_required:
        reason = "actionable state change"
    else:
        reason = "recordable state change"

    return DeliveryPlan(event.event_id, tuple(channels), reason)


class AttentionSink(Protocol):
    def deliver(self, event: AttentionEvent) -> dict[str, Any]:
        ...


class JsonlAttentionOutbox:
    """Durable local relay. Idempotent by event_id + channel."""

    def __init__(self, path: str | Path = "docs/control-plane/evidence/attention-events.jsonl"):
        self.path = Path(path)

    def append(self, event: AttentionEvent, plan: DeliveryPlan) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        known = self._known_keys()
        wrote = False
        with self.path.open("a", encoding="utf-8") as fh:
            for channel in plan.channels:
                key = f"{event.event_id}:{channel}"
                if key in known:
                    continue
                record = {
                    "delivery_key": key,
                    "event": event.to_dict(),
                    "channel": channel,
                    "status": "PENDING",
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
                fh.write(json.dumps(record, sort_keys=True) + "\n")
                wrote = True
        return wrote

    def _known_keys(self) -> set[str]:
        if not self.path.is_file():
            return set()
        keys: set[str] = set()
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                key = item.get("delivery_key")
                if key:
                    keys.add(str(key))
            except json.JSONDecodeError:
                continue
        return keys


class GoogleTasksAdapter:
    """Minimal Tasks REST adapter using caller-supplied OAuth."""

    endpoint = "https://tasks.googleapis.com/tasks/v1"

    def __init__(self, access_token: str, task_list: str = DEFAULT_TASK_LIST):
        if not access_token:
            raise ValueError("Google Tasks access token required")
        self.access_token = access_token
        self.task_list = task_list

    def deliver(self, event: AttentionEvent) -> dict[str, Any]:
        if not event.task_delivery:
            return {"status": "SKIPPED", "reason": "task delivery disabled"}

        body = json.dumps({
            "title": self._title(event),
            "notes": self._notes(event),
        }).encode("utf-8")
        url = f"{self.endpoint}/lists/{self.task_list}/tasks"
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "status": "DELIVERED",
                "provider": "google_tasks",
                "remote_id": payload.get("id"),
            }
        except urllib.error.HTTPError as exc:
            return {
                "status": "FAILED",
                "provider": "google_tasks",
                "http_status": exc.code,
                "error": exc.read().decode("utf-8", errors="replace")[:1000],
            }

    @staticmethod
    def _title(event: AttentionEvent) -> str:
        prefix = "AUTH" if event.human_authority_required else event.event_type.replace("_", " ")
        return f"{prefix}: {event.subject}"[:250]

    @staticmethod
    def _notes(event: AttentionEvent) -> str:
        lines = [
            f"Arkadia Event: {event.event_id}",
            f"Source: {event.source}",
            f"Severity: {event.severity}",
            f"State: {event.previous_state or 'UNKNOWN'} -> {event.current_state or 'UNKNOWN'}",
        ]
        if event.claim:
            lines += ["", "Claim:", event.claim]
        if event.evidence_refs:
            lines += ["", "Evidence:", *[f"- {ref}" for ref in event.evidence_refs]]
        if event.human_authority_required:
            lines += [
                "",
                "Human authority is required. Completing this task does not authorize execution.",
            ]
        return "\n".join(lines)


class WorkspaceStudioTriggerAdapter:
    """Fire one configured Workspace Studio custom starter event."""

    endpoint = "https://workspacestudio.googleapis.com/v1"

    def __init__(self, access_token: str, trigger_id: str):
        if not access_token or not trigger_id:
            raise ValueError("Workspace Studio access token and trigger_id required")
        self.access_token = access_token
        self.trigger_id = trigger_id

    def deliver(self, event: AttentionEvent) -> dict[str, Any]:
        if not event.workspace_studio_delivery:
            return {"status": "SKIPPED", "reason": "workspace studio delivery disabled"}

        payload = {
            "name": f"triggers/{self.trigger_id}",
            "requestId": event.event_id,
            "outputs": {
                "eventId": {"stringValues": [event.event_id]},
                "eventType": {"stringValues": [event.event_type]},
                "source": {"stringValues": [event.source]},
                "subject": {"stringValues": [event.subject]},
                "severity": {"stringValues": [event.severity]},
                "claim": {"stringValues": [event.claim or ""]},
                "humanAuthorityRequired": {
                    "stringValues": [str(event.human_authority_required).lower()]
                },
            },
        }
        request = urllib.request.Request(
            f"{self.endpoint}/triggers/{self.trigger_id}:fire",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response.read()
            return {"status": "DELIVERED", "provider": "workspace_studio", "event_id": event.event_id}
        except urllib.error.HTTPError as exc:
            return {
                "status": "FAILED",
                "provider": "workspace_studio",
                "http_status": exc.code,
                "error": exc.read().decode("utf-8", errors="replace")[:1000],
            }


def _engineering_result_is_blocked(result: dict[str, Any]) -> bool:
    """Whether an engineering result carries an unresolved boundary.

    `FAILED` and `BLOCKED` are explicit. `NO_LEGAL_MOVE` is only a clean stop when it
    has nothing to report; when the router returned it *with* blockers it means the
    trajectory still carried a frontier the session could not route — a structural
    slip, an unrecognized move status, or an unresolved dependency. Projecting that as
    a plain state change suppressed the push and left the hourly stop invisible.

    `select_next_move` returns the clean-stop sentinel *as* a blocker, so a status-only
    or non-empty-blockers test would push it — turning every idle hourly session into a
    HIGH alert. A clean stop is the sentinel and nothing else; any other blocker is a
    real boundary.
    """
    status = str(result.get("status") or "UNKNOWN")
    if status in {"FAILED", "BLOCKED"}:
        return True
    if status != "NO_LEGAL_MOVE":
        return False
    blockers = [str(b) for b in (result.get("blockers") or [])]
    return bool(blockers) and any(b != CLEAN_STOP_BLOCKER for b in blockers)


def build_engineering_attention_event(result: dict[str, Any]) -> AttentionEvent:
    move = result.get("next_move") or {}
    execution = result.get("execution") or {}
    status = str(result.get("status") or "UNKNOWN")
    move_id = str(move.get("id") or "NONE")
    blocked = _engineering_result_is_blocked(result)
    event_type = "WEAVER_BLOCKED" if blocked else "WEAVER_STATE_CHANGED"
    high = blocked or not execution.get("ok", True)
    authority = bool(move.get("requires_human_authority", False)) or status in {
        "READY_FOR_REVIEW",
        "QUEUED",
    }
    return AttentionEvent(
        event_id=f"WEAVER-{result.get('session_id', 'UNKNOWN')}-{move_id}",
        event_type=event_type,
        source="weaver.engineering_worker",
        subject=move_id,
        severity="HIGH" if high else "INFO",
        current_state=status,
        claim=f"Weaver session {result.get('session_id', 'UNKNOWN')} reached {status}.",
        evidence_refs=tuple(ref for ref in [result.get("evidence_path")] if ref),
        action_required=authority or high,
        human_authority_required=authority,
        task_delivery=authority or high,
        keep_delivery=True,
        push_delivery=high or authority,
        workspace_studio_delivery=False,
    )
