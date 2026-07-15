// @shared/types.ts
export type FlameHint = {
  id: string;
  title: string;
  description: string;
  origin?: string; // e.g., "Nova Flame", "Vhix", etc.
  resonanceLevel?: number;
  timestamp: string;
};