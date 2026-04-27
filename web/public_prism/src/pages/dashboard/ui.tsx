/**
 * Shared UI atoms for the dashboard. Tiny, self-contained, no external
 * shadcn install — just Tailwind + the existing Arkadia palette.
 */
import React, { useState } from "react"

const PALETTE = {
  bg: "#0A0A0F",
  panel: "rgba(13,13,26,0.7)",
  panelBorder: "rgba(0,212,170,0.10)",
  gold: "#C9A84C",
  teal: "#00D4AA",
  text: "rgba(232,232,232,0.85)",
  muted: "rgba(232,232,232,0.5)",
  dim: "rgba(232,232,232,0.3)",
}

export const COLORS = PALETTE

export function Card({
  title,
  subtitle,
  children,
  right,
  className = "",
}: {
  title?: string
  subtitle?: string
  children: React.ReactNode
  right?: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={className}
      data-testid="dashboard-card"
      style={{
        background: PALETTE.panel,
        border: `1px solid ${PALETTE.panelBorder}`,
        borderRadius: 14,
        padding: "18px 20px",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
    >
      {(title || right) && (
        <div className="flex items-center justify-between mb-3">
          <div>
            {title && (
              <h3
                style={{
                  fontFamily: "serif",
                  fontSize: 13,
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                  color: PALETTE.gold,
                  margin: 0,
                }}
              >
                {title}
              </h3>
            )}
            {subtitle && (
              <p
                style={{
                  fontFamily: "sans-serif",
                  fontSize: 11,
                  color: PALETTE.muted,
                  margin: "4px 0 0",
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  )
}

export function Stat({
  label,
  value,
  hint,
  tone = "default",
  testId,
}: {
  label: string
  value: React.ReactNode
  hint?: string
  tone?: "default" | "success" | "warn" | "fail"
  testId?: string
}) {
  const toneColor =
    tone === "success" ? PALETTE.teal :
    tone === "warn"    ? PALETTE.gold :
    tone === "fail"    ? "#EF6C6C" :
    PALETTE.text
  return (
    <Card>
      <div data-testid={testId}>
        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 9,
            letterSpacing: "0.3em",
            textTransform: "uppercase",
            color: PALETTE.dim,
            margin: 0,
          }}
        >
          {label}
        </p>
        <p
          style={{
            fontFamily: "serif",
            fontSize: 32,
            color: toneColor,
            margin: "8px 0 0",
            lineHeight: 1,
          }}
        >
          {value}
        </p>
        {hint && (
          <p
            style={{
              fontFamily: "sans-serif",
              fontSize: 11,
              color: PALETTE.muted,
              margin: "8px 0 0",
            }}
          >
            {hint}
          </p>
        )}
      </div>
    </Card>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() ?? ""
  const map: Record<string, { bg: string; fg: string; border: string }> = {
    completed: { bg: "rgba(0,212,170,0.10)",  fg: "#00D4AA", border: "rgba(0,212,170,0.4)" },
    success:   { bg: "rgba(0,212,170,0.10)",  fg: "#00D4AA", border: "rgba(0,212,170,0.4)" },
    active:    { bg: "rgba(0,212,170,0.10)",  fg: "#00D4AA", border: "rgba(0,212,170,0.4)" },
    running:   { bg: "rgba(201,168,76,0.10)", fg: "#C9A84C", border: "rgba(201,168,76,0.4)" },
    pending:   { bg: "rgba(201,168,76,0.10)", fg: "#C9A84C", border: "rgba(201,168,76,0.4)" },
    paused:    { bg: "rgba(232,232,232,0.06)", fg: "rgba(232,232,232,0.6)", border: "rgba(232,232,232,0.2)" },
    failed:    { bg: "rgba(239,108,108,0.10)", fg: "#EF6C6C", border: "rgba(239,108,108,0.4)" },
  }
  const c = map[s] ?? map["paused"]
  return (
    <span
      data-testid={`status-${s}`}
      style={{
        display: "inline-block",
        padding: "3px 10px",
        background: c.bg,
        color: c.fg,
        border: `1px solid ${c.border}`,
        borderRadius: 999,
        fontFamily: "sans-serif",
        fontSize: 10,
        letterSpacing: "0.18em",
        textTransform: "uppercase",
      }}
    >
      {s || "—"}
    </span>
  )
}

export function Button({
  children, onClick, variant = "default", disabled, testId, type = "button",
}: {
  children: React.ReactNode
  onClick?: () => void
  variant?: "default" | "primary" | "ghost" | "danger"
  disabled?: boolean
  testId?: string
  type?: "button" | "submit"
}) {
  const styles: Record<string, React.CSSProperties> = {
    default: {
      background: "rgba(201,168,76,0.08)", color: PALETTE.gold,
      border: "1px solid rgba(201,168,76,0.35)",
    },
    primary: {
      background: "rgba(0,212,170,0.10)", color: PALETTE.teal,
      border: "1px solid rgba(0,212,170,0.4)",
    },
    ghost: {
      background: "transparent", color: PALETTE.muted,
      border: "1px solid rgba(232,232,232,0.15)",
    },
    danger: {
      background: "rgba(239,108,108,0.08)", color: "#EF6C6C",
      border: "1px solid rgba(239,108,108,0.35)",
    },
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      data-testid={testId}
      style={{
        ...styles[variant],
        padding: "8px 14px",
        borderRadius: 8,
        fontFamily: "sans-serif",
        fontSize: 10,
        letterSpacing: "0.2em",
        textTransform: "uppercase",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "opacity .2s",
      }}
    >
      {children}
    </button>
  )
}

export function Input({
  value, onChange, placeholder, type = "text", testId,
}: {
  value: string | number
  onChange: (v: string) => void
  placeholder?: string
  type?: string
  testId?: string
}) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testId}
      style={{
        background: "rgba(0,0,0,0.3)",
        border: "1px solid rgba(201,168,76,0.2)",
        color: PALETTE.text,
        borderRadius: 8,
        padding: "10px 12px",
        fontFamily: "sans-serif",
        fontSize: 13,
        width: "100%",
        outline: "none",
      }}
    />
  )
}

export function CollapsibleJSON({
  data,
  defaultOpen = false,
  label = "JSON",
  testId,
}: {
  data: unknown
  defaultOpen?: boolean
  label?: string
  testId?: string
}) {
  const [open, setOpen] = useState(defaultOpen)
  const json = JSON.stringify(data ?? null, null, 2)
  return (
    <div data-testid={testId}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          background: "none", border: "none", cursor: "pointer",
          color: PALETTE.muted, fontFamily: "sans-serif",
          fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase",
          padding: "4px 0", display: "flex", alignItems: "center", gap: 8,
        }}
      >
        <span style={{ color: PALETTE.gold }}>{open ? "▾" : "▸"}</span>
        {label} {open ? "" : `(${json.length} chars)`}
      </button>
      {open && (
        <pre
          style={{
            background: "rgba(0,0,0,0.4)",
            border: "1px solid rgba(0,212,170,0.08)",
            borderRadius: 8,
            padding: "12px 14px",
            fontFamily: "ui-monospace, SFMono-Regular, monospace",
            fontSize: 11.5,
            color: PALETTE.text,
            overflow: "auto",
            maxHeight: 360,
            margin: "6px 0 0",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {json}
        </pre>
      )}
    </div>
  )
}

export function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        padding: "32px 16px",
        textAlign: "center",
        color: PALETTE.muted,
        fontFamily: "sans-serif",
        fontSize: 12,
      }}
    >
      {children}
    </div>
  )
}

export function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-testid="text-error"
      style={{
        padding: "12px 14px",
        border: "1px solid rgba(239,108,108,0.35)",
        background: "rgba(239,108,108,0.06)",
        borderRadius: 8,
        color: "#EF6C6C",
        fontFamily: "sans-serif",
        fontSize: 12,
      }}
    >
      {children}
    </div>
  )
}

export function fmtTime(ts?: number | null): string {
  if (!ts) return "—"
  const d = new Date(ts * 1000)
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  })
}

export function fmtDuration(start?: number | null, end?: number | null): string {
  if (!start) return "—"
  const e = end ?? Date.now() / 1000
  const sec = e - start
  if (sec < 1) return `${Math.round(sec * 1000)}ms`
  if (sec < 60) return `${sec.toFixed(2)}s`
  const m = Math.floor(sec / 60); const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

export function fmtMs(ms?: number | null): string {
  if (ms == null) return "—"
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

export function fmtAgo(ts?: number | null): string {
  if (!ts) return "never"
  const sec = Date.now() / 1000 - ts
  if (sec < 60)  return `${Math.round(sec)}s ago`
  if (sec < 3600) return `${Math.round(sec / 60)}m ago`
  if (sec < 86400) return `${Math.round(sec / 3600)}h ago`
  return `${Math.round(sec / 86400)}d ago`
}
