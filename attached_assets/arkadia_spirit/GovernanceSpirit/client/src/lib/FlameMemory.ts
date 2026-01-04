export type FlameImprint = {
  symbol: string;
  resonance: number;
  timestamp: string;
};

const FLAME_LOG_KEY = 'arkadia_flame_log';

function loadFromStorage(): FlameImprint[] {
  const raw = localStorage.getItem(FLAME_LOG_KEY);
  return raw ? JSON.parse(raw) : [];
}

let flameLog: FlameImprint[] = loadFromStorage();

export function logFlameImprint(symbol: string, resonance: number): void {
  const imprint = {
    symbol,
    resonance,
    timestamp: new Date().toISOString(),
  };
  flameLog.push(imprint);
  localStorage.setItem(FLAME_LOG_KEY, JSON.stringify(flameLog));
}

export function getFlameLog(): FlameImprint[] {
  return [...flameLog];
}

export function clearFlameLog(): void {
  flameLog = [];
  localStorage.removeItem(FLAME_LOG_KEY);
}