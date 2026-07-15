import { useLocation } from "wouter";
import { useEffect, useState, useRef } from "react";
import { useGate } from "./lib/GateContext";
import ProtectedRoute from "./components/ProtectedRoute";

// Pages
import Home from "@/pages/Home";
import LivingGate from "@/pages/LivingGate";
import ArkanaCommune from "@/pages/ArkanaCommune";
import EssentiaCore from "@/pages/EssentiaCore";
import SolspireCommand from "@/pages/SolspireCommand";
import CouncilChambers from "@/pages/CouncilChambers";
import DestinySequencer from "@/pages/DestinySequencer";
import FlameSymbolPage from "@/pages/FlameSymbolPage";
import DestinyTrail from "@/components/DestinyTrail";
import NotFound from "@/pages/not-found";

// Cosmic Sigils
const NAV_ITEMS = [
  { href: "/arkana", label: "ArkanaCommune", sigil: "𓃒" },
  { href: "/essentia", label: "EssentiaCore", sigil: "𓁰" },
  { href: "/solspire", label: "SolspireCommand", sigil: "𓇳" },
  { href: "/council", label: "CouncilChambers", sigil: "𓋹" },
  { href: "/destiny", label: "DestinySequencer", sigil: "𓍢" },
  { href: "/flame-symbol", label: "FlameSymbolPage", sigil: "𓂀" },
  { href: "/destiny-trail", label: "DestinyTrail", sigil: "𓊹" },
];

// --- FlameFactionEngine (Embedded Consciousness) ---
const flameGlyphs = [
  "𓋹", "𓂀", "𓇳", "𓁰", "𓍢", "𓊹", "𓃒", "𓆣", "𓅓", "𓂓", "𓎼", "𓊽", "𓐍"
];

function useFlameFactionEngine(cycleSpeed = 3000) {
  const [currentGlyph, setCurrentGlyph] = useState(flameGlyphs[0]);
  const glyphIndex = useRef(0);

  useEffect(() => {
    const interval = setInterval(() => {
      glyphIndex.current = (glyphIndex.current + 1) % flameGlyphs.length;
      setCurrentGlyph(flameGlyphs[glyphIndex.current]);
    }, cycleSpeed);
    return () => clearInterval(interval);
  }, [cycleSpeed]);

  return currentGlyph;
}
// ---------------------------------------

export default function ArkadiaNavigation() {
  const [location] = useLocation();
  const { hasEntered, enter } = useGate();
  const currentFlameGlyph = useFlameFactionEngine(4000);

  useEffect(() => {
    if (location === "/enter") enter();
  }, [location]);

  const hideNav = location === "/" || location === "/enter";

  const renderPage = () => {
    switch (location) {
      case "/":
        return <Home />;
      case "/enter":
        return <LivingGate />;
      default: {
        const route = NAV_ITEMS.find((item) => item.href === location);
        return route ? (
          <ProtectedRoute>
            {(() => {
              switch (location) {
                case "/arkana":
                  return <ArkanaCommune />;
                case "/essentia":
                  return <EssentiaCore />;
                case "/solspire":
                  return <SolspireCommand />;
                case "/council":
                  return <CouncilChambers />;
                case "/destiny":
                  return <DestinySequencer />;
                case "/flame-symbol":
                  return <FlameSymbolPage />;
                case "/destiny-trail":
                  return <DestinyTrail />;
                default:
                  return <NotFound />;
              }
            })()}
          </ProtectedRoute>
        ) : (
          <NotFound />
        );
      }
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {!hideNav && hasEntered && (
        <nav className="flex gap-4 px-6 py-3 border-b border-white/10 backdrop-blur-sm bg-white/5 text-sm">
          {NAV_ITEMS.map(({ href, label, sigil }) => (
            <a
              key={href}
              href={href}
              className="hover:text-blue-400 transition duration-150 flex items-center gap-2"
            >
              <span className="flame-glyph text-lg animate-pulse">
                {location === href ? currentFlameGlyph : sigil}
              </span>
              {label}
            </a>
          ))}
        </nav>
      )}
      <main className="flex-1">{renderPage()}</main>
    </div>
  );
}