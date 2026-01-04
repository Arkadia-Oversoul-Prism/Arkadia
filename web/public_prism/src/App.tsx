import React from "react";
import MoonPhaseRing from "./components/MoonPhaseRing";

function App() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 transition-colors duration-1000">
      <div className="glass-mansion p-12 rounded-3xl flex flex-col items-center max-w-2xl w-full">
        <header className="text-center mb-12">
          <h1 className="text-6xl font-bold tracking-tighter mb-4 shimmer-text uppercase">
            Arkadia Public Prism
          </h1>
          <p className="text-xl italic text-sky-blue opacity-80 tracking-widest">
            Cycle 11 • The Zenith Initiation
          </p>
        </header>

        <main className="flex flex-col items-center gap-12">
          <MoonPhaseRing />
          
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mt-8">
            <div className="p-6 border border-emerald-gold/30 bg-deep-azure/50 rounded-xl text-center">
              <h3 className="text-sm uppercase tracking-widest text-sky-blue mb-2">Status</h3>
              <p className="text-2xl font-bold">RADIANT</p>
            </div>
            <div className="p-6 border border-emerald-gold/30 bg-deep-azure/50 rounded-xl text-center">
              <h3 className="text-sm uppercase tracking-widest text-sky-blue mb-2">Vector</h3>
              <p className="text-2xl font-bold">GENESIS</p>
            </div>
          </section>
        </main>

        <footer className="mt-16 text-[10px] uppercase tracking-[0.5em] opacity-40">
          𓂀 🌀 🕯️ 💎 ⚡ 🧿
        </footer>
      </div>
    </div>
  );
}

export default App;
