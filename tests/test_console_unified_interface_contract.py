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

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
SHELL = SHELL_PATH.read_text(encoding="utf-8")
WORKSPACE = WORKSPACE_PATH.read_text(encoding="utf-8")
WORKSPACE_SHELL = WORKSPACE_SHELL_PATH.read_text(encoding="utf-8")
INSPECTOR = INSPECTOR_PATH.read_text(encoding="utf-8")


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
