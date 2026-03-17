import { useRef, useEffect } from "react";
import { Hint } from "@shared/schema";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface HintModalProps {
  hints: Hint[];
  selectedHint: Hint | null;
  onSelectHint: (hint: Hint) => void;
  onClose: () => void;
  onRevealHint: () => void;
  isLoading: boolean;
}

export default function HintModal({
  hints,
  selectedHint,
  onSelectHint,
  onClose,
  onRevealHint,
  isLoading,
}: HintModalProps) {
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
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-cosmic-black bg-opacity-80">
        <motion.div
          ref={modalRef}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ type: "spring", damping: 15 }}
          className="relative bg-deep-blue border border-cosmic-gold border-opacity-30 rounded-xl p-6 w-full max-w-md mx-4 backdrop-blur-sm"
        >
          <div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3">
            <div className="w-16 h-16 meditation-circle rounded-full border-2 border-cosmic-gold opacity-40"></div>
          </div>
          <div className="absolute bottom-0 left-0 transform -translate-x-1/3 translate-y-1/3">
            <div className="w-12 h-12 meditation-circle rounded-full border-2 border-cosmic-gold opacity-30"></div>
          </div>

          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-cosmic-light hover:text-cosmic-gold transition-colors"
          >
            <X className="h-5 w-5" />
          </button>

          <h2 className="text-2xl font-mystic text-cosmic-gold text-center mb-6">
            Celestial Guidance
          </h2>

          <div className="text-center space-y-6 my-6">
            <p className="text-cosmic-light">
              Your team is making progress, but could use a hint to move forward...
            </p>

            <div className="bg-cosmic-black bg-opacity-40 p-4 rounded-lg">
              <h4 className="font-mystic text-cosmic-gold mb-2">Available Hints</h4>
              {isLoading ? (
                <div className="flex justify-center p-4">
                  <div className="w-6 h-6 border-2 border-cosmic-gold border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : hints.length === 0 ? (
                <p className="text-cosmic-light text-center">No hints available at this time</p>
              ) : (
                <div className="space-y-3 text-left">
                  {hints.map((hint) => (
                    <div key={hint.id} className="flex items-start space-x-3">
                      <div>
                        <input
                          type="radio"
                          id={`hint-${hint.id}`}
                          name="hint"
                          className="sr-only peer"
                          checked={selectedHint?.id === hint.id}
                          onChange={() => onSelectHint(hint)}
                        />
                        <label
                          htmlFor={`hint-${hint.id}`}
                          className="cursor-pointer block w-5 h-5 rounded-full border border-cosmic-gold peer-checked:bg-cosmic-gold"
                        ></label>
                      </div>
                      <label htmlFor={`hint-${hint.id}`} className="cursor-pointer">
                        <span className="font-medium text-cosmic-light block">
                          {hint.title}
                        </span>
                        <span className="text-sm text-gray-400">
                          {hint.description}
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 portal-button bg-cosmic-black hover:bg-opacity-80 text-cosmic-light px-4 py-3 rounded-lg transition-all duration-300"
            >
              Maybe Later
            </button>
            <button
              onClick={onRevealHint}
              disabled={!selectedHint || isLoading}
              className={`flex-1 portal-button ${
                selectedHint
                  ? "bg-cosmic-gold bg-opacity-30 hover:bg-opacity-40 text-cosmic-gold"
                  : "bg-cosmic-black bg-opacity-50 text-cosmic-light opacity-50 cursor-not-allowed"
              } px-4 py-3 rounded-lg transition-all duration-300`}
            >
              Reveal Hint
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
