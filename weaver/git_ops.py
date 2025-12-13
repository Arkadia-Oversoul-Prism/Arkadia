# -*- coding: utf-8 -*-
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
    # Only commit if there are staged changes
    try:
        staged = subprocess.run(["git", "diff", "--staged", "--name-only"], capture_output=True, text=True, check=True)
        if not staged.stdout.strip():
            LOGGER.info("No staged changes to commit; skipping commit/push")
            return
    except subprocess.CalledProcessError:
        LOGGER.exception("Failed to check staged files; attempting commit anyway")

    try:
        run(["git", "commit", "-m", msg])
    except subprocess.CalledProcessError as e:
        # If there are no changes to commit, this is okay; otherwise re-raise
        LOGGER.warning("Git commit failed: %s", e)
        return
    LOGGER.info("Committed changes: %s", msg)
    try:
        run(["git", "push"])
        LOGGER.info("Pushed changes to origin")
    except subprocess.CalledProcessError:
        LOGGER.exception("Git push failed")


def last_commit_messages(n: int = 1) -> list[str]:
    try:
        res = subprocess.run(["git", "log", f"-n", str(n), "--pretty=%B"], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if not out:
            return []
        # Git separates multiple commits by blank lines; split them
        commits = [c.strip() for c in out.split("\n\n") if c.strip()]
        return commits
    except Exception:
        LOGGER.exception("Failed to read git logs")
        return []
