/**
 * A surface's lens strip — the sub-view switcher inside a surface.
 *
 * One control for every surface that has lenses (directive §5.1). Each lens is a
 * real navigation to `<surface-path>/<lens-id>` through the shared router, so the
 * strip and the address bar cannot disagree. A lens is never a decorative pill:
 * if it cannot navigate, it is not rendered as a control.
 */
import type { SurfaceId } from "../lib/surfaces";

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
    <div className="mb-4 flex flex-wrap gap-1" data-testid={`${surface}-lenses`}>
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
    </div>
  );
}
