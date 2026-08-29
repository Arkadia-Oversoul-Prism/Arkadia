"""Autonomy Guard — Cycle 9 + WEAVER-K0 allow-list support."""
from __future__ import annotations


class AutonomyGuard:
    def __init__(self, config: dict):
        self.config = config or {}

    def allowed(self) -> bool:
        if self.config.get("status") != "enabled":
            return False
        if self.config.get("kill_switch", {}).get("default", True):
            return False
        return True

    def path_allowed(self, path: str) -> bool:
        norm = path.replace("\\", "/").lstrip("./")
        for forbidden in self.config.get("forbidden_paths", []) or []:
            f = str(forbidden).replace("\\", "/").lstrip("./")
            if f and (norm == f or norm.startswith(f.rstrip("/") + "/") or norm.startswith(f)):
                return False
        allowed = self.config.get("allowed_paths") or []
        if allowed:
            for a in allowed:
                a = str(a).replace("\\", "/").lstrip("./")
                if not a:
                    continue
                if norm == a or norm.startswith(a.rstrip("/") + "/") or norm.startswith(a + "/"):
                    return True
                if a.endswith("/") and norm.startswith(a):
                    return True
            return False
        return True

    def check_conditions(self) -> dict:
        conditions = self.config.get("conditions", {}) or {}
        return {
            "tests_must_pass": conditions.get("tests_must_pass", False),
            "proposal_reviewed": conditions.get("proposal_reviewed", False),
            "human_present": conditions.get("human_present", False),
            "max_files_changed": conditions.get("max_files_changed", 5),
            "max_lines_changed": conditions.get("max_lines_changed", 300),
        }

    def can_write_files(self, num_files: int, num_lines: int) -> bool:
        conditions = self.check_conditions()
        if num_files > conditions["max_files_changed"]:
            return False
        if num_lines > conditions["max_lines_changed"]:
            return False
        return True

    @classmethod
    def from_pass_spec(cls, spec) -> "AutonomyGuard":
        return cls(
            {
                "status": "enabled",
                "kill_switch": {"default": False},
                "forbidden_paths": list(getattr(spec, "forbidden_paths", None) or []),
                "allowed_paths": list(getattr(spec, "allowed_paths", None) or []),
                "conditions": {
                    "tests_must_pass": True,
                    "max_files_changed": 50,
                    "max_lines_changed": 5000,
                },
            }
        )
