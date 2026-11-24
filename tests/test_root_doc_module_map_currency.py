"""Boundary guard: a live root map must not advertise a ``web/`` surface that is absent.

``PROJECT_INDEX.md`` opens with a currency contract of its own:

    A map of the repository. The agent reads this instead of exploring the tree.
    Update when a new module is added. Never let it drift from the codebase.

Measured on ``main`` @ ``bb19aabd``, the map's Presentation and Configuration
blocks declared

    web/public_prism/                React/Vite SPA — npm run dev on port 5173
    web/public_prism/package.json    Frontend dependencies

but that tree was archived into ``archive/frontend/arkadia-prism/`` by
``c081d200`` (2026-10-11); the active console is ``web/arkadia_console/``. An
agent told to read the map "instead of exploring the tree" was therefore pointed
at a frontend that does not exist, and was never told the one that does. Nothing
judged it: the only root-document gate (``root-doc-link-integrity.yml``, #714)
reads inline markdown *links* and deliberately excludes fenced code blocks, and
this defect lives in a fenced block.

Scope, stated rather than implied:

* the document set is derived at test time from ``*.md`` at the repository root,
  so a newly added root document is judged by the same rule;
* a document carrying a generation marker (``Last generated:``) is a
  point-in-time record, not a live map, and is excluded — rewriting a dated
  snapshot to look current would contradict its own header;
* only *listed* entries inside fenced code blocks are claims. A document may
  discuss an archived surface in prose, or show one in an example, without
  failing;
* the check is existence, not correctness of the description. A live map that
  names a present tree passes even if its one-line summary is imperfect.

Every detector carries a control, so a rewrite of this file cannot leave the
live assertion vacuously green.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "root-doc-module-map.yml"
GUARD = "tests/test_root_doc_module_map_currency.py"
MAP = "PROJECT_INDEX.md"

_FENCE = re.compile(r"^\s*(```|~~~)")
_WEB_PATH = re.compile(r"(?:^|[\s`(])(web/[A-Za-z0-9_./-]+)")
_POINT_IN_TIME = "Last generated:"
_TRAILING = ".,;:)]}"

# Verbatim from `main` @ `bb19aabd`, the state this guard was written against.
PRE_REPAIR_SNIPPET = """\
```
web/public_prism/        React/Vite SPA — npm run dev on port 5173
  src/components/        UI components
  src/views/             Page views
  src/contexts/          React contexts (voice, oracle, auth)
```

```
web/public_prism/package.json   Frontend dependencies
```
"""


def fenced_blocks(text: str) -> list[str]:
    """Every fenced code block body, in document order."""
    blocks: list[str] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if _FENCE.match(line):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
            continue
        if current is not None:
            current.append(line)
    return blocks


def declared_web_surfaces(text: str) -> list[str]:
    """``web/...`` paths listed inside fenced code blocks, in document order."""
    found: list[str] = []
    for block in fenced_blocks(text):
        for line in block.splitlines():
            for token in _WEB_PATH.findall(line):
                token = token.rstrip(_TRAILING)
                if token and token not in found:
                    found.append(token)
    return found


def missing_surfaces(text: str, root: Path | None = None) -> list[str]:
    """Declared ``web/`` surfaces that do not exist in the tree."""
    base = root or ROOT
    return [p for p in declared_web_surfaces(text) if not (base / p).exists()]


def is_point_in_time(text: str) -> bool:
    return _POINT_IN_TIME in text


def live_map_documents(root: Path | None = None) -> list[Path]:
    """Root ``*.md`` documents that present themselves as current, not as snapshots."""
    base = root or ROOT
    return [
        path
        for path in sorted(base.glob("*.md"))
        if not is_point_in_time(path.read_text(encoding="utf-8", errors="replace"))
    ]


def triggers(workflow: dict) -> dict:
    # PyYAML resolves the bare `on` key to the boolean True.
    return workflow.get(True) or workflow.get("on") or {}


def workflow_paths(workflow: dict, event: str) -> list[str]:
    block = triggers(workflow).get(event) or {}
    return list(block.get("paths") or [])


def pytest_arguments(run: str) -> list[str] | None:
    """Arguments of the first *invoked* pytest command, else ``None``.

    ``echo pytest tests/x.py`` and a commented mention are not invocations: the
    word must be the command itself, or follow ``-m``.
    """
    joined = " ".join(line.split("#", 1)[0] for line in run.splitlines())
    try:
        tokens = shlex.split(joined)
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if token != "pytest":
            continue
        previous = tokens[index - 1] if index else ""
        if index == 0 or previous == "-m" or previous.endswith("/pytest"):
            return tokens[index + 1 :]
    return None


def run_steps(workflow: dict) -> list[dict]:
    return [
        step
        for job in (workflow.get("jobs") or {}).values()
        for step in (job.get("steps") or [])
    ]


def load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# The live invariant
# --------------------------------------------------------------------------


@pytest.mark.parametrize("document", live_map_documents(), ids=lambda p: p.name)
def test_a_live_root_map_declares_only_present_web_surfaces(document: Path) -> None:
    text = document.read_text(encoding="utf-8", errors="replace")
    assert missing_surfaces(text) == []


def test_the_map_names_the_active_console() -> None:
    """The positive half: dropping the live console must not read as a pass."""
    text = (ROOT / MAP).read_text(encoding="utf-8")
    assert "web/arkadia_console/" in declared_web_surfaces(text)


# --------------------------------------------------------------------------
# Controls — the detector must bite on the measured defect, and only on it
# --------------------------------------------------------------------------


def test_negative_control_the_pre_repair_map_is_reported() -> None:
    assert missing_surfaces(PRE_REPAIR_SNIPPET) == [
        "web/public_prism/",
        "web/public_prism/package.json",
    ]


def test_positive_control_a_map_of_present_surfaces_is_clean() -> None:
    clean = "```\nweb/arkadia_console/   active console\nweb/console/           retired\n```\n"
    assert missing_surfaces(clean) == []


def test_prose_mentions_are_not_claims() -> None:
    prose = "The former SPA lived at web/public_prism/ before it was archived.\n"
    assert missing_surfaces(prose) == []


def test_a_dated_snapshot_is_not_a_live_map(tmp_path: Path) -> None:
    snapshot = tmp_path / "SNAPSHOT.md"
    snapshot.write_text(
        "> Last generated: 2026-07-25.\n\n```\nweb/public_prism/\n```\n", encoding="utf-8"
    )
    assert live_map_documents(tmp_path) == []

    # Control: remove the marker and the same document is enrolled.
    snapshot.write_text("```\nweb/public_prism/\n```\n", encoding="utf-8")
    assert [p.name for p in live_map_documents(tmp_path)] == ["SNAPSHOT.md"]


# --------------------------------------------------------------------------
# Wiring — a guard no workflow executes is decoration
# --------------------------------------------------------------------------


def test_the_gate_exists_and_is_dispatchable() -> None:
    assert WORKFLOW.is_file()
    assert "workflow_dispatch" in triggers(load_workflow())


@pytest.mark.parametrize("event", ["pull_request", "push"])
def test_the_gate_selects_every_input_its_guard_reads(event: str) -> None:
    paths = workflow_paths(load_workflow(), event)
    # The guard reads root `*.md`, the `web/` tree, its own file, and this gate.
    for required in ("*.md", "web/**", GUARD, WORKFLOW.relative_to(ROOT).as_posix()):
        assert required in paths, f"{event} filter omits {required}"


def test_push_and_pull_request_filters_agree() -> None:
    workflow = load_workflow()
    assert workflow_paths(workflow, "push") == workflow_paths(workflow, "pull_request")


def test_the_gate_executes_the_guard() -> None:
    executed: list[str] = []
    for step in run_steps(load_workflow()):
        arguments = pytest_arguments(str(step.get("run") or ""))
        if arguments is not None:
            executed.append(" ".join(arguments))
    assert any(GUARD in arguments for arguments in executed), executed


def test_the_gate_cannot_be_disarmed() -> None:
    workflow = load_workflow()
    for step in run_steps(workflow):
        assert step.get("continue-on-error") is not True
        assert step.get("if") is not False
    for job in (workflow.get("jobs") or {}).values():
        assert job.get("continue-on-error") is not True
        assert job.get("if") is not False


def test_the_mention_is_not_mistaken_for_an_invocation() -> None:
    """Control for the wiring detector: `echo pytest <guard>` must not count."""
    assert pytest_arguments(f"echo pytest {GUARD}") is None
    assert pytest_arguments(f"# pytest {GUARD}") is None
    assert pytest_arguments(f"python -m pytest -q {GUARD}") == ["-q", GUARD]
