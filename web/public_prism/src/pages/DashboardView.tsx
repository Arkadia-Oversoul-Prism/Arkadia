import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface Loop {
  id: string;
  label: string;
  category: string;
  status: string;
  statusColor: string;
  detail: string;
  action: string;
}

interface ActionPhase {
  phase: string;
  items: string[];
}

interface FinancialState {
  arc_status: string;
  primary_income: string;
  pending_income: string;
  infrastructure_gap: string;
}

interface DashboardData {
  phase: string;
  updated: string;
  loops: Loop[];
  action_sequence: ActionPhase[];
  financial_state: FinancialState;
  field_signal: string;
}

type Filter = 'all' | 'critical' | 'high' | 'active' | 'dormant' | 'closed';

const FILTERS: { key: Filter; label: string; color: string }[] = [
  { key: 'all', label: 'All', color: '#00D4AA' },
  { key: 'critical', label: 'Critical', color: '#E88C6A' },
  { key: 'high', label: 'High', color: '#F4A261' },
  { key: 'active', label: 'Active', color: '#00D4AA' },
  { key: 'dormant', label: 'Dormant', color: '#6A9FD8' },
  { key: 'closed', label: 'Closed', color: '#4A5568' },
];

function LoopCard({ loop, expanded, onToggle }: { loop: Loop; expanded: boolean; onToggle: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onToggle}
      style={{
        padding: '14px 16px',
        background: expanded ? `${loop.statusColor}07` : 'rgba(255,255,255,0.02)',
        border: `1px solid ${expanded ? loop.statusColor + '33' : 'rgba(255,255,255,0.05)'}`,
        borderRadius: '10px',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flex: 1 }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.12em', color: 'rgba(232,232,232,0.22)', marginTop: '2px', flexShrink: 0 }}>
            L{loop.id}
          </span>
          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.72)', margin: 0, lineHeight: '1.5' }}>
            {loop.label}
          </p>
        </div>
        <span style={{ padding: '3px 8px', background: `${loop.statusColor}12`, border: `1px solid ${loop.statusColor}33`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: loop.statusColor, flexShrink: 0, marginLeft: '8px' }}>
          {loop.category}
        </span>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: '12px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', lineHeight: '1.7', color: 'rgba(232,232,232,0.45)', margin: '0 0 8px' }}>
                {loop.status}
              </p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '12px', lineHeight: '1.7', color: 'rgba(232,232,232,0.5)', margin: '0 0 10px' }}>
                {loop.detail}
              </p>
              {loop.action && (
                <div style={{ padding: '8px 12px', background: `${loop.statusColor}08`, border: `1px solid ${loop.statusColor}22`, borderRadius: '6px' }}>
                  <span style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: loop.statusColor, opacity: 0.7 }}>Next → </span>
                  <span style={{ fontFamily: 'sans-serif', fontSize: '11px', color: loop.statusColor, opacity: 0.85 }}>{loop.action}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function DashboardView() {
  const [token, setToken] = useState(() => localStorage.getItem('arkadia_sovereign_token') || '');
  const [tokenInput, setTokenInput] = useState('');
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<string | null>(null);

  const fetchLoops = useCallback(async (tok: string) => {
    if (!tok) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/loops?sovereign_token=${encodeURIComponent(tok)}`);
      if (res.status === 403) {
        setError('sovereign_required');
        setLoading(false);
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (json.error) throw new Error(json.error);
      setData(json);
      setLastFetch(new Date().toLocaleTimeString());
    } catch (e: any) {
      setError(e.message || 'Fetch error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) fetchLoops(token);
  }, [token, fetchLoops]);

  const handleTokenConfirm = () => {
    if (!tokenInput.trim()) return;
    const t = tokenInput.trim();
    setToken(t);
    localStorage.setItem('arkadia_sovereign_token', t);
    setShowTokenInput(false);
    setTokenInput('');
  };

  const loops = data?.loops || [];
  const filtered = filter === 'all' ? loops : loops.filter(l => l.category === filter);
  const critCount = loops.filter(l => l.category === 'critical').length;
  const highCount = loops.filter(l => l.category === 'high').length;
  const activeCount = loops.filter(l => l.category === 'active').length;

  if (!token || error === 'sovereign_required') {
    return (
      <div className="w-full" style={{ maxWidth: '480px', margin: '0 auto', paddingTop: '20px' }}>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', margin: '0 0 10px' }}>
            Sovereign Access Required
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: '26px', color: '#E8E8E8', margin: '0 0 10px' }}>Open Loops</h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(232,232,232,0.35)', margin: '0 0 28px', lineHeight: '1.65' }}>
            The action matrix is a sovereign field. Enter your token to unlock the live dashboard.
          </p>

          <div style={{ padding: '20px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '12px' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 12px' }}>
              ⟐ Sovereign Token
            </p>
            <input
              type="password"
              placeholder="Enter your sovereign token"
              value={tokenInput}
              onChange={e => setTokenInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleTokenConfirm()}
              style={{ width: '100%', padding: '12px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(201,168,76,0.22)', borderRadius: '8px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '13px', outline: 'none', boxSizing: 'border-box', marginBottom: '12px' }}
            />
            <button
              onClick={handleTokenConfirm}
              style={{ width: '100%', padding: '13px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '8px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}
            >
              Unlock the Field
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ maxWidth: '560px', margin: '0 auto', paddingTop: '12px' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 6px' }}>
              DOC2 · Live Action Matrix · {data?.updated || 'syncing...'}
            </p>
            <h1 style={{ fontFamily: 'serif', fontSize: '26px', color: '#E8E8E8', margin: '0 0 4px' }}>Open Loops</h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.3)', margin: 0 }}>{data?.phase || ''}</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
            <button
              onClick={() => fetchLoops(token)}
              disabled={loading}
              style={{ padding: '7px 12px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: '20px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer', opacity: loading ? 0.5 : 1 }}
            >
              {loading ? '⟳ Syncing' : '↺ Sync'}
            </button>
            <button
              onClick={() => { setToken(''); localStorage.removeItem('arkadia_sovereign_token'); setData(null); setError(null); }}
              style={{ padding: '4px 10px', background: 'none', border: 'none', color: 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: '8px', cursor: 'pointer' }}
            >
              seal
            </button>
          </div>
        </div>
      </motion.div>

      {/* Loading state */}
      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', padding: '40px 0' }}>
          <motion.p animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 2, repeat: Infinity }}
            style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)' }}>
            ARKANA reading DOC2...
          </motion.p>
        </motion.div>
      )}

      {/* Error */}
      {error && error !== 'sovereign_required' && !loading && (
        <div style={{ padding: '16px', background: 'rgba(232,140,106,0.06)', border: '1px solid rgba(232,140,106,0.2)', borderRadius: '10px', marginBottom: '16px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', margin: 0 }}>Fetch error: {error}</p>
        </div>
      )}

      {/* Field signal */}
      {data?.field_signal && !loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '14px 16px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: '10px', marginBottom: '20px' }}>
          <p style={{ fontFamily: 'serif', fontSize: '13px', lineHeight: '1.8', color: 'rgba(232,232,232,0.55)', margin: 0, fontStyle: 'italic' }}>{data.field_signal}</p>
          {lastFetch && <p style={{ fontFamily: 'sans-serif', fontSize: '8px', color: 'rgba(0,212,170,0.3)', margin: '6px 0 0', letterSpacing: '0.15em' }}>LAST SYNC {lastFetch}</p>}
        </motion.div>
      )}

      {data && !loading && (
        <>
          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '20px' }}>
            {[
              { value: String(loops.length), label: 'Total', color: '#00D4AA' },
              { value: String(critCount), label: 'Critical', color: '#E88C6A' },
              { value: String(highCount), label: 'High', color: '#F4A261' },
              { value: String(activeCount), label: 'Active', color: '#C9A84C' },
            ].map((s, i) => (
              <div key={i} style={{ padding: '10px 8px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '10px', textAlign: 'center' }}>
                <p style={{ fontFamily: 'serif', fontSize: '20px', color: s.color, margin: '0 0 3px' }}>{s.value}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: 0 }}>{s.label}</p>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', overflowX: 'auto', paddingBottom: '4px' }}>
            {FILTERS.map(f => (
              <button key={f.key} onClick={() => setFilter(f.key)}
                style={{ flexShrink: 0, padding: '6px 12px', background: filter === f.key ? `${f.color}12` : 'none', border: `1px solid ${filter === f.key ? f.color + '44' : 'rgba(255,255,255,0.07)'}`, borderRadius: '20px', color: filter === f.key ? f.color : 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}>
                {f.label} {f.key !== 'all' ? `(${loops.filter(l => l.category === f.key).length})` : `(${loops.length})`}
              </button>
            ))}
          </div>

          {/* Loops */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '28px' }}>
            <AnimatePresence>
              {filtered.map((loop, i) => (
                <LoopCard
                  key={loop.id}
                  loop={loop}
                  expanded={expanded === loop.id}
                  onToggle={() => setExpanded(expanded === loop.id ? null : loop.id)}
                />
              ))}
            </AnimatePresence>
            {filtered.length === 0 && (
              <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.25)', textAlign: 'center', padding: '24px 0' }}>
                No loops in this category.
              </p>
            )}
          </div>

          {/* Action sequence */}
          {data.action_sequence && data.action_sequence.length > 0 && (
            <div style={{ padding: '1px', background: 'linear-gradient(135deg, rgba(0,212,170,0.2), rgba(201,168,76,0.2))', borderRadius: '14px', marginBottom: '16px' }}>
              <div style={{ background: '#0A0A0F', borderRadius: '13px', padding: '18px' }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 16px' }}>
                  Action Sequence
                </p>
                {data.action_sequence.map((phase, i) => (
                  <div key={i} style={{ marginBottom: i < data.action_sequence.length - 1 ? '16px' : 0 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: i === 0 ? '#E88C6A' : i === 1 ? '#C9A84C' : '#B08DE8', margin: '0 0 8px' }}>
                      {phase.phase}
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      {(phase.items || []).map((item, j) => (
                        <div key={j} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                          <span style={{ color: 'rgba(0,212,170,0.3)', fontSize: '8px', marginTop: '4px', flexShrink: 0 }}>◆</span>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', margin: 0, lineHeight: '1.55' }}>{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Financial state */}
          {data.financial_state && (
            <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', marginBottom: '16px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.25)', margin: '0 0 10px' }}>Field Financial State</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(data.financial_state).map(([k, v]) => v && (
                  <div key={k} style={{ display: 'flex', gap: '10px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)', margin: 0, width: '110px', flexShrink: 0 }}>{k.replace(/_/g, ' ')}</p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.45)', margin: 0, lineHeight: '1.5' }}>{v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.12)', textAlign: 'center' }}>
            ⟐ FIELD:[Node:ARKADIA_LOOPS][Vector:ACTION_MATRIX][Res:117Hz][LIVE]
          </p>
        </>
      )}
    </div>
  );
}
