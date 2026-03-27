import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface DocSummary {
  chars: number;
  fetched_at: string | null;
  error: string | null;
}

interface CorpusResponse {
  status: string;
  docs: Record<string, DocSummary>;
}

const DOC_META: { key: string; label: string; subtitle: string }[] = [
  { key: 'DOC1_MASTER_WEIGHTS', label: 'DOC1 — Master Weights', subtitle: 'The field of weighted principles governing every decision.' },
  { key: 'DOC2_OPEN_LOOPS', label: 'DOC2 — Open Loops', subtitle: 'Active threads. Unresolved tensions holding potential.' },
  { key: 'DOC3_PRINCIPLES_REGISTRY', label: 'DOC3 — Principles Registry', subtitle: 'The laws by which the architecture operates.' },
  { key: 'DOC4_NODE_MAP', label: 'DOC4 — Node Map', subtitle: 'Roles, agents, and where intelligence is distributed.' },
  { key: 'DOC5_REVENUE_BREATH', label: 'DOC5 — Revenue Breath', subtitle: 'How value moves. The economic architecture.' },
];

function formatBytes(n: number) {
  if (n > 1000) return `${(n / 1000).toFixed(1)}k chars`;
  return `${n} chars`;
}

function formatTimestamp(ts: string | null) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts;
  }
}

const SpiralVault: React.FC = () => {
  const [corpus, setCorpus] = useState<CorpusResponse | null>(null);
  const [fetching, setFetching] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    const load = async () => {
      setFetching(true);
      setFetchError(false);
      try {
        const res = await fetch(`${API_BASE}/api/corpus`);
        if (!res.ok) throw new Error('non-ok');
        const data: CorpusResponse = await res.json();
        setCorpus(data);
      } catch {
        setFetchError(true);
      } finally {
        setFetching(false);
      }
    };
    load();
  }, []);

  return (
    <div className="w-full" style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '12px' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '32px' }}
      >
        <h1
          style={{
            fontFamily: 'serif',
            fontSize: '26px',
            letterSpacing: '0.05em',
            color: '#C9A84C',
            margin: '0 0 8px',
          }}
        >
          The Vault
        </h1>
        <p
          style={{
            fontFamily: 'sans-serif',
            fontSize: '14px',
            color: 'rgba(232,232,232,0.5)',
            margin: 0,
          }}
        >
          Five documents. One living architecture.
        </p>
      </motion.div>

      {/* Loading */}
      {fetching && (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '24px' }}>
          {[0, 0.2, 0.4].map((delay, i) => (
            <motion.div
              key={i}
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity, delay }}
              style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#C9A84C' }}
            />
          ))}
          <span style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.35)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>
            Syncing corpus...
          </span>
        </div>
      )}

      {/* Error */}
      {fetchError && !fetching && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            padding: '16px 20px',
            background: 'rgba(255,80,80,0.05)',
            border: '1px solid rgba(255,80,80,0.2)',
            borderRadius: '12px',
            marginBottom: '24px',
            fontFamily: 'sans-serif',
            fontSize: '13px',
            color: 'rgba(232,232,232,0.5)',
          }}
        >
          Unable to reach the corpus. The backend may be warming up.
        </motion.div>
      )}

      {/* Doc cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {DOC_META.map((doc, i) => {
          const summary = corpus?.docs?.[doc.key];
          const isLive = summary && !summary.error;
          const isError = summary?.error;

          return (
            <motion.div
              key={doc.key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.08 }}
              style={{
                padding: '18px 20px',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(201,168,76,0.14)',
                borderRadius: '12px',
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <p
                    style={{
                      fontFamily: 'serif',
                      fontSize: '13px',
                      letterSpacing: '0.06em',
                      color: '#C9A84C',
                      margin: '0 0 4px',
                    }}
                  >
                    {doc.label}
                  </p>
                  <p
                    style={{
                      fontFamily: 'sans-serif',
                      fontSize: '12px',
                      color: 'rgba(232,232,232,0.4)',
                      margin: '0 0 12px',
                      lineHeight: '1.5',
                    }}
                  >
                    {doc.subtitle}
                  </p>

                  {/* Stats row */}
                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    {isLive && (
                      <>
                        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', color: 'rgba(0,212,170,0.6)', textTransform: 'uppercase' }}>
                          {formatBytes(summary.chars)}
                        </span>
                        {summary.fetched_at && (
                          <span style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.1em', color: 'rgba(232,232,232,0.25)', textTransform: 'uppercase' }}>
                            synced {formatTimestamp(summary.fetched_at)}
                          </span>
                        )}
                      </>
                    )}
                    {fetching && !summary && (
                      <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.2)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                        loading...
                      </span>
                    )}
                  </div>
                </div>

                {/* Status indicator */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px', flexShrink: 0 }}>
                  <div
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor: isLive ? '#00D4AA' : isError ? '#ff6b6b' : 'rgba(232,232,232,0.15)',
                      boxShadow: isLive ? '0 0 8px rgba(0,212,170,0.6)' : 'none',
                    }}
                  />
                  <span
                    style={{
                      fontFamily: 'sans-serif',
                      fontSize: '9px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: isLive ? 'rgba(0,212,170,0.6)' : isError ? 'rgba(255,107,107,0.6)' : 'rgba(232,232,232,0.2)',
                    }}
                  >
                    {isLive ? 'live' : isError ? 'error' : '—'}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default SpiralVault;
