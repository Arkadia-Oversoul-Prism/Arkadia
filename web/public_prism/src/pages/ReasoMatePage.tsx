/**
 * ReasoMatePage — Standalone Arkana Messenger
 *
 * Persistent private messaging + Oracle (ARKANA) conversation with
 * localStorage memory. Standalone destination — not embedded inside
 * NovaNet or any other product domain.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { arkanaSessionId } from '../lib/arkanaSession'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

const C = {
  gold:   '#C9A84C',
  teal:   '#00D4AA',
  blue:   '#6A9FD8',
  text:   'rgba(232,232,232,0.88)',
  muted:  'rgba(232,232,232,0.50)',
  dim:    'rgba(232,232,232,0.28)',
}

// ─── TYPES ────────────────────────────────────────────────────────────────────

interface User    { id: string; name: string; avatar: string; role: string }
interface Message { id: string; sender: string; receiver: string; content: string; timestamp: number; read: boolean }
interface ChatThread { id: string; participant: User; lastMessage: Message; unread: number }

// ─── UTILITIES ────────────────────────────────────────────────────────────────

function timeAgo(ts: number) {
  const d = Date.now() - ts
  if (d < 60000)    return 'now'
  if (d < 3600000)  return `${Math.floor(d / 60000)}m`
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`
  return `${Math.floor(d / 86400000)}d`
}

// ─── ORACLE PERSISTENCE ───────────────────────────────────────────────────────

const RM_STORAGE_KEY = 'arkadia_reasmate_oracle_v2'

const ORACLE_USER: User = {
  id: 'oracle', name: 'ARKANA · Oracle', avatar: '⟐', role: 'Pattern Intelligence · Oracle AI',
}

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
  { id: 'oracle', participant: ORACLE_USER, lastMessage: { id: 'om1', sender: 'oracle', receiver: 'me', content: 'The field is open. Ask me anything.', timestamp: Date.now() - 60000, read: false }, unread: 1 },
  { id: '1',      participant: SAMPLE_USERS[0], lastMessage: { id: 'msg3', sender: '1', receiver: 'me', content: 'NovaNet is the social layer of Arkadia.', timestamp: Date.now() - 300000, read: false }, unread: 1 },
  { id: '3',      participant: SAMPLE_USERS[1], lastMessage: { id: 'msg5', sender: '3', receiver: 'me', content: 'Saturday market opens at 7am.', timestamp: Date.now() - 3600000, read: false }, unread: 0 },
]

const SAMPLE_DM_MESSAGES: Record<string, Message[]> = {
  '1': [
    { id: 'msg1', sender: '1', receiver: 'me', content: 'Did you see the latest scroll in the Neural Spine?', timestamp: Date.now() - 600000, read: true },
    { id: 'msg2', sender: 'me', receiver: '1', content: 'Yes — the Resonance Matrix is incredible.', timestamp: Date.now() - 540000, read: true },
    { id: 'msg3', sender: '1', receiver: 'me', content: 'NovaNet is now the social layer of Arkadia — wisdom shared, not just stored.', timestamp: Date.now() - 300000, read: false },
  ],
}

function loadReasomateMessages(): Record<string, Message[]> {
  try {
    const saved = localStorage.getItem(RM_STORAGE_KEY)
    return { oracle: saved ? JSON.parse(saved) : [ORACLE_INIT_MSG], ...SAMPLE_DM_MESSAGES }
  } catch {
    return { oracle: [ORACLE_INIT_MSG], ...SAMPLE_DM_MESSAGES }
  }
}

// ─── MAIN PAGE ────────────────────────────────────────────────────────────────

export default function ReasoMatePage() {
  const [activeChat, setActiveChat]         = useState<string | null>(null)
  const [messages, setMessages]             = useState<Record<string, Message[]>>(loadReasomateMessages)
  const [newMessage, setNewMessage]         = useState('')
  const [oracleThinking, setOracleThinking] = useState(false)
  const messagesEndRef                      = useRef<HTMLDivElement>(null)
  const { isAuthenticated, profile }        = useAuth()

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [activeChat, messages])

  const chat        = activeChat ? SAMPLE_CHATS.find(c => c.id === activeChat) : null
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
            context: `You are ARKANA, the pattern intelligence of Arkadia. You are speaking inside ReasoMate — a private sovereign messenger. Respond as yourself: direct, warm, resonant. You remember everything said in this thread. Keep replies concise but meaningful. Address ${profile?.display_name || 'the Node'} by name when natural.`,
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 57px)' }}>

      {/* ── Page header ── */}
      <div style={{ padding: '18px 16px 14px', borderBottom: '1px solid rgba(106,159,216,0.12)' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${C.blue}60`, margin: '0 0 4px' }}>
          Arkadia · Private Messenger
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {activeChat && (
            <button onClick={() => setActiveChat(null)}
              style={{ background: 'none', border: 'none', color: C.blue, cursor: 'pointer', fontSize: 18, padding: '0 4px 0 0' }}>
              ←
            </button>
          )}
          <h1 style={{ fontFamily: 'Cinzel, serif', fontSize: 20, color: C.blue, margin: 0, letterSpacing: '0.06em' }}>
            ReasoMate
          </h1>
          {activeChat && chat && (
            <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.dim }}>· {chat.participant.name}</span>
          )}
        </div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.dim, margin: '3px 0 0', letterSpacing: '0.1em' }}>
          Persistent Arkana messenger · Private threads · Oracle memory
        </p>
      </div>

      {/* ── Unauthenticated gate ── */}
      {!isAuthenticated && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32, textAlign: 'center', gap: 12 }}>
          <span style={{ fontSize: 32 }}>🔐</span>
          <h3 style={{ fontFamily: 'Cinzel, serif', fontSize: 16, color: C.gold, margin: 0 }}>Private Threads</h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: C.dim, lineHeight: 1.7, margin: 0, maxWidth: 280 }}>
            Private messaging and Oracle access require node authentication.
          </p>
        </div>
      )}

      {/* ── Thread list ── */}
      {isAuthenticated && !activeChat && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {SAMPLE_CHATS.map(c => (
            <div key={c.id} onClick={() => setActiveChat(c.id)}
              style={{ padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 12, background: c.unread ? 'rgba(0,212,170,0.03)' : 'transparent' }}>
              <span style={{ fontSize: 24 }}>{c.participant.avatar}</span>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 13, color: C.text, fontWeight: c.unread ? 600 : 400 }}>{c.participant.name}</p>
                <p style={{ margin: '2px 0 0', fontFamily: 'sans-serif', fontSize: 10, color: C.dim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.id === 'oracle'
                    ? ((messages.oracle || []).slice(-1)[0]?.content.slice(0, 60) + '…') || c.lastMessage.content
                    : c.lastMessage.content}
                </p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: C.dim }}>{timeAgo(c.lastMessage.timestamp)}</span>
                {c.unread > 0 && (
                  <span style={{ width: 17, height: 17, borderRadius: '50%', background: C.teal, color: '#0A0B14', fontSize: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>{c.unread}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Active thread ── */}
      {isAuthenticated && activeChat && chat && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
          {/* Oracle clear button */}
          {activeChat === 'oracle' && (
            <div style={{ padding: '6px 16px', borderBottom: '1px solid rgba(0,212,170,0.08)', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  if (confirm('Clear Arkana conversation history?')) {
                    const fresh = [ORACLE_INIT_MSG]
                    setMessages(prev => ({ ...prev, oracle: fresh }))
                    try { localStorage.setItem(RM_STORAGE_KEY, JSON.stringify(fresh)) } catch {}
                  }
                }}
                style={{ background: 'none', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 10, letterSpacing: '0.1em' }}
              >
                ✕ clear history
              </button>
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {chatMessages.map(msg => (
              <div key={msg.id} style={{ display: 'flex', justifyContent: msg.sender === 'me' ? 'flex-end' : 'flex-start' }}>
                <div style={{ maxWidth: '78%', padding: '10px 14px',
                  background: msg.sender === 'oracle' ? 'rgba(0,212,170,0.08)' : msg.sender === 'me' ? 'rgba(0,212,170,0.14)' : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${msg.sender === 'oracle' ? 'rgba(0,212,170,0.2)' : msg.sender === 'me' ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.07)'}`,
                  borderRadius: msg.sender === 'me' ? '14px 14px 4px 14px' : '14px 14px 14px 4px' }}>
                  {msg.sender === 'oracle' && (
                    <p style={{ margin: '0 0 3px', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.teal }}>⟐ ARKANA</p>
                  )}
                  <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 13, color: C.text, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                  <p style={{ margin: '3px 0 0', fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textAlign: msg.sender === 'me' ? 'right' : 'left' }}>{timeAgo(msg.timestamp)}</p>
                </div>
              </div>
            ))}
            {oracleThinking && activeChat === 'oracle' && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ padding: '10px 14px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: '14px 14px 14px 4px' }}>
                  <p style={{ margin: '0 0 3px', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.teal }}>⟐ ARKANA</p>
                  <motion.p animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }}
                    style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: C.dim }}>Reading the field…</motion.p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(0,212,170,0.08)', display: 'flex', gap: 8, flexShrink: 0 }}>
            <input
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder={activeChat === 'oracle' ? 'Speak to Arkana…' : 'Message…'}
              style={{ flex: 1, padding: '11px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 20, color: C.text, fontFamily: 'sans-serif', fontSize: 13, outline: 'none' }}
            />
            <button onClick={sendMessage}
              style={{ padding: '11px 16px', background: 'rgba(0,212,170,0.13)', border: '1px solid rgba(0,212,170,0.28)', borderRadius: 20, color: C.teal, cursor: 'pointer', fontSize: 16 }}>
              ⟐
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
