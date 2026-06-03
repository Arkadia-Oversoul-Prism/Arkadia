import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { api, OpenLoopsResponse } from '../lib/dashboardApi'

const C = {
  teal:   '#00D4AA',
  gold:   '#C9A84C',
  purple: '#B08DE8',
  red:    '#C84848',
  muted:  'rgba(232,232,232,0.5)',
  dim:    'rgba(232,232,232,0.28)',
  text:   'rgba(232,232,232,0.85)',
}

const LEVEL_COLORS: Record<string, string> = {
  CRITICAL:  '#C84848',
  HIGH:      '#E88C6A',
  MEDIUM:    '#C9A84C',
  LOW:       '#00D4AA',
  SYSTEM:    '#B08DE8',
}

export default function OpenLoopsPage() {
  const { data, isLoading, error, refetch, isFetching } = useQuery<OpenLoopsResponse>({
    queryKey: ['open-loops-standalone'],
    queryFn: api.openLoops,
    refetchInterval: 60_000,
  })

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${C.teal}55`, margin: '0 0 4px' }}>
            Arkadia / Open Loops
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: 28, color: '#E8E8E8', margin: 0, letterSpacing: '0.04em' }}>
            Open Loops
          </h1>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, padding: '7px 14px', background: `${C.teal}07`, border: `1px solid ${C.teal}20`, borderRadius: 8, color: `${C.teal}70`, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: isFetching ? 'wait' : 'pointer' }}
        >
          <motion.span animate={isFetching ? { rotate: 360 } : {}} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>⟳</motion.span>
          Sync
        </button>
      </div>

      {isLoading && (
        <div style={{ padding: '60px 20px', textAlign: 'center' }}>
          <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ repeat: Infinity, duration: 2 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.28em', textTransform: 'uppercase', color: `${C.teal}50` }}>
              Loading loops…
            </p>
          </motion.div>
        </div>
      )}

      {error && (
        <div style={{ padding: '24px', background: 'rgba(200,72,72,0.04)', border: '1px solid rgba(200,72,72,0.15)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(200,72,72,0.7)', margin: 0 }}>
            Could not load open loops from the backend.
          </p>
        </div>
      )}

      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Summary bar */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', padding: '12px 16px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.08)', borderRadius: 10 }}>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: `${C.teal}60` }}>
              {data.total} open loops
            </span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.12em', color: 'rgba(232,232,232,0.2)' }}>·</span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.12em', color: 'rgba(232,232,232,0.3)' }}>
              {data.source}
            </span>
          </div>

          {/* Loop groups */}
          {data.groups.map((group, gi) => {
            const color = LEVEL_COLORS[group.level] ?? C.gold
            return (
              <motion.div
                key={group.level}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: gi * 0.07 }}
              >
                {/* Group header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}60` }} />
                  <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase', color, margin: 0 }}>
                    {group.section_title || group.label}
                  </p>
                  <div style={{ flex: 1, height: 1, background: `${color}18` }} />
                  <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: `${color}50` }}>{group.loops.length}</span>
                </div>

                {/* Loops */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingLeft: 18 }}>
                  {group.loops.map((loop, li) => (
                    <motion.div
                      key={loop.id}
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: gi * 0.07 + li * 0.03 }}
                      style={{ padding: '14px 16px', background: `${color}05`, border: `1px solid ${color}15`, borderLeft: `2px solid ${color}50`, borderRadius: '0 10px 10px 0' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: loop.next_action ? 8 : 0 }}>
                        <p style={{ fontFamily: 'sans-serif', fontSize: 12.5, color: C.text, margin: 0, lineHeight: 1.4, fontWeight: 500 }}>
                          {loop.name}
                        </p>
                        {loop.target && (
                          <span style={{ flexShrink: 0, padding: '2px 8px', background: `${color}10`, border: `1px solid ${color}25`, borderRadius: 6, fontFamily: 'ui-monospace, monospace', fontSize: 8, color: `${color}80`, whiteSpace: 'nowrap' }}>
                            {loop.target}
                          </span>
                        )}
                      </div>
                      {loop.next_action && (
                        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.muted, margin: 0, lineHeight: 1.55 }}>
                          → {loop.next_action}
                        </p>
                      )}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
