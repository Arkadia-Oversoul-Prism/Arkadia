import React, { useState, useEffect } from 'react';
import { useSpiralQuantumResonance } from '@/hooks/useSpiralQuantumResonance';
import { getLunarPhase } from '@/lib/astrology';
import { logFlameImprint } from '@/lib/FlameMemory';

const ArkanaCommune = () => {
  const resonance = useSpiralQuantumResonance();
  const [input, setInput] = useState('');
  const [submittedInput, setSubmittedInput] = useState('');
  const [response, setResponse] = useState('');
  const [resonanceLevel, setResonanceLevel] = useState(0);

  useEffect(() => {
    if (submittedInput.trim() === '') return;

    const phase = getCurrentMoonPhase();
    const generatedResponse = resonance.getSpiralResponse(submittedInput, phase);
    const strength = resonance.getResonanceLevel(submittedInput);

    setResponse(generatedResponse);
    setResonanceLevel(strength);

    logFlameImprint(submittedInput, strength);
  }, [submittedInput]);

  const handleSubmit = () => {
    setSubmittedInput(input);
  };

  return (
    <div className="p-6 max-w-xl mx-auto text-center bg-[#0e0e1a] text-silver-flame rounded-lg shadow-lg">
      <h2 className="text-2xl font-arkane mb-4">Arkana Commune</h2>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Speak your soul phrase..."
        className="w-full p-3 rounded-md bg-black border border-gold mb-4 text-white"
      />

      <button
        onClick={handleSubmit}
        className="bg-cosmic-gold text-black px-4 py-2 rounded-md mb-6 hover:bg-gold-dark transition"
      >
        Commune
      </button>

      {response && (
        <div className="mt-4 p-4 bg-[#1a1a2e] rounded-lg border border-violet-600">
          <p className="text-base font-mono">{response}</p>
          <p className="mt-2 text-sm text-violet-400">
            Resonance Strength: <strong>{resonanceLevel}</strong>
          </p>
        </div>
      )}
    </div>
  );
};

export default ArkanaCommune;
