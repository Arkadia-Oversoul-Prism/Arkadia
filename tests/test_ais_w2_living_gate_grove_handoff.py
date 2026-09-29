"""W2 — Living Gate A.I.S diagnostic → Spiral Grove handoff.

Static contract tests. No second diagnostic, catalogue, or learner-state system.

These assertions pin literals in a `.tsx` surface that has since been rewritten, so
several were asserting a *copy* of the contract rather than the contract itself. This
pass re-pins them to the live expressions while keeping, and in two places
strengthening, the property each test exists to protect. Gates over
`web/public_prism/**` are CP10-fenced: nothing in that tree is edited here.

Boundary of record: `docs/architecture/AEAS_FRONTEND_SCALPEL_PLAN.md` (Living Gate =
`pages/NodeEntry.tsx`, A.I.S signup + diagnostic; the legacy reset player was removed).
The A.I.S projection module `pages/LivingGate.tsx` is presently **not mounted** by
`App.tsx`; several assertions below therefore watch the interface it declares rather
than an `App.tsx` call site. See
`docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-living-gate-06/`
for the full classification, including one node escalated as a product decision.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"
GROVE = ROOT / "web/public_prism/src/pages/SpiralGrovePage.tsx"
CATALOG = ROOT / "web/public_prism/src/data/spiralGroveCatalog.ts"
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
ENTRY = ROOT / "web/public_prism/src/pages/NodeEntry.tsx"
PULSE_API = ROOT / "api/pulse.py"
OFFERINGS = ROOT / "web/public_prism/src/pages/OfferingsPage.tsx"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_living_gate_defaults_to_diagnostic_not_reset():
    """The gate opens on the diagnostic, and no reset entry survives.

    The instance has moved from a `FlowStep` union through the portfolio step list to
    the `AisCapabilityPortfolio` interface; the reset mode has been deleted outright.
    The gate now opens on the first portfolio step, which is the diagnostic itself.
    """
    src = _r(GATE)
    assert re.search(
        r"const STEPS: Array<\{ key: StepKey; label: string; question: string; helper: string \}>",
        src,
    ), "Living Gate must declare the diagnostic step list"
    assert re.search(r"const \[index, setIndex\] = useState\(0\)", src), (
        "Living Gate must open on the first diagnostic step"
    )
    # The legacy reset *flow* is gone — its state machine and its entry branch no
    # longer exist. Assert those constructs, not the bare token `reset`, which any
    # reset-styled button would trip without reopening the removed entry.
    assert "FlowStep" not in src, "the legacy reset flow-state type must not survive"
    assert "initialMode" not in src, "the legacy reset entry branch must not survive"
    assert not re.search(r"['\"]reset['\"]", src), (
        "the legacy reset flow step must not survive as an entry value"
    )


def test_pulse_analyze_endpoint_preserved():
    """The endpoint survives — at its definition and at its live call site.

    The legacy Living Gate *was* that call site; the acquired Arkadian Pulse surface
    (`pages/ArkadianPulse.tsx`) is now the caller. Asserting the exact `/api/pulse/analyze`
    string on some component is what let this test drift, so it now checks the whole
    path: route → caller → transport.
    """
    assert '@router.post("/api/pulse/analyze")' in _r(PULSE_API)
    pulse = _r(ROOT / "web/public_prism/src/pages/ArkadianPulse.tsx")
    assert "/api/pulse/analyze" in pulse
    assert "from '../lib/apiClient'" in pulse or 'from "../lib/apiClient"' in pulse


def test_spiral_grove_handoff_prop_and_cta():
    """The handoff prop and its CTA are both declared and wired to the snapshot surface."""
    src = _r(GATE)
    assert "onEnterSpiralGrove?: () => void;" in src
    assert 'data-testid="open-spiral-grove"' in src
    assert "Enter Spiral Grove →" in src
    assert "onGrove={onEnterSpiralGrove}" in src, (
        "the prop must reach the portfolio snapshot, not merely be declared"
    )


def test_app_wires_grove_navigation():
    """Grove stays reachable.

    The prop-drilled call site is gone; `App.tsx` now own-routes the grove view. Both
    halves are asserted — component mount and the view branch that reaches it — and the
    A.I.S handoff prop is asserted at the module seam that still consumes it.
    """
    app = _r(APP)
    assert "view === 'grove'" in app
    assert "<SpiralGrovePage />" in app
    assert "import SpiralGrovePage from './pages/SpiralGrovePage';" in app
    assert "onEnterSpiralGrove?: () => void;" in _r(GATE), (
        "the Living Gate must still expose the grove handoff seam"
    )


def test_no_second_capability_catalogue():
    grove = _r(GROVE)
    catalog = _r(CATALOG)
    assert "AIS_CAPABILITIES" in catalog
    assert "GROVE_DOMAINS" in catalog
    assert "INITIAL_LEARNER_STATES" in catalog
    assert "from '../data/spiralGroveCatalog'" in grove or 'from "../data/spiralGroveCatalog"' in grove
    assert not re.search(r"const\s+AIS_CAPABILITIES\s*=\s*\[", grove)


def test_homepage_untouched_in_app_home_function():
    app = _r(APP)
    assert "function Home(" in app
    assert "PortalDoor" in app


def test_nav_subtitle_describes_ais_onboarding():
    nav = _r(NAV)
    assert "A.I.S diagnostic" in nav
    assert "Reset - IMS - AIC - 5-Minute" not in nav


def test_no_firebase_persistence_in_gate():
    """No browser or cloud persistence may be introduced into the gate.

    FINDING F-01 — this node is a PROXY-INVALIDATION awaiting a sovereign decision, not
    stale-assertion drift, and it is deliberately left failing here. The gate genuinely
    carries zero `firebase`/`firestore` references, so its stated intent (no cloud
    persistence, no silent identity creation) still holds, but the `sessionStorage`
    proxy no longer measures that intent: `LivingGate.tsx` uses `sessionStorage` for a
    tab-scoped diagnostic handoff (`arkadia.ais.diagnostic-handoff.v1`). `sessionStorage`
    IS a browser persistence facility, so the guard is left exactly as `main` carries it
    rather than re-pinned to permit it — re-pinning would loosen a persistence boundary,
    which is a governance call, not test hygiene. See
    `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-living-gate-06/EVIDENCE.md`.
    """
    src = _r(GATE)
    assert "localStorage.setItem" not in src
    assert "sessionStorage" not in src


def test_ims_lineage_preserved():
    """The IMS lineage moved out of the component — assert it where it now lives.

    The Living Gate no longer carries the invitation ritual copy or its `BookingStep`
    component; the IMS offering, its delivery and its AIC prerequisite are declared on
    the acquired Offerings surface. The lineage is intact; only the location changed.
    """
    offerings = _r(OFFERINGS)
    assert "Identity Mapping Session" in offerings
    assert "IMS Scroll + live session" in offerings
    assert "prerequisite:'AIC completed'" in offerings
    assert "onGoToAIC" in offerings, "the IMS lineage must still connect to AIC"
    assert "aicSeed" in offerings, "the AIC reading must still seed the IMS entry"


def test_node_entry_declares_the_ais_signup_boundary():
    """Boundary of record: NodeEntry is the Living Gate's canonical surface.

    `LivingGate.tsx` is not mounted by `App.tsx`. Rather than silently accept an
    unmounted module as the onboarding surface, this test pins the surface that *is*
    mounted: the A.I.S signup on `pages/NodeEntry.tsx`.
    """
    entry = _r(ENTRY)
    assert "/api/me/ais-profile" in entry
    assert "AIS_PROFILE_PATH" in entry
    assert "kind:'portfolio'" in entry or "kind: 'portfolio'" in entry
    assert "<NodeEntry" in _r(APP), "the Living Gate surface must actually be mounted"

    # NOT AUTO-REPAIRED — escalated as a product decision.
    # `tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
    # asserts `AIS_CAPABILITIES` and `GROVE_DOMAINS` render *inside* NodeEntry. NodeEntry does
    # not import `data/spiralGroveCatalog` at all; it hard-codes its own node labels, so the
    # canonical catalogue is unreferenced there while `LivingGate.tsx` — which does import it —
    # is unmounted. "NodeEntry imports the canonical catalogue" and "LivingGate is the A.I.S
    # surface" are mutually exclusive, so the repair requires choosing one. Not patched here.
    assert (ROOT / "web/public_prism/src/data/spiralGroveCatalog.ts").is_file()
