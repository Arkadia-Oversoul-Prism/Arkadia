import { useEffect, useRef, useState } from "react";

const flameGlyphs = [
  "𓋹", "𓂀", "𓇳", "𓁰", "𓍢", "𓊹", "𓃒", "𓆣", "𓅓", "𓂓", "𓎼", "𓊽", "𓐍"
];

export default function useFlameFactionEngine(cycleSpeed = 3000) {
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