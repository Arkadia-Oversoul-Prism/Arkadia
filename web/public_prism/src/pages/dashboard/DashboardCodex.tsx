/**
 * Spiral Codex — live corpus browser, dashboard-embedded version.
 * Renders within the dashboard shell (no full-page wrapper, no back button).
 */
import React, { useState, useEffect, useMemo, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { RefreshCw, Upload, Search, X } from "lucide-react"
import { api, CodexResponse } from "../../lib/dashboardApi"
import { COLORS, Card, Empty, ErrorBox } from "./ui"

const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  NEURAL_SPINE: { label: "Neural Spine",  color: "#00D4AA", icon: "🧬" },
  CREATIVE_OS:  { label: "Creative OS",   color: "#C9A84C", icon: "🎨" },
  COLLECTIVE:   { label: "Collective",    color: "#B08DE8", icon: "📚" },
  GOVERNANCE:   { label: "Governance",    color: "#6A9FD8", icon: "⚖️" },
  ARCHIVE:      { label: "Archive",       color: "#8B7355", icon: "📦" },
  CODEX:        { label: "Codex",         color: "#D4AF37", icon: "📜" },
}

function getCatMeta(cat: string) {
  return CATEGORY_META[cat] ?? {
    label: cat.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
    color: "#888",
    icon: "📄",
  }
}

function fmtChars(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1000)      return `${(n / 1000).toFixed(1)}k`
  return `${n}`
}

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")

export default function DashboardCodex() {
  const qc = useQueryClient()
  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ["codex-full"],
    queryFn: api.codex,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  })

  const [activeCategory, setActiveCategory] = useState("ALL")
  const [search, setSearch] = useState("")
  const [expanded, setExpanded] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const scrolls = useMemo(() => {
    if (!data?.scrolls) return []
    return Object.entries(data.scrolls).map(([key, s]) => ({ key, ...s }))
  }, [data])

  const categories = useMemo(() => {
    const seen = new Map<string, number>()
    for (const s of scrolls) seen.set(s.category, (seen.get(s.category) ?? 0) + 1)
    return Array.from(seen.entries()).map(([key, count]) => ({ key, count }))
  }, [scrolls])

  const filtered = useMemo(() => {
    let list = scrolls
    if (activeCategory !== "ALL") list = list.filter(s => s.category === activeCategory)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(s =>
        s.label?.toLowerCase().includes(q) ||
        s.description?.toLowerCase().includes(q) ||
        s.preview?.toLowerCase().includes(q)
      )
    }
    return list
  }, [scrolls, activeCategory, search])

  const handleUpload = async (file: File) => {
    setUploading(true); setUploadMsg(null)
    const fd = new FormData()
    fd.append("file", file)
    fd.append("category", "COLLECTIVE")
    fd.append("description", `Uploaded via Spiral Codex: ${file.name}`)
    try {
      const res = await fetch(`${BASE}/api/codex/upload`, { method: "POST", body: fd })
      const d = await res.json()
      if (!res.ok) throw new Error(d.detail || `${res.status}`)
      setUploadMsg({ ok: true, text: d.message || `'${file.name}' ingested` })
      refetch()
    } catch (e: any) {
      setUploadMsg({ ok: false, text: e.message })
    } finally { setUploading(false) }
  }

  if (isLoading && !data) return <Empty>Loading Spiral Codex…</Empty>
  if (error) return <ErrorBox>Corpus sync failed: {(error as Error).message}</ErrorBox>

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Header strip */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
        <div>
          <p style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.dim, letterSpacing: "0.2em", textTransform: "uppercase", margin: 0 }}>
            Encyclopedia Galactica · Document Corpus Feed
          </p>
          <p style={{ fontFamily: "sans-serif", fontSize: 12, color: COLORS.muted, margin: "4px 0 0" }}>
            {data?.live_docs ?? 0} scrolls live · {fmtChars(data?.total_chars ?? 0)} chars
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => { setShowUpload(!showUpload); setUploadMsg(null) }}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, border: `1px solid ${showUpload ? "rgba(201,168,76,0.5)" : "rgba(232,232,232,0.1)"}`, background: showUpload ? "rgba(201,168,76,0.08)" : "transparent", color: showUpload ? COLORS.gold : COLORS.muted, fontSize: 10, letterSpacing: "0.15em", textTransform: "uppercase", cursor: "pointer", fontFamily: "sans-serif" }}
          >
            <Upload size={11} /> Upload
          </button>
          <button
            onClick={() => refetch()} disabled={isFetching}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, border: "1px solid rgba(0,212,170,0.25)", background: "rgba(0,212,170,0.06)", color: COLORS.teal, fontSize: 10, letterSpacing: "0.15em", textTransform: "uppercase", cursor: isFetching ? "wait" : "pointer", fontFamily: "sans-serif" }}
          >
            <RefreshCw size={11} style={{ animation: isFetching ? "spin 1s linear infinite" : "none" }} />
            Sync
          </button>
        </div>
      </div>

      {/* Upload area */}
      <AnimatePresence>
        {showUpload && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
            <div
              onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) handleUpload(f) }}
              onDragOver={e => e.preventDefault()}
              onClick={() => fileRef.current?.click()}
              style={{ border: "2px dashed rgba(201,168,76,0.25)", borderRadius: 12, padding: "20px", textAlign: "center", cursor: "pointer" }}
            >
              <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md,.json" className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }} />
              {uploading
                ? <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.gold, margin: 0 }}>Ingesting into the Codex…</p>
                : <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: 0 }}>Drop file or click · PDF · DOCX · TXT · MD</p>}
            </div>
            {uploadMsg && (
              <p style={{ fontFamily: "sans-serif", fontSize: 11, color: uploadMsg.ok ? "#00D4AA" : "#ef6c6c", margin: "8px 0 0", textAlign: "center" }}>
                {uploadMsg.text}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search */}
      <div style={{ position: "relative" }}>
        <Search size={13} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: COLORS.dim }} />
        <input
          value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search scrolls, labels, descriptions…"
          style={{ width: "100%", paddingLeft: 34, paddingRight: search ? 34 : 14, paddingTop: 9, paddingBottom: 9, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.09)", borderRadius: 10, color: COLORS.text, fontFamily: "sans-serif", fontSize: 12, outline: "none", boxSizing: "border-box" }}
        />
        {search && (
          <button onClick={() => setSearch("")} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: COLORS.dim, cursor: "pointer" }}>
            <X size={12} />
          </button>
        )}
      </div>

      {/* Category tabs */}
      <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 2 }}>
        {[{ key: "ALL", count: scrolls.length }, ...categories].map(({ key, count }) => {
          const meta = key === "ALL"
            ? { label: "All", color: COLORS.gold, icon: "✦" }
            : getCatMeta(key)
          const active = activeCategory === key
          return (
            <button key={key} onClick={() => setActiveCategory(key)}
              style={{ flexShrink: 0, display: "flex", alignItems: "center", gap: 5, padding: "5px 12px", borderRadius: 999, border: `1px solid ${active ? meta.color + "60" : "rgba(232,232,232,0.09)"}`, background: active ? `${meta.color}14` : "transparent", color: active ? meta.color : COLORS.muted, fontFamily: "sans-serif", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", cursor: "pointer", whiteSpace: "nowrap" }}>
              <span>{meta.icon}</span>
              <span>{meta.label}</span>
              <span style={{ opacity: 0.5 }}>({count})</span>
            </button>
          )
        })}
      </div>

      {/* Scroll cards */}
      {filtered.length === 0 && <Empty>No scrolls matching this filter.</Empty>}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {filtered.map((scroll, i) => {
          const meta = getCatMeta(scroll.category)
          const isExpanded = expanded === scroll.id
          const isLive = !scroll.error && scroll.chars > 0

          return (
            <motion.div key={scroll.id}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.03, 0.4) }}
              onClick={() => setExpanded(isExpanded ? null : scroll.id)}
              style={{ border: `1px solid ${meta.color}38`, background: `${meta.color}05`, borderRadius: 12, overflow: "hidden", cursor: "pointer" }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "12px 14px" }}>
                <span style={{ fontSize: 18, flexShrink: 0, marginTop: 2 }}>{meta.icon}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" }}>
                    <span style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.2em", textTransform: "uppercase", color: meta.color }}>
                      {meta.label}
                    </span>
                    <span style={{ color: COLORS.dim, fontSize: 9 }}>·</span>
                    <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 9, color: COLORS.dim }}>
                      {fmtChars(scroll.chars)} chars
                    </span>
                    {scroll.source && (
                      <>
                        <span style={{ color: COLORS.dim, fontSize: 9 }}>·</span>
                        <span style={{ fontFamily: "sans-serif", fontSize: 9, color: COLORS.dim, letterSpacing: "0.1em" }}>
                          {scroll.source}
                        </span>
                      </>
                    )}
                  </div>
                  <p style={{ fontFamily: "sans-serif", fontSize: 13, color: COLORS.text, margin: "0 0 4px", lineHeight: 1.4, fontWeight: 500 }}>
                    {scroll.label}
                  </p>
                  {scroll.preview && (
                    <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: 0, lineHeight: 1.6, overflow: isExpanded ? "visible" : "hidden", display: isExpanded ? "block" : "-webkit-box", WebkitLineClamp: isExpanded ? undefined : 2, WebkitBoxOrient: isExpanded ? undefined : "vertical" as any }}>
                      {scroll.preview}
                    </p>
                  )}
                  <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 6 }}>
                    <motion.div
                      animate={isLive ? { opacity: [0.4, 1, 0.4] } : {}}
                      transition={{ duration: 2.5, repeat: Infinity }}
                      style={{ width: 5, height: 5, borderRadius: "50%", background: isLive ? meta.color : "#ef6c6c", flexShrink: 0 }}
                    />
                    <span style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", color: isLive ? `${meta.color}90` : "rgba(239,108,108,0.6)" }}>
                      {isLive ? "live" : "error"}
                    </span>
                  </div>
                </div>
                <motion.span animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.25 }}
                  style={{ color: COLORS.dim, fontSize: 11, flexShrink: 0, marginTop: 4 }}>▾</motion.span>
              </div>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}>
                    <div style={{ borderTop: `1px solid ${meta.color}20`, padding: "12px 14px" }}>
                      {scroll.content && (
                        <pre style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: COLORS.muted, whiteSpace: "pre-wrap", maxHeight: 240, overflow: "auto", margin: "0 0 8px", lineHeight: 1.65 }}>
                          {scroll.content.slice(0, 2000)}
                          {scroll.content.length > 2000 ? "\n\n… (truncated)" : ""}
                        </pre>
                      )}
                      {scroll.description && (
                        <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.dim, margin: 0 }}>
                          {scroll.description}
                        </p>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      {filtered.length > 0 && (
        <p style={{ textAlign: "center", fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.4em", textTransform: "uppercase", color: COLORS.dim, margin: "8px 0 0" }}>
          ⟐ End of Transmission · {filtered.length} scrolls ⟐
        </p>
      )}
    </div>
  )
}
