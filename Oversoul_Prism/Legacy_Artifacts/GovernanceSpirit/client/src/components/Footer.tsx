import { motion } from "framer-motion";

export default function Footer() {
  return (
    <motion.footer 
      className="py-6 px-4 border-t border-cosmic-gold border-opacity-10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
    >
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
        <div className="text-cosmic-gold font-mystic mb-4 md:mb-0">ARKADIA</div>
        <div className="text-sm text-cosmic-light opacity-70">
          Manifesting in the eternal now • Cosmic cycle {new Date().getFullYear()}
        </div>
      </div>
    </motion.footer>
  );
}
