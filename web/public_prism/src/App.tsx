import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LivingGate from "./pages/LivingGate";
import MoonPhaseRing from "./components/MoonPhaseRing";

function Home() {
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
          <div className="mt-8 flex gap-4">
            <a href="/gate" className="px-8 py-3 bg-emerald-gold/10 border border-emerald-gold/40 rounded-full text-emerald-gold hover:bg-emerald-gold/20 transition-all">
              Enter the Living Gate
            </a>
          </div>
        </main>

        <footer className="mt-16 text-[10px] uppercase tracking-[0.5em] opacity-40">
          𓂀 🌀 🕯️ 💎 ⚡ 🧿
        </footer>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/gate" element={<LivingGate />} />
      </Routes>
    </Router>
  );
}

export default App;
