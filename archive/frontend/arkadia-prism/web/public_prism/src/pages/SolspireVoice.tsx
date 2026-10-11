import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch, ApiError, setApiAuthToken } from '../lib/apiClient';

/**
 * Arkadia Voice — operator console at /solspire/voice.
 *
 * The backend owns every state transition (speech → transcript → intent →
 * context → authority → proposal → human decision → authorization →
 * execution → work event → evidence → verification). This surface never
 * guesses: it renders stored event fields, chain stage payloads and explicit
 * error states returned by POST /solspire/voice/*.
 */

type Json = Record<string, any>;

// ── transport ────────────────────────────────────────────────────────────────

class VoiceCallError extends Error {
  readonly state: string;
  readonly recovery: string | undefined;
  readonly status: number;
  readonly eventId: string | undefined;
  constructor(state: string, detail: string,
              opts: { recovery?: string; status?: number; eventId?: string } = {}) {
    super(detail);
    this.name = 'VoiceCallError';
    this.state = state;
    this.recovery = opts.recovery;
    this.status = opts.status ?? 0;
    this.eventId = opts.eventId;
  }
}

async function voiceCall<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await apiFetch(path, init);
  } catch (err) {
    if (err instanceof ApiError) {
      throw new VoiceCallError(err.kind === 'NETWORK_ERROR' ? 'NETWORK_ERROR' : 'REQUEST_FAILED',
        err.message, { recovery: 'The console could not reach the Arkadia API. Check the backend and retry.' });
    }
    throw err;
  }
  const raw = await res.text();
  let body: any = null;
  if (raw) { try { body = JSON.parse(raw); } catch { body = raw; } }
  if (!res.ok) {
    const detail = body && typeof body === 'object' ? body.detail : body;
    if (detail && typeof detail === 'object') {
      throw new VoiceCallError(detail.state || `HTTP_${res.status}`, String(detail.detail || res.statusText), {
        recovery: detail.recovery, status: res.status, eventId: detail.event_id,
      });
    }
    throw new VoiceCallError(`HTTP_${res.status}`, typeof detail === 'string' && detail ? detail : `${res.status} ${res.statusText}`,
      { status: res.status });
  }
  return body as T;
}

const jsonBody = (payload: Json): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});

/** Deterministic silent WAV (8 kHz mono 16-bit) — transport for the test provider. */
function silentWav(ms: number): Blob {
  const rate = 8000;
  const n = Math.max(1, Math.floor((rate * ms) / 1000));
  const buffer = new ArrayBuffer(44 + n * 2);
  const view = new DataView(buffer);
  const str = (off: number, s: string) => { for (let i = 0; i < s.length; i += 1) view.setUint8(off + i, s.charCodeAt(i)); };
  str(0, 'RIFF'); view.setUint32(4, 36 + n * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  str(36, 'data'); view.setUint32(40, n * 2, true);
  return new Blob([buffer], { type: 'audio/wav' });
}

// ── visual language ──────────────────────────────────────────────────────────

const C = {
  bg: '#0B0E17', panel: 'rgba(17,20,30,.74)', line: 'rgba(255,255,255,.10)',
  text: '#F1F4F7', dim: 'rgba(233,231,223,.42)', faint: 'rgba(233,231,223,.24)',
  teal: '#00D4AA', gold: '#C9A84C', red: '#E85246', blue: '#6A9FD8', violet: '#B08DE8',
};

const toneForStatus = (s: string | undefined): string => {
  if (!s) return C.dim;
  if (['FAILED', 'REJECTED'].includes(s)) return C.red;
  if (['EXECUTED', 'AUTHORIZED', 'APPROVED', 'UNDERSTOOD', 'TRANSCRIBED'].includes(s)) return C.teal;
  if (['PROPOSED', 'APPROVAL_REQUIRED', 'CLARIFICATION_REQUIRED', 'RECEIVED'].includes(s)) return C.gold;
  return C.dim;
};

const stageTone = (stage: string): string => {
  if (stage === 'ERROR') return C.red;
  if (['PROPOSAL', 'APPROVAL', 'AUTHORIZATION', 'CLARIFICATION', 'ProposalRevision'].includes(stage)) return C.gold;
  if (['INTENT', 'CONTEXT', 'AUTHORITY', 'EXECUTION', 'WORK_EVENT', 'EVIDENCE', 'VERIFICATION'].includes(stage)) return C.teal;
  return C.blue;
};

function Kicker({ children, color = C.dim }: { children: React.ReactNode; color?: string }) {
  return <div style={{ font: '600 8px Inter,system-ui,sans-serif', letterSpacing: '.2em', textTransform: 'uppercase', color }}>{children}</div>;
}

function Chip({ label, tone = C.dim, title }: { label: string; tone?: string; title?: string }) {
  return <span title={title} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 7px', border: `1px solid ${tone}44`, background: `${tone}10`, borderRadius: 5, font: '700 8px ui-monospace,SFMono-Regular,monospace', letterSpacing: '.1em', textTransform: 'uppercase', color: tone }}>{label}</span>;
}

function Panel({ index, title, meta, children }: { index: string; title: string; meta?: React.ReactNode; children: React.ReactNode }) {
  return <section style={{ padding: '16px 17px 17px', background: C.panel, border: `1px solid ${C.line}`, borderRadius: 13, boxShadow: '0 12px 36px rgba(0,0,0,.16)', backdropFilter: 'blur(18px)' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
        <span style={{ font: '700 9px ui-monospace,SFMono-Regular,monospace', color: C.teal, letterSpacing: '.14em' }}>{index}</span>
        <Kicker>{title}</Kicker>
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{meta}</div>
    </div>
    <div style={{ marginTop: 11 }}>{children}</div>
  </section>;
}

function Act({ children, onClick, disabled, loading, tone = C.teal, subtle }
  : { children: React.ReactNode; onClick: () => void; disabled?: boolean; loading?: boolean; tone?: string; subtle?: boolean }) {
  const off = Boolean(disabled || loading);
  return <button type="button" onClick={onClick} disabled={off}
    style={{ padding: '8px 13px', borderRadius: 8, cursor: off ? 'not-allowed' : 'pointer',
      border: `1px solid ${off ? 'rgba(255,255,255,.10)' : tone + '55'}`,
      background: subtle ? 'rgba(255,255,255,.04)' : (off ? 'rgba(255,255,255,.03)' : tone + '14'),
      color: off ? 'rgba(233,231,223,.3)' : tone,
      font: '700 9px Inter,system-ui,sans-serif', letterSpacing: '.14em', textTransform: 'uppercase',
      transition: 'all .16s' }}>
    {loading ? '…' : children}
  </button>;
}

function Fact({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return <div style={{ minWidth: 0 }}>
    <Kicker>{label}</Kicker>
    <div style={{ marginTop: 3, font: mono ? '11px ui-monospace,SFMono-Regular,monospace' : '11px Inter,system-ui,sans-serif', color: C.text, wordBreak: 'break-word' }}>{value}</div>
  </div>;
}

function ErrorCard({ state, detail, recovery }: { state: string; detail: string; recovery?: string }) {
  const tone = C.red;
  return <div data-testid="voice-error-card" style={{ padding: '12px 14px', border: `1px solid ${tone}40`, background: `${tone}0d`, borderRadius: 10 }}>
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
      <span style={{ fontSize: 12, color: tone }}>▲</span>
      <span style={{ font: '700 10px ui-monospace,SFMono-Regular,monospace', letterSpacing: '.12em', color: tone }}>{state}</span>
    </div>
    <p style={{ margin: '6px 0 0', font: '11px/1.6 Inter,system-ui,sans-serif', color: C.dim }}>{detail}</p>
    {recovery && <p style={{ margin: '5px 0 0', font: '11px/1.6 Inter,system-ui,sans-serif', color: 'rgba(233,231,223,.55)' }}>↳ {recovery}</p>}
  </div>;
}

// ── page ─────────────────────────────────────────────────────────────────────

const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];

export default function SolspireVoice({ onNavigate }: { onNavigate?: (view: string) => void }) {
  const { isAuthenticated, user, loading } = useAuth();
  useLayoutEffect(() => { setApiAuthToken(user?.idToken ?? null); }, [user?.idToken]);

  // backend status board
  const [status, setStatus] = useState<Json | null>(null);
  const [providers, setProviders] = useState<Json | null>(null);
  const [events, setEvents] = useState<Json[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [providersOpen, setProvidersOpen] = useState(false);
  const [chainOpen, setChainOpen] = useState(false);
  const [openStage, setOpenStage] = useState<number | null>(null);

  // canonical event + chain (the single source of truth for every panel)
  const [current, setCurrent] = useState<Json | null>(null);
  const [understanding, setUnderstanding] = useState<Json | null>(null);

  // capture
  const [recState, setRecState] = useState<'idle' | 'recording' | 'uploading'>('idle');
  const [elapsed, setElapsed] = useState(0);
  const [micError, setMicError] = useState<VoiceCallError | null>(null);
  const [providerChoice, setProviderChoice] = useState('auto');
  const [typedHint, setTypedHint] = useState('');
  const [clarifyDraft, setClarifyDraft] = useState<Record<string, string>>({});
  const [reviseDraft, setReviseDraft] = useState('');
  const [reviseOpen, setReviseOpen] = useState(false);
  const [claim, setClaim] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [failure, setFailure] = useState<VoiceCallError | null>(null);

  const sessionRef = useRef(`vs-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startRef = useRef(0);
  const discardRef = useRef(false);

  const eventId = current?.event?.event_id as string | undefined;
  const ev: Json | undefined = current?.event;
  const stages: Json[] = useMemo(() => current?.chain ?? [], [current]);

  const stagePayload = useCallback((recordType: string): Json | null => {
    for (let i = stages.length - 1; i >= 0; i -= 1) {
      if (stages[i]?.record_type === recordType) return stages[i].payload ?? null;
    }
    return null;
  }, [stages]);

  const refreshStatus = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([
        voiceCall<Json>('/solspire/voice/status'),
        voiceCall<Json>('/solspire/voice/providers'),
      ]);
      setStatus(s); setProviders(p);
    } catch (err) { setFailure(err instanceof VoiceCallError ? err : null); }
  }, []);

  const loadEvent = useCallback(async (id: string) => {
    const data = await voiceCall<Json>(`/solspire/voice/events/${id}`);
    setCurrent(data);
    return data;
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      const data = await voiceCall<Json>('/solspire/voice/events?limit=20');
      setEvents(data.events || []);
    } catch { /* history is auxiliary */ }
  }, []);

  useEffect(() => { if (isAuthenticated) { void refreshStatus(); void refreshHistory(); } }, [isAuthenticated, refreshStatus, refreshHistory]);

  // capture duration timer
  useEffect(() => {
    if (recState !== 'recording') return undefined;
    const id = window.setInterval(() => setElapsed(Date.now() - startRef.current), 200);
    return () => window.clearInterval(id);
  }, [recState]);

  const run = useCallback(async (key: string, fn: () => Promise<void>) => {
    setBusy(key); setFailure(null);
    try { await fn(); }
    catch (err) {
      const callErr = err instanceof VoiceCallError ? err : new VoiceCallError('REQUEST_FAILED', err instanceof Error ? err.message : String(err));
      setFailure(callErr);
      if (callErr.eventId && callErr.eventId !== eventId) { try { await loadEvent(callErr.eventId); } catch { /* event unreadable */ } }
    }
    finally { setBusy(null); }
  }, [eventId, loadEvent]);

  const ingestBlob = useCallback(async (blob: Blob, durationMs: number) => {
    setRecState('uploading');
    await run('capture', async () => {
      const form = new FormData();
      form.append('file', new File([blob], 'voice-capture', { type: blob.type || 'audio/webm' }));
      form.append('language', 'en');
      form.append('session_id', sessionRef.current);
      form.append('duration_ms', String(Math.max(0, Math.round(durationMs))));
      if (providerChoice !== 'auto') form.append('provider', providerChoice);
      if (providerChoice === 'test' && typedHint.trim()) form.append('transcript_hint', typedHint.trim());
      const res = await voiceCall<Json>('/solspire/voice/events', { method: 'POST', body: form });
      setUnderstanding(null);
      setClarifyDraft({});
      setReviseOpen(false);
      if (res?.event?.event_id) { await loadEvent(res.event.event_id); void refreshHistory(); }
    });
    setRecState('idle');
  }, [loadEvent, providerChoice, refreshHistory, run, typedHint]);

  const startCapture = useCallback(async () => {
    setFailure(null); setMicError(null);
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia || typeof window.MediaRecorder === 'undefined') {
      setMicError(new VoiceCallError('AUDIO_CAPTURE_FAILED', 'This browser exposes no microphone capture API.', { recovery: 'Use the typed test-provider path below, or open the console in a browser with MediaRecorder support.' }));
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setMicError(new VoiceCallError('MIC_DENIED',
        err instanceof Error ? err.message : 'microphone permission was not granted',
        { recovery: status?.error_states?.MICROPHONE_DENIED?.recovery || 'Grant microphone permission for this site, then retry capture.' }));
      return;
    }
    streamRef.current = stream;
    const mime = MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported?.(m));
    const rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
    chunksRef.current = [];
    discardRef.current = false;
    rec.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data); };
    rec.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: rec.mimeType || 'audio/webm' });
      const duration = Date.now() - startRef.current;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      recorderRef.current = null;
      if (discardRef.current) { discardRef.current = false; setRecState('idle'); return; }
      void ingestBlob(blob, duration);
    };
    recorderRef.current = rec;
    startRef.current = Date.now();
    setElapsed(0);
    setRecState('recording');
    rec.start();
  }, [ingestBlob, status]);

  const stopCapture = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === 'recording') recorderRef.current.stop();
    else setRecState('idle');
  }, []);

  const cancelCapture = useCallback(() => {
    discardRef.current = true;
    if (recorderRef.current && recorderRef.current.state === 'recording') recorderRef.current.stop();
    else { setRecState('idle'); discardRef.current = false; }
  }, []);

  const sendTyped = useCallback(() => {
    if (!typedHint.trim()) return;
    void ingestBlob(silentWav(400), 400);
  }, [ingestBlob, typedHint]);

  // ── pipeline actions (each one re-reads the canonical event afterwards) ──
  const actUnderstand = useCallback((disambiguations: Json = {}) => eventId && run('understand', async () => {
    const res = await voiceCall<Json>(`/solspire/voice/events/${eventId}/understand`, jsonBody({ disambiguations }));
    setUnderstanding(res);
    await loadEvent(eventId);
  }), [eventId, loadEvent, run]);

  const actPropose = useCallback(() => eventId && run('propose', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/propose`, { method: 'POST' });
    await loadEvent(eventId);
  }), [eventId, loadEvent, run]);

  const actDecision = useCallback((decision: 'ACCEPTED' | 'DECLINED') => eventId && run('decision', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/decision`, jsonBody({ decision }));
    await loadEvent(eventId);
  }), [eventId, loadEvent, run]);

  const actRevise = useCallback(() => eventId && run('revise', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/revise`,
      jsonBody({ requested_action: reviseDraft.trim() || undefined, reason: 'operator edit from the voice console' }));
    setReviseOpen(false); setReviseDraft('');
    await loadEvent(eventId);
  }), [eventId, loadEvent, reviseDraft, run]);

  const actAuthorize = useCallback(() => eventId && run('authorize', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/authorize`, { method: 'POST' });
    await loadEvent(eventId);
  }), [eventId, loadEvent, run]);

  const actExecute = useCallback(() => eventId && run('execute', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/execute`, { method: 'POST' });
    await loadEvent(eventId);
    void refreshHistory();
  }), [eventId, loadEvent, refreshHistory, run]);

  const actVerify = useCallback((verdict: 'VERIFIED' | 'INSUFFICIENT' | 'CONTRADICTED') => eventId && run('verify', async () => {
    await voiceCall<Json>(`/solspire/voice/events/${eventId}/verify`, jsonBody({ verdict, claim: claim.trim() }));
    await loadEvent(eventId);
  }), [claim, eventId, loadEvent, run]);

  const openAudio = useCallback(async () => {
    if (!eventId) return;
    try {
      const res = await apiFetch(`/solspire/voice/events/${eventId}/audio`);
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new window.Audio(url);
      audio.controls = true;
      audio.style.width = '100%';
      audio.style.marginTop = '8px';
      const host = document.getElementById('voice-audio-slot');
      if (host) { host.innerHTML = ''; host.appendChild(audio); }
      URL.revokeObjectURL(url);
    } catch { /* playback is optional */ }
  }, [eventId]);

  if (loading) {
    return <div style={{ minHeight: '60vh', display: 'grid', placeItems: 'center', color: C.dim, font: '11px Inter,sans-serif', letterSpacing: '.14em', textTransform: 'uppercase' }}>Establishing session…</div>;
  }
  if (!isAuthenticated) {
    return <div className="solspire-auth-threshold"><div className="solspire-auth-card">
      <div className="solspire-brand-name">ARKADIA VOICE</div>
      <div className="solspire-kicker">SPEECH INPUT · GOVERNED EXECUTION</div>
      <p>Sign in to open the voice operator console. Every spoken request is transcribed, understood, proposed and approved by a human before anything executes.</p>
      <button type="button" onClick={() => onNavigate?.('gate')}>Sign in / create your node</button>
    </div></div>;
  }

  // ── derived, stored facts (never invented) ───────────────────────────────
  const intent: Json | null = ev?.intent ?? null;
  const context: Json | null = ev?.context ?? null;
  const authority: Json | null = stagePayload('AuthorityAssessment');
  const proposalStage: Json | null = stagePayload('Proposal');
  const authorizationStage: Json | null = stagePayload('Authorization');
  const executionStage: Json | null = stagePayload('Execution');
  const verificationStage: Json | null = stagePayload('Verification');
  const proposalStatus: string | undefined = proposalStage?.proposal?.proposal_status;
  const ambiguities: Json[] = context?.ambiguities ?? [];
  const riskPolicy: Json = status?.risk_policy ?? {};
  const errorStates: Json = status?.error_states ?? {};
  const stageNames: string[] = status?.chain ?? [];
  const presentStages = new Set(stages.map((s) => s.stage));
  const requiresProposal = intent ? !['ASK', 'SEARCH'].includes(intent.action) : false;
  const storedFailure = ev?.error_state
    ? { state: ev.error_state as string, detail: String(ev.error_detail || ''), recovery: errorStates[ev.error_state]?.recovery }
    : null;
  const softError = understanding?.error ?? null;
  const shownError = failure ?? micError ?? (softError
    ? new VoiceCallError(softError.state, softError.detail, { recovery: softError.recovery })
    : storedFailure ? new VoiceCallError(storedFailure.state, storedFailure.detail, { recovery: storedFailure.recovery }) : null);
  const providerList: Json[] = providers?.providers ?? [];
  const seconds = Math.floor(elapsed / 1000);
  const clock = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;

  const can = {
    understand: Boolean(eventId) && Boolean(ev?.transcript) && !busy,
    clarify: Boolean(eventId) && (ev?.status === 'CLARIFICATION_REQUIRED' || softError?.state === 'CONTEXT_AMBIGUOUS') && !busy,
    propose: Boolean(eventId) && ev?.status === 'UNDERSTOOD' && requiresProposal && !ev?.proposal_id && !busy,
    decide: Boolean(eventId) && ev?.status === 'PROPOSED' && !busy,
    authorize: Boolean(eventId) && ev?.status === 'APPROVED' && !ev?.authorization_ref && !busy,
    execute: Boolean(eventId) && (
      ev?.status === 'AUTHORIZED' ||
      (ev?.status === 'UNDERSTOOD' && !requiresProposal)
    ) && !busy,
    verify: Boolean(eventId) && Boolean(ev?.evidence_ref) && !busy,
    revise: Boolean(eventId) && Boolean(ev?.proposal_id) && ['PROPOSED', 'REJECTED'].includes(ev?.status || '') && !busy,
  };

  return (
    <div data-testid="solspire-voice-console" style={{ width: '100%', maxWidth: 1180, margin: '0 auto', padding: '18px 16px 60px', boxSizing: 'border-box' }}>
      {/* header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 0 }}>
          <Kicker color={C.teal}>SOLSPIRE · OPERATOR SURFACE</Kicker>
          <h1 style={{ margin: '6px 0 4px', font: '400 30px Georgia,"Times New Roman",serif', color: C.text, letterSpacing: '-.01em' }}>Arkadia Voice</h1>
          <div className="solspire-mono" style={{ color: C.faint }}>speech → transcript → intent → context → authority → proposal → approval → authorization → execution → evidence → verification</div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <Act subtle tone={C.blue} onClick={() => { setProvidersOpen((v) => !v); setHistoryOpen(false); }}>Providers</Act>
          <Act subtle tone={C.gold} onClick={() => { setHistoryOpen((v) => !v); setProvidersOpen(false); }}>Recent events</Act>
          <Act subtle tone={C.teal} onClick={() => setChainOpen(true)} disabled={!eventId}>Evidence chain</Act>
        </div>
      </div>

      {/* status board */}
      <div style={{ marginTop: 14, padding: '12px 15px', border: `1px solid ${C.line}`, borderRadius: 12, background: 'rgba(13,17,27,.7)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <Kicker>SUBJECT</Kicker>
            <Chip label={status?.subject?.role || 'node'} tone={C.gold} />
            <Chip label={`access ${status?.subject?.access_level ?? '—'}`} tone={C.blue} />
            <Chip label={ev ? `event ${ev.status}` : 'no event'} tone={toneForStatus(ev?.status)} />
            {ev?.proposal_id && <Chip label={`proposal ${proposalStatus || 'open'}`} tone={C.gold} title={ev.proposal_id} />}
            {ev?.authorization_ref && <Chip label="authorized" tone={C.teal} title={ev.authorization_ref} />}
            {ev?.work_event_id && <Chip label={`work ${ev.work_event_id}`} tone={C.teal} title={ev.work_event_id} />}
            {ev?.evidence_ref && <Chip label="evidence" tone={C.teal} title={ev.evidence_ref} />}
            {ev?.verification_ref && <Chip label="verified" tone={C.teal} title={ev.verification_ref} />}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {(stageNames.length ? stageNames : []).map((name) => (
              <span key={name} title={presentStages.has(name) ? 'recorded' : 'not reached'}
                style={{ font: '700 7.5px ui-monospace,SFMono-Regular,monospace', letterSpacing: '.1em', textTransform: 'uppercase',
                  color: presentStages.has(name) ? stageTone(name) : 'rgba(233,231,223,.2)',
                  borderBottom: presentStages.has(name) ? `1px solid ${stageTone(name)}` : '1px solid transparent', padding: '2px 0', marginRight: 6 }}>
                {name}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* providers + history panels */}
      <AnimatePresence>
        {providersOpen && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} style={{ marginTop: 12 }}>
            <Panel index="A0" title="ASR providers (configuration names only — no secrets)" meta={<Chip label={`default: ${(providers?.default_priority || []).join(' → ')}`} tone={C.blue} />}>
              <div style={{ display: 'grid', gap: 8 }}>
                {providerList.map((p) => (
                  <div key={p.name} style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap', padding: '8px 10px', border: `1px solid ${C.line}`, borderRadius: 9 }}>
                    <span style={{ font: '700 11px ui-monospace,SFMono-Regular,monospace', color: C.text }}>{p.name}</span>
                    <Chip label={p.state} tone={p.state === 'AVAILABLE' ? C.teal : p.state === 'UNAVAILABLE' ? C.red : C.gold} />
                    {p.model && <span style={{ font: '10px Inter,sans-serif', color: C.dim }}>model {p.model}</span>}
                    {p.config_source && <span style={{ font: '10px Inter,sans-serif', color: C.faint }}>via {p.config_source}</span>}
                    {typeof p.recognized === 'boolean' && <Chip label={p.recognized ? 'recognizes speech' : 'no speech recognition'} tone={p.recognized ? C.teal : C.gold} />}
                    {p.reason && <span style={{ font: '10px/1.5 Inter,sans-serif', color: C.dim, flexBasis: '100%' }}>{p.reason}</span>}
                  </div>
                ))}
                {providers?.requested_env && <div className="solspire-mono" style={{ color: C.faint }}>pinned by {providers.selection_env} = {providers.requested_env}</div>}
              </div>
            </Panel>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {historyOpen && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} style={{ marginTop: 12 }}>
            <Panel index="A1" title="Recent voice events" meta={<Chip label={`${events.length}`} tone={C.blue} />}>
              {events.length === 0 && <div style={{ font: '11px Inter,sans-serif', color: C.dim }}>No events recorded for this subject yet.</div>}
              <div style={{ display: 'grid', gap: 6 }}>
                {events.map((e) => (
                  <button key={e.event_id} type="button" onClick={() => { void loadEvent(e.event_id); setHistoryOpen(false); }}
                    style={{ display: 'flex', gap: 10, alignItems: 'center', textAlign: 'left', padding: '8px 10px', borderRadius: 9,
                      border: `1px solid ${e.event_id === eventId ? 'rgba(0,212,170,.4)' : C.line}`, background: e.event_id === eventId ? 'rgba(0,212,170,.06)' : 'rgba(255,255,255,.02)', cursor: 'pointer' }}>
                    <Chip label={e.status} tone={toneForStatus(e.status)} />
                    <span style={{ flex: 1, minWidth: 0, font: '11px Inter,sans-serif', color: C.dim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {e.transcript?.text || '—'}
                    </span>
                    <span className="solspire-mono" style={{ color: C.faint, flexShrink: 0 }}>{new Date((e.created_at || 0) * 1000).toLocaleString()}</span>
                  </button>
                ))}
              </div>
            </Panel>
          </motion.div>
        )}
      </AnimatePresence>

      {/* visible failure states */}
      {shownError && (
        <div style={{ marginTop: 12 }}>
          <ErrorCard state={shownError.state} detail={shownError.detail} recovery={shownError.recovery} />
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 12, marginTop: 12 }}>
        {/* 02 — voice control */}
        <Panel index="02" title="Voice control"
          meta={<>
            <Chip label={recState === 'recording' ? `recording ${clock}` : recState === 'uploading' ? 'transcribing…' : 'idle'} tone={recState === 'recording' ? C.red : C.teal} />
            <Chip label={`max ${Math.round(((status?.max_audio_bytes || 5242880) / 1048576))} MiB`} tone={C.blue} />
          </>}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {recState !== 'recording' ? (
              <Act onClick={() => void startCapture()} disabled={recState === 'uploading'} loading={busy === 'capture'} tone={C.red}>
                ● Start capture
              </Act>
            ) : (
              <>
                <Act onClick={stopCapture} tone={C.teal}>■ Stop & transcribe</Act>
                <Act onClick={cancelCapture} tone={C.gold} subtle>Cancel</Act>
              </>
            )}
            <label style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <Kicker>PROVIDER</Kicker>
              <select value={providerChoice} onChange={(e) => setProviderChoice(e.target.value)}
                style={{ padding: '7px 9px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }}>
                <option value="auto">auto (backend priority)</option>
                {providerList.map((p) => <option key={p.name} value={p.name}>{p.name} — {p.state}</option>)}
              </select>
            </label>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 7, alignItems: 'center' }}>
              <span className="solspire-mono" style={{ color: C.faint }}>no mic?</span>
              <input value={typedHint} onChange={(e) => setTypedHint(e.target.value)}
                placeholder="type the utterance (test provider)"
                style={{ width: 230, padding: '7px 9px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }} />
              <Act subtle tone={C.blue} onClick={() => void sendTyped()} disabled={!typedHint.trim() || recState !== 'idle' || Boolean(busy)}>Send</Act>
            </div>
          </div>
          <p style={{ margin: '10px 0 0', font: '11px/1.6 Inter,sans-serif', color: C.dim }}>
            Audio is captured in the browser, hashed and stored server-side (sha256), then transcribed by the selected ASR provider.
            The transcript you see below is exactly what the provider returned — provenance is shown with it.
          </p>
          {recState === 'recording' && <div style={{ marginTop: 9, font: '700 13px ui-monospace,monospace', color: C.red, letterSpacing: '.12em' }}>● REC {clock}</div>}
        </Panel>

        {/* 03 — transcript */}
        <Panel index="03" title="Transcript & provenance"
          meta={ev?.transcript ? <>
            <Chip label={ev.transcript.provider || ev.asr_provenance?.provider || 'unknown provider'} tone={C.blue} />
            <Chip label={ev.transcript.recognized ? 'speech recognized' : 'not a recognizer'} tone={ev.transcript.recognized ? C.teal : C.gold} />
            {ev.transcript.confidence != null && <Chip label={`conf ${Number(ev.transcript.confidence).toFixed(2)}`} tone={C.teal} />}
            <Chip label={`sha256 ${(ev.audio_hash || '').slice(0, 16)}…`} tone={C.faint} title={ev.audio_hash} />
          </> : <Chip label="awaiting capture" tone={C.dim} />}>
          {ev?.transcript ? (
            <>
              <blockquote data-testid="voice-transcript" style={{ margin: 0, padding: '11px 14px', borderLeft: `2px solid ${C.teal}`, background: 'rgba(0,212,170,.05)', borderRadius: '0 9px 9px 0', font: '400 15px/1.6 Georgia,serif', color: C.text }}>
                “{ev.transcript.text}”
              </blockquote>
              <div style={{ display: 'flex', gap: 8, marginTop: 9, flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="solspire-mono" style={{ color: C.faint }}>
                  {ev.audio_mime} · {ev.audio_size} bytes · {ev.duration_ms ?? '—'} ms · lang {ev.language}
                </span>
                <Act subtle tone={C.blue} onClick={() => void openAudio()}>Play audio</Act>
                <div id="voice-audio-slot" style={{ flexBasis: '100%' }} />
              </div>
            </>
          ) : (
            <div style={{ font: '11px Inter,sans-serif', color: C.dim }}>No transcript yet — record an utterance or use the typed test-provider path above.</div>
          )}
        </Panel>

        {/* 04 — understanding */}
        <Panel index="04" title="Understanding — intent · context · authority"
          meta={<>
            {intent && <Chip label={intent.action} tone={intent.action === 'UNKNOWN' ? C.red : C.teal} />}
            {intent?.confidence != null && <Chip label={`confidence ${intent.confidence}`} tone={C.blue} />}
            {context && <Chip label={`context ${context.resolution_status}`} tone={context.resolution_status === 'KNOWN' ? C.teal : C.gold} />}
            {authority && <Chip label={authority.authority_status} tone={authority.authority_status === 'OBSERVATION_ONLY' ? C.blue : C.gold} />}
            {intent?.entities?.human_only && <Chip label="human-only — refused at voice boundary" tone={C.red} />}
          </>}>
          {intent || context ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
              <Fact label="CANONICAL INTENT" value={intent?.canonical_intent_type || intent?.intent_type || '—'} mono />
              <Fact label="SUBJECT / OBJECT" value={
                Object.entries(intent?.entities || {}).filter(([k]) => k !== 'human_only')
                  .map(([k, v]) => `${k}: ${String(v)}`).join(' · ') || '—'} />
              <Fact label="RESOLVED" value={
                Object.entries(context?.resolved_entities || {}).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : String(v)}`).join(' · ') || '—'} />
              {authority && <Fact label="POLICY" value={authority.required_approval ? 'proposal → approval → authorization → execution' : 'observation-only (READ disposition)'} />}
            </div>
          ) : (
            <div style={{ font: '11px Inter,sans-serif', color: C.dim }}>
              {ev ? 'Not understood yet — run understanding on this event.' : 'Capture a transcript first.'}
            </div>
          )}

          {ambiguities.length > 0 && (
            <div style={{ marginTop: 12, padding: '11px 13px', border: `1px solid ${C.gold}3a`, background: `${C.gold}0a`, borderRadius: 10 }}>
              <Kicker color={C.gold}>CLARIFY BEFORE PROCEEDING</Kicker>
              <div style={{ display: 'grid', gap: 7, marginTop: 8 }}>
                {ambiguities.map((a) => (
                  <div key={a.field} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ font: '700 9px ui-monospace,monospace', letterSpacing: '.1em', color: C.gold, textTransform: 'uppercase', minWidth: 96 }}>{a.field}</span>
                    {Array.isArray(a.candidates) && a.candidates.length > 0 ? (
                      <select value={clarifyDraft[a.field] || ''} onChange={(e) => setClarifyDraft((d) => ({ ...d, [a.field]: e.target.value }))}
                        style={{ flex: 1, minWidth: 180, padding: '7px 9px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }}>
                        <option value="">choose one…</option>
                        {a.candidates.map((c: any) => <option key={String(c)} value={String(c)}>{String(c)}</option>)}
                      </select>
                    ) : (
                      <input value={clarifyDraft[a.field] || ''} onChange={(e) => setClarifyDraft((d) => ({ ...d, [a.field]: e.target.value }))}
                        placeholder={`name the ${a.field} explicitly`}
                        style={{ flex: 1, minWidth: 180, padding: '7px 9px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }} />
                    )}
                    {a.reason && <span style={{ font: '10px Inter,sans-serif', color: C.dim }}>{a.reason}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
            <Act onClick={() => void actUnderstand()} disabled={!can.understand} loading={busy === 'understand'}>
              {intent ? 'Re-run understanding' : 'Understand transcript'}
            </Act>
            {can.clarify && (
              <Act tone={C.gold} onClick={() => void actUnderstand(clarifyDraft)} loading={busy === 'understand'}>
                Submit clarification
              </Act>
            )}
          </div>
        </Panel>

        {/* 05 — proposal */}
        <Panel index="05" title="Arkadia proposes"
          meta={<>
            {proposalStage?.voice_proposal ? <Chip label={`risk ${proposalStage.voice_proposal.risk_level}`} tone={C.gold} /> : riskPolicy && intent && <Chip label={`risk ${riskPolicy[intent.action] || '—'}`} tone={C.gold} />}
            {proposalStatus && <Chip label={proposalStatus} tone={proposalStatus === 'ACCEPTED' ? C.teal : proposalStatus === 'DECLINED' || proposalStatus === 'WITHDRAWN' ? C.red : C.gold} />}
            {proposalStage?.voice_proposal && <Chip label={proposalStage.voice_proposal.authority_status} tone={C.gold} />}
            {proposalStage?.voice_proposal && <Chip label={`authz ${proposalStage.voice_proposal.authorization_status}`} tone={authorizationStage ? C.teal : C.dim} />}
            {authorizationStage && <Chip label="AUTHORIZED by govern authority" tone={C.teal} />}
          </>}>
          {!intent ? (
            <div style={{ font: '11px Inter,sans-serif', color: C.dim }}>No proposal surface until the transcript is understood.</div>
          ) : !requiresProposal ? (
            <div data-testid="voice-observation-note" style={{ padding: '10px 13px', border: `1px solid ${C.blue}3a`, background: `${C.blue}0a`, borderRadius: 10, font: '11px/1.6 Inter,sans-serif', color: C.dim }}>
              Observation-only request ({intent.action}) — no proposal and no approval required (Engineering Lab voice boundary, READ disposition).
              The result is still recorded as a work event with evidence.
            </div>
          ) : proposalStage ? (
            <div style={{ display: 'grid', gap: 10 }}>
              <div style={{ padding: '11px 14px', border: `1px solid ${C.gold}33`, background: `${C.gold}0a`, borderRadius: 10 }}>
                <div style={{ font: '400 15px/1.55 Georgia,serif', color: C.text }}>{proposalStage.proposal?.objective}</div>
                <div style={{ display: 'flex', gap: 14, marginTop: 8, flexWrap: 'wrap' }}>
                  <Fact label="REQUESTED" value={proposalStage.voice_proposal?.requested_action || '—'} />
                  <Fact label="EXECUTOR" value={proposalStage.voice_proposal?.executor || 'UNSUPPORTED'} mono />
                </div>
                {proposalStage.voice_proposal?.detail?.warning && (
                  <div style={{ marginTop: 8, font: '10px/1.5 Inter,sans-serif', color: C.red }}>⚠ {proposalStage.voice_proposal.detail.warning}: no canonical executor maps to this request — execution would be refused.</div>
                )}
                <div style={{ marginTop: 8, font: '10px/1.5 Inter,sans-serif', color: C.dim }}>
                  alternatives: {((proposalStage.proposal?.alternatives || []).join(' · ')) || '—'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <Act onClick={() => void actDecision('ACCEPTED')} disabled={!can.decide} loading={busy === 'decision'}>Approve</Act>
                <Act tone={C.red} onClick={() => void actDecision('DECLINED')} disabled={!can.decide} loading={busy === 'decision'}>Reject</Act>
                <Act tone={C.gold} subtle onClick={() => setReviseOpen((v) => !v)} disabled={!can.revise}>Edit</Act>
                <span className="solspire-mono" style={{ color: C.faint }}>a human decision is not authorization</span>
              </div>
              {reviseOpen && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <input value={reviseDraft} onChange={(e) => setReviseDraft(e.target.value)} placeholder="restate the request"
                    style={{ flex: 1, minWidth: 220, padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }} />
                  <Act tone={C.gold} onClick={() => void actRevise()} loading={busy === 'revise'}>Withdraw & re-propose</Act>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              <Act tone={C.gold} onClick={() => void actPropose()} disabled={!can.propose} loading={busy === 'propose'}>
                Draft proposal
              </Act>
              <span className="solspire-mono" style={{ color: C.faint }}>consequential actions require an explicit proposal</span>
            </div>
          )}
        </Panel>

        {/* 06 — authorize / execute */}
        <Panel index="06" title="Authorization & execution"
          meta={<>
            <Chip label={ev?.authorization_ref ? 'authorized' : ev?.status === 'APPROVED' ? 'awaiting authorization' : 'not authorized'} tone={ev?.authorization_ref ? C.teal : C.gold} />
            <Chip label={ev?.execution_id ? `exec ${ev.execution_id}` : 'not executed'} tone={ev?.execution_id ? C.teal : C.dim} />
            <Chip label={ev?.work_event_id ? `work ${ev.work_event_id}` : 'no work event'} tone={ev?.work_event_id ? C.teal : C.dim} />
          </>}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <Act tone={C.blue} onClick={() => void actAuthorize()} disabled={!can.authorize} loading={busy === 'authorize'}>
              Authorize (govern authority)
            </Act>
            <Act onClick={() => void actExecute()} disabled={!can.execute} loading={busy === 'execute'}>
              Execute
            </Act>
            {!can.authorize && !can.execute && ev && (
              <span className="solspire-mono" style={{ color: C.faint }}>
                {ev.status === 'PROPOSED' ? 'approve the proposal first' :
                 ev.status === 'REJECTED' ? 'proposal declined — edit or recapture' :
                 ev.status === 'UNDERSTOOD' && requiresProposal ? 'draft and approve a proposal first' :
                 'not executable in the current state'}
              </span>
            )}
          </div>
          {authorizationStage && (
            <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              <Fact label="AUTHORIZATION ID" value={authorizationStage.authorization?.id || ev?.authorization_ref || '—'} mono />
              <Fact label="CHANNEL" value={authorizationStage.scope?.channel || '—'} mono />
              <Fact label="TOOLS" value={(authorizationStage.scope?.tools || []).join(', ') || '—'} mono />
            </div>
          )}
          {executionStage && (
            <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              <Fact label="EXECUTION" value={executionStage.ok ? 'ok' : 'failed'} mono />
              <Fact label="STATUS" value={executionStage.result?.status || '—'} mono />
              <Fact label="RESULT" value={JSON.stringify(executionStage.result?.result ?? executionStage.result ?? {}).slice(0, 160)} mono />
            </div>
          )}
          {executionStage?.result?.note && <div style={{ marginTop: 8, font: '11px/1.6 Inter,sans-serif', color: C.dim }}>{executionStage.result.note}</div>}
        </Panel>

        {/* 07 — evidence & verification */}
        <Panel index="07" title="Evidence & verification"
          meta={<>
            <Chip label={ev?.evidence_ref ? 'evidence recorded' : 'no evidence yet'} tone={ev?.evidence_ref ? C.teal : C.dim} />
            <Chip label={ev?.verification_ref ? (verificationStage?.verification?.verdict || 'verified') : 'verification pending'} tone={ev?.verification_ref ? C.teal : C.gold} />
            {current?.chain_digest && <Chip label={`digest ${String(current.chain_digest).slice(0, 12)}…`} tone={C.faint} title={current.chain_digest} />}
          </>}>
          <div style={{ font: '11px/1.6 Inter,sans-serif', color: C.dim }}>
            Execution is not verification: a successful executor response is not verified real-world completion. Verification is a separate human act against the recorded evidence.
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 11, flexWrap: 'wrap', alignItems: 'center' }}>
            <input value={claim} onChange={(e) => setClaim(e.target.value)} placeholder="claim to verify (optional)"
              style={{ flex: 1, minWidth: 220, padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,.04)', border: `1px solid ${C.line}`, color: C.text, font: '11px Inter,sans-serif' }} />
            <Act onClick={() => void actVerify('VERIFIED')} disabled={!can.verify} loading={busy === 'verify'}>Verify</Act>
            <Act tone={C.gold} onClick={() => void actVerify('INSUFFICIENT')} disabled={!can.verify} loading={busy === 'verify'}>Insufficient</Act>
            <Act tone={C.red} onClick={() => void actVerify('CONTRADICTED')} disabled={!can.verify} loading={busy === 'verify'}>Contradicted</Act>
          </div>
          {verificationStage?.verification && (
            <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              <Fact label="VERDICT" value={verificationStage.verification.verdict || '—'} mono />
              <Fact label="VERIFIER" value={verificationStage.verification.verifier || '—'} mono />
              <Fact label="CLAIM" value={verificationStage.verification.claim || '—'} />
            </div>
          )}
        </Panel>
      </div>

      {/* evidence chain drawer */}
      <AnimatePresence>
        {chainOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setChainOpen(false)}
              style={{ position: 'fixed', inset: 0, zIndex: 80, background: 'rgba(2,3,8,.6)' }} />
            <motion.aside data-testid="voice-chain-drawer" initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 34 }}
              style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(460px, 92vw)', zIndex: 81,
                background: 'rgba(9,10,22,.98)', borderLeft: `1px solid ${C.gold}33`, display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', borderBottom: `1px solid ${C.line}` }}>
                <div>
                  <Kicker color={C.gold}>EVIDENCE CHAIN</Kicker>
                  <div className="solspire-mono" style={{ color: C.faint, marginTop: 4 }}>{eventId || 'no event selected'}</div>
                </div>
                <button type="button" onClick={() => setChainOpen(false)} aria-label="Close evidence chain"
                  style={{ background: 'none', border: `1px solid ${C.line}`, borderRadius: 8, color: C.dim, cursor: 'pointer', padding: '5px 9px' }}>✕</button>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px 20px' }}>
                {current?.chain_digest && (
                  <div className="solspire-mono" style={{ color: C.faint, marginBottom: 10, wordBreak: 'break-all' }}>chain digest · {current.chain_digest}</div>
                )}
                {stages.length === 0 && <div style={{ font: '11px Inter,sans-serif', color: C.dim }}>No chain stages yet.</div>}
                {stages.map((s) => {
                  const tone = stageTone(s.stage);
                  const open = openStage === s.seq;
                  return <div key={s.seq} style={{ position: 'relative', paddingLeft: 18, marginBottom: 10 }}>
                    <span style={{ position: 'absolute', left: 3, top: 4, width: 7, height: 7, borderRadius: '50%', background: tone, boxShadow: `0 0 8px ${tone}66` }} />
                    <button type="button" onClick={() => setOpenStage(open ? null : s.seq)}
                      style={{ width: '100%', textAlign: 'left', padding: '8px 10px', borderRadius: 9, cursor: 'pointer',
                        border: `1px solid ${open ? tone + '55' : C.line}`, background: open ? tone + '0f' : 'rgba(255,255,255,.02)' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
                        <span style={{ font: '700 8px ui-monospace,monospace', color: C.faint }}>#{s.seq}</span>
                        <span style={{ font: '700 9px ui-monospace,monospace', letterSpacing: '.1em', color: tone }}>{s.stage}</span>
                        <span style={{ font: '9px Inter,sans-serif', color: C.dim }}>{s.record_type}</span>
                        <span style={{ marginLeft: 'auto', font: '8px ui-monospace,monospace', color: C.faint }}>
                          {new Date((s.created_at || 0) * 1000).toLocaleTimeString()}
                        </span>
                      </div>
                      <div style={{ font: '8px ui-monospace,monospace', color: C.faint, marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {s.record_id} · {String(s.payload_digest || '').slice(0, 16)}…
                      </div>
                    </button>
                    {open && (
                      <pre style={{ margin: '6px 0 0', padding: '10px 11px', maxHeight: 260, overflow: 'auto', borderRadius: 9,
                        border: `1px solid ${C.line}`, background: 'rgba(0,0,0,.35)', font: '10px/1.55 ui-monospace,SFMono-Regular,monospace', color: 'rgba(233,231,223,.72)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(s.payload, null, 2)}
                      </pre>
                    )}
                  </div>;
                })}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
