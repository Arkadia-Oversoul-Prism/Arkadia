/**
 * Application composition root.
 *
 * The shell owns navigation; each surface renders inside it. Routing is a single
 * `useRouter()` over the declared surface paths. Protected surfaces render a
 * sign-in threshold until an identity is verified — the threshold is a real
 * authorization boundary, not a cosmetic redirect.
 */
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Shell } from "./components/Shell";
import { Loading, Page, Panel } from "./components/ui";
import { SURFACE_BY_ID } from "./lib/surfaces";
import { useRouter } from "./lib/router";
import { HomePage } from "./pages/HomePage";
import { NovaNetPage } from "./pages/NovaNetPage";
import { ArkanaPage } from "./pages/ArkanaPage";
import { SolariunPage } from "./pages/SolariunPage";
import { EngineeringLabPage } from "./pages/EngineeringLabPage";
import { SolSpirePage } from "./pages/SolSpirePage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { WeaverPage } from "./pages/WeaverPage";
import { AboutPage } from "./pages/AboutPage";
import { SignInPage } from "./pages/SignInPage";

function AuthThreshold() {
  return (
    <Page title="Protected surface" subtitle="This surface requires an authenticated Arkadia identity.">
      <Panel className="border-gold/30">
        <p className="font-display text-lg text-gold">Sign in to continue</p>
        <p className="mt-1 text-sm text-white/60">
          This surface reads protected contracts. Authentication is required; there is no anonymous
          view of the content behind it.
        </p>
        <a
          href="/login"
          data-testid="auth-threshold-signin"
          className="mt-4 inline-block rounded border border-gold/40 bg-gold/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-gold"
        >
          Go to sign in
        </a>
      </Panel>
    </Page>
  );
}

function Surfaces() {
  const { route, navigate } = useRouter();
  const { isAuthenticated, loading } = useAuth();
  const def = SURFACE_BY_ID[route.surface];

  const body = (() => {
    if (def.requiresAuth && loading) return <Loading label="Verifying identity…" />;
    if (def.requiresAuth && !isAuthenticated) return <AuthThreshold />;
    switch (route.surface) {
      case "home":
        return <HomePage onNavigate={navigate} />;
      case "novanet":
        return <NovaNetPage section={route.section} onNavigate={navigate} />;
      case "arkana":
        return <ArkanaPage />;
      case "solariun":
        return <SolariunPage section={route.section} />;
      case "engineering-lab":
        return <EngineeringLabPage />;
      case "solspire":
        return <SolSpirePage />;
      case "knowledge":
        return <KnowledgePage />;
      case "weaver":
        return <WeaverPage />;
      case "about":
        return <AboutPage />;
      case "login":
        return <SignInPage />;
      default:
        return <HomePage onNavigate={navigate} />;
    }
  })();

  return (
    <Shell current={route.surface} onNavigate={(id) => navigate(id)}>
      {body}
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
