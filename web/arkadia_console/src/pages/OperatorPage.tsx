/**
 * Operator — the reconciled governance console, as a surface of the one shell.
 *
 * This surface was a second React application (`web/console`) with its own
 * `react-router-dom` `BrowserRouter`, its own `/operator` + `/n-atlas-lab`
 * mounts, its own stylesheet and its own API client. It is now a section-addressed
 * surface of the canonical application:
 *
 *   - routing is the one `lib/router.ts` over `lib/surfaces.ts`;
 *   - navigation is the shell's, with the surface's own views on the shared
 *     `SurfaceLenses` strip (one control for every lensed surface);
 *   - the boundary instances are addressed at `/operator/boundary/<id>`, a nested
 *     shape this surface declares via `SurfaceDef.param` rather than a second
 *     router;
 *   - the stylesheet is scoped under `.ark-operator` so the shared tokens and
 *     Tailwind utilities of every other surface are untouched.
 *
 * What was NOT changed: every claim, posture ladder, evidence citation, boundary
 * instance and read-only API path is migrated verbatim. This surface's whole value
 * is that it says what can be proven and names what cannot, so the wording is
 * carried across rather than paraphrased.
 */
import { Page, Panel } from "../components/ui";
import { SurfaceLenses } from "../components/SurfaceLenses";
import type { SurfaceId } from "../lib/surfaces";
import { StandingBanner } from "../operator/components/ui";
import { STANDING_STATES } from "../operator/lib/standing";
import { Spine } from "../operator/surfaces/Spine";
import { BoundaryInspector } from "../operator/surfaces/BoundaryInspector";
import { BoundaryView } from "../operator/surfaces/BoundaryView";
import { WorkConsequence } from "../operator/surfaces/WorkConsequence";
import { Authority } from "../operator/surfaces/Authority";
import { MieLab } from "../operator/surfaces/MieLab";
import { NAtlasTester } from "../operator/surfaces/NAtlasTester";
import { SecurityVerification } from "../operator/surfaces/SecurityVerification";
import "../operator/operator.css";

/**
 * The surface's views. `boundary` is deliberately absent: a boundary instance is
 * reached from the spine or the inspector, not from the strip, and it carries its
 * own id — listing it here would render a control that cannot name a target.
 */
const SECTIONS = [
  { id: "spine", label: "Spine" },
  { id: "inspector", label: "Inspector" },
  { id: "authority", label: "Authority" },
  { id: "work", label: "Work" },
  { id: "mie-lab", label: "MIE Lab" },
  { id: "n-atlas", label: "N-ATLaS" },
  { id: "security", label: "Security" },
];

export function OperatorPage({
  section = "spine",
  param,
  onNavigate,
}: {
  section?: string;
  param?: string;
  onNavigate: (id: SurfaceId, section?: string, param?: string) => void;
}) {
  const openBoundary = (id: string) => onNavigate("operator", "boundary", id);
  const openSection = (next: string) => onNavigate("operator", next);

  const body = (() => {
    if (section === "boundary") {
      return <BoundaryView id={param} onOpenSection={openSection} />;
    }
    switch (section) {
      case "spine":
        return <Spine onOpenBoundary={openBoundary} />;
      case "inspector":
        return <BoundaryInspector onOpenBoundary={openBoundary} />;
      case "authority":
        return <Authority />;
      case "work":
        return <WorkConsequence onOpenBoundary={openBoundary} />;
      case "mie-lab":
        return <MieLab />;
      case "n-atlas":
        return <NAtlasTester />;
      // The retired application served this view at `/security-verification` (its
      // sidebar entry "07 · Security Verification"). The canonical id here is
      // `security`, but a rename without an alias silently converts a working deep
      // link into the "not a view of this surface" panel below: the address still
      // resolves, so nothing looks broken, and the view the link named is gone.
      case "security-verification":
      case "security":
        return <SecurityVerification />;
      default:
        return (
          <Panel className="border-gold/30">
            <p className="font-display text-lg text-gold" data-testid="operator-unknown-section">
              "{section}" is not a view of this surface
            </p>
            <p className="mt-1 text-sm text-white/60">
              The views this surface declares are{" "}
              {SECTIONS.map((s) => `"${s.id}"`).join(", ")}. Nothing is rendered for an undeclared
              view, so the address bar cannot claim a view this surface does not have.
            </p>
          </Panel>
        );
    }
  })();

  return (
    <Page
      title="Operator"
      subtitle="Boundary posture, evidence, and authority — what is enforced, what is only declared, and what remains unverified."
    >
      <SurfaceLenses
        surface="operator"
        lenses={SECTIONS}
        section={section}
        accent="text-gold"
        onNavigate={onNavigate}
      />

      <div className="ark-operator" data-testid="operator-surface">
        {/* Standing non-claims: first-class, persistent, never dismissible. They
            are the reason this surface exists, so they are not nested inside a
            view that some other view could replace. */}
        <div className="standing-bar">
          {STANDING_STATES.map((s) => (
            <StandingBanner key={s.id} state={s} />
          ))}
        </div>

        {body}
      </div>
    </Page>
  );
}
