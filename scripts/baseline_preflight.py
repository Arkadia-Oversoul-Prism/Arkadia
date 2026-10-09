#!/usr/bin/env python3
"""Baseline reproducibility preflight (gate-hygiene).

A full-suite failing/error node set is only usable as a baseline if an
independent operator's environment reproduces the *same* set. Two environment
properties silently change that set while every command still looks correct:

  * a shallow clone. ``tests/test_agents_md_encoding_adjudication.py`` resolves
    its oracle revision with ``git show <ORACLE_REV>:AGENTS.md``; when the clone
    does not contain that revision the live-file tests *error* rather than skip,
    so the suite reports four extra nodes (the oracle-pinned adjudication tests).
  * a missing declared dependency. ``requirements.txt`` is the contract; an
    environment provisioned without it drops nodes pytest depends on. Measured:
    without ``pdfminer.six``, ``test_market_data.py::``
    ``test_nepc_unparseable_pdf_fails_closed_at_fetch_boundary`` fails on import;
    without ``pytest-asyncio`` the async tests collect but never await, turning
    passing boundary nodes into failures.

The defect this fixes: PASS 3 published a reproduction command
(``PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
--continue-on-collection-errors -rEf``) that, run verbatim in a shallow clone,
yields **21** failing/error nodes instead of the canonical **16**. Nothing in the
command was wrong -- the *environment* was. This module makes that precondition
explicit and checkable before a fingerprint is derived, so a subset fingerprint
cannot be mistaken for a regression and a depth-dependent fingerprint cannot be
mistaken for repository debt.

Read-only. Runs no tests, mutates nothing, never prints a token.

Usage:
    python scripts/baseline_preflight.py            # human-readable
    python scripts/baseline_preflight.py --json     # machine output

Exit status: 0 when no blocking finding, 1 when a finding would change the node
set, 2 on a usage/IO fault.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Revision pinned by `tests/test_agents_md_encoding_adjudication.py` as the clean
# oracle. Imported from the audit module rather than restated, so the preflight
# cannot drift from the test it describes.
sys.path.insert(0, str(REPO_ROOT))
from scripts.agents_md_encoding_audit import ORACLE_REV  # noqa: E402

REQUIREMENTS = REPO_ROOT / "requirements.txt"

# Distribution name -> importable module name, for the requirements that pytest
# exercises at *module or fixture scope* (so a missing one changes the node set).
# A requirement that only the application imports at run time (e.g. `uvicorn`) is
# not listed: pytest would report the same nodes with or without it.
IMPORT_NAME = {
    "pdfminer.six": "pdfminer.high_level",
    "pytest-asyncio": "pytest_asyncio",
    "jsonschema": "jsonschema",
    "python-docx": "docx",
    "beautifulsoup4": "bs4",
    "pyyaml": "yaml",
    "cryptography": "cryptography",
}

# Requirements that are exercised by pytest and therefore *node-set
# consequential* when absent. Measured against a live full-suite run (see the
# evidence document). A missing non-consequential requirement is reported but
# does not set the exit status.
NODE_SET_CONSEQUENTIAL = ("pdfminer.six", "pytest-asyncio")

# The deprecated module shadowed by the tracked package `weaver/autonomy/`. Its
# collection error (CE-01) is reserved to the sovereign; the preflight reports it
# so a reader does not attribute it to their own change.
CE01_MODULE = "weaver.autonomy"


def clone_is_shallow(repo: Path = REPO_ROOT) -> bool:
    """True when `git rev-parse --is-shallow-repository` reports `true`."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--is-shallow-repository"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return True  # cannot prove otherwise -> treat as shallow (fail-closed)
    return out.stdout.strip() == "true"


def oracle_revision_present(rev: str = ORACLE_REV, repo: Path = REPO_ROOT) -> bool:
    """True when the clone can resolve `rev` (i.e. the oracle is reachable)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", rev],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0


def missing_requirements(path: Path = REQUIREMENTS) -> dict[str, list[str]]:
    """Return {'retained': [...], 'omitted': [...]} of declared requirements.

    `retained` requirements cannot be import-checked (their distribution name has
    no module mapping, e.g. a bare name); they are reported so they are not
    silently treated as satisfied. `omitted` requirements are declared but not
    importable in the running interpreter.
    """
    retained: list[str] = []
    omitted: list[str] = []
    if not path.exists():
        return {"retained": [], "omitted": []}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # Normalise extras/pins: `uvicorn[standard]` -> `uvicorn`, `x==1` -> `x`.
        name = line.split("[", 1)[0].split("=", 1)[0].split(">", 1)[0].strip()
        if not name:
            continue
        module = IMPORT_NAME.get(name, IMPORT_NAME.get(name.lower()))
        if module is None:
            retained.append(name)
            continue
        if importlib.util.find_spec(module) is None:
            omitted.append(name)
    return {"retained": retained, "omitted": omitted}


def ce01_collision_present(module: str = CE01_MODULE) -> bool:
    """True when `module` is a tracked package shadowing a tracked `.py` module.

    The module-vs-package collision is the CE-01 collection error. Read from the
    filesystem (not by importing, which would itself raise): a directory package
    and a sibling module of the same name.
    """
    base = REPO_ROOT / module.replace(".", os.sep)
    return base.is_dir() and (base.parent / (base.name + ".py")).is_file()


def collect(repo: Path = REPO_ROOT) -> dict:
    """Assemble the preflight findings. Pure read; no mutation."""
    shallow = clone_is_shallow(repo)
    oracle = oracle_revision_present(repo=repo)
    reqs = missing_requirements()
    consequential = [r for r in reqs["omitted"] if r in NODE_SET_CONSEQUENTIAL]

    findings = []
    if shallow or not oracle:
        findings.append(
            {
                "id": "SHALLOW_CLONE",
                "blocking": True,
                "detail": (
                    f"oracle revision {ORACLE_REV} is not resolvable in this clone "
                    f"(shallow={shallow}); the live-file adjudication tests error "
                    "rather than skip, adding 4 nodes to the failing/error set. "
                    "Remedy: `git fetch --unshallow` (or a fetch that includes "
                    f"{ORACLE_REV})."
                ),
            }
        )
    for name in consequential:
        findings.append(
            {
                "id": "MISSING_REQUIREMENT",
                "blocking": True,
                "detail": (
                    f"declared requirement `{name}` is not importable; it is "
                    "node-set consequential (absent -> the failing/error set "
                    "changes). Remedy: install requirements.txt."
                ),
            }
        )
    for name in reqs["omitted"]:
        if name in NODE_SET_CONSEQUENTIAL:
            continue
        findings.append(
            {
                "id": "MISSING_REQUIREMENT_NONCONSEQUENTIAL",
                "blocking": False,
                "detail": f"declared requirement `{name}` is not importable.",
            }
        )
    if ce01_collision_present():
        findings.append(
            {
                "id": "CE01_COLLISION",
                "blocking": False,
                "detail": (
                    f"`{CE01_MODULE}` resolves to the tracked package, not the "
                    "tracked module -> 1 collection error. Sovereign-reserved; "
                    "not attributable to an unrelated change."
                ),
            }
        )

    return {
        "repo_root": str(repo),
        "clone_shallow": shallow,
        "oracle_rev": ORACLE_REV,
        "oracle_revision_present": oracle,
        "requirements_omitted": reqs["omitted"],
        "requirements_retained": reqs["retained"],
        "node_set_consequential_omitted": consequential,
        "ce01_collision": ce01_collision_present(),
        "findings": findings,
        "blocking_count": sum(1 for f in findings if f["blocking"]),
    }


def render(report: dict) -> str:
    lines = ["BASELINE REPRODUCIBILITY PREFLIGHT", ""]
    lines.append(f"  repo root            : {report['repo_root']}")
    lines.append(f"  clone shallow        : {report['clone_shallow']}")
    lines.append(
        f"  oracle {report['oracle_rev']}  : "
        f"{'present' if report['oracle_revision_present'] else 'ABSENT'}"
    )
    lines.append(
        f"  omitted requirements : {', '.join(report['requirements_omitted']) or '(none)'}"
    )
    lines.append(
        f"  node-set consequential omitted : "
        f"{', '.join(report['node_set_consequential_omitted']) or '(none)'}"
    )
    lines.append(f"  CE-01 collision      : {report['ce01_collision']}")
    lines.append("")
    if not report["findings"]:
        lines.append("  no findings — the node set is reproducible in this environment.")
    else:
        for f in report["findings"]:
            tag = "BLOCKING" if f["blocking"] else "note"
            lines.append(f"  [{tag}] {f['id']}: {f['detail']}")
    lines.append("")
    lines.append(
        f"  {report['blocking_count']} blocking finding(s). "
        + (
            "A fingerprint derived here would NOT describe the canonical node set."
            if report["blocking_count"]
            else "Fingerprint may be derived."
        )
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Baseline reproducibility preflight (read-only)."
    )
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        report = collect(Path(args.repo))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    return 1 if report["blocking_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
