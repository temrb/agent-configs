import assert from "node:assert/strict";
import test from "node:test";

import { formatTitle } from "../src/title.mjs";

test("formats a catalog title", () => {
  assert.equal(formatTitle("  winter SALE "), "Winter Sale");
});
