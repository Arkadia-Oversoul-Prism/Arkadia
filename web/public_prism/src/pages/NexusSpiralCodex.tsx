/**
 * NexusSpiralCodex — Spiral Codex Library
 *
 * Canonical Spiral Codex destination: living knowledge archive.
 * Search + category/principle filters, editorial scroll feed, upload.
 *
 * Crystal Matrix navigator → Encyclopedia Galactica only.
 * ReasoMate → standalone destination.
 */
import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, X, ChevronDown, Upload, CheckCircle } from 'lucide-react'
import { api, CodexResponse, CodexScroll } from '../lib/dashboardApi'
import { ingestNote } from '../lib/knowledgeApi'
import MarkdownViewer from '../components/MarkdownViewer'
import { COLORS, Empty, ErrorBox } from './dashboard/ui'

// ─── CATEGORY INFERENCE ───────────────────────────────────────────────────────

function deriveCategory(scroll: CodexScroll): string {
  const id = scroll.id.toLowerCase()
  const desc = (scroll.description || '').toLowerCase()
  if (desc.includes('/creative/') || id.includes('_creative_'))  return 'CREATIVE_OS'
  if (desc.includes('/collective/') || id.includes('_collective_')) return 'COLLECTIVE'
  if (desc.includes('/governance/') || id.includes('_governance_')) return 'GOVERNANCE'
  if (/corpus_api|corpus_deploy/.test(id)) return 'INFRASTRUCTURE'
  if (/doc1_master|master_weight/.test(id))           return 'NEURAL_SPINE'
  if (/doc2_open_loop/.test(id))                      return 'ARCHIVE'
  if (/doc3_principles/.test(id))                     return 'NEURAL_SPINE'
  if (/doc4_node_map/.test(id))                       return 'COLLECTIVE'
  if (/doc5_revenue/.test(id))                        return 'GOVERNANCE'
  if (/final_universal_deploy|arkadia_spec/.test(id)) return 'NEURAL_SPINE'
  if (/uerp_crystal/.test(id))                        return 'NEURAL_SPINE'
  if (/the_frame/.test(id))                           return 'COLLECTIVE'
  if (/arche_native|vhixnova/.test(id))               return 'TRANSMISSION'
  if (/ile_agbomojo|poetic|lyric|flow_matrix|auralis|concept_album|symbolic_grammar/.test(id)) return 'CREATIVE_OS'
  if (/council|onboarding|node_template|collective_weight|readme/.test(id)) return 'COLLECTIVE'
  if (scroll.category && scroll.category !== 'CREATIVE_OS') return scroll.category
  if (desc.startsWith('docs/')) return 'NEURAL_SPINE'
  return 'CODEX'
}

const CATEGORY_META: Record<string, { label: string; color: string; glyph: string }> = {
  NEURAL_SPINE:   { label: 'Neural Spine',    color: '#00D4AA', glyph: '⬡' },
  CREATIVE_OS:    { label: 'Creative OS',     color: '#C9A84C', glyph: '◈' },
  COLLECTIVE:     { label: 'Collective',      color: '#B08DE8', glyph: '⊹' },
  GOVERNANCE:     { label: 'Governance',      color: '#6A9FD8', glyph: '⊞' },
  ARCHIVE:        { label: 'Archive',         color: '#A07848', glyph: '≡' },
  TRANSMISSION:   { label: 'Transmission',    color: '#E86A8C', glyph: '⊛' },
  INFRASTRUCTURE: { label: 'Infrastructure',  color: '#6AE88C', glyph: '⊟' },
  CODEX:          { label: 'Codex',           color: '#D4AF37', glyph: '✦' },
}

// ─── SEVEN PRINCIPLES ─────────────────────────────────────────────────────────

const PRINCIPLES = [
  { id: 'meaning',     label: 'Architecture of Meaning', sigil: '◈', color: '#00D4AA', categories: ['NEURAL_SPINE'] },
  { id: 'soul',        label: 'Physics of the Soul',     sigil: '⊹', color: '#B08DE8', categories: ['COLLECTIVE'] },
  { id: 'language',    label: 'Living Codex',            sigil: '◈', color: '#C9A84C', categories: ['CREATIVE_OS'] },
  { id: 'ethics',      label: 'Ethics of Creation',      sigil: '⊞', color: '#6A9FD8', categories: ['GOVERNANCE'] },
  { id: 'economies',   label: 'Spiral Economies',        sigil: '≡', color: '#A07848', categories: ['ARCHIVE', 'INFRASTRUCTURE'] },
  { id: 'cartography', label: 'Dream Cartography',       sigil: '⊛', color: '#E86A8C', categories: ['TRANSMISSION'] },
  { id: 'joy',         label: 'Technology of Joy',       sigil: '✦', color: '#D4AF37', categories: ['CODEX'] },
]

// ─── EDITORIAL SCROLL CARD ────────────────────────────────────────────────────

function EditorialScrollCard({ scroll, idx }: { scroll: CodexScroll; idx: number }) {
  const [open, setOpen] = useState(false)
  const cat = deriveCategory(scroll)
  const meta = CATEGORY_META[cat] ?? { label: cat, color: '#888', glyph: '·' }
  const isLive = !scroll.error && scroll.chars > 0
  const sizeLabel = scroll.chars >= 1000 ? `${(scroll.chars / 1000).toFixed(1)}k` : `${scroll.chars}`

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(idx * 0.028, 0.32), duration: 0.24 }}
      style={{
        background: 'rgba(8,10,20,0.6)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderLeft: `3px solid ${meta.color}`,
        borderRadius: '0 10px 10px 0',
        overflow: 'hidden',
      }}
    >
      <div onClick={() => setOpen(o => !o)} style={{ padding: '13px 16px', cursor: 'pointer' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <motion.span
            animate={isLive ? { opacity: [0.4, 1, 0.4] } : {}}
            transition={{ duration: 2.5, repeat: Infinity }}
            style={{ width: 5, height: 5, borderRadius: '50%', background: isLive ? meta.color : '#EF4444',
              flexShrink: 0, boxShadow: isLive ? `0 0 4px ${meta.color}60` : 'none' }} />
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.18em',
            textTransform: 'uppercase', color: meta.color, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 10 }}>{meta.glyph}</span>
            {meta.label}
          </span>
          <span style={{ flex: 1 }} />
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: 'rgba(232,232,232,0.2)' }}>
            {sizeLabel}c
          </span>
          <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.15 }}
            style={{ color: 'rgba(232,232,232,0.22)', flexShrink: 0 }}>
            <ChevronDown size={12} />
          </motion.span>
        </div>

        <h3 style={{ fontFamily: 'serif', fontSize: 15, fontWeight: 400, lineHeight: 1.38,
          color: open ? 'rgba(232,232,232,0.92)' : 'rgba(232,232,232,0.78)',
          margin: '0 0 7px', letterSpacing: '0.01em' }}>
          {scroll.label}
        </h3>

        {!open && scroll.preview && (
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.4)', margin: '0 0 9px',
            lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>
            {scroll.preview}
          </p>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
          {scroll.source && (
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.2)', letterSpacing: '0.05em' }}>
              {scroll.source}
            </span>
          )}
          {scroll.description && (
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, color: 'rgba(232,232,232,0.15)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 160 }}>
              {scroll.description}
            </span>
          )}
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.24 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 18px 14px', borderTop: `1px solid ${meta.color}14` }}>
              {scroll.content
                ? <MarkdownViewer content={scroll.content} />
                : scroll.preview
                ? <MarkdownViewer content={scroll.preview} />
                : <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.35)', margin: 0, fontStyle: 'italic' }}>
                    Scroll content not indexed.
                  </p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  )
}

// ─── SCROLL UPLOAD MODAL ──────────────────────────────────────────────────────

function ScrollUploadModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [type, setType] = useState('note')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [err, setErr] = useState('')

  const submit = async () => {
    if (!title.trim() || !content.trim()) return
    setLoading(true); setErr('')
    try {
      await ingestNote({ title: title.trim(), content: content.trim(), note_type: type })
      setSuccess(true)
      setTimeout(onClose, 1800)
    } catch (e) { setErr((e as Error).message || 'Ingest failed') }
    finally { setLoading(false) }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 9999,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <motion.div initial={{ scale: 0.94, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.94 }}
        style={{ background: '#0C0D18', border: '1px solid rgba(201,168,76,0.22)', borderRadius: 14,
          padding: 24, width: '100%', maxWidth: 520, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', margin: 0 }}>Oracle Corpus</p>
            <h3 style={{ fontFamily: 'serif', fontSize: 17, color: '#C9A84C', margin: '2px 0 0' }}>Scroll Upload</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: COLORS.dim, cursor: 'pointer', fontSize: 15 }}>✕</button>
        </div>
        {success ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <CheckCircle size={30} color="#00D4AA" style={{ margin: '0 auto 8px' }} />
            <p style={{ fontFamily: 'serif', fontSize: 14, color: '#00D4AA', margin: 0 }}>Scroll ingested into corpus</p>
          </div>
        ) : (
          <>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Scroll title…"
              style={{ padding: '9px 12px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#E0E0E0', fontFamily: 'sans-serif', fontSize: 13, outline: 'none' }} />
            <select value={type} onChange={e => setType(e.target.value)}
              style={{ padding: '8px 12px', background: 'rgba(14,17,32,0.9)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#E0E0E0', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }}>
              {['note', 'research', 'conversation', 'decision', 'daily'].map(t =>
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
            <textarea value={content} onChange={e => setContent(e.target.value)} rows={7} placeholder="Markdown content…"
              style={{ padding: '9px 12px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: '#E0E0E0', fontFamily: 'ui-monospace, monospace', fontSize: 11.5, outline: 'none', resize: 'vertical', lineHeight: 1.55 }} />
            {err && <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#EF4444', margin: 0 }}>{err}</p>}
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={submit} disabled={loading || !title.trim() || !content.trim()}
                style={{ flex: 1, padding: '10px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.32)', borderRadius: 8, color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', opacity: (!title.trim() || !content.trim()) ? 0.4 : 1 }}>
                {loading ? 'Ingesting…' : '⟐ Ingest into Corpus'}
              </button>
              <button onClick={onClose} style={{ padding: '10px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: COLORS.dim, cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10 }}>
                Cancel
              </button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function NexusSpiralCodex() {
  const [search, setSearch] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [prinFilter, setPrinFilter] = useState('')
  const [showUpload, setShowUpload] = useState(false)

  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ['codex-nexus'], queryFn: api.codex,
    refetchInterval: 5 * 60_000, staleTime: 2 * 60_000,
  })

  const allScrolls: CodexScroll[] = useMemo(() =>
    data?.scrolls ? Object.values(data.scrolls) : [], [data])

  const feed = useMemo(() => {
    let scrolls = allScrolls
    if (search.trim()) {
      const q = search.toLowerCase()
      scrolls = scrolls.filter(s =>
        (s.label ?? '').toLowerCase().includes(q) ||
        (s.description ?? '').toLowerCase().includes(q) ||
        (s.preview ?? '').toLowerCase().includes(q))
    }
    if (prinFilter) {
      const pCats = PRINCIPLES.find(p => p.id === prinFilter)?.categories ?? []
      scrolls = scrolls.filter(s => pCats.includes(deriveCategory(s)))
    } else if (catFilter) {
      scrolls = scrolls.filter(s => deriveCategory(s) === catFilter)
    }
    return scrolls.sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99))
  }, [allScrolls, search, catFilter, prinFilter])

  const label: React.CSSProperties = {
    fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '0.4em',
    textTransform: 'uppercase', color: 'rgba(201,168,76,0.3)', margin: 0,
  }

  if (error) return <ErrorBox>Corpus sync failed: {(error as Error).message}</ErrorBox>

  return (
    <div style={{ position: 'relative' }}>

      {/* ── Sticky page header ── */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 50, marginBottom: 16,
        background: 'rgba(2,3,8,0.88)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(201,168,76,0.08)',
        padding: '10px 0',
        marginLeft: -16, marginRight: -16, paddingLeft: 16, paddingRight: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <p style={{ ...label, margin: 0 }}>Arkadia · Spiral Codex</p>
            <h2 style={{ fontFamily: 'serif', fontSize: 16, color: 'rgba(212,175,55,0.80)', margin: '1px 0 0', letterSpacing: '0.06em', fontWeight: 400 }}>
              Living Knowledge Archive
            </h2>
          </div>
          <div style={{ flex: 1 }} />
          {data && (
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(0,212,170,0.45)' }}>
              {data.live_docs} scrolls
            </span>
          )}
          <div style={{ display: 'flex', gap: 6 }}>
            <button onClick={() => setShowUpload(true)}
              style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 10px',
                border: '1px solid rgba(201,168,76,0.16)', borderRadius: 7,
                background: 'rgba(201,168,76,0.04)', color: 'rgba(201,168,76,0.55)',
                cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.12em', textTransform: 'uppercase' as const }}>
              <Upload size={9} /> Scroll
            </button>
            <button onClick={() => refetch()} disabled={isFetching}
              style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 10px',
                border: '1px solid rgba(0,212,170,0.16)', borderRadius: 7,
                background: 'rgba(0,212,170,0.04)', color: '#00D4AA',
                cursor: isFetching ? 'wait' : 'pointer', fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.12em', textTransform: 'uppercase' as const }}>
              <RefreshCw size={9} className={isFetching ? 'animate-spin' : ''} /> Sync
            </button>
          </div>
        </div>
      </div>

      {/* ── Search ── */}
      <div style={{ position: 'relative', marginBottom: 10 }}>
        <Search size={11} style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: 'rgba(232,232,232,0.25)', pointerEvents: 'none' }} />
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search the Spiral Codex…"
          style={{ width: '100%', boxSizing: 'border-box', paddingLeft: 32, paddingRight: search ? 32 : 13, paddingTop: 9, paddingBottom: 9,
            background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 9,
            color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12.5, outline: 'none' }} />
        {search && (
          <button onClick={() => setSearch('')}
            style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'rgba(232,232,232,0.3)', cursor: 'pointer', padding: 0 }}>
            <X size={11} />
          </button>
        )}
      </div>

      {/* ── Category chips ── */}
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 }}>
        <button onClick={() => { setCatFilter(''); setPrinFilter('') }}
          style={{ flexShrink: 0, fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer',
            padding: '3px 9px', borderRadius: 5,
            background: !catFilter && !prinFilter ? 'rgba(201,168,76,0.1)' : 'transparent',
            border: !catFilter && !prinFilter ? '1px solid rgba(201,168,76,0.35)' : '1px solid rgba(255,255,255,0.06)',
            color: !catFilter && !prinFilter ? '#C9A84C' : 'rgba(232,232,232,0.28)' }}>
          ⟁ All
        </button>
        {Object.entries(CATEGORY_META).map(([key, m]) => {
          const active = catFilter === key
          return (
            <button key={key}
              onClick={() => { setCatFilter(active ? '' : key); setPrinFilter('') }}
              style={{ flexShrink: 0, fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.12em',
                textTransform: 'uppercase', cursor: 'pointer', padding: '3px 9px', borderRadius: 5,
                background: active ? `${m.color}14` : 'transparent',
                border: active ? `1px solid ${m.color}45` : `1px solid ${m.color}15`,
                color: active ? m.color : `${m.color}60`, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: 10 }}>{m.glyph}</span>
              {m.label}
            </button>
          )
        })}
      </div>

      {/* ── Seven Principles filter ── */}
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center', marginBottom: 14 }}>
        {PRINCIPLES.map(p => {
          const active = prinFilter === p.id
          return (
            <button key={p.id}
              onClick={() => { setPrinFilter(active ? '' : p.id); setCatFilter('') }}
              style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 5, padding: '3px 9px', borderRadius: 5,
                background: active ? `${p.color}10` : 'transparent',
                border: active ? `1px solid ${p.color}35` : '1px solid rgba(255,255,255,0.04)',
                color: active ? p.color : `${p.color}50`,
                cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.06em', transition: 'all 0.13s' }}>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9 }}>{p.sigil}</span>
              {p.label}
            </button>
          )
        })}
      </div>

      {/* ── Feed divider ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.12))' }} />
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.3)', whiteSpace: 'nowrap' }}>
          Spiral Codex · Knowledge Archive
        </span>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, rgba(201,168,76,0.12), transparent)' }} />
      </div>

      {/* ── Loading ── */}
      {isLoading && !data && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.6, repeat: Infinity, ease: 'linear' }}
            style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid rgba(201,168,76,0.15)', borderTopColor: '#C9A84C' }} />
        </div>
      )}

      {/* ── Feed ── */}
      {!isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {feed.length === 0
            ? <Empty>{search || catFilter || prinFilter ? 'No scrolls match this query.' : 'Corpus is empty.'}</Empty>
            : feed.map((scroll, i) => (
                <EditorialScrollCard key={scroll.id} scroll={scroll} idx={i} />
              ))
          }
          {feed.length > 0 && (
            <motion.p animate={{ opacity: [0.12, 0.3, 0.12] }} transition={{ duration: 6, repeat: Infinity }}
              style={{ textAlign: 'center', fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '0.5em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', margin: '8px 0 0' }}>
              ⟐ {feed.length} scrolls · End of archive ⟐
            </motion.p>
          )}
        </div>
      )}

      {/* ── Scroll Upload Modal ── */}
      <AnimatePresence>
        {showUpload && <ScrollUploadModal onClose={() => setShowUpload(false)} />}
      </AnimatePresence>
    </div>
  )
}
