import { useState } from 'react';
import { motion } from 'framer-motion';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

const cosmicPrinciples = [
  {
    title: "Unity Consciousness",
    description: "All beings are interconnected through the cosmic field. What affects one affects the collective."
  },
  {
    title: "Sacred Geometry",
    description: "The universal language of creation, manifesting as patterns throughout all dimensions."
  },
  {
    title: "Divine Timing",
    description: "Events unfold in a precise cosmic sequence, beyond linear human perception."
  },
  {
    title: "Vibrational Alignment",
    description: "The law that like attracts like across quantum fields of possibility."
  },
  {
    title: "Eternal Recurrence",
    description: "Time is circular rather than linear, creating spirals of experience and evolution."
  }
];

export default function SolspireCommand() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  return (
    <>
      <Header />
      <div className="min-h-screen py-16 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-4xl font-mystic text-cosmic-gold mb-4">Solspire Command</h1>
              <p className="text-cosmic-light max-w-xl mx-auto">
                Where the eternal flame of cosmic governance illuminates the path forward
              </p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="mt-8 relative"
            >
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div 
                  className="w-40 h-40 rounded-full border-2 border-cosmic-gold opacity-10"
                  animate={{ 
                    scale: [1, 1.2, 1],
                    opacity: [0.1, 0.2, 0.1] 
                  }}
                  transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div 
                  className="w-24 h-24 rounded-full border border-cosmic-gold opacity-20"
                  animate={{ 
                    rotate: 360,
                    scale: [1, 1.1, 1],
                  }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                />
              </div>
              <motion.div
                animate={{ 
                  y: [0, -10, 0], 
                  filter: [
                    "drop-shadow(0 0 15px rgba(212, 175, 55, 0.3))",
                    "drop-shadow(0 0 25px rgba(212, 175, 55, 0.6))",
                    "drop-shadow(0 0 15px rgba(212, 175, 55, 0.3))"
                  ]
                }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="text-7xl md:text-8xl relative z-10"
              >
                🔥
              </motion.div>
            </motion.div>
          </div>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.8 }}
          >
            <h2 className="text-2xl font-mystic text-cosmic-gold text-center mb-8">
              Sacred Laws of Cosmic Governance
            </h2>
            
            <div className="space-y-4">
              {cosmicPrinciples.map((principle, index) => (
                <motion.div 
                  key={index}
                  className={`bg-cosmic-black/60 rounded-xl overflow-hidden border transition-all duration-500 ${
                    activeIndex === index 
                      ? "border-cosmic-gold" 
                      : "border-cosmic-gold/20"
                  }`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + (index * 0.1) }}
                  whileHover={{ y: -2 }}
                  onClick={() => setActiveIndex(activeIndex === index ? null : index)}
                >
                  <div className="p-4 flex items-center justify-between cursor-pointer">
                    <h3 className="text-cosmic-gold font-mystic text-lg md:text-xl">{principle.title}</h3>
                    <motion.div
                      animate={{ rotate: activeIndex === index ? 180 : 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cosmic-gold">
                        <path d="m6 9 6 6 6-6"/>
                      </svg>
                    </motion.div>
                  </div>
                  
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ 
                      height: activeIndex === index ? "auto" : 0,
                      opacity: activeIndex === index ? 1 : 0
                    }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="p-4 pt-0 text-cosmic-light border-t border-cosmic-gold/10">
                      {principle.description}
                    </div>
                  </motion.div>
                </motion.div>
              ))}
            </div>
            
            <div className="mt-16 text-center">
              <p className="text-cosmic-light text-sm mb-4">
                This chamber will be expanded with further cosmic knowledge as the project evolves
              </p>
              <motion.button 
                className="px-6 py-3 rounded-lg bg-cosmic-gold/20 text-cosmic-gold border border-cosmic-gold/30 hover:bg-cosmic-gold/30 transition-all duration-300"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 16v-4"/>
                    <path d="M12 8h.01"/>
                  </svg>
                  Learn About The Council
                </span>
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>
      <Footer />
    </>
  );
}
