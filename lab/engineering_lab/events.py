"""EL-01 / EL-03 — live agent event stream.

A bounded run emits :class:`AgentEvent` records as it executes. This module
provides:

  * a monotonic per-session sequence,
  * an in-process observer/subscription bus (the live "streaming" surface the
    Canvas consumes),
  * a durable append log so a later reconstruct can replay what happened
    without trusting chat memory.

The bus carries *telemetry*, never authority. Subscribing to the stream grants
no execution capability.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from .models import AGENT_EVENT_TYPES, AgentEvent

_DEFAULT_LOG = os.path.join(
    os.environ.get("ENGINEERING_LAB_DATA_DIR", "data/engineering_lab"),
    "agent_events.jsonl",
)


class EventStream:
    """Per-session live event bus with a durable append log.

    Thread-safe. Persistence is best-effort: if the log cannot be written the
    event is still delivered to live observers and the failure is recorded on
    the event payload rather than raised into the run.
    """

    def __init__(self, log_path: str | None = None) -> None:
        self._log_path = Path(log_path or _DEFAULT_LOG)
        self._lock = threading.Lock()
        self._sequences: dict[str, int] = {}
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []

    # -- subscription ---------------------------------------------------------

    def subscribe(self, callback: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        """Register a live observer. Returns an unsubscribe callable."""
        with self._lock:
            self._subscribers.append(callback)

        def _unsubscribe() -> None:
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return _unsubscribe

    # -- emission -------------------------------------------------------------

    def emit(
        self,
        *,
        session_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> AgentEvent:
        if event_type not in AGENT_EVENT_TYPES:
            raise ValueError(f"unknown agent event type '{event_type}'")
        with self._lock:
            seq = self._sequences.get(session_id, 0) + 1
            self._sequences[session_id] = seq
            event = AgentEvent(
                event_id=f"AEV-{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                run_id=run_id,
                event_type=event_type,
                payload=dict(payload or {}),
                sequence=seq,
            )
            record = event.to_dict()
            persisted_error = self._append(record)
            if persisted_error:
                record["persist_error"] = persisted_error
            for callback in list(self._subscribers):
                try:
                    callback(record)
                except Exception:  # pragma: no cover - observer must not break runs
                    continue
        return event

    def _append(self, record: dict[str, Any]) -> str | None:
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
            return None
        except Exception as exc:  # pragma: no cover - defensive
            return str(exc)

    # -- reconstruction -------------------------------------------------------

    def replay(self, session_id: str) -> list[dict[str, Any]]:
        """Return the durable event log for a session, in order."""
        if not self._log_path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._log_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("session_id") == session_id:
                    records.append(record)
        records.sort(key=lambda r: r.get("sequence", 0))
        return records


_GLOBAL_STREAM: EventStream | None = None
_GLOBAL_LOCK = threading.Lock()


def get_event_stream() -> EventStream:
    """Return the process-wide event stream singleton."""
    global _GLOBAL_STREAM
    with _GLOBAL_LOCK:
        if _GLOBAL_STREAM is None:
            _GLOBAL_STREAM = EventStream()
        return _GLOBAL_STREAM
