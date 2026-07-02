import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = import.meta.env.VITE_API_URL ?? ''
const AUDIO_SRC = `${API_BASE}/static/coherence-meditation.mp3`
const TOTAL = 442 // 7:22

// ── Lyric types ───────────────────────────────────────────────────────────────
type LT = 'normal' | 'breath' | 'affirmation' | 'count'
interface Line { t: number; text: string; type?: LT }

// ── Full script with timestamps ───────────────────────────────────────────────
// Timestamps calibrated to the 7:22 audio. Adjust by editing the `t` values.
const SCRIPT: Line[] = [
  // ── ARRIVAL (0–26s) ──────────────────────────────────────────────────────
  { t: 0,   text: 'Welcome.' },
  { t: 4,   text: 'For the next few minutes, allow yourself to pause.' },
  { t: 11,  text: 'There is nothing to solve.' },
  { t: 15,  text: 'Nothing to chase.' },
  { t: 18,  text: 'Nothing to force.' },
  { t: 21,  text: 'Simply arrive here.' },

  // ── FIRST BREATHING (27–76s) ─────────────────────────────────────────────
  { t: 27,  text: 'Take a slow breath in...', type: 'breath' },
  { t: 35,  text: 'And a longer breath out.', type: 'breath' },
  { t: 44,  text: 'Again.' },
  { t: 48,  text: 'Inhale gently...', type: 'breath' },
  { t: 55,  text: 'Exhale completely.', type: 'breath' },
  { t: 63,  text: 'One more time.' },
  { t: 67,  text: 'Breathing in...', type: 'breath' },
  { t: 74,  text: 'And breathing out.', type: 'breath' },

  // ── BODY (80–110s) ───────────────────────────────────────────────────────
  { t: 82,  text: 'Allow your shoulders to soften.' },
  { t: 87,  text: 'Relax your jaw.' },
  { t: 91,  text: 'Unclench your hands.' },
  { t: 95,  text: 'Let your body know that, for this moment, it is safe to slow down.' },

  // ── REGULATION INSIGHT (103–142s) ────────────────────────────────────────
  { t: 103, text: 'When we are stressed, financial decisions feel heavy.' },
  { t: 109, text: 'We hesitate.' },
  { t: 112, text: 'We overthink.' },
  { t: 115, text: 'We delay.' },
  { t: 118, text: 'We question our value.' },
  { t: 122, text: 'But when we are regulated, decisions become simpler.' },
  { t: 128, text: 'Action becomes easier.' },
  { t: 132, text: 'Receiving becomes natural.' },
  { t: 136, text: 'Today, we begin with regulation.' },

  // ── SECOND BREATHING (142–186s) ──────────────────────────────────────────
  { t: 142, text: 'Take a slow breath in.', type: 'breath' },
  { t: 149, text: 'And an even slower breath out.', type: 'breath' },
  { t: 158, text: 'Again.' },
  { t: 162, text: 'Inhale.', type: 'breath' },
  { t: 169, text: 'Exhale.', type: 'breath' },
  { t: 177, text: 'Allow each exhale to be longer than the inhale.' },
  { t: 183, text: 'With every breath out, release what you no longer need to carry.' },

  // ── RELEASE (191–230s) ───────────────────────────────────────────────────
  { t: 191, text: 'Quietly repeat:' },
  { t: 196, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },
  { t: 205, text: 'Again.' },
  { t: 209, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },
  { t: 218, text: 'And once more.' },
  { t: 222, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },

  // ── LIGHTENING (231–256s) ─────────────────────────────────────────────────
  { t: 231, text: 'Feel your body becoming lighter.' },
  { t: 237, text: 'Your mind becoming clearer.' },
  { t: 242, text: 'Your breathing becoming steadier.' },

  // ── HAND + VALUE AFFIRMATIONS (248–310s) ──────────────────────────────────
  { t: 248, text: 'Now place one hand gently over your upper abdomen.' },
  { t: 255, text: 'Feel the warmth of your own presence.' },
  { t: 260, text: 'Feel yourself here.' },
  { t: 266, text: 'And slowly repeat:' },
  { t: 271, text: 'My work creates value.', type: 'affirmation' },
  { t: 278, text: 'My work creates value.', type: 'affirmation' },
  { t: 284, text: 'My actions create movement.', type: 'affirmation' },
  { t: 291, text: 'My actions create movement.', type: 'affirmation' },
  { t: 297, text: 'I am allowed to be paid.', type: 'affirmation' },
  { t: 304, text: 'I am allowed to be paid.', type: 'affirmation' },

  // ── RECOGNITION (311–345s) ────────────────────────────────────────────────
  { t: 311, text: 'There is no force here.' },
  { t: 316, text: 'No proving.' },
  { t: 319, text: 'No chasing.' },
  { t: 322, text: 'Simply recognition.' },
  { t: 327, text: 'Your work creates value.' },
  { t: 332, text: 'Your actions create movement.' },
  { t: 337, text: 'And movement creates opportunity.' },

  // ── POSTURE + CERTAINTY (342–360s) ────────────────────────────────────────
  { t: 342, text: 'Take a deeper breath now.', type: 'breath' },
  { t: 349, text: 'Feel your posture rise naturally.' },
  { t: 354, text: 'Not from effort.' },
  { t: 357, text: 'From certainty.' },

  // ── RECEIVING (361–372s) ──────────────────────────────────────────────────
  { t: 361, text: 'Now we enter the final phase.' },
  { t: 367, text: 'Receiving.' },

  // ── BOX BREATHING ROUND 1 (372–390s) ─────────────────────────────────────
  { t: 372, text: 'Breathe in for four.', type: 'breath' },
  { t: 375, text: 'Two...', type: 'count' },
  { t: 377, text: 'Three...', type: 'count' },
  { t: 379, text: 'Four...', type: 'count' },
  { t: 381, text: 'Hold.', type: 'breath' },
  { t: 383, text: 'Two.', type: 'count' },
  { t: 385, text: 'And exhale.', type: 'breath' },
  { t: 387, text: 'Two...', type: 'count' },
  { t: 389, text: 'Three...', type: 'count' },
  { t: 391, text: 'Four...', type: 'count' },
  { t: 393, text: 'Five...', type: 'count' },
  { t: 395, text: 'Six.', type: 'count' },

  // ── ROUND 2 (397–412s) ───────────────────────────────────────────────────
  { t: 397, text: 'Again.' },
  { t: 400, text: 'Inhale.', type: 'breath' },
  { t: 402, text: 'Two...', type: 'count' },
  { t: 404, text: 'Three...', type: 'count' },
  { t: 406, text: 'Four.', type: 'count' },
  { t: 408, text: 'Hold.', type: 'breath' },
  { t: 410, text: 'Two.', type: 'count' },
  { t: 412, text: 'Exhale.', type: 'breath' },
  { t: 414, text: 'Two...', type: 'count' },
  { t: 416, text: 'Three...', type: 'count' },
  { t: 418, text: 'Four...', type: 'count' },
  { t: 420, text: 'Five...', type: 'count' },
  { t: 422, text: 'Six.', type: 'count' },

  // ── ROUND 3 (424–438s) ───────────────────────────────────────────────────
  { t: 424, text: 'One final round.' },
  { t: 427, text: 'Inhale.', type: 'breath' },
  { t: 429, text: 'Two...', type: 'count' },
  { t: 431, text: 'Three...', type: 'count' },
  { t: 433, text: 'Four.', type: 'count' },
  { t: 435, text: 'Hold.', type: 'breath' },
  { t: 437, text: 'Two.', type: 'count' },
  { t: 438, text: 'Exhale.', type: 'breath' },
  { t: 439, text: 'Two...', type: 'count' },
  { t: 440, text: 'Three...', type: 'count' },
  { t: 441, text: 'Four...', type: 'count' },
  { t: 442, text: 'Five...', type: 'count' },
  { t: 443, text: 'Six.', type: 'count' },
]

// ── Closing lines shown after box breathing ───────────────────────────────────
// These have their own section since they're the denouement
const CLOSING: Line[] = [
  { t: 446, text: 'Good.' },
  { t: 449, text: 'Notice the calm that is available when you stop fighting yourself.' },
  { t: 454, text: 'Notice the clarity that appears when pressure leaves.' },
  { t: 458, text: 'Notice the space that opens when you trust your own value.' },
  { t: 463, text: 'Remember this:' },
  { t: 466, text: 'Self-belief creates action.' },
  { t: 469, text: 'Action creates receiving.' },
  { t: 472, text: 'Receiving strengthens self-belief.' },
  { t: 476, text: 'The cycle continues.' },
  { t: 479, text: 'If momentum feels slow today, keep it simple.' },
  { t: 483, text: 'One message.' },
  { t: 485, text: 'One offer.' },
  { t: 487, text: 'One post.' },
  { t: 489, text: 'One conversation.' },
  { t: 491, text: 'One action.' },
  { t: 493, text: 'Movement creates momentum.' },
  { t: 496, text: 'Momentum creates opportunity.' },
  { t: 499, text: 'And opportunity grows through consistent action.' },
  { t: 503, text: 'Take one final breath in.', type: 'breath' },
  { t: 508, text: 'And slowly let it go.', type: 'breath' },
  { t: 514, text: 'As we close, repeat softly:' },
  { t: 518, text: 'I move.', type: 'affirmation' },
  { t: 523, text: 'Money moves with me.', type: 'affirmation' },
  { t: 528, text: 'Again.' },
  { t: 531, text: 'I move.', type: 'affirmation' },
  { t: 535, text: 'Money moves with me.', type: 'affirmation' },
  { t: 540, text: 'One last time.' },
  { t: 543, text: 'I move.', type: 'affirmation' },
  { t: 547, text: 'Money moves with me.', type: 'affirmation' },
  { t: 553, text: 'Carry this feeling with you.' },
  { t: 557, text: 'Clear.' },
  { t: 560, text: 'Grounded.' },
  { t: 563, text: 'Open.' },
  { t: 566, text: 'Ready to act.' },
  { t: 569, text: 'Ready to receive.' },
  { t: 572, text: 'And ready to move forward.' },
  { t: 578, text: 'When you are ready, gently open your eyes.' },
  { t: 584, text: 'And begin.' },
]

const ALL_LINES = [...SCRIPT, ...CLOSING]

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${String(sec).padStart(2, '0')}`
}

function activeIndex(t: number) {
  let idx = 0
  for (let i = 0; i < ALL_LINES.length; i++) {
    if (ALL_LINES[i].t <= t) idx = i
    else break
  }
  return idx
}

// ── Per-line colour / size based on distance from active ─────────────────────
function lineStyle(dist: number, type?: LT) {
  const isBefore = dist < 0
  const isActive = dist === 0
  const isNear   = Math.abs(dist) === 1
  const isFar    = Math.abs(dist) === 2

  let color = '#ffffff'
  if (type === 'breath')      color = '#00D4AA'
  if (type === 'affirmation') color = '#C9A84C'
  if (type === 'count')       color = '#B08DE8'

  const opacity = isActive ? 1 : isNear ? (isBefore ? 0.28 : 0.22) : isFar ? (isBefore ? 0.12 : 0.10) : 0.06
  const scale   = isActive ? 1 : isNear ? 0.88 : 0.78
  const blur    = isActive ? 0 : isNear ? 0 : 2

  let fontSize = 22
  if (type === 'count' && isActive) fontSize = 28
  if (!isActive) fontSize = isNear ? 16 : 13

  return { color, opacity, scale, blur, fontSize }
}

// ── Breathing ring behind active breath lines ─────────────────────────────────
function BreathRing({ active, type }: { active: boolean; type?: LT }) {
  if (!active || (type !== 'breath' && type !== 'affirmation')) return null
  const col = type === 'affirmation' ? '#C9A84C' : '#00D4AA'
  return (
    <motion.div
      key={type}
      initial={{ opacity: 0, scale: 0.6 }}
      animate={{ opacity: [0, 0.12, 0], scale: [0.8, 2.4, 2.4] }}
      transition={{ duration: 3.5, repeat: Infinity, ease: 'easeOut' }}
      style={{
        position: 'absolute', borderRadius: '50%',
        width: 280, height: 280,
        left: '50%', top: '50%',
        transform: 'translate(-50%, -50%)',
        border: `1px solid ${col}`,
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  )
}

// ── Main player ───────────────────────────────────────────────────────────────
function Player({ onClose }: { onClose: () => void }) {
  const audioRef    = useRef<HTMLAudioElement>(null)
  const scrollRef   = useRef<HTMLDivElement>(null)
  const lineRefs    = useRef<(HTMLDivElement | null)[]>([])
  const [time, setTime]       = useState(0)
  const [dur,  setDur]        = useState(TOTAL)
  const [playing, setPlaying] = useState(false)
  const [loaded, setLoaded]   = useState<boolean | 'error'>(false)
  const [dragging, setDragging] = useState(false)

  const idx = activeIndex(time)
  const activeLine = ALL_LINES[idx]

  // ── Audio events ─────────────────────────────────────────────────────────
  useEffect(() => {
    const el = audioRef.current
    if (!el) return
    const onTime  = () => { if (!dragging) setTime(el.currentTime) }
    const onMeta  = () => setDur(el.duration || TOTAL)
    const onPlay  = () => setPlaying(true)
    const onPause = () => setPlaying(false)
    const onLoad  = () => setLoaded(true)
    const onErr   = () => setLoaded('error')
    el.addEventListener('timeupdate', onTime)
    el.addEventListener('loadedmetadata', onMeta)
    el.addEventListener('play',  onPlay)
    el.addEventListener('pause', onPause)
    el.addEventListener('canplaythrough', onLoad)
    el.addEventListener('error', onErr)
    return () => {
      el.removeEventListener('timeupdate', onTime)
      el.removeEventListener('loadedmetadata', onMeta)
      el.removeEventListener('play',  onPlay)
      el.removeEventListener('pause', onPause)
      el.removeEventListener('canplaythrough', onLoad)
      el.removeEventListener('error', onErr)
    }
  }, [dragging])

  // ── Scroll active line into center ────────────────────────────────────────
  useEffect(() => {
    const container = scrollRef.current
    const el = lineRefs.current[idx]
    if (!container || !el) return
    const containerH = container.clientHeight
    const elTop = el.offsetTop
    const elH   = el.offsetHeight
    const target = elTop - containerH / 2 + elH / 2
    container.scrollTo({ top: target, behavior: 'smooth' })
  }, [idx])

  const togglePlay = useCallback(() => {
    const el = audioRef.current
    if (!el) return
    if (el.paused) el.play()
    else el.pause()
  }, [])

  const seek = useCallback((frac: number) => {
    const el = audioRef.current
    const t = frac * dur
    setTime(t)
    if (el) el.currentTime = t
  }, [dur])

  const progressPct = dur > 0 ? (time / dur) * 100 : 0

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: '#050508',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Hidden audio */}
      <audio ref={audioRef} src={AUDIO_SRC} preload="auto" />

      {/* Ambient radial glow — changes with line type */}
      <motion.div
        animate={{
          background: activeLine?.type === 'affirmation'
            ? 'radial-gradient(ellipse 60% 40% at 50% 52%, rgba(201,168,76,0.07) 0%, transparent 70%)'
            : activeLine?.type === 'breath'
            ? 'radial-gradient(ellipse 60% 40% at 50% 52%, rgba(0,212,170,0.07) 0%, transparent 70%)'
            : activeLine?.type === 'count'
            ? 'radial-gradient(ellipse 60% 40% at 50% 52%, rgba(176,141,232,0.06) 0%, transparent 70%)'
            : 'radial-gradient(ellipse 60% 40% at 50% 52%, rgba(232,232,232,0.025) 0%, transparent 70%)',
        }}
        transition={{ duration: 1.8 }}
        style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0 }}
      />

      {/* Close */}
      <button
        onClick={onClose}
        style={{
          position: 'absolute', top: 20, left: 20, zIndex: 10,
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'rgba(232,232,232,0.2)', fontSize: 18, padding: 8,
          lineHeight: 1, transition: 'color 0.2s',
        }}
        onMouseEnter={e => (e.currentTarget.style.color = 'rgba(232,232,232,0.6)')}
        onMouseLeave={e => (e.currentTarget.style.color = 'rgba(232,232,232,0.2)')}
      >
        ✕
      </button>

      {/* Top badge */}
      <div style={{
        position: 'absolute', top: 22, left: '50%', transform: 'translateX(-50%)',
        zIndex: 10, display: 'flex', alignItems: 'center', gap: 7,
      }}>
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: playing ? 2 : 99, repeat: Infinity }}
          style={{ width: 5, height: 5, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 6px #00D4AA' }}
        />
        <span style={{ fontFamily: 'monospace', fontSize: 8.5, letterSpacing: '0.32em', color: 'rgba(232,232,232,0.22)', textTransform: 'uppercase' }}>
          COHERENCE RESET · ARK SESSION
        </span>
      </div>

      {/* Lyrics scroll area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          paddingTop: 'calc(50vh - 60px)',
          paddingBottom: 'calc(50vh - 60px)',
          scrollbarWidth: 'none',
          position: 'relative', zIndex: 1,
          WebkitOverflowScrolling: 'touch',
        }}
        className="hide-scrollbar"
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
          {ALL_LINES.map((line, i) => {
            const dist = i - idx
            const { color, opacity, scale, blur, fontSize } = lineStyle(dist, line.type)
            const isActive = dist === 0

            return (
              <div
                key={i}
                ref={el => { lineRefs.current[i] = el }}
                style={{
                  position: 'relative',
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'center',
                  padding: isActive ? '8px 24px' : '5px 24px',
                }}
              >
                {/* Breathing ring for active breath/affirmation lines */}
                {isActive && (
                  <BreathRing active={isActive} type={line.type} />
                )}

                <motion.p
                  animate={{ opacity, scale, filter: `blur(${blur}px)` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                  style={{
                    fontFamily: line.type === 'count' ? 'ui-monospace, monospace' : 'serif',
                    fontSize,
                    color,
                    textAlign: 'center',
                    margin: 0,
                    lineHeight: isActive ? 1.3 : 1.2,
                    letterSpacing: line.type === 'count' ? '0.18em' : isActive ? '0.04em' : '0.02em',
                    maxWidth: 520,
                    transition: 'font-size 0.4s ease, color 0.6s ease',
                    cursor: 'default',
                    userSelect: 'none',
                    position: 'relative', zIndex: 2,
                  }}
                >
                  {isActive && line.type === 'affirmation' && (
                    <motion.span
                      animate={{ opacity: [0, 0.4, 0] }}
                      transition={{ duration: 2.5, repeat: Infinity }}
                      style={{ position: 'absolute', left: -20, top: '50%', transform: 'translateY(-50%)', color, fontSize: 8 }}
                    >✦</motion.span>
                  )}
                  {line.text}
                </motion.p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Audio unavailable notice */}
      <AnimatePresence>
        {loaded === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'absolute', bottom: 120, left: '50%', transform: 'translateX(-50%)',
              fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.2em', color: 'rgba(232,232,232,0.18)',
              textTransform: 'uppercase', textAlign: 'center', zIndex: 10, whiteSpace: 'nowrap',
            }}
          >
            Audio file not found · Add coherence-meditation.mp3 to /static/
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Bottom controls ──────────────────────────────────────────────── */}
      <div style={{
        flexShrink: 0, zIndex: 10,
        padding: '0 0 24px',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
      }}>
        {/* Progress bar */}
        <div
          style={{ width: '80%', maxWidth: 420, cursor: 'pointer', padding: '8px 0' }}
          onClick={e => {
            const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
            seek((e.clientX - rect.left) / rect.width)
          }}
        >
          <div style={{ height: 2, background: 'rgba(255,255,255,0.07)', borderRadius: 1, position: 'relative', overflow: 'visible' }}>
            <motion.div
              animate={{ width: `${progressPct}%` }}
              transition={{ duration: 0.3, ease: 'linear' }}
              style={{
                height: '100%', borderRadius: 1,
                background: activeLine?.type === 'affirmation' ? '#C9A84C'
                  : activeLine?.type === 'breath' ? '#00D4AA'
                  : activeLine?.type === 'count' ? '#B08DE8'
                  : 'rgba(232,232,232,0.55)',
                transition: 'background 1s ease',
              }}
            />
          </div>
          {/* Time stamps */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
            <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.2)' }}>
              {fmtTime(time)}
            </span>
            <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.2)' }}>
              {fmtTime(dur)}
            </span>
          </div>
        </div>

        {/* Play / pause */}
        <motion.button
          onClick={togglePlay}
          whileTap={{ scale: 0.92 }}
          style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(232,232,232,0.8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', fontSize: 18,
          }}
        >
          {playing ? (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="3" y="2" width="4" height="12" rx="1"/>
              <rect x="9" y="2" width="4" height="12" rx="1"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 2.5l10 5.5-10 5.5V2.5z"/>
            </svg>
          )}
        </motion.button>
      </div>
    </motion.div>
  )
}

// ── Start screen ──────────────────────────────────────────────────────────────
function StartScreen({ onBegin }: { onBegin: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.7 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', minHeight: '60vh',
        textAlign: 'center', gap: 0,
      }}
    >
      {/* Pulsing sigil */}
      <motion.div
        animate={{ opacity: [0.3, 0.7, 0.3], scale: [0.98, 1.02, 0.98] }}
        transition={{ duration: 4, repeat: Infinity }}
        style={{ fontFamily: 'serif', fontSize: 36, color: '#00D4AA', marginBottom: 24, lineHeight: 1 }}
      >
        ◎
      </motion.div>

      <p style={{ fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 12px' }}>
        Arkadia · Field Calibration
      </p>

      <h1 style={{ fontFamily: 'serif', fontSize: 34, color: '#EAEAEA', margin: '0 0 14px', letterSpacing: '0.04em' }}>
        Coherence Reset
      </h1>

      <p style={{ fontFamily: 'sans-serif', fontSize: 13.5, color: 'rgba(232,232,232,0.38)', margin: '0 0 48px', maxWidth: 320, lineHeight: 1.7 }}>
        A 7-minute guided calibration session.<br />
        Find a quiet place. Use headphones if you can.
      </p>

      {/* Duration + details */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 48, flexWrap: 'wrap', justifyContent: 'center' }}>
        {[['7:22', 'Duration'], ['3', 'Breath Rounds'], ['Regulation', 'Focus']].map(([val, label]) => (
          <div key={label} style={{ textAlign: 'center' }}>
            <p style={{ fontFamily: 'serif', fontSize: 20, color: '#00D4AA', margin: '0 0 3px' }}>{val}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.25)', margin: 0, letterSpacing: '0.18em', textTransform: 'uppercase' }}>{label}</p>
          </div>
        ))}
      </div>

      <motion.button
        onClick={onBegin}
        whileTap={{ scale: 0.97 }}
        style={{
          padding: '14px 40px',
          background: 'rgba(0,212,170,0.07)',
          border: '1px solid rgba(0,212,170,0.3)',
          borderRadius: 50,
          color: '#00D4AA',
          fontFamily: 'serif',
          fontSize: 13,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          cursor: 'pointer',
          transition: 'all 0.22s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = 'rgba(0,212,170,0.14)'
          e.currentTarget.style.borderColor = 'rgba(0,212,170,0.6)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = 'rgba(0,212,170,0.07)'
          e.currentTarget.style.borderColor = 'rgba(0,212,170,0.3)'
        }}
      >
        Begin Session
      </motion.button>

      <p style={{ fontFamily: 'monospace', fontSize: 8, color: 'rgba(232,232,232,0.1)', letterSpacing: '0.18em', marginTop: 32, textTransform: 'uppercase' }}>
        Breathe. Regulate. Receive.
      </p>
    </motion.div>
  )
}

// ── Root export ───────────────────────────────────────────────────────────────
export default function CoherenceReset() {
  const [active, setActive] = useState(false)

  return (
    <div>
      <AnimatePresence mode="wait">
        {active ? (
          <Player key="player" onClose={() => setActive(false)} />
        ) : (
          <StartScreen key="start" onBegin={() => setActive(true)} />
        )}
      </AnimatePresence>
    </div>
  )
}
