import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

type Session = { session_id: string; state: string; objective?: string };
type Catalog = {
  provider: string;
  descriptor: { model: string; status: string; detail: string };
  live_boundary: string;
};
type RunResult = {
  run_id: string;
  provider: string;
  model: string;
  response: string;
  evaluation: { passed: boolean; name: string };
  evidence: { evidence_id: string; state: string; detail: Record<string, unknown> };
  reproduction: { provider: string; model: string; prompt_sha256: string };
};

export function NAtlasLab() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [prompt, setPrompt] = useState("Give one concise example of how Nigerian developers could use N-ATLAS in a civic technology workflow.");
  const [result, setResult] = useState<RunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [c, s] = await Promise.all([
        api.get<Catalog>("/api/lab/engineering/n-atlas/catalog"),
        api.get<{ sessions: Session[] }>("/api/lab/engineering/sessions"),
      ]);
      setCatalog(c);
      setSessions(s.sessions);
      const usable = s.sessions.find((item) => item.state === "AUTHORIZED" || item.state === "QUEUED");
      if (usable && !sessionId) setSessionId(usable.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load N-ATLAS Lab");
    }
  }

  useEffect(() => { void load(); }, []);

  const usableSessions = useMemo(
    () => sessions.filter((s) => s.state === "AUTHORIZED" || s.state === "QUEUED"),
    [sessions],
  );

  async function run() {
    if (!sessionId || !prompt.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await api.post<RunResult>("/api/lab/engineering/n-atlas/run", {
        session_id: sessionId,
        prompt: prompt.trim(),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "N-ATLAS run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <section className="mie-panel">
        <div className="mie-panel-label">N-ATLAS · DEVELOPER INFRASTRUCTURE</div>
        <h2 style={{ margin: "10px 0 6px", fontSize: 32 }}>Run. Inspect. Prove.</h2>
        <p style={{ maxWidth: 760, lineHeight: 1.65, opacity: 0.72 }}>
          One governed workflow for integrating N-ATLAS, executing a real request,
          evaluating the result, and leaving an inspectable evidence trail.
        </p>
      </section>

      <section className="mie-lab-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="mie-panel">
          <div className="mie-panel-label">01 · INTEGRATION</div>
          <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
            <div><strong>Provider</strong><div className="tiny mono">n_atlas</div></div>
            <div><strong>Status</strong><div className="tiny mono">{catalog?.descriptor.status ?? "LOADING"}</div></div>
            <div><strong>Model</strong><div className="tiny mono">{catalog?.descriptor.model ?? "—"}</div></div>
            <div style={{ opacity: 0.65, fontSize: 12 }}>{catalog?.descriptor.detail ?? "Checking configured endpoint…"}</div>
          </div>
          <div style={{ marginTop: 16, padding: 12, border: "1px solid rgba(255,255,255,.1)", fontSize: 12, lineHeight: 1.55 }}>
            {catalog?.live_boundary}
          </div>
        </div>

        <div className="mie-panel">
          <div className="mie-panel-label">02 · GOVERNED SESSION</div>
          <label style={{ display: "grid", gap: 7, marginTop: 14, fontSize: 12 }}>
            Authorized session
            <select value={sessionId} onChange={(e) => setSessionId(e.target.value)} style={{ padding: 11, background: "transparent", color: "inherit", border: "1px solid rgba(255,255,255,.16)" }}>
              <option value="">Select an authorized session</option>
              {usableSessions.map((s) => <option key={s.session_id} value={s.session_id}>{s.session_id} · {s.state}</option>)}
            </select>
          </label>
          <div className="tiny faint" style={{ marginTop: 10 }}>{usableSessions.length} executable session(s) available.</div>
        </div>
      </section>

      <section className="mie-panel">
        <div className="mie-panel-label">03 · GOLDEN WORKFLOW</div>
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={5} style={{ width: "100%", marginTop: 14, boxSizing: "border-box", padding: 14, background: "rgba(0,0,0,.18)", color: "inherit", border: "1px solid rgba(255,255,255,.12)", font: "inherit", resize: "vertical" }} />
        <div className="mie-actions" style={{ marginTop: 12 }}>
          <button className="mie-primary" disabled={busy || !sessionId || catalog?.descriptor.status !== "AVAILABLE"} onClick={() => void run()}>
            {busy ? "RUNNING N-ATLAS…" : "▶ RUN N-ATLAS"}
          </button>
          <button onClick={() => void load()} disabled={busy}>↻ REFRESH STATUS</button>
        </div>
        {error && <div style={{ marginTop: 12, color: "#D66A6A", fontSize: 12 }}>{error}</div>}
      </section>

      {result && (
        <section className="mie-lab-grid" style={{ gridTemplateColumns: "1.4fr .6fr" }}>
          <div className="mie-panel">
            <div className="mie-panel-label">04 · N-ATLAS RESPONSE</div>
            <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7, marginTop: 14 }}>{result.response}</div>
            <details className="mie-json" style={{ marginTop: 16 }}>
              <summary>INSPECT REPRODUCTION RECORD</summary>
              <pre>{JSON.stringify(result.reproduction, null, 2)}</pre>
            </details>
          </div>
          <div className="mie-panel">
            <div className="mie-panel-label">05 · EVIDENCE</div>
            <div style={{ marginTop: 14, display: "grid", gap: 12 }}>
              <div><span className="tiny faint">RUN</span><div className="mono">{result.run_id}</div></div>
              <div><span className="tiny faint">EVIDENCE</span><div className="mono">{result.evidence.evidence_id}</div></div>
              <div><span className="tiny faint">EVALUATION</span><div>{result.evaluation.passed ? "✓ PASS" : "✕ BLOCKED"}</div></div>
              <div><span className="tiny faint">PROVIDER</span><div className="mono">{result.provider}</div></div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
