import subprocess
from .logger import get_logger

LOGGER = get_logger()


def run(cmd, *, check=True):
    LOGGER.info("Running command: %s", " ".join(cmd))
    return subprocess.run(cmd, check=check)


def commit_and_push(msg="Arkadia Code Weaver update", paths: list[str] | None = None):
    add_cmd = ["git", "add"]
    if paths:
        add_cmd.extend(paths)
    else:
        add_cmd.append(".")
    run(add_cmd)
    run(["git", "commit", "-m", msg])
    LOGGER.info("Committed changes: %s", msg)
    run(["git", "push"])
    LOGGER.info("Pushed changes to origin")
