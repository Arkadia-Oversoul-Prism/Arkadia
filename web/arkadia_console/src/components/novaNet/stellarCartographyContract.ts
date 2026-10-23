/**
 * Stellar Cartography contract (feature-local).
 *
 * The shape `GET /api/stellar-cartography` actually returns, measured against
 * the canonical deployment (`200` anonymously, no identity required) rather than
 * inferred from the archived UI. `kernel/stellar.py::readout()` builds it and
 * `api/main.py:1648` returns it verbatim, so the fields below are the kernel's
 * own keys.
 *
 * The endpoint is the *Encyclopedia Galactica* living star-date readout: the Ark
 * Date, Schumann resonance, lunar phase, planetary sky ("bone report"), cosmic
 * weather, an Oversoul blind-pull transmission, and the volume index. The archive
 * mounted it as the header of `NexusSpiralCodex`
 * (`archive/.../src/pages/NexusSpiralCodex.tsx:953`), which is the surface the
 * console now expresses as the NovaNet `codex` lens.
 *
 * Two properties are load-bearing:
 *
 * 1. **The readout is server-derived and time-varying.** `ark_date.pulse` and
 *    `breath` are 0–11 / 0–47 clock subdivisions and `total_ark_day` advances at
 *    the Ark-day boundary, so the value is a *snapshot*, not a constant. Nothing
 *    here may be computed client-side from `Date.now()` — the kernel's epoch
 *    ("March 31 2026 — Birthday Seal") is not a UTC calendar derivation, and a
 *    client-side copy would silently disagree with the server's own readout.
 *
 * 2. **The Oversoul transmission is deliberately not attributable to a person.**
 *    `method` reads "blind-pull · rotated by Ark Day": the text is selected by
 *    the day index, so it is shared and reproducible, not a private message.
 *    It is presented as the day's transmission, never as guidance for a reader.
 */

/** The Ark Date — the primary coordinate. */
export interface ArkDate {
  ark_year: number;
  ark_total_years: number;
  day_in_year: number;
  total_ark_day: number;
  /** 0–11 clock subdivision. */
  pulse: number;
  /** 0–47 clock subdivision. */
  breath: number;
  ark_completion_pct: number;
  /** Prose form, e.g. "Ark Year 1 of 8 · Day 207 · 09:33". */
  coordinate: string;
  /** Compact form, e.g. "ARK Y1 · D207 · 09:33". */
  display: string;
  epoch: string;
  linear_utc: string;
  linear_note: string;
}

export interface SchumannBand {
  hz: number;
  name: string;
}

export interface Schumann {
  bands: SchumannBand[];
  dominant_hz: number;
  dominant_name: string;
  quality: string;
  dominant_index: number;
}

export interface Lunar {
  phase: string;
  glyph: string;
  meaning: string;
  illumination_pct: number;
  moon_name: string;
  phase_fraction: number;
  age_days: number;
}

export interface PlanetaryBody {
  sign: string;
  glyph: string;
  meaning: string;
  longitude: number;
}

export interface Planetary {
  bodies: Record<string, PlanetaryBody>;
  sun_sign: string;
  moon_sign: string;
  bone_report: string;
  zodiac: Array<{ name: string; glyph: string; meaning: string }>;
}

export interface CosmicWeather {
  solar_wind_kms: number;
  kp_index: number;
  solar_flux: number;
  geomagnetic_pressure: string;
  mood: string;
}

export interface OversoulBlindPull {
  transmission: string;
  pull_index: number;
  method: string;
}

export interface GalacticaVolume {
  volume: string;
  title: string;
  domain: string;
}

export interface Galactica {
  volumes: GalacticaVolume[];
  current_volume: string;
  total_volumes: number;
}

/** `GET /api/stellar-cartography` response envelope. */
export interface StellarReadout {
  ark_date: ArkDate;
  schumann: Schumann;
  lunar: Lunar;
  planetary: Planetary;
  cosmic_weather: CosmicWeather;
  oversoul_blind_pull: OversoulBlindPull;
  galactica: Galactica;
  timestamp_utc: string;
}

/**
 * Whether a payload is structurally usable.
 *
 * The panel reads seven nested sections and would otherwise render "undefined"
 * for a truncated or errored response. A shape check is honest about *which*
 * read failed rather than letting the component throw during render.
 */
export function isStellarReadout(value: unknown): value is StellarReadout {
  if (!value || typeof value !== "object") return false;
  const r = value as Partial<StellarReadout>;
  return Boolean(
    r.ark_date &&
      typeof r.ark_date.display === "string" &&
      r.schumann &&
      Array.isArray(r.schumann.bands) &&
      r.lunar &&
      typeof r.lunar.phase === "string" &&
      r.planetary &&
      typeof r.planetary.bone_report === "string" &&
      r.cosmic_weather &&
      typeof r.cosmic_weather.mood === "string" &&
      r.oversoul_blind_pull &&
      typeof r.oversoul_blind_pull.transmission === "string" &&
      r.galactica &&
      Array.isArray(r.galactica.volumes),
  );
}

/**
 * The moon glyph, falling back to a neutral mark when the kernel omits it.
 *
 * `lunar.glyph` is an emoji the kernel supplies; a response without one must not
 * render as the literal string "undefined" in the readout.
 */
export function lunarGlyph(lunar: Lunar): string {
  return lunar.glyph?.trim() || "◐";
}

/**
 * The bodies of the planetary sky in a stable, conventional order.
 *
 * The served `bodies` is a map; iterating it directly would make the row order
 * depend on JSON key insertion, so two renders of the same readout could order
 * the sky differently. Bodies the kernel did not report are omitted rather than
 * rendered blank.
 */
export const SKY_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"] as const;

export function orderedBodies(planetary: Planetary): Array<{ name: string; body: PlanetaryBody }> {
  const bodies = planetary.bodies ?? {};
  return SKY_ORDER.filter((name) => Boolean(bodies[name])).map((name) => ({
    name,
    body: bodies[name],
  }));
}

/**
 * How often the readout is refreshed, in milliseconds.
 *
 * The archive polled every 120s (`StellarCartography.tsx:76`). The readout's
 * finest published subdivision is the breath (48/day ≈ 30 min), so a 2-minute
 * poll is already well inside the kernel's resolution; it is kept rather than
 * tightened because the value is a snapshot the reader may be reading.
 */
export const STELLAR_REFRESH_MS = 120_000;
