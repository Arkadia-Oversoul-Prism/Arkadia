"""Console endpoint-registry contract.

``web/arkadia_console/src/lib/endpoints.ts`` is the console's single API surface
map. `SHARED-CONTRACTS.md` §3.3 requires API evidence before a UI claim ("a source
constant or archive usage is not proof of a live contract. Never invent an
endpoint"), and §3.1 requires one registry rather than page-local paths.

Measured at ``main`` ``a29a9b8f``: no test in ``tests/`` or ``scripts/`` read
``endpoints.ts`` at all, so the registry was an unpinned contract — a path could be
renamed or invented with nothing to catch it. This guard binds every declared
entry to a handler that is actually served by ``api.main:app``, and binds every
page read to a registry entry rather than an inline literal.

Domain: the Arkadia Console (``web/arkadia_console``), the primary application.
This is deliberately disjoint from ``test_console_shell_nav_contract.py`` (owned by
PR #418; navigation/shell/design invariants, no endpoint or backend assertions),
``test_canonical_frontend_routing.py`` (surface-path serving + shadowing) and
``test_documented_route_contract.py`` (the ``DEPLOYMENT_GUIDE.md`` table). No guard
is duplicated.

A related drift is recorded, not repaired here: the ``contract="…"`` strings that
``NotYetWired`` *advertises* are page-owned display copy, not registry entries, and
several name paths the backend does not serve. They live in feature pages owned by
other workstreams, so this file records them as a bounded finding
(``test_advertised_contract_strings_are_recorded``) rather than editing those pages.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _declared_endpoints(text: str) -> dict[str, str]:
    """The ``name: "path"`` pairs of the registry object."""
    body = re.search(r"export const endpoints\s*=\s*\{(.*?)\}\s*as const;", text, re.DOTALL)
    assert body, "endpoints.ts declares no `endpoints` object literal"
    return dict(re.findall(r'(\w+):\s*"([^"]+)"', body.group(1)))


def _malformed_entries(declared: dict[str, str]) -> list[str]:
    """Registry entries that are not a root-absolute API path.

    An absolute URL is a second API base; a relative or empty value cannot be
    requested from the canonical origin. Both are the class §3.4 forbids.
    """
    defects = []
    for name, path in sorted(declared.items()):
        # Check the absolute origin first: it also starts with "http", not "/", so
        # a root-absolute test ordered before this one would report it as merely
        # "not root-absolute" and hide the second-API-base defect.
        if re.match(r"^https?://", path):
            defects.append(f"{name} -> {path!r} is an absolute deployment origin")
        elif not path.startswith("/"):
            defects.append(f"{name} -> {path!r} is not root-absolute")
        elif path.rstrip("/") != path:
            defects.append(f"{name} -> {path!r} has a trailing slash")
    return defects


def _unserved(declared: dict[str, str], served: set[str]) -> list[str]:
    """Declared entries with no handler in the served OpenAPI schema."""
    return [f"{name} -> {path}" for name, path in sorted(declared.items()) if path not in served]


def _served_paths() -> set[str]:
    """The paths the served app declares. Imported lazily so the negative
    controls do not pay the application import."""
    from api.main import app

    return set(app.openapi()["paths"].keys())


def _hydration_path_arguments(text: str) -> list[str]:
    """The first argument of every ``useHydration<…>(`` call in a page."""
    return re.findall(r"useHydration<[^>]*>\(\s*([^,\n]+)", text)


def _balanced(text: str, start: int) -> str:
    """Text from the ``{`` at *start* through its matching ``}``.

    Balanced rather than ``[^}]*`` because a template literal's ``${…}`` would
    otherwise truncate the definition before the ``endpoints.`` reference.
    """
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise AssertionError("unbalanced braces in a local definition")


def _statement(text: str, start: int) -> str:
    """A statement's text from *start* to its top-level ``;``."""
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        if char in "{([":
            depth += 1
        elif char in "})]":
            depth -= 1
        elif char == ";" and depth == 0:
            return text[start:i]
    return text[start:]


def _local_definitions(text: str) -> dict[str, str]:
    """Map each local ``const``/``function`` name to its defining text."""
    defs: dict[str, str] = {}
    for match in re.finditer(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", text):
        defs.setdefault(match.group(1), _statement(text, match.end()))
    for match in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::[^{]*)?\{", text):
        defs.setdefault(match.group(1), _balanced(text, match.end() - 1))
    return defs


def _function_body(text: str, name: str) -> str | None:
    """The brace-balanced body of an exported ``function <name>``.

    ``[^}]*`` would truncate at the first ``}`` — which a template literal's
    ``${…}`` contains — so the body is extracted by brace matching.
    """
    match = re.search(rf"export\s+function\s+{re.escape(name)}\s*\([^)]*\)\s*(?::[^{{]*)?\{{", text)
    if not match:
        return None
    return _balanced(text, match.end() - 1)


def _registry_derived_names(text: str) -> set[str]:
    """Local identifiers whose value is (transitively) built from the registry.

    A sub-resource path is legitimately composed as ``endpoints.collection +
    '/' + id`` — in the page, in a local helper, or in a builder exported by
    ``lib/endpoints``. That is the *one registry*, expressed, so it must not be
    reported as a second, invented contract. Only a path that resolves to a raw
    literal is an inline path.
    """
    defs = _local_definitions(text)
    imported = set()
    for match in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*[\"'][^\"']*endpoints[\"']", text):
        for part in match.group(1).split(","):
            imported.add(part.strip().split(" as ")[-1].strip())

    known = set(defs) | imported
    derived = set(imported) | {name for name, body in defs.items() if re.search(r"\bendpoints\b", body)}
    changed = True
    while changed:
        changed = False
        for name, body in defs.items():
            if name in derived:
                continue
            # Propagate only through *defined* names, so a function parameter is
            # not promoted to "registry-derived" by appearing beside one.
            if set(re.findall(r"\b([A-Za-z_$][\w$]*)\b", body)) & known & derived:
                derived.add(name)
                changed = True
    return derived


def _inline_path_arguments(sources: dict[str, str]) -> list[str]:
    """``useHydration`` reads whose path is neither a registry member nor a
    registry-derived binding/call.

    A page that inlines a path has invented its own endpoint contract. The
    canonical forms are ``useHydration<T>(endpoints.name, …)`` and a
    registry-derived sub-resource path (``useHydration<T>(labSession(id), …)``
    or a local binding built from ``endpoints.*``).
    """
    defects = []
    for name, src in sources.items():
        derived = _registry_derived_names(src)
        for arg in _hydration_path_arguments(src):
            expression = arg.strip()
            if expression.startswith("endpoints."):
                continue
            root = re.match(r"[A-Za-z_$][\w$]*", expression)
            if root and root.group(0) in derived:
                continue
            defects.append(f"{name}: useHydration path argument {expression!r}")
    return defects


def _advertised_contract_strings(sources: dict[str, str]) -> dict[str, str]:
    """The ``contract="…"`` strings a page advertises on a ``NotYetWired`` panel."""
    found = {}
    for name, src in sources.items():
        for match in re.finditer(r'contract="([^"]+)"', src):
            found[name] = match.group(1)
    return found


def _tsx_sources() -> dict[str, str]:
    return {str(p.relative_to(SRC)): p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.tsx"))}


# ---------------------------------------------------------------------------
# The registry is the one API surface map, and every entry is served
# ---------------------------------------------------------------------------


def test_registry_is_non_empty_and_names_are_unique():
    """A vacuous registry would make every assertion below pass by accident."""
    text = ENDPOINTS_PATH.read_text(encoding="utf-8")
    declared = _declared_endpoints(text)
    assert declared, "endpoints.ts declares no entries -- the guard would be vacuous"
    names = re.findall(r"(\w+):\s*\"", text)
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert duplicates == [], f"duplicate registry key(s) in endpoints.ts: {duplicates}"


def test_every_declared_endpoint_is_a_root_absolute_path():
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    assert _malformed_entries(declared) == [], f"malformed registry entry: {_malformed_entries(declared)}"


def test_every_declared_endpoint_is_served_by_the_canonical_app():
    """Every registry path must be a handler on ``api.main:app``.

    This is the "never invent an endpoint" contract: a renamed or guessed path
    would 404 in production while type-checking and building cleanly.
    """
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    served = _served_paths()
    assert served, "the served app declares no paths -- the guard would be vacuous"
    unserved = _unserved(declared, served)
    assert unserved == [], (
        "endpoints.ts declares path(s) the canonical app does not serve: " + ", ".join(unserved)
    )


def test_every_page_read_uses_the_registry_not_an_inline_path():
    """One registry (§3.1): a page that inlines its path has a second, unreviewed
    endpoint contract."""
    defects = _inline_path_arguments(_tsx_sources())
    assert defects == [], f"page-local endpoint path(s): {defects}"


def test_registry_path_builders_derive_from_a_collection_and_encode():
    """A parameterized sub-resource helper must be derived from its declared
    collection (so the base cannot drift) and percent-encode the parameter (so
    an id containing ``/`` cannot address another route).

    ``labSession`` is Workstream 4's requested builder for the Engineering Lab
    session view. Its route is verified by the served-path test below.
    """
    text = ENDPOINTS_PATH.read_text(encoding="utf-8")
    body = _function_body(text, "labSession")
    assert body, "endpoints.ts declares no `labSession(...)` path builder"
    param = re.search(r"labSession\(([^):]*)(?::[^)]*)?\)", text).group(1).strip()
    assert "endpoints.labSessions" in body, "the builder must derive from its declared collection"
    assert f"encodeURIComponent({param})" in body, "the path parameter must be percent-encoded"


def test_lab_session_builder_matches_the_served_route():
    """The builder's composed path must be the served session-view route, with
    the sub-resource segment spelled the way the backend declares it.

    ``labSession(collection, id)`` composes a path under ``endpoints.labSessions``;
    that route and the ``/{session_id}`` sub-route must both be served, and the
    builder's own body must not carry a conflicting literal segment.
    """
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    served = _served_paths()
    collection = declared["labSessions"]
    assert collection in served, f"{collection!r} is not served"
    assert f"{collection}/{{session_id}}" in served, "the session-view sub-route is not served"

    text = ENDPOINTS_PATH.read_text(encoding="utf-8")
    body = _function_body(text, "labSession")
    # The only segment after the collection is the parameter; a hardcoded
    # segment here would be a second, unverified sub-resource spelling.
    assert re.sub(r"\$\{[^}]+\}", "", body).count("/") == 1, body


# ---------------------------------------------------------------------------
# Negative controls -- each detector must flag the defect it claims to detect.
# ---------------------------------------------------------------------------


def test_detector_flags_an_invented_endpoint():
    """The pre-repair shape: a plausible-looking path with no handler must be
    reported, and a genuinely served path must not be."""
    served = _served_paths()
    assert "/api/version" in served, "control premise: /api/version must be served"
    invented = {"ghostFeed": "/api/ghost-feed"}
    assert _unserved(invented, served) == ["ghostFeed -> /api/ghost-feed"]
    real = {"version": "/api/version"}
    assert _unserved(real, served) == []


def test_detector_flags_a_second_api_base_or_relative_path():
    """An absolute URL is a second API base; a relative value cannot be requested
    from the canonical origin."""
    stale = {"feed": "https://arkadia-ten.vercel.app/api/feed", "version": "api/version"}
    defects = _malformed_entries(stale)
    assert len(defects) == 2, defects
    assert any("absolute deployment origin" in d for d in defects), defects
    assert any("not root-absolute" in d for d in defects), defects
    assert _malformed_entries({"version": "/api/version"}) == []


def test_detector_flags_a_page_local_endpoint_path():
    """A page passing a literal path to ``useHydration`` is the second-registry
    defect; the registry forms must not be flagged."""
    stale = {"pages/X.tsx": 'useHydration<Thing>("/api/invented", (p) => apiRequest<Thing>(p))'}
    assert _inline_path_arguments(stale) == ["pages/X.tsx: useHydration path argument '\"/api/invented\"'"]
    clean = {"pages/X.tsx": "useHydration<Thing>(endpoints.thing, (p) => apiRequest<Thing>(p))"}
    assert _inline_path_arguments(clean) == []


def test_detector_accepts_a_registry_derived_sub_resource_path():
    """A sub-resource path built from a declared collection is the one registry.

    ``LabSessionList.tsx`` derives its view path from ``endpoints.labSessions``
    (in a local helper, transitively via a local binding). This is the canonical
    registry form, not a page-local contract, and the detector must not report
    it. The control proves the acceptance is specifically registry-derived: the
    same shape with a raw literal string is still a defect.
    """
    via_helper = {
        "pages/X.tsx": (
            "import { endpoints } from './endpoints';\n"
            "function viewPath(id: string): string {\n"
            '  return `${endpoints.sessions}/${encodeURIComponent(id)}`;\n'
            "}\n"
            "const path = viewPath(sessionId);\n"
            "useHydration<View>(path, (p) => apiRequest<View>(p));\n"
        )
    }
    assert _inline_path_arguments(via_helper) == []

    via_imported_builder = {
        "pages/X.tsx": (
            "import { endpoints, labSession } from './endpoints';\n"
            "useHydration<View>(labSession(id), (p) => apiRequest<View>(p));\n"
        )
    }
    assert _inline_path_arguments(via_imported_builder) == []

    raw_literal_in_a_helper = {
        "pages/X.tsx": (
            "function viewPath(id: string): string {\n"
            '  return `/api/invented/${encodeURIComponent(id)}`;\n'
            "}\n"
            "useHydration<View>(viewPath(sessionId), (p) => apiRequest<View>(p));\n"
        )
    }
    assert _inline_path_arguments(raw_literal_in_a_helper) == [
        "pages/X.tsx: useHydration path argument 'viewPath(sessionId)'"
    ]


# ---------------------------------------------------------------------------
# Recorded finding (not repaired here): advertised contract strings
# ---------------------------------------------------------------------------

#: Advertised ``contract="…"`` strings measured at ``a29a9b8f`` that the served app
#: does not serve as written. Each is display copy inside a feature page owned by
#: another workstream, so it is recorded here rather than edited.
RECORDED_ADVERTISED_DRIFT = {
    "/api/solspire/voice",
    "/api/lab/engineering/sessions/{id}/execute",
    "/api/solspire/projects/{id}/runtime-context",
    "/api/solspire/workloads",
    "/api/solspire/proposals",
    "/api/solspire/pulses",
}


def test_advertised_contract_strings_are_recorded():
    """Bound the drift: every advertised string the backend does not serve must be
    one we have recorded, so a *new* invented contract string is visible.

    The set is a floor, not an exact match: fixing one of these pages is a
    feature-page edit owned by another workstream, so this test must not fail
    when one is repaired.
    """
    advertised = set(_advertised_contract_strings(_tsx_sources()).values())
    served = _served_paths()
    normalized_served = {re.sub(r"\{[^}]*\}", "{}", p) for p in served}

    def is_served(value: str) -> bool:
        stripped = value[4:] if value.startswith("/api/") else value
        if value in served:
            return True
        # A page may legitimately advertise the served shape with its own param
        # name (e.g. `{id}` for a served `{project_id}`).
        return re.sub(r"\{[^}]*\}", "{}", stripped) in normalized_served

    unrecorded = sorted(v for v in advertised if not is_served(v) and v not in RECORDED_ADVERTISED_DRIFT)
    assert unrecorded == [], (
        "advertised contract string(s) that the canonical app does not serve and that are "
        "not in RECORDED_ADVERTISED_DRIFT: " + ", ".join(unrecorded)
    )
    # Positive control: the recorded set is not vacuous -- at least one recorded
    # string is genuinely unserved at this revision.
    assert any(v in advertised for v in RECORDED_ADVERTISED_DRIFT), (
        "no recorded drift string is still advertised -- prune RECORDED_ADVERTISED_DRIFT"
    )
