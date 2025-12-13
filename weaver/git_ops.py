# -*- coding: utf-8 -*-
import subprocess
from .logger import get_logger
import os
import time
from typing import Dict

LOGGER = get_logger()


def run(cmd, *, check=True):
    LOGGER.info("Running command: %s", " ".join(cmd))
    return subprocess.run(cmd, check=check)


def _format_meta(meta: Dict[str, str] | None) -> str:
    if not meta:
        return ""
    parts = [f"{k}={v}" for k, v in meta.items()]
    return " | " + " | ".join(parts)


def commit_and_push(msg: str = "Arkadia Code Weaver update",
                    paths: list[str] | None = None,
                    meta: Dict[str, str] | None = None,
                    max_commit_size: int | None = None,
                    allowed_exts: list[str] | None = None,
                    sign_commit: bool | None = None) -> bool:
    """Commit and push with optional metadata and safety checks.

    - `meta` will be appended to the commit message in the form: " | key=value | key=value"
    - `max_commit_size` limits the total size of staged files (bytes); if exceeded the commit will be skipped.
    - `allowed_exts` is a list of file extensions (e.g. ['.py','.md']) which limits commits to those file types.
    - `sign_commit` will attempt to pass `-S` to `git commit` if True.
    """
    repo_root = os.environ.get("REPO_ROOT", ".")
    env_allowed = os.environ.get("COMMIT_FILE_EXT_WHITELIST")
    if allowed_exts is None and env_allowed:
        allowed_exts = [e.strip() for e in env_allowed.split(",") if e.strip()]

    env_max = os.environ.get("REPO_MAX_COMMIT_SIZE")
    if max_commit_size is None and env_max:
        try:
            max_commit_size = int(env_max)
        except Exception:
            max_commit_size = None

    if sign_commit is None:
        sign_flag = os.environ.get("WEAVER_GIT_SIGN", "false").lower() in ("1", "true", "yes")
    else:
        sign_flag = bool(sign_commit)

    add_cmd = ["git", "add", "--"]
    if paths:
        filtered = [p for p in paths if str(os.path.realpath(p)).startswith(str(os.path.realpath(repo_root)))]
        if not filtered:
            LOGGER.warning("No files to add inside REPO_ROOT; skipping add/commit")
            return False
        # Filter by allowed extensions if configured
        if allowed_exts:
            filtered = [p for p in filtered if any(p.endswith(ext) for ext in allowed_exts)]
            if not filtered:
                LOGGER.warning("No files with allowed extensions to add; skipping add/commit")
                return False
        add_cmd.extend(filtered)
    else:
        add_cmd.append(".")
    run(add_cmd)

    # Only commit if there are staged changes
    try:
        staged = subprocess.run(["git", "diff", "--staged", "--name-only"], capture_output=True, text=True, check=True)
        staged_files = [l.strip() for l in staged.stdout.splitlines() if l.strip()]
        if not staged_files:
            LOGGER.info("No staged changes to commit; skipping commit/push")
            return False
    except subprocess.CalledProcessError:
        LOGGER.exception("Failed to check staged files; attempting commit anyway")
        staged_files = []

    # Enforce allowed_exts for staged files as safety check
    if allowed_exts and staged_files:
        disallowed = [p for p in staged_files if not any(p.endswith(ext) for ext in allowed_exts)]
        if disallowed:
            LOGGER.warning("Staged files contain disallowed extensions; refusing to commit: %s", disallowed)
            return False

    # Enforce max commit size
    if max_commit_size and staged_files:
        total_size = 0
        for f in staged_files:
            try:
                fp = os.path.join(repo_root, f)
                total_size += os.path.getsize(fp)
            except Exception:
                LOGGER.warning("Failed to read size for %s; skipping size accounting", f)
        if total_size > max_commit_size:
            LOGGER.warning("Total staged size %s exceeds max_commit_size %s; refusing to commit", total_size, max_commit_size)
            return False

    # Build commit message with metadata
    md = {"ts": int(time.time())}
    if meta:
        md.update({k: str(v) for k, v in meta.items()})
    full_msg = msg + _format_meta(md)

    try:
        commit_cmd = ["git", "commit", "-m", full_msg]
        if sign_flag:
            commit_cmd.insert(2, "-S")
        run(commit_cmd)
    except subprocess.CalledProcessError as e:
        # If there are no changes to commit, this is okay; otherwise re-raise
        LOGGER.warning("Git commit failed: %s", e)
        return False
    LOGGER.info("Committed changes: %s", full_msg)
    try:
        run(["git", "push"])
        LOGGER.info("Pushed changes to origin")
        return True
    except subprocess.CalledProcessError:
        LOGGER.exception("Git push failed")
        return False


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


def last_commit_files(n: int = 1) -> list[str]:
    try:
        if n <= 0:
            return []
        # When n==1, diff HEAD~1 HEAD returns the last commit files
        res = subprocess.run(["git", "diff", "--name-only", f"HEAD~{n}", "HEAD"], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if not out:
            return []
        files = [l.strip() for l in out.splitlines() if l.strip()]
        return files
    except Exception:
        LOGGER.exception("Failed to read commit files")
        return []
