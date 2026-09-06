import React, { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import MarkdownViewer from '../components/MarkdownViewer'
import { formatToArkadiaMarkdown } from '../lib/arkadiaFormatter'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

const C = {
  gold: '#C9A84C', teal: '#00D4AA', blue: '#6A9FD8', purple: '#B08DE8', red: '#C84848',
  text: 'rgba(232,232,232,0.9)', muted: 'rgba(232,232,232,0.55)', dim: 'rgba(232,232,232,0.32)',
  card: 'rgba(14,17,32,0.78)', border: 'rgba(106,159,216,0.14)',
}

type Tab = 'field' | 'nodes' | 'reasomate'
interface NodeProfile { uid: string; username?: string | null; handle?: string | null; display_name: string; bio?: string | null; avatar_url?: string | null }
interface Author { id?: string; name: string; avatar?: string; role?: string; avatar_url?: string | null; username?: string | null }
interface Comment { id: string; author: Author; content: string; timestamp: number }
interface Post { id: string; owner_uid?: string | null; author: Author; content: string; timestamp: number; reactions: Record<'heart'|'fire'|'star'|'mind', number>; comments: Comment[]; reposts: number; resonance: number; edited_at?: number }
interface Message { id: string; sender_uid: string; recipient_uid: string; content: string; timestamp: number }
interface RelationshipContext { relationship: { participants: NodeProfile[]; interaction_count: number; first_interaction_at?: number | null; last_interaction_at?: number | null; shared_memory_source: string; memory_policy: string }; messages: Message[] }

function timeAgo(ts?: number) {
  if (!ts) return ''
  const d = Date.now() - ts
  if (d < 60000) return 'now'
  if (d < 3600000) return `${Math.floor(d / 60000)}m`
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`
  return `${Math.floor(d / 86400000)}d`
}

function Avatar({ node, size = 38 }: { node?: Partial<NodeProfile> & { avatar?: string; name?: string; avatar_url?: string | null }; size?: number }) {
  const src = node?.avatar_url
  return src ? (
    <img src={src} alt="" style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', border: `1px solid ${C.blue}35` }} />
  ) : (
    <div style={{ width: size, height: size, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(106,159,216,0.10)', border: `1px solid ${C.blue}30`, color: C.blue, fontSize: Math.max(14, size * 0.38) }}>
      {node?.avatar || (node?.name || node?.display_name || 'N').slice(0, 1).toUpperCase()}
    </div>
  )
}

function useToken() {
  const { user } = useAuth()
  return user?.idToken || ''
}

function ProfileCard({ node, onMessage }: { node: NodeProfile; onMessage?: () => void }) {
  return (
    <div style={{ padding: 16, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14 }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <Avatar node={node} size={52} />
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ color: C.text, fontSize: 14, fontWeight: 600 }}>{node.display_name}</div>
          {node.handle && <div style={{ color: C.blue, fontSize: 10, marginTop: 2 }}>{node.handle}</div>}
        </div>
        {onMessage && <button onClick={onMessage} style={buttonStyle(C.teal)}>Message</button>}
      </div>
      {node.bio && <p style={{ color: C.muted, fontSize: 11, lineHeight: 1.6, margin: '12px 0 0' }}>{node.bio}</p>}
    </div>
  )
}

function buttonStyle(color: string, disabled = false): React.CSSProperties {
  return { padding: '7px 11px', background: `${color}10`, border: `1px solid ${color}35`, borderRadius: 8, color: disabled ? C.dim : color, cursor: disabled ? 'not-allowed' : 'pointer', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase' }
}

function Composer({ token, profile, onCreated }: { token: string; profile: any; onCreated: (post: Post) => void }) {
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const submit = async () => {
    if (!content.trim() || saving) return
    setSaving(true)
    try {
      const res = await fetch(`${API_BASE}/api/transmissions`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ content: formatToArkadiaMarkdown(content), author: { name: profile?.display_name || 'Node', avatar: profile?.role_sigil || '◈', role: profile?.role || 'Node' } }) })
      if (res.ok) { const data = await res.json(); onCreated(data.transmission); setContent('') }
    } finally { setSaving(false) }
  }
  return (
    <div style={{ padding: 14, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14 }}>
      <div style={{ display: 'flex', gap: 10 }}>
        <Avatar node={{ avatar: profile?.role_sigil, avatar_url: profile?.avatar_url, name: profile?.display_name }} />
        <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Say something to the field…" rows={3} style={{ flex: 1, resize: 'none', background: 'rgba(0,0,0,0.22)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: 10, color: C.text, outline: 'none', fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.6 }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}><button onClick={submit} disabled={!content.trim() || saving} style={buttonStyle(C.teal, !content.trim() || saving)}>{saving ? 'Sending…' : 'Transmit'}</button></div>
    </div>
  )
}

function PostCard({ post, myUid, token, profile, nodesByUid, onUpdated, onDeleted }: { post: Post; myUid: string; token: string; profile: any; nodesByUid: Record<string, NodeProfile>; onUpdated: (p: Post) => void; onDeleted: () => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(post.content)
  const [busy, setBusy] = useState(false)
  const [comment, setComment] = useState('')
  const [commentsOpen, setCommentsOpen] = useState(false)
  const isOwn = post.owner_uid === myUid
  const live = post.owner_uid ? nodesByUid[post.owner_uid] : undefined
  const author = live ? { ...post.author, name: live.display_name, avatar_url: live.avatar_url, username: live.username } : post.author

  const edit = async () => {
    if (!draft.trim()) return
    setBusy(true)
    try {
      const res = await fetch(`${API_BASE}/api/transmissions/${post.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ content: draft.trim() }) })
      if (res.ok) { const data = await res.json(); onUpdated(data.transmission); setEditing(false) }
    } finally { setBusy(false) }
  }
  const remove = async () => {
    if (!confirm('Delete this transmission?')) return
    setBusy(true)
    try { const res = await fetch(`${API_BASE}/api/transmissions/${post.id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }); if (res.ok) onDeleted() } finally { setBusy(false) }
  }
  const react = async (type: string) => {
    await fetch(`${API_BASE}/api/transmissions/${post.id}/react`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type }) })
    onUpdated({ ...post, reactions: { ...post.reactions, [type]: (post.reactions as any)[type] + 1 } })
  }
  const addComment = async () => {
    if (!comment.trim()) return
    const res = await fetch(`${API_BASE}/api/transmissions/${post.id}/comment`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ content: comment.trim(), author: { name: profile?.display_name || 'Node', avatar: profile?.role_sigil || '◈', role: profile?.role || 'Node' } })
    if (res.ok) { const data = await res.json(); onUpdated({ ...post, comments: [...post.comments, data.comment] }); setComment('') }
  }

  return (
    <motion.article initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: 'hidden' }}>
      <div style={{ padding: 13, display: 'flex', gap: 10, alignItems: 'center' }}>
        <Avatar node={author} />
        <div style={{ flex: 1 }}><div style={{ color: C.text, fontSize: 12, fontWeight: 600 }}>{author.name}</div><div style={{ color: C.dim, fontSize: 9 }}>{author.username ? `@${author.username} · ` : ''}{post.author.role || 'Node'} · {timeAgo(post.timestamp)}{post.edited_at ? ' · edited' : ''}</div></div>
        {isOwn && <div style={{ display: 'flex', gap: 5 }}><button onClick={() => { setDraft(post.content); setEditing(v => !v) }} style={buttonStyle(C.blue)}>Edit</button><button onClick={remove} disabled={busy} style={buttonStyle(C.red, busy)}>Delete</button></div>}
      </div>
      <div style={{ padding: '0 14px 12px' }}>{editing ? <><textarea value={draft} onChange={e => setDraft(e.target.value)} rows={5} style={{ width: '100%', boxSizing: 'border-box', background: 'rgba(0,0,0,0.25)', border: `1px solid ${C.blue}25`, borderRadius: 9, color: C.text, padding: 10, resize: 'vertical', outline: 'none' }} /><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 7 }}><button onClick={() => setEditing(false)} style={buttonStyle(C.dim)}>Cancel</button><button onClick={edit} disabled={busy || !draft.trim()} style={buttonStyle(C.teal, busy || !draft.trim())}>Save</button></div></> : <MarkdownViewer content={post.content} compact />}</div>
      <div style={{ padding: '7px 12px', borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', gap: 8 }}>
        {(['heart','fire','star','mind'] as const).map(t => <button key={t} onClick={() => react(t)} style={{ background: 'none', border: 0, color: C.dim, cursor: 'pointer', fontSize: 11 }}>{t === 'heart' ? '💜' : t === 'fire' ? '🔥' : t === 'star' ? '✨' : '🧠'} {post.reactions?.[t] || 0}</button>)}
        <button onClick={() => setCommentsOpen(v => !v)} style={{ marginLeft: 'auto', background: 'none', border: 0, color: C.dim, cursor: 'pointer', fontSize: 11 }}>💬 {post.comments?.length || 0}</button>
      </div>
      {commentsOpen && <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', padding: 10 }}><div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>{(post.comments || []).map(c => <div key={c.id} style={{ display: 'flex', gap: 7 }}><Avatar node={c.author} size={26} /><div><div style={{ color: C.text, fontSize: 10 }}><b>{c.author.name}</b> {c.content}</div><div style={{ color: C.dim, fontSize: 8 }}>{timeAgo(c.timestamp)}</div></div></div>)}</div><div style={{ display: 'flex', gap: 6, marginTop: 9 }}><input value={comment} onChange={e => setComment(e.target.value)} onKeyDown={e => e.key === 'Enter' && addComment()} placeholder="Reply…" style={{ flex: 1, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 15, padding: '7px 10px', color: C.text, outline: 'none', fontSize: 10 }} /><button onClick={addComment} style={buttonStyle(C.teal)}>Send</button></div></div>}
    </motion.article>
  )
}

function NodesTab({ token, onMessage }: { token: string; onMessage: (node: NodeProfile) => void }) {
  const [q, setQ] = useState('')
  const [nodes, setNodes] = useState<NodeProfile[]>([])
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    let alive = true
    setLoading(true)
    const timer = setTimeout(async () => {
      try { const res = await fetch(`${API_BASE}/api/social/nodes?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${token}` } }); const data = await res.json(); if (alive) setNodes(data.nodes || []) } finally { if (alive) setLoading(false) }
    }, 180)
    return () => { alive = false; clearTimeout(timer) }
  }, [q, token])
  return <div><div style={{ display: 'flex', gap: 8, marginBottom: 14 }}><input value={q} onChange={e => setQ(e.target.value)} placeholder="Find a Node by name, @handle or bio…" style={{ flex: 1, padding: 10, background: 'rgba(255,255,255,0.04)', border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, outline: 'none', fontSize: 11 }} /><span style={{ alignSelf: 'center', color: C.dim, fontSize: 9 }}>{loading ? '…' : `${nodes.length} Nodes`}</span></div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 10 }}>{nodes.map(n => <ProfileCard key={n.uid} node={n} onMessage={() => onMessage(n)} />)}</div>{!loading && !nodes.length && <div style={{ textAlign: 'center', color: C.dim, padding: 30, fontSize: 11 }}>No Nodes found yet.</div>}</div>
}

function Thread({ peer, token, myUid, onBack }: { peer: NodeProfile; token: string; myUid: string; onBack: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [context, setContext] = useState<RelationshipContext | null>(null)
  const [sending, setSending] = useState(false)
  const load = async () => {
    const [m, c] = await Promise.all([fetch(`${API_BASE}/api/messages/thread/${peer.uid}`, { headers: { Authorization: `Bearer ${token}` } }), fetch(`${API_BASE}/api/relationships/${peer.uid}/context`, { headers: { Authorization: `Bearer ${token}` } })])
    if (m.ok) setMessages((await m.json()).messages || [])
    if (c.ok) setContext(await c.json())
  }
  useEffect(() => { load() }, [peer.uid])
  const send = async () => {
    if (!text.trim() || sending) return
    setSending(true)
    try { const res = await fetch(`${API_BASE}/api/messages`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ recipient_uid: peer.uid, content: text.trim() }) }); if (res.ok) { const data = await res.json(); setMessages(v => [...v, data.message]); setContext(v => v ? { ...v, relationship: { ...v.relationship, interaction_count: v.relationship.interaction_count + 1, last_interaction_at: data.message.timestamp }, messages: [...v.messages, data.message].slice(-24) } : v); setText('') } } finally { setSending(false) }
  }
  return <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}><div style={{ display: 'flex', gap: 9, alignItems: 'center', paddingBottom: 10, borderBottom: `1px solid ${C.border}` }}><button onClick={onBack} style={{ background: 'none', border: 0, color: C.teal, cursor: 'pointer', fontSize: 16 }}>←</button><Avatar node={peer} size={34} /><div style={{ flex: 1 }}><div style={{ color: C.text, fontSize: 12 }}>{peer.display_name}</div><div style={{ color: C.dim, fontSize: 9 }}>{peer.handle || 'Node'}</div></div><span title="Shared context comes from the existing message thread" style={{ color: C.teal, fontSize: 9 }}>● shared field</span></div><div style={{ padding: '8px 0', color: C.dim, fontSize: 9 }}>{context?.relationship.interaction_count || 0} shared messages · companion context is derived from this thread</div><div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 7, padding: '8px 0' }}>{messages.map(m => <div key={m.id} style={{ alignSelf: m.sender_uid === myUid ? 'flex-end' : 'flex-start', maxWidth: '78%', padding: '8px 11px', background: m.sender_uid === myUid ? 'rgba(0,212,170,0.12)' : 'rgba(106,159,216,0.09)', border: `1px solid ${m.sender_uid === myUid ? C.teal + '25' : C.blue + '20'}`, borderRadius: 12 }}><div style={{ color: C.text, fontSize: 11, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{m.content}</div><div style={{ color: C.dim, fontSize: 8, marginTop: 3 }}>{timeAgo(m.timestamp)}</div></div>)}</div><div style={{ display: 'flex', gap: 6, paddingTop: 8, borderTop: `1px solid ${C.border}` }}><input value={text} onChange={e => setText(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder={`Message ${peer.display_name}…`} style={{ flex: 1, background: 'rgba(0,0,0,0.24)', border: `1px solid ${C.border}`, borderRadius: 18, padding: '9px 12px', color: C.text, outline: 'none', fontSize: 11 }} /><button onClick={send} disabled={sending || !text.trim()} style={buttonStyle(C.teal, sending || !text.trim())}>Send</button></div></div>
}

function ReasoMateTab({ token, myUid, profile, onFind }: { token: string; myUid: string; profile: any; onFind: () => void }) {
  const [conversations, setConversations] = useState<any[]>([])
  const [peer, setPeer] = useState<NodeProfile | null>(null)
  const [nodes, setNodes] = useState<NodeProfile[]>([])
  useEffect(() => { fetch(`${API_BASE}/api/messages/inbox`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).then(d => setConversations(d.conversations || [])).catch(() => {}) ; fetch(`${API_BASE}/api/social/nodes`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).then(d => setNodes(d.nodes || [])).catch(() => {}) }, [token])
  if (peer) return <Thread peer={peer} token={token} myUid={myUid} onBack={() => setPeer(null)} />
  return <div><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}><div><div style={{ color: C.text, fontSize: 14 }}>ReasoMate</div><div style={{ color: C.dim, fontSize: 9 }}>People, companions and shared context in one field.</div></div><button onClick={onFind} style={buttonStyle(C.blue)}>Find a Node</button></div><div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>{conversations.map(c => { const n = nodes.find(x => x.uid === c.peer_uid); return n ? <button key={c.peer_uid} onClick={() => setPeer(n)} style={{ display: 'flex', gap: 9, alignItems: 'center', textAlign: 'left', padding: 10, background: 'rgba(255,255,255,0.025)', border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, cursor: 'pointer' }}><Avatar node={n} size={34} /><div style={{ flex: 1 }}><div style={{ fontSize: 11 }}>{n.display_name}</div><div style={{ color: C.dim, fontSize: 9 }}>{c.last_message?.content?.slice(0, 70)}</div></div><span style={{ color: C.dim, fontSize: 8 }}>{timeAgo(c.last_message?.timestamp)}</span></button> : null })}</div>{!conversations.length && <div style={{ textAlign: 'center', padding: 28, color: C.dim, fontSize: 10 }}>Your ReasoMate field is quiet. Find a Node and begin a thread.</div>}</div>
}

export default function SocialFieldPage() {
  const { isAuthenticated, profile } = useAuth()
  const token = useToken()
  const [tab, setTab] = useState<Tab>('field')
  const [posts, setPosts] = useState<Post[]>([])
  const [nodes, setNodes] = useState<NodeProfile[]>([])
  const [selectedNode, setSelectedNode] = useState<NodeProfile | null>(null)
  const [search, setSearch] = useState('')

  const load = async () => {
    const [p, n] = await Promise.all([
      fetch(`${API_BASE}/api/transmissions`),
      token ? fetch(`${API_BASE}/api/social/nodes`, { headers: { Authorization: `Bearer ${token}` } }) : Promise.resolve(null),
    ])
    if (p.ok) setPosts((await p.json()).transmissions || [])
    if (n?.ok) setNodes((await n.json()).nodes || [])
  }
  useEffect(() => { load() }, [token])
  const nodesByUid = useMemo(() => Object.fromEntries(nodes.map(n => [n.uid, n])), [nodes])
  const filtered = posts.filter(p => !search || p.content.toLowerCase().includes(search.toLowerCase()) || p.author.name.toLowerCase().includes(search.toLowerCase()))

  if (!isAuthenticated) return <div style={{ padding: 40, textAlign: 'center', color: C.muted }}>Sign in to enter the Social Identity + ReasoMate Field.</div>

  return <div style={{ minHeight: 'calc(100vh - 80px)', color: C.text }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}><span style={{ color: C.blue, fontSize: 20 }}>◉</span><h2 style={{ margin: 0, fontFamily: 'Cinzel,serif', fontSize: 20 }}>The Social Field</h2><span style={{ marginLeft: 'auto', color: C.teal, fontSize: 8, letterSpacing: '0.16em', textTransform: 'uppercase' }}>One identity · one thread</span></div>
    <p style={{ color: C.dim, fontSize: 10, margin: '0 0 16px' }}>Your public identity travels with you. Your private memory stays private. Relationships grow from what you actually share.</p>
    <div style={{ display: 'flex', gap: 5, marginBottom: 14, borderBottom: `1px solid ${C.border}`, paddingBottom: 7 }}>{([['field','Field'],['nodes','Find Nodes'],['reasomate','ReasoMate']] as [Tab,string][]).map(([id,label]) => <button key={id} onClick={() => setTab(id)} style={{ ...buttonStyle(id === tab ? C.teal : C.dim), background: id === tab ? 'rgba(0,212,170,0.10)' : 'transparent' }}>{label}</button>)}</div>

    {tab === 'field' && <div style={{ maxWidth: 720, margin: '0 auto' }}><Composer token={token} profile={profile} onCreated={p => setPosts(v => [p, ...v])} /><div style={{ margin: '12px 0' }}><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search the field…" style={{ width: '100%', boxSizing: 'border-box', padding: 10, background: 'rgba(255,255,255,0.03)', border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, outline: 'none', fontSize: 11 }} /></div><div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>{filtered.map(p => <PostCard key={p.id} post={p} myUid={profile?.uid || ''} token={token} profile={profile} nodesByUid={nodesByUid} onUpdated={u => setPosts(v => v.map(x => x.id === u.id ? u : x))} onDeleted={() => setPosts(v => v.filter(x => x.id !== p.id))} />)}</div></div>}
    {tab === 'nodes' && <NodesTab token={token} onMessage={n => { setSelectedNode(n); setTab('reasomate') }} />}
    {tab === 'reasomate' && <ReasoMateTab token={token} myUid={profile?.uid || ''} profile={profile} onFind={() => setTab('nodes')} />}

    <AnimatePresence>{selectedNode && tab === 'reasomate' && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'rgba(0,0,0,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={() => setSelectedNode(null)}><motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} onClick={e => e.stopPropagation()} style={{ width: 'min(440px,100%)' }}><ProfileCard node={selectedNode} onMessage={() => setSelectedNode(null)} /></motion.div></motion.div>}</AnimatePresence>
  </div>
}
