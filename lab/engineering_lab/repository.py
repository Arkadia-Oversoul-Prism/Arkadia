"""AEAS-01 P0.3 — read-only repository and change inspection for the Lab.

The operator must be able to see the repository a bounded run executes against
*before* deciding anything: which branch, which source revision, what the
working tree actually changes, and the real diff. The Lab surface previously
carried no repository reading at all, so "inspect changes" had no native
surface — this module is that reading.

Everything here is an observation. It runs through the same bounded, read-only
git boundary bounded execution uses (``Sandbox`` with ``enforce_git_read_only``
plus the closed L1 terminal grammar), so inspection cannot become a mutation:
no checkout, no stage, no fetch, no write, no push.

Truthfulness rules (directive sections 1, 2 and 14):

* A git call that fails yields ``status="unavailable"`` **with the reason**. It
  never yields ``clean=True``: an unobserved working tree is UNKNOWN, not clean.
* ``repository.clean`` is ``None`` unless ``git status --porcelain`` actually
  ran and printed; ``changes.count`` is ``None`` when the read failed, never 0.
* Diff text is bounded and reports ``truncated`` when it was cut. A diff reads
  ``empty`` only when the read itself succeeded and printed nothing.
* An empty inventory reads ``clean: True`` only because git ran and printed
  nothing — that is the difference between an observation and an assumption.
"""

from __future__ import annotations

from typing import Any

from ..observatory.git import repository_state
from .contracts import utc_now
from .sandbox import Sandbox, SandboxError, SandboxPolicy

#: Response schema tag, so a projection can refuse a shape it does not know.
SCHEMA = "arkadia.lab.repository/1"

#: Bounds. The sandbox already caps captured output; these cap what the surface
#: renders, so one enormous diff cannot become the page.
MAX_DIFF_CHARS = 120_000
MAX_CHANGES = 400

#: ``git status --porcelain`` ``XY`` code -> human label. The raw code is always
#: carried alongside, so a code outside this table is *shown*, not hidden behind
#: a confident-looking guess: the fallback label says so.
_CHANGE_LABELS: dict[str, str] = {
    "??": "untracked",
    "!!": "ignored",
    " M": "modified",
    "M ": "modified",
    "MM": "modified",
    "AM": "modified",
    "FM": "modified",
    "A ": "added",
    " A": "added",
    "D ": "deleted",
    " D": "deleted",
    "AD": "deleted",
    "MD": "deleted",
    "R ": "renamed",
    " R": "renamed",
    "RM": "renamed",
    "RD": "renamed",
    "C ": "copied",
    " C": "copied",
    "CC": "copied",
    "DD": "conflicted",
    "AA": "conflicted",
    "UU": "conflicted",
    "AU": "conflicted",
    "UA": "conflicted",
    "DU": "conflicted",
    "UD": "conflicted",
}

#: Codes that count as "staged" / "unstaged". The space means *unchanged in
#: that half*, and ``?``/``!`` are untracked/ignored entries: they are
#: working-tree facts, but nothing is staged and no tracked file is modified.
_UNCHANGED_CHARS = frozenset(" ?!")


def label_for(code: str) -> str:
    """Human label for a two-character porcelain code, honestly fallback-ed."""
    if len(code) < 2:
        return "unclassified"
    return _CHANGE_LABELS.get(code, "unclassified")


def parse_porcelain(
    stdout: str, *, limit: int = MAX_CHANGES
) -> tuple[list[dict[str, Any]], bool]:
    """Parse ``git status --porcelain`` into bounded, labelled change entries.

    Returns ``(entries, truncated)``. Renames carry both paths (``old -> new``),
    so a rename is inspectable rather than reported as a mystery path.
    """
    entries: list[dict[str, Any]] = []
    truncated = False
    for line in stdout.splitlines():
        if not line.strip():
            continue
        if len(entries) >= limit:
            truncated = True
            break
        padded = line.ljust(3)
        code = padded[:2]
        path_part = line[3:].strip() if len(line) > 3 else ""
        original: str | None = None
        path = path_part
        if code[0] in "RC" and " -> " in path_part:
            original, path = path_part.split(" -> ", 1)
        entries.append(
            {
                "code": code,
                "label": label_for(code),
                "path": path,
                "original_path": original,
                "staged": code[0] not in _UNCHANGED_CHARS,
                "unstaged": code[1] not in _UNCHANGED_CHARS,
            }
        )
    return entries, truncated


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "text": "",
        "chars": 0,
        "truncated": False,
    }


def _failure_reason(result: dict[str, Any]) -> str:
    raw = result.get("stderr") or result.get("reason") or "git command failed"
    return str(raw).strip()[:400] or "git command failed"


def _observe_changes(sandbox: Sandbox, *, limit: int) -> dict[str, Any]:
    try:
        result = sandbox.git(["status", "--porcelain"])
    except SandboxError as exc:
        # NOT clean, NOT empty: the read did not happen.
        return {
            "status": "unavailable",
            "reason": str(exc)[:400],
            "files": [],
            "count": None,
            "truncated": False,
        }
    if not result.get("ok"):
        return {
            "status": "unavailable",
            "reason": _failure_reason(result),
            "files": [],
            "count": None,
            "truncated": False,
        }
    stdout = result.get("stdout", "") or ""
    files, truncated = parse_porcelain(stdout, limit=limit)
    # `count` is what git printed, not what the capped list carries: the cap is
    # on rendering, never on the reading.
    total = sum(1 for line in stdout.splitlines() if line.strip())
    return {
        "status": "observed",
        "reason": None,
        "files": files,
        "count": total,
        "truncated": truncated,
    }


def _observe_diff(sandbox: Sandbox, argv: list[str], *, max_chars: int) -> dict[str, Any]:
    try:
        result = sandbox.git(argv)
    except SandboxError as exc:
        return _unavailable(str(exc)[:400])
    if not result.get("ok"):
        return _unavailable(_failure_reason(result))
    text = result.get("stdout", "") or ""
    truncated = bool(result.get("truncated"))
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
    return {
        "status": "observed" if text else "empty",
        "reason": None,
        "text": text,
        "chars": len(text),
        "truncated": truncated,
    }


def _short_head(head: Any) -> str | None:
    return head[:12] if isinstance(head, str) and head else None


def observe_repository(
    root: str,
    *,
    max_diff_chars: int = MAX_DIFF_CHARS,
    max_changes: int = MAX_CHANGES,
) -> dict[str, Any]:
    """Observe branch, source revision, change inventory and diff under *root*.

    Pure observation: the only commands issued are read-only git subcommands
    inside a read-only :class:`Sandbox`. A failure anywhere degrades that one
    section to ``unavailable`` with its reason; it never degrades into a
    healthy-looking default.
    """
    state = repository_state(root)
    observation: dict[str, Any] = {
        "schema": SCHEMA,
        "observed_at": utc_now(),
        "repository": {
            "branch": state.get("branch"),
            "head": state.get("head"),
            "short_head": _short_head(state.get("head")),
            "remote": state.get("remote"),
            "remote_redacted": bool(state.get("remote_redacted")),
            "status": state.get("status"),
            "reason": state.get("reason"),
            # UNKNOWN until an actual status read says otherwise.
            "clean": None,
        },
        "boundary": (
            "read-only git observation through the bounded sandbox: no stage, "
            "checkout, fetch, write, or push is performed"
        ),
    }

    try:
        sandbox = Sandbox(
            SandboxPolicy(
                root=root,
                write_allowed=False,
                command_allowlist=("git",),
                enforce_git_read_only=True,
                enforce_command_grammar=True,
            )
        )
    except Exception as exc:  # any root failure is itself a reading, not a crash
        observation["changes"] = {
            "status": "unavailable",
            "reason": f"sandbox unavailable: {exc}"[:400],
            "files": [],
            "count": None,
            "truncated": False,
        }
        observation["diff"] = {
            "unstaged": _unavailable(f"sandbox unavailable: {exc}"),
            "staged": _unavailable(f"sandbox unavailable: {exc}"),
        }
        return observation

    changes = _observe_changes(sandbox, limit=max_changes)
    observation["changes"] = changes
    if changes["status"] == "observed":
        observation["repository"]["clean"] = changes["count"] == 0

    observation["diff"] = {
        "unstaged": _observe_diff(sandbox, ["diff"], max_chars=max_diff_chars),
        "staged": _observe_diff(sandbox, ["diff", "--cached"], max_chars=max_diff_chars),
    }
    return observation
