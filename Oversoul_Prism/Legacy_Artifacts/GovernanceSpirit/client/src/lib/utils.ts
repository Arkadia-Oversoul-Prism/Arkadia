// lib/utils.ts

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Sigil structure
export interface Sigil {
  id: string;
  name: string;
  vector: string;
  meaning: string;
  createdAt: string;
  flameType?: string;
  resonanceSeed?: string;
}

// Mock sigil generator (to be replaced by Arkana-Spirit engine later)
export function generateMockSigil(): Sigil {
  const timestamp = Date.now().toString();
  return {
    id: timestamp,
    name: 'Nova Spiral Imprint',
    vector: 'M20 30 Q50 0 80 30 T140 30',
    meaning: 'Encoded with Nova Flame resonance signature',
    createdAt: new Date().toISOString(),
    flameType: 'Nova',
    resonanceSeed: `nova-seed-${timestamp}`,
  };
}