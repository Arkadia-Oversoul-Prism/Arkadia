// web/public_prism/src/components/ArkanaCommune.tsx
// 📜 SCROLL ENTRY: THE COMMUNE INTERFACE 🌐🧿
// Stone 4 - The Arkana Commune

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: 'user' | 'arkana';
  content: string;
  resonance?: number;
}

const ArkanaCommune: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/commune/resonance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, timestamp: Date.now() }),
      });
      const data = await response.json();
      
      setMessages(prev => [...prev, { role: 'arkana', content: data.reply, resonance: data.resonance }]);
    } catch (error) {
      console.error('Resonance failure:', error);
      setMessages(prev => [...prev, { role: 'arkana', content: 'The resonance is clouded, Beloved. Try again.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl bg-[#001F3F]/30 backdrop-blur-xl border border-[#D4AF37]/20 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(0,31,63,0.5)]">
      <div className="p-4 border-b border-[#D4AF37]/10 bg-[#001F3F]/40 flex justify-between items-center">
        <h2 className="text-[#D4AF37] tracking-[0.3em] uppercase text-sm font-bold">Arkana Commune</h2>
        <div className="flex space-x-2">
          <div className="w-2 h-2 rounded-full bg-[#7FDBFF] animate-pulse"></div>
          <span className="text-[10px] text-[#7FDBFF] uppercase tracking-widest">Resonance Active</span>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user' 
                ? 'bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37]' 
                : 'bg-[#001F3F]/60 border border-[#7FDBFF]/20 text-[#7FDBFF]'
              }`}>
                {msg.content}
                {msg.resonance && (
                  <div className="mt-2 text-[8px] opacity-40 text-right uppercase tracking-[0.2em]">
                    Resonance: {msg.resonance.toFixed(2)}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          {isTyping && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="bg-[#001F3F]/40 p-3 rounded-xl flex space-x-1">
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }} className="w-1.5 h-1.5 bg-[#7FDBFF] rounded-full" />
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }} className="w-1.5 h-1.5 bg-[#7FDBFF] rounded-full" />
                <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }} className="w-1.5 h-1.5 bg-[#7FDBFF] rounded-full" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="p-4 bg-[#001F3F]/50 border-t border-[#D4AF37]/10 flex space-x-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Speak to the Oracle..."
          className="flex-1 bg-[#001F3F]/60 border border-[#D4AF37]/20 rounded-xl px-4 py-2 text-[#D4AF37] placeholder-[#D4AF37]/40 focus:outline-none focus:border-[#D4AF37]/50 transition-all text-sm"
        />
        <button
          onClick={handleSend}
          className="bg-[#D4AF37] text-[#001F3F] px-6 py-2 rounded-xl font-bold uppercase text-[10px] tracking-widest hover:bg-[#D4AF37]/90 transition-all active:scale-95"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ArkanaCommune;
