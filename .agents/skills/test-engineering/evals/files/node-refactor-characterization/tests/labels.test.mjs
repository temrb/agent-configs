import assert from "node:assert/strict";
import test from "node:test";

import { parseLabels, parseTags } from "../src/labels.mjs";

test("parses ordinary tag and label lists", () => {
  assert.deepEqual(parseTags(" red, blue "), ["red", "blue"]);
  assert.deepEqual(parseLabels("small, large"), ["small", "large"]);
});
