"""EL-04 — artifact canvas model.

Artifacts are first-class Engineering Lab objects. This module defines the
artifact kinds, their attribution, and a renderer-agnostic view model.

Rendering reuses *existing* Arkadia renderers where possible (MarkdownViewer,
react-markdown) rather than introducing a second rendering architecture. The
backend only produces a truthful view descriptor: ``renderer`` names the
canonical surface a client should use, and ``available`` reports whether the
content is actually present. Nothing is fabricated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .contracts import utc_now

#: Supported artifact kinds (directive section 7).
ARTIFACT_KINDS: tuple[str, ...] = (
    "markdown",
    "code",
    "diff",
    "svg",
    "image",
    "diagram",
    "html",
    "pdf",
    "json",
    "log",
    "test_report",
    "screenshot",
    "terminal_stream",
    "browser_observation",
)

#: Canonical client renderer per kind. Reuses existing Arkadia surfaces.
RENDERER_BY_KIND: dict[str, str] = {
    "markdown": "MarkdownViewer",
    "code": "CodeSurface",
    "diff": "DiffSurface",
    "svg": "ImageSurface",
    "image": "ImageSurface",
    "diagram": "ImageSurface",
    "html": "HtmlPreviewFrame",
    "pdf": "DocumentSurface",
    "json": "JsonSurface",
    "log": "LogSurface",
    "test_report": "TestReportSurface",
    "screenshot": "ImageSurface",
    "terminal_stream": "TerminalSurface",
    "browser_observation": "BrowserObservationSurface",
}

#: Canvas actions available per kind (directive section 7). These are UI
#: affordances; none of them is an execution or authorization action.
CANVAS_ACTIONS: tuple[str, ...] = ("INSPECT", "COMPARE", "ANNOTATE", "EXPORT", "ATTACH", "ARCHIVE")


@dataclass(frozen=True)
class ArtifactView:
    """A renderer-agnostic artifact descriptor.

    Attribution is mandatory: every artifact traces to workspace, session,
    agent, run, and (where present) the Move and evidence set.
    """

    artifact_id: str
    subject_ref: str
    workspace_ref: str
    session_id: str
    run_id: str | None
    agent_id: str | None
    kind: str
    title: str
    content: Any = None
    mime_type: str | None = None
    evidence_refs: tuple[str, ...] = ()
    move_ref: str | None = None
    created_at: str = field(default_factory=utc_now)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.kind not in ARTIFACT_KINDS:
            raise ValueError(f"unknown artifact kind '{self.kind}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "subject_ref": self.subject_ref,
            "workspace_ref": self.workspace_ref,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "kind": self.kind,
            "title": self.title,
            "content": self.content,
            "mime_type": self.mime_type,
            "evidence_refs": list(self.evidence_refs),
            "move_ref": self.move_ref,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }


def make_artifact(
    *,
    subject_ref: str,
    workspace_ref: str,
    session_id: str,
    kind: str,
    title: str,
    content: Any = None,
    run_id: str | None = None,
    agent_id: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    move_ref: str | None = None,
    mime_type: str | None = None,
) -> ArtifactView:
    return ArtifactView(
        artifact_id=f"ART-{uuid.uuid4().hex[:12]}",
        subject_ref=subject_ref,
        workspace_ref=workspace_ref,
        session_id=session_id,
        run_id=run_id,
        agent_id=agent_id,
        kind=kind,
        title=title,
        content=content,
        mime_type=mime_type,
        evidence_refs=evidence_refs,
        move_ref=move_ref,
    )


def canvas_view(artifact: dict[str, Any]) -> dict[str, Any]:
    """Project a stored artifact into a truthful canvas view descriptor.

    ``available`` is ``False`` when no content is present. The client must not
    render a placeholder as if it were a real artifact.
    """
    kind = artifact.get("kind", "json")
    content = artifact.get("content")
    available = content not in (None, "", [], {})
    return {
        "artifact": artifact,
        "renderer": RENDERER_BY_KIND.get(kind, "JsonSurface"),
        "available": available,
        "kind": kind,
        "actions": list(CANVAS_ACTIONS),
        "unavailable_reason": "" if available else "no content captured for this artifact",
    }
