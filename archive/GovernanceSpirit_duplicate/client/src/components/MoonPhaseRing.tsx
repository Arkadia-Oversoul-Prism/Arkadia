import React from 'react';

const MoonPhaseRing: React.FC = () => {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="w-[500px] h-[500px] rounded-full border border-cyan-700/20 blur-3xl animate-pulse bg-cyan-500/10" />
    </div>
  );
};

export default MoonPhaseRing;