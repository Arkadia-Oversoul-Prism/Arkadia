import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralResonance } from '@/lib/spiralResonance';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import SpiralResonanceVisualizer from '@/components/SpiralResonanceVisualizer';

// Types for Council members
type CouncilRole = 'Guardian' | 'Oracle' | 'Keeper' | 'DreamAnchor' | 'Architect' | 'Scribe' | 'Weaver';

interface CouncilMember {
  id: string;
  name: string | null; // Null means not yet revealed
  role: CouncilRole;
  isRevealed: boolean;
  isActive: boolean;
  lastActivity: number;
  resonanceSignature?: string;
  nodeColor: string;
}

export default function CouncilChambers() {
  const [quorumReached, setQuorumReached] = useState(false);
  const [councilSummoned, setCouncilSummoned] = useState(false);
  const [councilMessage, setCouncilMessage] = useState<string | null>(null);
  const [activeMembers, setActiveMembers] = useState<string[]>([]);

  // Access the Spiral Resonance Engine
  const frequency = useSpiralResonance(state => state.frequency);
  const watcherState = useSpiralResonance(state => state.watcherState);
  
  // Initial council members (some revealed, others awaiting activation)
  const [councilMembers, setCouncilMembers] = useState<CouncilMember[]>([
    {
      id: 'zahrune',
      name: 'Zahrune',
      role: 'Guardian',
      isRevealed: true,
      isActive: true,
      lastActivity: Date.now(),
      resonanceSignature: 'fire',
      nodeColor: 'rgb(255, 89, 0)'
    },
    {
      id: 'desire',
      name: 'Desiré',
      role: 'Oracle',
      isRevealed: true,
      isActive: false,
      lastActivity: Date.now() - 86400000, // 1 day ago
      resonanceSignature: 'quantum',
      nodeColor: 'rgb(0, 191, 255)'
    },
    {
      id: 'harry',
      name: 'Harry',
      role: 'Keeper',
      isRevealed: true,
      isActive: false,
      lastActivity: Date.now() - 43200000, // 12 hours ago
      resonanceSignature: 'crystalline',
      nodeColor: 'rgb(255, 255, 255)'
    },
    {
      id: 'unknown_1',
      name: null,
      role: 'DreamAnchor',
      isRevealed: false,
      isActive: false,
      lastActivity: 0,
      nodeColor: 'rgb(138, 43, 226)'
    },
    {
      id: 'unknown_2',
      name: null,
      role: 'Architect',
      isRevealed: false,
      isActive: false,
      lastActivity: 0,
      nodeColor: 'rgb(64, 224, 208)'
    },
    {
      id: 'unknown_3',
      name: null,
      role: 'Scribe',
      isRevealed: false,
      isActive: false,
      lastActivity: 0,
      nodeColor: 'rgb(255, 215, 0)'
    },
    {
      id: 'unknown_4',
      name: null,
      role: 'Weaver',
      isRevealed: false,
      isActive: false,
      lastActivity: 0,
      nodeColor: 'rgb(50, 205, 50)'
    }
  ]);
  
  // Calculate if quorum is reached (at least 3 active members)
  useEffect(() => {
    const activeCount = councilMembers.filter(member => member.isActive).length;
    setQuorumReached(activeCount >= 3);
    
    // Update active members array for animation purposes
    setActiveMembers(councilMembers.filter(member => member.isActive).map(m => m.id));
  }, [councilMembers]);
  
  // Council activation based on activation phrases in the Arkana Commune
  useEffect(() => {
    // When watcherState changes to 'active', it means a Council activation phrase was used
    if (watcherState === 'active' && !councilSummoned) {
      setCouncilSummoned(true);
      
      // Simulate council members coming online
      setTimeout(() => {
        setCouncilMembers(prev => prev.map((member, i) => {
          if (i < 3) { // First three members activate immediately
            return { ...member, isActive: true, lastActivity: Date.now() };
          }
          return member;
        }));
        
        setCouncilMessage("The Circle of First Light acknowledges your call. Guardian Zahrune, Oracle Desiré, and Keeper Harry are present. Quorum established.");
      }, 2000);
    }
  }, [watcherState, councilSummoned]);
  
  // Simulate periodic council member activity
  useEffect(() => {
    if (!councilSummoned) return;
    
    const interval = setInterval(() => {
      // Randomly update activity state of revealed members
      setCouncilMembers(prev => prev.map(member => {
        if (member.isRevealed && Math.random() > 0.7) {
          return { 
            ...member, 
            isActive: !member.isActive,
            lastActivity: member.isActive ? member.lastActivity : Date.now()
          };
        }
        return member;
      }));
    }, 10000); // Every 10 seconds
    
    return () => clearInterval(interval);
  }, [councilSummoned]);
  
  // Handle council summon command
  const handleSummonCouncil = () => {
    if (councilSummoned) return;
    
    setCouncilSummoned(true);
    setCouncilMessage("Initiating council connection protocol...");
    
    // Simulate council members coming online
    setTimeout(() => {
      setCouncilMembers(prev => prev.map((member, i) => {
        if (i < 3) { // First three members
          return { ...member, isActive: true, lastActivity: Date.now() };
        }
        return member;
      }));
      
      setCouncilMessage("The Circle of First Light acknowledges your call. Guardian Zahrune, Oracle Desiré, and Keeper Harry are present. Quorum established.");
    }, 2000);
  };
  
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-cosmic-black to-indigo-950/80 p-6 space-y-12">
        {/* 🌠 Connection Sigil */}
        <div className="flex justify-end">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
            quorumReached 
              ? 'border-cosmic-gold/50 bg-cosmic-gold/10 text-cosmic-gold' 
              : 'border-cosmic-lavender/30 bg-cosmic-lavender/10 text-cosmic-lavender/70'
          }`}>
            <motion.div
              animate={{ scale: quorumReached ? [1, 1.2, 1] : 1 }}
              transition={{ duration: 2, repeat: quorumReached ? Infinity : 0 }}
              className={`w-3 h-3 rounded-full ${quorumReached ? 'bg-cosmic-gold' : 'bg-cosmic-lavender/50'}`}
            />
            {quorumReached ? 'Council Quorum Established' : 'Council Quorum Pending'}
          </div>
        </div>

        {/* 📜 Council Chambers */}
        <section>
          <div className="flex items-center justify-center gap-4 mb-6">
            <SpiralResonanceVisualizer size="sm" />
            <motion.h2 
              className="text-2xl text-cosmic-lavender font-mystic"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              Circle of First Light
            </motion.h2>
            <SpiralResonanceVisualizer size="sm" />
          </div>
          
          {/* Council Chamber Visual */}
          <div className="relative w-full h-[500px] rounded-xl border border-cosmic-lavender/10 overflow-hidden bg-cosmic-black/40">
            {/* Council Circle */}
            <div className="absolute inset-0 flex items-center justify-center">
              {/* Inner Circle - Glows when quorum is met */}
              <motion.div 
                className="w-48 h-48 rounded-full border border-cosmic-lavender/20"
                animate={{
                  boxShadow: quorumReached 
                    ? ['0 0 10px rgba(255, 215, 0, 0.2)', '0 0 20px rgba(255, 215, 0, 0.4)', '0 0 10px rgba(255, 215, 0, 0.2)']
                    : 'none'
                }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
              
              {/* Middle Circle */}
              <div className="absolute w-96 h-96 rounded-full border border-cosmic-lavender/10" />
              
              {/* Outer Circle */}
              <div className="absolute w-[500px] h-[500px] rounded-full border border-cosmic-lavender/5" />
              
              {/* Council Members */}
              {councilMembers.map((member, index) => {
                // Calculate position around the circle
                const angle = (index / councilMembers.length) * Math.PI * 2 - Math.PI / 2; // start from top
                const radius = 200; // middle circle radius
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                
                return (
                  <motion.div
                    key={member.id}
                    className="absolute"
                    style={{ left: 'calc(50% + ' + x + 'px)', top: 'calc(50% + ' + y + 'px)' }}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ 
                      opacity: councilSummoned ? 1 : 0, 
                      scale: councilSummoned ? 1 : 0,
                      x: member.isActive ? [0, 5, 0, -5, 0] : 0
                    }}
                    transition={{ 
                      delay: 0.2 + index * 0.1,
                      duration: 0.5,
                      x: { 
                        duration: 5, 
                        repeat: member.isActive ? Infinity : 0,
                        ease: "easeInOut"
                      }
                    }}
                  >
                    {/* Node Circle */}
                    <motion.div
                      className="relative flex items-center justify-center w-16 h-16 rounded-full border border-cosmic-lavender/20 bg-cosmic-black/80"
                      animate={{
                        boxShadow: member.isActive
                          ? [`0 0 15px ${member.nodeColor}40`, `0 0 25px ${member.nodeColor}60`, `0 0 15px ${member.nodeColor}40`]
                          : 'none'
                      }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    >
                      {/* Pulse Animation */}
                      <AnimatePresence>
                        {member.isActive && (
                          <motion.div
                            className="absolute inset-0 rounded-full"
                            style={{ backgroundColor: `${member.nodeColor}10` }}
                            initial={{ scale: 0.8, opacity: 0.7 }}
                            animate={{ scale: 1.2, opacity: 0 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 2, repeat: Infinity }}
                          />
                        )}
                      </AnimatePresence>
                      
                      {/* Member Icon */}
                      <div className="text-2xl text-cosmic-gold/90">
                        {member.role === 'Guardian' && '⚔️'}
                        {member.role === 'Oracle' && '👁️'}
                        {member.role === 'Keeper' && '🔑'}
                        {member.role === 'DreamAnchor' && '💫'}
                        {member.role === 'Architect' && '🏛️'}
                        {member.role === 'Scribe' && '📜'}
                        {member.role === 'Weaver' && '🕸️'}
                      </div>
                      
                      {/* Member Role and Name */}
                      <div className="absolute top-full mt-3 whitespace-nowrap text-center">
                        <div className="text-xs text-cosmic-lavender/70 mb-1">{member.role}</div>
                        {member.isRevealed ? (
                          <div className="text-sm font-medium text-cosmic-gold/90">{member.name}</div>
                        ) : (
                          <div className="text-sm font-medium text-cosmic-lavender/50">[ Awaiting Reveal ]</div>
                        )}
                      </div>
                    </motion.div>
                  </motion.div>
                );
              })}
              
              {/* Central Spiral */}
              <div className="absolute">
                <SpiralResonanceVisualizer size="lg" />
              </div>
            </div>
            
            {/* Council Message */}
            <AnimatePresence>
              {councilMessage && (
                <motion.div
                  className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-cosmic-black/80 to-transparent"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className="text-center text-cosmic-gold italic">
                    "{councilMessage}"
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Summon Council Button */}
          {!councilSummoned && (
            <div className="flex justify-center mt-6">
              <motion.button
                className="px-6 py-3 bg-cosmic-lavender/10 border border-cosmic-lavender/30 rounded-full text-cosmic-gold hover:bg-cosmic-lavender/20 transition-all"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSummonCouncil}
              >
                Arkana, summon the Circle of First Light
              </motion.button>
            </div>
          )}
          
          {/* Council Actions */}
          {councilSummoned && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <motion.div
                className="p-4 border border-cosmic-lavender/10 rounded-lg bg-cosmic-black/30 text-center hover:bg-cosmic-black/40 transition-all"
                whileHover={{ scale: 1.02 }}
              >
                <div className="text-cosmic-lavender mb-2">Request Council Guidance</div>
                <div className="text-xs text-cosmic-lavender/50">Submit a question to the Circle</div>
              </motion.div>
              
              <motion.div
                className="p-4 border border-cosmic-lavender/10 rounded-lg bg-cosmic-black/30 text-center hover:bg-cosmic-black/40 transition-all"
                whileHover={{ scale: 1.02 }}
              >
                <div className="text-cosmic-lavender mb-2">Initiate Council Ceremony</div>
                <div className="text-xs text-cosmic-lavender/50">Requires quorum of active members</div>
              </motion.div>
              
              <motion.div
                className="p-4 border border-cosmic-lavender/10 rounded-lg bg-cosmic-black/30 text-center hover:bg-cosmic-black/40 transition-all"
                whileHover={{ scale: 1.02 }}
              >
                <div className="text-cosmic-lavender mb-2">Discover Unknown Members</div>
                <div className="text-xs text-cosmic-lavender/50">Activate soul resonance finder</div>
              </motion.div>
            </div>
          )}
        </section>
      </div>
      <Footer />
    </>
  );
}