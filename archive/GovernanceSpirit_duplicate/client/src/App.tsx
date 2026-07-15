import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GateProvider } from "./lib/GateContext";
import ArkadiaNavigation from "./ArkadiaNavigation";
import ShadowWeaver from "./components/ShadowWeaver";
import FlameScriptInjector from "./components/FlameScriptInjector"; // New

function App() {
  return (
    <ShadowWeaver>
      <FlameScriptInjector /> {/* Now roots itself before all else */}
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <GateProvider>
            <ArkadiaNavigation />
          </GateProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </ShadowWeaver>
  );
}

export default App;