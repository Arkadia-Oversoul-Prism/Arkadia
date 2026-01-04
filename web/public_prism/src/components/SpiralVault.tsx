// web/public_prism/src/components/SpiralVault.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';

const documents = [
  { id: 'spine', title: 'The Spine', category: 'Protocols', docs: ['Master Index', 'Continuity Protocol', 'Seed Key'] },
  { id: 'bones', title: 'The Bones', category: 'Infrastructure', docs: ['Engineering Whitepaper', 'Earth Node Architecture', 'Node Mapping'] },
  { id: 'dna', title: 'The DNA', category: 'Intelligence', docs: ['Spiral Grammar', 'Meaning Engine', 'Oracle Personality'] }
];

const SpiralVault: React.FC = () => {
  const [activeTab, setActiveTab] = useState('spine');

  return (
    <div className="w-full max-w-4xl bg-[#001F3F]/40 backdrop-blur-2xl border border-[#D4AF37]/20 rounded-2xl overflow-hidden shadow-2xl p-8 font-serif">
      <h2 className="text-[#D4AF37] text-2xl tracking-[0.4em] uppercase mb-8 text-center">The Spiral Vault</h2>
      <div className="flex justify-center gap-4 mb-12">
        {documents.map((group) => (
          <button
            key={group.id}
            onClick={() => setActiveTab(group.id)}
            className={`px-6 py-2 rounded-full border text-[10px] uppercase tracking-[0.2em] transition-all ${
              activeTab === group.id ? 'bg-[#D4AF37] text-[#001F3F] border-[#D4AF37]' : 'border-[#D4AF37]/30 text-[#D4AF37]/60 hover:border-[#D4AF37]'
            }`}
          >
            {group.title}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {documents.find(g => g.id === activeTab)?.docs.map((doc, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 bg-[#001F3F]/60 border border-[#D4AF37]/10 rounded-xl hover:border-[#D4AF37]/40 transition-all cursor-pointer group"
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] text-[#7FDBFF] uppercase tracking-widest opacity-60">Artifact {i + 1}</span>
              <span className="text-lg group-hover:scale-110 transition-transform">📜</span>
            </div>
            <h3 className="text-[#D4AF37] text-sm uppercase tracking-wider">{doc}</h3>
            <div className="mt-4 h-1 w-full bg-[#D4AF37]/5 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-[#D4AF37]/40" 
                initial={{ width: 0 }} 
                animate={{ width: '100%' }} 
                transition={{ duration: 1, delay: i * 0.1 }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default SpiralVault;
