/**
 * Shared UI primitives. Every surface uses these so loading, empty, error, and
 * "not yet wired" states look and behave the same everywhere.
 *
 * Crystal Glass (AO-001 beta): the primitives are the design system's public
 * surface. A page composes `Page` + `Panel` + `Facts` and gets the glass
 * language for free; it never re-declares a colour, a radius or a shadow.
 *
 * Contract invariants (pinned by tests/test_console_authorization_state_contract.py
 * and tests/test_console_facts_value_overflow_contract.py):
 *   - `ContractState` carries a distinct `forbidden` copy entry whose text does
 *     not tell a signed-in viewer to sign in;
 *   - `Facts`' value column keeps `min-w-0` + `break-words` and never sets
 *     `whitespace-nowrap`/`pre`.
 */
import type { ReactNode } from "react";
import type { HydrationState } from "../lib/useHydration";
import { IconArrow, IconShield } from "./Icons";

/**
 * The page frame: the shared aurora field, a generous content column, and the
 * surface header. `title` is the surface name; `eyebrow` is the product
 * boundary it belongs to.
 */
export function Page({
  title,
  subtitle,
  eyebrow,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="relative min-h-full w-full">
      <div className="page-column relative z-10 pb-24 pt-8 md:pt-10">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            {eyebrow && <p className="cg-eyebrow mb-2">{eyebrow}</p>}
            <h1 className="cg-title text-[26px] leading-tight md:text-[32px]">{title}</h1>
            {subtitle && (
              <p className="mt-2.5 max-w-2xl text-[13.5px] leading-relaxed text-white/55">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
        {children}
      </div>
    </div>
  );
}

/**
 * The canonical glass panel. `tone` selects the illumination: neutral crystal,
 * gold (attention / governance), or teal (live / primary).
 */
export function Panel({
  children,
  className = "",
  tone = "neutral",
  interactive = false,
  "data-testid": testid,
}: {
  children: ReactNode;
  className?: string;
  tone?: "neutral" | "gold" | "teal";
  interactive?: boolean;
  "data-testid"?: string;
}) {
  const toneClass = tone === "gold" ? "cg-panel-lit" : tone === "teal" ? "cg-panel-teal" : "";
  return (
    <section
      data-testid={testid}
      className={`cg-panel ${toneClass} ${interactive ? "cg-interactive" : ""} p-5 ${className}`}
    >
      {children}
    </section>
  );
}

/** A panel section heading: eyebrow + optional trailing control. */
export function PanelHead({
  label,
  hint,
  action,
}: {
  label: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-baseline justify-between gap-3">
      <div className="min-w-0">
        <p className="cg-eyebrow">{label}</p>
        {hint && <p className="mt-1 text-[11.5px] text-white/35">{hint}</p>}
      </div>
      {action}
    </div>
  );
}

/** A labelled set of key/value facts — used for real contract readings. */
export function Facts({ rows }: { rows: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="grid grid-cols-[minmax(0,10rem)_1fr] gap-x-4 gap-y-2.5 text-sm">
      {rows.map((row) => (
        <div key={row.label} className="contents">
          <dt className="font-mono text-[10px] uppercase tracking-[0.14em] text-white/35">{row.label}</dt>
          {/*
           * `min-w-0 break-words`: this column holds arbitrary contract readings,
           * including long unbroken tokens — a 40-char revision SHA, an `EVD-…`
           * evidence id, a session id, or the raw `JSON.stringify` output that
           * `scalarOverview` emits for an object-valued overview key. Measured in
           * Chromium 390x844 against the canonical deployment: substituting a
           * 164-char unbroken value into this element took the document from 0 to
           * 405px of horizontal overflow. `min-w-0` lets the grid track shrink
           * below the token's intrinsic width and `break-words` wraps it; neither
           * affects a value that already fits.
           */}
          <dd className="min-w-0 break-words text-white/85">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** A single headline metric — the overview's unit of reading. */
export function Stat({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "neutral" | "gold" | "teal";
}) {
  const valueTone =
    tone === "gold" ? "text-champagne" : tone === "teal" ? "text-teal" : "text-white/90";
  return (
    <div className="min-w-0">
      <p className="cg-eyebrow">{label}</p>
      <p className={`mt-1.5 truncate font-display text-[22px] leading-none ${valueTone}`}>{value}</p>
      {hint && <p className="mt-1.5 truncate text-[11px] text-white/35">{hint}</p>}
    </div>
  );
}

/** A status pill: a dot plus a word. Never a colour alone. */
export function StatusPill({
  state,
  label,
}: {
  state: "live" | "warn" | "off";
  label: string;
}) {
  const dot = state === "live" ? "cg-dot-live" : state === "warn" ? "cg-dot-warn" : "cg-dot-off";
  const text =
    state === "live" ? "text-teal/90" : state === "warn" ? "text-champagne/90" : "text-white/40";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-1 font-mono text-[9.5px] uppercase tracking-[0.16em] ${text}`}
    >
      <span className={`cg-dot ${dot}`} />
      {label}
    </span>
  );
}

export function Loading({ label = "Reading canonical contract…" }: { label?: string }) {
  return (
    <Panel>
      <div className="flex items-center gap-3">
        <span className="cg-orb cg-sheen h-6 w-6 flex-none" aria-hidden="true" />
        <p className="animate-pulse font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
          {label}
        </p>
      </div>
    </Panel>
  );
}

/** States for a protected read that could not be satisfied. */
export function ContractState({
  state,
  error,
  onRetry,
}: {
  state: HydrationState;
  error?: string | null;
  onRetry?: () => void;
}) {
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
    <Panel tone="gold">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex-none text-gold/70">
          <IconShield />
        </span>
        <div className="min-w-0">
          <p className="font-display text-[15px] text-champagne">{c.title}</p>
          <p className="mt-1 text-[13px] leading-relaxed text-white/55">{c.body}</p>
          {error && <p className="mt-3 break-words font-mono text-[11px] text-white/35">{error}</p>}
          {onRetry && (
            <button onClick={onRetry} className="cg-btn mt-4">
              Retry
            </button>
          )}
        </div>
      </div>
    </Panel>
  );
}

/**
 * An honest placeholder for a surface whose backend contract is not yet wired.
 * It states exactly what is missing rather than rendering mock data.
 */
export function NotYetWired({ contract, note }: { contract: string; note?: string }) {
  return (
    <Panel className="border-dashed">
      <p className="cg-eyebrow">Surface scaffolded · contract not yet wired</p>
      <p className="mt-2 text-[13px] leading-relaxed text-white/55">
        This surface is part of the product architecture but its interface is not built yet.
      </p>
      <p className="mt-3 break-words font-mono text-[11px] text-white/45">
        Expected contract: <span className="text-azure">{contract}</span>
      </p>
      {note && <p className="mt-2 text-[11.5px] leading-relaxed text-white/35">{note}</p>}
    </Panel>
  );
}

/** An empty state: a real answer, not a failure. */
export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-start gap-3 py-6">
      <span className="cg-orb h-10 w-10" aria-hidden="true" />
      <div>
        <p className="text-[14px] text-white/80">{title}</p>
        <p className="mt-1 max-w-md text-[12.5px] leading-relaxed text-white/45">{body}</p>
      </div>
      {action && (
        <button type="button" onClick={action.onClick} className="cg-btn cg-btn-primary">
          {action.label}
          <IconArrow />
        </button>
      )}
    </div>
  );
}
