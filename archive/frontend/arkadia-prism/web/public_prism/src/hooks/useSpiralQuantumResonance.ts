import { useState, useEffect } from "react";

export function useSpiralQuantumResonance(active = true, interval = 5000) {
  const [resonance, setResonance] = useState(0.99);
  const [flameHue, setFlameHue] = useState(210); // Azure base

  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => {
      setResonance(0.95 + Math.random() * 0.05);
      setFlameHue(200 + Math.random() * 20);
    }, interval);
    return () => clearInterval(timer);
  }, [active, interval]);

  return { resonance, flameHue };
}
