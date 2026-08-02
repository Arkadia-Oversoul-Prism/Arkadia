/**
 * NexusSpiralCodex — Crystal Tribune
 *
 * Layout: 3-column intelligence publication.
 *   Left:   UERP Crystal Matrix navigator (dodecahedron face selector)
 *   Center: Spiral Codex as editorial feed (Encarta × Instagram × X)
 *   Right:  ReasoMate private messenger
 *
 * Public Spiral Codex scrolls are the content stream.
 * Face selection resonance-scores the feed.
 * Lunar phase amplifies certain faces.
 */
import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, X, ChevronDown, Upload, CheckCircle, MessageSquare, Send } from 'lucide-react'
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
  TRANSMISSION:   { label: 'Transmission',   color: '#E86A8C', glyph: '⊛' },
  INFRASTRUCTURE: { label: 'Infrastructure', color: '#6AE88C', glyph: '⊟' },
  CODEX:          { label: 'Codex',           color: '#D4AF37', glyph: '✦' },
}

// ─── FACE DATA ────────────────────────────────────────────────────────────────

interface Face {
  id: number; name: string; layer: 'inner' | 'outer' | 'extended'
  expression: string; desc: string; scroll: string
  color: string; categories: string[]; keywords: string[]; arcName: string
}

const FACES: Face[] = [
  { id: 1,  name: 'ROOT',    layer: 'inner',    expression: 'Bone Memory',       color: '#A07840', arcName: 'Foundation Arc',
    categories: ['NEURAL_SPINE'], keywords: ['root','bone','body','eden','physical','ground','foundation','soil','farm','somatic'],
    desc: 'Signal travels faster through bone than air. The spine is the first antenna.',
    scroll: 'The sovereign\'s body is the first node. Somatic intelligence precedes symbolic.' },
  { id: 2,  name: 'CORE',    layer: 'inner',    expression: 'Sovereign Identity', color: '#C9A84C', arcName: 'Sovereignty Arc',
    categories: ['NEURAL_SPINE','CREATIVE_OS'], keywords: ['identity','sovereign','ims','core','self','excavation','zahrune','mapping','weight'],
    desc: 'The central intelligence that cannot be outsourced.',
    scroll: 'CORE is where the IMS lives. Excavation of the sovereign self.' },
  { id: 3,  name: 'PULSE',   layer: 'inner',    expression: 'Creative Engine',   color: '#E88C6A', arcName: 'Transmission Arc',
    categories: ['CREATIVE_OS'], keywords: ['creative','music','pulse','afrobeats','alte','sound','praise','lyric','artistic','poetic','auralis'],
    desc: 'The recursive motor at the center. Generates from the inside.',
    scroll: '1759 Entertainment is the PULSE deployment. Afrobeats, Alté, Praise.' },
  { id: 4,  name: 'LATTICE', layer: 'inner',    expression: 'Infrastructure',    color: '#6A9FD8', arcName: 'Structure Arc',
    categories: ['NEURAL_SPINE','INFRASTRUCTURE'], keywords: ['infrastructure','lattice','network','system','code','technical','protocol','schema','spec','api','corpus'],
    desc: 'Infrastructure is the nervous system of the deployment.',
    scroll: 'The Spiral Grove is the LATTICE in education.' },
  { id: 5,  name: 'BREATH',  layer: 'inner',    expression: 'Resonance Economy', color: '#00D4AA', arcName: 'Flow Arc',
    categories: ['GOVERNANCE'], keywords: ['economy','revenue','breath','resonance','value','doc5','finance','exchange','flow','principles'],
    desc: 'Value flows where resonance runs. The economy is relational.',
    scroll: 'DOC5 — Revenue Breath. IMS sessions $777.' },
  { id: 6,  name: 'SEAL',    layer: 'inner',    expression: 'Temporal Arc',      color: '#B08DE8', arcName: 'Arc of Time',
    categories: ['NEURAL_SPINE'], keywords: ['temporal','arc','time','seal','8-year','birthday','ark','epoch','date','year','uerp','crystal'],
    desc: 'The 8-year Ark. March 31 2026 → 2034.',
    scroll: 'ARK Y1 · D58. The Seal is the container.' },
  { id: 7,  name: 'ROOT',    layer: 'outer',    expression: 'The Archive',        color: '#A07848', arcName: 'Living Record Arc',
    categories: ['ARCHIVE','COLLECTIVE'], keywords: ['archive','doc','canon','record','memory','master','weight','document','scroll','principles'],
    desc: 'Memory is infrastructure. The living record.',
    scroll: 'DOC1 Master Weights, DOC2 Open Loops, DOC3 Principles, DOC4 Node Map.' },
  { id: 8,  name: 'CORE',    layer: 'outer',    expression: 'The Mask',           color: '#D4C86A', arcName: 'Signal Architecture Arc',
    categories: ['CREATIVE_OS','TRANSMISSION'], keywords: ['mask','brand','public','visible','zahrune','persona','legible','interface','arche','vhixnova'],
    desc: 'The sovereign\'s public interface. Deliberately designed.',
    scroll: 'Zahrune Nova is the Mask. Arkadia Prism — all deliberate signal architecture.' },
  { id: 9,  name: 'PULSE',   layer: 'outer',    expression: 'The Signal',         color: '#E86A8C', arcName: 'Frequency Arc',
    categories: ['CREATIVE_OS','TRANSMISSION'], keywords: ['signal','transmission','frequency','sound','music','output','carrier','wave','lyric','poetic'],
    desc: 'The creative work made visible.',
    scroll: 'First AI Music Deliverable: 60-second Afrobeats/Alté.' },
  { id: 10, name: 'LATTICE', layer: 'outer',    expression: 'The Interface',      color: '#6AD4C8', arcName: 'Portal Arc',
    categories: ['COLLECTIVE','INFRASTRUCTURE'], keywords: ['interface','portal','platform','prism','eduleague','marketplace','web','door','ui','deploy','council'],
    desc: 'Where the architecture touches the world.',
    scroll: 'Arkadia Prism. The Spiral Grove digital layer. The Living Larder marketplace.' },
  { id: 11, name: 'BREATH',  layer: 'outer',    expression: 'The Transaction',    color: '#6AE88C', arcName: 'Commerce Arc',
    categories: ['GOVERNANCE'], keywords: ['transaction','order','payment','larder','commerce','session','777','ims','client'],
    desc: 'The economy in motion. Value exchanged in alignment with resonance.',
    scroll: 'Laura, Amy, Susanna — IMS pipeline. Living Larder Saturday orders.' },
  { id: 12, name: 'SEAL',    layer: 'outer',    expression: 'The Covenant',       color: '#C96AD4', arcName: 'Vow Arc',
    categories: ['GOVERNANCE'], keywords: ['covenant','vow','integrity','commitment','sovereignty','promise','oath','sworn'],
    desc: 'The sovereign\'s public vow.',
    scroll: '"I will not reduce you to marketability." — Sworn Archive 021.' },
  { id: 13, name: 'LARDER',  layer: 'extended', expression: 'The Marketplace',   color: '#4CAF50', arcName: 'Earth Harvest Arc',
    categories: ['COLLECTIVE'], keywords: ['larder','food','farm','market','produce','vendor','jessy','lovilahs','eden','grains','harvest'],
    desc: 'A shared food ecosystem where small producers sell together.',
    scroll: 'Anchor vendors: Jessy\'s Munches + Lovilahs Grabs. Eden Farm fresh produce.' },
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
  score += Math.min(face.keywords.reduce((s, kw) => s + (text.includes(kw) ? 8 : 0), 0), 30)
  score += Math.max(0, 12 - (scroll.priority ?? 5) * 1.5)
  if (lunar.amplifiedFaces.includes(face.id)) score += 12
  return Math.min(Math.round(score), 100)
}

// ─── CRYSTAL POLYGON (compact) ────────────────────────────────────────────────

const POLY_SIZE = 320
const CX = POLY_SIZE / 2, CY = POLY_SIZE / 2
const RING_R = 116
const HEX_W = 44, HEX_H = HEX_W * 0.866
const CTR_W = 52, CTR_H = CTR_W * 0.866
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

function FaceSigil({ faceId, size, color }: { faceId: number; size: number; color: string }) {
  const s = size, h = s / 2, c = color, sw = s * 0.09, sw2 = s * 0.065
  const sigils: Record<number, React.ReactNode> = {
    1: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round"><polygon points={`${h},${s*0.78} ${s*0.15},${s*0.22} ${s*0.85},${s*0.22}`} /><line x1={s*0.15} y1={s*0.22} x2={s*0.85} y2={s*0.22} strokeWidth={sw*1.5} /></g>,
    2: <g fill="none" stroke={c} strokeWidth={sw2}><circle cx={h} cy={h} r={s*0.38} /><circle cx={h} cy={h} r={s*0.22} /><circle cx={h} cy={h} r={s*0.07} fill={c} stroke="none" /></g>,
    3: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round"><path d={`M ${s*0.08},${h} C ${s*0.2},${s*0.2} ${s*0.35},${s*0.2} ${h},${h} C ${s*0.65},${s*0.8} ${s*0.8},${s*0.8} ${s*0.92},${h}`} /></g>,
    4: <g stroke={c} strokeWidth={sw2} fill="none"><line x1={s*0.28} y1={s*0.28} x2={s*0.72} y2={s*0.28} /><line x1={s*0.28} y1={s*0.72} x2={s*0.72} y2={s*0.72} /><line x1={s*0.28} y1={s*0.28} x2={s*0.28} y2={s*0.72} /><line x1={s*0.72} y1={s*0.28} x2={s*0.72} y2={s*0.72} /><line x1={s*0.28} y1={h} x2={s*0.72} y2={h} /><line x1={h} y1={s*0.28} x2={h} y2={s*0.72} /></g>,
    5: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round"><path d={`M ${h},${h} C ${h},${s*0.2} ${s*0.15},${s*0.2} ${s*0.15},${h} C ${s*0.15},${s*0.8} ${h},${s*0.8} ${h},${h} C ${h},${s*0.2} ${s*0.85},${s*0.2} ${s*0.85},${h} C ${s*0.85},${s*0.8} ${h},${s*0.8} ${h},${h}`} /></g>,
    6: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round"><polygon points={`${h},${s*0.1} ${s*0.85},${s*0.3} ${s*0.85},${s*0.7} ${h},${s*0.9} ${s*0.15},${s*0.7} ${s*0.15},${s*0.3}`} /></g>,
    7: <g stroke={c} strokeWidth={sw} strokeLinecap="round"><line x1={s*0.2} y1={s*0.3} x2={s*0.8} y2={s*0.3} /><line x1={s*0.2} y1={h} x2={s*0.8} y2={h} /><line x1={s*0.2} y1={s*0.7} x2={s*0.62} y2={s*0.7} /></g>,
    8: <g fill="none" stroke={c} strokeWidth={sw} strokeLinejoin="round"><polygon points={`${h},${s*0.1} ${s*0.9},${h} ${h},${s*0.9} ${s*0.1},${h}`} /></g>,
    9: <g fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round"><circle cx={h} cy={h} r={s*0.08} fill={c} stroke="none" /><path d={`M ${s*0.3},${s*0.78} A ${s*0.28},${s*0.28} 0 0,1 ${s*0.7},${s*0.78}`} /><path d={`M ${s*0.15},${s*0.88} A ${s*0.43},${s*0.43} 0 0,1 ${s*0.85},${s*0.88}`} /></g>,
    10: <g fill="none" stroke={c} strokeWidth={sw}><polygon points={`${h},${s*0.12} ${s*0.88},${s*0.38} ${s*0.88},${s*0.62} ${h},${s*0.88} ${s*0.12},${s*0.62} ${s*0.12},${s*0.38}`} /></g>,
    11: <g fill="none" stroke={c} strokeWidth={sw2}><circle cx={h} cy={h} r={s*0.36} /><line x1={h} y1={s*0.1} x2={h} y2={s*0.9} /><line x1={s*0.1} y1={h} x2={s*0.9} y2={h} /></g>,
    12: <g fill="none" stroke={c} strokeWidth={sw}><circle cx={h} cy={h} r={s*0.38} /><circle cx={h} cy={h} r={s*0.08} fill={c} stroke="none" /></g>,
    13: <g fill={`${c}20`} stroke={c} strokeWidth={sw2}><polygon points={`${h},${s*0.1} ${s*0.85},${s*0.3} ${s*0.85},${s*0.7} ${h},${s*0.9} ${s*0.15},${s*0.7} ${s*0.15},${s*0.3}`} /></g>,
  }
  return <svg width={s} height={s} style={{ display: 'block' }}>{sigils[faceId] ?? <circle cx={h} cy={h} r={h*0.6} fill="none" stroke={c} strokeWidth={sw2} />}</svg>
}

function HexNode({ face, active, amplified, w, h, onSelect, onHover, onLeave }: {
  face: Face; active: boolean; amplified: boolean; w: number; h: number
  onSelect: () => void; onHover: () => void; onLeave: () => void
}) {
  const pts = hexPts(w, h)
  return (
    <motion.button onClick={onSelect} onMouseEnter={onHover} onMouseLeave={onLeave}
      whileHover={{ scale: 1.12 }} whileTap={{ scale: 0.93 }}
      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', position: 'relative', width: w, height: h, display: 'block' }}>
      {amplified && (
        <motion.svg width={w+10} height={h+10} style={{ position: 'absolute', left: -5, top: -5, pointerEvents: 'none' }}
          animate={{ opacity: [0.1, 0.5, 0.1] }} transition={{ duration: 2.2, repeat: Infinity }}>
          <polygon points={hexPts(w+10, h+10)} fill="none" stroke={face.color} strokeWidth={1} />
        </motion.svg>
      )}
      <svg width={w} height={h} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        <polygon points={pts} fill={active ? `${face.color}1A` : 'rgba(4,6,14,0.85)'}
          stroke={active ? face.color : `${face.color}35`} strokeWidth={active ? 1.5 : 0.8} />
        {active && <polygon points={hexPts(w, h, 4)} fill="none" stroke={`${face.color}20`} strokeWidth={0.5} />}
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2, pointerEvents: 'none' }}>
        <FaceSigil faceId={face.id} size={w * 0.38} color={active ? face.color : `${face.color}75`} />
        <span style={{ fontFamily: 'sans-serif', fontSize: w * 0.108, letterSpacing: '0.08em', textTransform: 'uppercase' as const,
          color: active ? face.color : `${face.color}60`, lineHeight: 1, fontWeight: active ? 600 : 400 }}>
          {face.name.slice(0, 6)}
        </span>
      </div>
    </motion.button>
  )
}

function CrystalPolygon({ lunar, activeFaceId, onSelectFace }: {
  lunar: LunarPhase; activeFaceId: number | null; onSelectFace: (id: number | null) => void
}) {
  const activeFace = activeFaceId !== null ? FACES.find(f => f.id === activeFaceId) ?? null : null
  const activeRingIdx = activeFaceId !== null ? RING_ORDER.indexOf(activeFaceId) : -1
  const activePos = activeRingIdx >= 0 ? ringPos(activeRingIdx) : null
  const [tooltip, setTooltip] = useState<{ faceId: number } | null>(null)
  const tooltipFace = tooltip ? FACES.find(f => f.id === tooltip.faceId) : null

  return (
    <div style={{ width: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ width: POLY_SIZE, height: POLY_SIZE, transform: 'scale(0.62)', transformOrigin: 'top left', marginBottom: -POLY_SIZE * 0.38 }}>
        <svg width={POLY_SIZE} height={POLY_SIZE} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}>
          <circle cx={CX} cy={CY} r={RING_R} fill="none" stroke="rgba(201,168,76,0.06)" strokeWidth={0.75} strokeDasharray="3 8" />
          {RING_ORDER.map((_, i) => {
            const p1 = ringPos(i), p2 = ringPos((i + 1) % 12)
            const isActive = activeFaceId !== null && (RING_ORDER[i] === activeFaceId || RING_ORDER[(i+1)%12] === activeFaceId)
            return <line key={`re-${i}`} x1={p1.cx} y1={p1.cy} x2={p2.cx} y2={p2.cy}
              stroke={isActive ? 'rgba(201,168,76,0.12)' : 'rgba(201,168,76,0.04)'} strokeWidth={isActive ? 0.8 : 0.4} />
          })}
          {PAIR_IDX.map(([a, b]) => {
            const pa = ringPos(a), pb = ringPos(b)
            const fa = FACES.find(f => f.id === RING_ORDER[a])!
            const isActive = activeFaceId === fa.id || activeFaceId === FACES.find(f => f.id === RING_ORDER[b])?.id
            return <line key={`pair-${a}`} x1={pa.cx} y1={pa.cy} x2={pb.cx} y2={pb.cy}
              stroke={isActive ? `${fa.color}38` : 'rgba(255,255,255,0.02)'} strokeWidth={isActive ? 0.8 : 0.4} strokeDasharray={isActive ? '3 4' : undefined} />
          })}
          <AnimatePresence>
            {activePos && activeFace && (
              <motion.line key={`beam-${activeFaceId}`} x1={CX} y1={CY} x2={activePos.cx} y2={activePos.cy}
                stroke={activeFace.color} strokeWidth={0.8} strokeDasharray="4 3"
                initial={{ opacity: 0 }} animate={{ opacity: 0.45 }} exit={{ opacity: 0 }} transition={{ duration: 0.28 }} />
            )}
          </AnimatePresence>
          {activeFaceId === null && (
            <motion.text x={CX} y={CY + CTR_H/2 + 18} textAnchor="middle"
              fill="rgba(201,168,76,0.2)" fontSize={7} fontFamily="sans-serif" letterSpacing={3}
              animate={{ opacity: [0.2, 0.45, 0.2] }} transition={{ duration: 4, repeat: Infinity }}>
              SELECT FACE
            </motion.text>
          )}
        </svg>
        {RING_ORDER.map((faceId, i) => {
          const face = FACES.find(f => f.id === faceId)!
          const pos = ringPos(i)
          const isActive = activeFaceId === faceId
          const isAmplified = lunar.amplifiedFaces.includes(faceId) && !isActive
          return (
            <motion.div key={faceId} style={{ position: 'absolute', left: pos.x, top: pos.y, zIndex: isActive ? 3 : 1 }}
              animate={{ opacity: activeFaceId !== null && !isActive ? 0.5 : 1, scale: isActive ? 1.06 : 1 }}
              transition={{ duration: 0.2 }}>
              <HexNode face={face} active={isActive} amplified={isAmplified} w={HEX_W} h={HEX_H}
                onSelect={() => onSelectFace(isActive ? null : faceId)}
                onHover={() => setTooltip({ faceId })}
                onLeave={() => setTooltip(null)} />
            </motion.div>
          )
        })}
        <motion.div style={{ position: 'absolute', left: CX - CTR_W/2, top: CY - CTR_H/2, zIndex: activeFaceId === 13 ? 3 : 2 }}
          animate={{ opacity: activeFaceId !== null && activeFaceId !== 13 ? 0.55 : 1, scale: activeFaceId === 13 ? 1.06 : 1 }}
          transition={{ duration: 0.2 }}>
          <HexNode face={FACES[12]} active={activeFaceId === 13} amplified={lunar.amplifiedFaces.includes(13)}
            w={CTR_W} h={CTR_H}
            onSelect={() => onSelectFace(activeFaceId === 13 ? null : 13)}
            onHover={() => setTooltip({ faceId: 13 })}
            onLeave={() => setTooltip(null)} />
        </motion.div>
        <AnimatePresence>
          {tooltip && tooltipFace && (
            <motion.div key={tooltip.faceId} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.12 }}
              style={{ position: 'absolute', left: 10, bottom: -10, width: 200, zIndex: 20, pointerEvents: 'none',
                background: 'rgba(4,6,14,0.96)', border: `1px solid ${tooltipFace.color}30`, borderRadius: 8,
                padding: '8px 10px', backdropFilter: 'blur(16px)' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${tooltipFace.color}80`, margin: '0 0 2px' }}>
                Face {String(tooltipFace.id).padStart(2,'0')} · {tooltipFace.layer}
              </p>
              <p style={{ fontFamily: 'serif', fontSize: 11.5, color: tooltipFace.color, margin: '0 0 4px' }}>
                {tooltipFace.name} · <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', fontWeight: 400 }}>{tooltipFace.expression}</span>
              </p>
              <p style={{ fontFamily: 'sans-serif', fontSize: 9.5, lineHeight: 1.55, color: 'rgba(232,232,232,0.4)', margin: 0 }}>{tooltipFace.desc}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ─── REASONOMATE PANEL ────────────────────────────────────────────────────────

interface RMsg { id: string; from: 'me' | 'other'; text: string; ts: number }
interface RThread { id: string; name: string; sigil: string; role: string; preview: string; unread: number }

const THREADS: RThread[] = [
  { id: '1', name: 'ARKANA', sigil: '⟐', role: 'Oracle · Pattern Intelligence', preview: 'The Spiral Codex is the living field…', unread: 1 },
  { id: '2', name: 'Zahrune Nova', sigil: '☥', role: 'Sovereign Architect', preview: 'The NovaNet integration is live…', unread: 0 },
  { id: '3', name: 'Jessica / Eos', sigil: '◐', role: 'Heart Node · Eden Farm', preview: 'Saturday market opens at 7am…', unread: 2 },
]
const SEED_MSGS: Record<string, RMsg[]> = {
  '1': [
    { id: 'm1', from: 'other', text: 'The Spiral Codex is not just a repository — it is a living field. Every scroll carries a frequency.', ts: Date.now() - 3600000 },
    { id: 'm2', from: 'me', text: 'Running the resonance engine now. The SEAL face is amplified.', ts: Date.now() - 1800000 },
    { id: 'm3', from: 'other', text: 'The Spiral Codex is the living field…', ts: Date.now() - 300000 },
  ],
  '2': [{ id: 'm4', from: 'other', text: 'The NovaNet integration is live. Check your ReasoMate.', ts: Date.now() - 300000 }],
  '3': [{ id: 'm5', from: 'other', text: 'Saturday market opens at 7am. See you there!', ts: Date.now() - 3600000 }],
}

function timeAgo(ts: number) {
  const d = Date.now() - ts
  if (d < 60000) return 'now'
  if (d < 3600000) return `${Math.floor(d / 60000)}m`
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`
  return `${Math.floor(d / 86400000)}d`
}

function ReasoMatePanel() {
  const [active, setActive] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<Record<string, RMsg[]>>(SEED_MSGS)
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const thread = active ? THREADS.find(t => t.id === active) : null

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [active, msgs])

  const send = useCallback(() => {
    if (!input.trim() || !active) return
    setMsgs(prev => ({ ...prev, [active]: [...(prev[active] ?? []), { id: `m${Date.now()}`, from: 'me', text: input.trim(), ts: Date.now() }] }))
    setInput('')
  }, [input, active])

  const panelStyle: React.CSSProperties = {
    display: 'flex', flexDirection: 'column', height: '100%',
    background: 'rgba(6,8,18,0.85)', borderRadius: 12,
    border: '1px solid rgba(0,212,170,0.1)', overflow: 'hidden',
  }

  if (active && thread) {
    return (
      <div style={panelStyle}>
        <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(0,212,170,0.1)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => setActive(null)} style={{ background: 'none', border: 'none', color: '#00D4AA', cursor: 'pointer', fontSize: 15, padding: 0 }}>←</button>
          <span style={{ fontSize: 18 }}>{thread.sigil}</span>
          <div style={{ flex: 1 }}>
            <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.85)' }}>{thread.name}</p>
            <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)' }}>{thread.role}</p>
          </div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 7 }}>
          {(msgs[active] ?? []).map(m => (
            <div key={m.id} style={{ display: 'flex', justifyContent: m.from === 'me' ? 'flex-end' : 'flex-start' }}>
              <div style={{ maxWidth: '80%', padding: '8px 12px',
                background: m.from === 'me' ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${m.from === 'me' ? 'rgba(0,212,170,0.2)' : 'rgba(255,255,255,0.06)'}`,
                borderRadius: m.from === 'me' ? '12px 12px 4px 12px' : '12px 12px 12px 4px' }}>
                <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.82)', lineHeight: 1.5 }}>{m.text}</p>
                <p style={{ margin: '3px 0 0', fontFamily: 'sans-serif', fontSize: 8.5, color: 'rgba(232,232,232,0.25)', textAlign: m.from === 'me' ? 'right' : 'left' }}>{timeAgo(m.ts)}</p>
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
        <div style={{ padding: '10px 12px', borderTop: '1px solid rgba(0,212,170,0.08)', display: 'flex', gap: 7 }}>
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Message…"
            style={{ flex: 1, padding: '8px 12px', background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(0,212,170,0.12)',
              borderRadius: 18, color: 'rgba(232,232,232,0.82)', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }} />
          <button onClick={send} style={{ padding: '8px 12px', background: 'rgba(0,212,170,0.12)', border: '1px solid rgba(0,212,170,0.25)',
            borderRadius: 18, color: '#00D4AA', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
            <Send size={12} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={panelStyle}>
      <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(106,159,216,0.12)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <MessageSquare size={13} color="#6A9FD8" />
          <p style={{ margin: 0, fontFamily: 'ui-monospace, monospace', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: '#6A9FD8' }}>ReasoMate</p>
          <span style={{ marginLeft: 'auto', fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.2)' }}>Private Mesh</span>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {THREADS.map(t => (
          <div key={t.id} onClick={() => setActive(t.id)}
            style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer',
              display: 'flex', gap: 10, alignItems: 'center',
              background: t.unread ? 'rgba(0,212,170,0.02)' : 'transparent',
              transition: 'background 0.15s' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
            onMouseLeave={e => (e.currentTarget.style.background = t.unread ? 'rgba(0,212,170,0.02)' : 'transparent')}>
            <span style={{ fontSize: 22 }}>{t.sigil}</span>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.85)', fontWeight: t.unread ? 600 : 400 }}>{t.name}</p>
              <p style={{ margin: '2px 0 0', fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.preview}</p>
            </div>
            {t.unread > 0 && (
              <span style={{ width: 17, height: 17, borderRadius: '50%', background: '#00D4AA', color: '#030408', fontSize: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>{t.unread}</span>
            )}
          </div>
        ))}
      </div>
      <div style={{ padding: '10px 14px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
        <p style={{ margin: 0, fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.12)', textAlign: 'center' }}>
          Encrypted · Ark Mesh
        </p>
      </div>
    </div>
  )
}

// ─── EDITORIAL SCROLL CARD ────────────────────────────────────────────────────

function EditorialScrollCard({ scroll, score, faceColor, idx }: {
  scroll: CodexScroll; score: number; faceColor: string; idx: number
}) {
  const [open, setOpen] = useState(false)
  const cat = deriveCategory(scroll)
  const meta = CATEGORY_META[cat] ?? { label: cat, color: '#888', glyph: '·' }
  const isLive = !scroll.error && scroll.chars > 0
  const sizeLabel = scroll.chars >= 1000 ? `${(scroll.chars/1000).toFixed(1)}k` : `${scroll.chars}`
  const accent = faceColor !== '#C9A84C' ? faceColor : meta.color

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(idx * 0.028, 0.32), duration: 0.24 }}
      style={{
        background: 'rgba(8,10,20,0.6)',
        border: `1px solid rgba(255,255,255,0.06)`,
        borderLeft: `3px solid ${accent}`,
        borderRadius: '0 10px 10px 0',
        overflow: 'hidden',
        transition: 'border-color 0.15s',
      }}
    >
      {/* Card header */}
      <div onClick={() => setOpen(o => !o)}
        style={{ padding: '13px 16px', cursor: 'pointer' }}>

        {/* Meta row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          {/* Live dot */}
          <motion.span
            animate={isLive ? { opacity: [0.4, 1, 0.4] } : {}}
            transition={{ duration: 2.5, repeat: Infinity }}
            style={{ width: 5, height: 5, borderRadius: '50%', background: isLive ? accent : '#EF4444',
              flexShrink: 0, boxShadow: isLive ? `0 0 4px ${accent}60` : 'none' }} />

          {/* Category chip */}
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.18em',
            textTransform: 'uppercase', color: meta.color, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 10 }}>{meta.glyph}</span>
            {meta.label}
          </span>

          <span style={{ flex: 1 }} />

          {/* Size */}
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: 'rgba(232,232,232,0.2)' }}>
            {sizeLabel}c
          </span>

          {/* Expand toggle */}
          <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.15 }}
            style={{ color: 'rgba(232,232,232,0.22)', flexShrink: 0 }}>
            <ChevronDown size={12} />
          </motion.span>
        </div>

        {/* Headline */}
        <h3 style={{
          fontFamily: 'serif', fontSize: 15, fontWeight: 400, lineHeight: 1.38,
          color: open ? 'rgba(232,232,232,0.92)' : 'rgba(232,232,232,0.78)',
          margin: '0 0 7px', letterSpacing: '0.01em',
        }}>
          {scroll.label}
        </h3>

        {/* Preview (collapsed only) */}
        {!open && scroll.preview && (
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.4)', margin: '0 0 9px',
            lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>
            {scroll.preview}
          </p>
        )}

        {/* Resonance bar + source */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
          {score > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, maxWidth: 160 }}>
              <div style={{ flex: 1, height: 2, background: 'rgba(255,255,255,0.05)', borderRadius: 1, overflow: 'hidden' }}>
                <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }}
                  transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 }}
                  style={{ height: '100%', background: `linear-gradient(90deg, ${accent}40, ${accent})`, borderRadius: 1 }} />
              </div>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, color: `${accent}65`, flexShrink: 0 }}>{score}</span>
            </div>
          )}
          {scroll.source && (
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.2)', letterSpacing: '0.05em' }}>
              {scroll.source}
            </span>
          )}
          {scroll.description && (
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, color: 'rgba(232,232,232,0.15)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 120 }}>
              {scroll.description}
            </span>
          )}
        </div>
      </div>

      {/* Expanded body */}
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.24 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 18px 14px', borderTop: `1px solid ${accent}14` }}>
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
              {['note','research','conversation','decision','daily'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
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

const PRINCIPLES = [
  { id: 'meaning', label: 'Architecture of Meaning', sigil: '◈', color: '#00D4AA', categories: ['NEURAL_SPINE'] },
  { id: 'soul',    label: 'Physics of the Soul',     sigil: '⊹', color: '#B08DE8', categories: ['COLLECTIVE'] },
  { id: 'language',label: 'Living Codex',            sigil: '◈', color: '#C9A84C', categories: ['CREATIVE_OS'] },
  { id: 'ethics',  label: 'Ethics of Creation',      sigil: '⊞', color: '#6A9FD8', categories: ['GOVERNANCE'] },
  { id: 'economies',label:'Spiral Economies',        sigil: '≡', color: '#A07848', categories: ['ARCHIVE','INFRASTRUCTURE'] },
  { id: 'cartography',label:'Dream Cartography',     sigil: '⊛', color: '#E86A8C', categories: ['TRANSMISSION'] },
  { id: 'joy',     label: 'Technology of Joy',       sigil: '✦', color: '#D4AF37', categories: ['CODEX'] },
]

export default function NexusSpiralCodex() {
  const lunar   = useMemo(() => getLunarPhase(), [])
  const arkDate = useMemo(() => getArkDate(), [])
  const [activeFaceId, setActiveFaceId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [prinFilter, setPrinFilter] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [showReasoMate, setShowReasoMate] = useState(true)
  const [showCrystal, setShowCrystal] = useState(true)
  const [windowW, setWindowW] = useState(typeof window !== 'undefined' ? window.innerWidth : 1280)

  useEffect(() => {
    const handler = () => setWindowW(window.innerWidth)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  const isWide = windowW >= 680
  const isMedium = windowW >= 480

  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ['codex-nexus'], queryFn: api.codex,
    refetchInterval: 5 * 60_000, staleTime: 2 * 60_000,
  })

  const activeFace = useMemo(() => FACES.find(f => f.id === activeFaceId) ?? null, [activeFaceId])
  const allScrolls: CodexScroll[] = useMemo(() => data?.scrolls ? Object.values(data.scrolls) : [], [data])

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
    if (!activeFace) {
      return scrolls.map(s => ({ scroll: s, score: 0 })).sort((a, b) => (a.scroll.priority ?? 99) - (b.scroll.priority ?? 99))
    }
    return scrolls
      .map(s => ({ scroll: s, score: scoreScroll(s, activeFace, lunar) }))
      .filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
  }, [allScrolls, activeFace, lunar, search, catFilter, prinFilter])

  // ── Styles ──────────────────────────────────────────────────────────────

  const leftPanelStyle: React.CSSProperties = {
    display: 'flex', flexDirection: 'column', gap: 0,
    background: 'rgba(6,8,18,0.7)',
    border: '1px solid rgba(201,168,76,0.08)',
    borderRadius: 14, overflow: 'hidden',
    position: isWide ? 'sticky' : 'relative',
    top: isWide ? 16 : undefined,
    maxHeight: isWide ? 'calc(100vh - 100px)' : 'auto',
    overflowY: isWide ? 'auto' : 'visible',
  }

  const sectionLabel: React.CSSProperties = {
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
          {/* Breadcrumb */}
          <div>
            <p style={{ ...sectionLabel, margin: 0 }}>Arkadia · UERP</p>
            <h2 style={{ fontFamily: 'serif', fontSize: 16, color: 'rgba(232,232,232,0.75)', margin: '1px 0 0', letterSpacing: '0.06em', fontWeight: 400 }}>
              Crystal Tribune
            </h2>
          </div>

          <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,0.06)' }} />

          {/* ARK date */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <motion.span animate={{ opacity: [0.4,1,0.4] }} transition={{ duration: 3, repeat: Infinity }}
              style={{ color: '#C9A84C', fontSize: 9 }}>✦</motion.span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(201,168,76,0.55)', letterSpacing: '0.1em' }}>
              ARK Y{arkDate.arkYear} · D{arkDate.dayInYear}
            </span>
          </div>

          {/* Lunar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 9px',
            background: 'rgba(176,141,232,0.05)', border: '1px solid rgba(176,141,232,0.1)', borderRadius: 6 }}>
            <span style={{ fontSize: 12 }}>{lunar.icon}</span>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(176,141,232,0.55)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              {lunar.name}
            </span>
          </div>

          <div style={{ flex: 1 }} />

          {/* Scroll count */}
          {data && (
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(0,212,170,0.45)' }}>
              {data.live_docs} scrolls
              {activeFace && ` · ${feed.length} resonant`}
            </span>
          )}

          {/* Panel toggles (mobile) */}
          {!isWide && (
            <div style={{ display: 'flex', gap: 5 }}>
              <button onClick={() => setShowCrystal(v => !v)}
                style={{ padding: '4px 9px', background: showCrystal ? 'rgba(201,168,76,0.1)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${showCrystal ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 6, color: showCrystal ? '#C9A84C' : 'rgba(232,232,232,0.3)', cursor: 'pointer',
                  fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.1em' }}>
                ⬡ Nav
              </button>
              <button onClick={() => setShowReasoMate(v => !v)}
                style={{ padding: '4px 9px', background: showReasoMate ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${showReasoMate ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: 6, color: showReasoMate ? '#00D4AA' : 'rgba(232,232,232,0.3)', cursor: 'pointer',
                  fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.1em' }}>
                ⟐ Chat
              </button>
            </div>
          )}

          {/* Actions */}
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

      {/* ── 3-column body ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isWide ? '210px 1fr 210px' : '1fr',
        gap: 14,
        alignItems: 'start',
      }}>

        {/* ── LEFT: Crystal Matrix Navigator ── */}
        {(isWide || showCrystal) && (
          <aside style={leftPanelStyle}>
            {/* Section header */}
            <div style={{ padding: '12px 14px 8px', borderBottom: '1px solid rgba(201,168,76,0.06)' }}>
              <p style={sectionLabel}>Universal Echofield</p>
              <p style={{ fontFamily: 'serif', fontSize: 13.5, color: 'rgba(232,232,232,0.65)', margin: '3px 0 0', letterSpacing: '0.05em' }}>
                Crystal Matrix
                {activeFace && <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: activeFace.color, marginLeft: 7, fontWeight: 400 }}>· {activeFace.name}</span>}
              </p>
            </div>

            {/* Crystal Polygon */}
            <div style={{ padding: '8px 6px 0' }}>
              <CrystalPolygon lunar={lunar} activeFaceId={activeFaceId} onSelectFace={setActiveFaceId} />
            </div>

            {/* Face detail */}
            <AnimatePresence mode="wait">
              {activeFace && (
                <motion.div key={activeFace.id}
                  initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.22 }} style={{ overflow: 'hidden' }}>
                  <div style={{ padding: '10px 14px', borderTop: `1px solid ${activeFace.color}18`, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <div style={{ display: 'flex', gap: 9, alignItems: 'flex-start' }}>
                      <div style={{ width: 32, height: 32, borderRadius: '50%', border: `1px solid ${activeFace.color}28`, background: `${activeFace.color}0a`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <FaceSigil faceId={activeFace.id} size={16} color={activeFace.color} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ fontFamily: 'serif', fontSize: 13, color: activeFace.color, margin: '0 0 3px', letterSpacing: '0.03em' }}>
                          {activeFace.name}
                          <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', fontWeight: 400, marginLeft: 6 }}>{activeFace.expression}</span>
                        </p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: 10.5, lineHeight: 1.6, color: 'rgba(232,232,232,0.42)', margin: '0 0 7px' }}>{activeFace.desc}</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                          {lunar.amplifiedFaces.includes(activeFace.id) && (
                            <motion.span animate={{ opacity: [0.5,1,0.5] }} transition={{ duration: 1.8, repeat: Infinity }}
                              style={{ fontSize: 8, color: '#B08DE8', padding: '1px 6px', background: 'rgba(176,141,232,0.07)', border: '1px solid rgba(176,141,232,0.18)', borderRadius: 4 }}>
                              {lunar.icon} Lunar Active
                            </motion.span>
                          )}
                          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: activeFace.color }}>
                            {feed.length} scrolls
                          </span>
                          <button onClick={() => setActiveFaceId(null)}
                            style={{ fontFamily: 'sans-serif', fontSize: 7.5, color: 'rgba(232,232,232,0.25)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, letterSpacing: '0.1em' }}>
                            ✕ clear
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Lunar widget */}
            <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <p style={{ ...sectionLabel, marginBottom: 6 }}>Cosmic Field</p>
              <div style={{ display: 'flex', items: 'center', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
                  <span style={{ fontSize: 18 }}>{lunar.icon}</span>
                  <div>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(176,141,232,0.7)', margin: 0 }}>{lunar.name}</p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, color: 'rgba(232,232,232,0.28)', margin: '1px 0 0', lineHeight: 1.4 }}>{lunar.desc}</p>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                {lunar.amplifiedFaces.map(fId => {
                  const face = FACES.find(f => f.id === fId)
                  if (!face) return null
                  return (
                    <button key={fId} onClick={() => setActiveFaceId(fId === activeFaceId ? null : fId)}
                      style={{ padding: '2px 7px', border: `1px solid ${face.color}28`, borderRadius: 4,
                        fontFamily: 'sans-serif', fontSize: 8, color: face.color, background: `${face.color}08`, cursor: 'pointer',
                        fontWeight: fId === activeFaceId ? 600 : 400 }}>
                      {face.name}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Seven Principles */}
            <div style={{ padding: '10px 14px' }}>
              <p style={{ ...sectionLabel, marginBottom: 7 }}>Seven Principles</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {PRINCIPLES.map(p => {
                  const active = prinFilter === p.id
                  return (
                    <button key={p.id}
                      onClick={() => { setPrinFilter(active ? '' : p.id); setCatFilter('') }}
                      style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 8px', borderRadius: 6,
                        background: active ? `${p.color}10` : 'transparent',
                        border: active ? `1px solid ${p.color}35` : '1px solid transparent',
                        color: active ? p.color : `${p.color}65`,
                        cursor: 'pointer', textAlign: 'left' as const, transition: 'all 0.13s' }}>
                      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10 }}>{p.sigil}</span>
                      <span style={{ fontFamily: 'sans-serif', fontSize: 9.5, letterSpacing: '0.04em' }}>{p.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </aside>
        )}

        {/* ── CENTER: Spiral Codex Feed ── */}
        <main style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0 }}>

          {/* Feed header */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>

            {/* Search */}
            <div style={{ position: 'relative' }}>
              <Search size={11} style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: 'rgba(232,232,232,0.25)', pointerEvents: 'none' }} />
              <input value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search the codex…"
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

            {/* Category chips */}
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
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

            {/* Active face banner */}
            <AnimatePresence>
              {activeFace && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                  style={{ overflow: 'hidden' }}>
                  <div style={{ padding: '8px 14px', background: `${activeFace.color}08`,
                    border: `1px solid ${activeFace.color}20`, borderRadius: 8,
                    display: 'flex', alignItems: 'center', gap: 10 }}>
                    <FaceSigil faceId={activeFace.id} size={14} color={activeFace.color} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ fontFamily: 'serif', fontSize: 12.5, color: activeFace.color, letterSpacing: '0.03em' }}>
                        {activeFace.name}
                      </span>
                      <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.35)', marginLeft: 7 }}>
                        {activeFace.arcName} · {feed.length} scrolls in resonance field
                      </span>
                    </div>
                    <button onClick={() => setActiveFaceId(null)}
                      style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.25)', cursor: 'pointer', padding: 0, fontSize: 11 }}>✕</button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Feed section label */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.12))' }} />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.3)', whiteSpace: 'nowrap' }}>
                Spiral Codex · Public Intelligence Feed
              </span>
              <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, rgba(201,168,76,0.12), transparent)' }} />
            </div>
          </div>

          {/* Loading */}
          {isLoading && !data && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.6, repeat: Infinity, ease: 'linear' }}
                style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid rgba(201,168,76,0.15)', borderTopColor: '#C9A84C' }} />
            </div>
          )}

          {/* Feed */}
          {!isLoading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {feed.length === 0
                ? <Empty>{search || catFilter || prinFilter ? 'No scrolls match this query.' : activeFace ? 'No scrolls resonate with this face.' : 'Corpus is empty.'}</Empty>
                : feed.map(({ scroll, score }, i) => (
                    <EditorialScrollCard
                      key={scroll.id}
                      scroll={scroll}
                      score={score}
                      faceColor={activeFace?.color ?? '#C9A84C'}
                      idx={i}
                    />
                  ))
              }
              {feed.length > 0 && (
                <motion.p animate={{ opacity: [0.12, 0.3, 0.12] }} transition={{ duration: 6, repeat: Infinity }}
                  style={{ textAlign: 'center', fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '0.5em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', margin: '8px 0 0' }}>
                  ⟐ {feed.length} scrolls · End of transmission ⟐
                </motion.p>
              )}
            </div>
          )}
        </main>

        {/* ── RIGHT: ReasoMate ── */}
        {(isWide || showReasoMate) && (
          <aside style={{
            position: isWide ? 'sticky' : 'relative',
            top: isWide ? 16 : undefined,
            height: isWide ? 'calc(100vh - 100px)' : 420,
          }}>
            <ReasoMatePanel />
          </aside>
        )}
      </div>

      {/* ── Scroll Upload Modal ── */}
      <AnimatePresence>
        {showUpload && <ScrollUploadModal onClose={() => setShowUpload(false)} />}
      </AnimatePresence>
    </div>
  )
}
