#!/usr/bin/env python3
"""Repository-level Arkadia Oversoul Prism language/coherence check.

This is a semantic guard, not a claim about runtime correctness. It checks that
documented surfaces identify themselves as Prism expressions and flags a small
set of obsolete identity claims.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

README_PATHS = sorted(ROOT.rglob("README.md"))
UI_PATHS = [
    ROOT / "web/public_prism/index.html",
    ROOT / "web/public_prism/src/App.tsx",
    ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx",
    ROOT / "web/public_prism/src/components/PrismInteriorShell.tsx",
    ROOT / "web/public_prism/src/pages/ArkadiaLandingPage.tsx",
    ROOT / "web/public_prism/src/pages/AboutArkadia.tsx",
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

def check_readmes() -> list[str]:
    errors: list[str] = []
    for path in README_PATHS:
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [m for m in REQUIRED_README_MARKERS if m not in text]
        if missing:
            errors.append(f"{path.relative_to(ROOT)}: missing {', '.join(missing)}")
        for pattern in FORBIDDEN_IDENTITY_PATTERNS:
            if re.search(pattern, text, re.I):
                errors.append(f"{path.relative_to(ROOT)}: forbidden identity language: {pattern}")
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
    errors = check_readmes() + check_ui()
    print(f"Prism coherence scan: {len(README_PATHS)} README(s), {len(UI_PATHS)} primary UI file(s)")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS — documented identity is Prism-native across the checked surfaces.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
