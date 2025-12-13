import importlib
import importlib.util
import os
import time
from typing import Dict

from .logger import get_logger
from .git_ops import last_commit_messages

LOGGER = get_logger()


class RecursiveEngine:
    """Minimal scaffold for Arkadia Recursive Engine.

    Responsibilities:
    - Validate core weaver modules are importable
    - Provide a controlled start/stop loop for multi-step operations
    - Read a small set of environment variables to tune operation
    """

    CORE_MODULES = [
        "weaver.agent",
        "weaver.llm",
        "weaver.fs",
        "weaver.git_ops",
        "weaver.prompts",
        "weaver.session_context",
        "weaver.user_profiles",
        "weaver.model_adapter",
    ]

    def __init__(self, initial_task: str = "", enabled: bool | None = None):
        self.initial_task = initial_task
        self.enabled = (
            bool(enabled)
            if enabled is not None
            else os.environ.get("ARKADIA_RECURSIVE_ENABLED", "false").lower() in ("1", "true", "yes")
        )
        self.depth = int(os.environ.get("ARKADIA_RECURSIVE_DEPTH", "3"))
        self.interval = float(os.environ.get("ARKADIA_RECURSIVE_INTERVAL", "1"))
        self._running = False
        self.logger = LOGGER
        # tracking state
        self.current_cycle = 0
        self.updates: list[str] = []
        self.commits: list[str] = []
        self.errors: list[str] = []
        self.metrics = {"cycles": []}  # store cycle runtime metrics

    def validate(self) -> Dict[str, str]:
        """Check if required modules are importable and report versions/status."""
        status = {}
        for mod in self.CORE_MODULES:
            # Prefer to find the module spec first to avoid executing import-time logic
            spec = importlib.util.find_spec(mod)
            if spec is None:
                status[mod] = "missing"
                continue
            try:
                # Try to import but capture runtime errors which may be caused by
                # missing API keys or runtime-only checks in the module.
                _mod = importlib.import_module(mod)
                status[mod] = "ok"
            except Exception as e:  # pragma: no cover - validation can vary
                status[mod] = f"present (import error: {type(e).__name__})"
        return status

    def ready(self) -> bool:
        """Return readiness flag: enabled and all core modules importable."""
        if not self.enabled:
            return False
        status = self.validate()
        # Consider the engine ready when ALL modules are present (findable).
        # Import-time errors (e.g., missing API keys) do not block readiness but
        # missing specs do.
        return all(v != "missing" for v in status.values())

    def run_step(self, step_index: int):
        """Run a single step of the recursive loop. Uses weaver.agent.run for simplicity."""
        from time import time
        start = time()
        try:
            from .agent import run as agent_run

            task = f"{self.initial_task} [recursive step {step_index}]"
            self.logger.info("Running step %s: %s", step_index, task)
            updated_files, commit_msg = agent_run(task)
            if updated_files:
                self.updates.extend(updated_files)
            if commit_msg:
                self.commits.append(commit_msg)
            return updated_files, commit_msg
        except Exception as e:
            self.logger.exception("Step %s failed: %s", step_index, e)
            self.errors.append(str(e))
            return [], None
        finally:
            duration = time() - start
            self.metrics.setdefault("cycles", []).append({"cycle": step_index, "duration": duration})
            self.logger.info("Step %s completed in %.2fs", step_index, duration)

    def start(self):
        """Execute a small, safe recursive loop. This intentionally respects `self.depth` and lies
        dormant if `enabled` is False.
        """
        if not self.enabled:
            self.logger.warning("Recursive engine not enabled; skipping start()")
            return
        self._running = True
        self.current_cycle = 0
        self.updates = []
        self.commits = []
        self.errors = []
        self.metrics = {"cycles": []}
        self.logger.info("Starting RecursiveEngine: depth=%s interval=%s", self.depth, self.interval)
        max_depth = int(os.environ.get("RECURSIVE_DEPTH", os.environ.get("ARKADIA_RECURSIVE_DEPTH", str(self.depth))))
        for i in range(1, max_depth + 1):
            if not self._running:
                break
            self.current_cycle = i
            updated_files, commit_msg = self.run_step(i)
            time.sleep(self.interval)
            # Stop condition: no updates or errors blocking progress
            if (not updated_files) and (not self.errors):
                self.logger.info("No updates in cycle %s; stopping early.", i)
                break
        self._running = False
        self.logger.info("RecursiveEngine completed %s cycles", self.current_cycle)

    def stop(self):
        """Signal the loop to stop gracefully."""
        self.logger.info("Stopping RecursiveEngine")
        self._running = False

    def set_depth(self, depth: int):
        """Set the engine depth and update environment if necessary."""
        self.logger.info("Setting RecursiveEngine depth: %s", depth)
        self.depth = int(depth)

    def report(self) -> dict:
        commits = list(self.commits)
        if not commits:
            commits = last_commit_messages(3)
        return {
            "cycle": self.current_cycle,
            "updates": list(self.updates),
            "commits": commits,
            "ready": self.ready(),
            "errors": list(self.errors),
            "metrics": self.metrics,
        }


__all__ = ["RecursiveEngine"]
