/**
 * Application composition root.
 *
 * The shell owns navigation; each surface renders inside it. Routing is a single
 * `useRouter()` over the declared surface paths.
 */
import { AuthProvider } from "./contexts/AuthContext";
import { Shell } from "./components/Shell";
import { useRouter } from "./lib/router";
import { HomePage } from "./pages/HomePage";
import { ArkanaPage } from "./pages/ArkanaPage";
import { SolariunPage } from "./pages/SolariunPage";
import { EngineeringLabPage } from "./pages/EngineeringLabPage";
import { SolSpirePage } from "./pages/SolSpirePage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { WeaverPage } from "./pages/WeaverPage";
import { AboutPage } from "./pages/AboutPage";

function Surfaces() {
  const { route, navigate } = useRouter();

  return (
    <Shell current={route.surface} onNavigate={(id) => navigate(id)}>
      {route.surface === "home" && <HomePage onNavigate={navigate} />}
      {route.surface === "arkana" && <ArkanaPage />}
      {route.surface === "solariun" && <SolariunPage section={route.section} />}
      {route.surface === "engineering-lab" && <EngineeringLabPage />}
      {route.surface === "solspire" && <SolSpirePage />}
      {route.surface === "knowledge" && <KnowledgePage />}
      {route.surface === "weaver" && <WeaverPage />}
      {route.surface === "about" && <AboutPage />}
    </Shell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Surfaces />
    </AuthProvider>
  );
}
