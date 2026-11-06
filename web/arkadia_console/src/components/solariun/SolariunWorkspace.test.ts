/**
 * Solariun collection envelope contract (AO4-07).
 *
 * The defect: `rowsOf` returned `[]` for any unrecognised envelope, so a
 * changed response shape rendered as "No tasks recorded for this project" —
 * a false statement about the project, not a statement about the read.
 *
 * These tests pin the five states apart. The important one is that a
 * `mismatch` is never `empty`: that is the exact confusion the finding names.
 */
import { describe, expect, it } from "vitest";

import { readCollection } from "./SolariunWorkspace";

describe("readCollection", () => {
  it("a bare array is a valid collection", () => {
    expect(readCollection([])).toEqual({ kind: "empty" });
    expect(readCollection([{ id: "1" }])).toEqual({ kind: "populated", rows: [{ id: "1" }] });
  });

  it("a known envelope key is a valid collection", () => {
    expect(readCollection({ tasks: [] })).toEqual({ kind: "empty" });
    expect(readCollection({ tasks: [{ id: "t1" }] })).toEqual({
      kind: "populated",
      rows: [{ id: "t1" }],
    });
    expect(readCollection({ files: [{ id: "f1" }] }).kind).toBe("populated");
    expect(readCollection({ events: [{ id: "e1" }] }).kind).toBe("populated");
    expect(readCollection({ items: [{ id: "i1" }] }).kind).toBe("populated");
  });

  it("an unrecognised envelope is a mismatch, never an empty collection", () => {
    // The regression: this used to be indistinguishable from `[]`.
    const result = readCollection({ data: [{ id: "t1" }] });
    expect(result.kind).toBe("mismatch");
    expect(result.kind).not.toBe("empty");
  });

  it("a non-object payload is a mismatch", () => {
    expect(readCollection(null).kind).toBe("mismatch");
    expect(readCollection("nope").kind).toBe("mismatch");
    expect(readCollection(42).kind).toBe("mismatch");
    expect(readCollection(undefined).kind).toBe("mismatch");
  });

  it("an empty object is a mismatch, not an empty collection", () => {
    expect(readCollection({}).kind).toBe("mismatch");
  });

  it("a mismatch carries a detail explaining what was seen", () => {
    const result = readCollection({ payload: [] });
    expect(result.kind).toBe("mismatch");
    if (result.kind === "mismatch") {
      expect(result.detail).toContain("payload");
    }
  });

  it("distinguishes empty from populated for the same key", () => {
    expect(readCollection({ tasks: [] }).kind).toBe("empty");
    expect(readCollection({ tasks: [1] }).kind).toBe("populated");
  });
});
