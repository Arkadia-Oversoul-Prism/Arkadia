/**
 * The unified application shell: persistent navigation, workspace identity, and
 * the shared aurora field. Mounted once by `App`.
 *
 * Crystal Glass (AO-001 beta): a fixed obsidian sidebar with a lit active
 * marker, a translucent header that carries the current surface and the
 * identity state, and a central workspace that scrolls independently. The
 * shell owns *where you are*; it never owns what a surface does.
 *
 * Contract invariants this file must keep (pinned by
 * tests/test_console_shell_nav_contract.py and
 * tests/test_console_lens_landmark_contract.py):
 *   - the navigation model is derived from the surface table, once;
 *   - the skip link targets a focusable `#main-content` landmark;
 *   - a route change moves focus to that landmark;
 *   - the document title is derived from the surface table;
 *   - the mobile strip is a real `<nav>` with an accessible name.
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { SURFACES, SURFACE_BY_ID, SURFACE_GROUPS, type SurfaceId, type SurfaceGroupId } from "../lib/surfaces";
import { useAuth } from "../contexts/AuthContext";
import { usePublishedChrome } from "../lib/surfaceChrome";
import { SURFACE_ICONS, IconMenu, IconClose, IconShield } from "./Icons";

const NAV_SURFACES = SURFACES.filter((s) => s.nav !== false);

/** The primary destinations, in product order. The surface table is the source
 *  of truth for *what exists*; this is only the reading order of the sidebar,
 *  and any surface not named here still renders after the named ones. */
const NAV_ORDER: SurfaceId[] = [
  "workspace",
  "home",
  "arkana",
  "projects",
  "engineering-lab",
  "weaver",
  "solariun",
  "knowledge",
  "novanet",
  "solspire",
  "settings",
  "operator",
  "about",
];

const ORDERED_NAV = [...NAV_SURFACES].sort((a, b) => {
  const ai = NAV_ORDER.indexOf(a.id);
  const bi = NAV_ORDER.indexOf(b.id);
  return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
});

/**
 * The navigation, grouped for reading.
 *
 * Still derived from the one surface table: `NAV_SURFACES` is the item list and
 * `SurfaceDef.group` is the only grouping input. A surface that declares no
 * group is collected into a trailing group rather than dropped, so adding a
 * surface to `surfaces.ts` can never make it unreachable from the shell.
 *
 * Groups with no members are omitted, so the sidebar never renders an empty
 * heading. The order of the groups is `SURFACE_GROUPS`'s order, and the order
 * within a group is `NAV_ORDER`'s — one declaration each, no third list.
 */
const UNGROUPED: SurfaceGroupId = "system";

const NAV_GROUPS: Array<{ id: SurfaceGroupId; label: string; items: typeof NAV_SURFACES }> =
  SURFACE_GROUPS.map((group) => ({
    id: group.id,
    label: group.label,
    items: ORDERED_NAV.filter((s) => (s.group ?? UNGROUPED) === group.id),
  })).filter((group) => group.items.length > 0);

function NavLink({
  active,
  label,
  id,
  onClick,
}: {
  active: boolean;
  label: string;
  id: SurfaceId;
  onClick: () => void;
}) {
  const Icon = SURFACE_ICONS[id];
  return (
    <button
      onClick={onClick}
      type="button"
      aria-current={active ? "page" : undefined}
      data-testid={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
      className="cg-nav-item"
    >
      <span className="cg-nav-icon">
        <Icon />
      </span>
      <span className="truncate">{label}</span>
    </button>
  );
}

/** The identity block: who is signed in, and the one control that changes it. */
function IdentityBlock({ onNavigate }: { onNavigate: (id: SurfaceId) => void }) {
  const { profile, isAuthenticated, identityState, signOutNow } = useAuth();
  const initials = (profile?.display_name ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <div className="mt-auto px-1 pt-5">
      <div className="cg-rule mb-4" />
      {isAuthenticated && profile ? (
        <div className="flex items-center gap-3 px-2">
          <span
            className="grid h-9 w-9 flex-none place-items-center rounded-full border border-gold/30 bg-gold/10 font-mono text-[11px] tracking-wider text-champagne"
            aria-hidden="true"
          >
            {initials || "·"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] text-white/85">{profile.display_name}</p>
            <p className="truncate font-mono text-[10px] uppercase tracking-widest text-white/35">
              {profile.role}
            </p>
          </div>
        </div>
      ) : (
        <div className="px-2">
          <p className="text-[13px] text-white/60">Not signed in</p>
          <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-white/30">
            public surfaces only
          </p>
        </div>
      )}

      <div className="mt-3 flex items-center gap-2 px-2">
        {isAuthenticated ? (
          <button
            onClick={() => void signOutNow()}
            data-testid="nav-sign-out"
            className="font-mono text-[10px] uppercase tracking-widest text-white/40 transition hover:text-white/80"
          >
            Sign out
          </button>
        ) : (
          <button
            onClick={() => onNavigate("login")}
            data-testid="nav-sign-in"
            className="font-mono text-[10px] uppercase tracking-widest text-champagne/80 transition hover:text-champagne"
          >
            Sign in
          </button>
        )}
        <span className="ml-auto flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-widest text-white/25">
          <span
            className={`cg-dot ${
              identityState === "ready" ? "cg-dot-live" : identityState === "loading" ? "cg-dot-warn" : "cg-dot-off"
            }`}
          />
          {identityState}
        </span>
      </div>

      <p className="mt-4 flex items-start gap-2 px-2 text-[10px] leading-relaxed text-white/45">
        <span className="mt-0.5 flex-none text-gold/50">
          <IconShield />
        </span>
        Human authority remains the decision boundary.
      </p>
    </div>
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
  const mainRef = useRef<HTMLElement>(null);
  const mobileNavRef = useRef<HTMLElement>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const surface = SURFACE_BY_ID[current];
  // The one shell renders the chrome a surface publishes. A surface never
  // renders its own rail or header — it contributes them here, so there is
  // exactly one navigation column and one header in the product.
  const chrome = usePublishedChrome();

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

  // A route change also closes the mobile drawer: leaving it open over the new
  // surface would hide the thing the user just asked for.
  useEffect(() => {
    setDrawerOpen(false);
  }, [current]);

  // Escape closes the drawer, and the body does not scroll behind it.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  // The document title is how a screen reader announces a navigation (WCAG
  // 2.4.2). One static <title> for every route leaves that announcement
  // unchanged, so the shell — the single owner of "which surface is current" —
  // derives the title from the surface table rather than a second list.
  useEffect(() => {
    document.title = `${SURFACE_BY_ID[current].name} · ARKADIA`;
  }, [current]);

  return (
    <div className="relative flex min-h-screen bg-ink text-white">
      <div className="aurora-bg" />

      <a
        href="#main-content"
        data-testid="skip-to-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:border focus:border-gold/40 focus:bg-panel focus:px-3 focus:py-2 focus:font-mono focus:text-[11px] focus:uppercase focus:tracking-widest focus:text-gold"
      >
        Skip to content
      </a>

      {/* ── Desktop sidebar ─────────────────────────────────────────────── */}
      <aside
        className="relative z-20 hidden w-[264px] shrink-0 flex-col border-r border-white/[0.07] p-4 md:flex"
        style={{
          background:
            "linear-gradient(180deg, rgba(10,12,22,0.92) 0%, rgba(5,6,11,0.96) 100%)",
          backdropFilter: "blur(20px)",
        }}
      >
        <button
          type="button"
          onClick={() => onNavigate("home")}
          data-testid="brand-home"
          className="mb-7 flex items-center gap-3 px-2 text-left"
        >
          <span className="cg-orb h-9 w-9 flex-none" aria-hidden="true" />
          <span className="min-w-0">
            <span className="cg-title block text-[15px] leading-none">ARKADIA</span>
            <span className="mt-1 block font-mono text-[9px] uppercase tracking-[0.22em] text-white/30">
              One
            </span>
          </span>
        </button>

        <nav aria-label="Primary navigation" className="flex flex-col gap-0.5">
          {NAV_GROUPS.map((group) => (
            <div key={group.id} className="cg-nav-group" data-testid={`nav-group-${group.id}`}>
              <p className="cg-nav-group-label">{group.label}</p>
              {group.items.map((s) => (
                <NavLink
                  key={s.id}
                  id={s.id}
                  active={current === s.id}
                  label={s.name}
                  onClick={() => onNavigate(s.id)}
                />
              ))}
            </div>
          ))}
        </nav>

        <IdentityBlock onNavigate={onNavigate} />
      </aside>

      {/* ── Main column ─────────────────────────────────────────────────── */}
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        {/* Header: the current surface, its boundary, and the mobile menu. */}
        <header
          className="sticky top-0 z-30 flex min-h-[60px] items-center gap-3 border-b border-white/[0.07] px-4 md:px-8"
          style={{
            background: "rgba(8,10,17,0.72)",
            backdropFilter: "blur(20px) saturate(1.2)",
            WebkitBackdropFilter: "blur(20px) saturate(1.2)",
          }}
        >
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
            aria-expanded={drawerOpen}
            data-testid="mobile-menu-open"
            className="grid h-9 w-9 place-items-center rounded-lg border border-white/10 text-white/70 md:hidden"
          >
            <IconMenu />
          </button>

          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-[9px] uppercase tracking-[0.22em] text-white/30">
              {surface.boundary}
            </p>
            <h2 className="truncate text-[15px] font-medium tracking-tight text-white/90">
              {surface.name}
            </h2>
          </div>

          {/* The surface's live status, published to the one header. A surface
              that publishes none renders nothing here — no placeholder. */}
          {chrome.status ? (
            <span
              data-testid="shell-surface-status"
              className="hidden max-w-[40%] truncate font-mono text-[9px] uppercase tracking-[0.18em] text-emerald/70 sm:block"
            >
              {chrome.status}
            </span>
          ) : null}

          <span className="hidden items-center gap-2 rounded-full border border-white/10 px-3 py-1 font-mono text-[9px] uppercase tracking-[0.18em] text-white/40 sm:flex">
            <span className="cg-dot cg-dot-live" />
            canonical
          </span>
        </header>

        {/* Mobile navigation: the same surfaces, no second global nav bar. */}
        <nav
          ref={mobileNavRef}
          aria-label="Primary navigation (mobile)"
          className="flex gap-1 overflow-x-auto border-b border-white/[0.07] bg-panel/40 p-2 md:hidden"
        >
          {ORDERED_NAV.map((s) => (
            <NavLink
              key={s.id}
              id={s.id}
              active={current === s.id}
              label={s.name}
              onClick={() => onNavigate(s.id)}
            />
          ))}
        </nav>

        <main
          id="main-content"
          ref={mainRef}
          tabIndex={-1}
          aria-label={`${SURFACE_BY_ID[current].name} content`}
          className="min-w-0 flex-1 focus:outline-none"
        >
          {/*
            The surface's context rail, rendered by the one shell.

            This is the region that used to be a second `<aside>` inside
            `WorkspaceShell` and `ArkanaShell`. It is now a single region owned
            by the shell and *filled* by whichever surface is current, so the
            product has one navigation column and one context column — never
            two of either. A surface that publishes no rail renders no region.
          */}
          {chrome.rail ? (
            <div className="cg-surface-rail" data-testid="shell-surface-rail">
              <aside aria-label={chrome.railLabel} className="cg-surface-rail-inner">
                {chrome.rail}
              </aside>
              <div className="cg-surface-rail-content">{children}</div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>

      {/* ── Mobile drawer ───────────────────────────────────────────────── */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <aside
            className="absolute inset-y-0 left-0 flex w-[280px] max-w-[86vw] flex-col border-r border-white/10 p-4"
            style={{
              background: "linear-gradient(180deg, rgba(10,12,22,0.98) 0%, rgba(5,6,11,0.99) 100%)",
            }}
          >
            <div className="mb-6 flex items-center justify-between px-2">
              <div className="flex items-center gap-3">
                <span className="cg-orb h-8 w-8 flex-none" aria-hidden="true" />
                <span className="cg-title text-[14px]">ARKADIA</span>
              </div>
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close navigation"
                className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 text-white/60"
              >
                <IconClose />
              </button>
            </div>
            <nav aria-label="Primary navigation (drawer)" className="flex flex-col gap-0.5 overflow-y-auto">
              {NAV_GROUPS.map((group) => (
                <div key={group.id} className="cg-nav-group">
                  <p className="cg-nav-group-label">{group.label}</p>
                  {group.items.map((s) => (
                    <NavLink
                      key={s.id}
                      id={s.id}
                      active={current === s.id}
                      label={s.name}
                      onClick={() => onNavigate(s.id)}
                    />
                  ))}
                </div>
              ))}
            </nav>
            <IdentityBlock onNavigate={onNavigate} />
          </aside>
        </div>
      )}
    </div>
  );
}
