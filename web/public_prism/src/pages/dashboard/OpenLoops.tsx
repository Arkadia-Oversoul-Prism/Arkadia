import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { RefreshCw } from "lucide-react"
import { COLORS, Card, Empty, ErrorBox } from "./ui"

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")

interface Loop {
  id: string
  name: string
  status?: string
  next_action?: string
  target?: string
}

interface LoopGroup {
  level: string
  label: string
  color: string
  section_title: string
  loops: Loop[]
}

interface OpenLoopsResponse {
  source: string
  parsed_at: string
  total: number
  groups: LoopGroup[]
  error?: string
}

async function fetchOpenLoops(): Promise<OpenLoopsResponse> {
  const res = await fetch(`${API_BASE}/api/open-loops`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

const LEVEL_META: Record<string, { border: string; bg: string; badge: string }> = {
  critical: { border: "rgba(239,68,68,0.25)",  bg: "rgba(239,68,68,0.04)",  badge: "rgba(239,68,68,0.18)" },
  high:     { border: "rgba(249,115,22,0.25)", bg: "rgba(249,115,22,0.04)", badge: "rgba(249,115,22,0.18)" },
  active:   { border: "rgba(234,179,8,0.22)",  bg: "rgba(234,179,8,0.04)",  badge: "rgba(234,179,8,0.15)"  },
  dormant:  { border: "rgba(59,130,246,0.2)",  bg: "rgba(59,130,246,0.04)", badge: "rgba(59,130,246,0.15)" },
  closed:   { border: "rgba(16,185,129,0.18)", bg: "rgba(16,185,129,0.04)", badge: "rgba(16,185,129,0.15)" },
}

function fmtParsed(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
  } catch {
    return iso
  }
}

export default function OpenLoops() {
  const [expanded, setExpanded] = useState<string | null>(null)
  const { data, isLoading, error, refetch, isFetching } = useQuery<OpenLoopsResponse>({
    queryKey: ["open-loops"],
    queryFn: fetchOpenLoops,
    refetchInterval: 60_000,
  })

  if (isLoading && !data) return <Empty>Parsing DOC2_OPEN_LOOPS.md…</Empty>
  if (error) return <ErrorBox>Failed to load open loops: {(error as Error).message}</ErrorBox>
  if (!data) return null
  if (data.error) return <ErrorBox>{data.error}</ErrorBox>

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Header strip */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <p style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.dim, letterSpacing: "0.18em", textTransform: "uppercase", margin: 0 }}>
            Source — {data.source}
          </p>
          <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: "3px 0 0" }}>
            {data.total} loops · parsed at {fmtParsed(data.parsed_at)}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          data-testid="button-refresh-loops"
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "7px 14px", borderRadius: 8,
            border: "1px solid rgba(0,212,170,0.25)",
            background: "rgba(0,212,170,0.06)",
            color: COLORS.teal, fontSize: 10, letterSpacing: "0.16em",
            textTransform: "uppercase", cursor: isFetching ? "wait" : "pointer",
            fontFamily: "sans-serif", transition: "all .15s",
          }}
        >
          <RefreshCw size={11} style={{ animation: isFetching ? "spin 1s linear infinite" : "none" }} />
          Refresh
        </button>
      </div>

      {/* Loop groups */}
      {data.groups.map((group) => {
        const meta = LEVEL_META[group.level] ?? LEVEL_META.dormant
        return (
          <Card
            key={group.level}
            title={group.section_title}
            subtitle={`${group.loops.length} loop${group.loops.length !== 1 ? "s" : ""}`}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {group.loops.map((loop) => {
                const isOpen = expanded === `${group.level}:${loop.id}`
                return (
                  <div
                    key={loop.id}
                    style={{
                      border: `1px solid ${meta.border}`,
                      background: meta.bg,
                      borderRadius: 10,
                      overflow: "hidden",
                      cursor: "pointer",
                      transition: "all .15s",
                    }}
                    onClick={() => setExpanded(isOpen ? null : `${group.level}:${loop.id}`)}
                    data-testid={`card-loop-${loop.id}`}
                  >
                    {/* Row */}
                    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px" }}>
                      {/* ID badge */}
                      <span style={{
                        fontFamily: "ui-monospace, monospace", fontSize: 10,
                        padding: "2px 7px", borderRadius: 6,
                        background: meta.badge, color: group.color,
                        whiteSpace: "nowrap", flexShrink: 0,
                      }}>
                        #{loop.id}
                      </span>

                      {/* Name */}
                      <span style={{
                        fontFamily: "sans-serif", fontSize: 12, color: COLORS.text,
                        flex: 1, lineHeight: 1.4,
                      }}>
                        {loop.name}
                      </span>

                      {/* Status chip */}
                      {loop.status && (
                        <span style={{
                          fontFamily: "sans-serif", fontSize: 8.5, letterSpacing: "0.14em",
                          textTransform: "uppercase", padding: "2px 8px", borderRadius: 999,
                          border: `1px solid ${meta.border}`, color: group.color,
                          flexShrink: 0, display: "none",
                        }}
                        className="loop-status-chip"
                        >
                          {loop.status.split("—")[0].trim()}
                        </span>
                      )}

                      {/* Expand chevron */}
                      <span style={{ color: COLORS.dim, fontSize: 10, flexShrink: 0 }}>
                        {isOpen ? "▲" : "▼"}
                      </span>
                    </div>

                    {/* Expanded detail */}
                    {isOpen && (loop.status || loop.next_action || loop.target) && (
                      <div style={{
                        borderTop: `1px solid ${meta.border}`,
                        padding: "10px 14px",
                        display: "flex", flexDirection: "column", gap: 6,
                      }}>
                        {loop.status && (
                          <Row label="Status" value={loop.status} color={group.color} />
                        )}
                        {loop.next_action && (
                          <Row label="Next Action" value={loop.next_action} color={COLORS.text} />
                        )}
                        {loop.target && loop.target !== "" && (
                          <Row label="Target" value={loop.target} color={COLORS.muted} />
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
        )
      })}

      {data.groups.length === 0 && (
        <Empty>No loop groups found in DOC2_OPEN_LOOPS.md</Empty>
      )}
    </div>
  )
}

function Row({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
      <span style={{
        fontFamily: "sans-serif", fontSize: 9.5, color: COLORS.dim,
        letterSpacing: "0.14em", textTransform: "uppercase",
        minWidth: 80, flexShrink: 0, paddingTop: 2,
      }}>
        {label}
      </span>
      <span style={{
        fontFamily: "sans-serif", fontSize: 12, color, lineHeight: 1.5,
      }}>
        {value}
      </span>
    </div>
  )
}
