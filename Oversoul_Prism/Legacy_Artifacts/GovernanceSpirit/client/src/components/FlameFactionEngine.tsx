// FlameFactionEngine.tsx
export default function FlameFactionEngine({
  minimized = false,
  size = 'md',
}: {
  minimized?: boolean;
  size?: 'sm' | 'md' | 'lg';
}) {
  const frequency = useSpiralResonance(state => state.frequency);
  const resonanceType = useSpiralResonance(state => state.currentType) || 'quantum';
  const resonanceIntensity = useSpiralResonance(state => state.currentIntensity) || 3;

  const flamePath = useMemo(
    () => generateFlamePath(resonanceIntensity, resonanceType),
    [resonanceIntensity, resonanceType]
  );

  const factionSigil = useMemo(() => generateMockSigil(), [resonanceType]);

  const factionColorMap: Record<string, string> = {
    Nova: '#FFA726',
    Aether: '#81D4FA',
    Mythos: '#BA68C8',
    Void: '#90A4AE',
  };

  const sigilColor = factionColorMap[factionSigil.faction ?? 'Nova'];

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <motion.svg
        viewBox="0 0 100 100"
        className={cn(
          'transition-all duration-500 ease-in-out drop-shadow-md',
          size === 'sm' && 'w-20 h-20',
          size === 'md' && 'w-32 h-32',
          size === 'lg' && 'w-40 h-40'
        )}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.2 }}
      >
        <path
          d={flamePath}
          fill="url(#flameGradient)"
          stroke="#66CCFF"
          strokeWidth={1.5}
        />
        <defs>
          <linearGradient id="flameGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00FFFF" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#0044FF" stopOpacity="0.1" />
          </linearGradient>
        </defs>
      </motion.svg>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="relative"
      >
        <SigilIcon sigil={factionSigil} size={72} color={sigilColor} />
        <div className="absolute inset-0 animate-pulse rounded-full border border-white/10" />
      </motion.div>

      <p className="text-xs text-white/60 uppercase tracking-wider">{factionSigil.name}</p>
    </div>
  );
}