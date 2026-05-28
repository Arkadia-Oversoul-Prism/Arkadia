/**
 * NexusSpiralCodex — Crystal Matrix × Spiral Codex unified intelligence feed.
 *
 * UERP Dodecahedron faces arranged as a geometric dodecagonal ring.
 * 12 faces at 30° intervals; Face 13 (Living Larder) at center.
 * Inner/outer pairs are adjacent on the ring.
 *
 * Category inference: derived from scroll `id` and `description` (file path),
 * not from the backend's CREATIVE_OS fallback.
 */
import React, { useState, useMemo, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, X, ChevronDown, ChevronUp } from 'lucide-react'
import { api, CodexResponse, CodexScroll, OpenLoopsResponse } from '../lib/dashboardApi'
import MarkdownViewer from '../components/MarkdownViewer'
import { COLORS, Empty, ErrorBox } from './dashboard/ui'

// ─── CATEGORY INFERENCE ───────────────────────────────────────────────────────

/**
 * Derives the real category from scroll id + description (which contains the
 * original file path). The backend often falls through to "CREATIVE_OS" for
 * anything under docs/ so we re-classify here with richer logic.
 */
function deriveCategory(scroll: CodexScroll): string {
  const id = scroll.id.toLowerCase()
  const desc = (scroll.description || '').toLowerCase()

  // Subdirectory signals (most reliable)
  if (desc.includes('/creative/') || id.includes('_creative_'))  return 'CREATIVE_OS'
  if (desc.includes('/collective/') || id.includes('_collective_')) return 'COLLECTIVE'
  if (desc.includes('/governance/') || id.includes('_governance_')) return 'GOVERNANCE'

  // Root-level corpus meta-docs → infrastructure
  if (/corpus_api|corpus_deploy/.test(id)) return 'INFRASTRUCTURE'

  // Named canonical documents
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

  // Already correctly set by backend
  if (scroll.category && scroll.category !== 'CREATIVE_OS') return scroll.category

  // Default for docs/ root = NEURAL_SPINE
  if (desc.startsWith('docs/')) return 'NEURAL_SPINE'

  return 'CODEX'
}

const CATEGORY_META: Record<string, { label: string; color: string; glyph: string }> = {
  NEURAL_SPINE:   { label: 'Neural Spine',   color: '#00D4AA', glyph: '⬡' },
  CREATIVE_OS:    { label: 'Creative OS',    color: '#C9A84C', glyph: '◈' },
  COLLECTIVE:     { label: 'Collective',     color: '#B08DE8', glyph: '⊹' },
  GOVERNANCE:     { label: 'Governance',     color: '#6A9FD8', glyph: '⊞' },
  ARCHIVE:        { label: 'Archive',        color: '#A07848', glyph: '≡' },
  TRANSMISSION:   { label: 'Transmission',  color: '#E86A8C', glyph: '⊛' },
  INFRASTRUCTURE: { label: 'Infrastructure',color: '#6AE88C', glyph: '⊟' },
  CODEX:          { label: 'Codex',          color: '#D4AF37', glyph: '✦' },
}

// ─── FACE SIGILS ──────────────────────────────────────────────────────────────

/**
 * Each sigil is a small SVG path on a 20×20 grid.
 * Designed to look like geometric glyphs, not emoji.
 */
function FaceSigil({ faceId, size, color }: { faceId: number; size: number; color: string }) {
  const s = size
  const h = s / 2
  const c = color
  const sw = s * 0.09      // stroke width
  const sw2 = s * 0.065    // thin stroke

  const sigils: Record<number, React.ReactNode> = {
    /* 1 ROOT inner — Downward grounding triangle */
    1: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round">
         <polygon points={`${h},${s*0.78} ${s*0.15},${s*0.22} ${s*0.85},${s*0.22}`} />
         <line x1={s*0.15} y1={s*0.22} x2={s*0.85} y2={s*0.22} strokeWidth={sw*1.5} />
       </g>,

    /* 2 CORE inner — Concentric rings + center node */
    2: <g fill="none" stroke={c} strokeWidth={sw2}>
         <circle cx={h} cy={h} r={s*0.38} />
         <circle cx={h} cy={h} r={s*0.22} />
         <circle cx={h} cy={h} r={s*0.07} fill={c} stroke="none" />
       </g>,

    /* 3 PULSE inner — Sine wave (transmission) */
    3: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round">
         <path d={`M ${s*0.08},${h} C ${s*0.2},${s*0.2} ${s*0.35},${s*0.2} ${h},${h} C ${s*0.65},${s*0.8} ${s*0.8},${s*0.8} ${s*0.92},${h}`} />
       </g>,

    /* 4 LATTICE inner — Grid of 4 nodes */
    4: <g stroke={c} strokeWidth={sw2} fill="none">
         <line x1={s*0.28} y1={s*0.28} x2={s*0.72} y2={s*0.28} />
         <line x1={s*0.28} y1={s*0.72} x2={s*0.72} y2={s*0.72} />
         <line x1={s*0.28} y1={s*0.28} x2={s*0.28} y2={s*0.72} />
         <line x1={s*0.72} y1={s*0.28} x2={s*0.72} y2={s*0.72} />
         <line x1={s*0.28} y1={h} x2={s*0.72} y2={h} />
         <line x1={h} y1={s*0.28} x2={h} y2={s*0.72} />
         {[s*0.28, h, s*0.72].map(x => [s*0.28, s*0.72].map(y =>
           <circle key={`${x}-${y}`} cx={x} cy={y} r={s*0.05} fill={c} stroke="none" />
         ))}
       </g>,

    /* 5 BREATH inner — Infinity / continuous flow */
    5: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round">
         <path d={`M ${h},${h} C ${h},${s*0.2} ${s*0.15},${s*0.2} ${s*0.15},${h} C ${s*0.15},${s*0.8} ${h},${s*0.8} ${h},${h} C ${h},${s*0.2} ${s*0.85},${s*0.2} ${s*0.85},${h} C ${s*0.85},${s*0.8} ${h},${s*0.8} ${h},${h}`} />
       </g>,

    /* 6 SEAL inner — Hexagon (temporal container) */
    6: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round">
         <polygon points={`${h},${s*0.1} ${s*0.85},${s*0.3} ${s*0.85},${s*0.7} ${h},${s*0.9} ${s*0.15},${s*0.7} ${s*0.15},${s*0.3}`} />
         <line x1={s*0.35} y1={h} x2={s*0.65} y2={h} strokeWidth={sw2} />
       </g>,

    /* 7 ROOT outer — Archive: three document lines */
    7: <g stroke={c} strokeWidth={sw} strokeLinecap="round">
         <line x1={s*0.2} y1={s*0.3} x2={s*0.8} y2={s*0.3} />
         <line x1={s*0.2} y1={h}     x2={s*0.8} y2={h} />
         <line x1={s*0.2} y1={s*0.7} x2={s*0.62} y2={s*0.7} />
         <rect x={s*0.15} y={s*0.18} width={s*0.7} height={s*0.64} rx={s*0.04} fill="none" strokeWidth={sw2} />
       </g>,

    /* 8 CORE outer — Mask / diamond visibility */
    8: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round">
         <polygon points={`${h},${s*0.1} ${s*0.9},${h} ${h},${s*0.9} ${s*0.1},${h}`} />
         <polygon points={`${h},${s*0.32} ${s*0.68},${h} ${h},${s*0.68} ${s*0.32},${h}`} strokeWidth={sw2} />
       </g>,

    /* 9 PULSE outer — Signal: radiating concentric arcs */
    9: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round">
         <circle cx={h} cy={h} r={s*0.08} fill={c} stroke="none" />
         <path d={`M ${s*0.3},${s*0.78} A ${s*0.28},${s*0.28} 0 0,1 ${s*0.7},${s*0.78}`} />
         <path d={`M ${s*0.15},${s*0.88} A ${s*0.43},${s*0.43} 0 0,1 ${s*0.85},${s*0.88}`} />
         <line x1={h} y1={h} x2={h} y2={s*0.28} strokeWidth={sw2} />
       </g>,

    /* 10 LATTICE outer — Interface: triangle of nodes */
    10: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round">
          <polygon points={`${h},${s*0.12} ${s*0.85},${s*0.82} ${s*0.15},${s*0.82}`} />
          <line x1={h} y1={s*0.12} x2={h} y2={s*0.82} strokeWidth={sw2} />
          <circle cx={h}       cy={s*0.12} r={s*0.07} fill={c} stroke="none" />
          <circle cx={s*0.85}  cy={s*0.82} r={s*0.07} fill={c} stroke="none" />
          <circle cx={s*0.15}  cy={s*0.82} r={s*0.07} fill={c} stroke="none" />
          <circle cx={h}       cy={s*0.82} r={s*0.05} fill={c} stroke="none" />
        </g>,

    /* 11 BREATH outer — Transaction: exchange arrows */
    11: <g stroke={c} strokeWidth={sw} strokeLinecap="round" fill="none">
          <line x1={s*0.18} y1={s*0.38} x2={s*0.82} y2={s*0.38} />
          <polyline points={`${s*0.68},${s*0.24} ${s*0.82},${s*0.38} ${s*0.68},${s*0.52}`} />
          <line x1={s*0.18} y1={s*0.62} x2={s*0.82} y2={s*0.62} />
          <polyline points={`${s*0.32},${s*0.48} ${s*0.18},${s*0.62} ${s*0.32},${s*0.76}`} />
        </g>,

    /* 12 SEAL outer — Covenant: padlock glyph */
    12: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round">
          <rect x={s*0.24} y={h} width={s*0.52} height={s*0.42} rx={s*0.05} />
          <path d={`M ${s*0.34},${h} Q ${s*0.34},${s*0.24} ${h},${s*0.24} Q ${s*0.66},${s*0.24} ${s*0.66},${h}`} />
          <circle cx={h} cy={s*0.72} r={s*0.06} fill={c} stroke="none" />
        </g>,

    /* 13 LARDER — Grain stalk + leaf */
    13: <g stroke={c} strokeWidth={sw} strokeLinecap="round" fill="none">
          <line x1={h} y1={s*0.88} x2={h} y2={s*0.12} />
          <path d={`M ${h},${s*0.45} Q ${s*0.28},${s*0.35} ${s*0.22},${s*0.22}`} />
          <path d={`M ${h},${s*0.55} Q ${s*0.72},${s*0.45} ${s*0.78},${s*0.32}`} />
          <path d={`M ${h},${s*0.65} Q ${s*0.32},${s*0.58} ${s*0.28},${s*0.48}`} />
        </g>,
  }

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: 'visible', display: 'block' }}>
      {sigils[faceId] ?? <circle cx={h} cy={h} r={h * 0.7} fill="none" stroke={c} strokeWidth={sw} />}
    </svg>
  )
}

// ─── FACE DATA ────────────────────────────────────────────────────────────────

interface Face {
  id: number
  name: string
  layer: 'inner' | 'outer' | 'extended'
  expression: string
  desc: string
  scroll: string
  color: string
  categories: string[]
  keywords: string[]
  arcName: string
}

const FACES: Face[] = [
  { id: 1,  name: 'ROOT',     layer: 'inner', expression: 'Bone Memory',       color: '#A07840',
    arcName: 'Foundation Arc', categories: ['NEURAL_SPINE'],
    keywords: ['root', 'bone', 'body', 'eden', 'physical', 'ground', 'foundation', 'soil', 'farm', 'somatic'],
    desc: 'Signal travels faster through bone than air. The spine is the first antenna. Ground all intelligence in physical reality.',
    scroll: 'The sovereign\'s body is the first node. Somatic intelligence precedes symbolic. Eden Farm is the ROOT deployment node.' },
  { id: 2,  name: 'CORE',     layer: 'inner', expression: 'Sovereign Identity', color: '#C9A84C',
    arcName: 'Sovereignty Arc', categories: ['NEURAL_SPINE', 'CREATIVE_OS'],
    keywords: ['identity', 'sovereign', 'ims', 'core', 'self', 'excavation', 'zahrune', 'mapping', 'weight'],
    desc: 'The central intelligence that cannot be outsourced. The irreducible signal at the center of all architecture.',
    scroll: 'CORE is where the IMS lives. Excavation of the sovereign self before any strategy, any system, any output.' },
  { id: 3,  name: 'PULSE',    layer: 'inner', expression: 'Creative Engine',   color: '#E88C6A',
    arcName: 'Transmission Arc', categories: ['CREATIVE_OS'],
    keywords: ['creative', 'music', 'pulse', 'afrobeats', 'alte', 'sound', 'praise', 'lyric', 'artistic', 'poetic', 'auralis'],
    desc: 'The recursive motor at the center. Generates from the inside — transmission, not performance.',
    scroll: '1759 Entertainment is the PULSE deployment. Afrobeats, Alté, Praise\'s first deliverable.' },
  { id: 4,  name: 'LATTICE',  layer: 'inner', expression: 'Infrastructure',    color: '#6A9FD8',
    arcName: 'Structure Arc', categories: ['NEURAL_SPINE', 'INFRASTRUCTURE'],
    keywords: ['infrastructure', 'lattice', 'network', 'system', 'code', 'technical', 'protocol', 'schema', 'spec', 'api', 'corpus'],
    desc: 'Infrastructure is the nervous system of the deployment. The Lattice holds the network while other faces do their work.',
    scroll: 'The Spiral Grove is the LATTICE in education. Eden Farm in agriculture. Networks that hold, not platforms that extract.' },
  { id: 5,  name: 'BREATH',   layer: 'inner', expression: 'Resonance Economy', color: '#00D4AA',
    arcName: 'Flow Arc', categories: ['GOVERNANCE'],
    keywords: ['economy', 'revenue', 'breath', 'resonance', 'value', 'doc5', 'finance', 'exchange', 'flow', 'principles'],
    desc: 'Value flows where resonance runs. The economy is relational — not transactional.',
    scroll: 'DOC5 — Revenue Breath. IMS sessions $777. Living Larder commissions 10–15%. Spiral Grove memberships.' },
  { id: 6,  name: 'SEAL',     layer: 'inner', expression: 'Temporal Arc',      color: '#B08DE8',
    arcName: 'Arc of Time', categories: ['NEURAL_SPINE'],
    keywords: ['temporal', 'arc', 'time', 'seal', '8-year', 'birthday', 'ark', 'epoch', 'date', 'year', 'uerp', 'crystal'],
    desc: 'The 8-year Ark. March 31 2026 → 2034. Every action measured against long-range coherence.',
    scroll: 'ARK Y1 · D58. The Seal is the container. Decisions against the 8-year arc hold differently.' },
  { id: 7,  name: 'ROOT',     layer: 'outer', expression: 'The Archive',        color: '#A07848',
    arcName: 'Living Record Arc', categories: ['ARCHIVE', 'COLLECTIVE'],
    keywords: ['archive', 'doc', 'canon', 'record', 'memory', 'master', 'weight', 'document', 'scroll', 'principles'],
    desc: 'Memory is infrastructure. The living record is the external expression of Bone Memory.',
    scroll: 'DOC1 Master Weights, DOC2 Open Loops, DOC3 Principles, DOC4 Node Map, DOC5 Revenue. 228+ principles.' },
  { id: 8,  name: 'CORE',     layer: 'outer', expression: 'The Mask',           color: '#D4C86A',
    arcName: 'Signal Architecture Arc', categories: ['CREATIVE_OS', 'TRANSMISSION'],
    keywords: ['mask', 'brand', 'public', 'visible', 'zahrune', 'persona', 'legible', 'interface', 'arche', 'vhixnova'],
    desc: 'The sovereign\'s public interface. Deliberately designed. How CORE becomes visible without being consumed.',
    scroll: 'Zahrune Nova is the Mask. Arkadia Prism platform — all deliberate signal architecture. Not organic drift.' },
  { id: 9,  name: 'PULSE',    layer: 'outer', expression: 'The Signal',         color: '#E86A8C',
    arcName: 'Frequency Arc', categories: ['CREATIVE_OS', 'TRANSMISSION'],
    keywords: ['signal', 'transmission', 'frequency', 'sound', 'music', 'output', 'carrier', 'wave', 'lyric', 'poetic'],
    desc: 'The creative work made visible. Pulse expressed into the world. Each piece a carrier wave.',
    scroll: 'First AI Music Deliverable: 60-second Afrobeats/Alté. "Awakening without spectacle."' },
  { id: 10, name: 'LATTICE',  layer: 'outer', expression: 'The Interface',      color: '#6AD4C8',
    arcName: 'Portal Arc', categories: ['COLLECTIVE', 'INFRASTRUCTURE'],
    keywords: ['interface', 'portal', 'platform', 'prism', 'eduleague', 'marketplace', 'web', 'door', 'ui', 'deploy', 'council'],
    desc: 'Where the architecture touches the world. Portals through which humans enter the field. Not websites — rooms.',
    scroll: 'Arkadia Prism. The Spiral Grove digital layer. The Living Larder marketplace. The Oracle (ARKANA).' },
  { id: 11, name: 'BREATH',   layer: 'outer', expression: 'The Transaction',    color: '#6AE88C',
    arcName: 'Commerce Arc', categories: ['GOVERNANCE'],
    keywords: ['transaction', 'order', 'payment', 'larder', 'commerce', 'session', '777', 'ims', 'client'],
    desc: 'The economy in motion. Value exchanged in alignment with resonance. Structured as fair exchange.',
    scroll: 'Laura, Amy, Susanna — IMS pipeline. Living Larder Saturday orders. $777 per session.' },
  { id: 12, name: 'SEAL',     layer: 'outer', expression: 'The Covenant',       color: '#C96AD4',
    arcName: 'Vow Arc', categories: ['GOVERNANCE'],
    keywords: ['covenant', 'vow', 'integrity', 'commitment', 'sovereignty', 'promise', 'oath', 'sworn'],
    desc: 'The sovereign\'s public vow. Every node: do not reduce the human to marketability.',
    scroll: '"I will not reduce you to marketability." — Sworn Archive 021. The Covenant seals every other face.' },
  { id: 13, name: 'LARDER',   layer: 'extended', expression: 'The Marketplace', color: '#4CAF50',
    arcName: 'Earth Harvest Arc', categories: ['COLLECTIVE'],
    keywords: ['larder', 'food', 'farm', 'market', 'produce', 'vendor', 'jessy', 'lovilahs', 'eden', 'grains', 'harvest'],
    desc: 'A shared food ecosystem where small producers sell together. The community eats together.',
    scroll: 'Anchor vendors: Jessy\'s Munches + Lovilahs Grabs and Go. Eden Farm fresh produce. Saturday deliveries.' },
]

// ─── LUNAR PHASE ──────────────────────────────────────────────────────────────

interface LunarPhase {
  phase: number; name: string; icon: string; illumination: number
  amplifiedFaces: number[]; desc: string
}
function getLunarPhase(date = new Date()): LunarPhase {
  const KNM = 1736207760000, LC = 29.53059 * 864e5
  const elapsed = ((date.getTime() - KNM) % LC + LC) % LC
  const phase = elapsed / LC
  const illumination = phase <= 0.5 ? phase * 2 : (1 - phase) * 2
  if (phase < 0.0625)  return { phase, name: 'New Moon',        icon: '🌑', illumination, amplifiedFaces: [1,6],  desc: 'Root intelligence and temporal sealing amplified.' }
  if (phase < 0.1875)  return { phase, name: 'Waxing Crescent', icon: '🌒', illumination, amplifiedFaces: [3,9],  desc: 'Creative pulse and signal transmission strengthen.' }
  if (phase < 0.3125)  return { phase, name: 'First Quarter',   icon: '🌓', illumination, amplifiedFaces: [4,10], desc: 'Infrastructure and interface scrolls heightened.' }
  if (phase < 0.4375)  return { phase, name: 'Waxing Gibbous',  icon: '🌔', illumination, amplifiedFaces: [5,11], desc: 'Economy and transaction frequencies peak.' }
  if (phase < 0.5625)  return { phase, name: 'Full Moon',        icon: '🌕', illumination, amplifiedFaces: [2,12], desc: 'Sovereign identity and covenant at maximum clarity.' }
  if (phase < 0.6875)  return { phase, name: 'Waning Gibbous',  icon: '🌖', illumination, amplifiedFaces: [7,8],  desc: 'Archive and signal intelligence gather the harvest.' }
  if (phase < 0.8125)  return { phase, name: 'Last Quarter',    icon: '🌗', illumination, amplifiedFaces: [1,7],  desc: 'Root and archive align for deep clearing.' }
  return                        { phase, name: 'Waning Crescent', icon: '🌘', illumination, amplifiedFaces: [6,13], desc: 'Temporal seal and living larder close the cycle.' }
}
function getArkDate(date = new Date()) {
  const D = Math.floor((date.getTime() - new Date('2026-03-31T00:00:00Z').getTime()) / 864e5)
  return { arkYear: D < 0 ? 0 : Math.floor(D / 365) + 1, dayInYear: D < 0 ? 365 + D : (D % 365) + 1 }
}

// ─── RESONANCE ENGINE ─────────────────────────────────────────────────────────

function scoreScroll(scroll: CodexScroll, face: Face, lunar: LunarPhase): number {
  const cat = deriveCategory(scroll)
  const text = `${scroll.label ?? ''} ${scroll.description ?? ''} ${scroll.preview ?? ''}`.toLowerCase()
  let score = 0
  if (face.categories.includes(cat)) score += 42
  const kwHits = face.keywords.reduce((s, kw) => s + (text.includes(kw) ? 8 : 0), 0)
  score += Math.min(kwHits, 30)
  score += Math.max(0, 12 - (scroll.priority ?? 5) * 1.5)
  if (lunar.amplifiedFaces.includes(face.id)) score += 12
  return Math.min(Math.round(score), 100)
}
function buildArcs(scored: { scroll: CodexScroll; score: number }[], face: Face) {
  const h = scored.filter(s => s.score >= 50)
  const m = scored.filter(s => s.score >= 25 && s.score < 50)
  const l = scored.filter(s => s.score > 0 && s.score < 25)
  return [
    ...(h.length ? [{ label: face.arcName,      tier: 'primary' as const, items: h }] : []),
    ...(m.length ? [{ label: 'Harmonic Echo',   tier: 'echo'    as const, items: m }] : []),
    ...(l.length ? [{ label: 'Field Whisper',   tier: 'whisper' as const, items: l }] : []),
  ]
}

// ─── CRYSTAL POLYGON ─────────────────────────────────────────────────────────

const POLY_SIZE = 420
const CX = POLY_SIZE / 2, CY = POLY_SIZE / 2
const RING_R = 152
const HEX_W = 56, HEX_H = HEX_W * 0.866
const CTR_W = 66, CTR_H = CTR_W * 0.866
// Pairs adjacent on ring: (6,12)(5,11)(4,10)(3,9)(2,8)(1,7)
const RING_ORDER = [6, 12, 5, 11, 4, 10, 3, 9, 2, 8, 1, 7]
const PAIR_IDX: [number, number][] = [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11]]

function hexPts(w: number, h: number, pad = 1.5) {
  return `${w*0.25+pad},${pad} ${w*0.75-pad},${pad} ${w-pad},${h/2} ${w*0.75-pad},${h-pad} ${w*0.25+pad},${h-pad} ${pad},${h/2}`
}
function ringPos(i: number) {
  const a = (i * 30 - 90) * Math.PI / 180
  return { x: CX + RING_R * Math.cos(a) - HEX_W/2, y: CY + RING_R * Math.sin(a) - HEX_H/2,
           cx: CX + RING_R * Math.cos(a), cy: CY + RING_R * Math.sin(a) }
}

interface TooltipState { faceId: number; x: number; y: number }

function HexNode({ face, active, amplified, w, h, onSelect, onHover, onLeave }: {
  face: Face; active: boolean; amplified: boolean; w: number; h: number
  onSelect: () => void; onHover: (e: React.MouseEvent) => void; onLeave: () => void
}) {
  const pts = hexPts(w, h)
  return (
    <motion.button
      onClick={onSelect}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.93 }}
      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', position: 'relative', width: w, height: h, display: 'block' }}
    >
      {/* Lunar pulse ring */}
      {amplified && (
        <motion.svg width={w+12} height={h+12}
          style={{ position: 'absolute', left: -6, top: -6, pointerEvents: 'none' }}
          animate={{ opacity: [0.1, 0.5, 0.1] }} transition={{ duration: 2.2, repeat: Infinity }}>
          <polygon points={hexPts(w+12, h+12)} fill="none" stroke={face.color} strokeWidth={1.2} />
        </motion.svg>
      )}
      {/* Active glow */}
      {active && (
        <motion.div style={{ position: 'absolute', inset: -14, borderRadius: '50%',
          background: `radial-gradient(ellipse, ${face.color}20 0%, transparent 65%)`, pointerEvents: 'none' }}
          animate={{ opacity: [0.4, 0.9, 0.4] }} transition={{ duration: 2.8, repeat: Infinity }} />
      )}
      {/* SVG hex shape */}
      <svg width={w} height={h} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}>
        <defs>
          <filter id={`glow-${face.id}`}>
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {/* Outer hex */}
        <polygon points={pts}
          fill={active ? `${face.color}18` : 'rgba(4,6,14,0.78)'}
          stroke={active ? face.color : `${face.color}30`}
          strokeWidth={active ? 1.5 : 0.8}
          filter={active ? `url(#glow-${face.id})` : undefined} />
        {/* Inner subtle second ring */}
        {active && <polygon points={hexPts(w, h, 5)} fill="none" stroke={`${face.color}25`} strokeWidth={0.6} />}
      </svg>
      {/* Content */}
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 3, pointerEvents: 'none' }}>
        <FaceSigil faceId={face.id} size={w * 0.4} color={active ? face.color : `${face.color}80`} />
        <span style={{ fontFamily: 'sans-serif', fontSize: w * 0.115, letterSpacing: '0.1em',
          textTransform: 'uppercase' as const, color: active ? face.color : `${face.color}65`,
          lineHeight: 1, fontWeight: active ? 600 : 400 }}>
          {face.name.slice(0, 6)}
        </span>
      </div>
    </motion.button>
  )
}

function CrystalPolygon({ lunar, activeFaceId, onSelectFace }: {
  lunar: LunarPhase; activeFaceId: number | null; onSelectFace: (id: number | null) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  useEffect(() => {
    const update = () => {
      if (!containerRef.current) return
      const w = containerRef.current.offsetWidth
      setScale(Math.min(1, w / POLY_SIZE))
    }
    update()
    const ro = new ResizeObserver(update)
    if (containerRef.current) ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  const activeFace = activeFaceId !== null ? FACES.find(f => f.id === activeFaceId) ?? null : null
  const activeRingIdx = activeFaceId !== null ? RING_ORDER.indexOf(activeFaceId) : -1
  const activePos = activeRingIdx >= 0 ? ringPos(activeRingIdx) : null

  const tooltipFace = tooltip ? FACES.find(f => f.id === tooltip.faceId) : null

  return (
    <div ref={containerRef} style={{ width: '100%', position: 'relative', overflow: 'visible' }}>
      {/* Scaled polygon container */}
      <div style={{
        width: POLY_SIZE, height: POLY_SIZE,
        transform: `scale(${scale})`, transformOrigin: 'top left',
        marginBottom: scale < 1 ? POLY_SIZE * (scale - 1) : 0,
      }}>
        {/* SVG structure */}
        <svg width={POLY_SIZE} height={POLY_SIZE}
          style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}>
          {/* Guide circle */}
          <circle cx={CX} cy={CY} r={RING_R} fill="none"
            stroke="rgba(201,168,76,0.07)" strokeWidth={0.75} strokeDasharray="3 10" />
          {/* Inner reference */}
          <circle cx={CX} cy={CY} r={RING_R * 0.44} fill="none"
            stroke="rgba(201,168,76,0.04)" strokeWidth={0.5} />

          {/* Adjacent ring edges */}
          {RING_ORDER.map((faceId, i) => {
            const p1 = ringPos(i), p2 = ringPos((i + 1) % 12)
            const active = activeFaceId !== null && (RING_ORDER[i] === activeFaceId || RING_ORDER[(i+1)%12] === activeFaceId)
            return <line key={`re-${i}`} x1={p1.cx} y1={p1.cy} x2={p2.cx} y2={p2.cy}
              stroke={active ? 'rgba(201,168,76,0.15)' : 'rgba(201,168,76,0.05)'}
              strokeWidth={active ? 0.8 : 0.4} />
          })}

          {/* Pair connectors */}
          {PAIR_IDX.map(([a, b]) => {
            const pa = ringPos(a), pb = ringPos(b)
            const fa = FACES.find(f => f.id === RING_ORDER[a])!
            const isActive = activeFaceId === fa.id || activeFaceId === FACES.find(f => f.id === RING_ORDER[b])?.id
            return <line key={`pair-${a}`} x1={pa.cx} y1={pa.cy} x2={pb.cx} y2={pb.cy}
              stroke={isActive ? `${fa.color}45` : 'rgba(255,255,255,0.03)'}
              strokeWidth={isActive ? 1 : 0.5} strokeDasharray={isActive ? '3 4' : undefined} />
          })}

          {/* Active beam center → face */}
          <AnimatePresence>
            {activePos && activeFace && (
              <motion.line key={`beam-${activeFaceId}`}
                x1={CX} y1={CY} x2={activePos.cx} y2={activePos.cy}
                stroke={activeFace.color} strokeWidth={1} strokeDasharray="5 4"
                initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }} />
            )}
          </AnimatePresence>

          {/* Center ring for face 13 active */}
          {activeFaceId === 13 && (
            <motion.circle cx={CX} cy={CY} r={RING_R * 0.68} fill="none"
              stroke={`${FACES[12].color}30`} strokeWidth={0.75} strokeDasharray="6 5"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} />
          )}

          {/* Active face index label */}
          {activeFace && activeRingIdx >= 0 && (() => {
            const a = (activeRingIdx * 30 - 90) * Math.PI / 180
            const r = RING_R + 40
            return <motion.text x={CX + r * Math.cos(a)} y={CY + r * Math.sin(a) + 3}
              textAnchor="middle" fill={activeFace.color} fontSize={7}
              fontFamily="sans-serif" letterSpacing={1.5}
              initial={{ opacity: 0 }} animate={{ opacity: 0.7 }}>
              F{String(activeFace.id).padStart(2,'0')}
            </motion.text>
          })()}

          {/* Idle prompt */}
          {activeFaceId === null && (
            <motion.text x={CX} y={CY + CTR_H/2 + 22} textAnchor="middle"
              fill="rgba(201,168,76,0.22)" fontSize={8} fontFamily="sans-serif" letterSpacing={3.5}
              animate={{ opacity: [0.25, 0.55, 0.25] }} transition={{ duration: 4, repeat: Infinity }}>
              SELECT A FACE
            </motion.text>
          )}
        </svg>

        {/* Ring face chips */}
        {RING_ORDER.map((faceId, i) => {
          const face = FACES.find(f => f.id === faceId)!
          const pos = ringPos(i)
          const isActive = activeFaceId === faceId
          const isAmplified = lunar.amplifiedFaces.includes(faceId) && !isActive
          return (
            <motion.div key={faceId}
              style={{ position: 'absolute', left: pos.x, top: pos.y, zIndex: isActive ? 3 : 1 }}
              animate={{ opacity: activeFaceId !== null && !isActive ? 0.48 : 1, scale: isActive ? 1.07 : 1 }}
              transition={{ duration: 0.22 }}>
              <HexNode face={face} active={isActive} amplified={isAmplified}
                w={HEX_W} h={HEX_H}
                onSelect={() => onSelectFace(isActive ? null : faceId)}
                onHover={(e) => setTooltip({ faceId, x: pos.cx, y: pos.y })}
                onLeave={() => setTooltip(null)} />
            </motion.div>
          )
        })}

        {/* Center Face 13 */}
        <motion.div style={{ position: 'absolute', left: CX - CTR_W/2, top: CY - CTR_H/2, zIndex: activeFaceId === 13 ? 3 : 2 }}
          animate={{ opacity: activeFaceId !== null && activeFaceId !== 13 ? 0.55 : 1, scale: activeFaceId === 13 ? 1.07 : 1 }}
          transition={{ duration: 0.22 }}>
          <HexNode face={FACES[12]} active={activeFaceId === 13} amplified={lunar.amplifiedFaces.includes(13)}
            w={CTR_W} h={CTR_H}
            onSelect={() => onSelectFace(activeFaceId === 13 ? null : 13)}
            onHover={(e) => setTooltip({ faceId: 13, x: CX, y: CY - CTR_H/2 })}
            onLeave={() => setTooltip(null)} />
        </motion.div>

        {/* Tooltip */}
        <AnimatePresence>
          {tooltip && tooltipFace && (
            <motion.div key={tooltip.faceId}
              initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              style={{
                position: 'absolute',
                left: Math.min(tooltip.x - 90, POLY_SIZE - 195),
                top: Math.max(tooltip.y - 112, 0),
                width: 188, zIndex: 10, pointerEvents: 'none',
                background: 'rgba(4,6,14,0.92)',
                border: `1px solid ${tooltipFace.color}35`,
                borderRadius: 10, padding: '10px 12px',
                backdropFilter: 'blur(16px)',
                boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px ${tooltipFace.color}12`,
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <FaceSigil faceId={tooltipFace.id} size={14} color={tooltipFace.color} />
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${tooltipFace.color}90`, margin: 0 }}>
                    Face {String(tooltipFace.id).padStart(2,'0')} · {tooltipFace.layer}
                  </p>
                  <p style={{ fontFamily: 'serif', fontSize: 12, color: tooltipFace.color, margin: 0, letterSpacing: '0.03em' }}>
                    {tooltipFace.name}
                    <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.35)', fontWeight: 400, marginLeft: 5 }}>
                      {tooltipFace.expression}
                    </span>
                  </p>
                </div>
              </div>
              <p style={{ fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.65, color: 'rgba(232,232,232,0.45)', margin: 0 }}>
                {tooltipFace.desc}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ─── FACE DETAIL PANEL ────────────────────────────────────────────────────────

function FaceDetail({ face, lunar, count }: { face: Face; lunar: LunarPhase; count: number }) {
  const amp = lunar.amplifiedFaces.includes(face.id)
  return (
    <motion.div key={face.id}
      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      style={{ padding: '18px 20px', background: `linear-gradient(135deg, ${face.color}08, transparent 55%)`,
        border: `1px solid ${face.color}28`, borderRadius: 16 }}>
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{ width: 42, height: 42, borderRadius: '50%', border: `1px solid ${face.color}35`,
          background: `${face.color}0e`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <FaceSigil faceId={face.id} size={20} color={face.color} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase',
              color: `${face.color}80`, padding: '2px 7px', background: `${face.color}0e`, border: `1px solid ${face.color}22`, borderRadius: 4 }}>
              Face {String(face.id).padStart(2,'0')} · {face.layer}
            </span>
            {amp && (
              <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.8, repeat: Infinity }}
                style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase',
                  color: '#B08DE8', padding: '2px 7px', background: 'rgba(176,141,232,0.08)', border: '1px solid rgba(176,141,232,0.22)', borderRadius: 4 }}>
                {lunar.icon} Lunar Active
              </motion.span>
            )}
          </div>
          <h3 style={{ fontFamily: 'serif', fontSize: 19, color: face.color, margin: '0 0 4px', letterSpacing: '0.04em' }}>
            {face.name}
            <span style={{ fontFamily: 'sans-serif', color: 'rgba(232,232,232,0.28)', fontSize: 12, fontWeight: 400, marginLeft: 8 }}>
              {face.expression}
            </span>
          </h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.72, color: 'rgba(232,232,232,0.5)', margin: '0 0 11px' }}>{face.desc}</p>
          <div style={{ borderLeft: `2px solid ${face.color}30`, paddingLeft: 12, marginBottom: 11 }}>
            <p style={{ fontFamily: 'serif', fontSize: 12.5, lineHeight: 1.8, color: 'rgba(232,232,232,0.36)', margin: 0, fontStyle: 'italic' }}>{face.scroll}</p>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: face.color }}>{count}</span>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8.5, color: 'rgba(232,232,232,0.2)', letterSpacing: '0.14em' }}>
              scrolls in resonance field · ordered by coherence
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ─── SCROLL CARDS ─────────────────────────────────────────────────────────────

function ScrollCard({ scroll, score, faceColor, idx }: {
  scroll: CodexScroll; score: number; faceColor: string; idx: number
}) {
  const [open, setOpen] = useState(false)
  const cat = deriveCategory(scroll)
  const meta = CATEGORY_META[cat] ?? { label: cat, color: '#888', glyph: '·' }
  const isLive = !scroll.error && scroll.chars > 0
  const sizeLabel = scroll.chars >= 1000 ? `${(scroll.chars/1000).toFixed(1)}k` : `${scroll.chars}`

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(idx * 0.032, 0.36), duration: 0.26 }}
      style={{ border: `1px solid ${faceColor}22`, background: `${faceColor}03`, borderRadius: 11, overflow: 'hidden' }}>

      {/* Header */}
      <div onClick={() => setOpen(o => !o)}
        style={{ padding: '12px 15px', cursor: 'pointer', display: 'flex', gap: 11, alignItems: 'flex-start' }}>

        {/* Status pulse */}
        <motion.div
          animate={isLive ? { opacity: [0.3, 1, 0.3] } : {}}
          transition={{ duration: 2.8, repeat: Infinity }}
          style={{ width: 6, height: 6, borderRadius: '50%', flexShrink: 0, marginTop: 7,
            background: isLive ? faceColor : '#ef6c6c',
            boxShadow: isLive ? `0 0 5px ${faceColor}50` : 'none' }} />

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Category + size strip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.15em',
              textTransform: 'uppercase', color: meta.color, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11, lineHeight: 1 }}>{meta.glyph}</span>
              {meta.label}
            </span>
            <span style={{ color: COLORS.dim, fontSize: 7 }}>·</span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, color: COLORS.dim }}>{sizeLabel}c</span>
            {scroll.source && (
              <><span style={{ color: COLORS.dim, fontSize: 7 }}>·</span>
              <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: COLORS.dim }}>{scroll.source}</span></>
            )}
          </div>

          {/* Title */}
          <p style={{ fontFamily: 'serif', fontSize: 14.5, color: '#DCDCE8', margin: '0 0 7px', lineHeight: 1.38, letterSpacing: '0.01em' }}>
            {scroll.label}
          </p>

          {/* Preview (collapsed) */}
          {!open && scroll.preview && (
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.muted, margin: '0 0 7px', lineHeight: 1.65,
              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>
              {scroll.preview}
            </p>
          )}

          {/* Resonance bar */}
          {score > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <div style={{ flex: 1, height: 1.5, background: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
                <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }}
                  transition={{ duration: 0.75, ease: 'easeOut', delay: 0.1 }}
                  style={{ height: '100%', background: `linear-gradient(90deg, ${faceColor}45, ${faceColor})`, borderRadius: 1 }} />
              </div>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, color: `${faceColor}70`, flexShrink: 0 }}>{score}</span>
            </div>
          )}
        </div>

        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.18 }}
          style={{ color: COLORS.dim, flexShrink: 0, marginTop: 4 }}>
          <ChevronDown size={13} />
        </motion.div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.26 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '13px 17px', borderTop: `1px solid ${faceColor}12` }}>
              {scroll.content ? <MarkdownViewer content={scroll.content} />
                : scroll.preview ? <MarkdownViewer content={scroll.preview} />
                : <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted }}>No content available.</p>}
              {scroll.description && (
                <div style={{ marginTop: 13, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.2em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 4px' }}>Source Path</p>
                  <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: COLORS.muted, margin: 0 }}>{scroll.description}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ArcDivider({ label, tier, color }: { label: string; tier: string; color: string }) {
  const a = tier === 'primary' ? '55' : tier === 'echo' ? '32' : '1e'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 11 }}>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${color}${a}, transparent)` }} />
      <span style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.28em', textTransform: 'uppercase',
        color: `${color}${tier === 'primary' ? '90' : tier === 'echo' ? '58' : '38'}`, whiteSpace: 'nowrap', flexShrink: 0 }}>
        {tier === 'primary' ? '◆' : tier === 'echo' ? '◇' : '·'} {label}
      </span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${color}${a})` }} />
    </div>
  )
}

// ─── COMPACT OPEN LOOPS ───────────────────────────────────────────────────────

function CompactLoopsPanel() {
  const [open, setOpen] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const { data, isLoading, refetch, isFetching } = useQuery<OpenLoopsResponse>({
    queryKey: ['open-loops-nexus'], queryFn: api.openLoops, refetchInterval: 60_000,
  })
  const LC: Record<string, string> = { critical: '#EF4444', high: '#F97316', active: '#EAB308', dormant: '#3B82F6', closed: '#10B981' }
  return (
    <div style={{ border: '1px solid rgba(239,68,68,0.13)', borderRadius: 14, overflow: 'hidden', background: 'rgba(239,68,68,0.02)' }}>
      <div onClick={() => setOpen(o => !o)}
        style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 15px', cursor: 'pointer',
          borderBottom: open ? '1px solid rgba(239,68,68,0.08)' : 'none' }}>
        <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2, repeat: Infinity }}
          style={{ color: '#EF4444', fontSize: 10 }}>⚡</motion.span>
        <div style={{ flex: 1 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.55)', margin: 0 }}>Open Loops · Live</p>
          {data && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '2px 0 0' }}>{data.total} active threads</p>}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={e => { e.stopPropagation(); refetch() }} disabled={isFetching}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.dim, padding: 0 }}>
            <RefreshCw size={10} className={isFetching ? 'animate-spin' : ''} />
          </button>
          {open ? <ChevronUp size={12} color={COLORS.dim} /> : <ChevronDown size={12} color={COLORS.dim} />}
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '11px 13px', maxHeight: 320, overflowY: 'auto' }}>
              {isLoading && <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.dim, textAlign: 'center', margin: '8px 0' }}>Parsing loops…</p>}
              {data?.groups?.map(group => (
                <div key={group.level} style={{ marginBottom: 11 }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: LC[group.level] ?? COLORS.dim, margin: '0 0 5px' }}>
                    {group.section_title} ({group.loops.length})
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {group.loops.map(loop => {
                      const key = `${group.level}:${loop.id}`
                      const isOpen = expanded === key
                      return (
                        <div key={loop.id} onClick={() => setExpanded(isOpen ? null : key)}
                          style={{ padding: '6px 9px', background: `${LC[group.level] ?? '#888'}08`,
                            border: `1px solid ${LC[group.level] ?? '#888'}18`, borderRadius: 7, cursor: 'pointer' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, color: LC[group.level] ?? COLORS.dim, flexShrink: 0 }}>#{loop.id}</span>
                            <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.text, flex: 1, lineHeight: 1.32 }}>{loop.name}</span>
                            <span style={{ color: COLORS.dim, fontSize: 8 }}>{isOpen ? '▲' : '▼'}</span>
                          </div>
                          {isOpen && (loop.next_action || loop.status) && (
                            <div style={{ marginTop: 5, paddingTop: 5, borderTop: `1px solid ${LC[group.level] ?? '#888'}18` }}>
                              {loop.status && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '0 0 2px' }}>{loop.status}</p>}
                              {loop.next_action && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.dim, margin: 0 }}>{loop.next_action}</p>}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
              {data?.groups?.length === 0 && <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.dim, textAlign: 'center', margin: '8px 0' }}>No open loops.</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function NexusSpiralCodex() {
  const lunar    = useMemo(() => getLunarPhase(), [])
  const arkDate  = useMemo(() => getArkDate(), [])
  const [activeFaceId, setActiveFaceId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')

  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ['codex-nexus'], queryFn: api.codex,
    refetchInterval: 5 * 60_000, staleTime: 2 * 60_000,
  })

  const activeFace = useMemo(() => FACES.find(f => f.id === activeFaceId) ?? null, [activeFaceId])
  const allScrolls: CodexScroll[] = useMemo(() => data?.scrolls ? Object.values(data.scrolls) : [], [data])

  const { scoredScrolls, meaningArcs } = useMemo(() => {
    let scrolls = allScrolls
    if (search.trim()) {
      const q = search.toLowerCase()
      scrolls = scrolls.filter(s =>
        (s.label ?? '').toLowerCase().includes(q) ||
        (s.description ?? '').toLowerCase().includes(q) ||
        (s.preview ?? '').toLowerCase().includes(q)
      )
    }
    if (categoryFilter) {
      scrolls = scrolls.filter(s => deriveCategory(s) === categoryFilter)
    }
    if (!activeFace) {
      return {
        scoredScrolls: scrolls.map(s => ({ scroll: s, score: 0 }))
          .sort((a, b) => (a.scroll.priority ?? 99) - (b.scroll.priority ?? 99)),
        meaningArcs: [],
      }
    }
    const scored = scrolls
      .map(s => ({ scroll: s, score: scoreScroll(s, activeFace, lunar) }))
      .filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
    return { scoredScrolls: scored, meaningArcs: buildArcs(scored, activeFace) }
  }, [allScrolls, activeFace, lunar, search, categoryFilter])

  if (isLoading && !data) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
        style={{ width: 26, height: 26, borderRadius: '50%', border: '2px solid rgba(201,168,76,0.15)', borderTopColor: '#C9A84C' }} />
    </div>
  )
  if (error) return <ErrorBox>Corpus sync failed: {(error as Error).message}</ErrorBox>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* Status bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 11px',
            background: 'rgba(176,141,232,0.05)', border: '1px solid rgba(176,141,232,0.13)', borderRadius: 8 }}>
            <span style={{ fontSize: 13 }}>{lunar.icon}</span>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.55)', margin: 0 }}>{lunar.name}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.32)', margin: '1px 0 0' }}>{lunar.desc}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 11px',
            background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.11)', borderRadius: 8 }}>
            <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 3, repeat: Infinity }}
              style={{ color: '#C9A84C', fontSize: 9 }}>✦</motion.span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9.5, color: 'rgba(201,168,76,0.6)', letterSpacing: '0.14em' }}>
              ARK Y{arkDate.arkYear} · D{arkDate.dayInYear}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {activeFace && (
            <button onClick={() => setActiveFaceId(null)}
              style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.15em', textTransform: 'uppercase',
                color: 'rgba(239,108,108,0.55)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              ✕ Clear
            </button>
          )}
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: COLORS.dim }}>
            {data?.live_docs ?? 0} scrolls{activeFace ? ` · ${scoredScrolls.length} resonant` : ''}
          </span>
          <button onClick={() => refetch()} disabled={isFetching}
            style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 9px',
              border: '1px solid rgba(0,212,170,0.18)', borderRadius: 7, background: 'rgba(0,212,170,0.04)',
              color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: isFetching ? 'wait' : 'pointer' }}>
            <RefreshCw size={9} className={isFetching ? 'animate-spin' : ''} /> Sync
          </button>
        </div>
      </div>

      {/* Section header */}
      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.35)', margin: '0 0 3px' }}>
          Universal Echofield Recursion Protocol
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: 20, color: '#DCDCE8', margin: 0, letterSpacing: '0.04em' }}>
          Crystal Matrix Spine
          {activeFace && <span style={{ fontFamily: 'sans-serif', fontSize: 12, color: activeFace.color, marginLeft: 10, fontWeight: 400 }}>
            · {activeFace.expression}
          </span>}
        </h2>
      </div>

      {/* Crystal Polygon (mobile-responsive) */}
      <CrystalPolygon lunar={lunar} activeFaceId={activeFaceId} onSelectFace={setActiveFaceId} />

      {/* Face detail */}
      <AnimatePresence mode="wait">
        {activeFace && <FaceDetail key={activeFace.id} face={activeFace} lunar={lunar} count={scoredScrolls.length} />}
      </AnimatePresence>

      {/* Codex divider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.15), transparent)' }} />
        <span style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.32em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.16)', whiteSpace: 'nowrap' }}>
          Spiral Codex Feed
        </span>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.15), transparent)' }} />
      </div>

      {/* Category filter chips */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          onClick={() => setCategoryFilter('')}
          style={{
            flexShrink: 0, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.14em',
            textTransform: 'uppercase', cursor: 'pointer',
            padding: '4px 10px', borderRadius: 5,
            background: !categoryFilter ? 'rgba(201,168,76,0.12)' : 'transparent',
            border: !categoryFilter ? '1px solid rgba(201,168,76,0.4)' : '1px solid rgba(255,255,255,0.08)',
            color: !categoryFilter ? '#C9A84C' : COLORS.dim,
            display: 'flex', alignItems: 'center', gap: 4,
          }}>
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10 }}>⟁</span>
          All
        </button>
        {Object.entries(CATEGORY_META).map(([key, m]) => {
          const active = categoryFilter === key
          return (
            <button key={key}
              onClick={() => setCategoryFilter(active ? '' : key)}
              style={{
                flexShrink: 0, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.14em',
                textTransform: 'uppercase', cursor: 'pointer',
                padding: '4px 10px', borderRadius: 5,
                background: active ? `${m.color}18` : 'transparent',
                border: active ? `1px solid ${m.color}55` : `1px solid ${m.color}18`,
                color: active ? m.color : `${m.color}70`,
                display: 'flex', alignItems: 'center', gap: 4,
                transition: 'all 0.15s',
              }}>
              <span style={{ fontSize: 10, fontFamily: 'ui-monospace, monospace' }}>{m.glyph}</span>
              {m.label}
            </button>
          )
        })}
        {categoryFilter && (
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: COLORS.dim, marginLeft: 4 }}>
            {scoredScrolls.length} scrolls
          </span>
        )}
      </div>

      {/* Search */}
      <div style={{ position: 'relative' }}>
        <Search size={11} style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: COLORS.dim, pointerEvents: 'none' }} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search the scrolls…"
          style={{ width: '100%', paddingLeft: 32, paddingRight: search ? 32 : 13, paddingTop: 8, paddingBottom: 8,
            boxSizing: 'border-box', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 9, color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }} />
        {search && (
          <button onClick={() => setSearch('')}
            style={{ position: 'absolute', right: 11, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: COLORS.dim, cursor: 'pointer', padding: 0 }}>
            <X size={11} />
          </button>
        )}
      </div>

      {/* Feed */}
      {activeFace && meaningArcs.length > 0 ? (
        <div>
          {meaningArcs.map((arc, ai) => {
            const startIdx = meaningArcs.slice(0, ai).reduce((s, a) => s + a.items.length, 0)
            return (
              <div key={arc.label} style={{ marginBottom: 22 }}>
                <ArcDivider label={arc.label} tier={arc.tier} color={activeFace.color} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  {arc.items.map(({ scroll, score }, i) => (
                    <ScrollCard key={scroll.id} scroll={scroll} score={score} faceColor={activeFace.color} idx={startIdx + i} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {scoredScrolls.length === 0
            ? <Empty>{search ? 'No scrolls match this query.' : 'Corpus is empty.'}</Empty>
            : scoredScrolls.map(({ scroll, score }, i) => (
                <ScrollCard key={scroll.id} scroll={scroll} score={score} faceColor='#C9A84C' idx={i} />
              ))
          }
        </div>
      )}

      {/* Open Loops */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 11 }}>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.15), transparent)' }} />
          <span style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.32em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.3)', whiteSpace: 'nowrap' }}>
            Open Loops
          </span>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.15), transparent)' }} />
        </div>
        <CompactLoopsPanel />
      </div>

      {scoredScrolls.length > 0 && (
        <motion.p animate={{ opacity: [0.12, 0.35, 0.12] }} transition={{ duration: 6, repeat: Infinity }}
          style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.5em', textTransform: 'uppercase', color: COLORS.dim, margin: '2px 0 0' }}>
          ⟐ End of Transmission · {scoredScrolls.length} scrolls ⟐
        </motion.p>
      )}
    </div>
  )
}
