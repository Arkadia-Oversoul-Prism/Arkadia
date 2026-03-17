import { create } from 'zustand';
import { EssenceEntry } from '@shared/schema';

interface EssentiaState {
  entries: EssenceEntry[];
  setEntries: (entries: EssenceEntry[]) => void;
  addEntry: (entry: EssenceEntry) => void;
}

export const useEssentiaStore = create<EssentiaState>((set) => ({
  entries: [],
  setEntries: (entries) => set({ entries }),
  addEntry: (entry) => set((state) => ({ 
    entries: [entry, ...state.entries] 
  })),
}));
