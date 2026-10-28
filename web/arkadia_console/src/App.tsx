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
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Loading, Page, Panel } from "./components/ui";
import { SURFACE_BY_ID, type SurfaceId } from "./lib/surfaces";
import { useRouter } from "./lib/router";
import { rememberReturnTo } from "./lib/returnTo";
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

function AuthThreshold({ onNavigate }: { onNavigate: (id: SurfaceId, section?: string) => void }) {
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
          onClick={(event) => {
            // The address bar still holds the protected path the user asked
            // for; the navigation wrapper below remembers it before crossing.
            // The href stays a real link for anything that skips this handler.
            event.preventDefault();
            onNavigate("login");
          }}
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

  // One entry for every trip into the sign-in surface: remember the path the
  // user was on before crossing, so a confirmed sign-in can return them there.
  // Both sign-in entries (the threshold and the shell button) reach `login`
  // through this wrapper, and the address-bar pathname itself stays owned by
  // the router — nothing outside `lib/router.ts` parses it.
  const handleNavigate = (id: SurfaceId, section?: string) => {
    if (id === "login") rememberReturnTo(route.path);
    navigate(id, section);
  };

  const body = (() => {
    if (def.requiresAuth && loading) return <Loading label="Verifying identity…" />;
    if (def.requiresAuth && !isAuthenticated) return <AuthThreshold onNavigate={handleNavigate} />;
    switch (route.surface) {
      case "home":
        return <HomePage onNavigate={navigate} />;
      case "novanet":
        return <NovaNetPage section={route.section} onNavigate={navigate} />;
      case "arkana":
        return <ArkanaPage />;
      case "solariun":
        return <SolariunPage section={route.section} onNavigate={navigate} />;
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
        return <SignInPage onNavigate={handleNavigate} />;
      default:
        return <HomePage onNavigate={navigate} />;
    }
  })();

  return (
    <Shell current={route.surface} onNavigate={handleNavigate}>
      <ErrorBoundary key={route.surface} surface={SURFACE_BY_ID[route.surface].name} onHome={() => navigate("home")}>
        {body}
      </ErrorBoundary>
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
