import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { Spine } from "./surfaces/Spine";
import { BoundaryInspector } from "./surfaces/BoundaryInspector";
import { BoundaryView } from "./surfaces/BoundaryView";
import { WorkConsequence } from "./surfaces/WorkConsequence";
import { Authority } from "./surfaces/Authority";
import "./styles.css";
import { MieLab } from "./surfaces/MieLab";
import { NAtlasLab } from "./surfaces/NAtlasLab";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Spine />} />
        <Route path="/inspector" element={<BoundaryInspector />} />
        <Route path="/boundary/:id" element={<BoundaryView />} />
        <Route path="/work" element={<WorkConsequence />} />
        <Route path="/authority" element={<Authority />} />
        <Route path="/mie-lab" element={<MieLab />} />
        <Route path="/n-atlas-lab" element={<NAtlasLab />} />
        <Route path="*" element={<Spine />} />
      </Routes>
    </Layout>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
);
