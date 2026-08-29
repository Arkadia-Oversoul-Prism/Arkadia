"""WEAVER-K8 — Durable engineering memory + continuation.

MEMORY ≠ AUTHORIZATION. HISTORY ≠ AUTHORIZATION. CHECKPOINT ≠ AUTHORIZATION.
A fresh process reconstructs knowledge and waits for a new PassSpec.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .pass_spec import current_head, current_origin_main
from .recon import recent_lineage

SCHEMA_VERSION = "1.0.0"
DEFAULT_REL = "data/weaver/continuation/current.json"


class ContinuityStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"


@dataclass
class WeaverContinuation:
    schema_version: str = SCHEMA_VERSION
    continuation_id: str = ""
    repository: dict[str, Any] = field(default_factory=dict)
    anchor: dict[str, Any] = field(default_factory=dict)
    last_pass: dict[str, Any] = field(default_factory=dict)
    objective: dict[str, Any] = field(default_factory=dict)
    scope: dict[str, Any] = field(default_factory=dict)
    proposal: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    publication: dict[str, Any] = field(default_factory=dict)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    next_action: str = "awaiting human authorization"
    authorization: dict[str, Any] = field(default_factory=dict)
    previous_session: dict[str, Any] = field(default_factory=dict)
    current_session: dict[str, Any] = field(default_factory=dict)
    generated_at: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeaverContinuation":
        if not isinstance(data, dict):
            raise ValueError("continuation must be a dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


def _default_decisions() -> list[dict[str, Any]]:
    return [
        {
            "id": "k2-key-pool",
            "statement": "K2 reuses api/key_pool.py for Gemini rotation.",
            "status": "accepted",
            "source": "docs/verification/WEAVER_K2.md",
        },
        {
            "id": "k7-delegate",
            "statement": "K7 delegates execution to K6 session conductor.",
            "status": "accepted",
            "source": "docs/verification/WEAVER_K7.md",
        },
        {
            "id": "no-autonomous-objectives",
            "statement": "Autonomous objectives are prohibited.",
            "status": "accepted",
            "source": "constitution",
        },
    ]


def _infer_last_pass_from_git(repo_root: str) -> dict[str, Any]:
    lineage = recent_lineage(repo_root, n=12)
    if not lineage:
        return {"pass_id": None, "capability": None, "commit_sha": None, "status": None}
    top = lineage[0]
    msg = top.get("message") or ""
    capability = None
    if "WEAVER-K" in msg:
        # e.g. WEAVER-K7: ...
        capability = msg.split(":", 1)[0].strip()
    return {
        "pass_id": capability,
        "capability": capability,
        "commit_sha": top.get("sha"),
        "status": "published",
        "message": msg,
        "source": "git_log",
    }


def build_continuation(
    *,
    repo_root: str = ".",
    previous_objective: str | None = None,
    allowed_paths: list[str] | None = None,
    forbidden_paths: list[str] | None = None,
    non_goals: list[str] | None = None,
    changed_files: list[str] | None = None,
    tests: list[str] | None = None,
    verification: str = "verified",
    limitations: list[str] | None = None,
    unresolved: list[str] | None = None,
    publication_status: str = "published",
    result_sha: str | None = None,
    remote_sha: str | None = None,
    proposal: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> WeaverContinuation:
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    last = _infer_last_pass_from_git(repo_root)
    cid = f"cont-{(result_sha or head or '')[:12]}"
    return WeaverContinuation(
        schema_version=SCHEMA_VERSION,
        continuation_id=cid,
        repository={"remote": "origin", "branch": "main"},
        anchor={
            "head_sha": head,
            "origin_sha": origin,
            "clean": True,
        },
        last_pass=last,
        objective={
            "previous_authorized_objective": previous_objective
            or (last.get("message") or ""),
        },
        scope={
            "allowed_paths": list(allowed_paths or []),
            "forbidden_paths": list(forbidden_paths or []),
            "non_goals": list(non_goals or ["Autonomous objectives", "Self-authorization"]),
        },
        proposal=dict(proposal or {}),
        plan=dict(plan or {}),
        execution={
            "changed_files": list(changed_files or []),
            "tests": list(tests or []),
            "builds": [],
            "verification": verification,
            "limitations": list(limitations or []),
        },
        publication={
            "required": True,
            "status": publication_status,
            "result_sha": result_sha or head,
            "remote_sha": remote_sha or origin,
        },
        decisions=_default_decisions(),
        unresolved=list(
            unresolved
            or [
                "CLI multi-step state is process-local",
                "Live multi-key 429 against production not always exercised",
            ]
        ),
        next_action="awaiting human authorization",
        authorization={
            "state": "NONE",
            "current_pass_authorized": False,
            "note": "MEMORY ≠ AUTHORIZATION. A new PassSpec is required to modify the repository.",
        },
        previous_session={
            "last_pass": last.get("capability"),
            "commit_sha": last.get("commit_sha"),
        },
        current_session={
            "authorization": "NONE",
            "next_action": "awaiting human authorization",
        },
        generated_at=int(time.time()),
    )


def write_continuation(cont: WeaverContinuation, repo_root: str = ".", rel: str = DEFAULT_REL) -> str:
    path = Path(repo_root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cont.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel.replace("\\", "/")


def load_continuation(repo_root: str = ".", rel: str = DEFAULT_REL) -> tuple[ContinuityStatus, WeaverContinuation | None, str]:
    """Return (status, record|None, message). Never grants authorization."""
    path = Path(repo_root) / rel
    if not path.is_file():
        return ContinuityStatus.MISSING, None, "no continuation artifact"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cont = WeaverContinuation.from_dict(data)
    except Exception as e:
        return ContinuityStatus.INVALID, None, f"invalid continuation: {e}"

    if not cont.schema_version or not cont.anchor:
        return ContinuityStatus.INVALID, cont, "missing schema or anchor"

    bound_head = (cont.anchor or {}).get("head_sha")
    bound_origin = (cont.anchor or {}).get("origin_sha")
    try:
        head = current_head(repo_root)
        origin = current_origin_main(repo_root)
    except Exception as e:
        return ContinuityStatus.INVALID, cont, f"cannot resolve git: {e}"

    if bound_head != head or (bound_origin is not None and origin is not None and bound_origin != origin):
        return (
            ContinuityStatus.STALE,
            cont,
            f"stale: bound head={bound_head} current={head}; bound origin={bound_origin} current={origin}",
        )

    # Force authorization fields on load — never trust stored "authorized=true"
    cont.authorization = {
        "state": "NONE",
        "current_pass_authorized": False,
        "note": "MEMORY ≠ AUTHORIZATION. Loaded continuation does not authorize mutation.",
    }
    cont.current_session = {
        "authorization": "NONE",
        "next_action": "awaiting human authorization",
    }
    cont.next_action = "awaiting human authorization"
    return ContinuityStatus.CURRENT, cont, "continuation matches current git state"


def reconstruct_fresh_session(repo_root: str = ".") -> dict[str, Any]:
    """Deterministic fresh-session summary. Never executes modifications."""
    status, cont, msg = load_continuation(repo_root)
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    out: dict[str, Any] = {
        "continuity_status": status.value,
        "message": msg,
        "repository_head": head,
        "repository_origin": origin,
        "authorization": {
            "state": "NONE",
            "current_pass_authorized": False,
            "note": "HISTORY ≠ AUTHORIZATION",
        },
        "next_action": "awaiting human authorization",
        "continuation": cont.to_dict() if cont else None,
    }
    return out
