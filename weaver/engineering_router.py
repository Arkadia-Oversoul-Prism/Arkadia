"""Deterministic Engineering Router — trajectory → next legal move.

Does not invent moves, reorder, expand scope, merge, or deploy.
Dry-run by default.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

TRAJECTORY_PATH = Path("docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml")
EVIDENCE_DIR = Path("docs/control-plane/evidence")
ACTIVE_STATUSES = frozenset({"pending", "revision_required"})
TERMINAL_DONE = frozenset({"completed", "accepted", "merged"})


@dataclass
class RouteResult:
    status: str  # READY_FOR_REVIEW | NO_LEGAL_MOVE | BLOCKED | FAILED
    trajectory_id: str
    repository_sha: str
    session_id: str
    dry_run: bool
    next_move: dict[str, Any] | None
    blockers: list[str] = field(default_factory=list)
    plan: dict[str, Any] | None = None
    evidence_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    if not path.is_file():
        raise FileNotFoundError(f"trajectory missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "trajectory" not in data or "moves" not in data:
        raise ValueError("invalid trajectory structure")
    return data


def _repo_sha(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    if not head.is_file():
        return "UNKNOWN"
    ref = head.read_text().strip()
    if ref.startswith("ref:"):
        ref_path = repo_root / ".git" / ref.split(" ", 1)[1].strip()
        if ref_path.is_file():
            return ref_path.read_text().strip()[:40]
    return ref[:40]


def _move_done(move: dict[str, Any], completion_index: dict[str, str]) -> bool:
    mid = str(move.get("id", ""))
    st = str(move.get("status", "pending")).lower()
    if st in TERMINAL_DONE:
        return True
    if completion_index.get(mid) in TERMINAL_DONE | {"accepted"}:
        return True
    return False


def _load_completion_index(repo_root: Path) -> dict[str, str]:
    """Optional evidence of accepted moves: docs/control-plane/evidence/*/ACCEPT.json."""
    idx: dict[str, str] = {}
    evidence = repo_root / EVIDENCE_DIR
    if not evidence.is_dir():
        return idx
    for p in evidence.glob("**/ACCEPT.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            mid = data.get("move_id")
            if mid:
                idx[str(mid)] = str(data.get("status", "accepted"))
        except Exception:
            continue
    return idx


def select_next_move(
    trajectory: dict[str, Any],
    *,
    completion_index: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Deterministic first legal incomplete move. Never invents or reorders."""
    completion_index = completion_index or {}
    moves = trajectory.get("moves") or []
    blockers: list[str] = []
    by_id = {str(m.get("id")): m for m in moves if isinstance(m, dict)}

    for move in moves:
        if not isinstance(move, dict):
            continue
        mid = str(move.get("id", ""))
        st = str(move.get("status", "pending")).lower()
        if st not in ACTIVE_STATUSES and not (
            st in TERMINAL_DONE or completion_index.get(mid) in TERMINAL_DONE | {"accepted"}
        ):
            # unknown non-active status: skip unless pending-like
            if st not in ACTIVE_STATUSES:
                continue
        if _move_done(move, completion_index):
            continue
        if st not in ACTIVE_STATUSES:
            continue

        deps = move.get("depends_on") or []
        dep_block = False
        for d in deps:
            dm = by_id.get(str(d))
            if dm is None:
                blockers.append(f"{mid}: missing dependency {d}")
                dep_block = True
                break
            if not _move_done(dm, completion_index):
                dep_block = True
                break
        if dep_block:
            continue

        spec = move.get("spec")
        if not spec:
            blockers.append(f"{mid}: scope/spec missing")
            continue

        # authorization: trajectory-level status must allow review-gated execution
        traj_status = str((trajectory.get("trajectory") or {}).get("status", "")).lower()
        if "authorized" not in traj_status and traj_status not in (
            "authorized-for-review-gated-execution",
        ):
            # still allow if explicit authorized-for-review-gated-execution substring
            if "authorized" not in traj_status:
                blockers.append(f"{mid}: trajectory authorization invalid ({traj_status})")
                continue

        return move, blockers

    if not blockers:
        blockers.append("no legal pending move (all complete or dependencies unresolved)")
    return None, blockers


class EngineeringRouter:
    def __init__(
        self,
        repo_root: str | Path = ".",
        session_id: str | None = None,
        dry_run: bool = True,
        trajectory_path: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.session_id = session_id or f"engineering-{int(time.time())}"
        self.dry_run = dry_run
        self.trajectory_path = trajectory_path or (self.repo_root / TRAJECTORY_PATH)

    def run(self) -> dict[str, Any]:
        sha = _repo_sha(self.repo_root)
        try:
            data = _load_yaml(self.trajectory_path)
        except Exception as e:
            result = RouteResult(
                status="FAILED",
                trajectory_id="UNKNOWN",
                repository_sha=sha,
                session_id=self.session_id,
                dry_run=self.dry_run,
                next_move=None,
                blockers=[str(e)],
            )
            path = self._write_evidence(result)
            result.evidence_path = str(path)
            return result.to_dict()

        traj = data["trajectory"]
        tid = str(traj.get("id", "UNKNOWN"))
        completion = _load_completion_index(self.repo_root)
        move, blockers = select_next_move(data, completion_index=completion)

        if move is None:
            result = RouteResult(
                status="NO_LEGAL_MOVE",
                trajectory_id=tid,
                repository_sha=sha,
                session_id=self.session_id,
                dry_run=self.dry_run,
                next_move=None,
                blockers=blockers,
            )
        else:
            plan = self._plan(move)
            result = RouteResult(
                status="READY_FOR_REVIEW" if self.dry_run else "QUEUED",
                trajectory_id=tid,
                repository_sha=sha,
                session_id=self.session_id,
                dry_run=self.dry_run,
                next_move={
                    "id": move.get("id"),
                    "name": move.get("name"),
                    "status": move.get("status"),
                    "depends_on": move.get("depends_on") or [],
                    "spec": move.get("spec"),
                    "packet": move.get("packet"),
                },
                blockers=blockers,
                plan=plan,
            )

        path = self._write_evidence(result)
        result.evidence_path = str(path)
        return result.to_dict()

    def _plan(self, move: dict[str, Any]) -> dict[str, Any]:
        spec_rel = str(move.get("spec") or "")
        spec_path = self.repo_root / spec_rel
        spec_exists = spec_path.is_file()
        spec_preview = ""
        if spec_exists:
            text = spec_path.read_text(encoding="utf-8", errors="replace")
            spec_preview = text[:800]
        return {
            "move_id": move.get("id"),
            "spec_path": spec_rel,
            "spec_loaded": spec_exists,
            "dry_run": self.dry_run,
            "actions": [
                "LOAD trajectory + move spec",
                "ORIENT repository state",
                "PLAN minimum implementation within move scope",
                "EXECUTE only if dry_run=false and human authorized",
                "VERIFY tests",
                "EVIDENCE + STOP at review (no merge, no deploy)",
            ],
            "spec_preview": spec_preview,
            "forbidden": [
                "merge",
                "production_deploy",
                "trajectory_rewrite",
                "autonomous_next_move",
            ],
        }

    def _write_evidence(self, result: RouteResult) -> Path:
        out_dir = self.repo_root / EVIDENCE_DIR / self.session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "session-report.json"
        path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
        human = out_dir / "WEAVER-ENGINEERING-RUN.md"
        nm = result.next_move or {}
        human.write_text(
            "\n".join(
                [
                    "# WEAVER ENGINEERING RUN",
                    "",
                    f"Trajectory: {result.trajectory_id}",
                    f"Move: {nm.get('id', 'NONE')}",
                    f"Status: {result.status}",
                    f"Repository SHA: {result.repository_sha}",
                    f"Branch: (session; no auto branch in dry-run)",
                    f"Worker Session: {result.session_id}",
                    f"Dry-run: {result.dry_run}",
                    f"Files Changed: none" if result.dry_run else "Files Changed: (execution mode)",
                    f"Tests: n/a (orientation)" if result.dry_run else "Tests: see worker",
                    f"Acceptance: not evaluated (dry-run)" if result.dry_run else "Acceptance: pending verification",
                    f"Evidence: {path}",
                    f"Known Limitations: bootstrap orientation; no provider execution",
                    f"Next Legal Move: {nm.get('id', 'NONE')}",
                    f"Blockers: {', '.join(result.blockers) if result.blockers else 'none'}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Arkadia Engineering Router")
    p.add_argument("--repo", default=".")
    p.add_argument("--session", default=None)
    p.add_argument("--execute", action="store_true", help="disable dry-run (still no merge)")
    args = p.parse_args()
    r = EngineeringRouter(repo_root=args.repo, session_id=args.session, dry_run=not args.execute)
    print(json.dumps(r.run(), indent=2))
