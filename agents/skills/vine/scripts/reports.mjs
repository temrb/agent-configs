import fs from "node:fs";
import { readJSON, safe, sha } from "./common.mjs";
const empty = () => ({
  executed: [],
  skipped: [],
  failed: [],
  expectedFailure: [],
  discovery: "unknown",
  filtered: false,
});
export function parseReport(dir, spec) {
  const result = { ...spec, status: "missing", limitations: [] };
  try {
    const file = safe(dir, spec.path);
    if (!fs.existsSync(file))
      return { ...result, limitations: ["Required native report absent"] };
    result.digest = sha(fs.readFileSync(file));
    const data = readJSON(file),
      o = empty();
    if (spec.adapter === "workerd") {
      if (
        data.schemaVersion !== 1 ||
        !["passed", "failed", "filtered"].includes(data.status) ||
        !Array.isArray(data.results)
      )
        throw Error("Invalid workerd completion report");
      if (data.status === "failed")
        result.limitations.push("Native suite reports unsuccessful completion");
      for (const r of data.results) {
        if (
          typeof r.name !== "string" || !r.name.trim() ||
          !["passed", "skipped", "failed"].includes(r.status)
        )
          throw Error("Invalid scenario result");
        o[r.status === "passed" ? "executed" : r.status].push(r.name);
      }
      o.executed.push(...o.failed);
      o.filtered = data.status === "filtered" || Boolean(data.filter);
      o.discovery =
        data.discovery === "completed-dispatch" ? "observed" : "unknown";
      if (o.discovery === "unknown")
        result.limitations.push("Dispatch incomplete or unobserved");
      if (data.status === "failed" && !o.failed.length)
        result.limitations.push(
          "Failure outside observed scenario: setup or environment unknown",
        );
    } else if (spec.adapter === "playwright") {
      if (
        !Array.isArray(data.suites) ||
        !data.stats ||
        ["expected", "unexpected", "flaky", "skipped"].some(
          (key) => !Number.isInteger(data.stats[key]) || data.stats[key] < 0,
        ) ||
        !Array.isArray(data.errors)
      )
        throw Error("Invalid Playwright report");
      if (data.stats.unexpected > 0 || data.stats.flaky > 0)
        result.limitations.push("Native suite reports unsuccessful completion");
      function visit(suites, prefix = "") {
        for (const suite of suites) {
          for (const spec of suite.specs ?? [])
            for (const test of spec.tests ?? []) {
              const id = `${prefix}${suite.title}/${spec.title}/${test.projectName ?? ""}`;
              if (
                !Array.isArray(test.results) ||
                !["passed", "failed", "skipped"].includes(
                  test.expectedStatus,
                ) ||
                !["expected", "unexpected", "flaky", "skipped"].includes(
                  test.status,
                ) ||
                test.results.some(
                  (r) =>
                    ![
                      "passed",
                      "failed",
                      "timedOut",
                      "skipped",
                      "interrupted",
                    ].includes(r.status),
                )
              )
                throw Error("Missing Playwright results");
              if (
                test.expectedStatus === "skipped" ||
                !test.results.length ||
                test.results.every((r) => r.status === "skipped")
              )
                o.skipped.push(id);
              else {
                o.executed.push(id);
                if (
                  test.status === "unexpected" ||
                  test.status === "flaky" ||
                  test.results.some((r) => r.status !== test.expectedStatus)
                )
                  o.failed.push(id);
                if (test.expectedStatus === "failed")
                  o.expectedFailure.push(id);
              }
            }
          visit(suite.suites ?? [], `${prefix}${suite.title}/`);
        }
      }
      visit(data.suites);
      o.discovery = "observed";
      if (data.errors.length)
        result.limitations.push("Playwright global errors present");
    } else if (spec.adapter === "vitest") {
      if (!Array.isArray(data.testResults) || typeof data.success !== "boolean")
        throw Error("Invalid Vitest report");
      if (!data.success)
        result.limitations.push("Native suite reports unsuccessful completion");
      for (const file of data.testResults) {
        if (
          typeof file.name !== "string" || !file.name.trim() ||
          !Array.isArray(file.assertionResults)
        )
          throw Error("Invalid Vitest file result");
        if (file.status === "failed")
          result.limitations.push(
            "Native suite reports unsuccessful completion",
          );
        for (const r of file.assertionResults) {
          if (typeof (r.fullName ?? r.title) !== "string" || !(r.fullName ?? r.title).trim())
            throw Error("Invalid Vitest assertion identity");
          const id = `${file.name}/${r.fullName ?? r.title}`;
          if (["pending", "skipped", "todo", "disabled"].includes(r.status))
            o.skipped.push(id);
          else if (["passed", "failed"].includes(r.status)) {
            o.executed.push(id);
            if (r.status === "failed") o.failed.push(id);
          } else throw Error("Unknown Vitest status");
        }
      }
      o.discovery = "observed";
      // Vitest JSON does not expose inverted-expectation identity consistently.
      result.limitations.push(
        "Expected-failure identity unavailable from this adapter",
      );
    } else if (spec.adapter === "built") {
      if (
        data.status !== "passed" ||
        typeof data.buildId !== "string" ||
        typeof data.manifestSHA256 !== "string" ||
        !Array.isArray(data.boundaries) ||
        !data.boundaries.length ||
        data.boundaries.some((id) => typeof id !== "string" || !id) ||
        new Set(data.boundaries).size !== data.boundaries.length
      )
        throw Error("Invalid built smoke report");
      o.executed = data.boundaries;
      o.discovery = "observed";
      result.limitations.push(...(data.exclusions ?? []));
    } else if (spec.adapter === "removal") {
      if (
        !Array.isArray(data.results) ||
        data.results.length !== 4 ||
        new Set(data.results.map((r) => r.feature)).size !== 4 ||
        !["hello", "work-items", "service-report", "all"].every((feature) =>
          data.results.some(
            (r) =>
              r.feature === feature &&
              r.status === "Passed" &&
              r.isolatedStaticAndBuild === true,
          ),
        )
      )
        throw Error("Incomplete removal report");
      o.executed = data.results.map((r) => r.feature);
      o.discovery = "observed";
    } else if (spec.adapter === "json-status") {
      if (!["passed", "Passed"].includes(data.status))
        throw Error("Native status does not establish completion");
      result.limitations.push("Scenario discovery unavailable");
    } else throw Error("Unknown report adapter");
    for (const key of ["executed", "skipped", "failed", "expectedFailure"])
      o[key] = [...new Set(o[key])].sort();
    return {
      ...result,
      limitations: [...new Set(result.limitations)],
      status: "valid",
      observation: o,
    };
  } catch (e) {
    return { ...result, status: "malformed", limitations: [e.message] };
  }
}
