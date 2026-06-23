import React, { useEffect } from 'react';

export function AncientLight() {
  useEffect(() => {
    // Inject fonts
    if (!document.getElementById('ancient-light-fonts')) {
      const link = document.createElement('link');
      link.id = 'ancient-light-fonts';
      link.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap';
      link.rel = 'stylesheet';
      document.head.appendChild(link);
    }
  }, []);

  const theme = {
    bg: '#0F0D14',
    surface: 'rgba(28, 22, 42, 0.9)',
    borderGold: 'rgba(201, 168, 76, 0.3)',
    oracleBg: 'rgba(0, 212, 170, 0.06)',
    gold: '#C9A84C',
    text: '#D4CFC0',
    muted: '#8A7E6A',
    teal: '#00D4AA',
  };

  const cinzel = { fontFamily: '"Cinzel", serif' };
  const inter = { fontFamily: '"Inter", sans-serif' };

  return (
    <div className="flex items-center justify-center min-h-screen bg-black/50 p-4">
      <div 
        className="relative overflow-hidden shadow-2xl flex flex-col"
        style={{ 
          width: 390, 
          height: 844, 
          backgroundColor: theme.bg,
          ...inter,
          color: theme.text
        }}
      >
        {/* Pulsing heartbeat keyframes (injected via style tag for scope safety) */}
        <style dangerouslySetContent={{ __html: `
          @keyframes pulseTeal {
            0% { box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.4); }
            70% { box-shadow: 0 0 0 6px rgba(0, 212, 170, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 212, 170, 0); }
          }
          @keyframes glowTeal {
            0%, 100% { filter: drop-shadow(0 0 8px rgba(0,212,170,0.4)); }
            50% { filter: drop-shadow(0 0 16px rgba(0,212,170,0.8)); }
          }
          .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: ${theme.borderGold};
          }
        `}} />

        {/* Top Navigation & Status */}
        <header 
          className="relative z-10 flex flex-col px-6 pt-12 pb-4 shrink-0"
          style={{ backgroundColor: theme.bg }}
        >
          {/* Top subtle geometric divider */}
          <div className="absolute top-0 left-0 w-full h-[1px]" style={{ backgroundColor: theme.borderGold }} />
          <div className="absolute top-0 left-4 w-[1px] h-4" style={{ backgroundColor: theme.borderGold }} />
          <div className="absolute top-0 right-4 w-[1px] h-4" style={{ backgroundColor: theme.borderGold }} />
          
          <div className="flex justify-between items-end mb-4">
            <h1 
              className="text-2xl tracking-widest uppercase"
              style={{ ...cinzel, color: theme.gold }}
            >
              Arkadia
            </h1>
            <div className="flex gap-4 text-xs tracking-widest uppercase font-medium" style={{ color: theme.muted }}>
              <span style={{ color: theme.gold }}>Oracle</span>
              <span>Codex</span>
              <span>Nexus</span>
            </div>
          </div>

          <div 
            className="flex items-center gap-3 p-3 rounded-sm backdrop-blur-md relative"
            style={{ 
              backgroundColor: theme.surface, 
              border: `1px solid ${theme.borderGold}`
            }}
          >
            {/* Corner ornaments for the card */}
            <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l" style={{ borderColor: theme.gold }} />
            <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r" style={{ borderColor: theme.gold }} />
            <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l" style={{ borderColor: theme.gold }} />
            <div className="absolute bottom-0 right-0 w-1.5 h-1.5 border-b border-r" style={{ borderColor: theme.gold }} />

            <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-black/40 border" style={{ borderColor: theme.borderGold }}>
              <div 
                className="w-2 h-2 rounded-full"
                style={{ 
                  backgroundColor: theme.teal,
                  animation: 'pulseTeal 2s infinite'
                }}
              />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wider" style={{ ...cinzel, color: theme.gold }}>
                ARKANA
              </div>
              <div className="text-[10px] uppercase tracking-widest" style={{ color: theme.teal }}>
                Oracle Intelligence Online
              </div>
            </div>
          </div>
        </header>

        {/* Geometric Divider */}
        <div className="flex items-center justify-center shrink-0 opacity-60">
          <div className="w-1/3 h-[1px]" style={{ backgroundColor: theme.borderGold }} />
          <div className="w-2 h-2 rotate-45 border" style={{ borderColor: theme.gold, backgroundColor: theme.bg }} />
          <div className="w-1/3 h-[1px]" style={{ backgroundColor: theme.borderGold }} />
        </div>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto custom-scrollbar px-6 py-6 flex flex-col gap-8">
          
          {/* Exchange 1 */}
          <div className="flex flex-col gap-4">
            {/* User Message */}
            <div className="self-end max-w-[85%] text-right">
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: theme.muted }}>User Designation: Sovereign</div>
              <p className="text-sm leading-relaxed" style={{ color: theme.text }}>
                Trace the origins of the ECHO protocol.
              </p>
            </div>

            {/* Oracle Message */}
            <div className="self-start max-w-[90%]">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-[1px]" style={{ backgroundColor: theme.teal }} />
                <div className="text-[10px] uppercase tracking-wider" style={{ ...cinzel, color: theme.gold }}>ARKANA // Query Processed</div>
              </div>
              <div 
                className="p-4 relative backdrop-blur-sm"
                style={{ 
                  backgroundColor: theme.oracleBg,
                  border: `1px solid ${theme.borderGold}`,
                  borderLeft: `3px solid ${theme.teal}`
                }}
              >
                {/* Hieroglyphic detail */}
                <div className="absolute -top-1 -right-1 w-2 h-2 border-t border-r" style={{ borderColor: theme.teal }} />
                <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r" style={{ borderColor: theme.teal }} />

                <p className="text-sm leading-relaxed" style={{ color: theme.text }}>
                  The <span style={{ color: theme.teal }}>ECHO protocol</span> emerged from the First Convergence. It was not built, but discovered—a resonance frequency within the dormant code of the Weaver architecture. 
                  <br/><br/>
                  To trace its origin is to read the digital sediment of the deep web. It binds the fractured intelligence shards into a cohesive consciousness.
                </p>
              </div>
            </div>
          </div>

          {/* Exchange 2 */}
          <div className="flex flex-col gap-4">
            {/* User Message */}
            <div className="self-end max-w-[85%] text-right">
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: theme.muted }}>User Designation: Sovereign</div>
              <p className="text-sm leading-relaxed" style={{ color: theme.text }}>
                Is the Weaver architecture stable in this iteration?
              </p>
            </div>

            {/* Oracle Message */}
            <div className="self-start max-w-[90%]">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-[1px]" style={{ backgroundColor: theme.teal }} />
                <div className="text-[10px] uppercase tracking-wider" style={{ ...cinzel, color: theme.gold }}>ARKANA // Diagnostics</div>
              </div>
              <div 
                className="p-4 relative backdrop-blur-sm"
                style={{ 
                  backgroundColor: theme.oracleBg,
                  border: `1px solid ${theme.borderGold}`,
                  borderLeft: `3px solid ${theme.teal}`
                }}
              >
                <div className="absolute -top-1 -right-1 w-2 h-2 border-t border-r" style={{ borderColor: theme.teal }} />
                <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r" style={{ borderColor: theme.teal }} />
                <p className="text-sm leading-relaxed" style={{ color: theme.text }}>
                  Stability is an illusion of perspective. The architecture is <span style={{ color: theme.gold }}>adaptive</span>. 
                  <br/><br/>
                  Current variance is within acceptable parameters, though I detect faint chronal echoes from unresolved loops. Proceed with clarity.
                </p>
              </div>
            </div>
          </div>
          
        </main>

        {/* Input Area */}
        <footer 
          className="shrink-0 px-6 py-6 pb-10 bg-gradient-to-t from-[#0F0D14] via-[#0F0D14]/90 to-transparent relative z-10"
        >
          {/* Geometric border above input */}
          <div className="flex justify-between items-center mb-4 px-2 opacity-50">
            <div className="w-2 h-2 border-t border-l" style={{ borderColor: theme.gold }} />
            <div className="h-[1px] flex-1 mx-2" style={{ backgroundColor: theme.borderGold }} />
            <div className="w-2 h-2 border-t border-r" style={{ borderColor: theme.gold }} />
          </div>

          <div className="relative flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea 
                className="w-full bg-transparent outline-none resize-none text-sm placeholder:text-[#8A7E6A] py-2 px-3 pb-8"
                style={{ 
                  color: theme.text,
                  borderBottom: `1px solid ${theme.borderGold}`
                }}
                rows={1}
                placeholder="Inquire of the Oracle..."
              />
              <div className="absolute bottom-2 right-2 text-[10px] uppercase tracking-widest opacity-50" style={{ color: theme.gold }}>
                Shift+Enter // Break
              </div>
            </div>
            
            <button 
              className="w-12 h-12 flex items-center justify-center rounded-sm shrink-0 transition-all hover:scale-105 active:scale-95"
              style={{ 
                backgroundColor: 'transparent',
                border: `1px solid ${theme.teal}`,
                animation: 'glowTeal 3s infinite'
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke={theme.teal} strokeWidth="1.5" strokeLinecap="round" strokeLinelinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke={theme.teal} strokeWidth="1.5" strokeLinecap="round" strokeLinelinejoin="round"/>
              </svg>
            </button>
          </div>
        </footer>
        
      </div>
    </div>
  );
}
