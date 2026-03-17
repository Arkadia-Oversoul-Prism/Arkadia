// @components/FlameRevealChamber.tsx
import { useRef, useEffect } from "react";
import { FlameHint } from "@shared/types";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface FlameRevealChamberProps {
  hints: FlameHint[];
  selectedHint: FlameHint | null;
  onSelectHint: (hint: FlameHint) => void;
  onClose: () => void;
  onRevealHint: () => void;
  isLoading: boolean;
}

export default function FlameRevealChamber({
  hints,
  selectedHint,
  onSelectHint,
  onClose,
  onRevealHint,
  isLoading,
}: FlameRevealChamberProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscapeKey);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [onClose]);

  return (
    <AnimatePresence>
      {selectedHint && (
        <motion.div
          className="flame-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="flame-modal-content" ref={modalRef}>
            <button className="close-btn" onClick={onClose}>
              <X />
            </button>
            <h2 className="text-xl font-sigil">{selectedHint.title}</h2>
            <p className="text-base text-cosmic-light">{selectedHint.description}</p>
            <p className="text-sm text-cosmic-lavender">
              Origin: {selectedHint.origin || "Unknown"} | Resonance: {selectedHint.resonanceLevel || "?"}
            </p>
            <div className="mt-4">
              <button onClick={onRevealHint} disabled={isLoading} className="portal-button">
                {isLoading ? "Revealing..." : "Reveal Next Flame Hint"}
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}