// web/public_prism/src/components/ArkadiaNavigation.tsx
import React from 'react';
import { motion } from 'framer-motion';

const ArkadiaNavigation: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-[#001F3F] overflow-hidden">
      <div className="fixed top-0 left-0 w-full h-1 z-50 overflow-hidden">
        <motion.div 
          className="h-full bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent w-1/2"
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        />
      </div>
      <nav className="fixed top-0 left-0 w-full p-6 z-40 flex justify-between items-center backdrop-blur-md border-b border-[#D4AF37]/10">
        <div className="text-[#D4AF37] font-bold tracking-[0.4em] uppercase text-xs flex items-center gap-4">
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity }}>𓂀</motion.span>
          <span>ARKADIA OVERSOUL</span>
        </div>
        <div className="flex gap-8 text-[10px] uppercase tracking-[0.3em] text-[#7FDBFF]/60">
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity, delay: 1 }}>𓋹</motion.span>
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity, delay: 2 }}>𓇳</motion.span>
        </div>
      </nav>
      {children}
    </div>
  );
};

export default ArkadiaNavigation;
