/**
 * ReasoMateSurface — the private ReasoMate lens inside NovaNet.
 *
 * ReasoMate is the authenticated conversational messenger layer: a lens over
 * the existing Arkana conversational runtime and the existing private
 * cross-user message substrate.
 *
 * It is NOT a second chatbot, memory system, identity system, or database:
 *   - the Arkana thread uses the canonical Oracle spine, so its session_id is
 *     the shared arkana-{uid} key and it reads/writes the SAME Knowledge OS
 *     thread as Oracle Chat (see lib/arkanaSession.ts);
 *   - direct threads use the canonical authenticated /api/messages substrate.
 *
 * Mounted by BOTH the /reasomate route and the NovaNet hub tab so the two
 * entry points cannot drift apart into different surfaces.
 */
import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import ArkanaCommune from './ArkanaCommune'
import SocialMessenger from '../pages/SocialMessenger'

const C = {
  teal: '#00D4AA',
  blue: '#6A9FD8',
  gold: '#C9A84C',
  text: 'rgba(232,232,232,.9)',
  dim: 'rgba(232,232,232,.35)',
}

type Lens = 'arkana' | 'direct'

const LENSES: { id: Lens; label: string; sub: string }[] = [
  { id: 'arkana', label: 'Arkana', sub: 'Shared conversation · Knowledge OS memory' },
  { id: 'direct', label: 'Direct threads', sub: 'Private node-to-node messages' },
]

function lensButton(active: boolean): React.CSSProperties {
  return {
    padding: '8px 13px',
    background: active ? 'rgba(0,212,170,.10)' : 'rgba(255,255,255,.03)',
    border: `1px solid ${active ? 'rgba(0,212,170,.35)' : 'rgba(255,255,255,.08)'}`,
    borderRadius: 9,
    color: active ? C.teal : C.dim,
    cursor: 'pointer',
    textAlign: 'left',
  }
}

export default function ReasoMateSurface() {
  const { isAuthenticated } = useAuth()
  const [lens, setLens] = useState<Lens>('arkana')

  if (!isAuthenticated) {
    return (
      <div style={{ minHeight: 420, display: 'grid', placeItems: 'center', padding: 32, textAlign: 'center' }}>
        <div>
          <span style={{ fontSize: 30 }}>🔐</span>
          <h3 style={{ fontFamily: 'Cinzel, serif', fontSize: 16, color: C.gold, margin: '10px 0 6px' }}>Private Messenger</h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: C.dim, lineHeight: 1.7, margin: 0, maxWidth: 300 }}>
            The Arkana thread and private node-to-node messages require node authentication.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div data-testid="reasomate-private-surface" style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 160px)' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <span style={{ color: C.blue, fontSize: 20 }}>✧</span>
        <div>
          <h2 style={{ margin: 0, fontFamily: 'Cinzel, serif', fontSize: 20, color: C.blue }}>ReasoMate</h2>
          <div style={{ color: C.dim, fontSize: 9 }}>Private messenger · Arkana conversation · not the public field</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 5 }}>
          {LENSES.map(item => (
            <button key={item.id} type="button" onClick={() => setLens(item.id)} aria-current={lens === item.id ? 'true' : undefined} style={lensButton(lens === item.id)}>
              <span style={{ display: 'block', fontSize: 10, letterSpacing: '.14em', textTransform: 'uppercase' }}>{item.label}</span>
              <span style={{ display: 'block', fontSize: 8, opacity: .7 }}>{item.sub}</span>
            </button>
          ))}
        </div>
      </header>

      {lens === 'arkana' ? <ArkanaCommune /> : <SocialMessenger />}
    </div>
  )
}