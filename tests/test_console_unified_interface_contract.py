"""Unified-interface contract (AO-002) — one shell, grouped navigation, one workspace.

The mission's non-negotiable rules are that unification happens through
*integration*, not duplication: one canonical shell, one navigation model, one
workspace, and no second approval/task/persistence system. These are source-level
contracts over ``web/arkadia_console`` — this repository's frontend-test
convention — and each detector carries a negative control so it cannot be
disarmed by editing the console source alone.

What this file pins that no existing guard does:

  * the navigation is *grouped* and the grouping is derived from the one surface
    table (``SurfaceDef.group``), not a second hardcoded list;
  * every navigable surface lands in exactly one declared group, so adding a
    surface cannot silently drop it out of the sidebar;
  * the workspace composes the *existing* Weaver and Engineering Lab components
    rather than re-implementing them (integration, not duplication);
  * the workspace does not introduce a second approval ledger, a second session
    list, or a second conversation-history reader.

Disjoint from ``test_console_shell_nav_contract.py`` (one nav model, one router,
one shell mount), ``test_arkana_mode_workspace_contract.py`` (Arkana modes) and
``test_canonical_workspace.py`` (workspace contract).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"

SURFACES_PATH = SRC / "lib" / "surfaces.ts"
SHELL_PATH = SRC / "components" / "Shell.tsx"
WORKSPACE_PATH = SRC / "pages" / "WorkspacePage.tsx"
WORKSPACE_SHELL_PATH = SRC / "components" / "workspace" / "WorkspaceShell.tsx"
INSPECTOR_PATH = SRC / "components" / "workspace" / "Inspector.tsx"
ARKANA_PAGE_PATH = SRC / "pages" / "ArkanaPage.tsx"

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
SHELL = SHELL_PATH.read_text(encoding="utf-8")
WORKSPACE = WORKSPACE_PATH.read_text(encoding="utf-8")
WORKSPACE_SHELL = WORKSPACE_SHELL_PATH.read_text(encoding="utf-8")
INSPECTOR = INSPECTOR_PATH.read_text(encoding="utf-8")
ARKANA_PAGE = ARKANA_PAGE_PATH.read_text(encoding="utf-8")


def _ts_sources() -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in SRC.rglob("*.ts*")
        if p.is_file()
    }


# ---------------------------------------------------------------------------
# Grouped navigation, derived from the one surface table
# ---------------------------------------------------------------------------


def test_surface_table_declares_the_navigation_groups():
    """The groups are a declaration in the surface table, not a component list."""
    assert "export type SurfaceGroupId" in SURFACES, "surfaces.ts declares no group id union"
    assert "export const SURFACE_GROUPS" in SURFACES, "surfaces.ts declares no group table"
    assert "group?: SurfaceGroupId" in SURFACES, "SurfaceDef has no group field"


def test_every_navigable_surface_declares_a_declared_group():
    """A navigable surface with no group would fall out of the sidebar.

    The shell collects an ungrouped surface into the trailing group, so this is
    a *declaration* check: every surface that appears in navigation must name a
    group that exists in ``SURFACE_GROUPS``.
    """
    declared_groups = set(re.findall(r'\{\s*id:\s*"([a-z]+)",\s*label:', SURFACES))
    assert declared_groups, "no groups declared -- the guard would be vacuous"

    # Each surface object: capture its id, whether nav is disabled, and its group.
    blocks = re.findall(r"\{\s*\n\s*id:\s*\"([a-z-]+)\",(.*?)\n  \},", SURFACES, re.DOTALL)
    assert blocks, "no surface objects parsed -- the guard would be vacuous"

    missing = []
    for surface_id, body in blocks:
        if re.search(r"nav:\s*false", body):
            continue
        group = re.search(r'group:\s*"([a-z]+)"', body)
        if not group:
            missing.append(f"{surface_id}: no group")
        elif group.group(1) not in declared_groups:
            missing.append(f"{surface_id}: group {group.group(1)!r} is not declared")
    assert missing == [], f"navigable surfaces without a declared group: {missing}"


def _groups_from_the_declared_table(shell_text: str) -> bool:
    """The shell groups by the declared group table, not a hardcoded list.

    Module level so the live assertion and its negative control call the *same*
    code. The control previously restated the membership test inline, which made
    it vacuous: renaming the marker in the live test left the control passing, so
    the detector could be disarmed with no red test (the class repaired in
    ``test_console_surface_error_boundary.py`` and
    ``test_console_shell_nav_contract.py``).
    """
    return "SURFACE_GROUPS.map" in shell_text


def test_shell_derives_grouped_navigation_from_the_surface_table():
    """The shell groups the one derived item list; it does not own a second list."""
    assert "NAV_SURFACES = SURFACES.filter" in SHELL, (
        "the shell must derive navigation from the surface table"
    )
    assert _groups_from_the_declared_table(SHELL), (
        "the shell must group by the declared group table"
    )
    assert "s.group ?? UNGROUPED" in SHELL, (
        "an ungrouped surface must be collected, not dropped"
    )
    # The grouped model is rendered in both the desktop sidebar and the drawer.
    assert SHELL.count("NAV_GROUPS.map") >= 2, (
        "the grouped navigation must render in both the sidebar and the drawer"
    )


def test_negative_control_a_second_group_list_would_be_detected():
    """The detector is proven on synthetic input: a hardcoded group list fails it.

    The control calls :func:`_groups_from_the_declared_table` — the same function
    the live assertion uses — so it can actually fail. The previous version
    compared the marker against a mutated string inline and passed even when the
    live detector's marker was renamed.
    """
    stale = SHELL.replace("SURFACE_GROUPS.map", "HARDCODED_GROUPS.map")
    assert stale != SHELL, "control did not mutate the shell -- detector unproven"
    assert not _groups_from_the_declared_table(stale), (
        "a shell that groups by a hardcoded list must be reported"
    )
    # The live tree still groups by the declared table, so the detector is not
    # trivially false.
    assert _groups_from_the_declared_table(SHELL)


# ---------------------------------------------------------------------------
# One workspace: integration, not duplication
# ---------------------------------------------------------------------------


def test_workspace_composes_the_existing_weaver_and_lab_components():
    """The workspace embeds the real components; it does not re-implement them."""
    for component, path in (
        ("ApprovalLedger", "components/weaver/ApprovalLedger.tsx"),
        ("LabRepositoryContext", "components/lab/LabRepositoryContext.tsx"),
        ("LabSessionList", "components/lab/LabSessionList.tsx"),
        ("ArkanaThreadHistory", "components/arkana/ArkanaThreadHistory.tsx"),
    ):
        module = path[: -len(".tsx")]
        assert f'from "../{module}"' in WORKSPACE, (
            f"the workspace must import the existing {component} from {path}"
        )
        assert (SRC / path).exists(), f"{path} does not exist -- the import would not resolve"


#: A workspace that re-declares one of these is a second approval/session/history
#: system — the duplication the mission forbids.
SECOND_SYSTEM_DEFINITIONS = (
    "function ApprovalLedger",
    "function LabSessionList",
    "function ArkanaThreadHistory",
)


def _second_system_definitions(source: str) -> list[str]:
    """Component definitions that would be a second approval/session/history system.

    Module level so the live assertion and its negative control call the *same*
    code; the control previously appended a definition and re-checked the marker
    inline, which could not fail for any edit to the live detector.
    """
    return [marker for marker in SECOND_SYSTEM_DEFINITIONS if marker in source]


def test_workspace_does_not_introduce_a_second_approval_or_session_system():
    """No second approval ledger, session list, or conversation reader."""
    # The workspace must not define its own approval/session/history components.
    assert _second_system_definitions(WORKSPACE) == [], (
        "the workspace defines a second approval/session/history system: "
        f"{_second_system_definitions(WORKSPACE)}"
    )
    # And it must not read the approval/session contracts directly.
    assert "endpoints.approvals" not in WORKSPACE, (
        "the workspace reads the approvals contract directly instead of composing the ledger"
    )


def test_workspace_shell_exposes_a_panels_slot_and_inspector_renders_it():
    """The expandable panels are a real slot, rendered by the shell and inspector."""
    assert "panels?: ReactNode" in WORKSPACE_SHELL, "WorkspaceShell has no panels slot"
    assert 'data-testid="workspace-panels"' in WORKSPACE_SHELL, (
        "the panels region has no test id"
    )
    assert "panels?: ReactNode" in INSPECTOR, "Inspector has no panels slot"
    assert "{context.panels}" in INSPECTOR, "the inspector does not render the contributed panels"
    assert "panels={panels}" in WORKSPACE, "the workspace does not pass its panels to the shell"


def test_negative_control_a_duplicated_ledger_would_be_detected():
    """The duplication detector is proven on synthetic input.

    The control calls :func:`_second_system_definitions` — the same function the
    live assertion uses — so it can actually fail. The previous version re-checked
    the marker inline and stayed green even when the live detector's marker was
    renamed.
    """
    assert _second_system_definitions(WORKSPACE) == [], (
        "the repaired workspace must not be reported"
    )
    duplicated = WORKSPACE + "\nfunction ApprovalLedger() { return null; }\n"
    assert _second_system_definitions(duplicated) == ["function ApprovalLedger"], (
        "a reintroduced second approval ledger must be reported"
    )


# ---------------------------------------------------------------------------
# The capability registry stays honest
# ---------------------------------------------------------------------------


def test_capability_registry_separates_verified_from_dispatchable():
    """A verified-but-automatic capability must not be offered as a dead token.

    Project conversations are wired (``lib/projectConversation.ts``) but are
    recorded because a project is active, not because a token was typed. The
    registry therefore carries a ``dispatchable`` dimension and the composer
    filters on it, so no control is offered that does not do what it says.
    """
    caps = (SRC / "lib" / "capabilities.ts").read_text(encoding="utf-8")
    assert "dispatchable?: boolean" in caps, "the registry has no dispatchable dimension"
    assert "dispatchable: false" in caps, "no capability is marked non-dispatchable"
    assert "c.dispatchable !== false" in WORKSPACE, (
        "the composer must filter out non-dispatchable capabilities"
    )
    # The stale claim that the console has no adapter must be gone.
    assert "the console has no adapter yet" not in caps, (
        "the registry still claims the project-conversation adapter does not exist"
    )


# ---------------------------------------------------------------------------
# One primary shell: no second navigation column, no second header
# ---------------------------------------------------------------------------
#
# `WorkspaceShell` and `ArkanaShell` used to be *shells*: each rendered its own
# rail, its own header and its own composer dock, nested inside the global
# `Shell`. Two navigation columns and two headers rendered at once — the
# structural reason the console read as several applications sharing a
# repository. They are now layouts: the one `Shell` owns navigation, the header
# and the identity block, and a surface *publishes* its rail to it through
# `lib/surfaceChrome.tsx`.
#
# These detectors are deliberately about *navigation chrome*, not about every
# `<aside>`: the workspace inspector is a legitimate `<aside>` (live state about
# the work in front of you), and forbidding it would be a false positive that
# pushes a real region out of the layout.

ARKANA_SHELL_PATH = SRC / "components" / "arkana" / "shell" / "ArkanaShell.tsx"
ARKANA_SHELL = ARKANA_SHELL_PATH.read_text(encoding="utf-8")

#: Markup that means "this file is rendering navigation chrome of its own".
SECOND_SHELL_MARKERS = (
    "cg-rail",  # the workspace's old left rail
    "arkana-sidebar",  # Arkana's old conversation sidebar
    "arkana-topbar",  # Arkana's old header
    "NAV_GROUPS",  # the shell's grouped navigation model
    "SURFACE_GROUPS",  # the group table the shell reads
    "cg-nav-item",  # a primary navigation item
    "Primary navigation",  # the shell's nav accessible name
)


def _second_shell_violations(source: str) -> list[str]:
    """Return the navigation-chrome markers a layout file still renders.

    A pure function so the negative control can run it over mutated source and
    prove the detector actually fires.
    """
    return [marker for marker in SECOND_SHELL_MARKERS if marker in source]


def test_layouts_render_no_navigation_chrome_of_their_own():
    """The two inner layouts must not own a rail, a header or a nav model."""
    for name, source in (
        ("WorkspaceShell.tsx", WORKSPACE_SHELL),
        ("ArkanaShell.tsx", ARKANA_SHELL),
    ):
        violations = _second_shell_violations(source)
        assert violations == [], (
            f"{name} still renders navigation chrome of its own: {violations}. "
            "The one canonical Shell owns navigation; a surface publishes its "
            "rail through useSurfaceChrome instead of rendering a second one."
        )


def _navigation_renderers(sources: dict[str, str]) -> list[str]:
    """Files that render the grouped navigation — the second-renderer detector.

    Module level so the live assertion and its negative control call the *same*
    code. The control previously restated this comprehension, so renaming the
    marker in the live test left the control passing.
    """
    return sorted(path for path, source in sources.items() if "NAV_GROUPS.map" in source)


def test_exactly_one_file_renders_the_primary_navigation():
    """`Shell.tsx` is the only file that renders the grouped navigation."""
    assert _navigation_renderers(_ts_sources()) == [
        "web/arkadia_console/src/components/Shell.tsx"
    ], f"the primary navigation must be rendered by exactly one file, found: {_navigation_renderers(_ts_sources())}"


def test_surfaces_publish_their_rail_instead_of_rendering_it():
    """Both conversational surfaces contribute chrome; neither passes a rail prop."""
    for name, source in (("WorkspacePage.tsx", WORKSPACE), ("ArkanaPage.tsx", ARKANA_PAGE)):
        assert "useSurfaceChrome(" in source, (
            f"{name} must publish its rail to the one shell via useSurfaceChrome"
        )
    # The old prop-passing shape is gone: a `rail=` prop on the layout would be
    # a second rail rendered inside the shell.
    assert "rail={rail}" not in WORKSPACE, "the workspace still passes a rail prop to its layout"
    assert "sidebar={<ArkanaThreadHistory />}" not in ARKANA_PAGE, (
        "Arkana still passes a sidebar prop to its layout"
    )


def test_the_shell_renders_the_published_rail_and_status():
    """The one shell is what renders the contributed rail and status line."""
    assert "usePublishedChrome" in SHELL, "the shell does not read the published chrome"
    assert 'data-testid="shell-surface-rail"' in SHELL, "the shell renders no surface rail region"
    assert 'data-testid="shell-surface-status"' in SHELL, "the shell renders no surface status line"
    assert "chrome.rail" in SHELL, "the shell does not gate the rail on published content"


def test_negative_control_a_reintroduced_second_shell_is_detected():
    """The detector is proven on synthetic input.

    Reintroducing the old rail markup into a layout must make the detector fire;
    otherwise the guard above could pass on a file that still renders a second
    navigation column.
    """
    assert _second_shell_violations(WORKSPACE_SHELL) == [], (
        "the repaired layout must not be reported"
    )
    reintroduced = WORKSPACE_SHELL.replace(
        '<div className="cg-canvas">',
        '<aside className="cg-rail">{rail}</aside>\n      <div className="cg-canvas">',
    )
    assert reintroduced != WORKSPACE_SHELL, "control did not mutate -- detector unproven"
    assert "cg-rail" in _second_shell_violations(reintroduced), (
        "the detector failed to notice a reintroduced second rail"
    )


def test_negative_control_a_second_nav_renderer_is_detected():
    """A second file rendering the grouped navigation would be caught.

    The control calls :func:`_navigation_renderers` — the same function the live
    assertion uses — so it can actually fail. The previous version restated the
    comprehension and passed even when the live detector's marker was renamed.
    """
    sources = _ts_sources()
    assert _navigation_renderers(sources) == [
        "web/arkadia_console/src/components/Shell.tsx"
    ], "the repaired tree must have exactly one navigation renderer"
    # Simulate a second renderer appearing in a layout file.
    simulated = dict(sources)
    simulated["web/arkadia_console/src/components/workspace/WorkspaceShell.tsx"] = (
        WORKSPACE_SHELL + "\n{NAV_GROUPS.map((g) => null)}\n"
    )
    assert _navigation_renderers(simulated) == [
        "web/arkadia_console/src/components/Shell.tsx",
        "web/arkadia_console/src/components/workspace/WorkspaceShell.tsx",
    ], "control did not produce a second renderer -- detector unproven"


# ---------------------------------------------------------------------------
# Context continuity: one project selection, remembered across a reload
# ---------------------------------------------------------------------------


#: The marks of a project selection that survives a reload and is re-validated
#: against the live list. A source missing any of these has a selection that is
#: lost on refresh or resurrects a stale id.
REMEMBERED_SELECTION_MARKERS = (
    "sessionStorage.getItem(ACTIVE_PROJECT_KEY)",
    "sessionStorage.setItem(ACTIVE_PROJECT_KEY",
    "rememberProject(null)",
    "projectRows.some((row) => row.id === activeProjectId)",
)


def _missing_remembered_selection_markers(source: str) -> list[str]:
    """Marks of a persisted, re-validated project selection that ``source`` omits.

    Module level so the live assertion and its negative control call the *same*
    code. The control previously re-checked one marker inline, so it could not
    fail for any edit to the live detector.
    """
    return [marker for marker in REMEMBERED_SELECTION_MARKERS if marker not in source]


def test_project_selection_is_remembered_and_revalidated():
    """The active project survives a reload, and a stale id is dropped.

    A selection held only in component state is lost on refresh, which silently
    unscopes the next conversation — the "navigation discards active work"
    failure. It is remembered in session storage and re-validated against the
    live project list, so a remembered id that no longer exists is cleared
    rather than trusted.
    """
    ctx = (SRC / "lib" / "projectContext.tsx").read_text(encoding="utf-8")
    missing = _missing_remembered_selection_markers(ctx)
    assert missing == [], (
        "the project selection is not persisted or re-validated; missing: " + ", ".join(missing)
    )


def test_negative_control_a_state_only_selection_would_be_detected():
    """The detector is proven: a state-only selection fails it.

    The control calls :func:`_missing_remembered_selection_markers` — the same
    function the live assertion uses — so it can actually fail. The previous
    version re-checked one marker inline and stayed green even when the live
    detector's markers were renamed.
    """
    ctx = (SRC / "lib" / "projectContext.tsx").read_text(encoding="utf-8")
    assert _missing_remembered_selection_markers(ctx) == [], (
        "the repaired context must not be reported"
    )
    state_only = ctx.replace("sessionStorage.getItem(ACTIVE_PROJECT_KEY)", "null")
    assert state_only != ctx, "control did not mutate -- detector unproven"
    assert _missing_remembered_selection_markers(state_only) == [
        "sessionStorage.getItem(ACTIVE_PROJECT_KEY)"
    ], "a selection that is not restored from storage must be reported"


def test_solariun_reads_the_shared_project_selection():
    """Solariun must not hold a second copy of "which project am I in"."""
    solariun = (SRC / "pages" / "SolariunPage.tsx").read_text(encoding="utf-8")
    assert "useProjectContext()" in solariun, (
        "Solariun does not read the shared project context"
    )
    assert "useState<string | null>(null)" not in solariun, (
        "Solariun still holds its own project selection state"
    )
    assert "selectProject(" in solariun, "Solariun does not write the shared selection"


# ---------------------------------------------------------------------------
# Weaver depth: real contracts composed, unpublished dimensions declared
# ---------------------------------------------------------------------------


#: A module-level worker roster in the orchestrator is the fabricated worker list
#: the surface's own doctrine forbids: "It refuses to invent workers, progress
#: percentages, retry counters or live telemetry." Weaver composes real read
#: models; a roster declared here would be invented state with no contract behind
#: it. Module level so the live assertion and its control call the *same* code.
FABRICATED_ROSTER_MARKERS = ("const WORKERS", "const WORKER_ROSTER")


def _fabricated_worker_rosters(source: str) -> list[str]:
    """Fabricated worker-roster declarations in a source file."""
    return [marker for marker in FABRICATED_ROSTER_MARKERS if marker in source]


def test_weaver_composes_real_read_models_and_declares_the_gaps():
    """Weaver surfaces real state and names what the contracts do not publish."""
    weaver = (SRC / "components" / "weaver" / "WeaverOrchestration.tsx").read_text(encoding="utf-8")
    for component in ("ApprovalLedger", "LabWorkLoop", "LabSessionList", "LabAgentRegistry"):
        assert f"<{component}" in weaver, f"Weaver does not compose the existing {component}"
    # The unpublished dimensions are declared, not rendered as empty lists.
    assert "UNAVAILABLE_DIMENSIONS" in weaver, "Weaver declares no unavailable dimensions"
    # AO-006 closed three of the four gaps at the contract level: the run record
    # now publishes depends_on / subtasks / attempt / retryable and the unified
    # canvas projects them. Declaring them unavailable would now be a false
    # statement about the contracts, so the guard asserts the opposite: they are
    # no longer declared, and the one remaining real gap (live telemetry) is.
    for closed in ("Task dependencies", "Subtask decomposition", "Retry conditions"):
        assert closed not in weaver, (
            f"Weaver still declares {closed!r} unavailable, but AO-006 publishes it"
        )
    assert "Live worker telemetry" in weaver, (
        "Weaver must still declare the live-telemetry gap it cannot close"
    )
    # And it must not invent workers or live telemetry.
    assert _fabricated_worker_rosters(weaver) == [], (
        "Weaver declares a fabricated worker roster: " f"{_fabricated_worker_rosters(weaver)}"
    )
    assert "EventSource" not in weaver, "Weaver opens a live stream the backend does not serve"
    assert "setInterval" not in weaver, "Weaver polls without declaring it"


# AO4-08: the no-polling assertion above only ever inspected the orchestrator.
# Weaver's real behaviour is the behaviour of the components it *composes*, so a
# `setInterval` added to `ApprovalLedger` (or any other composed panel) would
# have passed the guard while polling on the Weaver surface. The guard is
# widened to the composed set — and deliberately NOT to the whole console, so
# legitimate polling in unrelated surfaces stays allowed.
WEAVER_COMPOSED_COMPONENTS = (
    "components/weaver/WeaverOrchestration.tsx",
    "components/weaver/ApprovalLedger.tsx",
    "components/lab/LabWorkLoop.tsx",
    "components/lab/LabSessionList.tsx",
    "components/lab/LabAgentRegistry.tsx",
)


#: Patterns that mean "this component polls or opens a live stream the backend
#: does not serve". Weaver's orchestration contracts publish no such transport,
#: so any of these in a composed component is undeclared live state.
POLLING_PATTERNS = ("setInterval", "setTimeout(", "EventSource", "WebSocket(")


def _undeclared_polling_offenders(sources: dict[str, str]) -> list[str]:
    """``relative: pattern`` for every source that polls or opens a live stream.

    Module level so the live assertion and its negative control call the *same*
    code. The control previously appended a pattern and re-checked the literal
    inline, which could not fail for any edit to the live detector.
    """
    offenders = []
    for relative, source in sorted(sources.items()):
        for pattern in POLLING_PATTERNS:
            if pattern in source:
                offenders.append(f"{relative}: {pattern}")
    return offenders


def test_no_undeclared_polling_anywhere_in_the_weaver_composition():
    """Every component Weaver actually renders must be free of undeclared polling."""
    sources = {}
    for relative in WEAVER_COMPOSED_COMPONENTS:
        path = SRC / relative
        assert path.exists(), f"Weaver composition names a missing component: {relative}"
        sources[relative] = path.read_text(encoding="utf-8")
    assert _undeclared_polling_offenders(sources) == [], (
        "Weaver's composed components poll or open a live stream the backend does "
        f"not serve: {_undeclared_polling_offenders(sources)}"
    )


def test_negative_control_polling_in_a_composed_component_is_detected():
    """The widened guard must actually fire — proven against a mutated copy.

    The control calls :func:`_undeclared_polling_offenders` — the same function
    the live assertion uses — so it can actually fail. The previous version
    re-checked the ``setInterval`` literal inline and never exercised the live
    detector, so the live assertion could be disarmed with no red test.
    """
    relative = "components/weaver/ApprovalLedger.tsx"
    source = (SRC / relative).read_text(encoding="utf-8")
    assert _undeclared_polling_offenders({relative: source}) == [], (
        "the repaired component must not poll"
    )
    mutated = source + "\nconst _poll = setInterval(() => {}, 1000);\n"
    assert _undeclared_polling_offenders({relative: mutated}) == [f"{relative}: setInterval"], (
        "an undeclared poll in a composed component must be reported"
    )


def test_polling_remains_allowed_outside_the_weaver_composition():
    """The guard is scoped: it must not become a global no-polling rule."""
    # A surface that legitimately polls (or may) is not in the composed set, so
    # the guard above does not constrain it. This asserts the scope itself, so a
    # future edit cannot quietly widen the ban to the whole console.
    assert "components/weaver/WeaverOrchestration.tsx" in WEAVER_COMPOSED_COMPONENTS
    assert len(WEAVER_COMPOSED_COMPONENTS) == 5
    for relative in WEAVER_COMPOSED_COMPONENTS:
        assert relative.startswith(("components/weaver/", "components/lab/")), (
            "the no-polling guard must stay scoped to the Weaver composition"
        )


def test_negative_control_a_fabricated_worker_list_would_be_detected():
    """A hardcoded worker roster is the failure this guard exists to catch.

    The control calls :func:`_fabricated_worker_rosters` — the same function the
    live assertion uses — so it can actually fail. The previous version appended a
    roster and re-checked the marker inline; it never exercised the live detector,
    so the live assertion could be disarmed with no red test.
    """
    weaver = (SRC / "components" / "weaver" / "WeaverOrchestration.tsx").read_text(encoding="utf-8")
    assert _fabricated_worker_rosters(weaver) == [], "the repaired Weaver must not be reported"
    fabricated = weaver + '\nconst WORKERS = [{ id: "w1", progress: 42 }];\n'
    assert _fabricated_worker_rosters(fabricated) == ["const WORKERS"], (
        "a fabricated worker roster must be reported"
    )


# ---------------------------------------------------------------------------
# Solariun: persistent workspace reuses canonical contracts
# ---------------------------------------------------------------------------


def test_solariun_workspace_reuses_canonical_project_contracts():
    """The persistent workspace reads the existing project sub-resources."""
    panel = (SRC / "components" / "solariun" / "SolariunWorkspace.tsx").read_text(encoding="utf-8")
    for helper in ("solspireProjectTasks", "solspireProjectFiles", "solspireProjectEvents"):
        assert helper in panel, f"the Solariun workspace does not read {helper}"
    # No new persistence: it must not define its own fetch or store.
    assert "fetch(" not in panel, "the Solariun workspace bypasses the canonical api client"
    assert "localStorage" not in panel, "the Solariun workspace introduces a second store"
    # The unpublished document capability is declared, not faked.
    assert "solariun-documents-unavailable" in panel, (
        "the Solariun workspace does not declare the missing document contract"
    )
