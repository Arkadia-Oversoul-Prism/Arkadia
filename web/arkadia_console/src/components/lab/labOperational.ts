/**
 * Engineering Lab — operational projections (Workstream 4, feature-local, pure).
 *
 * `GET /api/lab/engineering/overview` already returns four truthful sub-reports
 * (`integrations`, `android`, `voice`, `automation_grammar`) alongside the
 * session/agent counts. The page previously dropped them into a raw JSON string
 * (`Object.entries(...).slice(0, 12)`), so the readings the backend took care to
 * make truthful were rendered as an unlabelled blob — or omitted entirely once
 * the overview grew past twelve keys.
 *
 * This module is dependency-free so it can be *executed* (not merely read) under
 * Node by the contract test, and it is pure: it takes the handler's own output
 * and returns a ledger. No field is invented, and a value the backend does not
 * declare is *stated* as UNKNOWN rather than defaulted to a healthy one.
 */

// ---------------------------------------------------------------------------
// Truthful sentinels — a missing value is stated, never promoted
// ---------------------------------------------------------------------------

/** Render an undeclared value as an explicit sentinel rather than a blank. */
function fact(value: unknown): string {
  if (value === null || value === undefined) return "UNKNOWN";
  if (typeof value === "string") return value.length > 0 ? value : "UNKNOWN";
  return String(value);
}

/** A boolean the backend did not state must not read as a stance. */
function label(value: unknown): "yes" | "no" | "UNKNOWN" {
  if (value === true) return "yes";
  if (value === false) return "no";
  return "UNKNOWN";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asStrings(value: unknown): string[] {
  return asArray(value).filter((v): v is string => typeof v === "string");
}

// ---------------------------------------------------------------------------
// Integrations — external services stay authoritative for their own data
// ---------------------------------------------------------------------------

export interface IntegrationFact {
  provider: string;
  state: string;
  detail: string;
  credential_source: string;
}

export interface IntegrationLedger {
  /** The handler's own `generated_at`, or UNKNOWN when it did not state one. */
  generated_at: string;
  /** The handler's non-collapse note, verbatim, or UNKNOWN. */
  note: string;
  adapters: IntegrationFact[];
  counts: { adapters: number; available: number };
}

/**
 * Project `describe_integrations()["adapters"]`.
 *
 * The handler keys its adapters by name; the console reads the name as
 * `provider` so the surface does not depend on the dict key. No adapter is
 * probed from the console — this is a description the handler already took.
 */
export function buildIntegrationLedger(detail: Record<string, unknown>): IntegrationLedger {
  const adapters = asRecord(detail["adapters"]);
  const rows: IntegrationFact[] = Object.entries(adapters).map(([name, raw]) => {
    const entry = asRecord(raw);
    return {
      provider: fact(entry["provider"] ?? name),
      state: fact(entry["state"]),
      detail: fact(entry["detail"]),
      credential_source: fact(entry["credential_source"]),
    };
  });
  return {
    generated_at: fact(detail["generated_at"]),
    note: fact(detail["note"]),
    adapters: rows,
    counts: {
      adapters: rows.length,
      available: rows.filter((r) => r.state === "AVAILABLE").length,
    },
  };
}

// ---------------------------------------------------------------------------
// Android control plane — a projection, never an authority layer
// ---------------------------------------------------------------------------

export interface AndroidCapability {
  capability: string;
  state: string;
  human_only: boolean;
}

export interface AndroidLedger {
  surface: string;
  execution_location: string;
  android_local_execution_required: string;
  capabilities: AndroidCapability[];
  counts: { capabilities: number; available: number; authorization_required: number };
  authority: {
    android_is_not_an_authority_layer: string;
    /** Whether the control plane exposes the human-only act. Taken from the report. */
    merge_exposed: string;
    deploy_exposed: string;
  };
}

/** Project `android_capability_report()`. */
export function buildAndroidLedger(detail: Record<string, unknown>): AndroidLedger {
  const rows: AndroidCapability[] = asArray(detail["capabilities"]).map((raw) => {
    const entry = asRecord(raw);
    return {
      capability: fact(entry["capability"]),
      state: fact(entry["state"]),
      human_only: asStrings(entry["human_only_never_exposed"]).length === 0,
    };
  });
  const authority = asRecord(detail["authority"]);
  return {
    surface: fact(detail["surface"]),
    execution_location: fact(detail["execution_location"]),
    android_local_execution_required: label(detail["android_local_execution_required"]),
    capabilities: rows,
    counts: {
      capabilities: rows.length,
      available: rows.filter((r) => r.state === "AVAILABLE").length,
      authorization_required: rows.filter((r) => r.state === "AUTHORIZATION_REQUIRED").length,
    },
    authority: {
      android_is_not_an_authority_layer: label(authority["android_is_not_an_authority_layer"]),
      merge_exposed: label(authority["merge_exposed"]),
      deploy_exposed: label(authority["deploy_exposed"]),
    },
  };
}

// ---------------------------------------------------------------------------
// Voice boundary — a transcript is not an authorization
// ---------------------------------------------------------------------------

export interface VoiceLedger {
  surface: string;
  provider_neutral: string;
  recognizer_state: string;
  recognizer_configured: string;
  detail: string;
  human_authority_preserved: string;
  assistant_is_hidden_authority: string;
  /** The boundary's own non-collapse phrase, verbatim, or UNKNOWN. */
  non_collapse: string;
  intents: string[];
  human_only_intents: string[];
}

/** Project `voice_boundary_report()`. */
export function buildVoiceLedger(detail: Record<string, unknown>): VoiceLedger {
  return {
    surface: fact(detail["surface"]),
    provider_neutral: label(detail["provider_neutral"]),
    recognizer_state: fact(detail["recognizer_state"]),
    recognizer_configured: label(detail["recognizer_configured"]),
    detail: fact(detail["detail"]),
    human_authority_preserved: label(detail["human_authority_preserved"]),
    assistant_is_hidden_authority: label(detail["assistant_is_hidden_authority"]),
    non_collapse: fact(detail["non_collapse"]),
    intents: asStrings(detail["intents"]),
    human_only_intents: asStrings(detail["human_only_intents"]),
  };
}

// ---------------------------------------------------------------------------
// Operational ledger — the four reports the overview carries
// ---------------------------------------------------------------------------

export interface OperationalReadings {
  integrations: IntegrationLedger;
  android: AndroidLedger | null;
  voice: VoiceLedger | null;
}

/**
 * Read the operational sub-reports out of the overview response.
 *
 * A sub-report the handler did not carry reads `null` rather than an
 * empty-but-plausible default, so the surface can say the reading is absent
 * instead of rendering a healthy-looking blank. `integrations` is always built
 * so a missing key reports zero adapters rather than vanishing.
 *
 * The overview's `automation_grammar` is deliberately not read here: rendering it
 * belongs to the sibling Lane-4 slice (`LabAutomationGrammar.tsx`), so this module
 * stays out of that file's territory.
 */
export function readOperationalReadings(overview: Record<string, unknown> | null): OperationalReadings {
  const source = overview ?? {};
  const asMaybeRecord = (v: unknown): Record<string, unknown> | null =>
    v !== null && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
  return {
    integrations: buildIntegrationLedger(asRecord(source["integrations"])),
    android: asMaybeRecord(source["android"]) ? buildAndroidLedger(asRecord(source["android"])) : null,
    voice: asMaybeRecord(source["voice"]) ? buildVoiceLedger(asRecord(source["voice"])) : null,
  };
}

/**
 * The top-level overview keys that are *not* a scalar fact.
 *
 * These are the container/feature keys the overview carries directly
 * (`automation_grammar` is rendered by the sibling Lane-4 slice; the other three
 * by this surface). They are removed from `scalarOverview` so a raw JSON dump
 * cannot re-emit them as an unlabelled blob.
 */
export const OPERATIONAL_KEYS = ["integrations", "android", "voice", "automation_grammar"] as const;

/** The scalars the overview carries directly, sub-reports removed. */
export function scalarOverview(overview: Record<string, unknown> | null): Array<{ label: string; value: string }> {
  const source = overview ?? {};
  return Object.entries(source)
    .filter(([key]) => !(OPERATIONAL_KEYS as readonly string[]).includes(key))
    .map(([key, value]) => ({
      label: key,
      value: value !== null && typeof value === "object" ? JSON.stringify(value) : fact(value),
    }));
}
