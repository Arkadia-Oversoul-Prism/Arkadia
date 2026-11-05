/**
 * Engineering Lab — PR state surface (Workstream 4, feature-local).
 *
 * Renders `GET /api/lab/engineering/pr/{number}` (`api.lab_routes.pr_state`,
 * EL-10) through the pure projection in `labPrState.ts`.
 *
 * Read-only by construction: GET only. GitHub remains the repository authority;
 * this surface reads what the handler reports and never merges, reviews,
 * approves, or claims acceptance. It shows the handler's own two states —
 * AVAILABLE (a record was read) and UNAVAILABLE (with the handler's reason) —
 * and never converts "we could not read it" into "there is no PR" or into a
 * mergeability claim.
 *
 * The number is a validated, encoded path segment; an invalid entry issues no
 * request at all and is reported as not a PR number.
 *
 * The read path is *derived from* the shared endpoint registry rather than
 * written here (SHARED-CONTRACTS §3.1). This surface names the handler and the
 * path segment it composes; `src/lib/endpoints.ts` owns the exact route template. Because that
 * file is Lane 1's, this surface consumes it and does not edit it — the
 * `labEngineeringPr` entry is requested through the interface-request process in
 * `docs/control-plane/evidence/lane4-lab-pr-state-surface-01/EVIDENCE.md`.
 */
import { useState } from "react";
import { endpoints } from "../../lib/endpoints";
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import {
  lifecyclePhrase,
  prStatePath,
  readPrState,
  reported,
  type LabPrStatePayload,
} from "./labPrState";

function Reading({ payload }: { payload: LabPrStatePayload | null }) {
  const reading = readPrState(payload);

  if (reading.availability === "UNAVAILABLE") {
    return (
      <div className="mt-3" data-testid="lab-pr-unavailable">
        <Facts
          rows={[
            { label: "state", value: reading.availability },
            { label: "detail", value: reading.detail ?? "the handler gave no detail" },
          ]}
        />
        <p className="mt-2 text-xs text-white/45">
          The Lab could not read this pull request. That is not an absence of pull requests, and it is not a
          mergeability reading.
        </p>
      </div>
    );
  }

  if (!reading.hasRecord) {
    return (
      <p className="mt-3 text-sm text-white/55" data-testid="lab-pr-unknown">
        The handler did not return a pull-request record, so no state is reported. Nothing is inferred from
        the absence.
      </p>
    );
  }

  return (
    <div className="mt-3" data-testid="lab-pr-reading">
      <Facts
        rows={[
          { label: "lifecycle", value: lifecyclePhrase(reading) },
          { label: "mergeable_state", value: reported(reading.mergeableState) },
          { label: "head", value: reported(reading.head) },
          { label: "base", value: reported(reading.base) },
        ]}
      />
      {reading.htmlUrl ? (
        <a
          className="mt-2 inline-block font-mono text-xs text-azure underline decoration-dotted"
          href={reading.htmlUrl}
          target="_blank"
          rel="noreferrer"
          data-testid="lab-pr-link"
        >
          open on GitHub
        </a>
      ) : null}
      <p className="mt-2 text-xs text-white/45" data-testid="lab-pr-non-collapse">
        Reachable is not mergeable, and GitHub remains the repository authority. This surface reads state; it
        cannot merge, review, approve, or accept anything.
      </p>
    </div>
  );
}

/**
 * The read path's exact route template comes from the shared endpoint registry
 * (`src/lib/endpoints.ts`, Lane 1's file) rather than being written here, so the
 * console keeps one endpoint contract (SHARED-CONTRACTS §3.1). When the registry
 * declares the template, pass it in:
 *
 *   <LabPrState pathTemplate={endpoints.labEngineeringPr} />
 *
 * Until then the surface renders a not-wired state and issues no request, rather
 * than inlining a second, unreviewed path.
 */
export function LabPrState({ pathTemplate }: { pathTemplate?: string }) {
  // The input is uncommitted: the handler performs a live GitHub read, so a
  // request is issued on submit rather than on every keystroke.
  const [number, setNumber] = useState("");
  const [target, setTarget] = useState<string | null>(null);

  // The exact route template is the registry's; this surface validates the number. The registry
  // is `as const` and Lane 1 has not declared the entry yet, so it is read
  // optionally: until the entry lands this is `undefined`, no path is built, and
  // the surface renders its not-wired state instead of issuing a request.
  const registry = endpoints as Partial<Record<string, string>>;
  const template = pathTemplate ?? registry.labEngineeringPr;
  const path = target === null || !template ? null : prStatePath(template, target);
  const pr = useHydration<LabPrStatePayload>(path ?? "", (p) =>
    p ? apiRequest<LabPrStatePayload>(p) : Promise.resolve({ state: null, detail: null, pr: null }),
  );

  const submit = () => setTarget(number);

  return (
    <Panel className="mb-4">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Pull-request state (read-only)
      </p>

      {!template ? (
        <p className="mt-3 text-sm text-white/55" data-testid="lab-pr-not-wired">
          This read is not wired yet: the shared endpoint registry does not declare the pull-request
          route template, and this surface does not inline one. No request is issued.
        </p>
      ) : (
      <form
        className="flex flex-wrap items-center gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label htmlFor="lab-pr-number" className="font-mono text-[11px] uppercase tracking-widest text-white/40">
          PR number
        </label>
        <input
          id="lab-pr-number"
          data-testid="lab-pr-number"
          inputMode="numeric"
          value={number}
          onChange={(event) => setNumber(event.target.value)}
          placeholder="e.g. 623"
          className="w-28 rounded border border-line bg-ink/60 px-2 py-1 font-mono text-[11px] text-white/80"
        />
        <button
          type="submit"
          data-testid="lab-pr-read"
          className="rounded border border-line bg-ink/60 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-white/70 hover:text-white"
        >
          Read state
        </button>
      </form>
      )}

      {!template ? null : target === null ? (
        <p className="mt-3 text-sm text-white/55" data-testid="lab-pr-invalid">
          Enter a pull-request number to read its recorded state.
        </p>
      ) : path === null ? (
        <p className="mt-3 text-sm text-white/55" data-testid="lab-pr-invalid">
          {`"${target}" is not a pull-request number, so no request was made.`}
        </p>
      ) : (
        <div data-testid="lab-pr-result">
          {pr.state === "ready" ? (
            <Reading payload={pr.data} />
          ) : (
            <ContractState state={pr.state} error={pr.error?.message} onRetry={pr.reload} />
          )}
        </div>
      )}
    </Panel>
  );
}
