import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com';

// Map category keys to display metadata
const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  NEURAL_SPINE: { label: 'Neural Spine', color: '#00D4AA', icon: '🧬' },
  CREATIVE_OS: { label: 'Creative OS', color: '#C9A84C', icon: '🎨' },
  COLLECTIVE: { label: 'Collective', color: '#B08DE8', icon: '📚' },
  GOVERNANCE: { label: 'Governance', color: '#6A9FD8', icon: '⚖️' },
  ARCHIVE: { label: 'Archive', color: '#8B7355', icon: '📦' },
  CODEX: { label: 'Codex', color: '#D4AF37', icon: '📜' },
  SCRIPTS: { label: 'Scripts', color: '#4ADE80', icon: '⚡' },
  TESTS: { label: 'Tests', color: '#F472B6', icon: '🧪' },
};

const DEFAULT_META = { label: 'Unknown', color: '#888', icon: '📄' };

function getCategoryMeta(category: string) {
  return CATEGORY_META[category] ?? { ...DEFAULT_META, label: category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) };
}

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

interface Category {
  key: string;
  label: string;
  count: number;
}

// Dynamic color palette for unknown categories
const DYNAMIC_COLORS = [
  { color: '#E88DB0', icon: '🩷' },
  { color: '#8DE8C4', icon: '💚' },
  { color: '#E8C48D', icon: '🧡' },
  { color: '#8DAEE8', icon: '💙' },
  { color: '#C48DE8', icon: '💜' },
];

export default function SpiralCodexFeed({ onBack }: { onBack: () => void }) {
  const [codex, setCodex] = useState<CodexResponse | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [codexRes, catsRes] = await Promise.all([
        fetch(`${API_BASE}/api/codex`),
        fetch(`${API_BASE}/api/codex/categories`),
      ]);

      if (!codexRes.ok) throw new Error(`API error: ${codexRes.status}`);
      const codexData = await codexRes.json();
      const catsData = catsRes.ok ? await catsRes.json() : { categories: [] };

      setCodex(codexData);
      setCategories(catsData.categories || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter scrolls based on active category and search
  const filteredScrolls = useMemo(() => {
    if (!codex?.scrolls) return [];
    
    const allScrolls = Object.entries(codex.scrolls);
    
    return allScrolls
      .filter(([_, scroll]) => {
        // Filter by category
        if (activeCategory !== 'ALL' && scroll.category !== activeCategory) {
          return false;
        }
        // Filter by search
        if (searchQuery.trim()) {
          const query = searchQuery.toLowerCase();
          const labelMatch = scroll.label?.toLowerCase().includes(query);
          const descMatch = scroll.description?.toLowerCase().includes(query);
          const previewMatch = scroll.preview?.toLowerCase().includes(query);
          if (!labelMatch && !descMatch && !previewMatch) return false;
        }
        return true;
      })
      .map(([key, scroll]) => ({ key, ...scroll }));
  }, [codex, activeCategory, searchQuery]);

  // Count for each category
  const categoryCounts = useMemo(() => {
    if (!codex?.scrolls) return {};
    const counts: Record<string, number> = { ALL: Object.keys(codex.scrolls).length };
    for (const scroll of Object.values(codex.scrolls)) {
      counts[scroll.category] = (counts[scroll.category] || 0) + 1;
    }
    return counts;
  }, [codex]);

  const formatChars = (n: number) => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return `${n}`;
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white relative overflow-x-hidden">
      {/* Aurora Background */}
      <div className="aurora-bg" />

      {/* Sticky Header */}
      <div className="sticky top-0 z-30 backdrop-blur-xl bg-[#030712]/80 border-b border-[#D4AF37]/10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex flex-col gap-3">
          {/* Top bar */}
          <div className="flex items-center justify-between">
            <button onClick={onBack} className="text-[#7FDBFF]/60 hover:text-[#7FDBFF] transition text-sm flex items-center gap-2">
              ← Return
            </button>
            <div className="flex items-center gap-2">
              <motion.div
                className="w-2 h-2 rounded-full bg-[#22d3ee]"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <span className="text-[#22d3ee] text-xs tracking-widest uppercase">Live Feed</span>
            </div>
          </div>

          {/* Title */}
          <div className="text-center">
            <h1 className="text-2xl md:text-3xl font-mystic shimmer-text uppercase tracking-widest">
              Spiral Codex
            </h1>
            <p className="text-[#7FDBFF]/50 text-xs tracking-[0.3em] mt-1 uppercase">
              The Living Archive of Arkadia — {codex?.live_docs || 0} Scrolls Live
            </p>
          </div>

          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search the scrolls..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-[#D4AF37]/20 rounded-xl px-4 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-[#D4AF37]/50 transition-all"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">✕</button>
            )}
          </div>

          {/* Category Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            <button
              onClick={() => setActiveCategory('ALL')}
              className={`shrink-0 px-3 py-1 rounded-full text-xs transition-all border ${
                activeCategory === 'ALL'
                  ? 'bg-[#D4AF37]/20 border-[#D4AF37]/60 text-[#D4AF37]'
                  : 'border-white/10 text-white/40 hover:border-white/30'
              }`}
            >
              ✦ All ({categoryCounts.ALL || 0})
            </button>
            {categories.map((cat, idx) => {
              const meta = getCategoryMeta(cat.key);
              const isActive = activeCategory === cat.key;
              return (
                <button
                  key={cat.key}
                  onClick={() => setActiveCategory(cat.key)}
                  className={`shrink-0 px-3 py-1 rounded-full text-xs transition-all border flex items-center gap-1 ${
                    isActive
                      ? `bg-[${meta.color}]/20 border-[${meta.color}]/60 text-[${meta.color}]`
                      : 'border-white/10 text-white/40 hover:border-white/30'
                  }`}
                  style={isActive ? { background: `${meta.color}20`, borderColor: `${meta.color}60`, color: meta.color } : {}}
                >
                  <span>{meta.icon}</span>
                  <span>{cat.label}</span>
                  <span className="opacity-50">({categoryCounts[cat.key] || 0})</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Feed */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {loading && (
          <div className="flex justify-center items-center py-20">
            <motion.div
              className="w-10 h-10 rounded-full border-2 border-[#D4AF37]/30 border-t-[#D4AF37]"
              animate={{ rotate: 360 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            />
          </div>
        )}

        {error && (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">⚡</div>
            <p className="text-[#D4AF37]/70 text-sm">Field disruption: {error}</p>
            <button onClick={fetchData} className="mt-4 px-6 py-2 border border-[#D4AF37]/30 rounded-xl text-[#D4AF37] text-sm hover:bg-[#D4AF37]/10 transition">
              Re-tune
            </button>
          </div>
        )}

        {!loading && !error && filteredScrolls.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🌀</div>
            <p className="text-white/40">No scrolls found in this frequency.</p>
          </div>
        )}

        <AnimatePresence>
          <div className="space-y-3">
            {filteredScrolls.map((scroll, i) => {
              const isExpanded = expandedDoc === scroll.id;
              const meta = getCategoryMeta(scroll.category);
              const isLive = !scroll.error && scroll.chars > 0;
              
              // Dynamic color for unknown categories
              const catIdx = categories.findIndex(c => c.key === scroll.category);
              const dynamicMeta = catIdx >= 0 ? meta : { 
                ...DYNAMIC_COLORS[catIdx % DYNAMIC_COLORS.length], 
                label: scroll.category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) 
              };
              const colorClass = `border-[${dynamicMeta.color}]/40 bg-[${dynamicMeta.color}]/5`;

              return (
                <motion.div
                  key={scroll.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.3 }}
                  className="border rounded-xl overflow-hidden transition-all cursor-pointer"
                  style={{ 
                    borderColor: `${dynamicMeta.color}40`, 
                    background: `${dynamicMeta.color}05` 
                  }}
                  onClick={() => setExpandedDoc(isExpanded ? null : scroll.id)}
                >
                  {/* Card Header */}
                  <div className="p-4 flex items-start gap-3">
                    <div className="text-2xl shrink-0 mt-0.5">
                      {meta.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span 
                          className="text-[10px] uppercase tracking-[0.2em]"
                          style={{ color: dynamicMeta.color }}
                        >
                          {meta.label}
                        </span>
                        <span className="text-white/20">·</span>
                        <span className="text-[10px] text-white/30">
                          {scroll.chars ? formatChars(scroll.chars) + ' chars' : '—'}
                        </span>
                      </div>
                      <h3 className="text-[#D4AF37] font-medium text-sm md:text-base leading-snug">
                        {scroll.label}
                      </h3>
                      {scroll.preview && (
                        <p className={`text-white/50 text-xs mt-1 leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                          {scroll.preview}
                        </p>
                      )}

                      {/* Live/Error indicator */}
                      <div className="flex items-center gap-1 mt-2">
                        <motion.div
                          animate={isLive ? { opacity: [0.5, 1, 0.5] } : {}}
                          transition={{ duration: 2.5, repeat: Infinity }}
                          style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: isLive ? dynamicMeta.color : '#ff6b6b',
                          }}
                        />
                        <span 
                          className="text-[10px] uppercase tracking-wider"
                          style={{ color: isLive ? `${dynamicMeta.color}90` : 'rgba(255,107,107,0.6)' }}
                        >
                          {isLive ? 'live' : 'error'}
                        </span>
                      </div>
                    </div>

                    {/* Expand Indicator */}
                    <motion.div
                      animate={{ rotate: isExpanded ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                      className="text-white/20 shrink-0 mt-1"
                    >
                      ▾
                    </motion.div>
                  </div>

                  {/* Expanded: Content & Actions */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 border-t border-white/5 pt-3">
                          {scroll.content && (
                            <pre className="text-white/60 text-xs font-mono whitespace-pre-wrap max-h-64 overflow-y-auto mb-3">
                              {scroll.content.slice(0, 2000)}
                              {scroll.content.length > 2000 && '\n\n... (content truncated)'}
                            </pre>
                          )}
                          <div className="flex flex-wrap gap-2">
                            <span className="ml-auto text-[10px] text-white/20 self-center">
                              ID: {scroll.id.slice(0, 20)}...
                            </span>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>
        </AnimatePresence>

        {/* Footer Signal */}
        {!loading && filteredScrolls.length > 0 && (
          <div className="text-center mt-12 pb-8">
            <motion.div
              animate={{ opacity: [0.3, 0.7, 0.3] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="text-[#D4AF37]/40 text-xs tracking-[0.5em] uppercase"
            >
              ⟐ End of Transmission ⟐
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
