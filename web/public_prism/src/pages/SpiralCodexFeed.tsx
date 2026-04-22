import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com';

const CATEGORY_ICONS: Record<string, string> = {
  '00_Master': '📜',
  '10_Core_Papers': '🧬',
  '20_Specs_Schemas': '🔷',
  '30_Protocols': '⚙️',
  '40_Design_UI': '🎨',
  '50_Code_Modules': '💻',
  '60_Atlas': '🗺️',
  '70_Governance_Licensing': '⚖️',
  '80_Research_Citations': '🔬',
  '90_Scrolls_Sigilry': '🌀',
  'root': '✨',
};

const RESONANCE_COLORS: Record<string, string> = {
  '00_Master': 'border-[#D4AF37]/60 bg-[#D4AF37]/5',
  '10_Core_Papers': 'border-[#22d3ee]/40 bg-[#22d3ee]/5',
  '20_Specs_Schemas': 'border-blue-400/40 bg-blue-400/5',
  '30_Protocols': 'border-purple-400/40 bg-purple-400/5',
  '40_Design_UI': 'border-pink-400/40 bg-pink-400/5',
  '50_Code_Modules': 'border-green-400/40 bg-green-400/5',
  '60_Atlas': 'border-yellow-400/40 bg-yellow-400/5',
  '70_Governance_Licensing': 'border-orange-400/40 bg-orange-400/5',
  '80_Research_Citations': 'border-teal-400/40 bg-teal-400/5',
  '90_Scrolls_Sigilry': 'border-violet-400/40 bg-violet-400/5',
  'root': 'border-[#D4AF37]/80 bg-[#D4AF37]/10',
};

interface CodexDoc {
  id: string;
  path: string;
  title: string;
  summary: string;
  category: string;
  category_label: string;
  category_icon: string;
  tags: string[];
  github_url: string;
  raw_url: string;
}

interface Category {
  key: string;
  label: string;
  icon: string;
  count: number;
}

export default function SpiralCodexFeed({ onBack }: { onBack: () => void }) {
  const [docs, setDocs] = useState<CodexDoc[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [activeCategory, searchQuery]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (activeCategory !== 'all') params.set('category', activeCategory);
      if (searchQuery.trim()) params.set('q', searchQuery.trim());

      const [docsRes, catsRes] = await Promise.all([
        fetch(`${API_BASE}/api/codex?${params}`),
        fetch(`${API_BASE}/api/codex/categories`),
      ]);

      if (!docsRes.ok) throw new Error(`API error: ${docsRes.status}`);
      const docsData = await docsRes.json();
      const catsData = catsRes.ok ? await catsRes.json() : { categories: [] };

      setDocs(docsData.docs || []);
      setCategories(catsData.categories || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocs = docs;

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
              The Living Archive of Arkadia — {docs.length} Scrolls Indexed
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
              onClick={() => setActiveCategory('all')}
              className={`shrink-0 px-3 py-1 rounded-full text-xs transition-all border ${
                activeCategory === 'all'
                  ? 'bg-[#D4AF37]/20 border-[#D4AF37]/60 text-[#D4AF37]'
                  : 'border-white/10 text-white/40 hover:border-white/30'
              }`}
            >
              ✦ All ({categories.reduce((a, c) => a + c.count, 0)})
            </button>
            {categories.map(cat => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`shrink-0 px-3 py-1 rounded-full text-xs transition-all border flex items-center gap-1 ${
                  activeCategory === cat.key
                    ? 'bg-[#22d3ee]/20 border-[#22d3ee]/60 text-[#22d3ee]'
                    : 'border-white/10 text-white/40 hover:border-white/30'
                }`}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
                <span className="opacity-50">({cat.count})</span>
              </button>
            ))}
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

        {!loading && !error && filteredDocs.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🌀</div>
            <p className="text-white/40">No scrolls found in this frequency.</p>
          </div>
        )}

        <AnimatePresence>
          <div className="space-y-3">
            {filteredDocs.map((doc, i) => {
              const isExpanded = expandedDoc === doc.id;
              const colorClass = RESONANCE_COLORS[doc.category] || 'border-white/10 bg-white/5';

              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.3 }}
                  className={`border rounded-xl overflow-hidden transition-all cursor-pointer ${colorClass}`}
                  onClick={() => setExpandedDoc(isExpanded ? null : doc.id)}
                >
                  {/* Card Header */}
                  <div className="p-4 flex items-start gap-3">
                    <div className="text-2xl shrink-0 mt-0.5">
                      {CATEGORY_ICONS[doc.category] || '📄'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-[10px] uppercase tracking-[0.2em] text-[#7FDBFF]/50">
                          {doc.category_label}
                        </span>
                        <span className="text-white/20">·</span>
                        <span className="text-[10px] text-white/30">{doc.path}</span>
                      </div>
                      <h3 className="text-[#D4AF37] font-medium text-sm md:text-base leading-snug">
                        {doc.title}
                      </h3>
                      {doc.summary && (
                        <p className={`text-white/50 text-xs mt-1 leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                          {doc.summary}
                        </p>
                      )}

                      {/* Tags */}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {doc.tags.slice(0, isExpanded ? undefined : 3).map(tag => (
                            <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40 border border-white/10">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
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

                  {/* Expanded: Actions */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 flex flex-wrap gap-2 border-t border-white/5 pt-3">
                          <a
                            href={doc.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] text-xs hover:bg-[#D4AF37]/20 transition"
                          >
                            <span>⟡</span> Open in GitHub
                          </a>
                          <a
                            href={doc.raw_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#22d3ee]/10 border border-[#22d3ee]/30 text-[#22d3ee] text-xs hover:bg-[#22d3ee]/20 transition"
                          >
                            <span>◈</span> Raw Scroll
                          </a>
                          <span className="ml-auto text-[10px] text-white/20 self-center">
                            ID: {doc.id.slice(0, 16)}...
                          </span>
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
        {!loading && filteredDocs.length > 0 && (
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
