import React, { createContext, useContext, useState } from "react";

interface GateContextType {
  gateOpen: boolean;
  enter: () => void;
  exit: () => void;
}

// Toggle this to true to bypass the gate temporarily
const BYPASS_GATE = true;

export const GateContext = createContext<GateContextType>({
  gateOpen: BYPASS_GATE,
  enter: () => {},
  exit: () => {},
});

export const useGate = () => useContext(GateContext);

export const GateProvider = ({ children }: { children: React.ReactNode }) => {
  const [gateOpen, setGateOpen] = useState<boolean>(BYPASS_GATE);

  const enter = () => setGateOpen(true);
  const exit = () => setGateOpen(false);

  return (
    <GateContext.Provider value={{ gateOpen, enter, exit }}>
      {children}
    </GateContext.Provider>
  );
};
