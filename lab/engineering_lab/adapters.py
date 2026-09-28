"""EL-05 — Google Tasks / Google Keep provider adapters.

Provider adapters, not hard-coded dependencies. Google data remains
Google-authoritative; Arkadia remains authoritative for its own engineering
state. The adapters map Engineering Lab state to task/note operations without
ever letting an external service become the authority for Arkadia state.

Truthfulness (directive section 8): if credentials or external configuration are
unavailable, the adapter reports ``UNAVAILABLE`` and performs no network call —
it never fabricates integration success.

Authentication is always explicit: the adapter reads a caller-supplied access
token or a named environment credential. It never silently reuses an ambient
credential.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from .contracts import utc_now

#: Engineering Lab state -> external task state mapping (one-directional export).
#: The mapping is descriptive; the reverse direction is never applied as
#: authority. A completed Google task never marks Arkadia work complete.
LAB_TO_TASK_STATE: dict[str, str] = {
    "PROPOSED": "needsAction",
    "AUTHORIZED": "needsAction",
    "QUEUED": "needsAction",
    "RUNNING": "needsAction",
    "VERIFYING": "needsAction",
    "READY_FOR_REVIEW": "needsAction",
    "COMPLETED": "completed",
}


@dataclass
class AdapterStatus:
    """Truthful integration status for an external provider."""

    provider: str
    state: str  # AVAILABLE | UNAVAILABLE | UNCONFIGURED | NOT_ATTEMPTED
    detail: str = ""
    credential_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "state": self.state,
            "detail": self.detail,
            "credential_source": self.credential_source,
        }


class TaskAdapter(Protocol):
    def status(self) -> AdapterStatus: ...

    def create_task(self, *, title: str, notes: str = "") -> dict[str, Any]: ...

    def update_task(self, task_id: str, *, patch: dict[str, Any]) -> dict[str, Any]: ...

    def complete_task(self, task_id: str) -> dict[str, Any]: ...


class NoteAdapter(Protocol):
    def status(self) -> AdapterStatus: ...

    def create_note(self, *, title: str, body: str) -> dict[str, Any]: ...

    def update_note(self, note_id: str, *, patch: dict[str, Any]) -> dict[str, Any]: ...


class _BaseGoogleAdapter:
    """Shared truthfulness + explicit-auth behaviour for Google adapters."""

    provider_name = "google"
    env_vars: tuple[str, ...] = ()

    def __init__(self, access_token: str | None = None) -> None:
        self._token = access_token
        self._credential_source: str | None = "argument" if access_token else None
        if not self._token:
            for var in self.env_vars:
                value = os.environ.get(var)
                if value:
                    self._token = value
                    self._credential_source = var
                    break

    def status(self) -> AdapterStatus:
        if not self._token:
            return AdapterStatus(
                provider=self.provider_name,
                state="UNCONFIGURED",
                detail="no explicit access token or named credential present",
            )
        return AdapterStatus(
            provider=self.provider_name,
            state="AVAILABLE",
            detail="explicit credential present; external calls not yet attempted",
            credential_source=self._credential_source,
        )

    def _require_credential(self) -> str:
        if not self._token:
            raise PermissionError(
                f"{self.provider_name} adapter has no explicit credential; "
                "integration is UNAVAILABLE (no fabrication)"
            )
        return self._token

    def _request(self, url: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
        import json

        token = self._require_credential()
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode()
                return {"ok": True, "status": resp.status, "data": json.loads(raw) if raw else {}}
        except urllib.error.HTTPError as exc:
            return {"ok": False, "status": exc.code, "error": exc.reason}
        except Exception as exc:  # pragma: no cover - network dependent
            return {"ok": False, "status": None, "error": str(exc)}

    def describe(self) -> dict[str, Any]:
        return self.status().to_dict()


class GoogleTasksAdapter(_BaseGoogleAdapter):
    """Google Tasks provider adapter.

    Endpoints follow the Google Tasks REST API. The adapter is constructed with
    an explicit token (or a named env credential) and reports UNAVAILABLE when
    none is present.
    """

    provider_name = "google_tasks"
    env_vars = ("GOOGLE_TASKS_ACCESS_TOKEN", "GOOGLE_ACCESS_TOKEN")
    BASE = "https://tasks.googleapis.com/tasks/v1"

    def create_task(self, *, title: str, notes: str = "", tasklist: str = "@default") -> dict[str, Any]:
        if not self._token:
            return {"state": "UNAVAILABLE", "detail": self.status().detail, "task": None}
        result = self._request(
            f"{self.BASE}/lists/{tasklist}/tasks",
            method="POST",
            body={"title": title, "notes": notes},
        )
        return {"state": "AVAILABLE" if result["ok"] else "UNAVAILABLE", "task": result.get("data"), "raw": result}

    def update_task(self, task_id: str, *, patch: dict[str, Any], tasklist: str = "@default") -> dict[str, Any]:
        if not self._token:
            return {"state": "UNAVAILABLE", "detail": self.status().detail, "task": None}
        result = self._request(
            f"{self.BASE}/lists/{tasklist}/tasks/{task_id}",
            method="PATCH",
            body=patch,
        )
        return {"state": "AVAILABLE" if result["ok"] else "UNAVAILABLE", "task": result.get("data"), "raw": result}

    def complete_task(self, task_id: str, *, tasklist: str = "@default") -> dict[str, Any]:
        return self.update_task(task_id, patch={"status": "completed"}, tasklist=tasklist)

    def attach_arkadia_reference(self, task_id: str, *, reference: str, tasklist: str = "@default") -> dict[str, Any]:
        """Attach an Arkadia provenance reference (URL/PR/session id) to a task."""
        if not self._token:
            return {"state": "UNAVAILABLE", "detail": self.status().detail, "task": None}
        existing = self._request(f"{self.BASE}/lists/{tasklist}/tasks/{task_id}")
        notes = (existing.get("data") or {}).get("notes", "") if existing["ok"] else ""
        merged = (notes + f"\n\nArkadia: {reference}").strip()
        return self.update_task(task_id, patch={"notes": merged}, tasklist=tasklist)

    def map_lab_state(self, lab_state: str) -> dict[str, Any]:
        """Describe the mapping from an Arkadia Lab state to a Google task state.

        One-directional: Google never becomes the authority for Arkadia state.
        """
        return {
            "lab_state": lab_state,
            "task_state": LAB_TO_TASK_STATE.get(lab_state, "needsAction"),
            "authority": "arkadia remains authoritative for its own engineering state",
        }


class GoogleKeepAdapter(_BaseGoogleAdapter):
    """Google Keep provider adapter.

    Keep has no broadly available public REST API; the adapter boundary is
    implemented and reports UNAVAILABLE unless an explicit endpoint/token is
    configured. This is an honest boundary, not a fabricated integration.
    """

    provider_name = "google_keep"
    env_vars = ("GOOGLE_KEEP_ACCESS_TOKEN",)

    def create_note(self, *, title: str, body: str) -> dict[str, Any]:
        if not self._token:
            return {
                "state": "UNAVAILABLE",
                "detail": "Google Keep has no public REST API; adapter boundary only",
                "note": None,
            }
        return {
            "state": "UNCONFIGURED",
            "detail": "no Keep endpoint configured; boundary implements create/update only",
            "note": None,
        }

    def update_note(self, note_id: str, *, patch: dict[str, Any]) -> dict[str, Any]:
        if not self._token:
            return {
                "state": "UNAVAILABLE",
                "detail": "Google Keep has no public REST API; adapter boundary only",
                "note": None,
            }
        return {
            "state": "UNCONFIGURED",
            "detail": "no Keep endpoint configured; boundary implements create/update only",
            "note": None,
        }


@dataclass
class AdapterRegistry:
    """Registry of external provider adapters with truthful status reporting."""

    adapters: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, adapter: Any) -> None:
        self.adapters[name] = adapter

    def status_all(self) -> dict[str, Any]:
        return {name: adapter.describe() for name, adapter in self.adapters.items()}

    def get(self, name: str) -> Any:
        return self.adapters.get(name)


def default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register("google_tasks", GoogleTasksAdapter())
    registry.register("google_keep", GoogleKeepAdapter())
    return registry


def describe_integrations() -> dict[str, Any]:
    """JSON-safe integration status for the Lab surface (directive section 14)."""
    registry = default_registry()
    return {
        "adapters": registry.status_all(),
        "generated_at": utc_now(),
        "note": "external services remain authoritative for their own data",
    }
