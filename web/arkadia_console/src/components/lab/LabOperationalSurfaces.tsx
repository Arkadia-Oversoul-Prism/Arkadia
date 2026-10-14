/**
 * Engineering Lab — operational read surfaces (Workstream 4, feature-local).
 *
 * `GET /api/lab/engineering/overview` returns four truthful sub-reports built by
 * the Lab's own modules. The page used to fold them into one
 * `Object.entries(...).slice(0, 12)` JSON blob, so the distinctions those reports
 * exist to state — UNAVAILABLE vs AVAILABLE, AVAILABLE vs AUTHORIZATION_REQUIRED,
 * "a transcript is not an authorization" — were presented as an opaque string, or
 * dropped past the twelve-key cut. This surface renders each report as its own
 * labelled reading.
 *
 * Ownership: the overview's automation-grammar render is owned by the sibling
 * Lane-4 slice (PR #493); this surface deliberately renders only the other three
 * sub-reports. See `labOperational.ts` for the projection.
 *
 * Read-only by construction: it takes the already-fetched overview object and
 * issues no request of its own. Nothing here is a control — every value is a
 * fact the backend authored, surfaced through `labOperational.ts` so an
 * undeclared field reads UNKNOWN rather than a blank.
 */
import { Panel, Facts } from "../ui";
import {
  buildAndroidLedger,
  buildIntegrationLedger,
  buildVoiceLedger,
  readOperationalReadings,
  type AndroidLedger,
  type IntegrationLedger,
  type VoiceLedger,
} from "./labOperational";

function ChipList({ values }: { values: string[] }) {
  if (values.length === 0) return <span className="text-white/40">none declared</span>;
  return (
    <span className="flex flex-wrap gap-1">
      {values.map((v) => (
        <span key={v} className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-white/70">
          {v}
        </span>
      ))}
    </span>
  );
}

function IntegrationsPanel({ ledger }: { ledger: IntegrationLedger }) {
  return (
    <Panel className="mb-4">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        External integrations (provider adapters)
      </p>
      {ledger.adapters.length === 0 ? (
        <p className="text-sm text-white/55" data-testid="lab-integrations-empty">
          The overview returned no provider adapters. None is inferred.
        </p>
      ) : (
        <Facts
          rows={ledger.adapters.map((a) => ({
            label: a.provider,
            value: (
              <span data-testid={`lab-integration-${a.provider}`}>
                <span className="font-mono text-[11px] text-white/70">{a.state}</span>
                <span className="ml-2 text-white/55">{a.detail}</span>
              </span>
            ),
          }))}
        />
      )}
      <p className="mt-3 text-xs text-white/40">
        {ledger.note} · {ledger.counts.available}/{ledger.counts.adapters} available · generated {ledger.generated_at}
      </p>
    </Panel>
  );
}

function AndroidPanel({ ledger }: { ledger: AndroidLedger }) {
  return (
    <Panel className="mb-4">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Android control plane (capability projection)
      </p>
      <Facts
        rows={[
          { label: "surface", value: ledger.surface },
          { label: "execution", value: ledger.execution_location },
          { label: "android-local required", value: ledger.android_local_execution_required },
          {
            label: "authority layer",
            value: ledger.authority.android_is_not_an_authority_layer,
          },
          { label: "merge exposed", value: ledger.authority.merge_exposed },
          { label: "deploy exposed", value: ledger.authority.deploy_exposed },
        ]}
      />
      <p className="mt-3 mb-2 font-mono text-[10px] uppercase tracking-wider text-white/35">
        capabilities ({ledger.counts.available} available · {ledger.counts.authorization_required} authorization-required)
      </p>
      <Facts
        rows={ledger.capabilities.map((c) => ({
          label: c.capability,
          value: (
            <span data-testid={`lab-android-${c.capability}`} className="font-mono text-[11px] text-white/70">
              {c.state}
            </span>
          ),
        }))}
      />
      <p className="mt-3 text-xs text-white/40">
        This is a projection of the bounded server's capabilities. The phone is not an authority layer, and no
        capability here is a grant.
      </p>
    </Panel>
  );
}

function VoicePanel({ ledger }: { ledger: VoiceLedger }) {
  return (
    <Panel className="mb-4">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Voice boundary (transcript ≠ authorization)
      </p>
      <Facts
        rows={[
          { label: "recognizer", value: `${ledger.recognizer_state} (configured: ${ledger.recognizer_configured})` },
          { label: "detail", value: ledger.detail },
          { label: "human authority preserved", value: ledger.human_authority_preserved },
          { label: "assistant hidden authority", value: ledger.assistant_is_hidden_authority },
          { label: "intents", value: <ChipList values={ledger.intents} /> },
          { label: "human-only intents", value: <ChipList values={ledger.human_only_intents} /> },
        ]}
      />
      <p className="mt-3 text-xs text-white/40" data-testid="lab-voice-non-collapse">
        Boundary: {ledger.non_collapse}
      </p>
    </Panel>
  );
}

/**
 * Render the operational sub-reports carried by the Lab overview.
 *
 * Scope note (parallel-UI ownership): the overview also carries an automation
 * grammar, but rendering that is owned by the sibling Lane-4 slice (PR #493), so
 * this surface renders only the three projections that slice does not:
 * `integrations`, `android`, and `voice`.
 */
export function LabOperationalSurfaces({ overview }: { overview: Record<string, unknown> | null }) {
  if (overview === null) {
    return (
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Lab operational readings</p>
        <p className="text-sm text-white/55" data-testid="lab-operational-absent">
          The Lab overview did not return, so no operational reading is shown. Nothing is inferred.
        </p>
      </Panel>
    );
  }

  const readings = readOperationalReadings(overview);
  return (
    <>
      <IntegrationsPanel ledger={readings.integrations} />
      {readings.android ? (
        <AndroidPanel ledger={readings.android} />
      ) : (
        <Panel className="mb-4">
          <p className="text-sm text-white/55" data-testid="lab-android-absent">
            Android control plane: the overview did not carry this reading. Nothing is inferred.
          </p>
        </Panel>
      )}
      {readings.voice ? (
        <VoicePanel ledger={readings.voice} />
      ) : (
        <Panel className="mb-4">
          <p className="text-sm text-white/55" data-testid="lab-voice-absent">
            Voice boundary: the overview did not carry this reading. Nothing is inferred.
          </p>
        </Panel>
      )}
    </>
  );
}

// Re-exports so callers can reach the pure builders from one module.
export { buildAndroidLedger, buildIntegrationLedger, buildVoiceLedger, readOperationalReadings };
