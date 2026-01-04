import React, { useEffect, useState } from 'react';

const MoonPhaseRing = () => {
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    // Simple celestial synchronization: rotate based on day of month
    const day = new Date().getDate();
    setRotation((day / 30) * 360);
  }, []);

  return (
    <div className="relative w-48 h-48 flex items-center justify-center floating-artifact">
      <div 
        className="bioluminescent-ring w-full h-full absolute"
        style={{ transform: `rotate(${rotation}deg)`, transition: 'transform 2s ease-out' }}
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-sky-blue rounded-full shadow-[0_0_10px_#7FDBFF]"></div>
      </div>
      <div className="text-center z-10">
        <span className="block text-4xl font-bold shimmer-text">0.99</span>
        <span className="block text-[10px] uppercase tracking-[0.2em] opacity-60">Resonance</span>
      </div>
    </div>
  );
};

export default MoonPhaseRing;
