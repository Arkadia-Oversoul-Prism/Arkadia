/**
 * A surface's lens strip — the sub-view switcher inside a surface.
 *
 * One control for every surface that has lenses (directive §5.1). Each lens is a
 * real navigation to `<surface-path>/<lens-id>` through the shared router, so the
 * strip and the address bar cannot disagree. A lens is never a decorative pill:
 * if it cannot navigate, it is not rendered as a control.
 *
 * The strip is a *labelled navigation landmark*, not an anonymous `<div>`. It is
 * a navigation region inside the surface, so a screen-reader or keyboard user must
 * be able to reach it as a landmark and hear what it switches; the archived Prism
 * rendered the same strip as `<nav aria-label="NovaNet primary navigation">`, and a
 * bare `<div>` of buttons announces only a pile of unlabelled controls. The name is
 * derived from the surface registry (`SURFACE_BY_ID`) rather than hardcoded, so the
 * one route/surface declaration stays the single source of that vocabulary.
 */
import { SURFACE_BY_ID, type SurfaceId } from "../lib/surfaces";

export interface SurfaceLens {
  id: string;
  label: string;
}

export function SurfaceLenses({
  surface,
  lenses,
  section,
  accent,
  onNavigate,
}: {
  surface: SurfaceId;
  lenses: SurfaceLens[];
  section: string;
  accent: string;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  return (
    <nav
      aria-label={`${SURFACE_BY_ID[surface].name} views`}
      data-testid={`${surface}-lenses`}
      className="mb-4 flex flex-wrap gap-1"
    >
      {lenses.map((l) => (
        <button
          key={l.id}
          type="button"
          onClick={() => onNavigate(surface, l.id)}
          aria-current={section === l.id ? "page" : undefined}
          data-testid={`surface-lens-${l.id}`}
          className={`rounded px-3 py-1 font-mono text-[11px] uppercase tracking-widest transition ${
            section === l.id ? `bg-white/5 ${accent}` : "text-white/40 hover:text-white/80"
          }`}
        >
          {l.label}
        </button>
      ))}
    </nav>
  );
}
