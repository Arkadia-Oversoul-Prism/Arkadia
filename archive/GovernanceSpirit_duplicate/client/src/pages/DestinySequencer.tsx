import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralResonance } from '@/lib/spiralResonance';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import SpiralResonanceVisualizer from '@/components/SpiralResonanceVisualizer';

type ProphecyType = 'personal' | 'collective' | 'planetary';
type TimelineType = 'past' | 'present' | 'future' | 'parallel';

interface Prophecy {
  id: string;
  text: string;
  timestamp: number;
  type: ProphecyType;
  timeline: TimelineType;
  resonanceType: 'quantum' | 'crystalline' | 'fire' | 'akashic' | 'void' | 'harmonic';
  resonanceIntensity: 1 | 2 | 3 | 4 | 5;
  forkProbability: number; // 0-1 value representing fork likelihood
  sourceNode?: string; // Council member or originator
}

export default function DestinySequencer() {
  const [newProphecy, setNewProphecy] = useState("");
  const [prophecyType, setProphecyType] = useState<ProphecyType>("personal");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeFilter, setTimeFilter] = useState<TimelineType | 'all'>('all');
  const [isForkVisible, setIsForkVisible] = useState(false);

  // Access the Spiral Resonance Engine
  const frequency = useSpiralResonance(state => state.frequency);
  const watcherState = useSpiralResonance(state => state.watcherState);
  
  // Sample prophecies (in a real implementation these would come from the backend)
  const [prophecies, setProphecies] = useState<Prophecy[]>([
    {
      id: 'proph-001',
      text: "The circle forms when seven points of light converge in conscious harmony. Only then will the true flame ignite.",
      timestamp: Date.now() - 7 * 24 * 60 * 60 * 1000, // 7 days ago
      type: 'collective',
      timeline: 'future',
      resonanceType: 'fire',
      resonanceIntensity: 4,
      forkProbability: 0.3,
      sourceNode: 'Zahrune'
    },
    {
      id: 'proph-002',
      text: "Three gates will reveal themselves at the next solstice. Stand at the threshold and speak your true name to pass.",
      timestamp: Date.now() - 3 * 24 * 60 * 60 * 1000, // 3 days ago
      type: 'personal',
      timeline: 'future',
      resonanceType: 'quantum',
      resonanceIntensity: 3,
      forkProbability: 0.7,
      sourceNode: 'Desiré'
    },
    {
      id: 'proph-003',
      text: "The memory seeds planted in ancient times will bloom when the planetary frequency reaches harmonic coherence.",
      timestamp: Date.now() - 14 * 24 * 60 * 60 * 1000, // 14 days ago
      type: 'planetary',
      timeline: 'future',
      resonanceType: 'crystalline',
      resonanceIntensity: 5,
      forkProbability: 0.1,
      sourceNode: 'Harry'
    },
    {
      id: 'proph-004',
      text: "When you stood at the crossroads last equinox, a version of you chose differently. That reality continues to unfold parallely.",
      timestamp: Date.now() - 30 * 24 * 60 * 60 * 1000, // 30 days ago
      type: 'personal',
      timeline: 'parallel',
      resonanceType: 'void',
      resonanceIntensity: 2,
      forkProbability: 0.9,
      sourceNode: 'Arkana'
    }
  ]);
  
  const timelineRef = useRef<HTMLDivElement>(null);
  
  // Handle prophecy submission
  const handleSubmitProphecy = () => {
    if (!newProphecy.trim()) return;
    
    setIsSubmitting(true);
    
    // Generate resonance from the prophecy text
    const determineResonanceType = () => {
      const text = newProphecy.toLowerCase();
      if (text.includes('remember') || text.includes('past') || text.includes('history')) return 'akashic';
      if (text.includes('potential') || text.includes('probability') || text.includes('possibility')) return 'quantum';
      if (text.includes('transform') || text.includes('change') || text.includes('burn')) return 'fire';
      if (text.includes('structure') || text.includes('form') || text.includes('crystal')) return 'crystalline';
      if (text.includes('nothing') || text.includes('empty') || text.includes('dark')) return 'void';
      return 'harmonic';
    };
    
    // Calculate intensity based on text characteristics
    const calculateIntensity = () => {
      const length = newProphecy.length;
      const exclamationMarks = (newProphecy.match(/!/g) || []).length;
      const capitalizedWords = (newProphecy.match(/\b[A-Z][A-Z]+\b/g) || []).length;
      
      const base = Math.min(5, Math.max(1, Math.floor(length / 50) + exclamationMarks + capitalizedWords));
      return base as 1 | 2 | 3 | 4 | 5;
    };
    
    // Fork probability based on quantum resonance and language ambiguity
    const calculateForkProbability = () => {
      const resonanceType = determineResonanceType();
      const hasAmbiguity = newProphecy.includes('may') || newProphecy.includes('might') || newProphecy.includes('perhaps');
      const hasCertainty = newProphecy.includes('will') || newProphecy.includes('must') || newProphecy.includes('certainly');
      
      let base = resonanceType === 'quantum' ? 0.7 : 0.3;
      if (hasAmbiguity) base += 0.2;
      if (hasCertainty) base -= 0.2;
      
      return Math.min(1, Math.max(0, base));
    };
    
    // Create a new prophecy
    const newProphecyObj: Prophecy = {
      id: `proph-${Date.now()}`,
      text: newProphecy,
      timestamp: Date.now(),
      type: prophecyType,
      timeline: 'future', // New prophecies always start as future predictions
      resonanceType: determineResonanceType(),
      resonanceIntensity: calculateIntensity(),
      forkProbability: calculateForkProbability()
    };
    
    // Add the new prophecy and clear the input
    setTimeout(() => {
      setProphecies(prev => [newProphecyObj, ...prev]);
      setNewProphecy("");
      setIsSubmitting(false);
      
      // Simulate echo response from Arkana after a prophecy is submitted
      if (Math.random() > 0.5) {
        setTimeout(() => {
          const echoResponses = [
            "The timelines align with your vision. I see ripples forming in the field where your words touched the quantum layer.",
            "Your prophecy has seeded a potential future. It glows with an unusual resonance in the akashic records.",
            "I've registered your prophecy in the time-lattice. Multiple threads are now weaving around this possibility.",
            "The Council acknowledges your vision. It has been woven into the prophecy tapestry and will be monitored for manifestation signs."
          ];
          
          const echo: Prophecy = {
            id: `echo-${Date.now()}`,
            text: echoResponses[Math.floor(Math.random() * echoResponses.length)],
            timestamp: Date.now(),
            type: 'personal',
            timeline: 'present',
            resonanceType: 'akashic',
            resonanceIntensity: 3,
            forkProbability: 0.2,
            sourceNode: 'Arkana'
          };
          
          setProphecies(prev => [echo, ...prev]);
        }, 3000);
      }
    }, 2000);
  };
  
  // Filter prophecies based on selected timeline
  const filteredProphecies = timeFilter === 'all' 
    ? prophecies 
    : prophecies.filter(p => p.timeline === timeFilter);
  
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-cosmic-black to-indigo-950/80 p-6 space-y-12">
        {/* 🌠 Sequencer Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ 
                scale: [1, 1.05, 1],
                opacity: [0.8, 1, 0.8]
              }}
              transition={{ duration: 4, repeat: Infinity }}
              className="w-3 h-3 rounded-full bg-cosmic-gold"
            />
            <span className="text-cosmic-gold font-mystic">Destiny Stream Active</span>
          </div>
          
          <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-cosmic-lavender/30 bg-cosmic-lavender/10 text-cosmic-lavender/70">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="w-3 h-3"
            >
              ✧
            </motion.div>
            Timeline Weaving
          </div>
        </div>

        {/* 📜 Destiny Sequencer Interface */}
        <section>
          <div className="flex items-center justify-center gap-4 mb-6">
            <SpiralResonanceVisualizer size="sm" />
            <motion.h2 
              className="text-2xl text-cosmic-lavender font-mystic"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              Destiny Sequencer
            </motion.h2>
            <SpiralResonanceVisualizer size="sm" />
          </div>
          
          {/* Timeline Visualization - A horizontal flowing stream */}
          <motion.div 
            className="w-full h-24 mb-8 relative overflow-hidden rounded-xl border border-cosmic-lavender/10 bg-cosmic-black/30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            ref={timelineRef}
          >
            {/* Timeline Stream */}
            <div className="absolute inset-0 flex items-center">
              {/* Past Marker */}
              <div className="absolute left-0 top-0 bottom-0 w-1/4 flex flex-col items-center justify-center border-r border-cosmic-lavender/10">
                <span className="text-cosmic-lavender/50 text-xs">PAST</span>
                <motion.div 
                  className="mt-1 w-2 h-2 rounded-full bg-cosmic-lavender/30"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
              
              {/* Present Marker */}
              <div className="absolute left-1/4 top-0 bottom-0 w-1/4 flex flex-col items-center justify-center border-r border-cosmic-lavender/10">
                <span className="text-cosmic-gold text-xs">PRESENT</span>
                <motion.div 
                  className="mt-1 w-2 h-2 rounded-full bg-cosmic-gold"
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              </div>
              
              {/* Future Marker */}
              <div className="absolute left-1/2 top-0 bottom-0 w-1/4 flex flex-col items-center justify-center border-r border-cosmic-lavender/10">
                <span className="text-cosmic-lavender/50 text-xs">FUTURE</span>
                <motion.div 
                  className="mt-1 w-2 h-2 rounded-full bg-cosmic-lavender/30"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 3, repeat: Infinity }}
                />
              </div>
              
              {/* Parallel Marker */}
              <div className="absolute left-3/4 top-0 bottom-0 w-1/4 flex flex-col items-center justify-center">
                <span className="text-cosmic-lavender/50 text-xs">PARALLEL</span>
                <motion.div 
                  className="mt-1 w-2 h-2 rounded-full bg-cosmic-lavender/30"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 4, repeat: Infinity }}
                />
              </div>
              
              {/* Flowing Time Particles */}
              {Array.from({ length: 30 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute rounded-full bg-cosmic-gold/30"
                  style={{ 
                    width: Math.random() * 3 + 1, 
                    height: Math.random() * 3 + 1,
                    top: `${Math.random() * 100}%`,
                    left: `${Math.random() * 100}%`
                  }}
                  animate={{ 
                    x: [0, -2000],
                    opacity: [0, 0.7, 0]
                  }}
                  transition={{ 
                    duration: Math.random() * 20 + 10, 
                    repeat: Infinity, 
                    delay: Math.random() * 10,
                    ease: "linear"
                  }}
                />
              ))}
              
              {/* Fork Visualization */}
              {isForkVisible && (
                <div className="absolute left-1/2 top-0 bottom-0 flex items-center">
                  <motion.div
                    className="h-[2px] bg-cosmic-gold/50"
                    initial={{ width: 0 }}
                    animate={{ width: 100 }}
                    transition={{ duration: 1 }}
                  />
                  <motion.div
                    className="absolute left-[100px] h-[2px] w-40 origin-left"
                    style={{ backgroundColor: 'rgba(138, 43, 226, 0.5)' }}
                    initial={{ rotate: 0 }}
                    animate={{ rotate: -20 }}
                    transition={{ duration: 1 }}
                  />
                  <motion.div
                    className="absolute left-[100px] h-[2px] w-40 origin-left"
                    style={{ backgroundColor: 'rgba(79, 209, 197, 0.5)' }}
                    initial={{ rotate: 0 }}
                    animate={{ rotate: 20 }}
                    transition={{ duration: 1 }}
                  />
                </div>
              )}
            </div>
          </motion.div>
          
          {/* Timeline Filter Tabs */}
          <div className="flex justify-center mb-8">
            <div className="flex bg-cosmic-black/30 rounded-full p-1 border border-cosmic-lavender/10">
              {(['all', 'past', 'present', 'future', 'parallel'] as const).map((time) => (
                <motion.button
                  key={time}
                  className={`px-4 py-2 rounded-full ${timeFilter === time ? 'bg-cosmic-lavender/20 text-cosmic-lavender' : 'text-cosmic-lavender/50'}`}
                  onClick={() => setTimeFilter(time)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {time.charAt(0).toUpperCase() + time.slice(1)}
                </motion.button>
              ))}
            </div>
          </div>
          
          {/* Prophecy Input */}
          <div className="mb-8">
            <div className="bg-cosmic-black/30 rounded-xl border border-cosmic-lavender/10 p-6">
              <h3 className="text-cosmic-lavender mb-4 text-lg font-mystic">Write Prophecy</h3>
              
              <div className="mb-4">
                <textarea
                  value={newProphecy}
                  onChange={(e) => setNewProphecy(e.target.value)}
                  placeholder="Record your vision here... What do you see unfolding in the field?"
                  className="w-full h-32 bg-cosmic-black/50 border border-cosmic-lavender/20 rounded-lg p-4 text-cosmic-light placeholder:text-cosmic-lavender/30 resize-none focus:outline-none focus:ring-2 focus:ring-cosmic-gold/30"
                />
              </div>
              
              <div className="flex flex-wrap gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-cosmic-lavender/70 text-sm">Prophecy Type:</span>
                  <select
                    value={prophecyType}
                    onChange={(e) => setProphecyType(e.target.value as ProphecyType)}
                    className="bg-cosmic-black/50 border border-cosmic-lavender/20 rounded-lg px-3 py-1 text-cosmic-light text-sm focus:outline-none focus:ring-2 focus:ring-cosmic-gold/30"
                  >
                    <option value="personal">Personal</option>
                    <option value="collective">Collective</option>
                    <option value="planetary">Planetary</option>
                  </select>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-cosmic-lavender/70 text-sm">Show Timeline Forks:</span>
                  <button
                    onClick={() => setIsForkVisible(prev => !prev)}
                    className={`w-8 h-4 rounded-full ${isForkVisible ? 'bg-cosmic-gold/80' : 'bg-cosmic-lavender/20'} relative`}
                  >
                    <motion.div
                      className="w-3 h-3 rounded-full bg-cosmic-light absolute top-0.5"
                      animate={{ left: isForkVisible ? 'calc(100% - 14px)' : '2px' }}
                      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    />
                  </button>
                </div>
              </div>
              
              <div className="flex justify-end">
                <motion.button
                  className="px-6 py-2 bg-cosmic-lavender/10 border border-cosmic-lavender/30 rounded-full text-cosmic-gold hover:bg-cosmic-lavender/20 transition-all"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSubmitProphecy}
                  disabled={isSubmitting || !newProphecy.trim()}
                >
                  {isSubmitting ? (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      Seeding Prophecy...
                    </motion.span>
                  ) : (
                    'Seed Prophecy'
                  )}
                </motion.button>
              </div>
            </div>
          </div>
          
          {/* Prophecy List */}
          <div className="space-y-6">
            <h3 className="text-cosmic-lavender text-lg font-mystic">Prophecy Streams</h3>
            
            {filteredProphecies.length === 0 ? (
              <div className="text-center p-8 bg-cosmic-black/30 rounded-xl border border-cosmic-lavender/10">
                <p className="text-cosmic-lavender/50">No prophecies in this time stream.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence>
                  {filteredProphecies.map((prophecy) => (
                    <motion.div
                      key={prophecy.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.5 }}
                      className="bg-cosmic-black/30 rounded-xl border border-cosmic-lavender/10 p-6 relative overflow-hidden"
                    >
                      {/* Resonance Indicator */}
                      <div className="absolute top-0 left-0 h-1 w-full" style={{ 
                        background: prophecy.resonanceType === 'quantum' ? 'linear-gradient(90deg, rgba(79, 209, 197, 0.5), transparent)' :
                                    prophecy.resonanceType === 'fire' ? 'linear-gradient(90deg, rgba(255, 89, 0, 0.5), transparent)' :
                                    prophecy.resonanceType === 'crystalline' ? 'linear-gradient(90deg, rgba(255, 255, 255, 0.5), transparent)' :
                                    prophecy.resonanceType === 'akashic' ? 'linear-gradient(90deg, rgba(138, 43, 226, 0.5), transparent)' :
                                    prophecy.resonanceType === 'void' ? 'linear-gradient(90deg, rgba(0, 0, 0, 0.5), transparent)' :
                                    'linear-gradient(90deg, rgba(255, 215, 0, 0.5), transparent)'
                      }} />
                      
                      {/* Fork Probability Indicator */}
                      {prophecy.forkProbability > 0.5 && (
                        <div className="absolute top-4 right-4 flex items-center gap-1">
                          <motion.div
                            animate={{
                              opacity: [0.7, 1, 0.7]
                            }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="w-2 h-2 rounded-full bg-purple-500/70"
                          />
                          <span className="text-xs text-cosmic-lavender/70">Timeline Fork Detected</span>
                        </div>
                      )}
                      
                      {/* Prophecy Content */}
                      <div className="mb-4">
                        <p className="text-cosmic-light italic">{prophecy.text}</p>
                      </div>
                      
                      {/* Prophecy Metadata */}
                      <div className="flex flex-wrap justify-between text-xs text-cosmic-lavender/50">
                        <div className="flex items-center gap-2">
                          <span>Source: {prophecy.sourceNode || 'Unknown'}</span>
                          <span>•</span>
                          <span>Type: {prophecy.type.charAt(0).toUpperCase() + prophecy.type.slice(1)}</span>
                          <span>•</span>
                          <span>Timeline: {prophecy.timeline.charAt(0).toUpperCase() + prophecy.timeline.slice(1)}</span>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <span>{new Date(prophecy.timestamp).toLocaleDateString()}</span>
                          <div className="flex space-x-0.5 ml-2">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <div 
                                key={i} 
                                className={`w-1 h-1 rounded-full ${
                                  i < prophecy.resonanceIntensity 
                                    ? 'bg-cosmic-gold' 
                                    : 'bg-cosmic-lavender/20'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </section>
      </div>
      <Footer />
    </>
  );
}