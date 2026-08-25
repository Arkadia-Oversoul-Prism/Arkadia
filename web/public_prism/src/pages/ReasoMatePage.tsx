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
import MarkdownViewer from '../components/MarkdownViewer'
import OracleVoicePlayer from '../components/OracleVoicePlayer'
import { API_BASE } from '../lib/apiConfig'

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

const BASE_CHATS: ChatThread[] = [
  { id: 'oracle', participant: ORACLE_USER, lastMessage: { id: 'om1', sender: 'oracle', receiver: 'me', content: 'The field is open. Ask me anything.', timestamp: Date.now() - 60000, read: false }, unread: 0 },
]

function loadReasomateMessages(): Record<string, Message[]> {
  try {
    const saved = localStorage.getItem(RM_STORAGE_KEY)
    return { oracle: saved ? JSON.parse(saved) : [ORACLE_INIT_MSG] }
  } catch {
    return { oracle: [ORACLE_INIT_MSG] }
  }
}

// ─── MAIN PAGE ────────────────────────────────────────────────────────────────

export default function ReasoMatePage() {
  const [activeChat, setActiveChat]         = useState<string | null>(null)
  const [messages, setMessages]             = useState<Record<string, Message[]>>(loadReasomateMessages)
  const [chats, setChats]                   = useState<ChatThread[]>(BASE_CHATS)
  const [newMessage, setNewMessage]         = useState('')
  const [peerUid, setPeerUid]               = useState('')
  const [oracleThinking, setOracleThinking] = useState(false)
  const [voiceIdx, setVoiceIdx]             = useState<number | null>(null)
  const [dmError, setDmError]               = useState('')
  const messagesEndRef                      = useRef<HTMLDivElement>(null)
  const { isAuthenticated, profile, user }  = useAuth()

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [activeChat, messages])

  // P1-A: load real DM inbox when authenticated
  useEffect(() => {
    if (!user?.idToken) return
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/messages/inbox`, {
          headers: { Authorization: `Bearer ${user.idToken}` },
        })
        if (!res.ok || cancelled) return
        const data = await res.json()
        const convs = (data.conversations || []) as Array<{ peer_uid: string; last_message: { content: string; timestamp: number; sender_uid: string }; count: number }>
        if (cancelled) return
        setChats(prev => {
          const oracle = prev.filter(c => c.id === 'oracle')
          const peers: ChatThread[] = convs.map(c => ({
            id: c.peer_uid,
            participant: { id: c.peer_uid, name: c.peer_uid.slice(0, 10) + '…', avatar: '◈', role: 'Peer' },
            lastMessage: {
              id: 'last',
              sender: c.last_message.sender_uid === user.uid ? 'me' : c.peer_uid,
              receiver: c.last_message.sender_uid === user.uid ? c.peer_uid : 'me',
              content: c.last_message.content,
              timestamp: c.last_message.timestamp,
              read: true,
            },
            unread: 0,
          }))
          return [...oracle, ...peers]
        })
      } catch { /* optional */ }
    })()
    return () => { cancelled = true }
  }, [user?.idToken, user?.uid])

  // Load thread when selecting a peer (not oracle)
  useEffect(() => {
    if (!user?.idToken || !activeChat || activeChat === 'oracle') return
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/messages/thread/${encodeURIComponent(activeChat)}`, {
          headers: { Authorization: `Bearer ${user.idToken}` },
        })
        if (!res.ok || cancelled) return
        const data = await res.json()
        const mapped: Message[] = (data.messages || []).map((m: { id: string; sender_uid: string; recipient_uid: string; content: string; timestamp: number }) => ({
          id: m.id,
          sender: m.sender_uid === user.uid ? 'me' : m.sender_uid,
          receiver: m.recipient_uid === user.uid ? 'me' : m.recipient_uid,
          content: m.content,
          timestamp: m.timestamp,
          read: true,
        }))
        if (!cancelled) setMessages(prev => ({ ...prev, [activeChat]: mapped }))
      } catch { /* optional */ }
    })()
    return () => { cancelled = true }
  }, [activeChat, user?.idToken, user?.uid])

  const chat        = activeChat ? chats.find(c => c.id === activeChat) : null
  const chatMessages = activeChat ? (messages[activeChat] || []) : []

  const openPeer = () => {
    const id = peerUid.trim()
    if (!id) return
    setChats(prev => {
      if (prev.some(c => c.id === id)) return prev
      return [...prev, {
        id,
        participant: { id, name: id.slice(0, 12) + (id.length > 12 ? '…' : ''), avatar: '◈', role: 'Peer' },
        lastMessage: { id: 'n', sender: 'me', receiver: id, content: 'New conversation', timestamp: Date.now(), read: true },
        unread: 0,
      }]
    })
    setActiveChat(id)
    setPeerUid('')
  }

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

    // P1-A: persist peer DMs server-side
    if (activeChat !== 'oracle') {
      if (!user?.idToken) {
        setDmError('Sign in to message other users.')
        return
      }
      try {
        const res = await fetch(`${API_BASE}/api/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${user.idToken}`,
          },
          body: JSON.stringify({ recipient_uid: activeChat, content: sentText }),
        })
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          setDmError(d.detail || `Send failed (${res.status})`)
        } else {
          setDmError('')
        }
      } catch (e) {
        setDmError((e as Error).message || 'Send failed')
      }
      return
    }
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
  }, [newMessage, activeChat, messages, profile, user])

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
          <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: 8 }}>
            <input
              value={peerUid}
              onChange={e => setPeerUid(e.target.value)}
              placeholder="Peer user id (Firebase uid)"
              data-testid="input-peer-uid"
              style={{ flex: 1, padding: '8px 10px', background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(106,159,216,0.25)', borderRadius: 8, color: C.text, fontSize: 12 }}
            />
            <button type="button" onClick={openPeer} data-testid="button-open-peer"
              style={{ padding: '8px 12px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.35)', borderRadius: 8, color: C.teal, fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', cursor: 'pointer' }}>
              Message
            </button>
          </div>
          {dmError && <p style={{ padding: '0 16px', fontSize: 11, color: '#E88C6A' }}>{dmError}</p>}
          {chats.map(c => (
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
            {chatMessages.map((msg, i) => {
              const isOracle = msg.sender === 'oracle'
              const isMe = msg.sender === 'me'
              return (
                <div key={msg.id} style={{ display: 'flex', justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
                  <div style={{ maxWidth: '78%', padding: '10px 14px',
                    background: isOracle ? 'rgba(0,212,170,0.08)' : isMe ? 'rgba(0,212,170,0.14)' : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${isOracle ? 'rgba(0,212,170,0.2)' : isMe ? 'rgba(0,212,170,0.25)' : 'rgba(255,255,255,0.07)'}`,
                    borderRadius: isMe ? '14px 14px 4px 14px' : '14px 14px 14px 4px' }}>
                    {isOracle && (
                      <p style={{ margin: '0 0 3px', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.teal }}>⟐ ARKANA</p>
                    )}
                    {isOracle ? (
                      <div className="arkadia-prose arkadia-prose-arkana" style={{ margin: 0 }}>
                        <MarkdownViewer content={msg.content} compact />
                      </div>
                    ) : (
                      <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 13, color: C.text, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                    )}
                    {/* Oracle voice player — full canvas read-aloud (sonata) */}
                    <AnimatePresence>
                      {isOracle && voiceIdx === i && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} style={{ overflow: 'hidden', marginTop: 8 }}>
                          <OracleVoicePlayer text={msg.content} accent={C.teal} autoPlay label="REASOMATE · ARKANA" />
                        </motion.div>
                      )}
                    </AnimatePresence>
                    {isOracle && (
                      <button
                        onClick={() => setVoiceIdx(prev => prev === i ? null : i)}
                        style={{ marginTop: 6, background: 'none', border: 'none', color: voiceIdx === i ? C.teal : C.dim, cursor: 'pointer', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', padding: 0, display: 'flex', alignItems: 'center', gap: 4 }}
                      >
                        {voiceIdx === i ? '✕ close voice' : '▶ listen'}
                      </button>
                    )}
                    <p style={{ margin: '3px 0 0', fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textAlign: isMe ? 'right' : 'left' }}>{timeAgo(msg.timestamp)}</p>
                  </div>
                </div>
              )
            })}
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
