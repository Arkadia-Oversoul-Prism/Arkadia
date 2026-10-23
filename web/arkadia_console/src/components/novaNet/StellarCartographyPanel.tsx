/**
 * NovaNet — the Stellar Cartography readout (the Encyclopedia Galactica header).
 *
 * The archive mounted `StellarCartography` at the head of `NexusSpiralCodex`
 * (`archive/.../src/pages/NexusSpiralCodex.tsx:953`), replacing a minimal
 * "Ark Y1 · D140" chip with the full celestial readout. The console referenced
 * `GET /api/stellar-cartography` nowhere — a verified anonymous open read
 * (`200`, no identity) had no surface.
 *
 * This is a **read**, and the only one on this lens. Nothing is submitted, and
 * no control implies an action the backend does not offer.
 *
 * Three deliberate departures from the archived component:
 *
 *   * **Failures are shown.** The archive's `load()` was
 *     `.catch(() => {})` with `setData` guarded on a non-null result, so a failed
 *     fetch rendered "◎ Calibrating the star date…" **forever** — an outage was
 *     indistinguishable from a slow load. This panel routes the failure through
 *     `ContractState`, which separates "still loading" from "this identity
 *     cannot see it" from "the backend is down".
 *   * **No client-side clock.** Every value is the server's. The Ark Date epoch
 *     ("March 31 2026 — Birthday Seal") is not a UTC calendar derivation, so a
 *     client-side recomputation would disagree with the server's own readout.
 *   * **No read-aloud control.** The archive put a `ScrollListenButton` on the
 *     Oversoul transmission; that component is not on this branch, and a
 *     per-message voice control is a different slice's seam.
 */
import { useEffect, useState } from "react";
import { ContractState, Facts, Loading, Panel } from "../ui";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  isStellarReadout,
  lunarGlyph,
  orderedBodies,
  STELLAR_REFRESH_MS,
  type StellarReadout,
} from "./stellarCartographyContract";

type ReadState = "loading" | "ready" | "unavailable";

export function StellarCartographyPanel() {
  const [readout, setReadout] = useState<StellarReadout | null>(null);
  const [state, setState] = useState<ReadState>("loading");
  const [detail, setDetail] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    setDetail(null);

    const load = () => {
      apiRequest<unknown>(endpoints.stellarCartography)
        .then((payload) => {
          if (cancelled) return;
          if (!isStellarReadout(payload)) {
            setState("unavailable");
            setDetail("The readout arrived in an unexpected shape.");
            return;
          }
          setReadout(payload);
          setState("ready");
        })
        .catch((error: unknown) => {
          if (cancelled) return;
          setState("unavailable");
          setDetail(error instanceof Error ? error.message : "The readout could not be read.");
        });
    };

    load();
    const timer = window.setInterval(load, STELLAR_REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [nonce]);

  if (state !== "ready" || !readout) {
    return (
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Stellar Cartography · Encyclopedia Galactica
        </p>
        {state === "loading" ? (
          <Loading label="Calibrating the star date…" />
        ) : (
          <ContractState
            state="unavailable"
            error={detail}
            onRetry={() => setNonce((n) => n + 1)}
          />
        )}
      </Panel>
    );
  }

  const { ark_date: ark, schumann, lunar, planetary, cosmic_weather: weather } = readout;
  const oversoul = readout.oversoul_blind_pull;
  const galactica = readout.galactica;
  const sky = orderedBodies(planetary);

  return (
    <Panel className="mb-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-amber-300/70">
            Stellar Cartography
          </p>
          <h2 className="mt-1 font-serif text-lg text-white/90">
            Encyclopedia Galactica · Vol {galactica.current_volume}
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((x) => !x)}
          aria-expanded={expanded}
          className="rounded-lg border border-amber-300/25 bg-amber-300/5 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-amber-200/80 hover:bg-amber-300/10"
        >
          {expanded ? "▾ Collapse atlas" : "▸ Full atlas"}
        </button>
      </div>

      <Facts
        rows={[
          { label: "Ark date", value: ark.display },
          { label: "Coordinate", value: ark.coordinate },
          { label: "Epoch", value: ark.epoch },
          {
            label: "Lunar",
            value: `${lunarGlyph(lunar)} ${lunar.phase} · ${lunar.illumination_pct.toFixed(1)}% · ${lunar.moon_name}`,
          },
          {
            label: "Schumann",
            value: `${schumann.dominant_hz} Hz · ${schumann.dominant_name} · ${schumann.quality}`,
          },
          {
            label: "Cosmic weather",
            value: `${weather.geomagnetic_pressure} · Kp ${weather.kp_index} · wind ${weather.solar_wind_kms} km/s`,
          },
        ]}
      />

      <p className="mt-3 text-sm italic text-white/60">{weather.mood}</p>

      <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.02] p-3">
        <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
          Oversoul blind-pull · the day's transmission
        </p>
        <p className="mt-2 font-serif text-[15px] leading-relaxed text-white/85">
          {oversoul.transmission}
        </p>
        <p className="mt-2 font-mono text-[10px] text-white/30">{oversoul.method}</p>
      </div>

      {expanded && (
        <div className="mt-4 space-y-4">
          <div>
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
              Planetary sky · the bone report
            </p>
            <p className="text-sm text-white/70">{planetary.bone_report}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {sky.map(({ name, body }) => (
                <span
                  key={name}
                  className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 font-mono text-[10px] text-white/60"
                >
                  {body.glyph} {name} · {body.sign}
                </span>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
              Schumann bands
            </p>
            <div className="space-y-1">
              {schumann.bands.map((band) => (
                <div
                  key={band.hz}
                  className={`flex items-center justify-between rounded px-2 py-1 font-mono text-[11px] ${
                    band.hz === schumann.dominant_hz
                      ? "bg-amber-300/10 text-amber-200/90"
                      : "text-white/50"
                  }`}
                >
                  <span>{band.name}</span>
                  <span>{band.hz} Hz</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
              Volume index · {galactica.total_volumes} volumes
            </p>
            <div className="space-y-1">
              {galactica.volumes.map((volume) => (
                <div
                  key={volume.volume}
                  className={`rounded px-2 py-1 ${
                    volume.volume === galactica.current_volume ? "bg-amber-300/10" : ""
                  }`}
                >
                  <span className="font-mono text-[10px] text-amber-200/70">
                    Vol {volume.volume}
                  </span>
                  <span className="ml-2 text-sm text-white/80">{volume.title}</span>
                  <span className="ml-2 text-xs text-white/40">{volume.domain}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="font-mono text-[10px] text-white/25">
            Read at {readout.timestamp_utc} · refreshes every{" "}
            {Math.round(STELLAR_REFRESH_MS / 1000)}s
          </p>
        </div>
      )}
    </Panel>
  );
}
