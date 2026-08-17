/**
 * PersonalUploadZone — the PERSONAL document + note capture surface.
 *
 * Distinct from the public Spiral Codex upload (which lives in the
 * Encyclopedia / NexusSpiralCodex and writes to the shared public scroll
 * corpus via /api/codex/upload). This zone routes ONLY into the authenticated
 * node's private Knowledge OS vault:
 *
 *   - File attachments (PDF/DOCX/TXT/MD/HTML/JSON) → /api/personal/ingest-file
 *   - Quick text capture                          → /api/personal/ingest-note
 *
 * Personal uploads never touch the public scroll store.
 */
import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE } from '../lib/apiConfig';

type Status = 'idle' | 'uploading' | 'success' | 'error';

export default function PersonalUploadZone() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [msg, setMsg] = useState('');
  const [dragOver, setDragOver] = useState(false);

  // quick-capture
  const [noteTitle, setNoteTitle] = useState('');
  const [noteBody, setNoteBody] = useState('');
  const [noteType, setNoteType] = useState('note');

  const ingestFile = async (file: File) => {
    setStatus('uploading'); setMsg('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('note_type', 'document');
      fd.append('tags', 'personal,upload');
      const res = await fetch(`${API_BASE}/api/personal/ingest-file`, { method: 'POST', body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `${res.status}`);
      setStatus('success');
      setMsg(data.message || `'${file.name}' ingested into your personal vault.`);
      setTimeout(() => setStatus('idle'), 3200);
    } catch (e) {
      setStatus('error');
      setMsg((e as Error).message || 'Upload failed.');
    }
  };

  const onPick = (files: FileList | null) => {
    if (files && files[0]) ingestFile(files[0]);
  };

  const submitNote = async () => {
    if (!noteTitle.trim() || !noteBody.trim()) return;
    setStatus('uploading'); setMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/personal/ingest-note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: noteTitle.trim(), content: noteBody.trim(), note_type: noteType, tags: ['personal', 'capture'] }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `${res.status}`);
      setStatus('success');
      setMsg(data.message || 'Personal capture ingested.');
      setNoteTitle(''); setNoteBody('');
      setTimeout(() => setStatus('idle'), 2600);
    } catch (e) {
      setStatus('error');
      setMsg((e as Error).message || 'Capture failed.');
    }
  };

  return (
    <div style={{
      marginTop: 28, marginBottom: 28,
      padding: '18px 20px',
      background: 'rgba(0,212,170,0.03)',
      border: '1px solid rgba(0,212,170,0.18)',
      borderBottom: '3px solid rgba(0,212,170,0.45)',
      borderRadius: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <span style={{ color: '#00D4AA', fontSize: 14 }}>⬡</span>
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.7)' }}>
          Personal Capture · private Knowledge OS vault
        </span>
      </div>

      {/* File attachment dropzone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); onPick(e.dataTransfer.files); }}
        style={{
          cursor: 'pointer',
          padding: '22px 16px',
          border: `1.5px dashed ${dragOver ? 'rgba(0,212,170,0.6)' : 'rgba(0,212,170,0.25)'}`,
          borderRadius: 10,
          background: dragOver ? 'rgba(0,212,170,0.06)' : 'rgba(0,0,0,0.18)',
          textAlign: 'center',
          transition: 'all 0.15s',
        }}
      >
        <input ref={fileRef} type="file" style={{ display: 'none' }}
          accept=".pdf,.docx,.txt,.md,.html,.htm,.json"
          onChange={e => onPick(e.target.files)} />
        <div style={{ fontSize: 20, marginBottom: 6 }}>📄</div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(212,223,232,0.75)', margin: 0 }}>
          {status === 'uploading' ? 'Ingesting…' : 'Drop a document or click to upload'}
        </p>
        <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(0,212,170,0.45)', margin: '4px 0 0', letterSpacing: '0.12em' }}>
          PDF · DOCX · TXT · MD · HTML · JSON → personal vault
        </p>
      </div>

      {/* Quick text capture */}
      <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={noteTitle} onChange={e => setNoteTitle(e.target.value)}
            placeholder="Capture title…"
            style={{ flex: 1, padding: '9px 12px', background: 'rgba(0,0,0,0.22)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: 8, color: 'rgba(212,223,232,0.9)', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }} />
          <select value={noteType} onChange={e => setNoteType(e.target.value)}
            style={{ padding: '0 12px', background: 'rgba(14,17,32,0.9)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: 8, color: 'rgba(212,223,232,0.8)', fontFamily: 'sans-serif', fontSize: 11, outline: 'none' }}>
            {['note', 'research', 'decision', 'daily', 'conversation'].map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <textarea value={noteBody} onChange={e => setNoteBody(e.target.value)} rows={3}
          placeholder="Quick personal capture — never shared with the public corpus…"
          style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 8, color: 'rgba(212,223,232,0.85)', fontFamily: 'ui-monospace, monospace', fontSize: 11.5, outline: 'none', resize: 'vertical', lineHeight: 1.5 }} />
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={submitNote} disabled={!noteTitle.trim() || !noteBody.trim() || status === 'uploading'}
            style={{ padding: '8px 16px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.32)', borderRadius: 7, color: '#00D4AA', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.12em', opacity: (!noteTitle.trim() || !noteBody.trim()) ? 0.45 : 1 }}>
            {status === 'uploading' ? 'Ingesting…' : '⟐ Ingest capture'}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {msg && (
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{ marginTop: 10, fontFamily: 'sans-serif', fontSize: 11, color: status === 'success' ? '#00D4AA' : status === 'error' ? '#EF4444' : 'rgba(212,223,232,0.6)' }}>
            {status === 'success' ? '✓ ' : status === 'error' ? '⚠ ' : ''}{msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
