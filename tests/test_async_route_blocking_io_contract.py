"""An async route must never call a blocking network API on the event loop.

The canonical runtime serves the whole application from **one** Uvicorn worker,
so every ``async def`` handler shares one event-loop thread. A handler that calls
a synchronous HTTP client (`urllib.request.urlopen`, `requests.*`) inside
``async def`` blocks that thread for the whole request: every other request —
including the liveness probe and every page load — waits behind it.

Measured on ``main`` @ ``bb19aabd``: ``api/lab_routes.py::pr_state``
(``GET /api/lab/engineering/pr/{number}``) was an ``async def`` route that called
``urllib.request.urlopen(..., timeout=10)`` directly, so a single Lab PR-state
read could stall the entire deployment for up to ten seconds. Ruff's ``ASYNC210``
flagged the same line, but Ruff is not part of any CI gate, so nothing prevented
the next instance.

The repair offloads the call with ``asyncio.to_thread``, which keeps the handler
a coroutine (the projection tests drive it with ``asyncio.run``) while moving the
blocking work off the loop thread.

This module is the continuous guard for the class, not for that one call site: it
derives its subject from the tracked ``api/`` corpus at test time, so a new route
that blocks is caught without editing this file. Awaiting an async client is
correct and is not judged — only the two synchronous clients above are.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

# Synchronous-only client entry points. Awaiting these is impossible: they always
# run on the calling thread.
BLOCKING_ATTRS = {"urlopen", "urlretrieve"}
BLOCKING_MODULES = {"requests"}

# Calls that move work to a worker thread. Anything inside them is off the loop.
OFFLOAD_ATTRS = {"to_thread", "run_in_executor"}


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _is_route_handler(node: ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr in ROUTE_METHODS:
            return True
    return False


def _is_offload(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    target = node.func
    if isinstance(target, ast.Attribute) and target.attr in OFFLOAD_ATTRS:
        return True
    dotted = _dotted(target)
    return dotted in {"asyncio.to_thread"} or dotted.endswith(".run_in_executor")


def _is_blocking_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    attr = node.func.attr
    if attr in BLOCKING_ATTRS:
        return True
    value = node.func.value
    return isinstance(value, ast.Name) and value.id in BLOCKING_MODULES and attr in ROUTE_METHODS | {
        "request",
        "head",
    }


def _walk(node: ast.AST, offloaded: bool = False):
    """Yield (call, offloaded) for every Call reachable from ``node``."""
    if isinstance(node, ast.Call):
        offloaded = offloaded or _is_offload(node)
        yield node, offloaded
    for child in ast.iter_child_nodes(node):
        yield from _walk(child, offloaded)


def blocking_calls_in_async_routes(source: str) -> list[tuple[str, int, str]]:
    """``(handler, lineno, api)`` for every blocking call on an async route."""
    tree = ast.parse(source)
    findings: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) or not _is_route_handler(node):
            continue
        for call, offloaded in _walk(node):
            if offloaded or not _is_blocking_call(call):
                continue
            findings.append((node.name, call.lineno, call.func.attr))
    return findings


def _tracked_api_modules() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "--", "api/*.py", "api/**/*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return sorted(REPO_ROOT / path for path in listed if path.endswith(".py"))


def test_the_tracked_corpus_is_what_the_guard_believes_it_is():
    """A guard over an empty domain would pass for the wrong reason."""
    modules = _tracked_api_modules()
    assert len(modules) > 30, f"derived only {len(modules)} api modules"
    assert any(m.name == "lab_routes.py" for m in modules)


def test_api_async_routes_do_not_block_the_event_loop():
    offenders: list[str] = []
    for module in _tracked_api_modules():
        source = module.read_text(encoding="utf-8")
        for handler, lineno, api in blocking_calls_in_async_routes(source):
            offenders.append(
                f"{module.relative_to(REPO_ROOT)}:{lineno} async route {handler}() "
                f"calls blocking {api}(); offload it with asyncio.to_thread"
            )
    assert offenders == [], "\n".join(offenders)


def test_the_guarded_handler_is_offloaded_where_it_runs():
    """Pin the repair at its definition, not at a call site."""
    source = (REPO_ROOT / "api" / "lab_routes.py").read_text(encoding="utf-8")
    assert "await asyncio.to_thread(_read_json_url" in source, (
        "the Lab PR-state read must run its blocking GET on a worker thread"
    )


def test_detector_flags_the_repaired_shape():
    """Negative control: the pre-repair handler, verbatim, must be reported."""
    before = '''
@router.get("/engineering/pr/{number}")
async def pr_state(number: int) -> dict:
    req = urllib.request.Request("https://api.github.com/x")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return {"state": "AVAILABLE"}
'''
    assert blocking_calls_in_async_routes(before) == [("pr_state", 5, "urlopen")]


def test_detector_flags_a_synchronous_requests_client():
    before = '''
@app.post("/ingest")
async def ingest(payload: dict) -> dict:
    return requests.post("https://example.test", json=payload).json()
'''
    findings = blocking_calls_in_async_routes(before)
    assert [(name, api) for name, _, api in findings] == [("ingest", "post")]


def test_detector_is_silent_on_offloaded_and_awaited_calls():
    """Positive control: the repair shape and an awaited async client pass."""
    after = '''
def _read_json_url(req, timeout):
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

@router.get("/engineering/pr/{number}")
async def pr_state(number: int) -> dict:
    data = await asyncio.to_thread(_read_json_url, req, 10)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post("https://example.test", json=data)
    return {"state": "AVAILABLE"}
'''
    assert blocking_calls_in_async_routes(after) == []


def test_detector_ignores_a_synchronous_helper_outside_a_route():
    """A plain ``def`` helper is already off the loop; it must not be flagged."""
    sync_helper = '''
def fetch(req):
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()
'''
    assert blocking_calls_in_async_routes(sync_helper) == []
