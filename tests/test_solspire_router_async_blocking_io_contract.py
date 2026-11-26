"""Boundary guard: a SolSpire async route must not block the one event loop.

`entrypoint.sh` starts `uvicorn api.main:app` with no `--workers`, so the canonical
deployment serves the whole application from a single process and a single event
loop. Every `async def` route runs on that loop; a blocking call inside one stalls
not only its own request but *every* other request — including the liveness probe.

`solspire/console_router.py` is mounted into that app (`api/main.py`, prefix
`/solspire`). Ten of its handlers were `async def` while doing blocking work:
`/solspire/run` and `/solspire/projects/{id}/run` call `_execute_run`, which polls
an execution for up to 60 s with `time.sleep(0.25)`; three GitHub tool routes call
the blocking `httpx` client in `solspire/tools_github.py`; the project-creation,
integration-health and Weaver routes call `subprocess.run`. One operator click
could freeze the deployment for a minute.

The repair is the FastAPI idiom: a `def` handler is run in the threadpool by
Starlette, so the blocking work no longer occupies the loop and no response shape,
status code or authorization dependency changes.

The detector is a class guard, not a pin on the ten repaired lines: the domain
is derived from the tracked corpus at test time, blocking work is followed through
same-module *and* imported synchronous callees, and both polarities are proved by
controls below (a re-introduced offender is reported; an offloaded or synchronous
one is not).

Known limit, stated rather than hidden: an HTTP verb called on a client instance
whose constructor the detector cannot bind (`client.get(...)` for a client created
in another module) is judged only when the receiver was bound from a sync client
constructor in the same function. Module-level `httpx.<verb>` and
`requests.<verb>` are always judged.
"""

from __future__ import annotations

import ast
import subprocess
import textwrap
from pathlib import Path

ROUTER_PREFIXES = ("router.", "app.")
OFFLOAD_METHODS = {"to_thread", "run_in_threadpool", "run_in_executor"}
SUBPROCESS_RUNNERS = {"run", "check_output", "check_call", "call", "Popen"}
HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "options", "request", "stream"}
SYNC_CLIENT_CTORS = {"httpx.Client", "requests.Session", "requests.sessions.Session"}
MAX_DEPTH = 4


def _parse(path: str | Path) -> ast.Module | None:
    try:
        return ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def _tracked_solspire_modules() -> list[str]:
    """Every tracked `solspire/*.py` module that constructs an `APIRouter`."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", "solspire/*.py", "solspire/**/*.py"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [path for path in tracked if _defines_router(path)]


def _defines_router(path: str | Path) -> bool:
    tree = _parse(path)
    if tree is None:
        return False
    return any(
        isinstance(node, (ast.Assign, ast.AnnAssign)) and "APIRouter(" in ast.unparse(node)
        for node in tree.body
    )


def _top_level_functions(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _route_handlers(tree: ast.Module) -> list[ast.AST]:
    handlers = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(ast.unparse(d).startswith(ROUTER_PREFIXES) for d in node.decorator_list):
            handlers.append(node)
    return handlers


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = func.value.id if isinstance(func.value, ast.Name) else None
        return f"{base}.{func.attr}" if base else func.attr
    return None


def _offloaded_calls(node: ast.AST) -> set[int]:
    """Ids of calls that leave the loop: awaited, or handed to an offload wrapper."""
    offloaded: set[int] = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Await):
            for call in ast.walk(inner.value):
                offloaded.add(id(call))
        elif isinstance(inner, ast.Call):
            if (_call_name(inner) or "").rpartition(".")[2] in OFFLOAD_METHODS:
                for argument in list(inner.args) + [kw.value for kw in inner.keywords]:
                    for call in ast.walk(argument):
                        offloaded.add(id(call))
    return offloaded


def _sync_client_names(node: ast.AST) -> set[str]:
    """Locals bound from a blocking client constructor (`c = httpx.Client(...)`)."""
    names: set[str] = set()
    for inner in ast.walk(node):
        if not isinstance(inner, (ast.Assign, ast.AnnAssign)):
            continue
        targets = inner.targets if isinstance(inner, ast.Assign) else [inner.target]
        if not isinstance(inner.value, ast.Call):
            continue
        if ast.unparse(inner.value.func) in SYNC_CLIENT_CTORS:
            names.update(t.id for t in targets if isinstance(t, ast.Name))
    return names


def _blocking_calls(node: ast.AST) -> list[str]:
    """Blocking calls in `node`, ignoring calls that are awaited or offloaded."""
    offloaded = _offloaded_calls(node)
    sync_clients = _sync_client_names(node)
    found: set[str] = set()
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call) or id(inner) in offloaded:
            continue
        name = _call_name(inner)
        if not name:
            continue
        base, _, attribute = name.rpartition(".")
        if attribute in ("urlopen", "urlretrieve"):
            found.add("urllib")
        elif base == "time" and attribute == "sleep":
            found.add("time.sleep")
        elif base == "requests" and attribute in HTTP_VERBS:
            found.add(f"requests.{attribute}")
        elif base == "httpx" and attribute in HTTP_VERBS:
            found.add(f"httpx.{attribute}")
        elif base == "subprocess" and attribute in SUBPROCESS_RUNNERS:
            found.add(f"subprocess.{attribute}")
        elif base == "socket" and attribute in ("create_connection", "socket"):
            found.add(f"socket.{attribute}")
        elif base in sync_clients and attribute in HTTP_VERBS:
            found.add(f"sync-client.{attribute}")
    return sorted(found)


def _import_map(node: ast.AST, tree: ast.Module) -> dict[str, tuple[str, str]]:
    """local name -> (module path, function name) for `from X import f` imports."""
    mapping: dict[str, tuple[str, str]] = {}
    # Function-local imports are visited first and win over module-level ones.
    for block in [node] + list(tree.body):
        for inner in ast.walk(block):
            if isinstance(inner, ast.ImportFrom) and inner.module:
                module_path = inner.module.replace(".", "/") + ".py"
                for alias in inner.names:
                    mapping.setdefault(alias.asname or alias.name, (module_path, alias.name))
    return mapping


def _resolve(path: str, name: str, depth: int = 0) -> tuple[ast.AST, str] | None:
    if depth > MAX_DEPTH:
        return None
    tree = _parse(path)
    if tree is None:
        return None
    function = _top_level_functions(tree).get(name)
    if function is not None:
        return function, path
    for inner in tree.body:
        if isinstance(inner, ast.ImportFrom) and inner.module:
            for alias in inner.names:
                if (alias.asname or alias.name) == name:
                    return _resolve(inner.module.replace(".", "/") + ".py", alias.name, depth + 1)
    return None


def _blocking_reachable(handler: ast.AST, path: str) -> list[str]:
    """Blocking work reachable through synchronous callees (same or imported module)."""
    found = set(_blocking_calls(handler))
    seen: set[tuple[str, str]] = set()
    pending = [(handler, path, 0)]
    while pending:
        node, node_path, depth = pending.pop()
        tree = _parse(node_path)
        if tree is None or depth > MAX_DEPTH:
            continue
        local = _top_level_functions(tree)
        imports = _import_map(node, tree)
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call) or not isinstance(inner.func, ast.Name):
                continue
            name = inner.func.id
            if name in local:
                resolved: tuple[ast.AST, str] | None = (local[name], node_path)
            elif name in imports:
                resolved = _resolve(*imports[name], depth + 1)
            else:
                resolved = None
            if resolved is None:
                continue
            callee, callee_path = resolved
            if isinstance(callee, ast.AsyncFunctionDef):
                continue  # an async callee is not blocking; it must be awaited
            key = (callee_path, getattr(callee, "name", name))
            if key in seen:
                continue
            seen.add(key)
            found.update(_blocking_calls(callee))
            pending.append((callee, callee_path, depth + 1))
    return sorted(found)


def offenders(modules: list[str] | None = None) -> list[str]:
    """Async SolSpire route handlers that perform blocking work, as readable rows."""
    rows = []
    for path in modules if modules is not None else _tracked_solspire_modules():
        tree = _parse(path)
        if tree is None:
            continue
        for handler in _route_handlers(tree):
            if not isinstance(handler, ast.AsyncFunctionDef):
                continue
            blocking = _blocking_reachable(handler, path)
            if blocking:
                rows.append(f"{path}:{handler.lineno} {handler.name}() -> {blocking}")
    return sorted(rows)


# ── The invariant ──────────────────────────────────────────────────────────

def test_no_solspire_async_route_blocks_the_event_loop():
    assert offenders() == []


def test_the_guarded_domain_is_the_solspire_router_corpus():
    modules = _tracked_solspire_modules()
    handlers = [h for path in modules if (tree := _parse(path)) for h in _route_handlers(tree)]
    assert len(modules) >= 5, f"derived only {len(modules)} SolSpire router modules"
    assert len(handlers) >= 40, f"derived only {len(handlers)} SolSpire routes"


def test_the_run_pipeline_routes_are_synchronous():
    """The two routes that poll `_execute_run` for up to 60 s must not be async."""
    functions = _top_level_functions(_parse("solspire/console_router.py"))
    for name in ("run_request", "project_run"):
        assert isinstance(functions[name], ast.FunctionDef), f"{name} must be a sync handler"


# ── Controls: the detector must see the defect and stay quiet on the repair ──

PRE_REPAIR_SHAPE = '''
import time

@router.post("/run")
async def run_request(body, user):
    return _execute_run(body, user)


def _execute_run(body, user):
    deadline = time.time() + 60
    while time.time() < deadline:
        time.sleep(0.25)
    return {}
'''


def _rows_for(source: str, tmp_path: Path, name: str = "synthetic_router.py") -> list[str]:
    module = tmp_path / name
    module.write_text(textwrap.dedent(source), encoding="utf-8")
    return offenders([str(module)])


def test_detector_flags_the_repaired_shape(tmp_path):
    rows = _rows_for(PRE_REPAIR_SHAPE, tmp_path)
    assert len(rows) == 1
    assert "run_request" in rows[0] and "time.sleep" in rows[0]


def test_detector_flags_a_direct_http_client(tmp_path):
    source = '''
@router.get("/x")
async def handler():
    return requests.get("https://example.test")
'''
    assert "requests.get" in _rows_for(source, tmp_path)[0]


def test_detector_flags_a_sync_client_instance(tmp_path):
    source = '''
@router.get("/x")
async def handler():
    client = requests.Session()
    return client.get("https://example.test")
'''
    assert "sync-client.get" in _rows_for(source, tmp_path)[0]


def test_detector_follows_an_imported_synchronous_helper(tmp_path):
    assert Path("solspire/tools_github.py").exists(), "the control needs the real helper module"
    source = '''
@router.post("/tools/github/repos")
async def github_repos(body):
    from solspire.tools_github import list_repos
    return list_repos(body.owner)
'''
    assert "httpx.get" in _rows_for(source, tmp_path)[0]


def test_detector_is_silent_on_offloaded_and_awaited_calls(tmp_path):
    source = '''
@router.post("/x")
async def handler():
    await asyncio.to_thread(requests.get, "https://example.test")
    await client.get("https://example.test")
'''
    assert _rows_for(source, tmp_path) == []


def test_detector_ignores_a_synchronous_route(tmp_path):
    """The repair shape itself: `def` handlers run in the threadpool."""
    source = PRE_REPAIR_SHAPE.replace(
        "async def run_request(body, user):", "def run_request(body, user):"
    )
    assert _rows_for(source, tmp_path) == []
