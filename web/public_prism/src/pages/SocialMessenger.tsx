import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const C = { teal: '#00D4AA', blue: '#6A9FD8', text: 'rgba(232,232,232,.9)', dim: 'rgba(232,232,232,.35)', border: 'rgba(106,159,216,.14)' }

type Node = { username?: string | null; handle?: string | null; display_name: string; bio?: string | null; avatar_url?: string | null }
type Message = { id: string; sender_uid: string; recipient_uid: string; content: string; timestamp: number }

function Avatar({ node, size = 38 }: { node: Node; size?: number }) {
  if (node.avatar_url) return <img src={node.avatar_url} alt="" style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover' }} />
  return <div style={{ width: size, height: size, borderRadius: '50%', display: 'grid', placeItems: 'center', background: 'rgba(0,212,170,.08)', color: C.teal }}>{node.display_name.slice(0, 1).toUpperCase()}</div>
}

export default function SocialMessenger() {
  const { profile, user } = useAuth()
  const token = user?.idToken || ''
  const [nodes, setNodes] = useState<Node[]>([])
  const [query, setQuery] = useState('')
  const [active, setActive] = useState<Node | null>(null)
  const [peerUid, setPeerUid] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [contextCount, setContextCount] = useState(0)

  const find = async () => {
    const response = await fetch(`${API_BASE}/api/social/nodes?q=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } })
    if (response.ok) setNodes((await response.json()).nodes || [])
  }

  useEffect(() => { find().catch(() => {}) }, [])

  const open = (node: Node) => {
    setActive(node)
    setPeerUid('')
    setMessages([])
    setContextCount(0)
  }

  const send = async () => {
    const handle = (active?.username || active?.handle || '').replace(/^@/, '')
    if (!handle || !text.trim()) return
    const response = await fetch(`${API_BASE}/api/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ recipient_handle: handle, content: text.trim() }),
    })
    if (!response.ok) return
    const data = await response.json()
    setPeerUid(data.message.recipient_uid)
    setMessages(current => [...current, data.message])
    setText('')
  }

  useEffect(() => {
    if (!peerUid) return
    Promise.all([
      fetch(`${API_BASE}/api/messages/thread/${peerUid}`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_BASE}/api/relationships/${peerUid}/context`, { headers: { Authorization: `Bearer ${token}` } }),
    ]).then(async ([threadResponse, contextResponse]) => {
      if (threadResponse.ok) setMessages((await threadResponse.json()).messages || [])
      if (contextResponse.ok) setContextCount((await contextResponse.json()).relationship?.interaction_count || 0)
    }).catch(() => {})
  }, [peerUid, token])

  return <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px,.7fr) minmax(280px,1.3fr)', minHeight: 520, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}>
    <section style={{ padding: 12, borderRight: `1px solid ${C.border}` }}>
      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        <input value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => event.key === 'Enter' && find()} placeholder="Find a Node…" style={{ flex: 1, padding: 9, background: 'rgba(0,0,0,.2)', border: `1px solid ${C.border}`, borderRadius: 8, color: C.text, outline: 'none' }} />
        <button onClick={find} style={{ padding: '0 10px', background: `${C.blue}10`, border: `1px solid ${C.blue}30`, borderRadius: 8, color: C.blue }}>Find</button>
      </div>
      {nodes.map((node, index) => <button key={node.username || node.handle || index} onClick={() => open(node)} style={{ width: '100%', display: 'flex', gap: 8, alignItems: 'center', textAlign: 'left', padding: 9, marginBottom: 6, background: C.border, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text }}><Avatar node={node} size={32} /><span><b style={{ display: 'block', fontSize: 11 }}>{node.display_name}</b><small style={{ color: C.teal }}>{node.handle || '@node'}</small></span></button>)}
    </section>
    <section style={{ display: 'flex', flexDirection: 'column' }}>
      {!active ? <div style={{ flex: 1, display: 'grid', placeItems: 'center', color: C.dim }}>Find a Node to open ReasoMate.</div> : <>
        <div style={{ padding: 12, borderBottom: `1px solid ${C.border}`, display: 'flex', gap: 9, alignItems: 'center' }}><Avatar node={active} size={40} /><div><b style={{ fontSize: 12 }}>{active.display_name}</b><div style={{ color: C.teal, fontSize: 9 }}>{active.handle}</div></div></div>
        <div style={{ padding: '7px 12px', color: C.dim, fontSize: 9 }}>{contextCount} shared messages · relational context comes from this thread</div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>{messages.map(message => <div key={message.id} style={{ display: 'flex', justifyContent: message.sender_uid === profile?.uid ? 'flex-end' : 'flex-start', marginBottom: 7 }}><div style={{ maxWidth: '78%', padding: '8px 11px', background: message.sender_uid === profile?.uid ? 'rgba(0,212,170,.12)' : 'rgba(255,255,255,.05)', borderRadius: 12, color: C.text, fontSize: 11 }}>{message.content}</div></div>)}</div>
        <div style={{ padding: 10, borderTop: `1px solid ${C.border}`, display: 'flex', gap: 6 }}><input value={text} onChange={event => setText(event.target.value)} onKeyDown={event => event.key === 'Enter' && send()} placeholder={`Message ${active.display_name}…`} style={{ flex: 1, padding: 9, borderRadius: 18, background: 'rgba(0,0,0,.2)', border: `1px solid ${C.border}`, color: C.text, outline: 'none' }} /><button onClick={send} style={{ padding: '0 14px', borderRadius: 18, background: `${C.teal}10`, border: `1px solid ${C.teal}30`, color: C.teal }}>Send</button></div>
      </>}
    </section>
  </div>
}
