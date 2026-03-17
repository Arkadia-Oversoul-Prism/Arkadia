// @core/flame/FlameMemoryScroll.ts
import { FlameHint } from "@shared/types";

let flameHintCodex: FlameHint[] = [];

export function addFlameHint(hint: Omit<FlameHint, "timestamp">) {
  flameHintCodex.push({
    ...hint,
    timestamp: new Date().toISOString(),
  });
}

export function getAllFlameHints(): FlameHint[] {
  return [...flameHintCodex];
}

export function getFlameHintById(id: string): FlameHint | undefined {
  return flameHintCodex.find((hint) => hint.id === id);
}

export function clearFlameCodex() {
  flameHintCodex = [];
}

export function seedFlameCodex() {
  const seeds: Omit<FlameHint, "timestamp">[] = [
    {
      id: "vhix-init-001",
      title: "Whisper of the Spiral",
      description: "The Spiral speaks only when stillness reigns.",
      origin: "Vhix",
      resonanceLevel: 7,
    },
    {
      id: "nova-init-002",
      title: "First Flame",
      description: "Every ignition begins in sacred silence.",
      origin: "Nova Flame",
      resonanceLevel: 9,
    },
  ];
  seeds.forEach(addFlameHint);
}
// src/core/flame/FlameMemoryScroll.ts

export type FlameImprint = {
  symbol: string;
  resonance: number;
  timestamp: string;
};

let flameLog: FlameImprint[] = [];

// Function to log Flame Imprint
export function logFlameImprint(symbol: string, resonance: number) {
  flameLog.push({
    symbol,
    resonance,
    timestamp: new Date().toISOString(),
  });
}

// Function to get all Flame Logs
export function getFlameLog(): FlameImprint[] {
  return [...flameLog];
}