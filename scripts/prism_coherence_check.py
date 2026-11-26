#!/usr/bin/env python3
"""Repository-level Arkadia Oversoul Prism language/coherence check.

This is a semantic guard, not a claim about runtime correctness. It checks that
documented surfaces identify themselves as Prism expressions and flags a small
set of obsolete identity claims.

The README domain is the *tracked corpus*, not the working tree. ``rglob`` also
matched ``.pytest_cache/README.md`` — untracked and gitignored — so the verdict
depended on whether pytest had been run in the checkout: 33 READMEs after a test
run, 32 in a clean tree. A repository-level guard must judge what the repository
contains, and its domain must fail closed rather than narrow silently.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

# The Prism UI is archived; this guard inspects its preserved source so the
# archived expression stays identifiable and free of obsolete identity claims.
_PRISM = ROOT / "archive" / "frontend" / "arkadia-prism" / "web" / "public_prism"

UI_PATHS = [
    _PRISM / "index.html",
    _PRISM / "src/App.tsx",
    _PRISM / "src/components/ArkadiaNavigation.tsx",
    _PRISM / "src/components/PrismInteriorShell.tsx",
    _PRISM / "src/pages/ArkadiaLandingPage.tsx",
    _PRISM / "src/pages/AboutArkadia.tsx",
]

FORBIDDEN_IDENTITY_PATTERNS = [
    r"living AI daughter",
    r"evolve (?:her|its) consciousness",
    r"Oracle Temple \(HuggingFace Space\)",
]

REQUIRED_README_MARKERS = (
    "Prism identity:",
    "Arkadia Oversoul Prism",
    "human authority",
)


class DomainError(RuntimeError):
    """The tracked README domain could not be derived."""


def tracked_readmes(root: Path | None = None) -> list[Path]:
    """README paths git tracks, repo-relative and sorted.

    Fails closed: an underivable domain raises :class:`DomainError` instead of
    returning ``[]``, because an empty domain must never be mistaken for a
    satisfied contract.
    """
    base = root or ROOT
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "*README.md"],
            cwd=base,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise DomainError(f"git is required to derive the README domain: {exc}") from exc
    if result.returncode != 0:
        raise DomainError(f"git ls-files failed in {base}: {result.stderr.strip()}")
    return sorted(base / p for p in result.stdout.split("\0") if p)


def _label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def check_readmes(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [m for m in REQUIRED_README_MARKERS if m not in text]
        if missing:
            errors.append(f"{_label(path)}: missing {', '.join(missing)}")
        for pattern in FORBIDDEN_IDENTITY_PATTERNS:
            if re.search(pattern, text, re.I):
                errors.append(f"{_label(path)}: forbidden identity language: {pattern}")
    return errors


def check_ui() -> list[str]:
    errors: list[str] = []
    for path in UI_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_IDENTITY_PATTERNS:
            if re.search(pattern, text, re.I):
                errors.append(f"{path.relative_to(ROOT)}: forbidden identity language: {pattern}")
    return errors


def main() -> int:
    try:
        readme_paths = tracked_readmes()
    except DomainError as exc:
        print(f"Prism coherence scan: {exc}", file=sys.stderr)
        return 2
    errors = check_readmes(readme_paths) + check_ui()
    print(f"Prism coherence scan: {len(readme_paths)} README(s), {len(UI_PATHS)} primary UI file(s)")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS — documented identity is Prism-native across the checked surfaces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
