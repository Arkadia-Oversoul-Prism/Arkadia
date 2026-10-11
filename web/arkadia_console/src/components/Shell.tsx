/**
 * The unified application shell: persistent navigation, workspace identity, and
 * the shared aurora field. Mounted once by `App`.
 */
import type { ReactNode } from "react";
import { SURFACES, type SurfaceId } from "../lib/surfaces";
import { useAuth } from "../contexts/AuthContext";

const NAV_SURFACES = SURFACES.filter((s) => s.nav !== false);

function NavLink({
  active,
  label,
  accent,
  onClick,
}: {
  active: boolean;
  label: string;
  accent: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      data-testid={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
      className={`rounded-lg px-3 py-2 text-left font-mono text-[11px] uppercase tracking-[0.16em] transition ${
        active ? `bg-white/5 ${accent}` : "text-white/45 hover:text-white/80"
      }`}
    >
      {label}
    </button>
  );
}

export function Shell({
  current,
  onNavigate,
  children,
}: {
  current: SurfaceId;
  onNavigate: (id: SurfaceId) => void;
  children: ReactNode;
}) {
  const { profile, isAuthenticated, identityState, signOutNow } = useAuth();

  return (
    <div className="flex min-h-screen bg-ink text-white">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-line bg-panel/40 p-4 md:flex">
        <div className="mb-6 px-2">
          <p className="font-display text-lg tracking-[0.2em] text-gold">ARKADIA</p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
            {isAuthenticated && profile ? profile.display_name : "Not signed in"}
          </p>
          {isAuthenticated ? (
            <button
              onClick={() => void signOutNow()}
              data-testid="nav-sign-out"
              className="mt-2 font-mono text-[10px] uppercase tracking-widest text-white/40 hover:text-white/80"
            >
              Sign out
            </button>
          ) : (
            <button
              onClick={() => onNavigate("login")}
              data-testid="nav-sign-in"
              className="mt-2 font-mono text-[10px] uppercase tracking-widest text-gold/80 hover:text-gold"
            >
              Sign in
            </button>
          )}
        </div>
        <nav className="flex flex-col gap-1">
          {NAV_SURFACES.map((s) => (
            <NavLink key={s.id} active={current === s.id} label={s.name} accent={s.accent} onClick={() => onNavigate(s.id)} />
          ))}
        </nav>
        <div className="mt-auto px-2 pt-6">
          <p className="font-mono text-[10px] uppercase tracking-widest text-white/30">
            identity · {identityState}
          </p>
          <p className="mt-1 text-[11px] text-white/30">Human authority remains the decision boundary.</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile navigation: the same surfaces, no second global nav bar. */}
        <nav className="flex gap-1 overflow-x-auto border-b border-line bg-panel/40 p-2 md:hidden">
          {NAV_SURFACES.map((s) => (
            <NavLink key={s.id} active={current === s.id} label={s.name} accent={s.accent} onClick={() => onNavigate(s.id)} />
          ))}
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
