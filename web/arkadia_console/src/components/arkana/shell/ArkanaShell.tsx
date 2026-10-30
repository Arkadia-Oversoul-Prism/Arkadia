/**
 * Arkana conversation shell — A1.
 *
 * Layout only. Does not own intelligence, persistence, or authorization.
 * Desktop: optional left rail for thread history.
 * Mobile: conversation-first with a drawer for the same rail.
 */
import { useEffect, useId, useState, type ReactNode } from "react";
import "../design/arkana.css";

export function ArkanaShell({
  brand = "Arkana",
  statusLabel = "Online",
  sidebar,
  topTrailing,
  children,
  composer,
}: {
  brand?: string;
  statusLabel?: string;
  sidebar?: ReactNode;
  topTrailing?: ReactNode;
  children: ReactNode;
  composer: ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const titleId = useId();

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  return (
    <div className="arkana-shell" data-testid="arkana-shell">
      {sidebar ? (
        <aside className="arkana-sidebar" aria-label="Conversation history">
          <div className="arkana-sidebar-header">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">Conversations</p>
            <p className="mt-1 text-xs text-white/50">Owner-scoped · read from Knowledge OS</p>
          </div>
          <div className="arkana-sidebar-body">{sidebar}</div>
        </aside>
      ) : null}

      <div className="arkana-main">
        <header className="arkana-topbar">
          <div className="flex min-w-0 items-center gap-3">
            {sidebar ? (
              <button
                type="button"
                className="rounded-lg border border-line px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-widest text-white/55 md:hidden"
                aria-expanded={drawerOpen}
                aria-controls="arkana-mobile-drawer"
                data-testid="arkana-open-history"
                onClick={() => setDrawerOpen(true)}
              >
                History
              </button>
            ) : null}
            <div className="min-w-0">
              <p id={titleId} className="font-display text-sm tracking-[0.18em] text-gold sm:text-base">
                {brand}
              </p>
              <p className="font-mono text-[10px] uppercase tracking-widest text-emerald/70">{statusLabel}</p>
            </div>
          </div>
          {topTrailing ? <div className="flex shrink-0 items-center gap-2">{topTrailing}</div> : null}
        </header>

        <div className="arkana-stage">{children}</div>

        <div className="arkana-composer-dock">
          <div className="arkana-composer-inner">{composer}</div>
        </div>
      </div>

      {sidebar && drawerOpen ? (
        <div className="arkana-mobile-drawer" id="arkana-mobile-drawer" role="dialog" aria-modal="true" aria-labelledby={titleId}>
          <button
            type="button"
            className="arkana-mobile-drawer-backdrop"
            aria-label="Close conversation history"
            data-testid="arkana-close-history-backdrop"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="arkana-mobile-drawer-panel">
            <div className="flex items-center justify-between border-b border-line px-4 py-3">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">Conversations</p>
              <button
                type="button"
                className="rounded border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/55"
                data-testid="arkana-close-history"
                onClick={() => setDrawerOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">{sidebar}</div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
