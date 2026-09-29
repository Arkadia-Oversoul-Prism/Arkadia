"""EL-06 — Android control plane view model.

The Android surface (existing ``arkadia-android/`` WebView shell and
``sonata-android/`` native client — both already layer-0 presentation) acts as a
portable control and observation plane. Execution stays on the bounded server;
Android never requires local execution.

This module produces a compact, mobile-shaped projection of the Engineering Lab
state. It is intentionally read-mostly: it exposes the capabilities the Android
client may initiate, but every initiation routes through the same authenticated
authorization boundary — Android-local code is never an authority layer.
"""

from __future__ import annotations

from typing import Any

from .contracts import HUMAN_ONLY

#: Conceptual capabilities the Android control plane exposes.
ANDROID_CAPABILITIES: tuple[str, ...] = (
    "view_active_runs",
    "inspect_current_action",
    "inspect_artifacts",
    "inspect_evidence",
    "inspect_pr_state",
    "receive_notifications",
    "initiate_authorized_run",
    "pause_hold",
    "request_review",
    "open_canvas",
    "voice_entry",
)

#: Capabilities that are observation-only (never initiate execution).
_READ_ONLY_CAPABILITIES = frozenset(
    {
        "view_active_runs",
        "inspect_current_action",
        "inspect_artifacts",
        "inspect_evidence",
        "inspect_pr_state",
        "receive_notifications",
        "open_canvas",
    }
)

#: Capabilities that require an existing human authorization to act.
_AUTHORIZATION_REQUIRED = frozenset({"initiate_authorized_run", "pause_hold", "request_review"})

#: Capabilities that are reserved for a future adapter boundary.
_DEFERRED = frozenset({"voice_entry"})


def android_capability_report() -> dict[str, Any]:
    """Truthful capability report for the Android control plane."""
    capabilities = []
    for cap in ANDROID_CAPABILITIES:
        if cap in _READ_ONLY_CAPABILITIES:
            state = "AVAILABLE"
        elif cap in _AUTHORIZATION_REQUIRED:
            state = "AUTHORIZATION_REQUIRED"
        elif cap in _DEFERRED:
            state = "DEFERRED"
        else:  # pragma: no cover - exhaustive
            state = "UNKNOWN"
        capabilities.append(
            {
                "capability": cap,
                "state": state,
                "human_only_never_exposed": sorted(HUMAN_ONLY & {cap}) or [],
            }
        )
    return {
        "surface": "android_control_plane",
        "execution_location": "bounded_server",
        "android_local_execution_required": False,
        "capabilities": capabilities,
        "authority": {
            "android_is_not_an_authority_layer": True,
            "merge_exposed": False,
            "deploy_exposed": False,
        },
    }


def android_session_projection(session_view: dict[str, Any]) -> dict[str, Any]:
    """Compact a full session view into a mobile-shaped observation payload."""
    session = session_view.get("session", {})
    runs = session_view.get("runs", [])
    current_run = runs[-1] if runs else None
    artifacts = session_view.get("artifacts", [])
    evidence = session_view.get("evidence", [])
    events = session_view.get("events", [])
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "objective": session.get("objective"),
        "agent_id": session.get("agent_id"),
        "workspace_ref": session.get("workspace_ref"),
        "current_action": (
            events[-1].get("event_type") if events else "NONE"
        ),
        "run_count": len(runs),
        "current_run_state": current_run.get("state") if current_run else None,
        "artifact_count": len(artifacts),
        "evidence_count": len(evidence),
        "human_decision_required": session_view.get("human_decision_required", False),
        "inspect": {
            "artifacts": [a.get("artifact_id") for a in artifacts],
            "evidence": [e.get("evidence_id") for e in evidence],
            "canvas_ref": f"/solspire/engineering-lab?session={session.get('session_id')}",
        },
    }
