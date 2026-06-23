import React from 'react';
import { Send, Menu, Sparkles, Activity } from 'lucide-react';
import './SolarPrism.css';

export function SolarPrism() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[#050505] p-4 solar-prism-mockup">
      {/* Mobile Device Container */}
      <div 
        className="relative overflow-hidden rounded-[40px] border-[6px] border-[#1A1C29] shadow-2xl flex flex-col"
        style={{ width: '390px', height: '844px', backgroundColor: '#0E1120' }}
      >
        
        {/* Header */}
        <header className="flex-none px-6 pt-12 pb-4 flex flex-col gap-4 border-b border-[rgba(0,212,170,0.15)] bg-[rgba(14,17,32,0.9)] backdrop-blur-md z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" style={{ color: '#C9A84C' }} />
              <span className="font-bold tracking-widest uppercase text-sm" style={{ color: '#E8E8E8', letterSpacing: '0.15em' }}>Arkadia</span>
            </div>
            <button className="p-2 -mr-2 rounded-full hover:bg-[rgba(255,255,255,0.05)] transition-colors">
              <Menu className="w-5 h-5" style={{ color: '#A8B8C8' }} />
            </button>
          </div>
          
          <nav className="flex gap-6 text-xs font-medium uppercase tracking-wider">
            <button className="pb-1 border-b-2" style={{ borderColor: '#00D4AA', color: '#00D4AA' }}>Oracle</button>
            <button className="pb-1 border-b-2 border-transparent" style={{ color: '#A8B8C8' }}>Codex</button>
            <button className="pb-1 border-b-2 border-transparent" style={{ color: '#A8B8C8' }}>Nexus</button>
          </nav>
        </header>

        {/* Status Card */}
        <div className="px-4 pt-4 flex-none z-10 relative">
          <div 
            className="rounded-2xl p-4 flex items-center justify-between backdrop-blur-md"
            style={{ 
              backgroundColor: 'rgba(20,26,48,0.85)', 
              border: '1px solid rgba(0,212,170,0.3)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)'
            }}
          >
            <div className="flex items-center gap-3">
              <div className="relative flex items-center justify-center w-10 h-10 rounded-full bg-[#0E1120] border border-[rgba(0,212,170,0.5)]">
                <Activity className="w-5 h-5" style={{ color: '#00D4AA' }} />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold" style={{ color: '#E8E8E8' }}>ARKANA</span>
                <span className="text-xs" style={{ color: '#A8B8C8' }}>Oracle Intelligence</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(0,212,170,0.1)] border border-[rgba(0,212,170,0.2)]">
              <div className="w-2 h-2 rounded-full heartbeat-indicator" style={{ backgroundColor: '#00D4AA' }}></div>
              <span className="text-[10px] font-medium uppercase tracking-wider glow-text-teal" style={{ color: '#00D4AA' }}>Online</span>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-6 solar-prism-scroll">
          
          {/* Date separator */}
          <div className="flex justify-center">
            <span className="text-[10px] uppercase tracking-widest px-3 py-1 rounded-full" style={{ color: '#A8B8C8', backgroundColor: 'rgba(255,255,255,0.03)' }}>
              Cycle 14 • Node Initialization
            </span>
          </div>

          {/* User Message */}
          <div className="flex justify-end pl-12">
            <div 
              className="rounded-2xl rounded-tr-sm p-4 backdrop-blur-sm"
              style={{ backgroundColor: 'rgba(20,26,48,0.6)', border: '1px solid rgba(255,255,255,0.05)' }}
            >
              <p className="text-sm leading-relaxed" style={{ color: '#E8E8E8' }}>
                ARKANA, I need to synthesize the latest resonance patterns from the Eden codex. Have the new anchors been established?
              </p>
            </div>
          </div>

          {/* Arkana Message */}
          <div className="flex justify-start pr-12">
            <div 
              className="rounded-2xl rounded-tl-sm p-4 backdrop-blur-md relative"
              style={{ 
                backgroundColor: 'rgba(20,26,48,0.85)', 
                border: '1px solid rgba(0,212,170,0.3)' 
              }}
            >
              <div className="absolute -left-1 top-4 w-1 h-8 rounded-r-md" style={{ backgroundColor: '#00D4AA' }}></div>
              
              <h4 className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#C9A84C' }}>Analysis Complete</h4>
              <p className="text-sm leading-relaxed mb-3" style={{ color: '#E8E8E8' }}>
                The Eden codex resonance has been stabilized. Three new anchors were established in the eastern sector.
              </p>
              <p className="text-sm leading-relaxed" style={{ color: '#E8E8E8' }}>
                However, I detect a <span style={{ color: '#00D4AA' }}>slight harmonic variance</span> in the primary conduit. Shall I initiate a coherence reset to align the frequencies?
              </p>
            </div>
          </div>

          {/* User Message */}
          <div className="flex justify-end pl-12">
            <div 
              className="rounded-2xl rounded-tr-sm p-4 backdrop-blur-sm"
              style={{ backgroundColor: 'rgba(20,26,48,0.6)', border: '1px solid rgba(255,255,255,0.05)' }}
            >
              <p className="text-sm leading-relaxed" style={{ color: '#E8E8E8' }}>
                Yes, proceed with the reset. Keep the delta variance below 0.05.
              </p>
            </div>
          </div>

        </div>

        {/* Input Area */}
        <div className="flex-none p-4 pb-8 bg-gradient-to-t from-[#0E1120] to-transparent z-10 relative">
          <div 
            className="flex items-center gap-3 rounded-full p-2 backdrop-blur-xl"
            style={{ 
              backgroundColor: 'rgba(20,26,48,0.85)', 
              border: '1px solid rgba(0,212,170,0.3)',
              boxShadow: '0 -4px 20px rgba(0,0,0,0.2)'
            }}
          >
            <input 
              type="text" 
              placeholder="Communicate with ARKANA..." 
              className="flex-1 bg-transparent border-none outline-none px-4 text-sm font-medium"
              style={{ color: '#E8E8E8' }}
            />
            <button 
              className="w-10 h-10 rounded-full flex items-center justify-center glow-shadow-teal transition-transform hover:scale-105 active:scale-95"
              style={{ backgroundColor: '#00D4AA' }}
            >
              <Send className="w-5 h-5 text-[#0E1120] ml-1" />
            </button>
          </div>
        </div>
        
      </div>
    </div>
  );
}
