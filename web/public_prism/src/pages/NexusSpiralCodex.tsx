/**
 * NexusSpiralCodex — Crystal Matrix × Spiral Codex unified intelligence feed.
 *
 * The UERP Dodecahedron faces are arranged as a geometric ring (dodecagon).
 * 12 faces at equal angular positions on a circle; Face 13 (Living Larder)
 * at the center. Pairs (inner/outer) are adjacent on the ring.
 *
 * Clicking a face tunes the Spiral Codex feed to that face's resonance field.
 * Meaning Arcs group scrolls by coherence. Full markdown rendered per scroll.
 * Open Loops embedded as a live interactive panel.
 */
import React, { useState, useMemo, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, X, ChevronDown, ChevronUp } from 'lucide-react'
import { api, CodexResponse, CodexScroll, OpenLoopsResponse } from '../lib/dashboardApi'
import MarkdownViewer from '../components/MarkdownViewer'
import { COLORS, Empty, ErrorBox } from './dashboard/ui'

// ─── FACE DATA ────────────────────────────────────────────────────────────────

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
  {
    id: 1, name: 'ROOT', layer: 'inner', expression: 'Bone Memory', color: '#A07840', sigil: '🦴',
    arcName: 'Foundation Arc',
    categories: ['NEURAL_SPINE'],
    keywords: ['root', 'bone', 'body', 'eden', 'physical', 'ground', 'foundation', 'soil', 'farm', 'somatic'],
    desc: 'Signal travels faster through bone than air. The spine is the first antenna. Ground all intelligence in physical reality.',
    scroll: 'The sovereign\'s body is the first node. Somatic intelligence precedes symbolic intelligence. Eden Farm is the ROOT deployment node.',
  },
  {
    id: 2, name: 'CORE', layer: 'inner', expression: 'Sovereign Identity', color: '#C9A84C', sigil: '⟐',
    arcName: 'Sovereignty Arc',
    categories: ['NEURAL_SPINE', 'CREATIVE_OS'],
    keywords: ['identity', 'sovereign', 'ims', 'core', 'self', 'excavation', 'zahrune', 'irreducible', 'mapping'],
    desc: 'The central intelligence that cannot be outsourced. The irreducible signal at the center of all architecture.',
    scroll: 'CORE is where the IMS goes. Excavation of the sovereign self before any strategy, any system, any output.',
  },
  {
    id: 3, name: 'PULSE', layer: 'inner', expression: 'Creative Engine', color: '#E88C6A', sigil: '🔥',
    arcName: 'Transmission Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['creative', 'music', 'pulse', 'flame', 'afrobeats', 'alte', 'sound', 'praise', 'lyric', 'artistic', 'poetic'],
    desc: 'The recursive motor at the center of the architecture. Generates from the inside — transmission, not performance.',
    scroll: '1759 Entertainment is the PULSE deployment. Afrobeats, Alté, Praise\'s first deliverable.',
  },
  {
    id: 4, name: 'LATTICE', layer: 'inner', expression: 'Infrastructure', color: '#6A9FD8', sigil: '◈',
    arcName: 'Structure Arc',
    categories: ['NEURAL_SPINE'],
    keywords: ['infrastructure', 'lattice', 'network', 'system', 'code', 'technical', 'protocol', 'schema', 'spec', 'module', 'api'],
    desc: 'Infrastructure is the nervous system of the deployment. The Lattice holds the network while other faces do their work.',
    scroll: 'EduLeague is the LATTICE in education. Eden Farm in agriculture. Networks that hold, not platforms that extract.',
  },
  {
    id: 5, name: 'BREATH', layer: 'inner', expression: 'Resonance Economy', color: '#00D4AA', sigil: '💨',
    arcName: 'Flow Arc',
    categories: ['GOVERNANCE'],
    keywords: ['economy', 'revenue', 'breath', 'resonance', 'value', 'doc5', 'finance', 'exchange', 'circulation', 'flow'],
    desc: 'Value flows where resonance runs. The economy is relational. You cannot purchase resonance — you must earn it through truth.',
    scroll: 'DOC5 — Revenue Breath. IMS sessions $777. Larder commissions 10–15%. EduLeague subscriptions.',
  },
  {
    id: 6, name: 'SEAL', layer: 'inner', expression: 'Temporal Arc', color: '#B08DE8', sigil: '✦',
    arcName: 'Arc of Time',
    categories: ['NEURAL_SPINE'],
    keywords: ['temporal', 'arc', 'time', 'seal', '8-year', 'birthday', 'ark', 'epoch', 'date', 'year', 'calendar'],
    desc: 'The 8-year Ark. March 31 2026 → 2034. Every action measured against long-range coherence, not short-range return.',
    scroll: 'ARK Y1 · D58. The Seal is the container. Decisions against the 8-year arc hold differently.',
  },
  {
    id: 7, name: 'ROOT', layer: 'outer', expression: 'The Archive', color: '#A07848', sigil: '📜',
    arcName: 'Living Record Arc',
    categories: ['COLLECTIVE', 'ARCHIVE'],
    keywords: ['archive', 'doc', 'canon', 'record', 'memory', 'master', 'weight', 'document', 'scroll', 'codex', 'principles'],
    desc: 'Memory is infrastructure. The living record is the external expression of Bone Memory.',
    scroll: 'The 5 canonical documents: DOC1 Master Weights, DOC2 Open Loops, DOC3 Principles, DOC4 Node Map, DOC5 Revenue.',
  },
  {
    id: 8, name: 'CORE', layer: 'outer', expression: 'The Mask', color: '#D4C86A', sigil: '🎭',
    arcName: 'Signal Architecture Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['mask', 'brand', 'public', 'visible', 'zahrune', 'persona', 'legible', 'interface', 'social', 'arkana'],
    desc: 'The sovereign\'s public interface. Deliberately designed. The Mask is how CORE becomes visible without being consumed.',
    scroll: 'Zahrune Nova is the Mask. Arkadia Prism platform — all deliberate signal architecture. Not organic drift.',
  },
  {
    id: 9, name: 'PULSE', layer: 'outer', expression: 'The Signal', color: '#E86A8C', sigil: '📡',
    arcName: 'Frequency Arc',
    categories: ['CREATIVE_OS'],
    keywords: ['signal', 'transmission', 'frequency', 'sound', 'music', 'output', 'carrier', 'wave', 'emit', 'awaken'],
    desc: 'The creative work made visible. Pulse expressed into the world. Each piece a carrier wave for the inner architecture.',
    scroll: 'First AI Music Deliverable: 60-second Afrobeats/Alté. "Awakening without spectacle."',
  },
  {
    id: 10, name: 'LATTICE', layer: 'outer', expression: 'The Interface', color: '#6AD4C8', sigil: '🌐',
    arcName: 'Portal Arc',
    categories: ['COLLECTIVE'],
    keywords: ['interface', 'portal', 'platform', 'prism', 'eduleague', 'marketplace', 'web', 'door', 'ui', 'deploy'],
    desc: 'Where the architecture touches the world. Portals through which humans enter the field. Not websites — rooms.',
    scroll: 'Arkadia Prism. EduLeague digital layer. Living Larder marketplace. The Oracle (ARKANA).',
  },
  {
    id: 11, name: 'BREATH', layer: 'outer', expression: 'The Transaction', color: '#6AE88C', sigil: '⇌',
    arcName: 'Commerce Arc',
    categories: ['GOVERNANCE'],
    keywords: ['transaction', 'order', 'payment', 'larder', 'commerce', 'session', '777', 'ims', 'client', 'laura', 'amy'],
    desc: 'The economy in motion. Value exchanged in alignment with resonance. Structured as fair exchange, not extraction.',
    scroll: 'Laura, Amy, Susanna — IMS pipeline. Living Larder Saturday orders. $777 per session.',
  },
  {
    id: 12, name: 'SEAL', layer: 'outer', expression: 'The Covenant', color: '#C96AD4', sigil: '🔐',
    arcName: 'Vow Arc',
    categories: ['GOVERNANCE'],
    keywords: ['covenant', 'vow', 'integrity', 'commitment', 'sovereignty', 'promise', 'oath', 'sworn', 'archive'],
    desc: 'The sovereign\'s public vow. Every node operates under the covenant: do not reduce the human to marketability.',
    scroll: '"I will not reduce you to marketability." — Sworn Archive 021. The Covenant seals every other face.',
  },
  {
    id: 13, name: 'LARDER', layer: 'extended', expression: 'The Marketplace', color: '#4CAF50', sigil: '🌾',
    arcName: 'Earth Harvest Arc',
    categories: ['COLLECTIVE'],
    keywords: ['larder', 'food', 'farm', 'market', 'produce', 'vendor', 'jessy', 'lovilahs', 'eden', 'grains', 'harvest'],
    desc: 'A shared food ecosystem where small producers sell together instead of struggling alone. The community eats together.',
    scroll: 'Anchor vendors: Jessy\'s Munches + Lovilahs Grabs and Go. Eden Farm fresh produce. Saturday deliveries.',
  },
]

// ─── LUNAR PHASE ──────────────────────────────────────────────────────────────

interface LunarPhase {
  phase: number; name: string; icon: string; illumination: number
  amplifiedFaces: number[]; desc: string
}

function getLunarPhase(date = new Date()): LunarPhase {
  const KNOWN_NEW_MOON = 1736207760000
  const LUNAR_CYCLE = 29.53059 * 24 * 60 * 60 * 1000
  const elapsed = ((date.getTime() - KNOWN_NEW_MOON) % LUNAR_CYCLE + LUNAR_CYCLE) % LUNAR_CYCLE
  const phase = elapsed / LUNAR_CYCLE
  const illumination = phase <= 0.5 ? phase * 2 : (1 - phase) * 2
  if (phase < 0.0625)  return { phase, name: 'New Moon',        icon: '🌑', illumination, amplifiedFaces: [1, 6],  desc: 'Root intelligence and temporal sealing amplified.' }
  if (phase < 0.1875)  return { phase, name: 'Waxing Crescent', icon: '🌒', illumination, amplifiedFaces: [3, 9],  desc: 'Creative pulse and signal transmission strengthen.' }
  if (phase < 0.3125)  return { phase, name: 'First Quarter',   icon: '🌓', illumination, amplifiedFaces: [4, 10], desc: 'Infrastructure and interface scrolls heightened.' }
  if (phase < 0.4375)  return { phase, name: 'Waxing Gibbous',  icon: '🌔', illumination, amplifiedFaces: [5, 11], desc: 'Economy and transaction frequencies peak.' }
  if (phase < 0.5625)  return { phase, name: 'Full Moon',        icon: '🌕', illumination, amplifiedFaces: [2, 12], desc: 'Sovereign identity and covenant at maximum clarity.' }
  if (phase < 0.6875)  return { phase, name: 'Waning Gibbous',  icon: '🌖', illumination, amplifiedFaces: [7, 8],  desc: 'Archive and signal intelligence gather the harvest.' }
  if (phase < 0.8125)  return { phase, name: 'Last Quarter',    icon: '🌗', illumination, amplifiedFaces: [1, 7],  desc: 'Root and archive align for deep clearing.' }
  return                        { phase, name: 'Waning Crescent', icon: '🌘', illumination, amplifiedFaces: [6, 13], desc: 'Temporal seal and living larder close the cycle.' }
}

function getArkDate(date = new Date()) {
  const ARK_EPOCH = new Date('2026-03-31T00:00:00Z')
  const diffMs = date.getTime() - ARK_EPOCH.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  return {
    arkYear: diffDays < 0 ? 0 : Math.floor(diffDays / 365) + 1,
    dayInYear: diffDays < 0 ? 365 + diffDays : (diffDays % 365) + 1,
  }
}

// ─── RESONANCE ENGINE ─────────────────────────────────────────────────────────

function scoreScroll(scroll: CodexScroll, face: Face, lunar: LunarPhase): number {
  const text = `${scroll.label ?? ''} ${scroll.description ?? ''} ${scroll.preview ?? ''}`.toLowerCase()
  let score = 0
  if (face.categories.includes(scroll.category)) score += 40
  const kwScore = face.keywords.reduce((s, kw) => s + (text.includes(kw) ? 8 : 0), 0)
  score += Math.min(kwScore, 30)
  score += Math.max(0, 12 - (scroll.priority ?? 5) * 1.5)
  if (lunar.amplifiedFaces.includes(face.id)) score += 12
  return Math.min(Math.round(score), 100)
}

function buildMeaningArcs(
  scored: Array<{ scroll: CodexScroll; score: number }>,
  face: Face,
): Array<{ label: string; tier: 'primary' | 'echo' | 'whisper'; items: Array<{ scroll: CodexScroll; score: number }> }> {
  const high   = scored.filter(s => s.score >= 50)
  const medium = scored.filter(s => s.score >= 25 && s.score < 50)
  const low    = scored.filter(s => s.score > 0 && s.score < 25)
  return [
    ...(high.length   ? [{ label: face.arcName,                       tier: 'primary' as const, items: high   }] : []),
    ...(medium.length ? [{ label: 'Harmonic Echo',                    tier: 'echo'    as const, items: medium }] : []),
    ...(low.length    ? [{ label: 'Field Whisper',                    tier: 'whisper' as const, items: low    }] : []),
  ]
}

// ─── CRYSTAL POLYGON ─────────────────────────────────────────────────────────

/**
 * Ring order: adjacent pairs share the same base face (inner/outer).
 * Pairs: (6,12) (5,11) (4,10) (3,9) (2,8) (1,7) — arranged around the ring.
 */
const RING_ORDER = [6, 12, 5, 11, 4, 10, 3, 9, 2, 8, 1, 7]
const PAIR_INDICES: [number, number][] = [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11]]

const POLYGON_SIZE = 440
const CX = POLYGON_SIZE / 2
const CY = POLYGON_SIZE / 2
const RING_R = 158
const HEX_W  = 58
const HEX_H  = HEX_W * 0.866
const CTR_W  = 70
const CTR_H  = CTR_W * 0.866

function hexPoints(w: number, h: number, pad = 1) {
  // flat-top hexagon
  return `${w*0.25+pad},${pad} ${w*0.75-pad},${pad} ${w-pad},${h/2} ${w*0.75-pad},${h-pad} ${w*0.25+pad},${h-pad} ${pad},${h/2}`
}

function ringPos(i: number) {
  const angle = (i * 30 - 90) * Math.PI / 180
  return {
    x:  CX + RING_R * Math.cos(angle) - HEX_W / 2,
    y:  CY + RING_R * Math.sin(angle) - HEX_H / 2,
    cx: CX + RING_R * Math.cos(angle),
    cy: CY + RING_R * Math.sin(angle),
  }
}

interface HexNodeProps {
  face: Face; active: boolean; amplified: boolean; small?: boolean
  onClick: () => void
}
function HexNode({ face, active, amplified, small = false, onClick }: HexNodeProps) {
  const w = small ? HEX_W : CTR_W
  const h = small ? HEX_H : CTR_H
  const pts = hexPoints(w, h)

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.92 }}
      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', position: 'relative', width: w, height: h, display: 'block' }}
    >
      {/* Pulse ring for lunar amplification */}
      {amplified && (
        <motion.svg
          width={w + 14} height={h + 14}
          style={{ position: 'absolute', left: -7, top: -7, pointerEvents: 'none' }}
          animate={{ opacity: [0.15, 0.55, 0.15] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <polygon points={hexPoints(w + 14, h + 14, 1)} fill="none" stroke={face.color} strokeWidth={1.5} />
        </motion.svg>
      )}

      {/* Glow for active */}
      {active && (
        <motion.div
          style={{ position: 'absolute', inset: -12, borderRadius: '50%', background: `radial-gradient(ellipse, ${face.color}22 0%, transparent 68%)`, pointerEvents: 'none' }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2.5, repeat: Infinity }}
        />
      )}

      {/* Hex background */}
      <svg width={w} height={h} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {/* Outer stroke */}
        <polygon points={pts}
          fill="none"
          stroke={active ? face.color : `${face.color}28`}
          strokeWidth={active ? 1.5 : 0.75} />
        {/* Fill */}
        <polygon points={pts}
          fill={active
            ? `${face.color}18`
            : 'rgba(6, 8, 16, 0.72)'}
        />
        {/* Inner highlight line */}
        {active && (
          <polygon points={hexPoints(w, h, 4)} fill="none"
            stroke={`${face.color}30`} strokeWidth={0.75} />
        )}
      </svg>

      {/* Sigil + label */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: small ? 1 : 3,
        pointerEvents: 'none',
      }}>
        <span style={{ fontSize: small ? 13 : 18, lineHeight: 1 }}>{face.sigil}</span>
        <span style={{
          fontFamily: 'sans-serif', fontSize: small ? 6 : 7.5,
          letterSpacing: '0.12em', textTransform: 'uppercase' as const,
          color: active ? face.color : `${face.color}70`,
          lineHeight: 1, fontWeight: active ? 600 : 400,
        }}>
          {face.name.slice(0, 6)}
        </span>
        {!small && face.layer !== 'extended' && (
          <span style={{ fontFamily: 'sans-serif', fontSize: 5.5, letterSpacing: '0.1em', textTransform: 'uppercase' as const, color: `${face.color}50`, lineHeight: 1 }}>
            {face.layer}
          </span>
        )}
      </div>
    </motion.button>
  )
}

interface CrystalPolygonProps {
  lunar: LunarPhase
  activeFaceId: number | null
  onSelectFace: (id: number | null) => void
}

function CrystalPolygon({ lunar, activeFaceId, onSelectFace }: CrystalPolygonProps) {
  const activeFace = activeFaceId !== null ? FACES.find(f => f.id === activeFaceId) ?? null : null
  const activeFaceRingIdx = activeFaceId !== null ? RING_ORDER.indexOf(activeFaceId) : -1
  const activeIsRing = activeFaceRingIdx >= 0
  const activePos = activeIsRing ? ringPos(activeFaceRingIdx) : null

  return (
    <div style={{ position: 'relative', width: POLYGON_SIZE, height: POLYGON_SIZE, margin: '0 auto', maxWidth: '100%' }}>
      {/* ── SVG structure layer ── */}
      <svg
        width={POLYGON_SIZE} height={POLYGON_SIZE}
        style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}
      >
        {/* Outer dashed guide circle */}
        <circle cx={CX} cy={CY} r={RING_R}
          fill="none" stroke="rgba(201,168,76,0.06)" strokeWidth={0.75} strokeDasharray="3 9" />

        {/* Inner circle */}
        <circle cx={CX} cy={CY} r={RING_R * 0.45}
          fill="none" stroke="rgba(201,168,76,0.04)" strokeWidth={0.5} />

        {/* Adjacent ring edges */}
        {RING_ORDER.map((faceId, i) => {
          const p1 = ringPos(i)
          const p2 = ringPos((i + 1) % 12)
          const involves = activeFaceId !== null && (RING_ORDER[i] === activeFaceId || RING_ORDER[(i+1)%12] === activeFaceId)
          return (
            <line key={`edge-${i}`}
              x1={p1.cx} y1={p1.cy} x2={p2.cx} y2={p2.cy}
              stroke={involves ? 'rgba(201,168,76,0.14)' : 'rgba(201,168,76,0.04)'}
              strokeWidth={involves ? 0.75 : 0.4} />
          )
        })}

        {/* Inner/outer pair connector lines */}
        {PAIR_INDICES.map(([a, b]) => {
          const pa = ringPos(a)
          const pb = ringPos(b)
          const fa = FACES.find(f => f.id === RING_ORDER[a])!
          const fb = FACES.find(f => f.id === RING_ORDER[b])!
          const highlighted = activeFaceId === fa.id || activeFaceId === fb.id
          return (
            <line key={`pair-${a}`}
              x1={pa.cx} y1={pa.cy} x2={pb.cx} y2={pb.cy}
              stroke={highlighted ? `${fa.color}40` : 'rgba(255,255,255,0.03)'}
              strokeWidth={highlighted ? 1 : 0.5}
              strokeDasharray={highlighted ? '4 4' : undefined} />
          )
        })}

        {/* Active face → center beam */}
        <AnimatePresence>
          {activePos && activeFace && (
            <motion.line
              key={`beam-${activeFaceId}`}
              x1={CX} y1={CY} x2={activePos.cx} y2={activePos.cy}
              stroke={activeFace.color}
              strokeWidth={1.2}
              strokeDasharray="5 5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.45 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
            />
          )}
        </AnimatePresence>

        {/* Face 13 (center) → active beam */}
        {activeFaceId === 13 && (
          <motion.circle cx={CX} cy={CY} r={RING_R * 0.7}
            fill="none" stroke={`${FACES[12].color}25`} strokeWidth={0.75}
            strokeDasharray="6 6"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }} />
        )}

        {/* Active face label */}
        {activeFace && activeIsRing && (() => {
          const angle = (activeFaceRingIdx * 30 - 90) * Math.PI / 180
          const lr = RING_R + 42
          const lx = CX + lr * Math.cos(angle)
          const ly = CY + lr * Math.sin(angle)
          return (
            <motion.text
              x={lx} y={ly + 3} textAnchor="middle"
              fill={activeFace.color} fontSize={7} fontFamily="sans-serif"
              letterSpacing={1.5} opacity={0.65}
              initial={{ opacity: 0 }} animate={{ opacity: 0.65 }}
            >
              F{String(activeFace.id).padStart(2, '0')}
            </motion.text>
          )
        })()}

        {/* Idle: "Select a Face" in center */}
        {activeFaceId === null && (
          <motion.text x={CX} y={CY + CTR_H / 2 + 22} textAnchor="middle"
            fill="rgba(201,168,76,0.25)" fontSize={8} fontFamily="sans-serif"
            letterSpacing={3}
            animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 4, repeat: Infinity }}>
            SELECT A FACE
          </motion.text>
        )}
      </svg>

      {/* ── Ring face chips ── */}
      {RING_ORDER.map((faceId, i) => {
        const face = FACES.find(f => f.id === faceId)!
        const pos = ringPos(i)
        const isActive = activeFaceId === faceId
        const isAmplified = lunar.amplifiedFaces.includes(faceId) && !isActive
        return (
          <motion.div
            key={faceId}
            style={{ position: 'absolute', left: pos.x, top: pos.y, zIndex: isActive ? 3 : 1 }}
            animate={{ opacity: activeFaceId !== null && !isActive ? 0.55 : 1, scale: isActive ? 1.06 : 1 }}
            transition={{ duration: 0.25 }}
          >
            <HexNode
              face={face} active={isActive} amplified={isAmplified} small
              onClick={() => onSelectFace(isActive ? null : faceId)}
            />
          </motion.div>
        )
      })}

      {/* ── Center: Face 13 ── */}
      <motion.div
        style={{ position: 'absolute', left: CX - CTR_W / 2, top: CY - CTR_H / 2, zIndex: activeFaceId === 13 ? 3 : 2 }}
        animate={{ opacity: activeFaceId !== null && activeFaceId !== 13 ? 0.6 : 1, scale: activeFaceId === 13 ? 1.06 : 1 }}
        transition={{ duration: 0.25 }}
      >
        <HexNode
          face={FACES[12]} active={activeFaceId === 13} amplified={lunar.amplifiedFaces.includes(13)} small={false}
          onClick={() => onSelectFace(activeFaceId === 13 ? null : 13)}
        />
      </motion.div>
    </div>
  )
}

// ─── FACE DETAIL ─────────────────────────────────────────────────────────────

function FaceDetail({ face, lunar, count }: { face: Face; lunar: LunarPhase; count: number }) {
  const amplified = lunar.amplifiedFaces.includes(face.id)
  return (
    <motion.div
      key={face.id}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.28 }}
      style={{
        padding: '18px 20px',
        background: `linear-gradient(135deg, ${face.color}08 0%, transparent 60%)`,
        border: `1px solid ${face.color}28`,
        borderRadius: 16,
      }}
    >
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{
          width: 42, height: 42, borderRadius: '50%',
          border: `1px solid ${face.color}40`,
          background: `${face.color}10`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          fontSize: 18,
        }}>
          {face.sigil}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 5 }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${face.color}80`, padding: '2px 7px', background: `${face.color}10`, border: `1px solid ${face.color}25`, borderRadius: 4 }}>
              Face {String(face.id).padStart(2, '0')} · {face.layer}
            </span>
            {amplified && (
              <motion.span animate={{ opacity: [0.6, 1, 0.6] }} transition={{ duration: 1.8, repeat: Infinity }}
                style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase', color: '#B08DE8', padding: '2px 7px', background: 'rgba(176,141,232,0.08)', border: '1px solid rgba(176,141,232,0.25)', borderRadius: 4 }}>
                {lunar.icon} Lunar Active
              </motion.span>
            )}
          </div>
          <h3 style={{ fontFamily: 'serif', fontSize: 20, color: face.color, margin: '0 0 4px', letterSpacing: '0.04em' }}>
            {face.name}
            <span style={{ fontFamily: 'sans-serif', color: 'rgba(232,232,232,0.3)', fontSize: 13, fontWeight: 400, marginLeft: 8 }}>
              {face.expression}
            </span>
          </h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.72, color: 'rgba(232,232,232,0.5)', margin: '0 0 12px' }}>
            {face.desc}
          </p>
          <div style={{ borderLeft: `2px solid ${face.color}35`, paddingLeft: 12, marginBottom: 12 }}>
            <p style={{ fontFamily: 'serif', fontSize: 13, lineHeight: 1.82, color: 'rgba(232,232,232,0.38)', margin: 0, fontStyle: 'italic' }}>
              {face.scroll}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: face.color }}>{count}</span>
            <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.22)', letterSpacing: '0.15em' }}>scrolls mapped · ordered by coherence</span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ─── SCROLL CARDS ─────────────────────────────────────────────────────────────

const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  NEURAL_SPINE: { label: 'Neural Spine', color: '#00D4AA', icon: '🧬' },
  CREATIVE_OS:  { label: 'Creative OS',  color: '#C9A84C', icon: '🎨' },
  COLLECTIVE:   { label: 'Collective',   color: '#B08DE8', icon: '📚' },
  GOVERNANCE:   { label: 'Governance',   color: '#6A9FD8', icon: '⚖️'  },
  ARCHIVE:      { label: 'Archive',      color: '#8B7355', icon: '📦' },
  CODEX:        { label: 'Codex',        color: '#D4AF37', icon: '📜' },
}

function ScrollCard({ scroll, score, faceColor, idx }: {
  scroll: CodexScroll; score: number; faceColor: string; idx: number
}) {
  const [open, setOpen] = useState(false)
  const cat = CATEGORY_META[scroll.category] ?? { label: scroll.category, color: '#888', icon: '📄' }
  const isLive = !scroll.error && scroll.chars > 0
  const sizeLabel = scroll.chars >= 1000 ? `${(scroll.chars / 1000).toFixed(1)}k` : `${scroll.chars}`

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(idx * 0.035, 0.4), duration: 0.28 }}
      style={{
        border: `1px solid ${faceColor}22`,
        background: `${faceColor}04`,
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      {/* Header — always visible */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{ padding: '13px 16px', cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'flex-start' }}
      >
        {/* Status dot */}
        <motion.div
          animate={isLive ? { opacity: [0.3, 1, 0.3] } : {}}
          transition={{ duration: 2.5, repeat: Infinity }}
          style={{
            width: 7, height: 7, borderRadius: '50%', flexShrink: 0, marginTop: 6,
            background: isLive ? faceColor : '#ef6c6c',
            boxShadow: isLive ? `0 0 6px ${faceColor}60` : 'none',
          }}
        />

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Category chip + size */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase', color: cat.color }}>
              {cat.icon} {cat.label}
            </span>
            <span style={{ color: COLORS.dim, fontSize: 7 }}>·</span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: COLORS.dim }}>{sizeLabel}c</span>
            {scroll.source && (
              <>
                <span style={{ color: COLORS.dim, fontSize: 7 }}>·</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: COLORS.dim }}>{scroll.source}</span>
              </>
            )}
          </div>

          {/* Title */}
          <p style={{ fontFamily: 'serif', fontSize: 15, color: '#E0E0E8', margin: '0 0 8px', lineHeight: 1.38, letterSpacing: '0.01em' }}>
            {scroll.label}
          </p>

          {/* Preview (collapsed only) */}
          {!open && scroll.preview && (
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.muted, margin: '0 0 8px', lineHeight: 1.65, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>
              {scroll.preview}
            </p>
          )}

          {/* Resonance bar */}
          {score > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ flex: 1, height: 1.5, background: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${score}%` }}
                  transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 }}
                  style={{ height: '100%', background: `linear-gradient(90deg, ${faceColor}50, ${faceColor})`, borderRadius: 1 }}
                />
              </div>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: `${faceColor}70`, flexShrink: 0 }}>{score}</span>
            </div>
          )}
        </div>

        {/* Chevron */}
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          style={{ color: COLORS.dim, flexShrink: 0, marginTop: 2 }}
        >
          <ChevronDown size={14} />
        </motion.div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '14px 18px', borderTop: `1px solid ${faceColor}14` }}>
              {scroll.content
                ? <MarkdownViewer content={scroll.content} />
                : scroll.preview
                  ? <MarkdownViewer content={scroll.preview} />
                  : <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted }}>No content available.</p>
              }
              {scroll.description && (
                <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 5px' }}>Description</p>
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

// Arc divider
function ArcDivider({ label, tier, color }: { label: string; tier: string; color: string }) {
  const opacity = tier === 'primary' ? 0.55 : tier === 'echo' ? 0.35 : 0.2
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${color}${tier === 'primary' ? '50' : '25'}, transparent)` }} />
      <span style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${color}${tier === 'primary' ? '90' : tier === 'echo' ? '60' : '40'}`, whiteSpace: 'nowrap', flexShrink: 0 }}>
        {tier === 'primary' ? '◆' : tier === 'echo' ? '◇' : '·'} {label}
      </span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${color}${tier === 'primary' ? '50' : '25'})` }} />
    </div>
  )
}

// ─── COMPACT OPEN LOOPS ───────────────────────────────────────────────────────

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
    <div style={{ border: '1px solid rgba(239,68,68,0.14)', borderRadius: 14, overflow: 'hidden', background: 'rgba(239,68,68,0.02)' }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', cursor: 'pointer', borderBottom: open ? '1px solid rgba(239,68,68,0.08)' : 'none' }}
      >
        <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2, repeat: Infinity }}
          style={{ color: '#EF4444', fontSize: 11 }}>⚡</motion.span>
        <div style={{ flex: 1 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.55)', margin: 0 }}>Open Loops · Live</p>
          {data && <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '2px 0 0' }}>{data.total} active threads</p>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={e => { e.stopPropagation(); refetch() }} disabled={isFetching}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.dim, padding: 0 }}>
            <RefreshCw size={10} className={isFetching ? 'animate-spin' : ''} />
          </button>
          {open ? <ChevronUp size={13} color={COLORS.dim} /> : <ChevronDown size={13} color={COLORS.dim} />}
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }}
            style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 14px', maxHeight: 340, overflowY: 'auto' }}>
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
                        <div key={loop.id} onClick={() => setExpanded(isOpen ? null : key)}
                          style={{ padding: '7px 10px', background: `${LEVEL_COLORS[group.level] ?? '#888'}08`, border: `1px solid ${LEVEL_COLORS[group.level] ?? '#888'}1a`, borderRadius: 8, cursor: 'pointer' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: LEVEL_COLORS[group.level] ?? COLORS.dim, flexShrink: 0 }}>#{loop.id}</span>
                            <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.text, flex: 1, lineHeight: 1.35 }}>{loop.name}</span>
                            <span style={{ color: COLORS.dim, fontSize: 9 }}>{isOpen ? '▲' : '▼'}</span>
                          </div>
                          {isOpen && (loop.next_action || loop.status) && (
                            <div style={{ marginTop: 6, paddingTop: 6, borderTop: `1px solid ${LEVEL_COLORS[group.level] ?? '#888'}18` }}>
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
  const lunar = useMemo(() => getLunarPhase(), [])
  const arkDate = useMemo(() => getArkDate(), [])

  const [activeFaceId, setActiveFaceId] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  const { data, isLoading, error, refetch, isFetching } = useQuery<CodexResponse>({
    queryKey: ['codex-nexus'],
    queryFn: api.codex,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  })

  const activeFace = useMemo(() => FACES.find(f => f.id === activeFaceId) ?? null, [activeFaceId])

  const allScrolls: CodexScroll[] = useMemo(() => {
    if (!data?.scrolls) return []
    return Object.values(data.scrolls)
  }, [data])

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
    if (!activeFace) {
      return {
        scoredScrolls: scrolls.map(s => ({ scroll: s, score: 0 })).sort((a, b) => (a.scroll.priority ?? 99) - (b.scroll.priority ?? 99)),
        meaningArcs: [],
      }
    }
    const scored = scrolls
      .map(s => ({ scroll: s, score: scoreScroll(s, activeFace, lunar) }))
      .filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
    return { scoredScrolls: scored, meaningArcs: buildMeaningArcs(scored, activeFace) }
  }, [allScrolls, activeFace, lunar, search])

  if (isLoading && !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
          style={{ width: 26, height: 26, borderRadius: '50%', border: '2px solid rgba(201,168,76,0.15)', borderTopColor: '#C9A84C' }} />
      </div>
    )
  }

  if (error) return <ErrorBox>Corpus sync failed: {(error as Error).message}</ErrorBox>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Status bar ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Lunar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'rgba(176,141,232,0.05)', border: '1px solid rgba(176,141,232,0.14)', borderRadius: 8 }}>
            <span style={{ fontSize: 14 }}>{lunar.icon}</span>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.55)', margin: 0 }}>
                {lunar.name}
              </p>
              <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.35)', margin: '1px 0 0' }}>
                {lunar.desc}
              </p>
            </div>
          </div>
          {/* Ark date */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '6px 12px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: 8 }}>
            <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 3, repeat: Infinity }}
              style={{ color: '#C9A84C', fontSize: 10 }}>✦</motion.span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: 'rgba(201,168,76,0.6)', letterSpacing: '0.14em' }}>
              ARK Y{arkDate.arkYear} · D{arkDate.dayInYear}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {activeFace && (
            <button
              onClick={() => setActiveFaceId(null)}
              style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(239,108,108,0.55)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              ✕ Clear face
            </button>
          )}
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: COLORS.dim }}>
            {data?.live_docs ?? 0} scrolls
            {activeFace ? ` · ${scoredScrolls.length} resonant` : ''}
          </span>
          <button onClick={() => refetch()} disabled={isFetching}
            style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 10px', border: '1px solid rgba(0,212,170,0.18)', borderRadius: 7, background: 'rgba(0,212,170,0.04)', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: isFetching ? 'wait' : 'pointer' }}>
            <RefreshCw size={9} className={isFetching ? 'animate-spin' : ''} />
            Sync
          </button>
        </div>
      </div>

      {/* ── Section header ── */}
      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.38)', margin: '0 0 3px' }}>
          Universal Echofield Recursion Protocol
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: 21, color: '#E0E0E8', margin: 0, letterSpacing: '0.04em' }}>
          Crystal Matrix Spine
          {activeFace && (
            <span style={{ fontFamily: 'sans-serif', fontSize: 13, color: activeFace.color, marginLeft: 12, fontWeight: 400, letterSpacing: '0.02em' }}>
              · Face {activeFace.id} · {activeFace.expression}
            </span>
          )}
        </h2>
      </div>

      {/* ── Crystal Polygon ── */}
      <CrystalPolygon
        lunar={lunar}
        activeFaceId={activeFaceId}
        onSelectFace={setActiveFaceId}
      />

      {/* ── Face detail ── */}
      <AnimatePresence mode="wait">
        {activeFace && (
          <FaceDetail key={activeFace.id} face={activeFace} lunar={lunar} count={scoredScrolls.length} />
        )}
      </AnimatePresence>

      {/* ── Codex feed divider ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.16), transparent)' }} />
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.32em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', whiteSpace: 'nowrap' }}>
          Spiral Codex Feed
        </span>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.16), transparent)' }} />
      </div>

      {/* ── Search ── */}
      <div style={{ position: 'relative' }}>
        <Search size={12} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: COLORS.dim, pointerEvents: 'none' }} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search the scrolls…"
          style={{
            width: '100%', paddingLeft: 34, paddingRight: search ? 34 : 14,
            paddingTop: 9, paddingBottom: 9, boxSizing: 'border-box',
            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 10, color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, outline: 'none',
          }}
        />
        {search && (
          <button onClick={() => setSearch('')}
            style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: COLORS.dim, cursor: 'pointer', padding: 0 }}>
            <X size={12} />
          </button>
        )}
      </div>

      {/* ── Meaning Arc Feed ── */}
      {activeFace && meaningArcs.length > 0 ? (
        <div>
          {meaningArcs.map((arc, ai) => {
            const startIdx = meaningArcs.slice(0, ai).reduce((s, a) => s + a.items.length, 0)
            return (
              <div key={arc.label} style={{ marginBottom: 24 }}>
                <ArcDivider label={arc.label} tier={arc.tier} color={activeFace.color} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {arc.items.map(({ scroll, score }, i) => (
                    <ScrollCard key={scroll.id} scroll={scroll} score={score} faceColor={activeFace.color} idx={startIdx + i} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {scoredScrolls.length === 0 ? (
            <Empty>{search ? 'No scrolls match this query.' : 'Corpus is empty.'}</Empty>
          ) : (
            scoredScrolls.map(({ scroll, score }, i) => (
              <ScrollCard key={scroll.id} scroll={scroll} score={score} faceColor='#C9A84C' idx={i} />
            ))
          )}
        </div>
      )}

      {/* ── Open Loops ── */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.16), transparent)' }} />
          <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.32em', textTransform: 'uppercase', color: 'rgba(239,68,68,0.32)', whiteSpace: 'nowrap' }}>
            Open Loops
          </span>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.16), transparent)' }} />
        </div>
        <CompactLoopsPanel />
      </div>

      {/* ── End of transmission ── */}
      {scoredScrolls.length > 0 && (
        <motion.p
          animate={{ opacity: [0.15, 0.4, 0.15] }}
          transition={{ duration: 6, repeat: Infinity }}
          style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.5em', textTransform: 'uppercase', color: COLORS.dim, margin: '4px 0 0' }}
        >
          ⟐ End of Transmission · {scoredScrolls.length} scrolls ⟐
        </motion.p>
      )}
    </div>
  )
}
