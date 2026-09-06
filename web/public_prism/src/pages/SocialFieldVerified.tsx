import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import MarkdownViewer from '../components/MarkdownViewer'
import SocialMessenger from './SocialMessenger'
import { formatToArkadiaMarkdown } from '../lib/arkadiaFormatter'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const C = { teal: '#00D4AA', blue: '#6A9FD8', red: '#C84848', text: 'rgba(232,232,232,.9)', dim: 'rgba(232,232,232,.35)', card: 'rgba(14,17,32,.78)', border: 'rgba(106,159,216,.14)' }
type Post = { id: string; owner_uid?: string; author: any; content: string; timestamp: number; edited_at?: number }
const ago = (ts: number) => { const d = Date.now() - ts; if (d < 60000) return 'now'; if (d < 3600000) return `${Math.floor(d / 60000)}m`; if (d < 86400000) return `${Math.floor(d / 3600000)}h`; return `${Math.floor(d / 86400000)}d` }
const button = (color: string, disabled = false): React.CSSProperties => ({ padding: '7px 11px', background: `${color}10`, border: `1px solid ${color}35`, borderRadius: 8, color: disabled ? C.dim : color, cursor: disabled ? 'not-allowed' : 'pointer', fontSize: 9, letterSpacing: '.1em', textTransform: 'uppercase' })

function Composer({ token, profile, onCreated }: { token: string; profile: any; onCreated: (post: Post) => void }) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async () => {
    if (!text.trim() || busy) return
    setBusy(true)
    try {
      const response = await fetch(`${API_BASE}/api/transmissions`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ content: formatToArkadiaMarkdown(text), author: { name: profile?.display_name || 'Node', avatar: profile?.role_sigil || '◈', role: profile?.role || 'Node' } }) })
      if (response.ok) { const data = await response.json(); onCreated(data.transmission); setText('') }
    } finally { setBusy(false) }
  }
  return <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 13, marginBottom: 12 }}><textarea value={text} onChange={event => setText(event.target.value)} placeholder="Transmit something to the field…" rows={3} style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(0,0,0,.22)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 9, padding: 10, color: C.text, resize: 'vertical', outline: 'none' }} /><div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 7 }}><button onClick={submit} disabled={!text.trim() || busy} style={button(C.teal, !text.trim() || busy)}>{busy ? 'Transmitting…' : 'Transmit'}</button></div></div>
}

function PostCard({ post, token, myUid, onChange }: { post: Post; token: string; myUid: string; onChange: (post: Post | null) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(post.content)
  const [busy, setBusy] = useState(false)
  const own = post.owner_uid === myUid
  const save = async () => {
    if (!draft.trim() || busy) return
    setBusy(true)
    try {
      const response = await fetch(`${API_BASE}/api/transmissions/${post.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ content: draft.trim() }) })
      if (response.ok) { const data = await response.json(); onChange(data.transmission); setEditing(false) }
    } finally { setBusy(false) }
  }
  const remove = async () => {
    if (busy || !confirm('Delete this transmission?')) return
    setBusy(true)
    try {
      const response = await fetch(`${API_BASE}/api/transmissions/${post.id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
      if (response.ok) onChange(null)
    } finally { setBusy(false) }
  }
  return <article style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden', marginBottom: 10 }}><div style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 9 }}><div style={{ width: 34, height: 34, borderRadius: '50%', display: 'grid', placeItems: 'center', background: 'rgba(0,212,170,.08)', color: C.teal }}>{post.author?.avatar || '◈'}</div><div style={{ flex: 1 }}><div style={{ color: C.text, fontSize: 12, fontWeight: 600 }}>{post.author?.name || 'Node'}</div><div style={{ color: C.dim, fontSize: 9 }}>{post.author?.role || 'Node'} · {ago(post.timestamp)}{post.edited_at ? ' · edited' : ''}</div></div>{own && <div style={{ display: 'flex', gap: 5 }}><button onClick={() => { setDraft(post.content); setEditing(value => !value) }} style={button(C.blue)}>Edit</button><button onClick={remove} disabled={busy} style={button(C.red, busy)}>Delete</button></div>}</div><div style={{ padding: '0 13px 13px' }}>{editing ? <><textarea value={draft} onChange={event => setDraft(event.target.value)} rows={5} style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(0,0,0,.2)', border: `1px solid ${C.blue}30`, borderRadius: 9, color: C.text, padding: 10 }} /><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 5, marginTop: 6 }}><button onClick={() => setEditing(false)} style={button(C.dim)}>Cancel</button><button onClick={save} disabled={busy} style={button(C.teal, busy)}>Save</button></div></> : <MarkdownViewer content={post.content} compact />}</div></article>
}

export default function SocialFieldVerified() {
  const { isAuthenticated, profile, user } = useAuth()
  const token = user?.idToken || ''
  const [mode, setMode] = useState<'field' | 'reasomate'>('field')
  const [posts, setPosts] = useState<Post[]>([])
  useEffect(() => { fetch(`${API_BASE}/api/transmissions`).then(response => response.json()).then(data => setPosts(data.transmissions || [])).catch(() => {}) }, [])
  if (!isAuthenticated) return <div style={{ padding: 40, textAlign: 'center', color: C.dim }}>Sign in to enter the Social Identity + ReasoMate Field.</div>
  return <div style={{ minHeight: 'calc(100vh - 80px)', color: C.text }}><header style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}><span style={{ color: C.blue, fontSize: 20 }}>◉</span><div><h2 style={{ margin: 0, fontFamily: 'Cinzel,serif', fontSize: 20 }}>The Social Field</h2><div style={{ color: C.dim, fontSize: 9 }}>One public identity · one governed relationship field</div></div><div style={{ marginLeft: 'auto', display: 'flex', gap: 5 }}><button onClick={() => setMode('field')} style={button(mode === 'field' ? C.teal : C.dim)}>NovaNet</button><button onClick={() => setMode('reasomate')} style={button(mode === 'reasomate' ? C.blue : C.dim)}>ReasoMate</button></div></header>{mode === 'field' ? <div style={{ maxWidth: 720, margin: '0 auto' }}><Composer token={token} profile={profile} onCreated={post => setPosts(current => [post, ...current])} />{posts.map(post => <PostCard key={post.id} post={post} token={token} myUid={profile?.uid || ''} onChange={next => setPosts(current => next ? current.map(item => item.id === next.id ? next : item) : current.filter(item => item.id !== post.id))} />)}</div> : <SocialMessenger />}</div>
}
