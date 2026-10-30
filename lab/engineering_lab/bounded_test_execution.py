"""P0.4 — the bounded containerized test-execution contract.

The Engineering Lab may run a test suite. It may not run a shell.

This module is the single, reviewable place where that promise is defined:

* **Command allowlist.** A ``test`` operation never carries its own argv. It
  resolves against the pinned :data:`TEST_COMMAND_ALLOWLIST`, so no client,
  model, or session can turn "run the tests" into "run this binary". The
  operator may re-point the suite with ``ENGINEERING_LAB_TEST_COMMAND``, but
  only to a command whose argv still matches an allowlisted prefix.
* **Target rule.** The only caller-controlled input is an optional test
  selector (a path or a node id). It is validated here, before it can reach
  argv, so option injection and traversal are refused up front.
* **Resource envelope.** The timeout handed to the container boundary is
  bounded to the same 1–900 second window that ``run_isolated`` enforces.

Nothing here executes anything. Execution happens only through
``Sandbox.run_test``, which requires a containerized policy and delegates to
the Solspire container boundary: digest-pinned image, ``--network=none``,
read-only root filesystem, all capabilities dropped, ``no-new-privileges``,
pid/memory/cpu limits, a non-root uid, and output bounded at capture. Host
execution of an allowlisted test command is deliberately impossible — the L1
terminal grammar stays closed and this module never routes around it.
"""

from __future__ import annotations

import os
import re
import shlex
from typing import Sequence

from .contracts import BoundaryViolation

#: The operation token a bounded task uses to request test execution.
TEST_OPERATION = "test"

#: The explicit command allowlist: argv prefixes a ``test`` operation may run.
#: Widening it is an operator act — a reviewable diff to this file — never a
#: caller choice. No entry spawns a shell, and nothing here is a mutation
#: capability on its own.
TEST_COMMAND_ALLOWLIST: tuple[tuple[str, ...], ...] = (
    ("python", "-m", "pytest"),
    ("python", "-m", "unittest"),
    ("pytest",),
    ("node", "--test"),
    ("npm", "test"),
    ("pnpm", "test"),
    ("yarn", "test"),
    ("bun", "test"),
    ("cargo", "test"),
    ("go", "test"),
)

#: What runs when the operator has not re-pointed the suite.
DEFAULT_TEST_COMMAND: tuple[str, ...] = ("python", "-m", "pytest", "-q")

#: Operator override for the test command. Still allowlist-checked on read.
COMMAND_ENV = "ENGINEERING_LAB_TEST_COMMAND"
#: Operator override for the per-run timeout, in seconds.
TIMEOUT_ENV = "ENGINEERING_LAB_TEST_TIMEOUT_SECONDS"

DEFAULT_TIMEOUT_SECONDS = 120
MIN_TIMEOUT_SECONDS = 1
#: The container boundary refuses anything above this; clamp rather than
#: silently exceed it — and refuse a value the operator got wrong.
MAX_TIMEOUT_SECONDS = 900

MAX_TARGET_LENGTH = 200
#: Selectors are paths or node ids (``tests/test_a.py::test_b[1]``), never
#: options: the character class has no whitespace, quotes, ``$``, ``;`` or
#: ``&``, and ``validate_target`` refuses anything starting with ``-``.
_TARGET_RE = re.compile(r"^[A-Za-z0-9_./*=:+\-\[\]]+$")

#: Hard ceiling on argv length handed to the boundary.
MAX_COMMAND_LENGTH = 64


def configured_command() -> tuple[str, ...]:
    """The operator-pinned test command, as argv.

    The environment may re-point the suite, but it cannot escape the
    allowlist: a configuration that does not match a pinned prefix is a
    refusal, not a fallback to a default (a silent default would hide a
    misconfiguration from the operator who made it).
    """
    configured = os.environ.get(COMMAND_ENV)
    if configured is None:
        return DEFAULT_TEST_COMMAND
    if not configured.strip():
        # Set but blank: a misconfiguration, not an invitation to fall back to
        # the default silently — the operator who set it must see the refusal.
        raise BoundaryViolation(f"{COMMAND_ENV} is set but empty")
    try:
        argv = tuple(shlex.split(configured))
    except ValueError as exc:
        raise BoundaryViolation(f"{COMMAND_ENV} is not a parseable argv: {exc}") from exc
    if not argv:
        raise BoundaryViolation(f"{COMMAND_ENV} is set but empty")
    return argv


def assert_command_allowlisted(command: Sequence[str]) -> None:
    """Refuse anything that is not an allowlisted test command prefix."""
    argv = tuple(command)
    if not argv:
        raise BoundaryViolation("test command is empty")
    if any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv):
        raise BoundaryViolation("test command contains an invalid argument")
    if len(argv) > MAX_COMMAND_LENGTH:
        raise BoundaryViolation(
            f"test command exceeds {MAX_COMMAND_LENGTH} argv entries"
        )
    if not any(argv[: len(prefix)] == prefix for prefix in TEST_COMMAND_ALLOWLIST):
        raise BoundaryViolation(
            f"test command {list(argv)!r} does not match the pinned allowlist "
            f"{[list(p) for p in TEST_COMMAND_ALLOWLIST]}; a test operation can "
            "only run an allowlisted suite command"
        )


def validate_target(target: str) -> str:
    """Validate the one caller-controlled input: an optional test selector.

    Returns the cleaned selector (``""`` when absent). Anything that could
    steer the process rather than name a test — a leading option, an absolute
    path, a traversal, shell punctuation, an over-long selector — is refused
    here, before it can be concatenated onto argv.
    """
    if not target:
        return ""
    cleaned = str(target).replace("\\", "/")
    if len(cleaned) > MAX_TARGET_LENGTH:
        raise BoundaryViolation(
            f"test target exceeds {MAX_TARGET_LENGTH} characters"
        )
    if cleaned.startswith("-"):
        raise BoundaryViolation(
            "test target must not start with '-': a selector names a test, "
            "it never supplies an option"
        )
    if cleaned.startswith("/"):
        raise BoundaryViolation("test target must be relative to the workspace")
    parts = cleaned.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BoundaryViolation(
            "test target must be a normalized relative path without '..'"
        )
    if not _TARGET_RE.fullmatch(cleaned):
        raise BoundaryViolation(
            "test target contains characters outside the selector grammar"
        )
    return cleaned


def resolve_test_command(target: str = "") -> tuple[str, ...]:
    """The full argv a ``test`` operation runs: pinned command (+ selector)."""
    command = configured_command()
    assert_command_allowlisted(command)
    cleaned = validate_target(target)
    if cleaned:
        command = command + (cleaned,)
    assert_command_allowlisted(command)
    return command


def configured_timeout_seconds() -> int:
    """Bounded timeout for one containerized test run (1..900 seconds).

    Caller-independent: a bounded task cannot ask for a longer or shorter
    budget, only the operator's environment can, and even that is clamped to
    the window the container boundary accepts.
    """
    raw = os.environ.get(TIMEOUT_ENV, "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        seconds = int(raw)
    except ValueError as exc:
        raise BoundaryViolation(
            f"{TIMEOUT_ENV} must be an integer number of seconds, got {raw!r}"
        ) from exc
    if seconds < MIN_TIMEOUT_SECONDS or seconds > MAX_TIMEOUT_SECONDS:
        raise BoundaryViolation(
            f"{TIMEOUT_ENV} must be between {MIN_TIMEOUT_SECONDS} and "
            f"{MAX_TIMEOUT_SECONDS} seconds"
        )
    return seconds
