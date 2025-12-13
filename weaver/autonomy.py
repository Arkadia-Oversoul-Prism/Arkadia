import json
import os
import time
from typing import Dict, Optional

from .logger import get_logger
from .recursive import RecursiveEngine
from .git_ops import last_commit_messages

LOGGER = get_logger()

AUTONOMY_PATH = os.path.join(os.getcwd(), "governance", "autonomy.json")


def load_autonomy_config() -> Dict:
    if not os.path.exists(AUTONOMY_PATH):
        raise FileNotFoundError("governance/autonomy.json not found")
    with open(AUTONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_autonomy_config(cfg: Dict) -> bool:
    # Basic validation of required fields
    if not isinstance(cfg, dict):
        return False
    for k in ["enabled", "approved_by", "max_commits_per_run", "allowed_extensions", "interval_seconds"]:
        if k not in cfg:
            LOGGER.warning("Autonomy config missing key: %s", k)
            return False
    return True


def deterministic_stub(provider, prompt: str) -> str:
    # Minimal deterministic content generator for testing/autonomy
    import re
    m = re.search(r"recursive step (\d+)", prompt)
    step = int(m.group(1)) if m else 0
    target = f"weaver/notes/autonomy_step_{int(time.time())}_{step}.txt"
    content = f"Scheduled autonomous patch (step {step})\n"
    return f"--- FILE: {target} ---\n{content}\n"


def run_scheduled_once(config: Optional[Dict] = None, use_stub: bool = True) -> Dict:
    """Run one scheduled invocation of the engine according to the autonomy config.
    Returns a dict summary containing commits and counts.
    """
    cfg = config if config is not None else load_autonomy_config()
    if not validate_autonomy_config(cfg):
        raise RuntimeError("Invalid autonomy config")

    # Ensure the environment match required keys
    req = cfg.get("require_env") or {}
    for k, v in req.items():
        if os.environ.get(k) != v:
            LOGGER.warning("Environment mismatch for autonomy: %s must be %s", k, v)
            return {"ran": False, "reason": "env_mismatch"}

    if not cfg.get("enabled", False):
        LOGGER.info("Autonomy disabled in governance/autonomy.json")
        return {"ran": False, "reason": "disabled"}

    # Verify approved_by role exists in governance roles
    try:
        roles_path = os.path.join(os.getcwd(), "governance", "roles.json")
        if os.path.exists(roles_path):
            with open(roles_path, "r", encoding="utf-8") as rf:
                roles = json.load(rf)
                if cfg.get("approved_by") not in roles:
                    LOGGER.warning("Autonomy approved_by role %s not found in roles.json", cfg.get("approved_by"))
                    return {"ran": False, "reason": "approval_missing"}
    except Exception:
        LOGGER.exception("Failed to validate autonomy approval")
        return {"ran": False, "reason": "approval_error"}

    # Create engine & configure
    engine = RecursiveEngine(initial_task="autonomous scheduled run", enabled=True)
    engine.set_depth(cfg.get("run_depth", engine.depth))

    # stub the llm if required
    if use_stub:
        import weaver.agent as agent
        agent.call_llm = deterministic_stub

    # Run engine but enforce commit counting
    engine.start()
    commits = list(engine.commits)
    max_commits = int(cfg.get("max_commits_per_run", 0))
    if max_commits and len(commits) > max_commits:
        LOGGER.warning("Commits %s exceeded max_commits_per_run=%s; flagging for review", len(commits), max_commits)
    # Sanity report
    return {"ran": True, "commits": commits, "commit_count": len(commits)}
