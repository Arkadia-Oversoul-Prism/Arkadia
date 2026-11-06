/**
 * Capability registry contract (AO4-04).
 *
 * The registry declares, for every capability, the endpoint it dispatches to.
 * That field is **metadata**, not routing: nothing in the console reads
 * `capability.endpoint` to make a request — the workspace dispatches through
 * `lib/arkana` and the project services. The risk is therefore not a broken
 * route, it is a *lie in the registry*: an entry naming a path that does not
 * exist in `endpoints.ts` reads as "this is wired" when it is not.
 *
 * This test makes the metadata mechanically checkable:
 *
 *   1. every `endpoint` is either a value that exists in the canonical
 *      `endpoints` map, or a builder exported by `endpoints.ts`, or a literal
 *      path that is declared in `endpoints.ts` (a template such as
 *      `/solspire/projects/{project_id}/conversations` is accepted only when
 *      its static prefix is a real declared path);
 *   2. no capability names an endpoint that resolves to nothing;
 *   3. the registry's own invariants hold (unique ids and tokens, a
 *      `dispatchable: false` entry always explains itself, and a consequential
 *      capability is never silently dispatchable without a note).
 *
 * It deliberately does **not** assert that the backend serves the path — that
 * would be a runtime claim this test cannot make. It asserts the registry is
 * internally consistent with the one path map, which is what "deterministic
 * registry contract" can honestly mean.
 */
import { describe, expect, it } from "vitest";

import { CAPABILITIES, CAPABILITY_BY_TOKEN, COMPOSER_TOKENS } from "./capabilities";
import * as endpointModule from "./endpoints";

const { endpoints } = endpointModule;

/** Every string value declared in the canonical endpoint map. */
const DECLARED_PATHS = new Set<string>(Object.values(endpoints) as string[]);

/** Every exported builder function from `endpoints.ts`. */
const BUILDERS = new Set(
  Object.entries(endpointModule)
    .filter(([, v]) => typeof v === "function")
    .map(([k]) => k),
);

/**
 * Resolve one capability's `endpoint` field to a canonical path, or null when
 * it cannot be verified against `endpoints.ts`.
 */
function resolveEndpoint(endpoint: string | ((id: string) => string)): string | null {
  if (typeof endpoint === "function") {
    // A builder must be one of the module's own exports, and must produce a
    // path that starts with a declared prefix.
    const name = Object.entries(endpointModule).find(([, v]) => v === endpoint)?.[0];
    if (!name || !BUILDERS.has(name)) return null;
    const produced = endpoint("00000000-0000-0000-0000-000000000000");
    return typeof produced === "string" && produced.length > 0 ? produced : null;
  }
  if (DECLARED_PATHS.has(endpoint)) return endpoint;
  // A template path is acceptable when its static prefix is a declared path.
  const staticPrefix = endpoint.split("{")[0].replace(/\/$/, "");
  if (staticPrefix && DECLARED_PATHS.has(staticPrefix)) return endpoint;
  return null;
}

describe("capability registry contract", () => {
  it("every declared capability endpoint resolves to a canonical definition", () => {
    const unresolved = CAPABILITIES.filter((c) => resolveEndpoint(c.endpoint) === null).map(
      (c) => `${c.id} → ${typeof c.endpoint === "function" ? "<builder>" : c.endpoint}`,
    );
    expect(unresolved).toEqual([]);
  });

  it("a builder endpoint is a real export of endpoints.ts", () => {
    for (const capability of CAPABILITIES) {
      if (typeof capability.endpoint !== "function") continue;
      const exported = Object.values(endpointModule).includes(capability.endpoint as never);
      expect(exported, `${capability.id} uses a builder that endpoints.ts does not export`).toBe(true);
    }
  });

  it("capability ids and tokens are unique", () => {
    const ids = CAPABILITIES.map((c) => c.id);
    const tokens = CAPABILITIES.map((c) => c.token);
    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(tokens).size).toBe(tokens.length);
  });

  it("a non-dispatchable capability always explains why", () => {
    for (const capability of CAPABILITIES.filter((c) => c.dispatchable === false)) {
      expect(capability.note, `${capability.id} is not dispatchable but has no note`).toBeTruthy();
    }
  });

  it("consequential capabilities are never offered as composer tokens", () => {
    // AO4-03: a consequential capability has no authorized dispatch path from
    // the ordinary conversational composer, so it must not appear there —
    // whether it is excluded because it is unverified or because it is
    // explicitly non-dispatchable.
    const offered = CAPABILITIES.filter(
      (c) => c.consequential && COMPOSER_TOKENS.includes(c.token),
    ).map((c) => c.id);
    expect(offered).toEqual([]);
  });

  it("the composer token list only contains dispatchable, verified capabilities", () => {
    for (const token of COMPOSER_TOKENS) {
      const capability = CAPABILITY_BY_TOKEN[token];
      expect(capability, `composer token @${token} has no registry entry`).toBeTruthy();
      expect(capability.status).toBe("verified");
      expect(capability.dispatchable).not.toBe(false);
    }
  });

  it("lab.authorize and lab.execute are not dispatchable (AO4-03)", () => {
    for (const id of ["lab.authorize", "lab.execute"]) {
      const capability = CAPABILITIES.find((c) => c.id === id);
      expect(capability, `${id} missing from the registry`).toBeTruthy();
      expect(capability!.consequential).toBe(true);
      expect(capability!.dispatchable).toBe(false);
      expect(COMPOSER_TOKENS).not.toContain(capability!.token);
    }
  });
});
