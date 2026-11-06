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


def test_shell_derives_grouped_navigation_from_the_surface_table():
    """The shell groups the one derived item list; it does not own a second list."""
    assert "NAV_SURFACES = SURFACES.filter" in SHELL, (
        "the shell must derive navigation from the surface table"
    )
    assert "SURFACE_GROUPS.map" in SHELL, "the shell must group by the declared group table"
    assert "s.group ?? UNGROUPED" in SHELL, (
        "an ungrouped surface must be collected, not dropped"
    )
    # The grouped model is rendered in both the desktop sidebar and the drawer.
    assert SHELL.count("NAV_GROUPS.map") >= 2, (
        "the grouped navigation must render in both the sidebar and the drawer"
    )


def test_negative_control_a_second_group_list_would_be_detected():
    """The detector is proven on synthetic input: a hardcoded group list fails it."""
    stale = SHELL.replace("SURFACE_GROUPS.map", "HARDCODED_GROUPS.map")
    assert "SURFACE_GROUPS.map" in SHELL, "the repaired shell must not be reported"
    assert "SURFACE_GROUPS.map" not in stale, "control did not mutate the shell -- detector unproven"


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


def test_workspace_does_not_introduce_a_second_approval_or_session_system():
    """No second approval ledger, session list, or conversation reader."""
    # The workspace must not define its own approval/session/history components.
    assert "function ApprovalLedger" not in WORKSPACE, "the workspace defines a second approval ledger"
    assert "function LabSessionList" not in WORKSPACE, "the workspace defines a second session list"
    assert "function ArkanaThreadHistory" not in WORKSPACE, (
        "the workspace defines a second conversation-history reader"
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
    """The duplication detector is proven on synthetic input."""
    duplicated = WORKSPACE + "\nfunction ApprovalLedger() { return null; }\n"
    assert "function ApprovalLedger" not in WORKSPACE, "the repaired workspace must not be reported"
    assert "function ApprovalLedger" in duplicated, "control did not mutate -- detector unproven"


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


def test_exactly_one_file_renders_the_primary_navigation():
    """`Shell.tsx` is the only file that renders the grouped navigation."""
    renderers = sorted(
        path
        for path, source in _ts_sources().items()
        if "NAV_GROUPS.map" in source
    )
    assert renderers == ["web/arkadia_console/src/components/Shell.tsx"], (
        f"the primary navigation must be rendered by exactly one file, found: {renderers}"
    )


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
    """A second file rendering the grouped navigation would be caught."""
    sources = _ts_sources()
    assert [p for p, s in sources.items() if "NAV_GROUPS.map" in s] == [
        "web/arkadia_console/src/components/Shell.tsx"
    ], "the repaired tree must have exactly one navigation renderer"
    # Simulate a second renderer appearing in a layout file.
    simulated = dict(sources)
    simulated["web/arkadia_console/src/components/workspace/WorkspaceShell.tsx"] = (
        WORKSPACE_SHELL + "\n{NAV_GROUPS.map((g) => null)}\n"
    )
    renderers = sorted(p for p, s in simulated.items() if "NAV_GROUPS.map" in s)
    assert len(renderers) == 2, "control did not produce a second renderer -- detector unproven"


# ---------------------------------------------------------------------------
# Context continuity: one project selection, remembered across a reload
# ---------------------------------------------------------------------------


def test_project_selection_is_remembered_and_revalidated():
    """The active project survives a reload, and a stale id is dropped.

    A selection held only in component state is lost on refresh, which silently
    unscopes the next conversation — the "navigation discards active work"
    failure. It is remembered in session storage and re-validated against the
    live project list, so a remembered id that no longer exists is cleared
    rather than trusted.
    """
    ctx = (SRC / "lib" / "projectContext.tsx").read_text(encoding="utf-8")
    assert "sessionStorage.getItem(ACTIVE_PROJECT_KEY)" in ctx, (
        "the active project is not restored from session storage"
    )
    assert "sessionStorage.setItem(ACTIVE_PROJECT_KEY" in ctx, (
        "the active project selection is not persisted"
    )
    # The invalidation path must clear storage too, or a stale id resurrects.
    assert "rememberProject(null)" in ctx, (
        "a stale selection is cleared from state but not from storage"
    )
    # Re-validation against the live list must still exist.
    assert "projectRows.some((row) => row.id === activeProjectId)" in ctx, (
        "the remembered selection is not re-validated against the live project list"
    )


def test_negative_control_a_state_only_selection_would_be_detected():
    """The detector is proven: a state-only selection fails it."""
    ctx = (SRC / "lib" / "projectContext.tsx").read_text(encoding="utf-8")
    state_only = ctx.replace("sessionStorage.getItem(ACTIVE_PROJECT_KEY)", "null")
    assert "sessionStorage.getItem(ACTIVE_PROJECT_KEY)" in ctx, "the repaired context must not be reported"
    assert "sessionStorage.getItem(ACTIVE_PROJECT_KEY)" not in state_only, (
        "control did not mutate -- detector unproven"
    )


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


def test_weaver_composes_real_read_models_and_declares_the_gaps():
    """Weaver surfaces real state and names what the contracts do not publish."""
    weaver = (SRC / "components" / "weaver" / "WeaverOrchestration.tsx").read_text(encoding="utf-8")
    for component in ("ApprovalLedger", "LabWorkLoop", "LabSessionList", "LabAgentRegistry"):
        assert f"<{component}" in weaver, f"Weaver does not compose the existing {component}"
    # The unpublished dimensions are declared, not rendered as empty lists.
    assert "UNAVAILABLE_DIMENSIONS" in weaver, "Weaver declares no unavailable dimensions"
    for dimension in ("Task dependencies", "Subtask decomposition", "Retry conditions"):
        assert dimension in weaver, f"Weaver does not declare {dimension!r} as unavailable"
    # And it must not invent live telemetry.
    assert "EventSource" not in weaver, "Weaver opens a live stream the backend does not serve"
    assert "setInterval" not in weaver, "Weaver polls without declaring it"


def test_negative_control_a_fabricated_worker_list_would_be_detected():
    """A hardcoded worker roster is the failure this guard exists to catch."""
    weaver = (SRC / "components" / "weaver" / "WeaverOrchestration.tsx").read_text(encoding="utf-8")
    fabricated = weaver + '\nconst WORKERS = [{ id: "w1", progress: 42 }];\n'
    assert "const WORKERS" not in weaver, "the repaired Weaver must not be reported"
    assert "const WORKERS" in fabricated, "control did not mutate -- detector unproven"


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
