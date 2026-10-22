/**
 * The unified application shell: persistent navigation, workspace identity, and
 * the shared aurora field. Mounted once by `App`.
 */
import { useCallback, useEffect, useRef, type ReactNode } from "react";
import { SURFACES, SURFACE_BY_ID, type SurfaceId } from "../lib/surfaces";
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
      type="button"
      aria-current={active ? "page" : undefined}
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
  const mainRef = useRef<HTMLElement>(null);
  const mobileNavRef = useRef<HTMLElement>(null);

  // A route change moves to a new surface, but the browser keeps the keyboard
  // focus (and scroll position) where the previous surface left it. Focus the
  // content landmark so keyboard and screen-reader users resume at the top of
  // the new surface instead of in the navigation that is now behind them.
  useEffect(() => {
    mainRef.current?.focus();
  }, [current]);

  // The mobile strip is wider than the viewport and scrolls horizontally, so a
  // surface whose item sits past the right edge would render with no visible
  // current-page marker — the one thing the strip exists to show. Reveal the
  // active item on every route change. Only `scrollLeft` is adjusted: a
  // `scrollIntoView` here would also move the page vertically. The scroll is
  // instant (no `behavior: "smooth"`), so it needs no reduced-motion guard.
  //
  // A route change is not the only event that can hide the active item: narrowing
  // the viewport grows the strip's scrollable range without moving `scrollLeft`,
  // which strands the active item off-screen again (measured 4/4 at 700→400,
  // 600→360, 390→320 and 767→300, active item past the right edge every time).
  // The reveal is therefore a callback invoked from both effects below, rather
  // than logic owned by the route effect alone.
  const revealActiveItem = useCallback(() => {
    const nav = mobileNavRef.current;
    // `md:hidden` leaves the strip in the DOM with no layout box on desktop;
    // every rect reads 0 there, which would compute a spurious offset.
    if (!nav || nav.clientWidth === 0) return;
    const active = nav.querySelector<HTMLElement>('[aria-current="page"]');
    if (!active) return;
    const navBox = nav.getBoundingClientRect();
    const box = active.getBoundingClientRect();
    const pad = 8; // matches the strip's `p-2`
    if (box.left < navBox.left + pad) {
      nav.scrollLeft -= navBox.left + pad - box.left;
    } else if (box.right > navBox.right - pad) {
      nav.scrollLeft += box.right - (navBox.right - pad);
    }
  }, []);

  useEffect(() => {
    revealActiveItem();
  }, [current, revealActiveItem]);

  // Observed on the strip itself rather than on `window.resize`: the strip's
  // scrollable range changes whenever its own box changes, which covers a
  // viewport resize without a second, independent breakpoint constant.
  useEffect(() => {
    const nav = mobileNavRef.current;
    if (!nav || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => revealActiveItem());
    observer.observe(nav);
    return () => observer.disconnect();
  }, [revealActiveItem]);

  return (
    <div className="flex min-h-screen bg-ink text-white">
      <a
        href="#main-content"
        data-testid="skip-to-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:border focus:border-gold/40 focus:bg-panel focus:px-3 focus:py-2 focus:font-mono focus:text-[11px] focus:uppercase focus:tracking-widest focus:text-gold"
      >
        Skip to content
      </a>
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
        <nav aria-label="Primary navigation" className="flex flex-col gap-1">
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
        <nav
          ref={mobileNavRef}
          aria-label="Primary navigation (mobile)"
          className="flex gap-1 overflow-x-auto border-b border-line bg-panel/40 p-2 md:hidden"
        >
          {NAV_SURFACES.map((s) => (
            <NavLink key={s.id} active={current === s.id} label={s.name} accent={s.accent} onClick={() => onNavigate(s.id)} />
          ))}
        </nav>
        <main
          id="main-content"
          ref={mainRef}
          tabIndex={-1}
          aria-label={`${SURFACE_BY_ID[current].name} content`}
          className="min-w-0 flex-1 focus:outline-none"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
