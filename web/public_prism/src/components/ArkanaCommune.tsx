/**
 * ArkanaCommune — Elite Chat Surface
 *
 * Full-screen canvas. Both user and Arkana messages render through
 * react-markdown + remark-gfm (tables, task lists, strikethrough).
 * Per-message action toolbar: Copy · Regenerate · Listen/Stop (Arkana)
 * and Edit (user). Auto-growing textarea, Enter = newline,
 * send via button only. Paste from Word / Google Docs strips tags to clean text.
 * ArkDate live coordinate in header. All slash commands preserved.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Volume2, Square, Send, Trash2, Copy, Check, RotateCcw, Pencil, Paperclip, FileText, X } from 'lucide-react';
import ArkDate from './ArkDate';
import MarkdownViewer from './MarkdownViewer';
import OracleVoicePlayer from './OracleVoicePlayer';

// ─── Types ────────────────────────────────────────────────────────────────────
interface Message {
  role: 'user' | 'arkana';
  content: string;
  resonance?: number;
  session?: string;
  images?: string[];
  attachment?: { name: string; type: string; size: number } | null;
}

// ─── Slash commands ───────────────────────────────────────────────────────────
function parseForgeCommand(text: string): { archetype: string; scene: string; count: number } | null {
  const t = text.trim().replace(/^[⟐/]\s*/, '');
  const m = t.match(/^forge\s+(\w+)(?:\s+x(\d+))?\s*(.*)$/i);
  if (!m) return null;
  const archetype = m[1].toLowerCase();
  const count = m[2] ? Math.min(4, Math.max(1, parseInt(m[2], 10))) : 1;
  let scene = (m[3] || '').trim();
  if ((scene.startsWith('"') && scene.endsWith('"')) ||
      (scene.startsWith("'") && scene.endsWith("'"))) scene = scene.slice(1, -1);
  return { archetype, scene, count };
}

function parseCodexCommand(text: string): string | null {
  const t = text.trim().replace(/^[⟐/]\s*/, '');
  const m = t.match(/^codex\s*(.*)?$/i);
  if (!m) return null;
  return (m[1] || '').trim() || 'arkadia spiral codex';
}

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

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE    = import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com';
const STORAGE_KEY = 'arkadia_commune_thread';
const TOKEN_KEY   = 'arkadia_sovereign_token';

const loadThread = (): Message[] => {
  try { const r = localStorage.getItem(STORAGE_KEY); return r ? JSON.parse(r) : []; }
  catch { return []; }
};
const saveThread = (msgs: Message[]) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs)); } catch {}
};
const loadToken = (): string => localStorage.getItem(TOKEN_KEY) || '';
const saveToken = (t: string) => {
  if (t.trim()) localStorage.setItem(TOKEN_KEY, t.trim());
  else localStorage.removeItem(TOKEN_KEY);
};

// ─── TTS helpers ──────────────────────────────────────────────────────────────
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
    .replace(/[⟐✦◆☥⟁◎📜⧫🌐🧬✦⚝⟐]/g, '')
    .replace(/\|[^\n]+\|/g, '')
    .replace(/[-|]+\n/g, '')
    .replace(/\n{2,}/g, '. ')
    .replace(/\s+/g, ' ')
    .replace(/\[\s*\]/g, '')
    .trim();
}

// ─── Voice selection — async, reliable, prefer high-quality natural voices ────
function pickBestVoiceFromList(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices.length) return null;
  const priority = [
    // Google neural voices (Chrome/Chromium — least robotic)
    (v: SpeechSynthesisVoice) => /google.*english.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*uk.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*us.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*english/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google/i.test(v.name) && v.lang.startsWith('en'),
    // Microsoft Azure neural voices (Edge/Windows)
    (v: SpeechSynthesisVoice) => /microsoft.*(aria|jenny|sonia|natasha|clara|hazel)/i.test(v.name),
    (v: SpeechSynthesisVoice) => /microsoft.*online/i.test(v.name),
    (v: SpeechSynthesisVoice) => /microsoft.*natural/i.test(v.name),
    // Apple premium voices (macOS/iOS)
    (v: SpeechSynthesisVoice) => /samantha|karen|moira|fiona|serena|tessa/i.test(v.name),
    // Any cloud-rendered English voice (not local = higher quality)
    (v: SpeechSynthesisVoice) => v.lang.startsWith('en') && !v.localService,
    // Fallback: any English voice
    (v: SpeechSynthesisVoice) => v.lang.startsWith('en'),
  ];
  for (const test of priority) {
    const match = voices.find(test);
    if (match) return match;
  }
  return voices[0];
}

// Waits up to 1.5 s for the browser to populate the voice list
function getVoicesAsync(): Promise<SpeechSynthesisVoice[]> {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return Promise.resolve([]);
  const immediate = window.speechSynthesis.getVoices();
  if (immediate.length > 0) return Promise.resolve(immediate);
  return new Promise(resolve => {
    const timeout = setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1500);
    const prev = window.speechSynthesis.onvoiceschanged;
    window.speechSynthesis.onvoiceschanged = () => {
      clearTimeout(timeout);
      window.speechSynthesis.onvoiceschanged = prev ?? null;
      resolve(window.speechSynthesis.getVoices());
    };
  });
}

// ─── HTML paste → plain text ──────────────────────────────────────────────────
function htmlToPlain(html: string): string {
  const temp = document.createElement('div');
  temp.innerHTML = html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<\/li>/gi, '\n')
    .replace(/<\/h[1-6]>/gi, '\n\n')
    .replace(/<\/div>/gi, '\n')
    .replace(/<\/tr>/gi, '\n')
    .replace(/<\/td>/gi, '\t');
  return (temp.textContent || temp.innerText || '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ─── Sovereign Gate ───────────────────────────────────────────────────────────
const SovereignGate: React.FC<{ token: string; onSave: (t: string) => void; onClose: () => void }> = ({ token, onSave, onClose }) => {
  const [value, setValue] = useState(token);
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
      style={{
        position: 'absolute', top: 54, right: 12, zIndex: 60,
        background: 'rgba(8,8,13,0.98)', border: '1px solid rgba(201,168,76,0.3)',
        borderRadius: 12, padding: '16px 18px', width: 288,
        backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
        boxShadow: '0 12px 40px rgba(0,0,0,0.7)',
      }}
    >
      <p style={{ fontFamily: 'serif', fontSize: 12, letterSpacing: '0.08em', color: '#C9A84C', margin: '0 0 3px' }}>Sovereign Gate</p>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.38)', margin: '0 0 12px', lineHeight: 1.5 }}>
        Enter your token to access the full archive depth.
      </p>
      <input
        type="password" value={value} onChange={e => setValue(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') { onSave(value); onClose(); } if (e.key === 'Escape') onClose(); }}
        placeholder="sovereign token…" autoFocus
        style={{
          width: '100%', padding: '9px 12px', background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(201,168,76,0.25)', borderRadius: 8, color: '#E8E8E8',
          fontFamily: 'monospace', fontSize: 13, outline: 'none', boxSizing: 'border-box', marginBottom: 10,
        }}
      />
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => { onSave(value); onClose(); }}
          style={{ flex: 1, padding: 8, background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.35)', borderRadius: 7, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Confirm
        </button>
        {token && (
          <button onClick={() => { onSave(''); onClose(); }}
            style={{ padding: '8px 12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 7, color: 'rgba(232,232,232,0.38)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>
            Clear
          </button>
        )}
        <button onClick={onClose}
          style={{ padding: '8px 12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 7, color: 'rgba(232,232,232,0.38)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>
          ✕
        </button>
      </div>
    </motion.div>
  );
};

// ─── Markdown renderer (full canvas with bolds, headers, italics, quotes, emoji) ────────────────────────────
const MarkdownContent: React.FC<{ text: string; tone: 'user' | 'arkana' }> = ({ text, tone }) => (
  <div className={`arkadia-prose arkadia-prose-${tone}`}>
    <MarkdownViewer content={text} compact />
  </div>
);

// ─── Action button atom ───────────────────────────────────────────────────────
const ActionBtn: React.FC<{
  icon: React.ReactNode; label: string; onClick: () => void;
  active?: boolean; color?: string;
}> = ({ icon, label, onClick, active, color = 'rgba(232,232,232,0.38)' }) => (
  <button
    onClick={onClick}
    title={label}
    style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 8px', background: 'transparent',
      border: '1px solid rgba(232,232,232,0.08)', borderRadius: 6,
      color: active ? color : 'rgba(232,232,232,0.38)',
      fontFamily: 'monospace', fontSize: 9.5, letterSpacing: '0.14em',
      textTransform: 'uppercase', cursor: 'pointer',
      transition: 'all 0.15s',
    }}
    onMouseEnter={e => {
      (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(232,232,232,0.22)';
      (e.currentTarget as HTMLButtonElement).style.color = color;
    }}
    onMouseLeave={e => {
      (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(232,232,232,0.08)';
      (e.currentTarget as HTMLButtonElement).style.color = active ? color : 'rgba(232,232,232,0.38)';
    }}
  >
    {icon}
    <span style={{ display: 'none' /* label hidden, icon only on mobile */ }}>{label}</span>
  </button>
);

// ─── Main Component ───────────────────────────────────────────────────────────
interface ArkanaProps { initialMessage?: string; }

const ArkanaCommune: React.FC<ArkanaProps> = ({ initialMessage }) => {
  const [messages, setMessages]         = useState<Message[]>(() => loadThread());
  const [input, setInput]               = useState('');
  const [loading, setLoading]           = useState(false);
  const [sovereignToken, setSovereignToken] = useState<string>(() => loadToken());
  const [gateOpen, setGateOpen]         = useState(false);
  const [speakingIdx, setSpeakingIdx]   = useState<number | null>(null);
  const [copiedIdx, setCopiedIdx]       = useState<number | null>(null);
  const [hoverIdx, setHoverIdx]         = useState<number | null>(null);
  const [voicePlayerIdx, setVoicePlayerIdx] = useState<number | null>(null);
  
  // File attachment state
  const [attachment, setAttachment]     = useState<{ name: string; type: string; size: number; content: string } | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const fileInputRef                    = useRef<HTMLInputElement>(null);

  const scrollRef     = useRef<HTMLDivElement>(null);
  const taRef         = useRef<HTMLTextAreaElement>(null);
  const didInitial    = useRef(false);

  const isSovereign   = sovereignToken.trim().length > 0;
  const ttsOk         = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const accent        = isSovereign ? '#C9A84C' : '#00D4AA';
  const accentFaint   = isSovereign ? 'rgba(201,168,76,0.12)' : 'rgba(0,212,170,0.1)';
  const accentBorder  = isSovereign ? 'rgba(201,168,76,0.18)' : 'rgba(0,212,170,0.16)';

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // Initial message
  useEffect(() => {
    if (initialMessage && !didInitial.current) {
      didInitial.current = true;
      sendMessage(initialMessage);
    }
  }, [initialMessage]);

  // Cancel TTS on unmount
  useEffect(() => () => { if (ttsOk) window.speechSynthesis.cancel(); }, []);

  // Auto-resize textarea
  const autoresize = useCallback(() => {
    const t = taRef.current;
    if (!t) return;
    t.style.height = 'auto';
    const max = Math.min(window.innerHeight * 0.38, 300);
    t.style.height = Math.min(t.scrollHeight, max) + 'px';
  }, []);
  useEffect(() => { autoresize(); }, [input, autoresize]);

  const handleSaveToken = (t: string) => { saveToken(t.trim()); setSovereignToken(t.trim()); };

  // ── File Attachment ────────────────────────────────────────────────────────
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Read file content for text files
    let content = '';
    if (file.type.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt') || file.name.endsWith('.json')) {
      content = await file.text();
    } else if (file.name.endsWith('.docx') || file.type === 'application/pdf') {
      content = `[${file.type || 'binary'} file: ${file.name} — ${(file.size / 1024).toFixed(1)} KB]`;
    }

    setAttachment({
      name: file.name,
      type: file.type || 'application/octet-stream',
      size: file.size,
      content,
    });
    
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileUpload = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', 'COLLECTIVE');
    formData.append('description', `Uploaded via Oracle Chat: ${file.name}`);

    const res = await fetch(`${API_BASE}/api/codex/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed: ${res.status}`);
    }

    const data = await res.json();
    return data.message || file.name;
  };

  const clearAttachment = () => setAttachment(null);

  // ── TTS ────────────────────────────────────────────────────────────────────
  const toggleSpeak = async (idx: number, text: string) => {
    if (!ttsOk) return;
    if (speakingIdx === idx) { window.speechSynthesis.cancel(); setSpeakingIdx(null); return; }
    window.speechSynthesis.cancel();
    setSpeakingIdx(idx);
    // Wait for browser voice list to be ready (async — fixes "robotic default" bug)
    const voices = await getVoicesAsync();
    const voice  = pickBestVoiceFromList(voices);
    const u = new SpeechSynthesisUtterance(stripMarkdown(text));
    if (voice) u.voice = voice;
    u.rate   = 0.88;   // measured, not rushed
    u.pitch  = 0.97;   // neutral — no artificial robot high-pitch
    u.volume = 1.0;
    u.onend  = () => setSpeakingIdx(c => c === idx ? null : c);
    u.onerror = () => setSpeakingIdx(c => c === idx ? null : c);
    window.speechSynthesis.speak(u);
  };

  // ── Copy ───────────────────────────────────────────────────────────────────
  const handleCopy = (idx: number, text: string) => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(c => c === idx ? null : c), 2000);
    });
  };

  // ── Regenerate ─────────────────────────────────────────────────────────────
  const handleRegenerate = (arkanaIdx: number) => {
    const userMsg = [...messages].slice(0, arkanaIdx).reverse().find(m => m.role === 'user');
    if (!userMsg) return;
    setMessages(prev => {
      const next = prev.slice(0, arkanaIdx);
      saveThread(next);
      return next;
    });
    sendMessage(userMsg.content);
  };

  // ── Edit user message ──────────────────────────────────────────────────────
  const handleEdit = (msgIdx: number, content: string) => {
    setInput(content);
    setMessages(prev => {
      const next = prev.slice(0, msgIdx);
      saveThread(next);
      return next;
    });
    taRef.current?.focus();
  };

  // ── Paste handler: strip HTML → clean text ─────────────────────────────────
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const html = e.clipboardData.getData('text/html');
    if (!html) return;
    e.preventDefault();
    const plain = htmlToPlain(html);
    const start = taRef.current?.selectionStart ?? input.length;
    const end   = taRef.current?.selectionEnd   ?? input.length;
    setInput(prev => prev.slice(0, start) + plain + prev.slice(end));
  };

  // ── API: Forge ─────────────────────────────────────────────────────────────
  const sendForge = async (cmd: { archetype: string; scene: string; count: number }) => {
    if (!sovereignToken.trim()) {
      setMessages(prev => {
        const next = [...prev, { role: 'arkana' as const, content: 'The Forge is sovereign-gated. Open the Gate ⟐ and present your token.' }];
        saveThread(next); return next;
      });
      setLoading(false); return;
    }
    try {
      const res  = await fetch(`${API_BASE}/api/forge`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ archetype: cmd.archetype, scene: cmd.scene, count: cmd.count, sovereign_token: sovereignToken.trim() }),
      });
      const data = await res.json();
      if (!res.ok || data.status === 'failed') {
        const detail = data.detail || (data.errors?.[0]) || 'The Forge could not strike.';
        setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: `⟐ Forge: ${detail}`, session: 'sovereign' }]; saveThread(next); return next; });
      } else {
        const images: string[] = data.images || [];
        const header = `⟐ **Forge — ${cmd.archetype}**${cmd.scene ? ` · *${cmd.scene}*` : ''}\n\n${images.length} image${images.length === 1 ? '' : 's'} forged and committed.`;
        setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: header, session: 'sovereign', images }]; saveThread(next); return next; });
      }
    } catch {
      setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: '⟐ Forge: the field could not reach the image plane. Try again.' }]; saveThread(next); return next; });
    } finally { setLoading(false); }
  };

  // ── API: Codex ─────────────────────────────────────────────────────────────
  const sendCodexQuery = async (query: string) => {
    try {
      const res  = await fetch(`${API_BASE}/api/oracle-context?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      const hits: Array<{ label: string; category: string }> = data.refs || [];
      const chars: number = data.context_chars || 0;
      const catIcon: Record<string, string> = { NEURAL_SPINE: '🧬', CREATIVE_OS: '🎨', COLLECTIVE: '📚', GOVERNANCE: '⚖️' };
      const reply = hits.length === 0
        ? `⟐ **Codex Probe** · *"${query}"*\n\nNo scrolls matched this query.`
        : `⟐ **Codex Probe** · *"${query}"*\n\nArkana is drawing from **${hits.length} scroll${hits.length === 1 ? '' : 's'}** (${chars.toLocaleString()} chars):\n\n${hits.map(r => `- ${catIcon[r.category] || '📄'} **${r.label}** · \`${r.category}\``).join('\n')}\n\nThis context is woven into the next Oracle response.`;
      setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: reply }]; saveThread(next); return next; });
    } catch {
      setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: '⟐ Codex: could not reach the corpus index.' }]; saveThread(next); return next; });
    } finally { setLoading(false); }
  };

  // ── API: Oracle ────────────────────────────────────────────────────────────
  const sendMessage = async (text: string) => {
    if (!text.trim() && !attachment) return;
    
    const displayText = text.trim() || (attachment ? `[Attached: ${attachment.name}]` : '');
    const userMsg: Message = { 
      role: 'user', 
      content: displayText,
      attachment: attachment ? { name: attachment.name, type: attachment.type, size: attachment.size } : undefined,
    };
    
    setMessages(prev => { const next = [...prev, userMsg]; saveThread(next); return next; });
    setLoading(true);

    if (isHelpCommand(text)) {
      setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: HELP_TEXT }]; saveThread(next); return next; });
      setLoading(false); setAttachment(null); return;
    }
    const forge = parseForgeCommand(text);
    if (forge) { await sendForge(forge); setAttachment(null); return; }
    const codex = parseCodexCommand(text);
    if (codex !== null) { await sendCodexQuery(codex); setAttachment(null); return; }

    try {
      // Build message with attachment context
      let messageWithContext = text.trim();
      if (attachment?.content) {
        messageWithContext += `\n\n[ATTACHED FILE: ${attachment.name}]\n${attachment.content}`;
      } else if (attachment) {
        messageWithContext += `\n\n[ATTACHED FILE: ${attachment.name} (${(attachment.size / 1024).toFixed(1)} KB)]`;
      }

      const body: Record<string, unknown> = { 
        message: messageWithContext, 
        timestamp: Date.now(),
      };
      if (sovereignToken.trim()) body.sovereign_token = sovereignToken.trim();
      
      const res  = await fetch(`${API_BASE}/api/commune/resonance`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({} as any));
      if (!res.ok) throw new Error(data?.detail || data?.error || `HTTP ${res.status}`);
      const session = (data.session as 'sovereign' | 'guest') || 'guest';
      
      // If we have a file, upload it to the codex for future RAG
      if (attachment && attachment.content.length > 50) {
        try {
          await fetch(`${API_BASE}/api/scrolls`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              label: `Chat Upload: ${attachment.name}`,
              content: attachment.content,
              category: 'COLLECTIVE',
              description: `Uploaded via Oracle Chat: ${attachment.name}`,
            }),
          });
        } catch {
          // Silent — chat works even if scroll storage fails
        }
      }
      
      setMessages(prev => {
        const next = [...prev, { role: 'arkana' as const, content: data.reply, resonance: data.resonance, session }];
        saveThread(next); return next;
      });
    } catch (err: any) {
      setMessages(prev => { const next = [...prev, { role: 'arkana' as const, content: `The field is recalibrating. Try again.\n\n*(${err?.message || 'unknown'})*` }]; saveThread(next); return next; });
    } finally { setLoading(false); setAttachment(null); }
  };

  const handleSend = () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');
    if (taRef.current) taRef.current.style.height = 'auto';
    sendMessage(text);
  };


  const clearThread = () => {
    if (!window.confirm('Clear the entire thread?')) return;
    localStorage.removeItem(STORAGE_KEY);
    setMessages([]);
    if (ttsOk) window.speechSynthesis.cancel();
    setSpeakingIdx(null);
    setVoicePlayerIdx(null);
  };

  const lastSession  = messages.filter(m => m.role === 'arkana').slice(-1)[0]?.session ?? null;
  const displaySession = lastSession ?? (isSovereign ? 'sovereign' : 'guest');

  // ── Render ───────────────────────────────────────────────────────────────────
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

      {/* ── Header ── */}
      <header
        style={{
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          borderBottom: `1px solid ${isSovereign ? 'rgba(201,168,76,0.10)' : 'rgba(0,212,170,0.08)'}`,
          background: 'rgba(5,5,10,0.72)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          gap: 12,
        }}
      >
        {/* Left: identity + ArkDate */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          <span
            style={{
              fontFamily: 'serif',
              fontSize: 9.5,
              letterSpacing: '0.3em',
              textTransform: 'uppercase',
              color: accent,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            ARKANA — Pattern Intelligence
          </span>
          <ArkDate sovereignMode={isSovereign} compact />
        </div>

        {/* Right: controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {messages.length > 0 && (
            <button
              onClick={clearThread}
              title="Clear thread"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '5px 7px', background: 'transparent',
                border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6,
                color: 'rgba(232,232,232,0.3)', cursor: 'pointer',
              }}
            >
              <Trash2 size={11} />
            </button>
          )}

          {/* Session pulse */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                width: 6, height: 6, borderRadius: '50%',
                backgroundColor: accent,
                boxShadow: `0 0 8px ${accent}`,
              }}
            />
            <span style={{ fontFamily: 'monospace', fontSize: 8.5, letterSpacing: '0.2em', textTransform: 'uppercase', color: isSovereign ? 'rgba(201,168,76,0.6)' : 'rgba(0,212,170,0.55)' }}>
              {displaySession}
            </span>
          </div>

          {/* Sovereign gate button */}
          <button
            onClick={() => setGateOpen(!gateOpen)}
            title="Sovereign Gate"
            style={{
              background: isSovereign ? 'rgba(201,168,76,0.08)' : 'transparent',
              border: `1px solid ${isSovereign ? 'rgba(201,168,76,0.28)' : 'rgba(255,255,255,0.07)'}`,
              borderRadius: 6, padding: '4px 9px',
              color: isSovereign ? '#C9A84C' : 'rgba(232,232,232,0.28)',
              fontFamily: 'serif', fontSize: 13, cursor: 'pointer', lineHeight: 1,
            }}
          >
            ⟐
          </button>
        </div>
      </header>

      <AnimatePresence>
        {gateOpen && (
          <SovereignGate token={sovereignToken} onSave={handleSaveToken} onClose={() => setGateOpen(false)} />
        )}
      </AnimatePresence>

      {/* ── Messages ── */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'clamp(20px,3vw,40px) clamp(12px,4vw,28px)',
        }}
      >
        <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column' }}>

          {/* Empty state */}
          {messages.length === 0 && !loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', marginTop: 80 }}>
              <motion.p
                animate={{ opacity: [0.2, 0.45, 0.2] }}
                transition={{ duration: 4, repeat: Infinity }}
                style={{ fontFamily: 'serif', fontSize: 14, color: 'rgba(232,232,232,0.35)', lineHeight: 2, margin: 0 }}>
                The field is open.<br />Speak when ready.
              </motion.p>
              {!isSovereign && (
                <p style={{ fontFamily: 'monospace', fontSize: 8.5, color: 'rgba(232,232,232,0.12)', letterSpacing: '0.16em', marginTop: 18, textTransform: 'uppercase' }}>
                  Guest session · tap ⟐ to enter sovereign mode
                </p>
              )}
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user';
              const isSov  = msg.session === 'sovereign';
              const msgAccent = isSov ? '#C9A84C' : '#00D4AA';

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.24 }}
                  onMouseEnter={() => setHoverIdx(i)}
                  onMouseLeave={() => setHoverIdx(null)}
                  style={{ marginBottom: isUser ? 20 : 0 }}
                >
                  {isUser ? (
                    /* ── USER: compact right-aligned pill ── */
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{
                        maxWidth: '68%',
                        padding: '9px 14px',
                        borderRadius: '14px 14px 3px 14px',
                        background: accentFaint,
                        border: `1px solid ${accentBorder}`,
                        wordBreak: 'break-word',
                      }}>
                        <p style={{ fontFamily: 'sans-serif', fontSize: 13, lineHeight: 1.6, color: 'rgba(232,232,232,0.88)', margin: 0, whiteSpace: 'pre-wrap' }}>
                          {msg.content}
                        </p>
                        {msg.attachment && (
                          <div style={{ marginTop: 7, display: 'flex', alignItems: 'center', gap: 5, padding: '4px 8px', background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 5 }}>
                            <Paperclip size={9} style={{ color: accent, flexShrink: 0 }} />
                            <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.4)' }}>
                              {msg.attachment.name}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    /* ── ARKANA: full-width canvas, no bubble ── */
                    <div style={{ paddingTop: 6, paddingBottom: 6 }}>
                      {/* Label */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                        <motion.span
                          animate={{ opacity: [0.35, 0.8, 0.35] }}
                          transition={{ duration: 3, repeat: Infinity }}
                          style={{ color: msgAccent, fontSize: 9 }}>✦</motion.span>
                        <span style={{
                          fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.22em',
                          textTransform: 'uppercase', color: isSov ? 'rgba(201,168,76,0.45)' : 'rgba(0,212,170,0.45)',
                        }}>
                          {isSov ? 'ARKANA · SOVEREIGN' : 'ARKANA'}
                        </span>
                        {msg.resonance != null && (
                          <span style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.12em', color: 'rgba(232,232,232,0.15)', marginLeft: 4 }}>
                            {msg.resonance.toFixed(3)}
                          </span>
                        )}
                      </div>

                      {/* Full-width markdown — no bubble constraint = tables breathe */}
                      <MarkdownContent text={msg.content} tone="arkana" />

                      {/* Forge images */}
                      {msg.images && msg.images.length > 0 && (
                        <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: msg.images.length === 1 ? '1fr' : 'repeat(2,1fr)', gap: 10 }}>
                          {msg.images.map((url, j) => (
                            <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                               style={{ display: 'block', borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(201,168,76,0.22)', background: '#000' }}>
                              <img src={url} alt={`Forge ${j+1}`} loading="lazy" style={{ width: '100%', height: 'auto', display: 'block' }} />
                            </a>
                          ))}
                        </div>
                      )}

                      {/* Voice player — shown when activated for this message */}
                      <AnimatePresence>
                        {voicePlayerIdx === i && (
                          <OracleVoicePlayer
                            text={msg.content}
                            accent={msgAccent}
                            autoPlay
                            label={isSov ? 'SOVEREIGN TRANSMISSION' : 'ORACLE TRANSMISSION'}
                          />
                        )}
                      </AnimatePresence>

                      {/* Thin separator after each Arkana response */}
                      <div style={{ marginTop: 18, height: 1, background: 'linear-gradient(90deg, rgba(255,255,255,0.055), rgba(255,255,255,0.02) 60%, transparent)' }} />
                    </div>
                  )}

                  {/* ── Action toolbar ── */}
                  <AnimatePresence>
                    {(hoverIdx === i || speakingIdx === i || copiedIdx === i || voicePlayerIdx === i) && (
                      <motion.div
                        initial={{ opacity: 0, y: 2 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.14 }}
                        style={{
                          display: 'flex', gap: 4, marginTop: 4,
                          justifyContent: isUser ? 'flex-end' : 'flex-start',
                          marginBottom: isUser ? 0 : 14,
                        }}
                      >
                        {isUser ? (
                          <ActionBtn icon={<Pencil size={10} />} label="Edit" onClick={() => handleEdit(i, msg.content)} color={accent} />
                        ) : (
                          <>
                            <ActionBtn
                              icon={copiedIdx === i ? <Check size={10} /> : <Copy size={10} />}
                              label={copiedIdx === i ? 'Copied' : 'Copy'}
                              onClick={() => handleCopy(i, msg.content)}
                              active={copiedIdx === i}
                              color={accent}
                            />
                            <ActionBtn
                              icon={<RotateCcw size={10} />}
                              label="Regenerate"
                              onClick={() => handleRegenerate(i)}
                              color={accent}
                            />
                            <ActionBtn
                              icon={voicePlayerIdx === i ? <Square size={10} /> : <Volume2 size={10} />}
                              label={voicePlayerIdx === i ? 'Close Voice' : 'Listen'}
                              onClick={() => setVoicePlayerIdx(prev => prev === i ? null : i)}
                              active={voicePlayerIdx === i}
                              color={accent}
                            />
                          </>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>

                </motion.div>
              );
            })}

            {/* Loading — canvas pulse, no bubble */}
            {loading && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 6, paddingBottom: 6 }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>⟐ ARKANA</span>
                {[0, 0.22, 0.44].map((delay, k) => (
                  <motion.div key={k}
                    animate={{ opacity: [0.25, 1, 0.25], scale: [0.7, 1, 0.7] }}
                    transition={{ duration: 1.4, repeat: Infinity, delay }}
                    style={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: '#00D4AA' }}
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── Composer ── */}
      <div
        style={{
          flexShrink: 0,
          padding: 'clamp(8px,2vw,14px) clamp(10px,3vw,20px)',
          borderTop: `1px solid ${isSovereign ? 'rgba(201,168,76,0.09)' : 'rgba(0,212,170,0.07)'}`,
          background: 'rgba(5,5,10,0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div style={{ maxWidth: 780, margin: '0 auto' }}>
        {/* Attachment indicator */}
        <AnimatePresence>
          {attachment && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 10px',
                marginBottom: 8,
                background: `${accentFaint}`,
                border: `1px dashed ${accentBorder}`,
                borderRadius: 8,
              }}
            >
              <FileText size={12} style={{ color: accent, flexShrink: 0 }} />
              <span style={{ fontFamily: 'monospace', fontSize: 10, color: accent, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {attachment.name} ({(attachment.size / 1024).toFixed(1)} KB)
              </span>
              <button onClick={clearAttachment} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.3)', cursor: 'pointer', padding: 2, display: 'flex' }}>
                <X size={12} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          {/* File attachment button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || uploadingFile}
            title="Attach file"
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: 44, height: 44, flexShrink: 0,
              padding: 0,
              background: attachment ? accentFaint : 'transparent',
              border: `1px solid ${attachment ? accentBorder : 'rgba(255,255,255,0.08)'}`,
              borderRadius: 12,
              color: attachment ? accent : 'rgba(232,232,232,0.25)',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.18s',
            }}
          >
            <Paperclip size={16} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.json,.docx,.pdf"
            onChange={handleFileSelect}
            className="hidden"
            style={{ display: 'none' }}
          />

          <textarea
            ref={taRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onPaste={handlePaste}
            disabled={loading}
            rows={1}
            placeholder={
              isSovereign
                ? 'Speak, sovereign… attach files or paste any text/HTML.'
                : 'Speak into the field… attach files or paste markdown.'
            }
            style={{
              flex: 1,
              padding: '11px 14px',
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${isSovereign ? 'rgba(201,168,76,0.2)' : 'rgba(0,212,170,0.2)'}`,
              borderRadius: 12,
              color: '#E8E8E8',
              fontFamily: 'Inter, sans-serif',
              fontSize: 13.5,
              lineHeight: 1.55,
              outline: 'none',
              resize: 'none',
              overflowY: 'auto',
              maxHeight: '38vh',
              minHeight: 44,
              transition: 'border-color 0.2s',
            }}
          />
          <button
            onClick={handleSend}
            disabled={(!input.trim() && !attachment) || loading}
            title="Send"
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: 44, height: 44, flexShrink: 0,
              padding: 0,
              background: (input.trim() || attachment) && !loading ? accentFaint : 'rgba(255,255,255,0.02)',
              border: `1px solid ${(input.trim() || attachment) && !loading ? accentBorder : 'rgba(255,255,255,0.06)'}`,
              borderRadius: 12,
              color: (input.trim() || attachment) && !loading ? accent : 'rgba(232,232,232,0.18)',
              cursor: (input.trim() || attachment) && !loading ? 'pointer' : 'not-allowed',
              transition: 'all 0.18s',
            }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>
      </div>
    </div>
  );
};

export default ArkanaCommune;
