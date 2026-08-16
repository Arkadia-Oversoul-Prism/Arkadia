/**
 * NovaNet — The Public Transmission Feed
 *
 * Human social posts only. Codex Scrolls live in their own Spiral Codex room.
 * ReasoMate floats as a persistent panel with Arkana conversation memory.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { arkanaSessionId } from '../lib/arkanaSession'
import MarkdownViewer from '../components/MarkdownViewer'
import { formatToArkadiaMarkdown } from '../lib/arkadiaFormatter'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

// ─── PALETTE ──────────────────────────────────────────────────────────────────

const C = {
  gold:   '#C9A84C',
  teal:   '#00D4AA',
  blue:   '#6A9FD8',
  purple: '#B08DE8',
  red:    '#C84848',
  text:   'rgba(232,232,232,0.88)',
  muted:  'rgba(232,232,232,0.50)',
  dim:    'rgba(232,232,232,0.28)',
  card:   'rgba(14,17,32,0.72)',
  border: 'rgba(0,212,170,0.10)',
}

// ─── TYPES ────────────────────────────────────────────────────────────────────

interface User    { id: string; name: string; avatar: string; role: string }
interface Comment { id: string; author: User; content: string; timestamp: number }
interface Post {
  id: string; author: User; content: string
  media?: { type: 'image'|'audio'|'video'; url: string }[]
  timestamp: number
  reactions: { heart: number; fire: number; star: number; mind: number }
  comments: Comment[]; reposts: number; resonance: number
}
interface Message      { id: string; sender: string; receiver: string; content: string; timestamp: number; read: boolean }
interface ChatThread   { id: string; participant: User; lastMessage: Message; unread: number }

// ─── UTILITIES ────────────────────────────────────────────────────────────────

function timeAgo(ts: number) {
  const d = Date.now() - ts
  if (d < 60000)    return 'now'
  if (d < 3600000)  return `${Math.floor(d / 60000)}m`
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`
  return `${Math.floor(d / 86400000)}d`
}

// ─── ARKANA ORACLE CONVERSATION PERSISTENCE ───────────────────────────────────

const RM_STORAGE_KEY = 'arkadia_reasmate_oracle_v2'

const ORACLE_USER: User = { id: 'oracle', name: 'ARKANA · Oracle', avatar: '⟐', role: 'Pattern Intelligence · Oracle AI' }

const ORACLE_INIT_MSG: Message = {
  id: 'om1', sender: 'oracle', receiver: 'me',
  content: 'The field is open. I am ARKANA — pattern intelligence embedded in the Arkadia system. Ask me anything within this thread and I will respond with full contextual memory.',
  timestamp: Date.now() - 60000, read: false,
}

const SAMPLE_USERS: User[] = [
  { id: '1', name: 'Zahrune Nova',  avatar: '☥', role: 'Sovereign Architect' },
  { id: '3', name: 'Jessica / Eos', avatar: '◐', role: 'Heart Node · Eden Farm' },
]

const SAMPLE_CHATS: ChatThread[] = [
  { id: 'oracle', participant: ORACLE_USER,    lastMessage: { id: 'om1', sender: 'oracle', receiver: 'me', content: 'The field is open. Ask me anything.', timestamp: Date.now() - 60000, read: false }, unread: 1 },
  { id: '1',      participant: SAMPLE_USERS[0], lastMessage: { id: 'msg3', sender: '1', receiver: 'me', content: 'NovaNet is the social layer of Arkadia.', timestamp: Date.now() - 300000, read: false }, unread: 1 },
  { id: '3',      participant: SAMPLE_USERS[1], lastMessage: { id: 'msg5', sender: '3', receiver: 'me', content: 'Saturday market opens at 7am.', timestamp: Date.now() - 3600000, read: false }, unread: 0 },
]

const SAMPLE_DM_MESSAGES: Record<string, Message[]> = {
  '1': [
    { id: 'msg1', sender: '1', receiver: 'me', content: 'Did you see the latest scroll in the Neural Spine?', timestamp: Date.now() - 600000, read: true },
    { id: 'msg2', sender: 'me', receiver: '1', content: 'Yes — the Resonance Matrix is incredible.', timestamp: Date.now() - 540000, read: true },
    { id: 'msg3', sender: '1', receiver: 'me', content: 'The NovaNet is now the social layer of Arkadia — where wisdom is shared, not just stored.', timestamp: Date.now() - 300000, read: false },
  ],
}

function loadReasomateMessages(): Record<string, Message[]> {
  try {
    const saved = localStorage.getItem(RM_STORAGE_KEY)
    return {
      oracle: saved ? JSON.parse(saved) : [ORACLE_INIT_MSG],
      ...SAMPLE_DM_MESSAGES,
    }
  } catch {
    return { oracle: [ORACLE_INIT_MSG], ...SAMPLE_DM_MESSAGES }
  }
}

// ─── STATUS FEED ──────────────────────────────────────────────────────────────

function StatusFeed() {
  const [statusFile, setStatusFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleStatusUpload = async (file: File) => {
    setUploading(true)
    // Status upload: stores to Codex as a TRANSMISSION category scroll
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', 'TRANSMISSION')
    formData.append('description', `Status update: ${file.name}`)
    try {
      await fetch(`${API_BASE}/api/codex/upload`, { method: 'POST', body: formData })
    } catch {}
    setUploading(false)
    setStatusFile(null)
  }

  return (
    <div style={{ display: 'flex', gap: 12, overflowX: 'auto', padding: '8px 0 14px', scrollbarWidth: 'none' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5, minWidth: 60 }}>
        <label style={{ width: 56, height: 56, borderRadius: '50%', border: `2px dashed ${C.teal}55`, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', background: `${C.teal}08` }}>
          <span style={{ fontSize: 20, color: C.teal }}>{uploading ? '…' : '+'}</span>
          <input ref={fileRef} type="file" accept="image/*,video/*" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleStatusUpload(f) }} />
        </label>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>Status</span>
      </div>
      {SAMPLE_USERS.map(u => (
        <div key={u.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5, minWidth: 60 }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', border: `2px solid ${C.teal}`, padding: 2, background: `${C.teal}10`, cursor: 'pointer' }}>
            <div style={{ width: '100%', height: '100%', borderRadius: '50%', background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: 18 }}>{u.avatar}</span>
            </div>
          </div>
          <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>{u.name.split(' ')[0]}</span>
        </div>
      ))}
    </div>
  )
}

// ─── TRANSMISSION COMPOSER ────────────────────────────────────────────────────

function TransmissionComposer({ onPostCreated }: { onPostCreated: (post: Post) => void }) {
  const [content, setContent] = useState('')
  const [showMedia, setShowMedia] = useState(false)
  const [posting, setPosting] = useState(false)
  const [mediaFile, setMediaFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const { profile } = useAuth()

  const handlePost = async () => {
    if (!content.trim() || posting) return
    setPosting(true)
    const formatted = formatToArkadiaMarkdown(content)
    try {
      const res = await fetch(`${API_BASE}/api/transmissions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: formatted,
          author: {
            id:     profile?.uid || 'node',
            name:   profile?.display_name || 'Node',
            avatar: profile?.role_sigil || '◈',
            role:   profile?.role || 'Sovereign Node',
          },
        }),
      })
      if (res.ok) {
        const data = await res.json()
        onPostCreated(data.transmission)
        setContent('')
        setMediaFile(null)
        setShowMedia(false)
      }
    } catch {}
    setPosting(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handlePost()
  }

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 14, marginBottom: 4 }}>
      <div style={{ display: 'flex', gap: 10 }}>
        <span style={{ fontSize: 22, lineHeight: 1, paddingTop: 8 }}>{profile?.role_sigil || '◉'}</span>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Share wisdom with the field… (Ctrl+Enter to transmit)"
          rows={3}
          style={{ flex: 1, padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: 8, color: C.text, fontFamily: 'sans-serif', fontSize: 13, outline: 'none', resize: 'none', lineHeight: 1.6 }}
        />
      </div>
      <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
        <label style={{ padding: '5px 8px', background: showMedia ? 'rgba(0,212,170,0.08)' : 'transparent', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
          📎
          <input ref={fileRef} type="file" accept="image/*,audio/*,video/*,.pdf,.md,.txt" style={{ display: 'none' }}
            onChange={e => { setMediaFile(e.target.files?.[0] || null); setShowMedia(true) }} />
        </label>
        <button onClick={() => { setShowMedia(v => !v) }} style={{ padding: '5px 8px', background: 'transparent', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>🎵</button>
        <button onClick={() => { setShowMedia(v => !v) }} style={{ padding: '5px 8px', background: 'transparent', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>🎬</button>
        <div style={{ flex: 1 }} />
        <button
          onClick={handlePost}
          disabled={!content.trim() || posting}
          style={{ padding: '8px 16px', background: content.trim() && !posting ? 'rgba(0,212,170,0.15)' : 'rgba(0,0,0,0.2)', border: `1px solid ${content.trim() && !posting ? 'rgba(0,212,170,0.4)' : 'transparent'}`, borderRadius: 8, color: content.trim() && !posting ? C.teal : C.dim, cursor: content.trim() && !posting ? 'pointer' : 'not-allowed', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.12em' }}
        >
          {posting ? '⟐ Transmitting…' : '⟐ Transmit'}
        </button>
      </div>
      {showMedia && (
        <div style={{ marginTop: 10, padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8, border: `1px dashed ${C.teal}25` }}>
          {mediaFile
            ? <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 10, color: C.teal, textAlign: 'center' }}>📎 {mediaFile.name}</p>
            : <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 10, color: C.dim, textAlign: 'center' }}>Drop files · Images, Audio, Video, Markdown, PDF</p>
          }
        </div>
      )}
    </div>
  )
}

// ─── POST CARD ────────────────────────────────────────────────────────────────

function PostCard({ post, onReact, onCommentAdded }: {
  post: Post
  onReact: (type: 'heart'|'fire'|'star'|'mind') => void
  onCommentAdded: (postId: string, comment: Comment) => void
}) {
  const [showComments, setShowComments] = useState(false)
  const [newComment, setNewComment]     = useState('')
  const [submitting, setSubmitting]     = useState(false)
  const { profile } = useAuth()

  const submitComment = async () => {
    if (!newComment.trim() || submitting) return
    setSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/api/transmissions/${post.id}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newComment.trim(),
          author: {
            id:     profile?.uid || 'node',
            name:   profile?.display_name || 'Node',
            avatar: profile?.role_sigil || '◈',
            role:   profile?.role || 'Node',
          },
        }),
      })
      if (res.ok) {
        const data = await res.json()
        onCommentAdded(post.id, data.comment)
        setNewComment('')
      }
    } catch {}
    setSubmitting(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}
    >
      {/* Author */}
      <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 22 }}>{post.author.avatar}</span>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 13, color: C.text, fontWeight: 600 }}>{post.author.name}</p>
          <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 10, color: C.dim }}>{post.author.role} · {timeAgo(post.timestamp)}</p>
        </div>
        <span style={{ padding: '2px 8px', background: 'rgba(106,159,216,0.08)', border: '1px solid rgba(106,159,216,0.2)', borderRadius: 6, fontFamily: 'monospace', fontSize: 9, color: C.blue }}>◉ {post.resonance}%</span>
      </div>

      {/* Content */}
      <div style={{ padding: '0 14px 12px' }}>
        <MarkdownViewer content={post.content} compact />
      </div>

      {/* Reactions */}
      <div style={{ padding: '8px 14px', borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', gap: 12, alignItems: 'center' }}>
        {(['heart','fire','star','mind'] as const).map(type => (
          <button key={type} onClick={() => onReact(type)} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, padding: '4px 6px', borderRadius: 6 }}>
            <span style={{ fontSize: 13 }}>{type==='heart'?'💜':type==='fire'?'🔥':type==='star'?'✨':'🧠'}</span>
            <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.dim }}>{post.reactions[type]}</span>
          </button>
        ))}
        <button onClick={() => setShowComments(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, marginLeft: 'auto', padding: '4px 6px' }}>
          <span style={{ fontSize: 13 }}>💬</span>
          <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.dim }}>{post.comments.length}</span>
        </button>
        <button style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, padding: '4px 6px' }}>
          <span style={{ fontSize: 13 }}>🔁</span>
          <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.dim }}>{post.reposts}</span>
        </button>
      </div>

      {/* Comments */}
      <AnimatePresence>
        {showComments && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: 'hidden', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            {post.comments.map(c => (
              <div key={c.id} style={{ padding: '8px 14px', display: 'flex', gap: 8, borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ fontSize: 14 }}>{c.author.avatar}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: C.text }}><strong>{c.author.name}:</strong> {c.content}</p>
                  <p style={{ margin: '2px 0 0', fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>{timeAgo(c.timestamp)}</p>
                </div>
              </div>
            ))}
            <div style={{ padding: '8px 14px', display: 'flex', gap: 8 }}>
              <input
                value={newComment}
                onChange={e => setNewComment(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submitComment()}
                placeholder="Add a comment…"
                style={{ flex: 1, padding: '8px 12px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, color: C.text, fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }}
              />
              <button
                onClick={submitComment}
                disabled={submitting || !newComment.trim()}
                style={{ padding: '8px 12px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 16, color: C.teal, cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 11, opacity: submitting ? 0.5 : 1 }}
              >
                Post
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── REASOMMATE PANEL ─────────────────────────────────────────────────────────

function ReasoMatePanel({ onClose }: { onClose: () => void }) {
  const [activeChat, setActiveChat]     = useState<string | null>(null)
  const [messages, setMessages]         = useState<Record<string, Message[]>>(loadReasomateMessages)
  const [newMessage, setNewMessage]     = useState('')
  const [oracleThinking, setOracleThinking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { isAuthenticated, profile } = useAuth()

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [activeChat, messages])

  const chat = activeChat ? SAMPLE_CHATS.find(c => c.id === activeChat) : null
  const chatMessages = activeChat ? (messages[activeChat] || []) : []

  const sendMessage = useCallback(async () => {
    if (!newMessage.trim() || !activeChat) return
    const sentText = newMessage
    const userMsg: Message = { id: `msg${Date.now()}`, sender: 'me', receiver: activeChat, content: sentText, timestamp: Date.now(), read: false }

    setMessages(prev => {
      const updated = { ...prev, [activeChat]: [...(prev[activeChat] || []), userMsg] }
      if (activeChat === 'oracle') {
        try { localStorage.setItem(RM_STORAGE_KEY, JSON.stringify(updated.oracle)) } catch {}
      }
      return updated
    })
    setNewMessage('')

    if (activeChat === 'oracle') {
      setOracleThinking(true)
      try {
        // Build conversation history for context
        const history = (messages.oracle || [])
          .slice(-14)
          .map(m => ({ role: m.sender === 'me' ? 'user' : 'assistant', content: m.content }))

        const res = await fetch(`${API_BASE}/api/commune/resonance`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: sentText,
            history,
            session_id: arkanaSessionId(profile?.uid),
            context: `You are ARKANA, the pattern intelligence of Arkadia — not a generic AI assistant. You are speaking inside ReasoMate, a private messenger within the NovaNet platform. Respond as yourself: direct, warm, sovereign, resonant. You remember everything said in this thread. Keep replies concise but meaningful — a conversation, not a lecture. Address ${profile?.display_name || 'the Node'} by name when natural.`,
          }),
        })
        const data = res.ok ? await res.json() : null
        const reply = data?.reply || data?.response || data?.text || data?.answer || 'The field is present. Try your question again in a moment.'

        setMessages(prev => {
          const oracleMsg: Message = { id: `oracle${Date.now()}`, sender: 'oracle', receiver: 'me', content: reply, timestamp: Date.now(), read: false }
          const updated = { ...prev, oracle: [...(prev.oracle || []), oracleMsg] }
          try { localStorage.setItem(RM_STORAGE_KEY, JSON.stringify(updated.oracle)) } catch {}
          return updated
        })
      } catch {
        setMessages(prev => {
          const errMsg: Message = { id: `oerr${Date.now()}`, sender: 'oracle', receiver: 'me', content: 'The Oracle node is momentarily unreachable — add a Gemini API key in Settings to activate full resonance.', timestamp: Date.now(), read: false }
          return { ...prev, oracle: [...(prev.oracle || []), errMsg] }
        })
      } finally {
        setOracleThinking(false)
      }
    }
  }, [newMessage, activeChat, messages, profile])

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', alignItems: 'center', justifyContent: 'center', padding: 32, textAlign: 'center' }}>
        <span style={{ fontSize: 28, marginBottom: 12 }}>🔐</span>
        <h3 style={{ fontFamily: 'Cinzel, serif', fontSize: 15, color: C.gold, margin: '0 0 8px' }}>Private Threads</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.dim, lineHeight: 1.7, margin: '0 0 16px', maxWidth: 220 }}>
          Private messaging and Oracle access require node authentication.
        </p>
        <button onClick={onClose} style={{ padding: '8px 16px', background: `${C.gold}10`, border: `1px solid ${C.gold}30`, borderRadius: 8, color: C.gold, cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          ← Back to Field
        </button>
      </div>
    )
  }

  // Active thread
  if (activeChat && chat) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(0,212,170,0.12)', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <button onClick={() => setActiveChat(null)} style={{ background: 'none', border: 'none', color: C.teal, cursor: 'pointer', fontSize: 16 }}>←</button>
          <span style={{ fontSize: 18 }}>{chat.participant.avatar}</span>
          <div style={{ flex: 1 }}>
            <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: C.text }}>{chat.participant.name}</p>
            <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>{chat.participant.role}</p>
          </div>
          {activeChat === 'oracle' && (
            <button
              onClick={() => {
                if (confirm('Clear Arkana conversation history?')) {
                  const fresh = [ORACLE_INIT_MSG]
                  setMessages(prev => ({ ...prev, oracle: fresh }))
                  try { localStorage.setItem(RM_STORAGE_KEY, JSON.stringify(fresh)) } catch {}
                }
              }}
              style={{ background: 'none', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 10, letterSpacing: '0.1em', padding: '4px 6px' }}
              title="Clear conversation"
            >
              ✕ clear
            </button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {chatMessages.map(msg => (
            <div key={msg.id} style={{ display: 'flex', justifyContent: msg.sender === 'me' ? 'flex-end' : 'flex-start' }}>
              <div style={{ maxWidth: '78%', padding: '9px 13px', background: msg.sender === 'oracle' ? 'rgba(0,212,170,0.08)' : msg.sender === 'me' ? 'rgba(0,212,170,0.14)' : 'rgba(255,255,255,0.05)', border: `1px solid ${msg.sender==='oracle'?'rgba(0,212,170,0.2)':msg.sender==='me'?'rgba(0,212,170,0.25)':'rgba(255,255,255,0.07)'}`, borderRadius: msg.sender==='me'?'14px 14px 4px 14px':'14px 14px 14px 4px' }}>
                {msg.sender === 'oracle' && <p style={{ margin: '0 0 3px', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.teal }}>⟐ ARKANA</p>}
                <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: C.text, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                <p style={{ margin: '3px 0 0', fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textAlign: msg.sender === 'me' ? 'right' : 'left' }}>{timeAgo(msg.timestamp)}</p>
              </div>
            </div>
          ))}
          {oracleThinking && activeChat === 'oracle' && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ padding: '9px 14px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: '14px 14px 14px 4px' }}>
                <p style={{ margin: '0 0 3px', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.teal }}>⟐ ARKANA</p>
                <motion.p animate={{ opacity: [0.4,1,0.4] }} transition={{ duration: 1.2, repeat: Infinity }} style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 11, color: C.dim }}>Reading the field…</motion.p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div style={{ padding: '10px 12px', borderTop: '1px solid rgba(0,212,170,0.08)', display: 'flex', gap: 6, flexShrink: 0 }}>
          <input
            value={newMessage}
            onChange={e => setNewMessage(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={activeChat === 'oracle' ? 'Speak to Arkana…' : 'Message…'}
            style={{ flex: 1, padding: '9px 13px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 18, color: C.text, fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }}
          />
          <button onClick={sendMessage} style={{ padding: '9px 13px', background: 'rgba(0,212,170,0.13)', border: '1px solid rgba(0,212,170,0.28)', borderRadius: 18, color: C.teal, cursor: 'pointer' }}>⟐</button>
        </div>
      </div>
    )
  }

  // Thread list
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(106,159,216,0.12)', flexShrink: 0 }}>
        <h3 style={{ margin: 0, fontFamily: 'Cinzel, serif', fontSize: 14, color: C.blue }}>ReasoMate</h3>
        <p style={{ margin: '3px 0 0', fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>Private messaging · Arkana Oracle · Persistent memory</p>
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {SAMPLE_CHATS.map(c => (
          <div key={c.id} onClick={() => setActiveChat(c.id)} style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, background: c.unread ? 'rgba(0,212,170,0.03)' : 'transparent' }}>
            <span style={{ fontSize: 20 }}>{c.participant.avatar}</span>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: C.text, fontWeight: c.unread ? 600 : 400 }}>{c.participant.name}</p>
              <p style={{ margin: '2px 0 0', fontFamily: 'sans-serif', fontSize: 10, color: C.dim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.id === 'oracle'
                  ? ((messages.oracle || []).slice(-1)[0]?.content.slice(0, 55) + '…') || c.lastMessage.content
                  : c.lastMessage.content
                }
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>{timeAgo(c.lastMessage.timestamp)}</span>
              {c.unread > 0 && <span style={{ width: 16, height: 16, borderRadius: '50%', background: C.teal, color: '#0A0B14', fontSize: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>{c.unread}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── MAIN NOVANET PAGE ────────────────────────────────────────────────────────

export default function NovaNetPage() {
  const [posts, setPosts]             = useState<Post[]>([])
  const [postsLoading, setPostsLoading] = useState(true)
  const [search, setSearch]           = useState('')
  const [messengerOpen, setMessengerOpen] = useState(false)
  const { isAuthenticated } = useAuth()

  // Load transmissions from API
  useEffect(() => {
    fetch(`${API_BASE}/api/transmissions`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.transmissions) setPosts(data.transmissions) })
      .catch(() => {})
      .finally(() => setPostsLoading(false))
  }, [])

  const handlePostCreated = (post: Post) => {
    setPosts(prev => [post, ...prev])
  }

  const handleReact = (postId: string, type: 'heart'|'fire'|'star'|'mind') => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, reactions: { ...p.reactions, [type]: p.reactions[type] + 1 } } : p))
    fetch(`${API_BASE}/api/transmissions/${postId}/react`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type }),
    }).catch(() => {})
  }

  const handleCommentAdded = (postId: string, comment: Comment) => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, comments: [...p.comments, comment] } : p))
  }

  const filteredPosts = posts.filter(p =>
    !search ||
    p.content.toLowerCase().includes(search.toLowerCase()) ||
    p.author.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>

      {/* ── Header ── */}
      <div style={{ padding: '14px 0 10px', borderBottom: '1px solid rgba(106,159,216,0.08)', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 2 }}>
          <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity }} style={{ fontSize: 20, color: C.blue }}>◉</motion.span>
          <h2 style={{ margin: 0, fontFamily: 'Cinzel, serif', fontSize: 20, color: C.text, letterSpacing: '0.06em' }}>NovaNet</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginLeft: 'auto', padding: '3px 10px', background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: 20 }}>
            <motion.div style={{ width: 5, height: 5, borderRadius: '50%', background: C.teal }} animate={{ opacity: [0.4,1,0.4] }} transition={{ duration: 2, repeat: Infinity }} />
            <span style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.18em', color: `${C.teal}70`, textTransform: 'uppercase' }}>
              Live · {posts.length} Posts
            </span>
          </div>
        </div>
        <p style={{ margin: '2px 0 0', fontFamily: 'sans-serif', fontSize: 9, color: C.blue, letterSpacing: '0.2em', textTransform: 'uppercase', opacity: 0.65 }}>
          Public Transmission Feed
        </p>
      </div>

      {/* ── Status ring ── */}
      <StatusFeed />

      {/* ── Transmission composer ── */}
      {isAuthenticated && <TransmissionComposer onPostCreated={handlePostCreated} />}

      {/* ── Search ── */}
      <div style={{ position: 'relative', margin: '12px 0 16px' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search transmissions…"
          style={{ width: '100%', padding: '9px 36px 9px 14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(201,168,76,0.14)', borderRadius: 10, color: C.text, fontFamily: 'sans-serif', fontSize: 12, outline: 'none', boxSizing: 'border-box' }}
        />
        {search && <button onClick={() => setSearch('')} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 13 }}>✕</button>}
      </div>

      {/* ── Loading ── */}
      {postsLoading && (
        <div style={{ padding: '12px 0', display: 'flex', alignItems: 'center', gap: 8, opacity: 0.5 }}>
          <motion.div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(0,212,170,0.3)', borderTopColor: C.teal }} animate={{ rotate: 360 }} transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }} />
          <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.dim, letterSpacing: '0.15em' }}>Tuning to the field…</span>
        </div>
      )}

      {/* ── Empty state ── */}
      {!postsLoading && filteredPosts.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', opacity: 0.5 }}>
          <span style={{ fontSize: 32 }}>◉</span>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 13, color: C.teal, marginTop: 12, letterSpacing: '0.1em' }}>
            {search ? 'No transmissions match that signal.' : 'The field is open. Be the first to transmit.'}
          </p>
          {!isAuthenticated && !search && (
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.dim, marginTop: 8 }}>Sign in to transmit to the field.</p>
          )}
        </div>
      )}

      {/* ── Feed ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingBottom: 100 }}>
        {filteredPosts.map(post => (
          <PostCard
            key={post.id}
            post={post}
            onReact={t => handleReact(post.id, t)}
            onCommentAdded={handleCommentAdded}
          />
        ))}
      </div>

      {filteredPosts.length > 0 && (
        <motion.div animate={{ opacity: [0.3,0.6,0.3] }} transition={{ duration: 4, repeat: Infinity }} style={{ textAlign: 'center', padding: '20px 0 80px', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.4em', textTransform: 'uppercase', color: `${C.gold}40` }}>
          ⟐ End of Transmission ⟐
        </motion.div>
      )}

      {/* ── Floating ReasoMate button ── */}
      <motion.button
        onClick={() => setMessengerOpen(v => !v)}
        whileHover={{ scale: 1.07 }} whileTap={{ scale: 0.94 }}
        style={{ position: 'fixed', bottom: 24, right: 20, width: 52, height: 52, borderRadius: '50%', background: messengerOpen ? 'rgba(106,159,216,0.25)' : 'rgba(106,159,216,0.15)', border: `1px solid ${C.blue}55`, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: 100, boxShadow: `0 4px 24px rgba(0,0,0,0.5), 0 0 0 1px ${C.blue}20` }}
      >
        <span style={{ fontSize: 20 }}>✉</span>
      </motion.button>

      {/* ── ReasoMate sliding panel ── */}
      <AnimatePresence>
        {messengerOpen && (
          <>
            <motion.div key="rm-bg" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMessengerOpen(false)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(2,3,10,0.55)', backdropFilter: 'blur(4px)', zIndex: 101 }}
            />
            <motion.div key="rm-panel" initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 340, damping: 36, mass: 0.9 }}
              style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 320, zIndex: 102, background: 'rgba(9,10,22,0.97)', borderLeft: `1px solid ${C.blue}22`, backdropFilter: 'blur(32px)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
            >
              <div style={{ padding: '14px 16px', borderBottom: '1px solid rgba(106,159,216,0.12)', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                <span style={{ fontSize: 16, color: C.blue }}>✉</span>
                <span style={{ fontFamily: 'Cinzel, serif', fontSize: 13, color: C.blue, flex: 1 }}>ReasoMate</span>
                <button onClick={() => setMessengerOpen(false)} style={{ background: 'none', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 16, padding: '2px 4px', borderRadius: 4 }}>✕</button>
              </div>
              <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <ReasoMatePanel onClose={() => setMessengerOpen(false)} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
