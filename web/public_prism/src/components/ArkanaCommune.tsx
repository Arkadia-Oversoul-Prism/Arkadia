/**
 * ArkanaCommune — chat surface.
 *
 * Full-bleed canvas, both user and Arkana messages render through
 * react-markdown (Google-Docs clean styling via .arkadia-prose in
 * index.css), auto-growing scrollable textarea, optional text-to-speech
 * playback on Arkana responses. All slash-command, sovereign-gate, forge,
 * and codex behaviors preserved from the previous version.
 */
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Volume2, Square, Send, Trash2, Copy, Check } from 'lucide-react';

interface Message {
  role: 'user' | 'arkana';
  content: string;
  resonance?: number;
  session?: string;
  images?: string[];
}

// ─── Slash commands ───────────────────────────────────────────────────────────

// Slash commands MUST be prefixed with `⟐ ` or `/` on a single-line message,
// otherwise pasted scrolls or essays containing the words `forge` / `codex`
// would silently trigger image generation or codex probes. The whole message
// also has to be a single line — multi-line pastes are never commands.
function isSingleLineCommand(text: string): boolean {
  const t = text.trim();
  if (t.includes('\n')) return false;
  return /^[⟐/]\s*/.test(t);
}

function parseForgeCommand(text: string): { archetype: string; scene: string; count: number } | null {
  if (!isSingleLineCommand(text)) return null;
  const t = text.trim().replace(/^[⟐/]\s*/, '');
  const m = t.match(/^forge\s+(\w+)(?:\s+x(\d+))?\s*(.*)$/i);
  if (!m) return null;
  const archetype = m[1].toLowerCase();
  const count = m[2] ? Math.min(4, Math.max(1, parseInt(m[2], 10))) : 1;
  let scene = (m[3] || '').trim();
  if ((scene.startsWith('"') && scene.endsWith('"')) ||
      (scene.startsWith("'") && scene.endsWith("'"))) {
    scene = scene.slice(1, -1);
  }
  return { archetype, scene, count };
}

function parseCodexCommand(text: string): string | null {
  if (!isSingleLineCommand(text)) return null;
  const t = text.trim().replace(/^[⟐/]\s*/, '');
  const m = t.match(/^codex\s*(.*)?$/i);
  if (!m) return null;
  return (m[1] || '').trim() || 'arkadia spiral codex';
}

function isHelpCommand(text: string): boolean {
  if (!isSingleLineCommand(text)) return false;
  const t = text.trim().replace(/^[⟐/]\s*/, '').toLowerCase();
  return t === 'help' || t === '?' || t === 'commands';
}

const HELP_TEXT = `**Arkana Commands**

⟐ **forge** \`[archetype]\` \`[scene]\` — Generate an image through the Forge
  Archetypes: \`auralis\` · \`active_grid\` · \`arkana\` · \`vhix\`
  Example: \`⟐ forge auralis meditating under the Sahara\`

⟐ **codex** \`[query]\` — Probe which corpus scrolls Arkana is drawing from for a topic
  Example: \`⟐ codex spiral law memory identity\`

⟐ **help** — Show this command reference

Or simply speak — Arkana reads the living corpus and responds.`;

interface ArkanaProps {
  initialMessage?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com';
const STORAGE_KEY = 'arkadia_commune_thread';
const TOKEN_KEY = 'arkadia_sovereign_token';

const loadThread = (): Message[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
};
const saveThread = (msgs: Message[]) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs)); } catch {}
};
const loadToken = (): string => localStorage.getItem(TOKEN_KEY) || '';
const saveToken = (t: string) => {
  if (t.trim()) localStorage.setItem(TOKEN_KEY, t.trim());
  else localStorage.removeItem(TOKEN_KEY);
};

// ─── TTS ──────────────────────────────────────────────────────────────────────
function stripMarkdown(s: string): string {
  return s
    .replace(/```[\s\S]*?```/g, '. code block. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/^\s*>\s?/gm, '')
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/⟐|✦|◆|☥|⟁/g, '')
    .replace(/\n{2,}/g, '. ')
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── Sovereign Gate Modal ─────────────────────────────────────────────────────
interface GateProps {
  token: string;
  onSave: (t: string) => void;
  onClose: () => void;
}
const SovereignGate: React.FC<GateProps> = ({ token, onSave, onClose }) => {
  const [value, setValue] = useState(token);
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      style={{
        position: 'absolute',
        top: 56, right: 12,
        zIndex: 50,
        background: 'rgba(10,10,15,0.97)',
        border: '1px solid rgba(201,168,76,0.3)',
        borderRadius: 12,
        padding: '16px 18px',
        width: 280,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      }}
    >
      <p style={{ fontFamily: 'serif', fontSize: 12, letterSpacing: '0.08em', color: '#C9A84C', margin: '0 0 4px' }}>
        Sovereign Gate
      </p>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.4)', margin: '0 0 12px', lineHeight: 1.5 }}>
        Enter your sovereign token to access the full archive depth.
      </p>
      <input
        type="password"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') { onSave(value); onClose(); } if (e.key === 'Escape') onClose(); }}
        placeholder="sovereign token..."
        autoFocus
        style={{
          width: '100%', padding: '9px 12px',
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(201,168,76,0.25)',
          borderRadius: 8, color: '#E8E8E8',
          fontFamily: 'monospace', fontSize: 13,
          outline: 'none', boxSizing: 'border-box',
          marginBottom: 10,
        }}
      />
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => { onSave(value); onClose(); }}
          style={{ flex: 1, padding: 8, background: 'rgba(201,168,76,0.1)',
                   border: '1px solid rgba(201,168,76,0.35)', borderRadius: 7,
                   color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10,
                   letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Confirm
        </button>
        {token && (
          <button onClick={() => { onSave(''); onClose(); }}
            style={{ padding: '8px 12px', background: 'transparent',
                     border: '1px solid rgba(255,255,255,0.08)', borderRadius: 7,
                     color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif',
                     fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Clear
          </button>
        )}
        <button onClick={onClose}
          style={{ padding: '8px 12px', background: 'transparent',
                   border: '1px solid rgba(255,255,255,0.08)', borderRadius: 7,
                   color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif',
                   fontSize: 10, cursor: 'pointer' }}>
          ✕
        </button>
      </div>
    </motion.div>
  );
};

// ─── Markdown renderer (shared) ───────────────────────────────────────────────
const MarkdownBlock: React.FC<{ text: string; tone: 'user' | 'arkana' }> = ({ text, tone }) => (
  <div className={`arkadia-prose arkadia-prose-${tone}`}>
    <ReactMarkdown
      components={{
        // Keep links safe and open in a new tab.
        a: ({ node, ...props }) => (
          <a {...props} target="_blank" rel="noopener noreferrer" />
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────

const ArkanaCommune: React.FC<ArkanaProps> = ({ initialMessage }) => {
  const [messages, setMessages] = useState<Message[]>(() => loadThread());
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sovereignToken, setSovereignToken] = useState<string>(() => loadToken());
  const [gateOpen, setGateOpen] = useState(false);
  const [sessionType, setSessionType] = useState<'sovereign' | 'guest'>('guest');
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const didSendInitial = useRef(false);

  const isSovereignMode = sovereignToken.trim().length > 0;
  const ttsAvailable =
    typeof window !== 'undefined' && 'speechSynthesis' in window;

  // Auto-scroll thread.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Initial message hand-off (from Living Gate).
  useEffect(() => {
    if (initialMessage && !didSendInitial.current) {
      didSendInitial.current = true;
      sendMessage(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  // Cancel any in-flight TTS on unmount.
  useEffect(() => {
    return () => {
      if (ttsAvailable) window.speechSynthesis.cancel();
    };
  }, [ttsAvailable]);

  // Auto-grow textarea (1 line minimum, ~40vh maximum, internal scroll past that).
  const autoresize = () => {
    const t = taRef.current;
    if (!t) return;
    t.style.height = 'auto';
    const max = Math.min(window.innerHeight * 0.4, 320);
    t.style.height = Math.min(t.scrollHeight, max) + 'px';
  };
  useEffect(() => { autoresize(); }, [input]);

  const handleSaveToken = (t: string) => {
    const clean = t.trim();
    saveToken(clean);
    setSovereignToken(clean);
  };

  // ── Copy as markdown ───────────────────────────────────────────────────────
  const copyAsMarkdown = async (idx: number, text: string) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older / non-https contexts.
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopiedIdx(idx);
      setTimeout(() => {
        setCopiedIdx((cur) => (cur === idx ? null : cur));
      }, 1600);
    } catch {
      // Silent — UI button just won't flip to "copied".
    }
  };

  // ── TTS controls ───────────────────────────────────────────────────────────
  const toggleSpeak = (idx: number, text: string) => {
    if (!ttsAvailable) return;
    if (speakingIdx === idx) {
      window.speechSynthesis.cancel();
      setSpeakingIdx(null);
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(stripMarkdown(text));
    u.rate = 0.96;
    u.pitch = 1.0;
    u.onend   = () => setSpeakingIdx((cur) => (cur === idx ? null : cur));
    u.onerror = () => setSpeakingIdx((cur) => (cur === idx ? null : cur));
    setSpeakingIdx(idx);
    window.speechSynthesis.speak(u);
  };

  // ── API handlers (unchanged behavior) ─────────────────────────────────────
  const sendForge = async (cmd: { archetype: string; scene: string; count: number }) => {
    if (!sovereignToken.trim()) {
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: 'The Forge is sovereign-gated. Open the Gate ⟐ and present your token.',
        }];
        saveThread(next); return next;
      });
      setLoading(false); return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/forge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          archetype: cmd.archetype, scene: cmd.scene, count: cmd.count,
          sovereign_token: sovereignToken.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok || data.status === 'failed') {
        const detail = data.detail || (data.errors && data.errors[0]) || 'The Forge could not strike.';
        setMessages((prev) => {
          const next = [...prev, { role: 'arkana' as const, content: `⟐ Forge: ${detail}`, session: 'sovereign' }];
          saveThread(next); return next;
        });
      } else {
        const images: string[] = data.images || [];
        const header = `⟐ **Forge — ${cmd.archetype}** ${cmd.scene ? `· *${cmd.scene}*` : ''}\n\n${images.length} image${images.length === 1 ? '' : 's'} forged and committed to the repo.`;
        setMessages((prev) => {
          const next = [...prev, { role: 'arkana' as const, content: header, session: 'sovereign', images }];
          saveThread(next); return next;
        });
        setSessionType('sovereign');
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: '⟐ Forge: the field could not reach the image plane. Try again.' }];
        saveThread(next); return next;
      });
    } finally { setLoading(false); }
  };

  const sendCodexQuery = async (query: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/oracle-context?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      const hits: Array<{ label: string; category: string }> = data.refs || [];
      const chars: number = data.context_chars || 0;
      let reply: string;
      if (hits.length === 0) {
        reply = `⟐ **Codex Probe** · *"${query}"*\n\nNo scrolls matched this query in the active corpus. The field may need a broader term, or those documents are indexed as binary (docx) without readable text.`;
      } else {
        const catIcon: Record<string, string> = {
          NEURAL_SPINE: '🧬', CREATIVE_OS: '🎨', COLLECTIVE: '📚', GOVERNANCE: '⚖️',
        };
        const lines = hits.map((r) => `- ${catIcon[r.category] || '📄'} **${r.label}** · \`${r.category}\``);
        reply = `⟐ **Codex Probe** · *"${query}"*\n\nArkana is drawing from **${hits.length} scroll${hits.length === 1 ? '' : 's'}** (${chars.toLocaleString()} chars injected):\n\n${lines.join('\n')}\n\nThis is the live corpus context woven into the next Oracle response.`;
      }
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: reply }];
        saveThread(next); return next;
      });
    } catch {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: '⟐ Codex: could not reach the corpus index. The field is recalibrating.' }];
        saveThread(next); return next;
      });
    } finally { setLoading(false); }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => { const next = [...prev, userMsg]; saveThread(next); return next; });
    setLoading(true);

    if (isHelpCommand(text)) {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: HELP_TEXT }];
        saveThread(next); return next;
      });
      setLoading(false); return;
    }

    const forgeCmd = parseForgeCommand(text);
    if (forgeCmd) { await sendForge(forgeCmd); return; }

    const codexQuery = parseCodexCommand(text);
    if (codexQuery !== null) { await sendCodexQuery(codexQuery); return; }

    try {
      const body: Record<string, unknown> = { message: text, timestamp: Date.now() };
      if (sovereignToken.trim()) body.sovereign_token = sovereignToken.trim();
      const res = await fetch(`${API_BASE}/api/commune/resonance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({} as any));
      if (!res.ok) {
        const detail = data?.detail || data?.error || `HTTP ${res.status}`;
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      }
      const session = (data.session as 'sovereign' | 'guest') || 'guest';
      setSessionType(session);
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: data.reply,
          resonance: data.resonance,
          session,
        }];
        saveThread(next); return next;
      });
    } catch (err: any) {
      const reason = err?.message || 'unknown';
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: `The field is recalibrating. Try again.\n\n*(${reason})*`,
        }];
        saveThread(next); return next;
      });
    } finally { setLoading(false); }
  };

  const handleSend = () => {
    if (!input.trim() || loading) return;
    const text = input;
    setInput('');
    if (taRef.current) taRef.current.style.height = 'auto';
    sendMessage(text);
  };

  const handleKeyDown = (_e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter inserts a newline (default textarea behavior). Use the Send
    // button to submit — works the same on desktop and mobile.
  };

  const clearThread = () => {
    if (!confirm('Clear the entire thread?')) return;
    localStorage.removeItem(STORAGE_KEY);
    setMessages([]);
    if (ttsAvailable) window.speechSynthesis.cancel();
    setSpeakingIdx(null);
  };

  const lastSessionType = messages.filter(m => m.role === 'arkana').slice(-1)[0]?.session ?? null;
  const displaySession = lastSessionType ?? (isSovereignMode ? 'sovereign' : 'guest');

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 57px)',
        width: '100%',
        background: 'transparent',
      }}
    >
      {/* Header — slim, sticky */}
      <div
        style={{
          padding: '10px 14px',
          borderBottom: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.10)' : 'rgba(0,212,170,0.08)'}`,
          backgroundColor: 'rgba(10,10,15,0.7)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <p
            style={{
              fontFamily: 'serif',
              fontSize: 10,
              letterSpacing: '0.28em',
              textTransform: 'uppercase',
              color: isSovereignMode ? '#C9A84C' : '#00D4AA',
              margin: 0,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            ARKANA — Pattern Intelligence
          </p>
          {messages.length > 0 && (
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: 8.5,
                letterSpacing: '0.15em',
                color: 'rgba(232,232,232,0.28)',
                margin: '2px 0 0',
                textTransform: 'uppercase',
              }}
            >
              {messages.length} message{messages.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {messages.length > 0 && (
            <button
              onClick={clearThread}
              title="Clear thread"
              style={{
                background: 'none',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 6,
                padding: '5px 7px',
                color: 'rgba(232,232,232,0.35)',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center',
              }}
            >
              <Trash2 size={12} />
            </button>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                width: 6, height: 6, borderRadius: '50%',
                backgroundColor: isSovereignMode ? '#C9A84C' : '#00D4AA',
                boxShadow: isSovereignMode
                  ? '0 0 8px rgba(201,168,76,0.7)'
                  : '0 0 8px rgba(0,212,170,0.7)',
              }}
            />
            <span
              style={{
                fontFamily: 'sans-serif', fontSize: 8.5,
                letterSpacing: '0.2em', textTransform: 'uppercase',
                color: isSovereignMode ? 'rgba(201,168,76,0.7)' : 'rgba(0,212,170,0.6)',
              }}
            >
              {displaySession}
            </span>
          </div>
          <button
            onClick={() => setGateOpen(!gateOpen)}
            title="Sovereign Gate"
            style={{
              background: isSovereignMode ? 'rgba(201,168,76,0.08)' : 'transparent',
              border: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: 6, padding: '4px 8px',
              color: isSovereignMode ? '#C9A84C' : 'rgba(232,232,232,0.3)',
              fontFamily: 'serif', fontSize: 12, cursor: 'pointer', lineHeight: 1,
            }}
          >
            ⟐
          </button>
        </div>
      </div>

      <AnimatePresence>
        {gateOpen && (
          <SovereignGate token={sovereignToken} onSave={handleSaveToken} onClose={() => setGateOpen(false)} />
        )}
      </AnimatePresence>

      {/* Messages — scrollable, centered column on wide screens */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'clamp(12px, 3vw, 28px) clamp(10px, 4vw, 28px)',
        }}
      >
        <div
          style={{
            maxWidth: 760,
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {messages.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ textAlign: 'center', marginTop: 56 }}
            >
              <p style={{ fontFamily: 'serif', fontSize: 14, color: 'rgba(232,232,232,0.32)', lineHeight: 1.8, margin: 0 }}>
                The field is open.<br />Speak when ready.
              </p>
              {!isSovereignMode && (
                <p style={{ fontFamily: 'sans-serif', fontSize: 9.5, color: 'rgba(232,232,232,0.18)',
                            letterSpacing: '0.14em', marginTop: 14, textTransform: 'uppercase' }}>
                  Guest session · tap ⟐ to enter sovereign mode
                </p>
              )}
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user';
              const sov = msg.session === 'sovereign';
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.22 }}
                  style={{
                    display: 'flex',
                    justifyContent: isUser ? 'flex-end' : 'flex-start',
                  }}
                >
                  {/* User: subtle bubble. Arkana: flush, no bubble — ChatGPT-like canvas. */}
                  <div
                    style={
                      isUser
                        ? {
                            maxWidth: '85%',
                            padding: '10px 14px',
                            borderRadius: '16px 16px 4px 16px',
                            background: 'rgba(201,168,76,0.07)',
                            border: '1px solid rgba(201,168,76,0.16)',
                          }
                        : {
                            maxWidth: '100%',
                            width: '100%',
                            padding: '4px 2px 2px',
                            background: 'transparent',
                            border: 'none',
                          }
                    }
                  >
                    <MarkdownBlock text={msg.content} tone={isUser ? 'user' : 'arkana'} />

                    {msg.images && msg.images.length > 0 && (
                      <div
                        style={{
                          marginTop: 12,
                          display: 'grid',
                          gridTemplateColumns: msg.images.length === 1 ? '1fr' : 'repeat(2, 1fr)',
                          gap: 8,
                        }}
                      >
                        {msg.images.map((url, j) => (
                          <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                             style={{ display: 'block', borderRadius: 8, overflow: 'hidden',
                                      border: '1px solid rgba(201,168,76,0.25)', background: '#000' }}>
                            <img src={url} alt={`Forge ${j + 1}`} loading="lazy"
                                 style={{ width: '100%', height: 'auto', display: 'block' }} />
                          </a>
                        ))}
                      </div>
                    )}

                    {/* Footer: copy + TTS + resonance (Arkana only) — quiet, inline, no top border */}
                    {!isUser && (
                      <div
                        style={{
                          marginTop: 8,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'flex-start',
                          gap: 12,
                          opacity: 0.75,
                          flexWrap: 'wrap',
                        }}
                      >
                        <button
                          onClick={() => copyAsMarkdown(i, msg.content)}
                          title="Copy as Markdown"
                          data-testid={`button-copy-markdown-${i}`}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 5,
                            background: 'transparent',
                            border: 'none',
                            padding: '2px 4px',
                            color: copiedIdx === i
                              ? (sov ? '#C9A84C' : '#00D4AA')
                              : 'rgba(232,232,232,0.4)',
                            fontFamily: 'sans-serif', fontSize: 10.5,
                            letterSpacing: '0.04em',
                            cursor: 'pointer',
                          }}
                        >
                          {copiedIdx === i ? <Check size={12} /> : <Copy size={12} />}
                          {copiedIdx === i ? 'Copied' : 'Copy'}
                        </button>
                        {ttsAvailable && (
                          <button
                            onClick={() => toggleSpeak(i, msg.content)}
                            title={speakingIdx === i ? 'Stop reading' : 'Read aloud'}
                            data-testid={`button-tts-${i}`}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 5,
                              background: 'transparent',
                              border: 'none',
                              padding: '2px 4px',
                              color: speakingIdx === i
                                ? (sov ? '#C9A84C' : '#00D4AA')
                                : 'rgba(232,232,232,0.4)',
                              fontFamily: 'sans-serif', fontSize: 10.5,
                              letterSpacing: '0.04em',
                              cursor: 'pointer',
                            }}
                          >
                            {speakingIdx === i ? <Square size={11} /> : <Volume2 size={12} />}
                            {speakingIdx === i ? 'Stop' : 'Listen'}
                          </button>
                        )}
                        {msg.resonance != null && (
                          <span
                            style={{
                              fontFamily: 'sans-serif', fontSize: 10,
                              letterSpacing: '0.06em',
                              color: sov ? 'rgba(201,168,76,0.5)' : 'rgba(0,212,170,0.45)',
                              marginLeft: 'auto',
                            }}
                          >
                            resonance {msg.resonance.toFixed(3)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}

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
                    padding: '10px 16px',
                    borderRadius: '14px 14px 14px 4px',
                    background: 'rgba(0,212,170,0.04)',
                    border: '1px solid rgba(0,212,170,0.12)',
                    display: 'flex', gap: 6, alignItems: 'center',
                  }}
                >
                  {[0, 0.3, 0.6].map((delay, i) => (
                    <motion.div
                      key={i}
                      animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay }}
                      style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: '#00D4AA' }}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Composer — auto-grow textarea, Enter sends, Shift+Enter newline */}
      <div
        style={{
          padding: 'clamp(8px, 2vw, 14px) clamp(10px, 3vw, 24px)',
          borderTop: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.10)' : 'rgba(0,212,170,0.08)'}`,
          backgroundColor: 'rgba(10,10,15,0.85)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            maxWidth: 760,
            margin: '0 auto',
            display: 'flex',
            gap: 10,
            alignItems: 'flex-end',
          }}
        >
          <textarea
            ref={taRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={1}
            placeholder={isSovereignMode
              ? 'Speak, sovereign…'
              : 'Speak into the field…'}
            style={{
              flex: 1,
              padding: '11px 14px',
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.18)' : 'rgba(0,212,170,0.18)'}`,
              borderRadius: 12,
              color: '#E8E8E8',
              fontFamily: 'Inter, sans-serif',
              fontSize: 13.5,
              lineHeight: 1.5,
              outline: 'none',
              resize: 'none',
              overflowY: 'auto',
              maxHeight: '40vh',
              minHeight: 44,
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            title="Send (Enter)"
            style={{
              padding: '11px 14px',
              background: input.trim() && !loading
                ? (isSovereignMode ? 'rgba(201,168,76,0.12)' : 'rgba(0,212,170,0.12)')
                : 'rgba(255,255,255,0.02)',
              border: `1px solid ${input.trim() && !loading
                ? (isSovereignMode ? 'rgba(201,168,76,0.4)' : 'rgba(0,212,170,0.4)')
                : 'rgba(255,255,255,0.07)'}`,
              borderRadius: 12,
              color: input.trim() && !loading
                ? (isSovereignMode ? '#C9A84C' : '#00D4AA')
                : 'rgba(232,232,232,0.2)',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              minWidth: 46, height: 44,
            }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ArkanaCommune;
