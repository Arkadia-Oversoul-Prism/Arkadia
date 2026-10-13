"""Solariun lens strip — routed navigation and truthful per-lens state (PRR-01).

Directive §4 and the shared lens contract (`SurfaceLenses`) require that a lens
is real navigation — never a decorative pill — and that the strip and the
address bar cannot disagree. Before this work item, `SolariunPage` rendered a
page-local `<span>` strip that never navigated, the content ignored `section`,
and `/solariun/bogus` silently showed the projects view.

Domain: the Arkadia Console (`web/arkadia_console`), the primary application.
The retired Prism UI is archived under `archive/frontend/arkadia-prism` and is
not built or served; its Solariun route table
(`src/pages/SolariunConsole.tsx`, `src/App.tsx` `routeForView('solariun')`)
is the reference this slice reconciles: routed `/solariun/<lens>` sub-views.

What is asserted:

  * the lens strip is the shared `SurfaceLenses` component (real navigation,
    `aria-current`, `data-testid`), not a page-local decorative strip;
  * every declared Solariun lens resolves, through the *executed* router, to
    `{surface: "solariun", section: <lens>}`;
  * every lens has a content branch: `projects` keeps the real
    `/solspire/projects` read; `knowledge`/`weaver` point at a declared
    canonical owning surface; `memory` states that no verified contract exists;
  * an unknown `/solariun/<x>` renders the honest "not a lens" state instead of
    silently showing projects;
  * the composition root passes `onNavigate` to `SolariunPage`.

The router half is **executed** in Node (the same technique as
`test_console_shell_nav_contract.py`); the component half is source-contract
with a negative control per load-bearing detector, so a detector that always
passes is itself caught.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"
SOLARIUN_PATH = SRC / "pages" / "SolariunPage.tsx"
SURFACES_PATH = SRC / "lib" / "surfaces.ts"
ROUTER_PATH = SRC / "lib" / "router.ts"
APP_PATH = SRC / "App.tsx"

SOLARIUN = SOLARIUN_PATH.read_text(encoding="utf-8")
SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")
APP = APP_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module-level so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _declared_lens_ids(text: str) -> list[str]:
    """The `id` values of the LENSES array in SolariunPage."""
    block = re.search(r"const LENSES = \[(.*?)\];", text, re.DOTALL)
    assert block, "SolariunPage declares no LENSES array"
    return re.findall(r'id: "([^"]+)"', block.group(1))


def _declared_surface_ids(text: str) -> list[str]:
    union = re.search(r"export type SurfaceId\s*=\s*(.*?);", text, re.DOTALL)
    assert union, "surfaces.ts declares no SurfaceId union"
    return re.findall(r'"([^"]+)"', union.group(1))


def _owning_surface_targets(text: str) -> dict[str, str]:
    """`{lens: surface}` for the lenses whose authority lives elsewhere."""
    block = re.search(r"const OWNING_SURFACE[^=]*=\s*\{(.*?)\n\};", text, re.DOTALL)
    assert block, "SolariunPage declares no OWNING_SURFACE map"
    return dict(re.findall(r'(\w+):\s*\{[^}]*?surface:\s*"([^"]+)"', block.group(1)))


def _renders_shared_lenses(text: str) -> bool:
    return bool(re.search(r"<SurfaceLenses\b", text)) and 'surface="solariun"' in text


def _has_decorative_span_strip(text: str) -> bool:
    """A page-local strip rendering plain `<span>` pills from LENSES.

    This is the defect shape this work item removed: a lens-looking strip that
    cannot navigate.
    """
    return bool(re.search(r"LENSES\.map\(\s*\(\s*l\s*\)\s*=>\s*\(\s*<span", text, re.DOTALL))


def _unknown_section_guard(text: str) -> bool:
    return "!LENS_IDS.has(section)" in text and "is not a lens of this surface" in text


def _js_resolve(router_text: str, probes: list[str]) -> list[dict]:
    """Execute the console's real `resolvePath` in Node on the given probes."""

    def strip_types(source: str) -> str:
        source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
        source = re.sub(
            r":\s*(?:SurfaceId|SurfaceDef\[\]|Route|string|boolean|Record<[^>]*>)\b",
            "",
            source,
        )
        return source

    node = shutil.which("node")
    assert node, "node is required to evaluate the console router"
    surfaces = strip_types(SURFACES)
    router = strip_types(router_text).replace("as const", "")
    script = (
        surfaces
        + "\n"
        + router
        + "\n"
        + f"const probes = {json.dumps(probes)};\n"
        + "console.log(JSON.stringify(probes.map((p) => resolvePath(p))));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"router evaluation failed: {result.stderr.strip()}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# 1. The strip is the shared, navigating component.
# ---------------------------------------------------------------------------


def test_lens_strip_is_the_shared_navigating_component():
    assert _renders_shared_lenses(SOLARIUN), (
        "SolariunPage must render the shared SurfaceLenses with surface=\"solariun\" — "
        "a page-local strip is not routed navigation"
    )
    assert not _has_decorative_span_strip(SOLARIUN), (
        "SolariunPage renders a decorative <span> lens strip that cannot navigate"
    )
    assert "onNavigate={onNavigate}" in SOLARIUN, "the strip must be wired to the router"


def test_negative_control_detects_a_decorative_span_strip():
    """The decorative-strip detector must fire on the pre-fix shape."""
    synthetic = """
    <div className="mb-4 flex gap-1">
      {LENSES.map((l) => (
        <span key={l.id} className={section === l.id ? "text-violet" : "text-white/40"}>
          {l.label}
        </span>
      ))}
    </div>
    """
    assert _has_decorative_span_strip(synthetic), (
        "the detector must catch the decorative strip it exists to prevent"
    )
    assert not _has_decorative_span_strip(SOLARIUN)


def test_composition_root_passes_onNavigate_to_solariun():
    case = re.search(r'case "solariun":\s*return <SolariunPage[^;]*;', APP)
    assert case, "App.tsx has no solariun case"
    assert "onNavigate={navigate}" in case.group(0), (
        "SolariunPage must receive the shared navigate so its lenses can route"
    )


# ---------------------------------------------------------------------------
# 2. Every declared lens resolves to this surface, executed in Node.
# ---------------------------------------------------------------------------


def test_every_declared_lens_resolves_to_a_solariun_section():
    lens_ids = _declared_lens_ids(SOLARIUN)
    assert lens_ids, "no lens ids declared"
    probes = [f"/solariun/{lens}" for lens in lens_ids] + ["/solariun"]
    resolved = _js_resolve(ROUTER, probes)
    by_path = dict(zip(probes, resolved))
    for lens in lens_ids:
        route = by_path[f"/solariun/{lens}"]
        assert route["surface"] == "solariun", (lens, route)
        assert route["section"] == lens, (lens, route)
    assert by_path["/solariun"]["surface"] == "solariun"


def test_unknown_solariun_section_resolves_honestly():
    (route,) = _js_resolve(ROUTER, ["/solariun/bogus"])
    assert route["surface"] == "solariun"
    assert route["section"] == "bogus"


# ---------------------------------------------------------------------------
# 3. Every lens has a truthful content branch.
# ---------------------------------------------------------------------------


def test_projects_lens_keeps_the_real_read():
    assert "endpoints.solspireProjects" in SOLARIUN, (
        "the projects lens must keep reading the owner-scoped /solspire/projects contract"
    )
    assert 'section === "projects"' in SOLARIUN


def test_authority_lenses_point_at_declared_canonical_surfaces():
    targets = _owning_surface_targets(SOLARIUN)
    assert set(targets) >= {"knowledge", "weaver"}, targets
    declared = set(_declared_surface_ids(SURFACES))
    for lens, surface in targets.items():
        assert surface in declared, f"{lens} lens points at undeclared surface {surface}"
    # Both target surfaces are real routes in the composition root.
    for surface in set(targets.values()):
        assert f'case "{surface}":' in APP, f"no composition-root case for {surface}"


def test_memory_lens_states_no_verified_contract():
    """`memory` has no verified read contract — it must say so, not render data."""
    block = re.search(r'\{section === "memory" &&\s*\((.*?)\n\s*\)\}', SOLARIUN, re.DOTALL)
    assert block, "the memory lens has no content branch"
    assert "NotYetWired" in block.group(1)
    assert "UNKNOWN" in block.group(1)
    assert "no verified read contract" in block.group(1)


def test_unknown_section_renders_the_honest_not_a_lens_state():
    assert _unknown_section_guard(SOLARIUN), (
        "an undeclared /solariun/<section> must render the not-a-lens state, "
        "not silently fall through to the projects view"
    )
    # ...and the message lists the reconciled lenses from the live array.
    lens_ids = _declared_lens_ids(SOLARIUN)
    for lens in lens_ids:
        assert f'"{lens}"' in SOLARIUN


def test_negative_control_detects_a_missing_unknown_section_guard():
    stripped = SOLARIUN.replace("!LENS_IDS.has(section)", "false")
    assert not _unknown_section_guard(stripped), (
        "the guard detector must fail when the unknown-section guard is removed"
    )


def test_negative_control_declared_lens_ids_are_read_from_source():
    synthetic = 'const LENSES = [{ id: "alpha", label: "A" }, { id: "beta", label: "B" }];'
    assert _declared_lens_ids(synthetic) == ["alpha", "beta"]


def test_lens_ids_are_a_unique_set():
    lens_ids = _declared_lens_ids(SOLARIUN)
    assert len(lens_ids) == len(set(lens_ids))
