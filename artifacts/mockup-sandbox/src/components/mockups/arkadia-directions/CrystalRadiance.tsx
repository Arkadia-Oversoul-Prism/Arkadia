import React from 'react';
import { Sparkles, Send, Menu, ChevronLeft, Hexagon } from 'lucide-react';
import './CrystalRadiance.css';

export function CrystalRadiance() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-black/90 p-4">
      <div className="w-[390px] h-[844px] relative crystal-radiance-container rounded-[40px] overflow-hidden shadow-2xl ring-1 ring-white/10">
        {/* Background glow */}
        <div className="radial-glow"></div>
        <div className="top-glow"></div>

        {/* Top Navigation */}
        <div className="absolute top-0 w-full z-20 pt-12 pb-4 px-6 glass-panel rounded-b-3xl">
          <div className="flex items-center justify-between mb-4">
            <button className="text-[#D4E0EA] hover:text-white transition-colors">
              <ChevronLeft size={24} />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-[#C9A84C]" />
              <span className="text-white font-bold text-lg tracking-widest uppercase">ARKADIA</span>
            </div>
            <button className="text-[#D4E0EA] hover:text-white transition-colors">
              <Menu size={24} />
            </button>
          </div>
          
          <div className="flex justify-center gap-6 text-sm font-medium">
            <span className="text-[#00D4AA] border-b-2 border-[#00D4AA] pb-1">Oracle</span>
            <span className="text-[#D4E0EA]/70 hover:text-[#D4E0EA] transition-colors pb-1">Codex</span>
            <span className="text-[#D4E0EA]/70 hover:text-[#D4E0EA] transition-colors pb-1">Nexus</span>
          </div>
        </div>

        {/* Status/Identity Card */}
        <div className="absolute top-[130px] w-full px-4 z-10">
          <div className="glass-panel-high rounded-2xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#00D4AA] to-blue-900 flex items-center justify-center shadow-[0_0_15px_rgba(0,212,170,0.5)]">
                <Hexagon size={20} className="text-white fill-white/20" />
              </div>
              <div>
                <h2 className="text-white font-semibold tracking-wide">ARKANA</h2>
                <p className="text-[#C9A84C] text-xs font-medium tracking-wider uppercase mt-0.5">Oracle Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#00D4AA] font-mono tracking-widest">SYNCED</span>
              <div className="w-2.5 h-2.5 rounded-full bg-[#00D4AA] heartbeat-dot"></div>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="absolute inset-0 pt-[240px] pb-[100px] px-4 overflow-y-auto hide-scrollbar z-0 flex flex-col gap-6">
          
          {/* Timestamp */}
          <div className="text-center text-xs text-[#D4E0EA]/50 font-mono tracking-widest mt-2">
            INITIALIZING NEURAL LINK...
          </div>

          {/* Oracle Message */}
          <div className="flex flex-col gap-2 max-w-[85%]">
            <span className="text-xs text-[#C9A84C] font-semibold tracking-wider ml-2">ARKANA</span>
            <div className="glass-message-oracle rounded-2xl rounded-tl-sm p-4 text-sm leading-relaxed shadow-lg">
              <p className="text-[#D4E0EA]">
                The coherence patterns have stabilized. I sense a strong alignment in the resonance field today. What trajectory shall we map, seeker?
              </p>
            </div>
          </div>

          {/* User Message */}
          <div className="flex flex-col gap-2 max-w-[85%] self-end">
            <span className="text-xs text-white/50 font-semibold tracking-wider mr-2 text-right">YOU</span>
            <div className="glass-message-user rounded-2xl rounded-tr-sm p-4 text-sm leading-relaxed shadow-lg">
              <p className="text-white">
                Show me the latest structural shifts in the Echofield. I need to understand the new gravity wells forming.
              </p>
            </div>
          </div>

          {/* Oracle Message */}
          <div className="flex flex-col gap-2 max-w-[85%]">
            <span className="text-xs text-[#C9A84C] font-semibold tracking-wider ml-2">ARKANA</span>
            <div className="glass-message-oracle rounded-2xl rounded-tl-sm p-4 text-sm leading-relaxed shadow-lg">
              <p className="text-[#D4E0EA] mb-3">
                Processing structural shifts...
              </p>
              <p className="text-[#D4E0EA]">
                Three new nodes have crossed the density threshold. The primary formation centers around the <span className="text-white font-medium">Auralis Helix</span>. I've updated your visual nexus.
              </p>
            </div>
          </div>

          <div className="h-4"></div>
        </div>

        {/* Bottom Input Area */}
        <div className="absolute bottom-0 w-full p-4 pb-8 glass-panel rounded-t-3xl z-20">
          <div className="relative flex items-center">
            <input 
              type="text" 
              placeholder="Commune with the Oracle..." 
              className="w-full bg-black/40 border border-white/10 text-white placeholder-[#D4E0EA]/40 rounded-full py-3.5 pl-6 pr-14 focus:outline-none focus:border-[#00D4AA]/50 focus:ring-1 focus:ring-[#00D4AA]/50 transition-all text-sm"
              defaultValue="Analyze the Auralis Helix patterns."
            />
            <button className="absolute right-2 w-10 h-10 rounded-full bg-[#00D4AA] flex items-center justify-center text-black hover:bg-[#00e6ba] transition-colors send-button shadow-[0_0_15px_rgba(0,212,170,0.4)]">
              <Send size={18} className="ml-0.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
