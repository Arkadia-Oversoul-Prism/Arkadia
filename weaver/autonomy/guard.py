"""
Autonomy Guard — Cycle 9

Hard constraints on autonomy activation.
Kill-switch enabled by default.
"""


class AutonomyGuard:
    """Guard that enforces autonomy constraints."""

    def __init__(self, config: dict):
        """Initialize with autonomy contract."""
        self.config = config

    def allowed(self) -> bool:
        """
        Check if autonomy is allowed to act.

        Returns False if:
        - status is not "enabled"
        - kill_switch default is True
        """
        if self.config.get("status") != "enabled":
            return False

        if self.config.get("kill_switch", {}).get("default", True):
            return False

        return True

    def path_allowed(self, path: str) -> bool:
        """
        Check if path is allowed to be modified.

        Returns False if path is in forbidden_paths.
        """
        for forbidden in self.config.get("forbidden_paths", []):
            if path.startswith(forbidden):
                return False
        return True

    def check_conditions(self) -> dict:
        """
        Check all conditions for autonomy.

        Returns status of each condition.
        """
        conditions = self.config.get("conditions", {})
        return {
            "tests_must_pass": conditions.get("tests_must_pass", False),
            "proposal_reviewed": conditions.get("proposal_reviewed", False),
            "human_present": conditions.get("human_present", False),
            "max_files_changed": conditions.get("max_files_changed", 5),
            "max_lines_changed": conditions.get("max_lines_changed", 300),
        }

    def can_write_files(self, num_files: int, num_lines: int) -> bool:
        """
        Check if change volume is within limits.

        Returns False if exceeds configured thresholds.
        """
        conditions = self.check_conditions()
        if num_files > conditions["max_files_changed"]:
            return False
        if num_lines > conditions["max_lines_changed"]:
            return False
        return True
