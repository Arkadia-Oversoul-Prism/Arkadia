/**
 * Application composition root.
 *
 * The shell owns navigation; each surface renders inside it. Routing is a single
 * `useRouter()` over the declared surface paths. Protected surfaces render a
 * sign-in threshold until an identity is verified — the threshold is a real
 * authorization boundary, not a cosmetic redirect.
 */
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ProjectProvider } from "./lib/projectContext";
import { Shell } from "./components/Shell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Loading, Page, Panel } from "./components/ui";
import { SURFACE_BY_ID, type SurfaceId } from "./lib/surfaces";
import { useRouter } from "./lib/router";
import { rememberReturnTo } from "./lib/returnTo";
import { WorkspacePage } from "./pages/WorkspacePage";
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
import { OperatorPage } from "./pages/OperatorPage";
import { NAtlasTesterPage } from "./pages/NAtlasTesterPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SettingsPage } from "./pages/SettingsPage";

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
  const handleNavigate = (id: SurfaceId, section?: string, param?: string) => {
    if (id === "login") rememberReturnTo(route.path);
    navigate(id, section, param);
  };

  const body = (() => {
    if (def.requiresAuth && loading) return <Loading label="Verifying identity…" />;
    if (def.requiresAuth && !isAuthenticated) return <AuthThreshold onNavigate={handleNavigate} />;
    switch (route.surface) {
      case "workspace":
        return <WorkspacePage />;
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
      case "projects":
        return <ProjectsPage section={route.section} onNavigate={navigate} />;
      case "settings":
        return <SettingsPage />;
      case "weaver":
        return <WeaverPage />;
      case "operator":
        return <OperatorPage section={route.section} param={route.param} onNavigate={handleNavigate} />;
      case "n-atlas":
        return <NAtlasTesterPage />;
      case "about":
        return <AboutPage />;
      case "login":
        return <SignInPage onNavigate={handleNavigate} />;
      default:
        return <HomePage onNavigate={navigate} />;
    }
  })();

  // A standalone surface owns the whole document. Only the external N-ATLaS
  // tester declares it: its contract is "no Arkadia architecture knowledge
  // required", which the product shell's navigation and identity chrome would
  // contradict. It is still this application — same bundle, same origin, same
  // backend — not a second shell.
  //
  // The boundary is hoisted so it wraps the surface body for *every* surface,
  // standalone included. A second mount on the standalone path would nest
  // failure states (`tests/test_console_surface_error_boundary.py` pins exactly
  // one), so the boundary is defined once and the shell is what varies: a
  // standalone surface skips the shell, not the boundary. Before this, a render
  // failure in the external tester tore down the whole application with no
  // recovery control.
  const surfaceBody = (
    <ErrorBoundary key={route.surface} surface={SURFACE_BY_ID[route.surface].name} onHome={() => navigate("home")}>
      {body}
    </ErrorBoundary>
  );

  if (def.standalone) return surfaceBody;

  return (
    <Shell current={route.surface} onNavigate={handleNavigate}>
      {surfaceBody}
    </Shell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      {/*
        The project-scoped context sits above the router so every surface reads
        one answer to "which project am I in". It is inside AuthProvider because
        both of its reads are authenticated contracts, and outside the router
        because a project selection must survive a navigation between Workspace,
        Projects and the Engineering Lab — that survival is the whole point.
      */}
      <ProjectProvider>
        <Surfaces />
      </ProjectProvider>
    </AuthProvider>
  );
}
