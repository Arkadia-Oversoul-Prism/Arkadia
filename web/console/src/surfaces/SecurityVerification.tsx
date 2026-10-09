import { useState } from "react";
import { ApiError, api } from "../api/client";

type Check = { id: string; status: "PASS" | "FAIL" };
type Attestation = { run_id: string; observed_at: string; result: "PASS" | "FAIL"; read_only: boolean; checks: Check[]; redaction: string };
type Row = { id: string; status: "PASS" | "FAIL" | "UNKNOWN"; detail: string };

export function SecurityVerification() {
  const [running, setRunning] = useState(false);
  const [rows, setRows] = useState<Row[]>([]);
  const [attestation, setAttestation] = useState<Attestation | null>(null);
  const [message, setMessage] = useState("No verification has been run in this session.");

  async function run() {
    setRunning(true); setRows([]); setAttestation(null);
    setMessage("Running bounded authorization probes…");
    const next: Row[] = [];
    try {
      try {
        await api.get<Attestation>("/api/operator/security-verification", { auth: false });
        next.push({ id: "anonymous_rejected", status: "FAIL", detail: "Unauthenticated request unexpectedly succeeded." });
      } catch (error) {
        const status = error instanceof ApiError ? error.status : null;
        next.push({ id: "anonymous_rejected", status: status === 401 ? "PASS" : "FAIL", detail: status === 401 ? "Anonymous request rejected with HTTP 401." : status === 403 ? "Got HTTP 403, not the expected HTTP 401." : status === null ? "Probe failed before an HTTP status was received." : "Unexpected HTTP " + status + "." });
      }
      try {
        const result = await api.get<Attestation>("/api/operator/security-verification");
        setAttestation(result);
        next.push({ id: "signed_in_sovereign_accepted", status: result.result === "PASS" ? "PASS" : "FAIL", detail: result.result === "PASS" ? "Server accepted the Firebase-authenticated sovereign and all runtime checks passed." : "Server returned an attestation, but one or more runtime checks failed." });
        for (const check of result.checks) next.push({ id: check.id, status: check.status, detail: check.status === "PASS" ? "Confirmed by the running server." : "Not proven by the running server." });
      } catch (error) {
        const status = error instanceof ApiError ? error.status : null;
        next.push({ id: "signed_in_sovereign_accepted", status: status === 401 || status === 403 ? "FAIL" : "UNKNOWN", detail: status === 401 ? "Console token was not accepted. Sign in to Arkadia, then reload this console." : status === 403 ? "Identity was recognized but lacks sovereign authorization." : status === null ? "No HTTP response; network or transport failure." : "Unexpected HTTP " + status + "." });
      }
      setRows(next);
      setMessage(next.every((row) => row.status === "PASS") ? "Verification passed. Evidence is correlated to the server run ID below." : "Verification completed with failed or unresolved checks. This control collected no secrets.");
    } finally { setRunning(false); }
  }

  function tone(status: string) { return status === "PASS" ? "demonstrated" : status === "FAIL" ? "contradicted" : "unresolved"; }

  return <div className="grid" style={{ gap: 16 }}>
    <section className="card">
      <p className="small dim" style={{ marginTop: 0 }}>A read-only production control. It sends one anonymous probe and one request using the existing same-origin Arkadia session. The server returns redacted runtime evidence and writes a correlated event to application logs.</p>
      <p className="tiny faint">No secrets, bearer tokens, UIDs, emails, or raw exception details are displayed. This action does not change configuration or execute mutations.</p>
      <button type="button" onClick={run} disabled={running} style={{ padding: "10px 14px", borderRadius: 6, cursor: running ? "wait" : "pointer" }}>{running ? "Verifying…" : "Run security verification"}</button>
      <p className="small" role="status">{message}</p>
    </section>
    {rows.length > 0 && <section className="card">
      <h3 className="card-title">Observed checks</h3>
      <div className="edge-list">{rows.map((row) => <div key={row.id} className={"edge edge-" + tone(row.status)}><span className="mono edge-line">{row.id}</span><span className={"edge-status " + tone(row.status)}>{row.status}</span><span className="edge-witness">{row.detail}</span></div>)}</div>
    </section>}
    {attestation && <section className="card">
      <h3 className="card-title">Server evidence</h3>
      <p className="small">Result: <strong>{attestation.result}</strong></p>
      <p className="tiny faint">Run ID: <code>{attestation.run_id}</code></p>
      <p className="tiny faint">Observed: {new Date(attestation.observed_at).toLocaleString()}</p>
      <p className="tiny faint">Redaction: {attestation.redaction}</p>
    </section>}
  </div>;
}