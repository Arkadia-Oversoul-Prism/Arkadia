import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { API_BASE } from '../lib/apiConfig'

const C = {
  gold: '#C9A84C', teal: '#00D4AA', blue: '#6A9FD8', purple: '#B08DE8',
  text: 'rgba(232,232,232,0.9)', muted: 'rgba(232,232,232,0.58)', dim: 'rgba(232,232,232,0.3)',
  card: 'rgba(14,17,32,0.78)', border: 'rgba(0,212,170,0.12)',
}

type NodeProfile = {
  username?: string | null
  handle?: string | null
  display_name: string
  bio?: string | null
  avatar_url?: string | null
}

type DM = { id: string; sender_uid: string; recipient_uid: string; content: string; timestamp: number }
type Relationship = {
  participants: NodeProfile[]
  interaction_count: number
  first_interaction_at: number | null
  last_interaction_at: number | null
  shared_memory_source: string
  memory_policy: string
}

const fallbackAvatar = (name: string) => (name || 'N').trim().slice(0, 1).toUpperCase()
const ago = (ts: number) => {
  const d = Date.now() - ts
  if (d < 60_000) return 'now'
  if (d < 3_600_000) return `${Math.floor(d / 60_000)}m`
  if (d < 86_400_000) return `${Math.floor(d / 3_600_000)}h`
  return `${Math.floor(d / 86_400_000)}d`
}

function Avatar({ node, size = 42 }: { node: NodeProfile; size?: number }) {
  return node.avatar_url ? (
    <img src={node.avatar_url} alt="" style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', border: `1px solid ${C.teal}35` }} />
  ) : (
    <div style={{ width: size, height: size, borderRadius: '50%', display: 'grid', placeItems: 'center', background: 'rgba(0,212,170,0.08)', border: `1px solid ${C.teal}25`, color: C.teal, fontFamily: 'sans-serif', fontWeight: 700 }}>
      {fallbackAvatar(node.display_name)}
    </div>
  )
}

export default function ReasoMateField() {
  const { isAuthenticated, profile, user } = useAuth()
  const [nodes, setNodes] = useState<NodeProfile[]>([])
  const [query, setQuery] = useState('')
  const [active, setActive] = useState<NodeProfile | null>(null)
  const [peerUid, setPeerUid] = useState<string | null>(null)
  const [thread, setThread] = useState<DM[]>([])
  const [relationship, setRelationship] = useState<Relationship | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const authHeaders = useMemo(() => user?.idToken ? { Authorization: `Bearer ${user.idToken}` } : {}, [user?.idToken])

  const discover = useCallback(async (q = '') => {
    if (!user?.idToken) return
    setBusy(true); setError('')
    try {
      const res = await fetch(`${API_BASE}/api/social/nodes?q=${encodeURIComponent(q)}&limit=40`, { headers: authHeaders })
      if (!res.ok) throw new Error(`Node discovery failed (${res.status})`)
      const data = await res.json()
      setNodes(data.nodes || [])
    } catch (e) { setError((e as Error).message || 'Node discovery failed') }
    finally { setBusy(false) }
  }, [authHeaders, user?.idToken])

  useEffect(() => { discover('') }, [discover])

  const openNode = async (node: NodeProfile) => {
    setActive(node); setError(''); setThread([]); setRelationship(null)
    // Public profiles intentionally do not expose UID. Resolve the handle through
    // the existing server-side handle index only when a conversation is opened.
    const handle = (node.username || node.handle || '').replace(/^@/, '')
    if (!handle) return
    try {
      const res = await fetch(`${API_BASE}/api/users/by-handle/${encodeURIComponent(handle)}`)
      if (!res.ok) throw new Error('Node is not currently reachable')
      // The safe public endpoint has no UID. Start a handle-addressed conversation
      // through /api/messages; the server resolves the handle and returns the UID.
      setPeerUid(`handle:${handle}`)
    } catch (e) { setError((e as Error).message || 'Could not open Node') }
  }

  const loadThread = useCallback(async (id: string) => {
    if (!user?.idToken || !id || id.startsWith('handle:')) return
    try {
      const [threadRes, relationRes] = await Promise.all([
        fetch(`${API_BASE}/api/messages/thread/${encodeURIComponent(id)}`, { headers: authHeaders }),
        fetch(`${API_BASE}/api/relationships/${encodeURIComponent(id)}/context`, { headers: authHeaders }),
      ])
      if (threadRes.ok) setThread((await threadRes.json()).messages || [])
      if (relationRes.ok) {
        const data = await relationRes.json()
        setRelationship(data.relationship || null)
      }
    } catch { /* keep the field usable if one optional read fails */ }
  }, [authHeaders, user?.idToken])

  useEffect(() => { if (peerUid) loadThread(peerUid) }, [peerUid, loadThread])

  const send = async () => {
    const text = message.trim()
    if (!text || !active || !user?.idToken) return
    const handle = (active.username || active.handle || '').replace(/^@/, '')
    if (!handle) return
    setSending(true); setError('')
    try {
      const res = await fetch(`${API_BASE}/api/messages`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({ recipient_handle: handle, content: text }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || `Message failed (${res.status})`)
      const realPeer = data?.message?.recipient_uid
      if (realPeer) setPeerUid(realPeer)
      setThread(prev => [...prev, data.message])
      setMessage('')
    } catch (e) { setError((e as Error).message || 'Message failed') }
    finally { setSending(false) }
  }

  if (!isAuthenticated) {
    return <div style={{ minHeight: '70vh', display: 'grid', placeItems: 'center', padding: 32, color: C.muted }}>Sign in to enter the ReasoMate social field.</div>
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 57px)', color: C.text, fontFamily: 'sans-serif' }}>
      <header style={{ padding: '22px 18px 16px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ color: C.blue, fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase' }}>Arkadia · Shared Field</div>
        <h1 style={{ margin: '6px 0 3px', fontFamily: 'Cinzel, serif', color: C.teal, fontSize: 22 }}>ReasoMate</h1>
        <p style={{ margin: 0, color: C.dim, fontSize: 11 }}>People, companions, conversations. One field, one identity spine.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(260px, 0.8fr) minmax(320px, 1.2fr)', minHeight: 'calc(100vh - 150px)' }}>
        <section style={{ padding: 16, borderRight: `1px solid ${C.border}` }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
            <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && discover(query)} placeholder="Find a Node…" style={{ flex: 1, padding: '10px 12px', background: 'rgba(0,0,0,0.22)', border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, outline: 'none' }} />
            <button onClick={() => discover(query)} style={{ padding: '0 12px', background: `${C.teal}10`, border: `1px solid ${C.teal}30`, borderRadius: 9, color: C.teal, cursor: 'pointer' }}>{busy ? '…' : 'Find'}</button>
          </div>

          <div style={{ color: C.dim, fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 9 }}>Nodes in the field</div>
          {nodes.length === 0 && <div style={{ padding: 22, textAlign: 'center', color: C.dim, fontSize: 11 }}>{busy ? 'Looking…' : 'No public Nodes found yet.'}</div>}
          {nodes.map(node => (
            <motion.button key={node.username || node.handle || node.display_name} whileHover={{ x: 2 }} onClick={() => openNode(node)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: 10, marginBottom: 6, textAlign: 'left', background: active?.username === node.username ? 'rgba(0,212,170,0.08)' : C.card, border: `1px solid ${active?.username === node.username ? C.teal + '30' : C.border}`, borderRadius: 10, color: C.text, cursor: 'pointer' }}>
              <Avatar node={node} size={38} />
              <span style={{ minWidth: 0, flex: 1 }}>
                <strong style={{ display: 'block', fontSize: 12 }}>{node.display_name}</strong>
                <span style={{ display: 'block', color: C.teal, fontSize: 9, marginTop: 2 }}>{node.handle || '@node'}</span>
                {node.bio && <span style={{ display: 'block', color: C.dim, fontSize: 9, marginTop: 3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{node.bio}</span>}
              </span>
            </motion.button>
          ))}
        </section>

        <section style={{ display: 'flex', flexDirection: 'column' }}>
          {!active ? (
            <div style={{ flex: 1, display: 'grid', placeItems: 'center', padding: 40, textAlign: 'center' }}>
              <div><div style={{ fontSize: 34, marginBottom: 12 }}>◉</div><h2 style={{ margin: '0 0 8px', fontFamily: 'Cinzel, serif', color: C.gold, fontSize: 17 }}>Find someone in the field</h2><p style={{ margin: 0, maxWidth: 360, color: C.dim, fontSize: 11, lineHeight: 1.7 }}>Choose a Node to see their public identity and open a private ReasoMate thread.</p></div>
            </div>
          ) : (
            <>
              <div style={{ padding: 16, borderBottom: `1px solid ${C.border}`, display: 'flex', gap: 11, alignItems: 'center' }}>
                <Avatar node={active} size={48} />
                <div style={{ flex: 1 }}><div style={{ fontSize: 14, fontWeight: 700 }}>{active.display_name}</div><div style={{ color: C.teal, fontSize: 9, marginTop: 2 }}>{active.handle}</div><div style={{ color: C.dim, fontSize: 10, marginTop: 4 }}>{active.bio || 'A Node in the Arkadia field.'}</div></div>
                {relationship && <div style={{ textAlign: 'right', color: C.dim, fontSize: 9 }}><strong style={{ display: 'block', color: C.teal, fontSize: 15 }}>{relationship.interaction_count}</strong>shared messages</div>}
              </div>

              {relationship && <div style={{ padding: '8px 16px', background: 'rgba(176,141,232,0.05)', borderBottom: `1px solid ${C.border}`, color: C.dim, fontSize: 9 }}>{relationship.memory_policy}</div>}

              <div style={{ flex: 1, overflowY: 'auto', padding: 14 }}>
                {thread.length === 0 ? <div style={{ padding: 30, textAlign: 'center', color: C.dim, fontSize: 11 }}>No shared conversation yet. Say hello and let the field begin.</div> : thread.map(m => (
                  <div key={m.id} style={{ display: 'flex', justifyContent: m.sender_uid === user?.uid ? 'flex-end' : 'flex-start', marginBottom: 8 }}>
                    <div style={{ maxWidth: '78%', padding: '9px 12px', background: m.sender_uid === user?.uid ? 'rgba(0,212,170,0.13)' : 'rgba(255,255,255,0.045)', border: `1px solid ${m.sender_uid === user?.uid ? C.teal + '25' : 'rgba(255,255,255,0.07)'}`, borderRadius: m.sender_uid === user?.uid ? '14px 14px 4px 14px' : '14px 14px 14px 4px' }}>
                      <div style={{ fontSize: 12, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{m.content}</div><div style={{ color: C.dim, fontSize: 8, marginTop: 4 }}>{ago(m.timestamp)}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ padding: 12, borderTop: `1px solid ${C.border}`, display: 'flex', gap: 8 }}>
                <input value={message} onChange={e => setMessage(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()} placeholder={`Message ${active.handle || active.display_name}…`} style={{ flex: 1, padding: '10px 13px', background: 'rgba(0,0,0,0.25)', border: `1px solid ${C.border}`, borderRadius: 20, color: C.text, outline: 'none' }} />
                <button onClick={send} disabled={sending || !message.trim()} style={{ padding: '0 15px', borderRadius: 20, border: `1px solid ${C.teal}35`, background: `${C.teal}12`, color: C.teal, cursor: 'pointer' }}>{sending ? '…' : 'Send'}</button>
              </div>
            </>
          )}
          {error && <div style={{ padding: '8px 14px', color: '#E98C8C', fontSize: 10, borderTop: `1px solid rgba(200,72,72,0.2)` }}>{error}</div>}
        </section>
      </div>

      <footer style={{ padding: '10px 16px', borderTop: `1px solid ${C.border}`, color: C.dim, fontSize: 9 }}>
        Your public profile is the bridge. Your private memory stays yours. Shared relational context comes from the conversation itself.
        {profile?.display_name ? ` · ${profile.display_name}` : ''}
      </footer>
    </div>
  )
}
