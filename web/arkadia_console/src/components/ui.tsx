/**
 * Shared UI primitives. Every surface uses these so loading, empty, error, and
 * "not yet wired" states look and behave the same everywhere.
 */
import type { ReactNode } from "react";
import type { HydrationState } from "../lib/useHydration";

export function Page({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-24">
        <header className="mb-8">
          <h1 className="font-display text-3xl tracking-[0.16em] text-gold">{title}</h1>
          {subtitle && <p className="mt-2 max-w-2xl text-sm text-white/60">{subtitle}</p>}
        </header>
        {children}
      </div>
    </div>
  );
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-panel/70 p-5 ${className}`}>{children}</section>
  );
}

/** A labelled set of key/value facts — used for real contract readings. */
export function Facts({ rows }: { rows: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="grid grid-cols-[minmax(0,10rem)_1fr] gap-x-4 gap-y-2 text-sm">
      {rows.map((row) => (
        <div key={row.label} className="contents">
          <dt className="font-mono text-[11px] uppercase tracking-wider text-white/40">{row.label}</dt>
          <dd className="text-white/85">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Loading({ label = "Reading canonical contract…" }: { label?: string }) {
  return (
    <Panel>
      <p className="animate-pulse font-mono text-xs uppercase tracking-widest text-white/40">{label}</p>
    </Panel>
  );
}

/** States for a protected read that could not be satisfied. */
export function ContractState({ state, error, onRetry }: { state: HydrationState; error?: string | null; onRetry?: () => void }) {
  if (state === "loading" || state === "idle") return <Loading />;

  const copy: Record<Exclude<HydrationState, "loading" | "idle" | "ready">, { title: string; body: string }> = {
    "auth-required": {
      title: "Authentication required",
      body: "This surface reads a protected contract. Sign in to load it.",
    },
    forbidden: {
      title: "Not authorized for this identity",
      body: "You are signed in, but this identity is not entitled to read this contract. Signing in again will not change the answer — the backend refused the read.",
    },
    unavailable: {
      title: "Backend unavailable",
      body: "Arkadia is not reachable right now. The contract was not read — this is not an empty result.",
    },
    error: {
      title: "Read failed",
      body: "The contract returned an error the client does not recognise.",
    },
  };

  if (state === "ready") return null;
  const c = copy[state];
  return (
    <Panel className="border-gold/30">
      <p className="font-display text-lg text-gold">{c.title}</p>
      <p className="mt-1 text-sm text-white/60">{c.body}</p>
      {error && <p className="mt-3 font-mono text-xs text-white/40">{error}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded border border-emerald/40 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald"
        >
          Retry
        </button>
      )}
    </Panel>
  );
}

/**
 * An honest placeholder for a surface whose backend contract is not yet wired.
 * It states exactly what is missing rather than rendering mock data.
 */
export function NotYetWired({ contract, note }: { contract: string; note?: string }) {
  return (
    <Panel className="border-dashed border-line">
      <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Surface scaffolded · contract not yet wired</p>
      <p className="mt-2 text-sm text-white/60">
        This surface is part of the product architecture but its interface is not built yet.
      </p>
      <p className="mt-3 font-mono text-xs text-white/50">
        Expected contract: <span className="text-azure">{contract}</span>
      </p>
      {note && <p className="mt-2 text-xs text-white/40">{note}</p>}
    </Panel>
  );
}
