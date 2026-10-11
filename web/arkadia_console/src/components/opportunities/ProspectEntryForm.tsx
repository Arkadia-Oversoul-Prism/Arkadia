/**
 * Prospect entry — create/edit control for one project opportunity board.
 *
 * Backed only by the two verified write handlers in `solspire/buyer_recon_router.py`:
 *
 *   POST  /solspire/buyer-recon/projects/{project_id}/entries
 *   PATCH /solspire/buyer-recon/projects/{project_id}/entries/{entry_id}
 *
 * Both are declared on the `/solspire` router, which carries
 * `dependencies=[Depends(require_auth)]`, and the project routes additionally
 * enforce ownership through `require_project_owner` (a non-owner receives `404`,
 * not an empty board). This control never invents a route, a method, or a field:
 * the paths come from the contract module, and the body is built from the
 * handler's own `BuyerReconEntryInput` / `BuyerReconEntryPatch` declarations.
 *
 * Truthfulness rules this control holds to:
 *
 *  * An unverified commercial fact stays `UNKNOWN`. Commercial inputs default to
 *    the backend's own sentinel and are **omitted from the body** when left
 *    there, so the server applies its default rather than the client asserting a
 *    value it does not hold.
 *  * Nothing is recorded until the server confirms it. The saved entry is the
 *    one the response carried (`{"entry": {...}}`), never the submitted draft.
 *  * `evidence_status` and `evidence` are never sent. Capturing a prospect does
 *    not assert that evidence exists, so the backend's `NONE` / `[]` stand.
 *  * There is no delete, bulk, spend, approve, or execute control. Those have no
 *    verified handler and would imply authority this surface does not have.
 */
import { useState, type FormEvent } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { Panel } from "../ui";
import {
  COMMERCIAL_FIELDS,
  DESCRIPTIVE_FIELDS,
  SETTABLE_STATUSES,
  UNVERIFIED,
  createEntryBody,
  draftFromEntry,
  editEntryBody,
  emptyDraft,
  isSettableStatus,
  entriesPathFromBoard,
  entryPathFromBoard,
  isNoOpEdit,
  parseEntryResponse,
  prospectRequired,
  type OpportunityEntry,
  type ProspectDraft,
} from "./opportunityRadarContract";

const FIELD_LABELS: Record<string, string> = {
  location: "Location",
  buyer_type: "Buyer type",
  contact_route: "Contact route",
  commodity: "Commodity",
  estimated_demand: "Estimated demand",
  procurement_frequency: "Procurement frequency",
  decision_maker: "Decision maker",
  current_price: "Current price",
  quantity: "Quantity",
  specification: "Specification",
  delivery_point: "Delivery point",
  delivery_window: "Delivery window",
  payment_terms: "Payment terms",
  supplier: "Supplier",
  source_price: "Source price",
  available_quantity: "Available quantity",
  logistics_quote: "Logistics quote",
  packaging_qc_cost: "Packaging / QC cost",
  landed_cost: "Landed cost",
  buyer_price: "Buyer price",
  expected_gross_margin: "Expected gross margin",
  capital_required: "Capital required",
};

type SaveState =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved"; entry: OpportunityEntry }
  | { kind: "invalid"; message: string }
  | { kind: "auth"; message: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

const inputClass =
  "min-w-0 rounded border border-line bg-ink/50 px-2 py-1 text-sm text-white/85 outline-none focus:border-emerald/50";

export function ProspectEntryForm({
  boardPath,
  mode,
  entry,
  onSaved,
  onCancel,
}: {
  boardPath: string;
  mode: "create" | "edit";
  entry?: OpportunityEntry;
  onSaved: (entry: OpportunityEntry) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<ProspectDraft>(() =>
    mode === "edit" && entry ? draftFromEntry(entry) : emptyDraft(),
  );
  const [state, setState] = useState<SaveState>({ kind: "idle" });

  function update(field: keyof ProspectDraft, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state.kind === "saving") return;

    // A blank prospect is the one server rule the operator can break locally
    // (`create_entry` raises `ValueError("prospect is required")`). Explain it
    // here; the server remains the authority and still refuses it.
    const missing = mode === "create" ? prospectRequired(draft) : null;
    if (missing) {
      setState({ kind: "invalid", message: missing });
      return;
    }

    const body = mode === "create" ? createEntryBody(draft) : editEntryBody(draft, entry);
    if (mode === "edit" && Object.keys(body).length === 0) {
      // Nothing changed. Say so rather than issuing a write that records nothing.
      setState({ kind: "invalid", message: "No change to save — every field still matches the recorded entry." });
      return;
    }

    const path =
      mode === "create"
        ? entriesPathFromBoard(boardPath)
        : entryPathFromBoard(boardPath, entry?.id ?? "");

    setState({ kind: "saving" });
    try {
      const payload = await apiRequest<unknown>(path, {
        method: mode === "create" ? "POST" : "PATCH",
        body: JSON.stringify(body),
      });
      const saved = parseEntryResponse(payload);
      if (!saved) {
        // A body without the declared `entry` key is an unrecognised shape, not
        // a successful empty write — never treat it as one.
        setState({
          kind: "error",
          message: "The board returned an unrecognised response shape. The write was not confirmed.",
        });
        return;
      }
      setState({ kind: "saved", entry: saved });
      onSaved(saved);
    } catch (caught: unknown) {
      const error = caught instanceof ApiError ? caught : null;
      const message = error?.message ?? (caught instanceof Error ? caught.message : "Request failed.");
      if (error?.kind === "AUTH_REQUIRED" || error?.kind === "FORBIDDEN") {
        setState({ kind: "auth", message: "Sign in with access to this project to record a prospect." });
      } else if (error?.kind === "NOT_FOUND") {
        // The project routes return 404 for a non-owner as well as for a missing
        // entry, so the message must not assert which of the two it was.
        setState({
          kind: "auth",
          message:
            mode === "create"
              ? "This project is not available to this identity, so no prospect was recorded."
              : "This entry is not available on this board, so nothing was changed.",
        });
      } else if (error?.kind === "BAD_REQUEST" || error?.kind === "UNPROCESSABLE") {
        setState({ kind: "invalid", message: message || "The board refused this entry." });
      } else if (error?.kind === "NETWORK_ERROR" || error?.kind === "SERVER_ERROR") {
        setState({ kind: "unavailable", message: "The board could not be reached. Nothing was recorded." });
      } else {
        setState({ kind: "error", message });
      }
    }
  }

  const title = mode === "create" ? "Record a prospect" : `Edit prospect`;

  return (
    <Panel data-testid={`prospect-entry-form-${mode}`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">
            {mode === "create" ? "Capture demand" : "Edit recorded prospect"}
          </p>
          <p className="mt-1 text-sm text-white/60">
            {title}. An unverified commercial fact stays {UNVERIFIED} until it is recorded — this
            control asserts no price, demand, or commitment of its own.
          </p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-line px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-white/60"
        >
          {mode === "create" ? "Cancel" : "Close"}
        </button>
      </div>

      <form onSubmit={(event) => void save(event)} className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="prospect-entry-prospect" className="font-mono text-[10px] uppercase tracking-widest text-white/45">
            Prospect
          </label>
          <input
            id="prospect-entry-prospect"
            data-testid="prospect-entry-prospect"
            value={draft.prospect}
            onChange={(event) => update("prospect", event.target.value)}
            placeholder="Buyer / prospect"
            className={inputClass}
          />
        </div>

        <fieldset className="grid gap-2 sm:grid-cols-2">
          <legend className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
            Described, not verified
          </legend>
          {DESCRIPTIVE_FIELDS.filter((field) => field !== "why_this_prospect" && field !== "notes").map((field) => (
            <div key={field} className="flex flex-col gap-1">
              <label htmlFor={`prospect-entry-${field}`} className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                {FIELD_LABELS[field] ?? field}
              </label>
              <input
                id={`prospect-entry-${field}`}
                data-testid={`prospect-entry-${field}`}
                value={draft[field]}
                onChange={(event) => update(field, event.target.value)}
                placeholder="Not recorded"
                className={inputClass}
              />
            </div>
          ))}
        </fieldset>

        <details className="rounded border border-line/60 p-3" data-testid="prospect-entry-commercial">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-widest text-white/45">
            Commercial facts · unverified until recorded
          </summary>
          <p className="mt-2 text-xs text-white/45">
            Leave a field at {UNVERIFIED} to keep it unverified. Unverified fields are not sent, so the
            board keeps its own {UNVERIFIED} default.
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {COMMERCIAL_FIELDS.map((field) => (
              <div key={field} className="flex flex-col gap-1">
                <label htmlFor={`prospect-entry-${field}`} className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                  {FIELD_LABELS[field] ?? field}
                </label>
                <input
                  id={`prospect-entry-${field}`}
                  data-testid={`prospect-entry-${field}`}
                  value={draft[field]}
                  onChange={(event) => update(field, event.target.value)}
                  placeholder={UNVERIFIED}
                  className={inputClass}
                />
              </div>
            ))}
          </div>
        </details>

        <div className="flex flex-col gap-1">
          <label htmlFor="prospect-entry-why" className="font-mono text-[10px] uppercase tracking-widest text-white/40">
            Why this prospect
          </label>
          <textarea
            id="prospect-entry-why"
            data-testid="prospect-entry-why"
            value={draft.why_this_prospect}
            onChange={(event) => update("why_this_prospect", event.target.value)}
            rows={2}
            className={inputClass}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="prospect-entry-notes" className="font-mono text-[10px] uppercase tracking-widest text-white/40">
            Notes
          </label>
          <textarea
            id="prospect-entry-notes"
            data-testid="prospect-entry-notes"
            value={draft.notes}
            onChange={(event) => update("notes", event.target.value)}
            rows={2}
            className={inputClass}
          />
        </div>

        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label htmlFor="prospect-entry-status" className="font-mono text-[10px] uppercase tracking-widest text-white/40">
            Pipeline status
          </label>
          {isSettableStatus(draft.status) ? (
            <select
              id="prospect-entry-status"
              data-testid="prospect-entry-status"
              value={draft.status}
              onChange={(event) => update("status", event.target.value)}
              className={inputClass}
            >
              {SETTABLE_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          ) : (
            <>
              <input
                id="prospect-entry-status"
                data-testid="prospect-entry-status"
                readOnly
                value={draft.status}
                aria-describedby="prospect-entry-status-locked"
                className={inputClass}
              />
              <p id="prospect-entry-status-locked" className="text-[11px] text-amber-300/80">
                This entry records a transaction outcome. It cannot be changed from reconnaissance.
              </p>
            </>
          )}
          <p className="text-[11px] text-white/35">
            Recording a status is reconnaissance. It authorizes no spending, approval, or execution.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            data-testid="prospect-entry-submit"
            disabled={state.kind === "saving"}
            className="rounded border border-emerald/40 px-4 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald disabled:opacity-40"
          >
            {state.kind === "saving" ? "Saving…" : mode === "create" ? "Record prospect" : "Save changes"}
          </button>
          {mode === "edit" && entry && isNoOpEdit(draft, entry) && state.kind !== "saving" && (
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/35">No changes yet</span>
          )}
        </div>
      </form>

      {state.kind === "invalid" && (
        <p role="alert" data-testid="prospect-entry-invalid" className="mt-3 rounded border border-gold/30 p-3 text-sm text-gold">
          {state.message}
        </p>
      )}
      {state.kind === "auth" && (
        <p role="alert" data-testid="prospect-entry-auth" className="mt-3 rounded border border-gold/30 p-3 text-sm text-gold">
          {state.message}
        </p>
      )}
      {state.kind === "unavailable" && (
        <p role="alert" data-testid="prospect-entry-unavailable" className="mt-3 rounded border border-gold/30 p-3 text-sm text-gold">
          {state.message}
        </p>
      )}
      {state.kind === "error" && (
        <p role="alert" data-testid="prospect-entry-error" className="mt-3 rounded border border-rose-300/30 p-3 text-sm text-rose-300">
          {state.message}
        </p>
      )}
      {state.kind === "saved" && (
        <p role="status" data-testid="prospect-entry-saved" className="mt-3 rounded border border-emerald/30 p-3 text-sm text-emerald">
          {mode === "create" ? "Recorded by the board" : "Saved by the board"}: {state.entry.prospect} ·{" "}
          {state.entry.status} · evidence {state.entry.evidence_status}
        </p>
      )}
    </Panel>
  );
}
