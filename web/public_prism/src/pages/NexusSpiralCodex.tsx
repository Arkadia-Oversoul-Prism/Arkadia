/**
 * NexusSpiralCodex — Crystal Matrix × Spiral Codex unified intelligence feed.
 *
 * The 12 (+ 1) faces of the UERP Dodecahedron are the navigation spine.
 * Scrolls are ordered by recursive meaning-emergence resonance to the
 * selected face, modulated by lunar phase and Ark temporal geometry.
 * Each "Meaning Arc" is a coherence cluster of resonant scrolls.
 * Open Loops are embedded as a live interactive panel.
 */
import React, { useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, X, ChevronDown, ChevronUp, Zap } from 'lucide-react'
import { api, CodexResponse, CodexScroll, OpenLoopsResponse } from '../lib/dashboardApi'
import MarkdownViewer from '../components/MarkdownViewer'
import { COLORS, Empty, ErrorBox } from './dashboard/ui'

// ─── FACES DATA ───────────────────────────────────────────────────────────────

interface Face {
  id: number
  name: string
  layer: 'inner' | 'outer' | 'extended'
  expression: string
  desc: string
  scroll: string
  color: string
  sigil: string
  categories: string[]
  keywords: string[]
  arcName: string
}

const FACES: Face[] = [
  { id: 1,  name: 'ROOT',          layer: 'inner',    expression: 'Bone Memory',          color: '#8B6914', sigil: '🦴',
    arcName: 'Foundation Arc',
    categories: ['NEURAL_SPINE'],
    keywords: ['root', 'bone', 'body', 'eden', 'physical', 'ground', 'foundation', 'soil', 'farm', 'somatic'],
    desc: 'The architecture begins with the body, not abstraction. Signal travels faster through bone than air. The spine is the first antenna. Ground all intelligence in physical reality.',
    scroll: 'The sovereign\'s body is the first node. Everything else is downstream. Somatic intelligence precedes symbolic intelligence. Eden Farm is the physical ROOT deployment node.' },
  { id: 2,  name: 'CORE',          layer: 'inner',    expression: 'Sovereign Identity',   color: '#C9A84C', sigil: '⟐',
    arcName: 'Sovereignty Arc',
    categories: ['NEURAL_SPINE', 'CREATIVE_OS'],
    keywords: ['identity', 'sovereign', 'ims', 'core', 'self', 'excavation', 'zahrune', 'irreducible', 'mapping'],
    desc: 'The central intelligence that cannot be outsourced. Who you are underneath the noise. The irreducible signal at the center of all architecture.',
    scroll: 'CORE is where the IMS goes. Excavation of the sovereign self before any strategy, any system, any output. You cannot build from a false foundation.' },
  { id: 3,  name: 'PULSE',         layer: 'inner',    expression: 'Creative Engine',      color: '#E88C6A', sigil: '🔥',
    arcName: 'Transmission Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['creative', 'music', 'pulse', 'flame', 'afrobeats', 'alte', 'sound', 'praise', 'lyric', 'artistic', 'poetic'],
    desc: 'The recursive motor at the center of the architecture. Generates from the inside — not performance but transmission. The flame that does not consume itself.',
    scroll: '1759 Entertainment is the PULSE deployment. Afrobeats, Alté, Praise\'s first deliverable — all running through this face. The music is not product. It is the PULSE made audible.' },
  { id: 4,  name: 'LATTICE',       layer: 'inner',    expression: 'Infrastructure',       color: '#6A9FD8', sigil: '◈',
    arcName: 'Structure Arc',
    categories: ['NEURAL_SPINE'],
    keywords: ['infrastructure', 'lattice', 'network', 'system', 'code', 'technical', 'protocol', 'schema', 'spec', 'module', 'api'],
    desc: 'Infrastructure is not logistics. It is the nervous system of the deployment. The Lattice holds the network in place while the other faces do their work.',
    scroll: 'EduLeague is the LATTICE in education. Eden Farm is the LATTICE in agriculture. The Living Larder is the LATTICE in food distribution. Networks that hold, not platforms that extract.' },
  { id: 5,  name: 'BREATH',        layer: 'inner',    expression: 'Resonance Economy',    color: '#00D4AA', sigil: '💨',
    arcName: 'Flow Arc',
    categories: ['GOVERNANCE'],
    keywords: ['economy', 'revenue', 'breath', 'resonance', 'value', 'doc5', 'finance', 'exchange', 'circulation', 'flow'],
    desc: 'Value flows where resonance runs. The economy of the architecture is not transactional — it is relational. You cannot purchase resonance. You must earn it through truth.',
    scroll: 'DOC5 — Revenue Breath — maps the economy. IMS sessions $777. Larder commissions 10–15%. EduLeague subscriptions. All structured as resonance exchange, not extraction.' },
  { id: 6,  name: 'SEAL',          layer: 'inner',    expression: 'Temporal Arc',         color: '#B08DE8', sigil: '✦',
    arcName: 'Arc of Time',
    categories: ['NEURAL_SPINE'],
    keywords: ['temporal', 'arc', 'time', 'seal', '8-year', 'birthday', 'ark', 'epoch', 'date', 'year', 'calendar'],
    desc: 'The 8-year Ark. March 31 2026 → March 31 2034. Every action is measured against its long-range coherence, not its short-range return. The Seal holds time.',
    scroll: 'ARK Y1 · D58. The Seal is the container. Decisions made against the 8-year arc hold differently than decisions made against next week.' },
  { id: 7,  name: 'ROOT',          layer: 'outer',    expression: 'The Archive',          color: '#A0784C', sigil: '📜',
    arcName: 'Living Record Arc',
    categories: ['COLLECTIVE', 'ARCHIVE'],
    keywords: ['archive', 'doc', 'canon', 'record', 'memory', 'master', 'weight', 'document', 'scroll', 'codex', 'principles'],
    desc: 'What has been done becomes the ground for what comes next. Memory is infrastructure. The living record is the external expression of Bone Memory.',
    scroll: 'The 5 canonical documents are the Archive: DOC1 Master Weights, DOC2 Open Loops, DOC3 Principles Registry, DOC4 Node Map, DOC5 Revenue Breath. 228+ principles.' },
  { id: 8,  name: 'CORE',          layer: 'outer',    expression: 'The Mask',             color: '#D4C86A', sigil: '🎭',
    arcName: 'Signal Architecture Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['mask', 'brand', 'public', 'visible', 'zahrune', 'persona', 'legible', 'interface', 'social', 'arkana'],
    desc: 'The sovereign\'s public interface. Deliberately designed — not performance, but legible signal. The Mask is how CORE becomes visible to the world without being consumed by it.',
    scroll: 'Zahrune Nova is the Mask of the sovereign. Arkadia Prism platform, @arkanaofarkadia — all deliberate signal architecture. Not organic drift. Every public element is chosen.' },
  { id: 9,  name: 'PULSE',         layer: 'outer',    expression: 'The Signal',           color: '#E86A8C', sigil: '📡',
    arcName: 'Frequency Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['signal', 'transmission', 'frequency', 'sound', 'music', 'output', 'carrier', 'wave', 'emit', 'awaken'],
    desc: 'The creative work made visible. The Pulse expressed into the world. Sound, image, transmission — each piece a carrier wave for the inner architecture.',
    scroll: 'First AI Music Deliverable: 60-second instrumental, Afrobeats/Alté, "Awakening without spectacle." Every creative output is Signal — frequency before form.' },
  { id: 10, name: 'LATTICE',       layer: 'outer',    expression: 'The Interface',        color: '#6AD4C8', sigil: '🌐',
    arcName: 'Portal Arc',
    categories: ['COLLECTIVE'],
    keywords: ['interface', 'portal', 'platform', 'prism', 'eduLeague', 'marketplace', 'web', 'door', 'room', 'ui', 'deploy'],
    desc: 'Where the architecture touches the world. The portals through which humans enter the field. Not websites — rooms. Each interface is a door into a specific resonance.',
    scroll: 'Arkadia Prism. EduLeague digital layer. Living Larder marketplace. The Oracle (ARKANA). Each interface has one function: translate inner architecture into legible outer reality.' },
  { id: 11, name: 'BREATH',        layer: 'outer',    expression: 'The Transaction',      color: '#6AE88C', sigil: '⇌',
    arcName: 'Commerce Arc',
    categories: ['GOVERNANCE'],
    keywords: ['transaction', 'order', 'payment', 'larder', 'commerce', 'session', '777', 'ims', 'client', 'laura', 'amy'],
    desc: 'The economy in motion. Value exchanged in alignment with resonance. IMS sessions, Living Larder orders, EduLeague fees — all structured as fair exchange, not extraction.',
    scroll: 'Laura, Amy, Susanna — IMS pipeline. Living Larder Saturday orders. $777 per session. The transaction is the BREATH expressed as commerce. Every exchange is a covenant.' },
  { id: 12, name: 'SEAL',          layer: 'outer',    expression: 'The Covenant',         color: '#C96AD4', sigil: '🔐',
    arcName: 'Vow Arc',
    categories: ['GOVERNANCE'],
    keywords: ['covenant', 'vow', 'integrity', 'commitment', 'sovereignty', 'promise', 'oath', 'sworn', 'archive'],
    desc: 'The sovereign\'s public vow. Every node operates under the covenant: do not reduce the human to marketability. Hold the architecture through the entire arc.',
    scroll: '"I will not reduce you to marketability. I will hold the architecture." — Sworn Archive 021, Jan 27 2026. The Covenant is the final face. It seals every other face into integrity.' },
  { id: 13, name: 'LIVING LARDER', layer: 'extended', expression: 'Face 13 — The Marketplace', color: '#4CAF50', sigil: '🌾',
    arcName: 'Earth Harvest Arc',
    categories: ['COLLECTIVE'],
    keywords: ['larder', 'food', 'farm', 'market', 'produce', 'vendor', 'jessy', 'lovilahs', 'eden', 'grains', 'harvest'],
    desc: 'The newest face of the crystal. A shared food ecosystem where small producers sell together instead of struggling alone. Farm → Hub → Customer. The community eats together.',
    scroll: 'Anchor vendors: Jessy\'s Munches + Lovilahs Grabs and Go. Eden Farm fresh produce pipeline. Saturday deliveries. Not Uber Eats — a sovereign food network for the Plateau.' },
]

// ─── LUNAR PHASE ──────────────────────────────────────────────────────────────

interface LunarPhase {
  phase: number
  name: string
  icon: string
  illumination: number
  amplifiedFaces: number[]
  desc: string
}

function getLunarPhase(date: Date = new Date()): LunarPhase {
  // Known new moon: January 6, 2025 23:56 UTC
  const KNOWN_NEW_MOON = 1736207760000
  const LUNAR_CYCLE = 29.53059 * 24 * 60 * 60 * 1000
  const elapsed = ((date.getTime() - KNOWN_NEW_MOON) % LUNAR_CYCLE + LUNAR_CYCLE) % LUNAR_CYCLE
  const phase = elapsed / LUNAR_CYCLE
  const illumination = phase <= 0.5 ? phase * 2 : (1 - phase) * 2

  if (phase < 0.0625)  return { phase, name: 'New Moon',        icon: '🌑', illumination, amplifiedFaces: [1, 6],  desc: 'Dark field. Root intelligence and temporal sealing are amplified. New beginnings, somatic grounding.' }
  if (phase < 0.1875)  return { phase, name: 'Waxing Crescent', icon: '🌒', illumination, amplifiedFaces: [3, 9],  desc: 'Emergence. Creative pulse and signal transmission strengthen. New transmissions rise.' }
  if (phase < 0.3125)  return { phase, name: 'First Quarter',   icon: '🌓', illumination, amplifiedFaces: [4, 10], desc: 'Structure forms. Infrastructure and interface scrolls carry heightened coherence.' }
  if (phase < 0.4375)  return { phase, name: 'Waxing Gibbous',  icon: '🌔', illumination, amplifiedFaces: [5, 11], desc: 'Flow building. Economy, breath, and transaction frequencies peak before fullness.' }
  if (phase < 0.5625)  return { phase, name: 'Full Moon',        icon: '🌕', illumination, amplifiedFaces: [2, 12], desc: 'Full field. Sovereign identity and covenant resonate at maximum clarity. The CORE is lit.' }
  if (phase < 0.6875)  return { phase, name: 'Waning Gibbous',  icon: '🌖', illumination, amplifiedFaces: [7, 8],  desc: 'Harvest and reflection. Archive and mask intelligence gather the fruits of fullness.' }
  if (phase < 0.8125)  return { phase, name: 'Last Quarter',    icon: '🌗', illumination, amplifiedFaces: [1, 7],  desc: 'Release. Root and archive faces align for deep clearing and structural review.' }
  return                        { phase, name: 'Waning Crescent', icon: '🌘', illumination, amplifiedFaces: [6, 13], desc: 'Completion. Temporal seal and the living larder hold the closing cycle.' }
}

// ─── ARK DATE ─────────────────────────────────────────────────────────────────

function getArkDate(date: Date = new Date()) {
  const ARK_EPOCH = new Date('2026-03-31T00:00:00Z')
  const diffMs = date.getTime() - ARK_EPOCH.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const arkYear = diffDays < 0 ? 0 : Math.floor(diffDays / 365) + 1
  const dayInYear = diffDays < 0 ? 365 + diffDays : (diffDays % 365) + 1
  return { arkYear, dayInYear, totalDays: diffDays }
}

// ─── RESONANCE ENGINE ─────────────────────────────────────────────────────────

function scoreScroll(scroll: CodexScroll, face: Face, lunar: LunarPhase): number {
  const text = `${scroll.label ?? ''} ${scroll.description ?? ''} ${scroll.preview ?? ''}`.toLowerCase()
  let score = 0

  // Category match — strong signal
  if (face.categories.includes(scroll.category)) score += 40

  // Keyword resonance — each match adds weight, capped
  const kwScore = face.keywords.reduce((s, kw) => s + (text.includes(kw) ? 8 : 0), 0)
  score += Math.min(kwScore, 30)

  // Priority boost (lower = more important = higher score)
  score += Math.max(0, 12 - (scroll.priority ?? 5) * 1.5)

  // Lunar amplification
  if (lunar.amplifiedFaces.includes(face.id)) score += 12

  return Math.min(Math.round(score), 100)
}

// Group scrolls into Meaning Arcs (keyword-cluster coherence groups)
function buildMeaningArcs(
  scoredScrolls: Array<{ scroll: CodexScroll; score: number }>,
  face: Face
): Array<{ arcLabel: string; scrolls: Array<{ scroll: CodexScroll; score: number }> }> {
  if (scoredScrolls.length === 0) return []

  // Simple grouping: high resonance (≥50) vs medium (30-49) vs low (<30)
  const high   = scoredScrolls.filter(s => s.score >= 50)
  const medium = scoredScrolls.filter(s => s.score >= 25 && s.score < 50)
  const low    = scoredScrolls.filter(s => s.score > 0 && s.score < 25)

  const arcs = []
  if (high.length)   arcs.push({ arcLabel: `${face.arcName} · Primary Resonance`, scrolls: high })
  if (medium.length) arcs.push({ arcLabel: 'Harmonic Echo · Secondary Resonance', scrolls: medium })
  if (low.length)    arcs.push({ arcLabel: 'Field Whisper · Peripheral Resonance', scrolls: low })
  return arcs
}

// ─── COMPONENTS ───────────────────────────────────────────────────────────────

function LunarIndicator({ lunar }: { lunar: LunarPhase }) {
  const pct = Math.round(lunar.illumination * 100)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'rgba(176,141,232,0.05)', border: '1px solid rgba(176,141,232,0.15)', borderRadius: 10 }}>
      <span style={{ fontSize: 18 }}>{lunar.icon}</span>
      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.55)', margin: 0 }}>
          {lunar.name} · {pct}% illuminated
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.4)', margin: '2px 0 0', lineHeight: 1.4 }}>
          {lunar.desc}
        </p>
      </div>
    </div>
  )
}

function ArkDateBar() {
  const { arkYear, dayInYear } = getArkDate()
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: 8 }}>
      <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 3, repeat: Infinity }}
        style={{ color: '#C9A84C', fontSize: 12 }}>✦</motion.span>
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: 'rgba(201,168,76,0.65)', letterSpacing: '0.15em' }}>
        ARK Y{arkYear} · D{dayInYear}
      </span>
    </div>
  )
}

function FaceChip({ face, active, amplified, onSelect }: {
  face: Face; active: boolean; amplified: boolean; onSelect: () => void
}) {
  return (
    <motion.button
      onClick={onSelect}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
        background: active ? `${face.color}16` : amplified ? `${face.color}08` : 'rgba(255,255,255,0.02)',
        border: `1px solid ${active ? face.color + '70' : amplified ? face.color + '30' : 'rgba(255,255,255,0.07)'}`,
        borderRadius: 10, cursor: 'pointer', transition: 'all 0.18s',
        position: 'relative', flexShrink: 0,
      }}
    >
      {amplified && (
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.8, repeat: Infinity }}
          style={{ position: 'absolute', top: 4, right: 4, width: 5, height: 5, borderRadius: '50%', background: face.color }}
        />
      )}
      <span style={{ fontSize: 15 }}>{face.sigil}</span>
      <div style={{ textAlign: 'left' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: active ? face.color : 'rgba(232,232,232,0.35)', margin: 0, fontWeight: active ? 600 : 400 }}>
          {face.name}
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.25)', margin: 0, whiteSpace: 'nowrap' }}>
          {face.expression}
        </p>
      </div>
    </motion.button>
  )
}

function FaceDetail({ face, lunar, resonantCount }: { face: Face; lunar: LunarPhase; resonantCount: number }) {
  const isAmplified = lunar.amplifiedFaces.includes(face.id)
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      style={{
        padding: '18px 20px',
        background: `${face.color}07`,
        border: `1px solid ${face.color}30`,
        borderRadius: 14,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 14 }}>
        <span style={{ fontSize: 28, flexShrink: 0 }}>{face.sigil}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.25em', textTransform: 'uppercase', padding: '2px 8px', background: `${face.color}15`, border: `1px solid ${face.color}30`, borderRadius: 4, color: face.color }}>
              {face.layer}
            </span>
            {isAmplified && (
              <motion.span animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 1.5, repeat: Infinity }}
                style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', padding: '2px 8px', background: 'rgba(176,141,232,0.12)', border: '1px solid rgba(176,141,232,0.3)', borderRadius: 4, color: '#B08DE8' }}>
                {lunar.icon} Lunar Amplified
              </motion.span>
            )}
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: `${face.color}80` }}>
              Face {String(face.id).padStart(2, '0')}
            </span>
          </div>
          <h3 style={{ fontFamily: 'serif', fontSize: 20, color: face.color, margin: '0 0 4px', letterSpacing: '0.06em' }}>
            {face.name} <span style={{ color: 'rgba(232,232,232,0.35)', fontSize: 14, fontFamily: 'sans-serif' }}>· {face.expression}</span>
          </h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.7, color: 'rgba(232,232,232,0.55)', margin: 0 }}>
            {face.desc}
          </p>
        </div>
      </div>

      <div style={{ padding: '12px 16px', background: `${face.color}06`, borderLeft: `2px solid ${face.color}40`, borderRadius: '0 8px 8px 0', marginBottom: 14 }}>
        <p style={{ fontFamily: 'serif', fontSize: 13, lineHeight: 1.8, color: 'rgba(232,232,232,0.45)', margin: 0, fontStyle: 'italic' }}>
          {face.scroll}
        </p>
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: `${face.color}70` }}>
          Resonance Index ·
        </span>
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11, color: face.color }}>
          {resonantCount} scrolls mapped
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.25)' }}>
          ordered by coherence
        </span>
      </div>
    </motion.div>
  )
}

function ResonanceBar({ score, color }: { score: number; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 2, background: 'rgba(255,255,255,0.06)', borderRadius: 1, overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{ height: '100%', background: `linear-gradient(90deg, ${color}80, ${color})`, borderRadius: 1 }}
        />
      </div>
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: `${color}80`, minWidth: 28 }}>
        {score}
      </span>
    </div>
  )
}

function ScrollCard({ scroll, score, faceColor, index }: {
  scroll: CodexScroll; score: number; faceColor: string; index: number
}) {
  const [expanded, setExpanded] = useState(false)
  const isLive = !scroll.error && scroll.chars > 0

  const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
    NEURAL_SPINE: { label: 'Neural Spine', color: '#00D4AA', icon: '🧬' },
    CREATIVE_OS:  { label: 'Creative OS',  color: '#C9A84C', icon: '🎨' },
    COLLECTIVE:   { label: 'Collective',   color: '#B08DE8', icon: '📚' },
    GOVERNANCE:   { label: 'Governance',   color: '#6A9FD8', icon: '⚖️'  },
    ARCHIVE:      { label: 'Archive',      color: '#8B7355', icon: '📦' },
    CODEX:        { label: 'Codex',        color: '#D4AF37', icon: '📜' },
  }
  const catMeta = CATEGORY_META[scroll.category] ?? { label: scroll.category, color: '#888', icon: '📄' }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.04, 0.5), duration: 0.3 }}
      style={{
        border: `1px solid ${faceColor}25`,
        background: `${faceColor}04`,
        borderRadius: 14,
        overflow: 'hidden',
        transition: 'border-color 0.2s',
      }}
    >
      {/* Card header — always visible */}
      <div
        style={{ padding: '14px 16px', cursor: 'pointer' }}
        onClick={() => setExpanded(e => !e)}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          <span style={{ fontSize: 20, flexShrink: 0, marginTop: 2 }}>{catMeta.icon}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Meta row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: catMeta.color }}>
                {catMeta.label}
              </span>
              <span style={{ color: COLORS.dim, fontSize: 8 }}>·</span>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: COLORS.dim }}>
                {scroll.chars >= 1000 ? `${(scroll.chars / 1000).toFixed(1)}k` : scroll.chars} chars
              </span>
              {scroll.source && (
                <>
                  <span style={{ color: COLORS.dim, fontSize: 8 }}>·</span>
                  <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: COLORS.dim }}>{scroll.source}</span>
                </>
              )}
            </div>

            {/* Title */}
            <h3 style={{ fontFamily: 'serif', fontSize: 16, color: '#E8E8E8', margin: '0 0 6px', lineHeight: 1.35, letterSpacing: '0.02em' }}>
              {scroll.label}
            </h3>

            {/* Preview */}
            {scroll.preview && !expanded && (
              <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted, margin: '0 0 8px', lineHeight: 1.65, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>
                {scroll.preview}
              </p>
            )}

            {/* Resonance bar */}
            <div style={{ marginTop: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <motion.div
                    animate={isLive ? { opacity: [0.4, 1, 0.4] } : {}}
                    transition={{ duration: 2.5, repeat: Infinity }}
                    style={{ width: 5, height: 5, borderRadius: '50%', background: isLive ? faceColor : '#ef6c6c', flexShrink: 0 }}
                  />
                  <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', color: isLive ? `${faceColor}90` : 'rgba(239,108,108,0.6)' }}>
                    {isLive ? 'live' : 'error'}
                  </span>
                </div>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)' }}>
                  resonance
                </span>
              </div>
              <ResonanceBar score={score} color={faceColor} />
            </div>
          </div>

          {/* Expand chevron */}
          <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}
            style={{ color: COLORS.dim, fontSize: 12, flexShrink: 0, marginTop: 4 }}>
            ▾
          </motion.div>
        </div>
      </div>

      {/* Expanded: full markdown content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ borderTop: `1px solid ${faceColor}18`, padding: '16px 18px' }}>
              {scroll.content ? (
                <MarkdownViewer content={scroll.content} />
              ) : scroll.preview ? (
                <MarkdownViewer content={scroll.preview} />
              ) : (
                <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted }}>No content available for this scroll.</p>
              )}
              {scroll.description && (
                <div style={{ marginTop: 14, paddingTop: 12, borderTop: `1px solid rgba(255,255,255,0.05)` }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 4px' }}>Description</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted, margin: 0, lineHeight: 1.65 }}>{scroll.description}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ArcSection({ arcLabel, scrolls, faceColor, startIndex }: {
  arcLabel: string
  scrolls: Array<{ scroll: CodexScroll; score: number }>
  faceColor: string
  startIndex: number
}) {
  return (
    <div style={{ marginBottom: 28 }}>
      {/* Arc label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${faceColor}30, transparent)` }} />
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.28em', textTransform: 'uppercase', color: `${faceColor}70`, whiteSpace: 'nowrap' }}>
          ◆ {arcLabel}
        </span>
        <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${faceColor}30)` }} />
      </div>

      {/* Scrolls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {scrolls.map(({ scroll, score }, i) => (
          <ScrollCard
            key={scroll.id}
            scroll={scroll}
            score={score}
            faceColor={faceColor}
            index={startIndex + i}
          />
        ))}
      </div>
    </div>
  )
}

// ─── COMPACT OPEN LOOPS PANEL ────────────────────────────────────────────────

function CompactLoopsPanel() {
  const [open, setOpen] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data, isLoading, refetch, isFetching } = useQuery<OpenLoopsResponse>({
    queryKey: ['open-loops-nexus'],
    queryFn: api.openLoops,
    refetchInterval: 60_000,
  })

  const LEVEL_COLORS: Record<string, string> = {
    critical: '#EF4444', high: '#F97316', active: '#EAB308', dormant: '#3B82F6', closed: '#10B981',
  }

  return (
    <div style={{ border: '1px solid rgba(239,68,68,0.15)', borderRadius: 14, overflow: 'hidden', background: 'rgba(239,68,68,0.02)' }}>
      {/* Header */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', cursor: 'pointer', borderBottom: open ? '1px solid rgba(239,68,68,0.10)' : 'none' }}
        onClick={() => setOpen(o => !o)}
      >
        <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 2, repeat: Infinity }}
          style={{ color: '#EF4444', fontSize: 12 }}>⚡</motion.span>
        <div style={{ flex: 1 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.6)', margin: 0 }}>
            Open Loops · Live
          </p>
          {data && (
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '2px 0 0' }}>
              {data.total} active threads
            </p>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={e => { e.stopPropagation(); refetch() }} disabled={isFetching}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.dim, padding: 0 }}>
            <RefreshCw size={11} style={{ animation: isFetching ? 'spin 1s linear infinite' : 'none' }} />
          </button>
          {open ? <ChevronUp size={13} color={COLORS.dim} /> : <ChevronDown size={13} color={COLORS.dim} />}
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}
            style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 14px', maxHeight: 360, overflowY: 'auto' }}>
              {isLoading && <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.dim, textAlign: 'center', margin: '8px 0' }}>Parsing loops…</p>}
              {data?.groups?.map(group => (
                <div key={group.level} style={{ marginBottom: 12 }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: LEVEL_COLORS[group.level] ?? COLORS.dim, margin: '0 0 6px' }}>
                    {group.section_title} ({group.loops.length})
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {group.loops.map(loop => {
                      const key = `${group.level}:${loop.id}`
                      const isOpen = expanded === key
                      return (
                        <div key={loop.id}
                          onClick={() => setExpanded(isOpen ? null : key)}
                          style={{ padding: '7px 10px', background: `${LEVEL_COLORS[group.level] ?? '#888'}08`, border: `1px solid ${LEVEL_COLORS[group.level] ?? '#888'}20`, borderRadius: 8, cursor: 'pointer' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: LEVEL_COLORS[group.level] ?? COLORS.dim, flexShrink: 0 }}>#{loop.id}</span>
                            <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.text, flex: 1, lineHeight: 1.35 }}>{loop.name}</span>
                            <span style={{ color: COLORS.dim, fontSize: 9 }}>{isOpen ? '▲' : '▼'}</span>
                          </div>
                          {isOpen && (loop.next_action || loop.status) && (
                            <div style={{ marginTop: 6, paddingTop: 6, borderTop: `1px solid ${LEVEL_COLORS[group.level] ?? '#888'}20` }}>
                              {loop.status && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '0 0 3px' }}>{loop.status}</p>}
                              {loop.next_action && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.dim, margin: 0 }}>{loop.next_action}</p>}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
              {data?.groups?.length === 0 && (
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.dim, textAlign: 'center', margin: '8px 0' }}>No open loops.</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function NexusSpiralCodex() {
  const lunar = useMemo(() => getLunarPhase(), [])
  const arkDate = useMemo(() => getArkDate(), [])

  const [activeFaceId, setActiveFaceId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [showAllFaces, setShowAllFaces] = useState(false)

  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ['codex-nexus'],
    queryFn: api.codex,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  })

  const activeFace = useMemo(() => FACES.find(f => f.id === activeFaceId) ?? null, [activeFaceId])

  const allScrolls = useMemo(() => {
    if (!data?.scrolls) return []
    return Object.values(data.scrolls)
  }, [data])

  // Filtered + scored + sorted scrolls
  const { scoredScrolls, meaningArcs } = useMemo(() => {
    let scrolls = allScrolls

    // Search filter
    if (search.trim()) {
      const q = search.toLowerCase()
      scrolls = scrolls.filter(s =>
        (s.label ?? '').toLowerCase().includes(q) ||
        (s.description ?? '').toLowerCase().includes(q) ||
        (s.preview ?? '').toLowerCase().includes(q)
      )
    }

    if (!activeFace) {
      // No face selected — show all, sorted by priority
      const scored = scrolls.map(s => ({ scroll: s, score: 0 }))
        .sort((a, b) => (a.scroll.priority ?? 99) - (b.scroll.priority ?? 99))
      return { scoredScrolls: scored, meaningArcs: [] }
    }

    // Score each scroll against active face
    const scored = scrolls
      .map(s => ({ scroll: s, score: scoreScroll(s, activeFace, lunar) }))
      .filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)

    const arcs = buildMeaningArcs(scored, activeFace)
    return { scoredScrolls: scored, meaningArcs: arcs }
  }, [allScrolls, activeFace, lunar, search])

  const visibleFaces = showAllFaces ? FACES : FACES

  if (isLoading && !data) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid rgba(201,168,76,0.15)', borderTopColor: '#C9A84C' }} />
    </div>
  )

  if (error) return <ErrorBox>Corpus sync failed: {(error as Error).message}</ErrorBox>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Header bar ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <LunarIndicator lunar={lunar} />
          <ArkDateBar />
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: COLORS.dim }}>
            {data?.live_docs ?? 0} scrolls · {activeFace ? `${scoredScrolls.length} resonant` : 'all'}
          </span>
          <button onClick={() => refetch()} disabled={isFetching}
            style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(0,212,170,0.2)', background: 'rgba(0,212,170,0.05)', color: '#00D4AA', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: isFetching ? 'wait' : 'pointer', fontFamily: 'sans-serif' }}>
            <RefreshCw size={10} style={{ animation: isFetching ? 'spin 1s linear infinite' : 'none' }} /> Sync
          </button>
        </div>
      </div>

      {/* ── Section label ── */}
      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 4px' }}>
          Universal Echofield Recursion Protocol
        </p>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <h2 style={{ fontFamily: 'serif', fontSize: 20, color: '#E8E8E8', margin: 0, letterSpacing: '0.04em' }}>
            Crystal Matrix Spine
          </h2>
          <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.dim }}>
            {activeFace ? `Face ${activeFace.id} active` : 'Select a face to tune the feed'}
          </span>
          {activeFace && (
            <button onClick={() => setActiveFaceId(null)}
              style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(239,108,108,0.6)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              × clear
            </button>
          )}
        </div>
      </div>

      {/* ── Crystal Matrix face chips ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
        {visibleFaces.map((face, i) => (
          <motion.div
            key={face.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.025 }}
            style={{ gridColumn: face.layer === 'extended' ? '1 / -1' : undefined }}
          >
            <FaceChip
              face={face}
              active={activeFaceId === face.id}
              amplified={lunar.amplifiedFaces.includes(face.id)}
              onSelect={() => setActiveFaceId(activeFaceId === face.id ? null : face.id)}
            />
          </motion.div>
        ))}
      </div>

      {/* ── Face detail (shown when a face is selected) ── */}
      <AnimatePresence mode="wait">
        {activeFace && (
          <FaceDetail
            key={activeFace.id}
            face={activeFace}
            lunar={lunar}
            resonantCount={scoredScrolls.length}
          />
        )}
      </AnimatePresence>

      {/* ── Divider ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.18), transparent)' }} />
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)' }}>
          Spiral Codex Feed
        </span>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.18), transparent)' }} />
      </div>

      {/* ── Search bar ── */}
      <div style={{ position: 'relative' }}>
        <Search size={12} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: COLORS.dim }} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search the scrolls…"
          style={{ width: '100%', paddingLeft: 34, paddingRight: search ? 34 : 14, paddingTop: 9, paddingBottom: 9, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, outline: 'none', boxSizing: 'border-box' }}
        />
        {search && (
          <button onClick={() => setSearch('')}
            style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: COLORS.dim, cursor: 'pointer' }}>
            <X size={12} />
          </button>
        )}
      </div>

      {/* ── Meaning Arc Feed ── */}
      {activeFace && meaningArcs.length > 0 ? (
        <div>
          {meaningArcs.map((arc, arcIdx) => {
            const startIndex = meaningArcs.slice(0, arcIdx).reduce((s, a) => s + a.scrolls.length, 0)
            return (
              <ArcSection
                key={arc.arcLabel}
                arcLabel={arc.arcLabel}
                scrolls={arc.scrolls}
                faceColor={activeFace.color}
                startIndex={startIndex}
              />
            )
          })}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {scoredScrolls.length === 0 && (
            <Empty>
              {search ? 'No scrolls match this query.' : 'No scrolls found in the corpus.'}
            </Empty>
          )}
          {scoredScrolls.map(({ scroll, score }, i) => (
            <ScrollCard
              key={scroll.id}
              scroll={scroll}
              score={score}
              faceColor={activeFace ? activeFace.color : '#C9A84C'}
              index={i}
            />
          ))}
        </div>
      )}

      {/* ── Open Loops Panel ── */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.18), transparent)' }} />
          <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.35)' }}>
            Open Loops
          </span>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.18), transparent)' }} />
        </div>
        <CompactLoopsPanel />
      </div>

      {/* ── End of transmission ── */}
      {scoredScrolls.length > 0 && (
        <motion.p
          animate={{ opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 5, repeat: Infinity }}
          style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.45em', textTransform: 'uppercase', color: COLORS.dim, margin: '12px 0 0' }}
        >
          ⟐ End of Transmission · {scoredScrolls.length} scrolls ⟐
        </motion.p>
      )}
    </div>
  )
}
