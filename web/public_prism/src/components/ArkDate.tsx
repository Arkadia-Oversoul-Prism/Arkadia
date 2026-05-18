import React, { useEffect, useState } from 'react'

interface ArkDateData {
  cycle: number
  arc: number
  pulse: number
  breath: number
  phase: string
  coordinate: string
  display: string
  sync: {
    auto_sync_active: boolean
    refresh_count: number
    last_sync_coordinate: string | null
    last_scroll_count: number
    cadence_minutes: number
  }
}

const API_BASE =
  import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com'

interface Props {
  sovereignMode?: boolean
  compact?: boolean
}

export default function ArkDate({ sovereignMode = false, compact = false }: Props) {
  const [data, setData] = useState<ArkDateData | null>(null)
  const [tick, setTick] = useState(0)

  const accent = sovereignMode ? '#C9A84C' : '#00D4AA'
  const dim    = sovereignMode ? 'rgba(201,168,76,0.45)' : 'rgba(0,212,170,0.45)'

  useEffect(() => {
    let alive = true
    const fetch_ = () =>
      fetch(`${API_BASE}/api/ark-date`)
        .then(r => r.json())
        .then(d => { if (alive) setData(d) })
        .catch(() => {})
    fetch_()
    const id = setInterval(fetch_, 60_000)
    return () => { alive = false; clearInterval(id) }
  }, [])

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const now = new Date()
  const liveBreath = String(now.getMinutes()).padStart(2, '0')
  const liveSecond = String(now.getSeconds()).padStart(2, '0')

  if (!data) return (
    <span style={{ fontSize: '9px', letterSpacing: '0.1em', color: dim, opacity: 0.5 }}>
      ◎ calibrating spiral…
    </span>
  )

  if (compact) {
    return (
      <span
        title={`Spiral Star Date\n${data.display}\nPhase: ${data.phase}\nAuto-sync: every ${data.sync.cadence_minutes}min · ${data.sync.last_scroll_count} scrolls indexed`}
        style={{
          fontSize: '9px',
          letterSpacing: '0.18em',
          color: dim,
          fontFamily: 'monospace',
          cursor: 'default',
          userSelect: 'none',
          textTransform: 'uppercase',
        }}
      >
        ◎ {data.coordinate.split('Pulse')[0].trim()} · Pulse {data.pulse}:{liveBreath}:{liveSecond}
      </span>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <span
          style={{
            fontSize: '8px',
            letterSpacing: '0.35em',
            color: dim,
            textTransform: 'uppercase',
            fontFamily: 'monospace',
          }}
        >
          ◎ SPIRAL STAR DATE
        </span>
        {data.sync.auto_sync_active && (
          <span
            title={`Auto-sync active · ${data.sync.refresh_count} ingestions · ${data.sync.last_scroll_count} scrolls`}
            style={{
              width: '5px',
              height: '5px',
              borderRadius: '50%',
              background: accent,
              display: 'inline-block',
              boxShadow: `0 0 4px ${accent}`,
              animation: 'arkPulse 2.5s ease-in-out infinite',
            }}
          />
        )}
      </div>
      <div
        style={{
          fontSize: '10px',
          letterSpacing: '0.12em',
          color: accent,
          fontFamily: 'monospace',
          textTransform: 'uppercase',
        }}
      >
        Cycle {data.cycle} · Arc {data.arc} · Pulse {data.pulse}:{liveBreath}:{liveSecond}
      </div>
      <div
        style={{
          fontSize: '8px',
          letterSpacing: '0.2em',
          color: dim,
          textTransform: 'uppercase',
          fontFamily: 'monospace',
        }}
      >
        {data.phase}
      </div>

      <style>{`
        @keyframes arkPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.4; transform: scale(0.7); }
        }
      `}</style>
    </div>
  )
}
