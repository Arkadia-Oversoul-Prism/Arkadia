import { useEffect, useState, useMemo } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { useSpiralResonance, type ResonanceType, type ResonanceIntensity } from '@/lib/spiralResonance';

interface SpiralResonanceVisualizerProps {
  minimized?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function generateFlamePath(intensity: ResonanceIntensity, resonanceType: ResonanceType): string {
  // Parametric SVG path generator for a flame shape
  // Intensity controls the height/amplitude of flame curves
  // ResonanceType could modulate complexity or curve sharpness
  const baseHeight = 50 + intensity * 20;
  const width = 30;
  // Example simplified parametric curve — can evolve into fractal later
  return `
    M 15 100
    C 15 ${100 - baseHeight / 2} ${width / 2} ${100 - baseHeight} 15 ${100 - baseHeight}
    C 25 ${100 - baseHeight - 15} 5 ${100 - baseHeight - 25} 15 ${100 - baseHeight - 35}
    C 20 ${100 - baseHeight - 40} 10 ${100 - baseHeight - 50} 15 ${100 - baseHeight - 55}
    C 15 30 5 70 15 100
    Z
  `;
}

export default function SpiralResonanceVisualizer({
  minimized = false,
  size = 'md'
}: SpiralResonanceVisualizerProps) {
  const frequency = useSpiralResonance(state => state.frequency);
  const resonanceHistory = useSpiralResonance(state => state.resonanceHistory);
  const resonanceType = useSpiralResonance(state => state.currentType) || 'quantum';
  const resonanceIntensity = useSpiralResonance(state => state.currentIntensity) || 3;

  const [isExpanded, setIsExpanded] = useState(!minimized);

  // Controls for flicker/breath animation synced with resonance frequency
  const controls = useAnimation();

  // Calculate flame path memoized for performance
  const flamePath = useMemo(() => generateFlamePath(resonanceIntensity, resonanceType), [resonanceIntensity, resonanceType]);

  // Color based on resonance type
  const resonanceColors: Record<ResonanceType, string> = {
    quantum: 'rgba(79, 209, 197, 0.6)',
    crystalline: 'rgba(255, 255, 255, 0.4)',
    fire: 'rgba(255, 107, 0, 0.6)',
    akashic: 'rgba(138, 43, 226, 0.5)',
    void: 'rgba(0, 0, 0, 0.3)',
    harmonic: 'rgba(255, 215, 0, 0.6)'
  };
  const flameColor = resonanceColors[resonanceType] ?? 'rgba(255,255,255,0.5)';

  // Size classes
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32'
  };

  // Animate breathing flame based on resonance frequency & intensity
  useEffect(() => {
    async function animateFlame() {
      while (true) {
        await controls.start({
          scale: 1 + 0.05 * resonanceIntensity,
          opacity: 0.7 + 0.3 * resonanceIntensity,
          transition: { duration: 1 / (frequency || 1), ease: 'easeInOut' }
        });
        await controls.start({
          scale: 1,
          opacity: 0.5,
          transition: { duration: 1 / (frequency || 1), ease: 'easeInOut' }
        });
      }
    }
    animateFlame();
  }, [controls, frequency, resonanceIntensity]);

  // Placeholder: Emit flame symbol data for faction orchestration (to be replaced)
  useEffect(() => {
    // Example: send flame shape parameters to the faction system
    // sendFlameSymbol({ path: flamePath, color: flameColor, intensity: resonanceIntensity });
  }, [flamePath, flameColor, resonanceIntensity]);

  return (
    <div className={`flex flex-col items-center justify-center ${sizeClasses[size]} relative`}>
      <motion.svg
        viewBox="0 0 30 100"
        className="origin-bottom"
        animate={controls}
        style={{ filter: 'drop-shadow(0 0 8px ' + flameColor + ')' }}
      >
        <motion.path
          d={flamePath}
          fill={flameColor}
          stroke={flameColor}
          strokeWidth={1}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 2, ease: 'easeInOut' }}
        />
      </motion.svg>

      {!minimized && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 text-blue-300 underline text-sm"
        >
          {isExpanded ? 'Collapse Flame' : 'Expand Flame'}
        </button>
      )}

      {isExpanded && !minimized && (
        <div className="mt-2 text-center text-blue-300 text-xs max-w-xs px-2 select-none">
          {/* Placeholder descriptive text for flame resonance */}
          The Nova Flame symbol shifts and breathes with your quantum resonance, guiding the Flame Factions in Arkadia towards their sacred destinies.
        </div>
      )}
    </div>
  );
}