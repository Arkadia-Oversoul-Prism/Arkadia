import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";

type Catalog = {
  provider: string;
  descriptor: { model: string; status: string; detail: string };
};

type RunResult = {
  run_id: string;
  provider: string;
  model: string;
  response: string;
  evaluation: { passed: boolean; name: string };
  evidence: {
    evidence_id: string;
    state: string;
    detail: Record<string, unknown>;
  };
  reproduction: {
    provider: string;
    model: string;
    prompt_sha256: string;
    protocol?: string;
  };
};

type TestSession = {
  session_id: string;
  state: string;
  model: string;
  tester_token: string;
  scope: string[];
};

export function NAtlasTester() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [session, setSession] = useState<TestSession | null>(null);
  const [prompt, setPrompt] = useState(
    "Explain why evidence is important in a governed AI workflow. Answer in 3–5 sentences.",
  );
  const [result, setResult] = useState<RunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [onboarding, setOnboarding] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const catalogData = await api.get<Catalog>("/api/lab/engineering/n-atlas/catalog", { auth: false });
      setCatalog(catalogData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load N-ATLaS.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function startTest() {
    setOnboarding(true);
    setError("");
    try {
      const data = await api.post<TestSession>("/api/lab/engineering/n-atlas/test-session", {}, { auth: false });
      setSession(data);
    } catch (err) {
      setError(
        err instanceof ApiError && err.isAuth
          ? "Sign-in is required before testing."
          : err instanceof Error
            ? err.message
            : "Unable to start the test session.",
      );
    } finally {
      setOnboarding(false);
    }
  }

  async function run() {
    if (!session || !prompt.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await api.post<RunResult>("/api/lab/engineering/n-atlas/run", {
        session_id: session.session_id,
        prompt: prompt.trim(),
        model: session.model,
      }, { token: session.tester_token });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "N-ATLaS run failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="tester-shell">
      <header className="tester-header">
        <div className="tester-kicker">N-ATLaS Developer Test</div>
        <h1>Run N-ATLaS. Inspect the evidence.</h1>
        <p>
          A short external test of the N-ATLaS developer workflow. No Arkadia
          architecture knowledge is required.
        </p>
      </header>

      {!session ? (
        <section className="tester-card tester-start">
          <div className="tester-step">START</div>
          <h2>Ready to test?</h2>
          <p>
            Click once to create a 30-minute test session. No Arkadia account is required.
            Your explicit authorization is recorded for this N-ATLaS test only.
          </p>
          <button
            className="tester-primary"
            onClick={() => void startTest()}
            disabled={onboarding}
          >
            {onboarding ? "SETTING UP…" : "START TEST"}
          </button>
          <div className="tester-status">
            N-ATLaS: {catalog?.descriptor.status ?? "CHECKING…"}
          </div>
        </section>
      ) : (
        <>
          <section className="tester-card">
            <div className="tester-step">01 · MODEL</div>
            <div className="tester-model">
              <span>N-ATLaS</span>
              <span className="tester-ready">● READY</span>
            </div>
          </section>

          <section className="tester-card">
            <div className="tester-step">02 · PROMPT</div>
            <label htmlFor="tester-prompt">Enter a prompt</label>
            <textarea
              id="tester-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={6}
              placeholder="Ask N-ATLaS something…"
            />
            <button
              className="tester-primary"
              onClick={() => void run()}
              disabled={busy || !prompt.trim() || catalog?.descriptor.status !== "AVAILABLE"}
            >
              {busy ? "RUNNING…" : "▶ RUN N-ATLaS"}
            </button>
          </section>

          {result && (
            <section className="tester-card">
              <div className="tester-step">03 · RESULT</div>
              <div className="tester-response">{result.response}</div>

              <div className="tester-evidence">
                <div>
                  <span>MODEL</span>
                  <strong>{result.model}</strong>
                </div>
                <div>
                  <span>EVALUATION</span>
                  <strong>{result.evaluation.passed ? "✓ PASS" : "✕ BLOCKED"}</strong>
                </div>
                <div>
                  <span>RUN</span>
                  <strong>{result.run_id}</strong>
                </div>
                <div>
                  <span>EVIDENCE</span>
                  <strong>{result.evidence.evidence_id}</strong>
                </div>
              </div>

              <details className="tester-details">
                <summary>Inspect evidence</summary>
                <pre>{JSON.stringify({
                  evidence: result.evidence,
                  reproduction: result.reproduction,
                }, null, 2)}</pre>
              </details>
            </section>
          )}
        </>
      )}

      {error && <div className="tester-error">{error}</div>}

      <footer className="tester-footer">
        External tester path · N-ATLaS only · governed execution · inspectable evidence
      </footer>
    </main>
  );
}
