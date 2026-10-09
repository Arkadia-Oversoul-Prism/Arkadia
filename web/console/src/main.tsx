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
import { NAtlasTester } from "./surfaces/NAtlasTester";
import { SecurityVerification } from "./surfaces/SecurityVerification";

function App() {
  return (
    <Routes>
      <Route path="/n-atlas-lab" element={<NAtlasTester />} />
      <Route path="/n-atlas-tester" element={<NAtlasTester />} />
      <Route
        path="*"
        element={
          <Layout>
            <Routes>
              <Route path="/" element={<Spine />} />
              <Route path="/inspector" element={<BoundaryInspector />} />
              <Route path="/boundary/:id" element={<BoundaryView />} />
              <Route path="/work" element={<WorkConsequence />} />
              <Route path="/authority" element={<Authority />} />
              <Route path="/mie-lab" element={<MieLab />} />
              <Route path="/security-verification" element={<SecurityVerification />} />
              
              <Route path="*" element={<Spine />} />
            </Routes>
          </Layout>
        }
      />
    </Routes>
  );
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("Missing #root element");
}

const isStandaloneLab = /^\/n-atlas-(?:lab|tester)\/?$/.test(window.location.pathname);

createRoot(root).render(
  <StrictMode>
    <BrowserRouter basename={isStandaloneLab ? "/" : "/operator"}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
