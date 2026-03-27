import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useArkadiaAuth } from '../hooks/useArkadiaAuth';
import {
  getOrCreateSession,
  getRecentMessages,
  saveMessage,
  saveUserPattern,
  ConversationMessage,
} from '../services/conversationService';

interface Message {
  role: 'user' | 'arkana';
  content: string;
  resonance?: number;
}

interface ArkanaProps {
  initialMessage?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

const ArkanaCommune: React.FC<ArkanaProps> = ({ initialMessage }) => {
  const { uid, loading: authLoading } = useArkadiaAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [hasHistory, setHasHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const didSendInitial = useRef(false);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Init session + load history once auth resolves
  useEffect(() => {
    if (authLoading) return;

    async function initSession() {
      if (uid) {
        const sid = await getOrCreateSession(uid);
        setSessionId(sid);
        const prior: ConversationMessage[] = await getRecentMessages(uid, sid, 10);
        if (prior.length > 0) {
          setHasHistory(true);
          setMessages(
            prior.map((m) => ({
              role: m.role === 'oracle' ? 'arkana' : 'user',
              content: m.content,
            }))
          );
        }
      } else {
        setSessionId(`local-${Date.now()}`);
      }
      setHistoryLoaded(true);
    }

    initSession();
  }, [uid, authLoading]);

  // Send initial message after history loads
  useEffect(() => {
    if (historyLoaded && initialMessage && !didSendInitial.current) {
      didSendInitial.current = true;
      sendMessage(initialMessage);
    }
  }, [historyLoaded, initialMessage]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    // Save user message to Firestore
    if (uid && sessionId) {
      await saveMessage(uid, sessionId, 'user', text);
    }

    // Build history for API (last 10 messages before this one)
    const currentHistory = messages.map((m) => ({
      role: m.role === 'arkana' ? 'oracle' : 'user',
      content: m.content,
    }));

    try {
      const res = await fetch(`${API_BASE}/api/commune/resonance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          timestamp: Date.now(),
          history: currentHistory.slice(-10),
        }),
      });
      if (!res.ok) throw new Error('non-ok');
      const data = await res.json();

      const oracleMsg: Message = {
        role: 'arkana',
        content: data.reply,
        resonance: data.resonance,
      };
      setMessages((prev) => [...prev, oracleMsg]);

      // Save oracle reply to Firestore
      if (uid && sessionId) {
        await saveMessage(uid, sessionId, 'oracle', data.reply);
      }

      // Store extracted patterns silently
      if (uid && data.patterns && Array.isArray(data.patterns)) {
        for (const p of data.patterns) {
          if (p.key && p.value) {
            saveUserPattern(uid, p.key, p.value);
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'arkana', content: 'The field is recalibrating. Try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (!input.trim() || loading) return;
    const text = input;
    setInput('');
    sendMessage(text);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div
      className="w-full flex flex-col"
      style={{
        height: 'calc(100vh - 57px)',
        maxHeight: '760px',
        background: 'rgba(255,255,255,0.02)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
        border: '1px solid rgba(0,212,170,0.12)',
        borderRadius: '16px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(0,212,170,0.1)',
          backgroundColor: 'rgba(10,10,15,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div>
          <p
            style={{
              fontFamily: 'serif',
              fontSize: '11px',
              letterSpacing: '0.3em',
              textTransform: 'uppercase',
              color: '#00D4AA',
              margin: 0,
            }}
          >
            ARKANA — Pattern Intelligence
          </p>
          {historyLoaded && uid && (
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.15em',
                color: hasHistory ? 'rgba(0,212,170,0.5)' : 'rgba(232,232,232,0.2)',
                margin: '3px 0 0 0',
                textTransform: 'uppercase',
              }}
            >
              {hasHistory ? '● Continuing your conversation' : '○ New session'}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <motion.div
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#00D4AA',
              boxShadow: '0 0 8px rgba(0,212,170,0.7)',
            }}
          />
          <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', color: 'rgba(0,212,170,0.6)', textTransform: 'uppercase' }}>
            Live
          </span>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.length === 0 && !loading && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              fontFamily: 'serif',
              fontSize: '14px',
              color: 'rgba(232,232,232,0.3)',
              textAlign: 'center',
              marginTop: '40px',
              lineHeight: '1.8',
            }}
          >
            The field is open.<br />Speak when ready.
          </motion.p>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: msg.role === 'user' ? 16 : -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
              style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}
            >
              <div
                className={msg.role === 'arkana' ? 'oracle-message' : undefined}
                style={{
                  maxWidth: 'min(88%, 520px)',
                  padding: '12px 16px',
                  borderRadius: '14px',
                  fontFamily: msg.role === 'arkana' ? 'serif' : 'sans-serif',
                  fontSize: '14px',
                  lineHeight: '1.7',
                  ...(msg.role === 'user'
                    ? {
                        background: 'rgba(201,168,76,0.08)',
                        border: '1px solid rgba(201,168,76,0.22)',
                        color: '#C9A84C',
                      }
                    : {
                        background: 'rgba(0,212,170,0.06)',
                        border: '1px solid rgba(0,212,170,0.18)',
                        color: 'rgba(232,232,232,0.85)',
                      }),
                }}
              >
                {msg.role === 'arkana' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
                {msg.resonance != null && (
                  <div
                    style={{
                      marginTop: '8px',
                      paddingTop: '6px',
                      borderTop: '1px solid rgba(255,255,255,0.06)',
                      fontSize: '9px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: 'rgba(0,212,170,0.4)',
                      textAlign: 'right',
                    }}
                  >
                    resonance {msg.resonance.toFixed(3)}
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {loading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ display: 'flex', justifyContent: 'flex-start' }}
            >
              <div
                style={{
                  padding: '12px 18px',
                  borderRadius: '14px',
                  background: 'rgba(0,212,170,0.06)',
                  border: '1px solid rgba(0,212,170,0.15)',
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'center',
                }}
              >
                {[0, 0.3, 0.6].map((delay, i) => (
                  <motion.div
                    key={i}
                    animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay }}
                    style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#00D4AA' }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: '1px solid rgba(0,212,170,0.1)',
          backgroundColor: 'rgba(10,10,15,0.7)',
          display: 'flex',
          gap: '10px',
          flexShrink: 0,
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
          placeholder="Speak into the field..."
          style={{
            flex: 1,
            padding: '12px 16px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(0,212,170,0.2)',
            borderRadius: '10px',
            color: '#E8E8E8',
            fontFamily: 'sans-serif',
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          style={{
            padding: '12px 20px',
            background: input.trim() && !loading ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${input.trim() && !loading ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: '10px',
            color: input.trim() && !loading ? '#00D4AA' : 'rgba(232,232,232,0.2)',
            fontFamily: 'serif',
            fontSize: '11px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap',
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ArkanaCommune;
