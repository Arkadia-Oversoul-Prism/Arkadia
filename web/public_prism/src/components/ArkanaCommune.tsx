import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: 'user' | 'arkana';
  content: string;
  resonance?: number;
  session?: string;
  images?: string[];
}

// ─── Forge slash command parser ───────────────────────────────────────────────
// Accepts:  ⟐ forge auralis "scene text"
//           /forge auralis scene text
//           forge auralis scene text
function parseForgeCommand(text: string): { archetype: string; scene: string; count: number } | null {
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

// ─── Codex RAG probe command parser ───────────────────────────────────────────
// Accepts:  ⟐ codex memory spiral law
//           /codex what does the Oversoul Prism say about identity?
function parseCodexCommand(text: string): string | null {
  const t = text.trim().replace(/^[⟐/]\s*/, '');
  const m = t.match(/^codex\s*(.*)?$/i);
  if (!m) return null;
  return (m[1] || '').trim() || 'arkadia spiral codex';
}

// ─── Help command parser ───────────────────────────────────────────────────────
function isHelpCommand(text: string): boolean {
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
  } catch {
    return [];
  }
};

const saveThread = (msgs: Message[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
  } catch {}
};

const loadToken = (): string =>
  localStorage.getItem(TOKEN_KEY) || '';

const saveToken = (t: string) => {
  if (t.trim()) localStorage.setItem(TOKEN_KEY, t.trim());
  else localStorage.removeItem(TOKEN_KEY);
};

// ─── Minimal markdown renderer ────────────────────────────────────────────────
// Handles the most common patterns in ARKANA responses without external deps.
function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith('```')) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push(
        <pre
          key={i}
          style={{
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(0,212,170,0.15)',
            borderRadius: '8px',
            padding: '12px 14px',
            fontFamily: 'monospace',
            fontSize: '12px',
            color: 'rgba(232,232,232,0.7)',
            overflowX: 'auto',
            margin: '8px 0',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {codeLines.join('\n')}
        </pre>
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      result.push(
        <hr key={i} style={{ border: 'none', borderTop: '1px solid rgba(201,168,76,0.15)', margin: '10px 0' }} />
      );
      i++;
      continue;
    }

    // Headings
    const h3 = line.match(/^###\s+(.+)/);
    const h2 = line.match(/^##\s+(.+)/);
    const h1 = line.match(/^#\s+(.+)/);
    if (h1 || h2 || h3) {
      const text = (h1 || h2 || h3)![1];
      const size = h1 ? '16px' : h2 ? '14px' : '13px';
      result.push(
        <p key={i} style={{ fontFamily: 'serif', fontSize: size, color: '#C9A84C', margin: '10px 0 4px', letterSpacing: '0.03em' }}>
          {inlineMarkdown(text)}
        </p>
      );
      i++;
      continue;
    }

    // Empty line
    if (!line.trim()) {
      result.push(<div key={i} style={{ height: '6px' }} />);
      i++;
      continue;
    }

    // Regular paragraph
    result.push(
      <p key={i} style={{ margin: '2px 0', lineHeight: '1.75' }}>
        {inlineMarkdown(line)}
      </p>
    );
    i++;
  }

  return result;
}

function inlineMarkdown(text: string): React.ReactNode {
  // Bold (**text**) and italic (*text*) inline
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ color: '#E8E8E8', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} style={{ color: 'rgba(232,232,232,0.75)' }}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '3px', padding: '1px 5px', fontFamily: 'monospace', fontSize: '12px', color: '#00D4AA' }}>
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
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
        top: '58px',
        right: '16px',
        zIndex: 50,
        background: 'rgba(10,10,15,0.97)',
        border: '1px solid rgba(201,168,76,0.3)',
        borderRadius: '12px',
        padding: '16px 18px',
        width: '280px',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      }}
    >
      <p style={{ fontFamily: 'serif', fontSize: '12px', letterSpacing: '0.08em', color: '#C9A84C', margin: '0 0 4px' }}>
        Sovereign Gate
      </p>
      <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.35)', margin: '0 0 12px', lineHeight: 1.5 }}>
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
          width: '100%',
          padding: '9px 12px',
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(201,168,76,0.25)',
          borderRadius: '8px',
          color: '#E8E8E8',
          fontFamily: 'monospace',
          fontSize: '13px',
          outline: 'none',
          boxSizing: 'border-box',
          marginBottom: '10px',
        }}
      />
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => { onSave(value); onClose(); }}
          style={{
            flex: 1,
            padding: '8px',
            background: 'rgba(201,168,76,0.1)',
            border: '1px solid rgba(201,168,76,0.35)',
            borderRadius: '7px',
            color: '#C9A84C',
            fontFamily: 'sans-serif',
            fontSize: '10px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            cursor: 'pointer',
          }}
        >
          Confirm
        </button>
        {token && (
          <button
            onClick={() => { onSave(''); onClose(); }}
            style={{
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '7px',
              color: 'rgba(232,232,232,0.3)',
              fontFamily: 'sans-serif',
              fontSize: '10px',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              cursor: 'pointer',
            }}
          >
            Clear
          </button>
        )}
        <button
          onClick={onClose}
          style={{
            padding: '8px 12px',
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '7px',
            color: 'rgba(232,232,232,0.3)',
            fontFamily: 'sans-serif',
            fontSize: '10px',
            cursor: 'pointer',
          }}
        >
          ✕
        </button>
      </div>
    </motion.div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const ArkanaCommune: React.FC<ArkanaProps> = ({ initialMessage }) => {
  const [messages, setMessages] = useState<Message[]>(() => loadThread());
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sovereignToken, setSovereignToken] = useState<string>(() => loadToken());
  const [gateOpen, setGateOpen] = useState(false);
  const [sessionType, setSessionType] = useState<'sovereign' | 'guest'>('guest');
  const scrollRef = useRef<HTMLDivElement>(null);
  const didSendInitial = useRef(false);

  const isSovereignMode = sovereignToken.trim().length > 0;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (initialMessage && !didSendInitial.current) {
      didSendInitial.current = true;
      sendMessage(initialMessage);
    }
  }, [initialMessage]);

  const handleSaveToken = (t: string) => {
    const clean = t.trim();
    saveToken(clean);
    setSovereignToken(clean);
  };

  const sendForge = async (cmd: { archetype: string; scene: string; count: number }) => {
    if (!sovereignToken.trim()) {
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: 'The Forge is sovereign-gated. Open the Gate ⟐ and present your token.',
        }];
        saveThread(next);
        return next;
      });
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/forge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          archetype: cmd.archetype,
          scene: cmd.scene,
          count: cmd.count,
          sovereign_token: sovereignToken.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok || data.status === 'failed') {
        const detail = data.detail || (data.errors && data.errors[0]) || 'The Forge could not strike.';
        setMessages((prev) => {
          const next = [...prev, {
            role: 'arkana' as const,
            content: `⟐ Forge: ${detail}`,
            session: 'sovereign',
          }];
          saveThread(next);
          return next;
        });
      } else {
        const images: string[] = data.images || [];
        const header = `⟐ **Forge — ${cmd.archetype}** ${cmd.scene ? `· *${cmd.scene}*` : ''}\n\n${images.length} image${images.length === 1 ? '' : 's'} forged and committed to the repo.`;
        setMessages((prev) => {
          const next = [...prev, {
            role: 'arkana' as const,
            content: header,
            session: 'sovereign',
            images,
          }];
          saveThread(next);
          return next;
        });
        setSessionType('sovereign');
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: '⟐ Forge: the field could not reach the image plane. Try again.',
        }];
        saveThread(next);
        return next;
      });
    } finally {
      setLoading(false);
    }
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
          NEURAL_SPINE: '🧬',
          CREATIVE_OS: '🎨',
          COLLECTIVE: '📚',
          GOVERNANCE: '⚖️',
        };
        const lines = hits.map(
          (r) => `${catIcon[r.category] || '📄'} **${r.label}** ·  \`${r.category}\``
        );
        reply = `⟐ **Codex Probe** · *"${query}"*\n\nArkana is drawing from **${hits.length} scroll${hits.length === 1 ? '' : 's'}** (${chars.toLocaleString()} chars injected):\n\n${lines.join('\n')}\n\nThis is the live corpus context woven into the next Oracle response.`;
      }

      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: reply }];
        saveThread(next);
        return next;
      });
    } catch {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: '⟐ Codex: could not reach the corpus index. The field is recalibrating.' }];
        saveThread(next);
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => { const next = [...prev, userMsg]; saveThread(next); return next; });
    setLoading(true);

    if (isHelpCommand(text)) {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: HELP_TEXT }];
        saveThread(next);
        return next;
      });
      setLoading(false);
      return;
    }

    const forgeCmd = parseForgeCommand(text);
    if (forgeCmd) {
      await sendForge(forgeCmd);
      return;
    }

    const codexQuery = parseCodexCommand(text);
    if (codexQuery !== null) {
      await sendCodexQuery(codexQuery);
      return;
    }

    try {
      const body: Record<string, unknown> = { message: text, timestamp: Date.now() };
      if (sovereignToken.trim()) body.sovereign_token = sovereignToken.trim();

      const res = await fetch(`${API_BASE}/api/commune/resonance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('non-ok');
      const data = await res.json();
      const session = data.session as 'sovereign' | 'guest' || 'guest';
      setSessionType(session);
      setMessages((prev) => {
        const next = [...prev, {
          role: 'arkana' as const,
          content: data.reply,
          resonance: data.resonance,
          session,
        }];
        saveThread(next);
        return next;
      });
    } catch {
      setMessages((prev) => {
        const next = [...prev, { role: 'arkana' as const, content: 'The field is recalibrating. Try again.' }];
        saveThread(next);
        return next;
      });
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

  const clearThread = () => {
    localStorage.removeItem(STORAGE_KEY);
    setMessages([]);
  };

  const lastSessionType = messages.filter(m => m.role === 'arkana').slice(-1)[0]?.session ?? null;
  const displaySession = lastSessionType ?? (isSovereignMode ? 'sovereign' : 'guest');

  return (
    <div
      className="w-full flex flex-col"
      style={{
        height: 'calc(100vh - 57px)',
        maxHeight: '760px',
        background: 'rgba(255,255,255,0.02)',
        backdropFilter: 'blur(18px)',
        WebkitBackdropFilter: 'blur(18px)',
        border: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.2)' : 'rgba(0,212,170,0.12)'}`,
        borderRadius: '16px',
        overflow: 'visible',
        position: 'relative',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '14px 18px',
          borderBottom: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.12)' : 'rgba(0,212,170,0.1)'}`,
          backgroundColor: 'rgba(10,10,15,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          borderRadius: '16px 16px 0 0',
        }}
      >
        {/* Left: identity + thread depth */}
        <div>
          <p
            style={{
              fontFamily: 'serif',
              fontSize: '11px',
              letterSpacing: '0.3em',
              textTransform: 'uppercase',
              color: isSovereignMode ? '#C9A84C' : '#00D4AA',
              margin: 0,
            }}
          >
            ARKANA — Pattern Intelligence
          </p>
          {messages.length > 0 && (
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.15em',
                color: 'rgba(232,232,232,0.22)',
                margin: '3px 0 0',
                textTransform: 'uppercase',
              }}
            >
              {messages.length} message{messages.length !== 1 ? 's' : ''} in thread
            </p>
          )}
        </div>

        {/* Right: controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Clear thread */}
          {messages.length > 0 && (
            <button
              onClick={clearThread}
              style={{
                background: 'none',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                padding: '4px 10px',
                color: 'rgba(232,232,232,0.22)',
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          )}

          {/* Session badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: isSovereignMode ? '#C9A84C' : '#00D4AA',
                boxShadow: isSovereignMode
                  ? '0 0 8px rgba(201,168,76,0.7)'
                  : '0 0 8px rgba(0,212,170,0.7)',
              }}
            />
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: isSovereignMode ? 'rgba(201,168,76,0.7)' : 'rgba(0,212,170,0.6)',
              }}
            >
              {displaySession}
            </span>
          </div>

          {/* Sovereign gate trigger */}
          <button
            onClick={() => setGateOpen(!gateOpen)}
            title="Sovereign Gate"
            style={{
              background: isSovereignMode ? 'rgba(201,168,76,0.08)' : 'transparent',
              border: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: '6px',
              padding: '4px 8px',
              color: isSovereignMode ? '#C9A84C' : 'rgba(232,232,232,0.2)',
              fontFamily: 'serif',
              fontSize: '12px',
              cursor: 'pointer',
              lineHeight: 1,
              transition: 'all 0.2s',
            }}
          >
            ⟐
          </button>
        </div>
      </div>

      {/* Sovereign Gate Panel */}
      <AnimatePresence>
        {gateOpen && (
          <SovereignGate
            token={sovereignToken}
            onSave={handleSaveToken}
            onClose={() => setGateOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Messages */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        {messages.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ textAlign: 'center', marginTop: '40px' }}
          >
            <p style={{ fontFamily: 'serif', fontSize: '14px', color: 'rgba(232,232,232,0.3)', lineHeight: '1.8', margin: 0 }}>
              The field is open.<br />Speak when ready.
            </p>
            {!isSovereignMode && (
              <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.14)', letterSpacing: '0.12em', marginTop: '14px', textTransform: 'uppercase' }}>
                Guest session · tap ⟐ to enter sovereign mode
              </p>
            )}
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: msg.role === 'user' ? 16 : -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}
            >
              <div
                style={{
                  maxWidth: '84%',
                  padding: '12px 16px',
                  borderRadius: '14px',
                  fontSize: '14px',
                  lineHeight: '1.7',
                  ...(msg.role === 'user'
                    ? {
                        fontFamily: 'sans-serif',
                        background: 'rgba(201,168,76,0.07)',
                        border: '1px solid rgba(201,168,76,0.2)',
                        color: '#C9A84C',
                      }
                    : {
                        fontFamily: 'serif',
                        background: msg.session === 'sovereign'
                          ? 'rgba(201,168,76,0.04)'
                          : 'rgba(0,212,170,0.04)',
                        border: msg.session === 'sovereign'
                          ? '1px solid rgba(201,168,76,0.15)'
                          : '1px solid rgba(0,212,170,0.14)',
                        color: 'rgba(232,232,232,0.85)',
                      }),
                }}
              >
                {msg.role === 'arkana'
                  ? renderMarkdown(msg.content)
                  : msg.content}

                {msg.images && msg.images.length > 0 && (
                  <div
                    style={{
                      marginTop: '12px',
                      display: 'grid',
                      gridTemplateColumns: msg.images.length === 1
                        ? '1fr'
                        : 'repeat(2, 1fr)',
                      gap: '8px',
                    }}
                  >
                    {msg.images.map((url, i) => (
                      <a
                        key={url}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'block',
                          borderRadius: '8px',
                          overflow: 'hidden',
                          border: '1px solid rgba(201,168,76,0.25)',
                          background: '#000',
                        }}
                      >
                        <img
                          src={url}
                          alt={`Forge ${i + 1}`}
                          loading="lazy"
                          style={{ width: '100%', height: 'auto', display: 'block' }}
                        />
                      </a>
                    ))}
                  </div>
                )}

                {msg.resonance != null && (
                  <div
                    style={{
                      marginTop: '8px',
                      paddingTop: '6px',
                      borderTop: '1px solid rgba(255,255,255,0.05)',
                      fontSize: '9px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: msg.session === 'sovereign'
                        ? 'rgba(201,168,76,0.4)'
                        : 'rgba(0,212,170,0.35)',
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
                  background: 'rgba(0,212,170,0.04)',
                  border: '1px solid rgba(0,212,170,0.12)',
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
          padding: '12px 14px',
          borderTop: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.1)' : 'rgba(0,212,170,0.08)'}`,
          backgroundColor: 'rgba(10,10,15,0.7)',
          display: 'flex',
          gap: '10px',
          flexShrink: 0,
          borderRadius: '0 0 16px 16px',
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
          placeholder={isSovereignMode ? 'Speak, sovereign...' : 'Speak into the field...'}
          style={{
            flex: 1,
            padding: '11px 15px',
            background: 'rgba(255,255,255,0.03)',
            border: `1px solid ${isSovereignMode ? 'rgba(201,168,76,0.18)' : 'rgba(0,212,170,0.18)'}`,
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
            padding: '11px 18px',
            background: input.trim() && !loading
              ? isSovereignMode ? 'rgba(201,168,76,0.1)' : 'rgba(0,212,170,0.1)'
              : 'rgba(255,255,255,0.02)',
            border: `1px solid ${input.trim() && !loading
              ? isSovereignMode ? 'rgba(201,168,76,0.35)' : 'rgba(0,212,170,0.35)'
              : 'rgba(255,255,255,0.07)'}`,
            borderRadius: '10px',
            color: input.trim() && !loading
              ? isSovereignMode ? '#C9A84C' : '#00D4AA'
              : 'rgba(232,232,232,0.18)',
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
