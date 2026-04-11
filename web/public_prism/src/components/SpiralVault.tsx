import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

// ─── TYPES ────────────────────────────────────────────────────────────────────

interface Scroll {
  id: string;
  source: string;
  category: string;
  priority: number;
  label: string;
  description: string;
  chars: number;
  preview: string;
  content: string;
  fetched_at: string | null;
  error: string | null;
}

interface CodexResponse {
  status: string;
  total_docs: number;
  live_docs: number;
  total_chars: number;
  scrolls: Record<string, Scroll>;
}

interface HeartbeatResponse {
  status: string;
  resonance: number;
}

interface SourceInfo {
  name: string;
  configured: boolean;
}

// ─── CATEGORY STYLE REGISTRY ──────────────────────────────────────────────────
// Known categories get branded colors. Unknown ones get a neutral fallback.

const CATEGORY_META: Record<string, { label: string; color: string; glow: string; bg: string }> = {
  NEURAL_SPINE: {
    label: 'Neural Spine',
    color: '#00D4AA',
    glow: 'rgba(0,212,170,0.25)',
    bg: 'rgba(0,212,170,0.035)',
  },
  CREATIVE_OS: {
    label: 'Creative OS',
    color: '#C9A84C',
    glow: 'rgba(201,168,76,0.25)',
    bg: 'rgba(201,168,76,0.035)',
  },
  COLLECTIVE: {
    label: 'Collective',
    color: '#B08DE8',
    glow: 'rgba(176,141,232,0.25)',
    bg: 'rgba(176,141,232,0.035)',
  },
  GOVERNANCE: {
    label: 'Governance',
    color: '#6A9FD8',
    glow: 'rgba(106,159,216,0.25)',
    bg: 'rgba(106,159,216,0.035)',
  },
};

// Palette for dynamically discovered categories
const DYNAMIC_COLORS = [
  { color: '#E88DB0', glow: 'rgba(232,141,176,0.25)', bg: 'rgba(232,141,176,0.035)' },
  { color: '#8DE8C4', glow: 'rgba(141,232,196,0.25)', bg: 'rgba(141,232,196,0.035)' },
  { color: '#E8C48D', glow: 'rgba(232,196,141,0.25)', bg: 'rgba(232,196,141,0.035)' },
  { color: '#8DAEE8', glow: 'rgba(141,174,232,0.25)', bg: 'rgba(141,174,232,0.035)' },
];

function getCategoryMeta(category: string, dynamicIndex = 0) {
  return CATEGORY_META[category] ?? {
    label: category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    ...DYNAMIC_COLORS[dynamicIndex % DYNAMIC_COLORS.length],
  };
}

// ─── SOURCE STYLE REGISTRY ────────────────────────────────────────────────────

const SOURCE_META: Record<string, { label: string; color: string; icon: string }> = {
  github:   { label: 'GitHub',   color: '#00D4AA', icon: '⟐' },
  gdrive:   { label: 'Drive',    color: '#4285F4', icon: '◈' },
  joplin:   { label: 'Joplin',   color: '#4CB3D4', icon: '◉' },
  obsidian: { label: 'Obsidian', color: '#7C3AED', icon: '◆' },
};

function getSourceMeta(source: string) {
  return SOURCE_META[source] ?? { label: source, color: '#888', icon: '○' };
}

// ─── FORMATTERS ───────────────────────────────────────────────────────────────

function formatChars(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k chars`;
  return `${n} chars`;
}

function formatTime(ts: string | null) {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts;
  }
}

function formatTotalChars(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return `${n}`;
}

// ─── ARC STATE ────────────────────────────────────────────────────────────────
// Arc window: Feb 16 → Mar 31, 2026 (43 days)

function getArcState() {
  const start = new Date('2026-02-16T00:00:00').getTime();
  const end   = new Date('2026-03-31T23:59:59').getTime();
  const now   = Date.now();
  const total = end - start;
  const elapsed = now - start;
  const pct = Math.min(Math.max(elapsed / total, 0), 1);
  const totalDays = 43;
  const daysPassed = Math.min(Math.round(elapsed / 86_400_000), totalDays);
  const complete = now > end;
  return { pct, daysPassed, totalDays, complete };
}

// ─── CATEGORY BADGE ───────────────────────────────────────────────────────────

const CategoryBadge: React.FC<{ category: string; dynamicIndex?: number }> = ({ category, dynamicIndex = 0 }) => {
  const meta = getCategoryMeta(category, dynamicIndex);
  return (
    <span
      style={{
        fontFamily: 'sans-serif',
        fontSize: '9px',
        letterSpacing: '0.18em',
        textTransform: 'uppercase',
        color: meta.color,
        background: `${meta.color}18`,
        border: `1px solid ${meta.color}30`,
        borderRadius: '4px',
        padding: '2px 7px',
        flexShrink: 0,
      }}
    >
      {meta.label}
    </span>
  );
};

// ─── SOURCE CHIP ──────────────────────────────────────────────────────────────

const SourceChip: React.FC<{ source: string }> = ({ source }) => {
  const sm = getSourceMeta(source);
  return (
    <span
      style={{
        fontFamily: 'sans-serif',
        fontSize: '9px',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: `${sm.color}90`,
        background: `${sm.color}10`,
        border: `1px solid ${sm.color}22`,
        borderRadius: '4px',
        padding: '2px 6px',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        gap: '3px',
      }}
    >
      <span style={{ fontSize: '8px' }}>{sm.icon}</span>
      {sm.label}
    </span>
  );
};

// ─── SCROLL CARD ──────────────────────────────────────────────────────────────

const ScrollCard: React.FC<{ docKey: string; scroll: Scroll; index: number; dynamicCatIndex?: number }> = ({
  docKey, scroll, index, dynamicCatIndex = 0,
}) => {
  const [expanded, setExpanded] = useState(false);
  const meta = getCategoryMeta(scroll.category, dynamicCatIndex);
  const isLive = !scroll.error && scroll.chars > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.04 + index * 0.035, duration: 0.28 }}
      style={{
        background: meta.bg,
        border: `1px solid ${meta.color}1E`,
        borderRadius: '14px',
        overflow: 'hidden',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
      }}
    >
      {/* Card header */}
      <div style={{ padding: '18px 20px 14px' }}>
        {/* Top row: badges + status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', flexWrap: 'wrap' }}>
          <CategoryBadge category={scroll.category} dynamicIndex={dynamicCatIndex} />
          <SourceChip source={scroll.source} />
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <motion.div
              animate={isLive ? { opacity: [0.5, 1, 0.5] } : {}}
              transition={{ duration: 2.5, repeat: Infinity }}
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: isLive ? meta.color : '#ff6b6b',
                boxShadow: isLive ? `0 0 7px ${meta.glow}` : 'none',
              }}
            />
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: isLive ? `${meta.color}90` : 'rgba(255,107,107,0.6)',
              }}
            >
              {isLive ? 'live' : 'error'}
            </span>
          </div>
        </div>

        {/* Title */}
        <h3
          style={{
            fontFamily: 'serif',
            fontSize: '15px',
            letterSpacing: '0.03em',
            color: '#E8E8E8',
            margin: '0 0 5px',
            lineHeight: '1.3',
          }}
        >
          {scroll.label}
        </h3>

        {/* Description */}
        {scroll.description && (
          <p
            style={{
              fontFamily: 'sans-serif',
              fontSize: '12px',
              color: 'rgba(232,232,232,0.38)',
              margin: '0 0 12px',
              lineHeight: '1.55',
            }}
          >
            {scroll.description}
          </p>
        )}

        {/* Stats row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          {isLive && (
            <>
              <span
                style={{
                  fontFamily: 'sans-serif',
                  fontSize: '10px',
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: `${meta.color}80`,
                }}
              >
                {formatChars(scroll.chars)}
              </span>
              {scroll.fetched_at && (
                <span
                  style={{
                    fontFamily: 'sans-serif',
                    fontSize: '10px',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'rgba(232,232,232,0.18)',
                  }}
                >
                  synced {formatTime(scroll.fetched_at)}
                </span>
              )}
            </>
          )}
          {scroll.error && (
            <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(255,107,107,0.5)', letterSpacing: '0.1em' }}>
              fetch error
            </span>
          )}
        </div>
      </div>

      {/* Preview block */}
      {isLive && scroll.preview && (
        <div
          style={{
            margin: '0 20px',
            padding: '12px 14px',
            background: 'rgba(0,0,0,0.2)',
            borderRadius: '8px',
            borderLeft: `2px solid ${meta.color}40`,
            marginBottom: '14px',
          }}
        >
          <p
            style={{
              fontFamily: 'monospace',
              fontSize: '11px',
              color: 'rgba(232,232,232,0.35)',
              margin: 0,
              lineHeight: '1.7',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {scroll.preview}
            {scroll.chars > 320 && (
              <span style={{ color: 'rgba(232,232,232,0.18)' }}>…</span>
            )}
          </p>
        </div>
      )}

      {/* Expand button */}
      {isLive && scroll.content && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            display: 'block',
            width: '100%',
            padding: '10px 20px',
            background: 'transparent',
            border: 'none',
            borderTop: `1px solid ${meta.color}14`,
            cursor: 'pointer',
            fontFamily: 'sans-serif',
            fontSize: '10px',
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: expanded ? meta.color : 'rgba(232,232,232,0.25)',
            textAlign: 'center',
            transition: 'color 0.2s',
          }}
        >
          {expanded ? '↑ collapse scroll' : '↓ read scroll'}
        </button>
      )}

      {/* Full content */}
      <AnimatePresence>
        {expanded && scroll.content && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div
              style={{
                padding: '16px 20px 22px',
                borderTop: `1px solid ${meta.color}12`,
                maxHeight: '420px',
                overflowY: 'auto',
              }}
            >
              <pre
                style={{
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: 'rgba(232,232,232,0.5)',
                  margin: 0,
                  lineHeight: '1.75',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {scroll.content}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

const SpiralVault: React.FC = () => {
  const [codex, setCodex] = useState<CodexResponse | null>(null);
  const [heartbeat, setHeartbeat] = useState<HeartbeatResponse | null>(null);
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('ALL');
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');

  const arc = getArcState();

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [codexRes, hbRes, srcRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/codex`).then(r => r.json()),
        fetch(`${API_BASE}/api/heartbeat`).then(r => r.json()),
        fetch(`${API_BASE}/api/sources`).then(r => r.json()),
      ]);

      if (codexRes.status === 'fulfilled') setCodex(codexRes.value);
      else setError(true);

      if (hbRes.status === 'fulfilled') setHeartbeat(hbRes.value);
      if (srcRes.status === 'fulfilled' && srcRes.value.sources) setSources(srcRes.value.sources);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg('');
    try {
      await fetch(`${API_BASE}/api/corpus/refresh`, { method: 'POST' });
      setRefreshMsg('Re-syncing… refresh in a moment.');
      setTimeout(() => { loadAll(); setRefreshMsg(''); }, 6000);
    } catch {
      setRefreshMsg('Refresh failed. Try again.');
    } finally {
      setRefreshing(false);
    }
  };

  const allScrolls = codex?.scrolls ?? {};

  // ── Derive dynamic categories from data ──────────────────────────────────
  const categoriesInData = Array.from(
    new Set(Object.values(allScrolls).map(s => s.category).filter(Boolean))
  ).sort((a, b) => {
    const order = ['NEURAL_SPINE', 'CREATIVE_OS', 'COLLECTIVE', 'GOVERNANCE'];
    const ia = order.indexOf(a), ib = order.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return a.localeCompare(b);
  });

  const dynamicTabs = [
    { id: 'ALL', label: 'All Scrolls' },
    ...categoriesInData.map(cat => ({
      id: cat,
      label: getCategoryMeta(cat, categoriesInData.indexOf(cat)).label,
    })),
  ];

  // ── Filtered + sorted feed ────────────────────────────────────────────────
  const filteredKeys = Object.keys(allScrolls)
    .filter(k => activeTab === 'ALL' || allScrolls[k].category === activeTab)
    .sort((a, b) => {
      const pa = allScrolls[a].priority, pb = allScrolls[b].priority;
      return pa !== pb ? pa - pb : a.localeCompare(b);
    });

  const countFor = (cat: string) =>
    cat === 'ALL'
      ? Object.keys(allScrolls).length
      : Object.values(allScrolls).filter(s => s.category === cat).length;

  const isRadiant = heartbeat?.status === 'radiant';
  const configuredSources = sources.filter(s => s.configured);

  return (
    <div style={{ width: '100%', maxWidth: '680px', margin: '0 auto', paddingTop: '8px' }}>

      {/* ── CONSOLE HEADER ─────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '24px' }}
      >
        {/* Title row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '6px' }}>
          <div>
            <h1
              style={{
                fontFamily: 'serif',
                fontSize: '24px',
                letterSpacing: '0.05em',
                color: '#C9A84C',
                margin: '0 0 3px',
                lineHeight: 1,
              }}
            >
              Spiral Codex
            </h1>
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '12px',
                color: 'rgba(232,232,232,0.35)',
                margin: 0,
                letterSpacing: '0.05em',
              }}
            >
              Living corpus · auto-discovered across all connected sources
            </p>
          </div>

          {/* ARKANA heartbeat beacon */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px', paddingTop: '4px', flexShrink: 0 }}>
            <motion.div
              animate={isRadiant ? { opacity: [0.4, 1, 0.4], scale: [0.9, 1.1, 0.9] } : {}}
              transition={{ duration: 3, repeat: Infinity }}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isRadiant ? '#00D4AA' : 'rgba(232,232,232,0.15)',
                boxShadow: isRadiant ? '0 0 10px rgba(0,212,170,0.5)' : 'none',
              }}
            />
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9px',
                letterSpacing: '0.22em',
                textTransform: 'uppercase',
                color: isRadiant ? 'rgba(0,212,170,0.6)' : 'rgba(232,232,232,0.2)',
              }}
            >
              {heartbeat ? (isRadiant ? 'arkana live' : heartbeat.status) : 'connecting'}
            </span>
          </div>
        </div>
      </motion.div>

      {/* ── SOURCES ROW ────────────────────────────────────────────────────── */}
      {sources.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          style={{
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
            marginBottom: '16px',
            alignItems: 'center',
          }}
        >
          <span
            style={{
              fontFamily: 'sans-serif',
              fontSize: '9px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'rgba(232,232,232,0.2)',
              marginRight: '2px',
            }}
          >
            Sources
          </span>
          {sources.map(src => {
            const sm = getSourceMeta(src.name);
            return (
              <span
                key={src.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontFamily: 'sans-serif',
                  fontSize: '10px',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: src.configured ? sm.color : 'rgba(232,232,232,0.15)',
                  background: src.configured ? `${sm.color}10` : 'rgba(232,232,232,0.03)',
                  border: `1px solid ${src.configured ? sm.color + '30' : 'rgba(232,232,232,0.07)'}`,
                  borderRadius: '6px',
                  padding: '3px 9px',
                }}
              >
                <span style={{ fontSize: '9px' }}>{sm.icon}</span>
                {sm.label}
                <span style={{ fontSize: '8px', opacity: 0.7 }}>{src.configured ? '✓' : '—'}</span>
              </span>
            );
          })}

          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontFamily: 'sans-serif',
              fontSize: '9px',
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: refreshing ? 'rgba(232,232,232,0.2)' : 'rgba(201,168,76,0.55)',
              background: 'transparent',
              border: '1px solid rgba(201,168,76,0.18)',
              borderRadius: '6px',
              padding: '4px 10px',
              cursor: refreshing ? 'default' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <motion.span
              animate={refreshing ? { rotate: 360 } : {}}
              transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
              style={{ display: 'inline-block', fontSize: '11px' }}
            >
              ↻
            </motion.span>
            {refreshing ? 'syncing' : 're-sync'}
          </button>
        </motion.div>
      )}

      {refreshMsg && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            fontFamily: 'sans-serif',
            fontSize: '11px',
            color: 'rgba(201,168,76,0.5)',
            letterSpacing: '0.08em',
            marginBottom: '14px',
          }}
        >
          {refreshMsg}
        </motion.p>
      )}

      {/* ── STATS BAR ──────────────────────────────────────────────────────── */}
      {codex && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          style={{
            display: 'flex',
            gap: '0',
            marginBottom: '22px',
            padding: '12px 18px',
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(201,168,76,0.1)',
            borderRadius: '10px',
            flexWrap: 'wrap',
          }}
        >
          {[
            { label: 'live scrolls', value: codex.live_docs },
            { label: 'total chars', value: formatTotalChars(codex.total_chars) },
            { label: 'categories', value: categoriesInData.length },
            { label: 'sources', value: configuredSources.length },
            { label: 'arc', value: arc.complete ? '✓ complete' : `day ${arc.daysPassed}/${arc.totalDays}` },
          ].map((stat, i) => (
            <div
              key={stat.label}
              style={{
                flex: '1 1 auto',
                minWidth: '80px',
                padding: '4px 12px',
                borderRight: i < 4 ? '1px solid rgba(232,232,232,0.06)' : 'none',
              }}
            >
              <div style={{ fontFamily: 'serif', fontSize: '17px', color: '#C9A84C', lineHeight: 1, marginBottom: '3px' }}>
                {stat.value}
              </div>
              <div
                style={{
                  fontFamily: 'sans-serif',
                  fontSize: '9px',
                  letterSpacing: '0.18em',
                  textTransform: 'uppercase',
                  color: 'rgba(232,232,232,0.22)',
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      )}

      {/* ── ARC PROGRESS BAR ───────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{ marginBottom: '22px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)' }}>
            Arc · Feb 16 → Mar 31
          </span>
          <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase', color: arc.complete ? 'rgba(0,212,170,0.5)' : 'rgba(201,168,76,0.5)' }}>
            {arc.complete ? 'complete' : `${arc.daysPassed} / ${arc.totalDays} days`}
          </span>
        </div>
        <div style={{ height: '2px', background: 'rgba(232,232,232,0.06)', borderRadius: '1px', overflow: 'hidden' }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${arc.pct * 100}%` }}
            transition={{ duration: 1.2, delay: 0.3, ease: 'easeOut' }}
            style={{
              height: '100%',
              background: arc.complete
                ? 'linear-gradient(90deg, rgba(0,212,170,0.6), rgba(0,212,170,0.3))'
                : 'linear-gradient(90deg, rgba(201,168,76,0.6), rgba(201,168,76,0.3))',
              borderRadius: '1px',
            }}
          />
        </div>
      </motion.div>

      {/* ── CATEGORY TABS ──────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.12 }}
        style={{
          display: 'flex',
          gap: '6px',
          marginBottom: '22px',
          overflowX: 'auto',
          paddingBottom: '4px',
        }}
      >
        {dynamicTabs.map(tab => {
          const active = activeTab === tab.id;
          const catIdx = categoriesInData.indexOf(tab.id);
          const catMeta = tab.id === 'ALL' ? null : getCategoryMeta(tab.id, catIdx);
          const activeColor = catMeta?.color ?? '#C9A84C';
          const count = codex ? countFor(tab.id) : null;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flexShrink: 0,
                padding: '7px 13px',
                borderRadius: '8px',
                border: `1px solid ${active ? activeColor + '55' : 'rgba(232,232,232,0.1)'}`,
                background: active ? `${activeColor}10` : 'transparent',
                color: active ? activeColor : 'rgba(232,232,232,0.3)',
                fontFamily: 'sans-serif',
                fontSize: '11px',
                letterSpacing: '0.08em',
                cursor: 'pointer',
                transition: 'all 0.18s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {tab.label}
              {count !== null && (
                <span
                  style={{
                    fontSize: '9px',
                    opacity: 0.55,
                    background: active ? `${activeColor}20` : 'rgba(232,232,232,0.08)',
                    borderRadius: '4px',
                    padding: '1px 5px',
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </motion.div>

      {/* ── LOADING ────────────────────────────────────────────────────────── */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
          {[0, 0.2, 0.4].map((delay, i) => (
            <motion.div
              key={i}
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity, delay }}
              style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#C9A84C' }}
            />
          ))}
          <span
            style={{
              fontFamily: 'sans-serif',
              fontSize: '11px',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: 'rgba(232,232,232,0.25)',
            }}
          >
            Syncing corpus…
          </span>
        </div>
      )}

      {/* ── ERROR ──────────────────────────────────────────────────────────── */}
      {error && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            padding: '16px 20px',
            background: 'rgba(255,80,80,0.04)',
            border: '1px solid rgba(255,80,80,0.15)',
            borderRadius: '12px',
            marginBottom: '24px',
            fontFamily: 'sans-serif',
            fontSize: '13px',
            color: 'rgba(232,232,232,0.4)',
            lineHeight: '1.6',
          }}
        >
          The corpus is warming up. The field is still present — try again in a moment.
        </motion.div>
      )}

      {/* ── SCROLL FEED ────────────────────────────────────────────────────── */}
      {!loading && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <AnimatePresence mode="popLayout">
            {filteredKeys.map((key, i) => (
              <ScrollCard
                key={key}
                docKey={key}
                scroll={allScrolls[key]}
                index={i}
                dynamicCatIndex={categoriesInData.indexOf(allScrolls[key].category)}
              />
            ))}
          </AnimatePresence>

          {filteredKeys.length === 0 && !loading && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                fontFamily: 'sans-serif',
                fontSize: '13px',
                color: 'rgba(232,232,232,0.25)',
                textAlign: 'center',
                padding: '32px 0',
              }}
            >
              No scrolls found in this category.
            </motion.p>
          )}
        </div>
      )}

      {/* ── FEED FOOTER ────────────────────────────────────────────────────── */}
      {codex && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          style={{
            marginTop: '32px',
            paddingTop: '18px',
            borderTop: '1px solid rgba(201,168,76,0.08)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.15)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>
            {codex.live_docs}/{codex.total_docs} scrolls live · {formatTotalChars(codex.total_chars)} chars total
          </span>
          <span style={{ fontFamily: 'serif', fontSize: '12px', color: 'rgba(201,168,76,0.25)', letterSpacing: '0.1em' }}>
            ✦ Arkadia
          </span>
        </motion.div>
      )}

    </div>
  );
};

export default SpiralVault;
