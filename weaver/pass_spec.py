"""WEAVER-K0.1 — machine-readable PassSpec (human authorization object).

Model output is never treated as authorization.
"""
from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any


class PassSpecError(Exception):
    """Authorization or lineage violation."""


@dataclass
class PassSpec:
    pass_id: str
    objective: str
    base_sha: str
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    required_builds: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    commit_required: bool = True
    push_allowed: bool = True  # K0.1: terminal turns publish by default
    publication_required: bool = True
    human_approval_required: bool = True
    checkpoint_required: bool = True
    provider: str = "gemini"
    pass_type: str = "engineering"  # engineering | recon | blocked | no_change

    def validate_structure(self) -> None:
        if not self.pass_id or not str(self.pass_id).strip():
            raise PassSpecError("pass_id is required")
        if not self.objective or not str(self.objective).strip():
            raise PassSpecError("objective is required")
        if not self.base_sha or len(str(self.base_sha).strip()) < 7:
            raise PassSpecError("base_sha is required")
        if not self.allowed_paths:
            raise PassSpecError("allowed_paths must be non-empty")
        if "self_authorize" in (self.pass_id or "").lower():
            raise PassSpecError("self-authorization is forbidden")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PassSpec":
        if not isinstance(data, dict):
            raise PassSpecError("PassSpec must be a dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        spec = cls(**{k: v for k, v in data.items() if k in known})
        spec.validate_structure()
        return spec


def current_head(repo_root: str = ".") -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise PassSpecError(f"cannot resolve HEAD: {r.stderr.strip()}")
    return r.stdout.strip()


def current_origin_main(repo_root: str = ".") -> str | None:
    r = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def verify_lineage(spec: PassSpec, repo_root: str = ".") -> str:
    """Refuse to operate when HEAD does not match PassSpec.base_sha."""
    spec.validate_structure()
    head = current_head(repo_root)
    base = spec.base_sha.strip()
    if head == base or head.startswith(base) or (len(base) >= 7 and base.startswith(head[: len(base)])):
        return head
    raise PassSpecError(f"HEAD mismatch: HEAD={head} base_sha={base}")


def path_in_allowlist(path: str, allowed_paths: list[str]) -> bool:
    norm = path.replace("\\", "/").lstrip("./")
    for allowed in allowed_paths:
        a = allowed.replace("\\", "/").lstrip("./")
        if not a:
            continue
        if norm == a or norm.startswith(a.rstrip("/") + "/") or norm.startswith(a + "/"):
            return True
        if a.endswith("/") and norm.startswith(a):
            return True
    return False


def assert_paths_authorized(paths: list[str], spec: PassSpec) -> None:
    for p in paths:
        norm = p.replace("\\", "/").lstrip("./")
        for forbidden in spec.forbidden_paths:
            f = forbidden.replace("\\", "/").lstrip("./")
            if f and (norm == f or norm.startswith(f.rstrip("/") + "/") or norm.startswith(f)):
                raise PassSpecError(f"forbidden path: {p}")
        if not path_in_allowlist(p, spec.allowed_paths):
            raise PassSpecError(f"path not in allowed_paths: {p}")
