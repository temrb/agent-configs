import assert from "node:assert/strict";
import test from "node:test";

import { nextTheme } from "../src/theme.mjs";

test("nextTheme alternates supported themes", () => {
  assert.equal(nextTheme("light"), "dark");
  assert.equal(nextTheme("dark"), "light");
});
