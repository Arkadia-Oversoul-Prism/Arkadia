"""Boundary guard: a root narrative document must not link to a missing path.

The root `*.md` files are the repository's front door. Measured on `main` @
`bb19aabd`, `README.md`'s "How to inspect Arkadia" list carried

    [web/public_prism/](web/public_prism/) — current frontend

but that tree was archived by `c081d200` (2026-10-11) and no longer exists; the
active console is `web/arkadia_console/`. A newcomer following the front door hit
a dead link *and* a false statement about which frontend is current. Nothing
judged it: `grep -rn "README.md" .github/workflows/` matched no gate, so the stale
link survived the archive move.

The invariant is stated over the whole root document set rather than the one file
the defect happened to be in, and the domain is derived from the tree at test
time, so a newly added root document is judged by the same rule.

Scope, stated rather than implied:

* only *relative* targets are repository paths. `http://`, `https://`, `mailto:`,
  `tel:` and in-page `#anchor` targets are not checked;
* a target is resolved relative to the document that contains it, and a leading
  `/` is treated as repository-root-relative (GitHub's rendering);
* fenced code blocks and inline code spans are not links and are excluded, so a
  document may show an example of a link without failing the guard.

Every detector carries a control, so a rewrite of this file cannot leave the
live assertion vacuously green.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "root-doc-link-integrity.yml"
GUARD = "tests/test_root_doc_link_integrity.py"

_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#")


def _strip_fenced_blocks(text: str) -> str:
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            kept.append("")
            continue
        kept.append("" if in_fence else line)
    return "\n".join(kept)


def iter_link_targets(text: str) -> list[str]:
    """Every inline markdown link destination outside code, in document order."""
    without_code = _INLINE_CODE.sub("", _strip_fenced_blocks(text))
    return [m.group(1).strip() for m in _LINK.finditer(without_code)]


def repository_target(raw: str) -> str | None:
    """The repository-relative destination, or ``None`` when it is not a path."""
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    tokens = target.split()
    if not tokens:
        return None
    target = tokens[0]
    if target.startswith(_EXTERNAL_PREFIXES):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return target or None


def broken_links(document: Path, root: Path | None = None) -> list[str]:
    """Relative targets in ``document`` that do not resolve inside ``root``."""
    base = root or ROOT
    text = document.read_text(encoding="utf-8", errors="replace")
    missing: list[str] = []
    for raw in iter_link_targets(text):
        target = repository_target(raw)
        if target is None:
            continue
        candidate = (
            base / target.lstrip("/") if target.startswith("/") else document.parent / target
        )
        if not candidate.exists():
            missing.append(target)
    return missing


def root_documents() -> list[Path]:
    return sorted(ROOT.glob("*.md"))


# ---------------------------------------------------------------------------
# Detector controls
# ---------------------------------------------------------------------------


def test_detector_flags_a_missing_relative_target(tmp_path: Path):
    """Negative control: the shape that reached `main` must be reported."""
    doc = tmp_path / "README.md"
    doc.write_text("[frontend](web/public_prism/) — current frontend\n", encoding="utf-8")
    assert broken_links(doc, tmp_path) == ["web/public_prism/"]


def test_detector_accepts_an_existing_relative_target(tmp_path: Path):
    """Positive control: an existing directory must not be reported."""
    (tmp_path / "web" / "arkadia_console").mkdir(parents=True)
    doc = tmp_path / "README.md"
    doc.write_text("[console](web/arkadia_console/)\n", encoding="utf-8")
    assert broken_links(doc, tmp_path) == []


def test_detector_ignores_external_anchors_and_code(tmp_path: Path):
    """Positive control: only repository paths are judged."""
    doc = tmp_path / "README.md"
    doc.write_text(
        "[site](https://example.com)\n"
        "[mail](mailto:a@b.example)\n"
        "[section](#verification-honesty)\n"
        "`[inline](missing-inline/)`\n"
        "```\n"
        "[example](missing-fenced/)\n"
        "```\n"
        "[root-relative](/web/arkadia_console/)\n",
        encoding="utf-8",
    )
    (tmp_path / "web" / "arkadia_console").mkdir(parents=True)
    assert broken_links(doc, tmp_path) == []


def test_the_domain_is_derived_from_the_tree_not_restated():
    """A new root document must enter the domain without editing this file."""
    assert root_documents(), "the repository declares root narrative documents"
    assert all(p.suffix == ".md" and p.parent == ROOT for p in root_documents())


# ---------------------------------------------------------------------------
# The live invariant
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("document", root_documents(), ids=lambda p: p.name)
def test_root_documents_link_only_to_paths_that_exist(document: Path):
    missing = broken_links(document)
    assert missing == [], (
        f"{document.name} links to path(s) that do not exist: {missing}; "
        "point the link at the tree that carries the content, or state the "
        "retired path in prose without linking it"
    )


def test_the_readme_links_the_active_console():
    """Pin the specific repair, not only the generic invariant."""
    readme = ROOT / "README.md"
    targets = [repository_target(raw) for raw in iter_link_targets(readme.read_text(encoding="utf-8"))]
    assert "web/arkadia_console/" in targets, (
        "README.md must link the active console at web/arkadia_console/"
    )


# ---------------------------------------------------------------------------
# The gate that executes this guard
# ---------------------------------------------------------------------------


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    block = workflow.get(True, workflow.get("on"))
    assert isinstance(block, dict), "the workflow declares an event mapping"
    return block


def test_the_gate_workflow_selects_every_input_the_guard_reads():
    """A filter that omits an input leaves that input change unjudged."""
    triggers = _triggers(_workflow())
    required = {"*.md", GUARD, f".github/workflows/{WORKFLOW.name}"}
    for event in ("pull_request", "push"):
        paths = set(triggers[event]["paths"])
        assert required <= paths, f"{event} filter omits {sorted(required - paths)}"
    assert "workflow_dispatch" in triggers, "the gate must be executable on demand"


def test_the_gate_workflow_executes_this_guard_and_can_fail():
    workflow = _workflow()
    steps = [
        step
        for job in (workflow.get("jobs") or {}).values()
        for step in (job.get("steps") or [])
        if isinstance(step, dict)
    ]
    executing = [s for s in steps if GUARD in (s.get("run") or "")]
    assert executing, f"no step runs {GUARD}"
    assert all(s.get("continue-on-error") is not True for s in executing), (
        "a masked step reports success whatever the guard found"
    )
