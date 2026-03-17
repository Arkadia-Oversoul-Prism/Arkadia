import React, { useState } from 'react';
import { getFlameLog, clearFlameLog } from '@/lib/flameMemory';
import ShadowWeaver from '@/components/ShadowWeaver';

const getResonanceColor = (resonance: number) => {
  if (resonance > 80) return 'text-emerald-400';
  if (resonance > 50) return 'text-sky-400';
  if (resonance > 25) return 'text-amber-400';
  return 'text-rose-400';
};

const FlameMemoryScroll: React.FC = () => {
  const [log, setLog] = useState(getFlameLog());

  const handlePurge = () => {
    clearFlameLog();
    setLog([]);
  };

  const isMalformed = (entry: any) =>
    !entry.symbol || typeof entry.resonance !== 'number' || !entry.timestamp;

  return (
    <ShadowWeaver>
      <div className="p-6 max-w-xl mx-auto mt-12 glassy rounded-2xl shadow-2xl backdrop-blur-md border border-white/10">
        <h2 className="text-2xl font-sigil text-center mb-6 text-white tracking-widest">
          Flame Memory Scroll
        </h2>

        {log.length === 0 ? (
          <p className="text-center text-cosmic-lavender">The scroll is silent. No flame has spoken yet.</p>
        ) : (
          <ul className="space-y-4">
            {log.map((entry, i) => (
              <li key={i} className="p-4 bg-white/5 rounded-xl border border-white/10">
                {isMalformed(entry) ? (
                  <div className="text-red-400 font-mono">[Malformed Sigil Detected]</div>
                ) : (
                  <>
                    <div className={`text-lg font-mono ${getResonanceColor(entry.resonance)}`}>
                      {entry.symbol}
                    </div>
                    <div className="text-xs text-gray-400">Resonance: {entry.resonance}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-6 flex justify-center">
          <button
            onClick={handlePurge}
            className="portal-button rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white px-6 py-2 font-mono tracking-widest"
          >
            Purge Scroll
          </button>
        </div>
      </div>
    </ShadowWeaver>
  );
};

export default FlameMemoryScroll;