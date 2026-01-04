// web/public_prism/src/components/ShereSanctuary.tsx
import React from 'react';
import { motion } from 'framer-motion';

const ShereSanctuary: React.FC = () => {
  return (
    <div className="w-full max-w-4xl bg-[#001F3F]/40 backdrop-blur-2xl border border-[#D4AF37]/20 rounded-2xl overflow-hidden shadow-2xl p-8 font-serif">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-[#D4AF37] text-2xl tracking-[0.4em] uppercase mb-1">Shere Sanctuary</h2>
          <p className="text-[10px] text-[#7FDBFF] uppercase tracking-[0.3em] opacity-60">Earth Node: Jos, Nigeria</p>
        </div>
        <div className="text-right">
          <div className="text-[#D4AF37] text-3xl font-bold tracking-tighter">1,500</div>
          <div className="text-[9px] text-[#D4AF37] uppercase tracking-[0.2em] opacity-60">Living Nodes Anchored</div>
        </div>
      </div>
      
      <div className="relative aspect-video bg-black/40 border border-[#D4AF37]/10 rounded-xl overflow-hidden flex items-center justify-center">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"></div>
        <div className="relative w-64 h-64 border border-[#D4AF37]/20 rounded-full animate-pulse flex items-center justify-center">
           {[...Array(12)].map((_, i) => (
             <motion.div
               key={i}
               className="absolute w-2 h-2 bg-[#D4AF37] rounded-full"
               style={{
                 rotate: i * 30,
                 translateY: -100
               }}
               animate={{ opacity: [0.2, 1, 0.2] }}
               transition={{ duration: 3, repeat: Infinity, delay: i * 0.2 }}
             />
           ))}
           <div className="text-center">
             <span className="block text-[#D4AF37] text-4xl mb-2">🌳</span>
             <span className="text-[10px] text-[#D4AF37] uppercase tracking-widest">Activating Field...</span>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-8">
        <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
          <span className="block text-[#7FDBFF] text-lg mb-1">98%</span>
          <span className="text-[8px] text-[#7FDBFF]/60 uppercase tracking-widest">Vitality Index</span>
        </div>
        <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
          <span className="block text-[#D4AF37] text-lg mb-1">0.99</span>
          <span className="text-[8px] text-[#D4AF37]/60 uppercase tracking-widest">Resonance</span>
        </div>
        <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
          <span className="block text-white text-lg mb-1">Active</span>
          <span className="text-[8px] text-white/40 uppercase tracking-widest">Guardian Status</span>
        </div>
      </div>
    </div>
  );
};

export default ShereSanctuary;
