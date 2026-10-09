import { useState } from "react";
import { ApiError, api } from "../api/client";

type Check = { id: string; status: "PASS" | "FAIL" };
type Attestation = { run_id: string; observed_at: string; result: "PASS" | "FAIL"; read_only: boolean; checks: Check[]; redaction: string };
type Row = { id: string; status: "PASS" | "FAIL" | "UNKNOWN"; detail: string };
type ExpectedIdentity = "sovereign" | "non-sovereign";

function statusOf(error: unknown): number | null {
  return error instanceof ApiError ? error.status : null;
}

export function SecurityVerification() {
  const [running, setRunning] = useState(false);
  const [expectedIdentity, setExpectedIdentity] = useState<ExpectedIdentity>("sovereign");
  const [rows, setRows] = useState<Row[]>([]);
  const [attestation, setAttestation] = useState<Attestation | null>(null);
  const [message, setMessage] = useState("No verification has been run in this session.");

  async function run() {
    setRunning(true);
    setRows([]);
    setAttestation(null);
    setMessage("Running bounded authorization probes…");
    const next: Row[] = [];
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 12000);
    try {
      try {
        await api.get<Attestation>("/api/operator/security-verification", { auth: false, signal: controller.signal });
        next.push({ id: "anonymous_401", status: "FAIL", detail: "Unauthenticated request unexpectedly succeeded." });
      } catch (error) {
        const status = statusOf(error);
        next.push({
          id: "anonymous_401",
          status: status === 401 ? "PASS" : "FAIL",
          detail: status === 401 ? "Anonymous request rejected with HTTP 401." : `Expected HTTP 401; observed ${status ?? "no HTTP status"}.`,
        });
      }

      try {
        await api.get<Attestation>("/api/operator/security-verification", { token: "invalid.security-verification.token", signal: controller.signal });
        next.push({ id: "invalid_token_401", status: "FAIL", detail: "Invalid bearer token unexpectedly succeeded." });
      } catch (error) {
        const status = statusOf(error);
        next.push({
          id: "invalid_token_401",
          status: status === 401 ? "PASS" : "FAIL",
          detail: status === 401 ? "Invalid bearer token rejected with HTTP 401." : `Expected HTTP 401; observed ${status ?? "no HTTP status"}.`,
        });
      }

      try {
        const result = await api.get<Attestation>("/api/operator/security-verification", { signal: controller.signal });
        setAttestation(result);
        const accepted = expectedIdentity === "sovereign" && result.result === "PASS";
        next.push({
          id: expectedIdentity === "sovereign" ? "sovereign_200" : "non_sovereign_403",
          status: accepted ? "PASS" : "FAIL",
          detail: expectedIdentity === "sovereign"
            ? (accepted ? "Firebase-verified sovereign accepted with all runtime checks PASS." : "Sovereign response did not include an all-PASS attestation.")
            : "A non-sovereign test identity was expected to receive HTTP 403, but the server returned HTTP 200.",
        });
        for (const check of result.checks) {
          next.push({ id: check.id, status: check.status, detail: check.status === "PASS" ? "Confirmed by the running server." : "Not proven by the running server." });
        }
      } catch (error) {
        const status = statusOf(error);
        const expected403 = expectedIdentity === "non-sovereign" && status === 403;
        next.push({
          id: expectedIdentity === "sovereign" ? "sovereign_200" : "non_sovereign_403",
          status: expected403 ? "PASS" : "FAIL",
          detail: expected403
            ? "Firebase-authenticated non-sovereign identity rejected with HTTP 403."
            : expectedIdentity === "sovereign" && status === 403
              ? "Current identity is authenticated but lacks sovereign authorization. Switch to the authorized sovereign account."
              : `Expected ${expectedIdentity === "sovereign" ? "HTTP 200" : "HTTP 403"}; observed ${status ?? "no HTTP status"}.`,
        });
      }

      setRows(next);
      const passed = next.every((row) => row.status === "PASS");
      setMessage(passed
        ? (expectedIdentity === "sovereign"
          ? "Sovereign verification passed. Correlate the run ID below with Render logs."
          : "Authorization-denial probes passed. Repeat with the sovereign session to obtain the server attestation.")
        : "Verification has failed or unresolved checks. No credentials or caller identifiers were displayed.");
    } finally {
      window.clearTimeout(timeoutId);
      setRunning(false);
    }
  }

  function tone(status: string) {
    return status === "PASS" ? "demonstrated" : status === "FAIL" ? "contradicted" : "unresolved";
  }

  return <div className="grid" style={{ gap: 16 }}>
    <section className="card">
      <p className="small dim" style={{ marginTop: 0 }}>Read-only authorization verification. It tests an anonymous request, a deliberately invalid bearer token, and the current Arkadia session. The server validates real Firebase tokens; the console does not manufacture production identity.</p>
      <label htmlFor="expected-identity" className="small">Current session being tested</label>
      <select
        id="expected-identity"
        value={expectedIdentity}
        onChange={(event) => setExpectedIdentity(event.target.value as ExpectedIdentity)}
        disabled={running}
        style={{ display: "block", margin: "8px 0 12px", padding: "8px", maxWidth: 360 }}
      >
        <option value="sovereign">Authorized sovereign session (expect 200)</option>
        <option value="non-sovereign">Valid non-sovereign test session (expect 403)</option>
      </select>
      <p className="tiny faint">For the 403 test, first sign in to Arkadia as a real Firebase test identity whose server-side access level is below 3. This selector only states the expected result; it does not grant or simulate an identity.</p>
      <p className="tiny faint">No token, secret, UID, email, or raw exception is displayed. The action makes no configuration changes and executes no mutations.</p>
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
