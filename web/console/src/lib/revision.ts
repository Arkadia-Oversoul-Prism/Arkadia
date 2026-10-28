/**
 * Revision claims — one source, and the running revision is READ, never frozen.
 *
 * The console used to stamp a hardcoded revision (`ae847dd · reconciled`) into
 * three separate files. That is a claim about the running system rendered from a
 * constant: it cannot be true for more than one deployment, and it silently
 * misreports every later one. Measured on `main` @ `9195334c`, the deployed
 * console served a bundle whose revision token named an ancestor.
 *
 * So the running revision is fetched from the runtime's own read-only probe
 * (`GET /api/version` -> `source_revision`), and the map's derivation point is
 * kept separately and labelled as what it is: history, not the live revision.
 * When the probe cannot be read the console says so; it never falls back to a
 * remembered revision.
 */
import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * The revision the boundary map was derived from. This is the console's
 * provenance, NOT the running revision — `useLiveRevision` answers that.
 */
export const MAP_DERIVED_FROM = "ae847dd";

export interface VersionReading {
  source_revision?: string | null;
  revision_source?: string | null;
  revision_conflict?: boolean | null;
  read_only?: boolean;
}

export type RevisionState =
  | { state: "loading" }
  | { state: "ready"; revision: string; short: string; conflict: boolean }
  | { state: "unavailable" };

/** The probe is read-only and unauthenticated by design; it must not 401. */
export const versionReading = () =>
  api.get<VersionReading>("/api/version", { auth: false });

export function useLiveRevision(): RevisionState {
  const [value, setValue] = useState<RevisionState>({ state: "loading" });

  useEffect(() => {
    let alive = true;
    versionReading()
      .then((v) => {
        if (!alive) return;
        const rev = (v?.source_revision ?? "").trim();
        if (!rev) {
          setValue({ state: "unavailable" });
          return;
        }
        setValue({
          state: "ready",
          revision: rev,
          short: rev.slice(0, 7),
          conflict: v.revision_conflict === true,
        });
      })
      .catch(() => {
        if (alive) setValue({ state: "unavailable" });
      });
    return () => {
      alive = false;
    };
  }, []);

  return value;
}

/** The one-line revision label. Unreadable is stated, never guessed. */
export function revisionLabel(s: RevisionState): string {
  if (s.state === "ready") {
    return s.conflict ? `${s.short} · REVISION CONFLICT` : `${s.short} · running`;
  }
  if (s.state === "loading") return "reading revision…";
  return "revision unavailable";
}
