import { describe, expect, it } from "vitest";

import { normalizeTimeout } from "../src/timeout";

describe("normalizeTimeout", () => {
  it("preserves an existing whole value", () => {
    expect(normalizeTimeout(5)).toBe(5);
  });
});
