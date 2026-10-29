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

Re-measured 2026-10-29 at ``main`` ``b5bc34cb``: the oracle that decided "served" was
wrong in both directions, and the extractor that fed it dropped every advertised
literal but the last one per file. Both are repaired here; see :func:`_is_served` and
:func:`_advertised_contract_strings`. The repair *reduces* the recorded set from six
entries to one — four were never drift, and two are no longer advertised.
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


def _param_normalized(path: str) -> str:
    """A path with every parameter segment collapsed to ``{}``."""
    return re.sub(r"\{[^}]*\}", "{}", path)


def _is_served(value: str, served: set[str]) -> bool:
    """Whether the served app declares ``value``.

    The comparison is **symmetric**: both sides are parameter-normalized, and the
    ``/api`` prefix is significant on both. The earlier oracle stripped ``/api/``
    from the *advertised* side only, which made the comparison a one-way prefix
    removal and wrong in both directions:

    * false positive — ``/api/lab/engineering/sessions/{id}/execute`` read as
      unserved while the app serves it under ``{session_id}``, because the strip
      discarded the only prefix that distinguishes it from ``/lab/...``;
    * false negative — ``/api/solspire/proposals`` read as *served* while no such
      route exists, because the strip collapsed it onto the real ``/solspire/...``
      handler. That is the dangerous direction: a genuinely invented endpoint
      passed the guard whose entire purpose is to catch invented endpoints.

    A page may still legitimately advertise the served shape with its own parameter
    name (``{id}`` for a served ``{project_id}``), which the normalization keeps.
    """
    if value in served:
        return True
    return _param_normalized(value) in {_param_normalized(p) for p in served}


def _unserved(declared: dict[str, str], served: set[str]) -> list[str]:
    """Declared entries with no handler in the served OpenAPI schema."""
    return [f"{name} -> {path}" for name, path in sorted(declared.items()) if path not in served]


def _served_paths() -> set[str]:
    """The paths the served app declares. Imported lazily so the negative
    controls do not pay the application import."""
    from api.main import app

    return set(app.openapi()["paths"].keys())


def _canvas_route_template(artifacts_path: str, builder_body: str) -> str:
    """The route template a ``labCanvas`` builder body composes.

    The body is evaluated as *shape*, not executed: the derivation is the
    ``.replace(/\\/artifacts$/, "/canvas")`` substitution, and the parameter
    becomes the ``{artifact_id}`` template segment. A body without the
    substitution keeps the artifacts collection and therefore composes the
    route the backend does not serve — which is the defect the control feeds
    to the detector.
    """
    base = artifacts_path
    if re.search(r'\.replace\(\s*/\\/artifacts\$/\s*,\s*"/canvas"\s*\)', builder_body):
        base = artifacts_path[: -len("/artifacts")] + "/canvas"
    return f"{base}/{{artifact_id}}"


def _hydration_path_arguments(text: str) -> list[str]:
    """The first argument of every ``useHydration<…>(`` call in a page."""
    return re.findall(r"useHydration<[^>]*>\(\s*([^,\n]+)", text)


def _request_path_arguments(text: str) -> list[str]:
    """The first argument of every ``apiRequest<…>(`` call."""
    return re.findall(r"apiRequest(?:\s*<[^>]*>)?\(\s*([^,\n]+)", text)


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


def _inline_request_literals(sources: dict[str, str]) -> list[str]:
    """``apiRequest`` reads whose path argument is a raw string literal.

    ``useHydration`` always receives a path expression written in the page, so
    the detector above can judge every argument. ``apiRequest`` cannot be read
    the same way: the dominant call shape is a callback that *receives* its path
    (``useHydration<T>(path, (p) => apiRequest<T>(p))``), and the path there is
    a function or prop parameter, not a page-local decision. Only a literal is
    decidable without interprocedural analysis, and only a literal is a second,
    unreviewed endpoint contract — so that is exactly what is flagged. A
    registry-derived expression, a parameter, and a local binding are all
    outside this detector's domain by construction.
    """
    defects = []
    for name, src in sources.items():
        derived = _registry_derived_names(src)
        for arg in _request_path_arguments(src):
            expression = arg.strip()
            if not expression[:1] in {'"', "'", "`"}:
                continue
            if expression.startswith("endpoints."):
                continue
            root = re.match(r"[A-Za-z_$][\w$]*", expression)
            if root and root.group(0) in derived:
                continue
            defects.append(f"{name}: apiRequest path literal {expression!r}")
    return defects


def _advertised_contract_strings(sources: dict[str, str]) -> dict[str, list[str]]:
    """Every literal ``contract="…"`` string a page advertises on a ``NotYetWired`` panel.

    *Every* literal, not one per file. Keying by file kept only the last match, so
    ``SolSpirePage`` (four panels) had three of its advertised contracts silently
    unjudged — the same blind spot, one level down. Expression-valued props
    (``contract={DEFERRED[section]}``) are not literals and cannot be read statically.
    """
    found: dict[str, list[str]] = {}
    for name, src in sources.items():
        values = [match.group(1) for match in re.finditer(r'contract="([^"]+)"', src)]
        if values:
            found[name] = list(dict.fromkeys(values))
    return found


def _tsx_sources() -> dict[str, str]:
    return {str(p.relative_to(SRC)): p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.tsx"))}


def _transport_sources() -> dict[str, str]:
    """Every module the ``apiRequest`` detector scans.

    ``.ts`` as well as ``.tsx``: the read is what carries the endpoint contract,
    not the extension of the file that performs it, and ``lib/arkana.ts`` already
    reaches the backend through ``apiRequest``. A ``.tsx``-only domain would let a
    contract module (or a hook, or a plain helper) inline a path and pass the guard
    — the same blind spot the ``useHydration`` widening closed for ``.tsx``.

    ``lib/apiClient.ts`` is excluded because it *is* the transport: its own
    ``fetch(path, …)`` takes the path as a parameter, so scanning it would report
    the transport's signature rather than a page-local contract.
    """
    skip = {"lib/apiClient.ts"}
    sources = {}
    for pattern in ("*.ts", "*.tsx"):
        for path in sorted(SRC.rglob(pattern)):
            relative = str(path.relative_to(SRC))
            if relative not in skip:
                sources[relative] = path.read_text(encoding="utf-8")
    return sources


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


def test_no_page_passes_a_literal_path_to_api_request():
    """The same one-registry rule, widened to ``apiRequest``.

    ``useHydration`` always receives its path as a page-local expression, so the
    detector above judges every argument. ``apiRequest`` usually receives it as a
    *parameter* (``useHydration<T>(path, (p) => apiRequest<T>(p))``), which is not
    a page-local decision and cannot be judged without interprocedural analysis.
    A **literal** can be judged, and a literal is exactly the second, unreviewed
    contract this guard exists to catch.
    """
    defects = _inline_request_literals(_transport_sources())
    assert defects == [], f"literal endpoint path(s) passed to apiRequest: {defects}"


def test_request_detector_is_not_trivially_true():
    """Negative control: a literal passed to ``apiRequest`` must be reported,
    and the legitimate shapes must not be.

    Without this, a detector that matched nothing at all would pass the guard
    above on any tree -- including one that inlines every path.
    """
    invented = 'const r = await apiRequest<unknown>("/api/invented/route");'
    assert _inline_request_literals({"Page.tsx": invented}) != []

    template = "const r = await apiRequest<unknown>(`/api/invented/${id}`);"
    assert _inline_request_literals({"Page.tsx": template}) != []

    for legitimate in (
        "const r = await apiRequest<unknown>(endpoints.knowledgeGraph);",
        "const r = await apiRequest<unknown>(path);",
        "const r = await apiRequest<unknown>(p);",
        "const r = await apiRequest<unknown>(readPath);",
        "useHydration<T>(endpoints.echoes, (p) => apiRequest<T>(p), [flag]);",
    ):
        assert _inline_request_literals({"Page.tsx": legitimate}) == [], legitimate


def test_transport_detector_domain_includes_ts_modules():
    """Negative control: the detector's domain must not be ``.tsx``-only.

    A path literal in a plain ``.ts`` module is the same second, unreviewed
    contract as one in a page, and ``lib/arkana.ts`` already reaches the backend
    through ``apiRequest``. If the domain narrowed back to ``*.tsx``, a contract
    module could inline a path and pass the guard above — which is exactly the
    blind spot this domain closes.
    """
    assert "lib/arkana.ts" in _transport_sources(), "a real .ts transport read must be scanned"
    assert "lib/apiClient.ts" not in _transport_sources(), "the transport itself is a parameter"

    inlined = {"lib/helper.ts": 'export const load = () => apiRequest<Thing>("/api/invented");\n'}
    assert _inline_request_literals(inlined) != [], "a .ts literal must be reported"
    assert "lib/helper.ts" not in _tsx_sources(), "control premise: .ts is outside the tsx domain"


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


def test_lab_canvas_builder_derives_from_artifacts_and_encodes():
    """``labCanvas(id)`` must derive its base from a declared collection and
    percent-encode the id.

    The base is derived from ``endpoints.labArtifacts`` because the backend
    serves ``/engineering/canvas/{artifact_id}`` as a **sibling** of
    ``/engineering/artifacts`` — ``/engineering/canvas`` alone is not a route,
    so declaring it as a registry entry would fail the served-path test above.
    """
    text = ENDPOINTS_PATH.read_text(encoding="utf-8")
    body = _function_body(text, "labCanvas")
    assert body, "endpoints.ts declares no `labCanvas(...)` path builder"
    param = re.search(r"labCanvas\(([^):]*)(?::[^)]*)?\)", text).group(1).strip()
    assert "endpoints.labArtifacts" in body, "the builder must derive from a declared collection"
    assert f"encodeURIComponent({param})" in body, "the path parameter must be percent-encoded"


def test_lab_canvas_builder_composes_the_served_route():
    """The composed path must be exactly the served canvas route, and the
    sub-resource spelling the backend does *not* serve must not be produced.

    The backend declares ``/api/lab/engineering/canvas/{artifact_id}`` and does
    **not** declare ``/api/lab/engineering/artifacts/{artifact_id}``. A builder
    that merely appended the id to the artifacts collection would compose a
    plausible path that 404s, so both the correct and the wrong shape are
    asserted here.
    """
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    served = _served_paths()
    artifacts = declared["labArtifacts"]
    assert artifacts in served, f"{artifacts!r} is not served"

    text = ENDPOINTS_PATH.read_text(encoding="utf-8")
    body = _function_body(text, "labCanvas")
    # The same derivation the negative control feeds the detector: the live
    # builder must compose the served canvas route, and the artifacts
    # sub-resource the backend does not serve must stay unserved.
    composed = _canvas_route_template(artifacts, body)
    assert composed == "/api/lab/engineering/canvas/{artifact_id}", composed
    assert composed in served, f"the canvas route {composed!r} is not served"
    assert f"{artifacts}/{{artifact_id}}" not in served, (
        "control premise broken: the artifacts sub-resource is now served, so the "
        "sibling-canvas derivation must be re-derived rather than assumed"
    )


def test_registry_declares_the_automations_collection():
    """``labAutomations`` is Workstream 4's recorded request. The entry must be
    declared *and* served; the mutation routes under it stay out of the registry.
    """
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    served = _served_paths()
    assert declared.get("labAutomations") == "/api/lab/engineering/automations"
    assert declared["labAutomations"] in served, "the automations collection is not served"

    # The registry maps *read* collections. The mutating sub-routes are served
    # but deliberately unwired by the UI, so a registry entry for them would
    # advertise a mutation surface as a readable contract.
    mutation_paths = {p for p in declared.values() if "/state" in p or p.endswith("/execute")}
    assert mutation_paths == set(), f"registry declares mutation path(s): {sorted(mutation_paths)}"


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


def test_detector_flags_an_artifacts_sub_resource_canvas_path():
    """Negative control for the canvas builder: the plausible-but-unserved
    shape must be reported by the same derivation + detector the live
    assertion uses.

    The pre-repair composition (append the id to the artifacts collection
    without substituting the terminal segment) yields the template
    ``/api/lab/engineering/artifacts/{artifact_id}``, which the backend does
    not serve. If this control ever stops firing, the live assertion has been
    disarmed rather than satisfied.
    """
    declared = _declared_endpoints(ENDPOINTS_PATH.read_text(encoding="utf-8"))
    served = _served_paths()
    artifacts = declared["labArtifacts"]

    # The live derivation, applied to the real builder body.
    live_body = _function_body(ENDPOINTS_PATH.read_text(encoding="utf-8"), "labCanvas")
    live_template = _canvas_route_template(artifacts, live_body)
    assert live_template in served, f"live builder composes an unserved route: {live_template}"

    # The same derivation, applied to the pre-repair body (no substitution).
    pre_repair_body = 'return `${endpoints.labArtifacts}/${encodeURIComponent(artifactId)}`;'
    wrong_template = _canvas_route_template(artifacts, pre_repair_body)
    assert wrong_template == f"{artifacts}/{{artifact_id}}", wrong_template
    assert _unserved({"labCanvas": wrong_template}, served) == [
        f"labCanvas -> {wrong_template}"
    ], "the detector must report the artifacts sub-resource shape"

    # And it stays silent on the served shape.
    assert _unserved({"labCanvas": live_template}, served) == []


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


def test_served_oracle_is_prefix_symmetric_in_both_directions():
    """The oracle must not treat ``/api`` as an optional prefix.

    The pre-repair shape stripped ``/api/`` from the advertised value only, which
    made a *served* ``/api`` route read as unserved and — the dangerous direction —
    an *unserved* ``/api`` route read as served by collapsing onto its bare twin.
    Both controls below fail against that shape and pass against the repair.
    """
    served = _served_paths()
    assert "/api/version" in served, "control premise: /api/version must be served"

    # False positive: a served /api route advertised with a different param name.
    assert _is_served("/api/lab/engineering/sessions/{id}/execute", served) is True, (
        "a served /api route with a page-local parameter name must read as served"
    )
    # The bare twin is a different route and is not served.
    assert _is_served("/lab/engineering/sessions/{id}/execute", served) is False, (
        "dropping the /api prefix must not make an unserved route read as served"
    )

    # False negative: a genuinely invented /api route that has a served bare twin.
    assert "/solspire/proposals" in served, "control premise: /solspire/proposals must be served"
    assert _is_served("/api/solspire/proposals", served) is False, (
        "an invented /api route must not pass by collapsing onto its /solspire handler"
    )


def test_advertised_extractor_returns_every_literal_not_just_the_last():
    """A file with several ``NotYetWired`` panels advertises several contracts.

    Keying the result by file kept only the final match, so the earlier panels of
    ``SolSpirePage`` were never judged. The control feeds the exact multi-panel
    shape and requires every literal back; it fails against the keyed-by-file form.
    """
    multi_panel = {
        "pages/X.tsx": (
            'const a = <NotYetWired contract="/solspire/proposals" />;\n'
            'const b = <NotYetWired contract="/solspire/workevents" />;\n'
            'const c = <NotYetWired contract="/api/invented/route" />;\n'
            "const d = <NotYetWired contract={DEFERRED[section]} />;\n"
        )
    }
    assert _advertised_contract_strings(multi_panel) == {
        "pages/X.tsx": [
            "/solspire/proposals",
            "/solspire/workevents",
            "/api/invented/route",
        ]
    }, "every literal must be returned; an expression-valued prop is not a literal"

    # The live tree must exercise the multi-value path, or the control above is
    # the only thing holding the shape.
    live = _advertised_contract_strings(_tsx_sources())
    assert any(len(values) > 1 for values in live.values()), (
        "no live page advertises more than one contract -- the multi-panel path is untested"
    )


# ---------------------------------------------------------------------------
# Recorded finding (not repaired here): advertised contract strings
# ---------------------------------------------------------------------------

#: Advertised ``contract="…"`` strings measured at ``a29a9b8f`` that the served app
#: does not serve as written. Each is display copy inside a feature page owned by
#: another workstream, so it is recorded here rather than edited.
#:
#: Re-measured 2026-10-29 at ``main`` ``b5bc34cb``, and again at the repaired oracle.
#: The record is now **empty**, and that is a measurement, not a cleanup: every entry
#: the pre-repair oracle reported was an artifact of its one-way ``/api/`` strip
#: (see :func:`_is_served`). Four named routes the app *does* serve under the
#: ``/solspire`` prefix had been collapsed onto their bare twin; two of those
#: (``proposals``, ``workloads``) are no longer advertised by any page; and the last
#: entry, ``/api/lab/engineering/sessions/{id}/execute``, advertised by
#: ``pages/WeaverPage.tsx``, **resolves** — the handler serves ``{session_id}`` and
#: parameter normalization keeps it, which is the intended page-local naming case.
#:
#: So the repaired oracle leaves no unserved advertised contract at this revision.
#: This stays a floor, not an exact match: a *new* invented contract string is still
#: visible, because the assertion below fails on any advertised string outside it.
RECORDED_ADVERTISED_DRIFT: set[str] = set()


def test_advertised_contract_strings_are_recorded():
    """Bound the drift: every advertised string the backend does not serve must be
    one we have recorded, so a *new* invented contract string is visible.

    The set is a floor, not an exact match: fixing one of these pages is a
    feature-page edit owned by another workstream, so this test must not fail
    when one is repaired.
    """
    advertised = {
        value
        for values in _advertised_contract_strings(_tsx_sources()).values()
        for value in values
    }
    served = _served_paths()

    unrecorded = sorted(
        v for v in advertised if not _is_served(v, served) and v not in RECORDED_ADVERTISED_DRIFT
    )
    assert unrecorded == [], (
        "advertised contract string(s) that the canonical app does not serve and that are "
        "not in RECORDED_ADVERTISED_DRIFT: " + ", ".join(unrecorded)
    )
    # The recorded set is a floor, and it may legitimately be empty. What it may
    # not be is *stale*: an entry that is still advertised and that the app now
    # serves is a false record, so it must be pruned rather than carried.
    stale = sorted(
        v for v in RECORDED_ADVERTISED_DRIFT if v in advertised and _is_served(v, served)
    )
    assert stale == [], (
        "recorded drift string(s) that the canonical app actually serves -- prune "
        "RECORDED_ADVERTISED_DRIFT: " + ", ".join(stale)
    )
    # Negative control for the detector: it must not be trivially true. An invented
    # ``/api`` route with a served bare twin is exactly the shape the pre-repair
    # oracle passed by collapsing the prefix, and it must be reported here.
    invented = "/api/solspire/proposals"
    assert "/solspire/proposals" in served, "control premise: the bare twin must be served"
    assert _is_served(invented, served) is False, (
        "detector control: an invented /api route must not read as served"
    )
    assert invented not in RECORDED_ADVERTISED_DRIFT, (
        "the invented control route must not be pre-recorded, or the control is vacuous"
    )
