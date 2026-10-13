import fs from "node:fs";
import path from "node:path";
import {
  matches,
  isMain,
  args,
  options,
  rootAt,
  policy,
  manifest,
  helperIdentity,
  readJSON,
  schema,
  safe,
  sha,
  atomic,
  main,
  git,
  secret,
} from "./common.mjs";
import { parseReport } from "./reports.mjs";
import { artifact } from "./run-check.mjs";

export function inspectAttempt(root, p, current, dir, a, targeted = false) {
  schema("attempt", a);
  const problems = [];
  if (a.id !== path.basename(dir) || a.project !== root || a.cwd !== root)
    problems.push("Attempt/project identity mismatch");
  if (!Object.hasOwn(p.suites, a.suite)) return ["Unknown suite"];
  const suite = p.suites[a.suite];
  if (a.evaluatedRevision !== git(root, "rev-parse", "HEAD").trim())
    problems.push("Evaluated revision changed");
  if (a.lifecycle !== "completed" || a.exitCode !== 0 || a.signal !== null)
    problems.push("Process did not complete successfully");
  if (
    a.pre.digest !== current.digest ||
    a.post?.digest !== current.digest ||
    sha(JSON.stringify(a.pre.entries)) !== a.pre.digest ||
    sha(JSON.stringify(a.post?.entries)) !== a.post?.digest
  )
    problems.push("Stale or changed-during-run inputs");
  if (
    a.policyDigest !==
    sha(fs.readFileSync(path.join(root, ".vine/project.json")))
  )
    problems.push("Policy identity changed");
  if (a.helperDigest !== helperIdentity())
    problems.push("Helper identity changed");
  if (
    a.environment.node !== p.runtime.node ||
    a.environment.bun !== p.runtime.bun
  )
    problems.push("Toolchain mismatch");
  if (
    !targeted &&
    (a.selection.length ||
      suite.filterEnv.some((key) => Boolean(a.environment[key])))
  )
    problems.push("Filtered selection cannot satisfy full obligation");
  if (
    !a.endedAt ||
    !Number.isFinite(Date.parse(a.startedAt)) ||
    !Number.isFinite(Date.parse(a.endedAt)) ||
    Date.parse(a.endedAt) < Date.parse(a.startedAt)
  )
    problems.push("Invalid completion timestamps");
  const expectedArgs = [
    "run",
    suite.script,
    ...suite.args.map((arg) =>
      arg === "{artifact}" ? (a.artifact?.path ?? "") : arg,
    ),
    ...a.selection,
  ];
  if (suite.reports.some((r) => r.adapter === "vitest"))
    expectedArgs.push(
      "--reporter=json",
      `--outputFile=${safe(path.join(dir, "native"), suite.reports.find((r) => r.adapter === "vitest").path)}`,
    );
  if (JSON.stringify(a.argv) !== JSON.stringify(expectedArgs))
    problems.push("Executed arguments differ from full obligation");
  if (suite.artifact !== "none") {
    try {
      if (JSON.stringify(artifact(root, suite)) !== JSON.stringify(a.artifact))
        problems.push("Built artifact identity changed");
    } catch {
      problems.push("Built artifact unavailable");
    }
  }
  if (!a.logs.length) problems.push("Missing execution log");
  for (const log of a.logs) {
    try {
      if (sha(fs.readFileSync(safe(dir, log.path))) !== log.digest)
        problems.push("Execution log changed");
    } catch {
      problems.push("Execution log unavailable");
    }
  }
  if (a.reports.length !== suite.reports.length)
    problems.push("Native report inventory differs");
  for (const spec of suite.reports) {
    const fresh = parseReport(safe(dir, "native"), spec);
    const recorded = a.reports.find(
      (r) => r.path === spec.path && r.adapter === spec.adapter,
    );
    if (
      fresh.status !== "valid" ||
      JSON.stringify(fresh) !== JSON.stringify(recorded)
    )
      problems.push(`Incomplete or altered native report ${spec.path}`);
    if (
      (!targeted &&
        (fresh.observation?.filtered || fresh.observation?.skipped.length)) ||
      fresh.observation?.failed.length
    )
      problems.push(`Skipped, filtered or failed scenarios in ${spec.path}`);
    if (
      ["workerd", "playwright", "vitest", "built"].includes(spec.adapter) &&
      (!fresh.observation?.executed.length ||
        fresh.observation.discovery !== "observed")
    )
      problems.push(`No executed scenarios in ${spec.path}`);
    if (
      fresh.limitations.includes("Native suite reports unsuccessful completion")
    )
      problems.push("Native suite unsuccessful despite process result");
    if (fresh.limitations.includes("Playwright global errors present"))
      problems.push("Native global failure");
    if (spec.adapter === "built" && fresh.status === "valid") {
      const data = readJSON(safe(path.join(dir, "native"), spec.path));
      if (JSON.stringify([...data.boundaries].sort()) !== JSON.stringify([...(suite.expectedBoundaries ?? [])].sort()))
        problems.push("Smoke boundary inventory differs from expectedBoundaries");
      if (
        data.buildId !== a.artifact?.buildId ||
        data.manifestSHA256 !== a.artifact?.digest
      )
        problems.push("Smoke report refers to another artifact");
    }
  }
  return problems;
}
export function verify(
  root,
  scope,
  boundaries = [],
  reconcile = false,
  trustedFile = null,
  base = null,
) {
  const p = policy(root, trustedFile),
    current = manifest(root, p);
  if (
    trustedFile &&
    sha(fs.readFileSync(trustedFile)) !==
      sha(fs.readFileSync(path.join(root, ".vine/project.json")))
  )
    throw Error(
      "Candidate policy differs from trusted policy; independent approval required",
    );
  let applicability = null;
  if (scope === "task") {
    if (!base)
      throw Error("Task scope requires --base for complete applicability");
    const revision = git(
      root,
      "rev-parse",
      "--verify",
      `${base}^{commit}`,
    ).trim();
    const mergeBase = git(root, "merge-base", revision, "HEAD").trim();
    const changed = [
      ...new Set([
        ...git(root, "diff", "--name-only", "--no-renames", "-z", mergeBase, "--").split("\0"),
        ...git(root, "ls-files", "--others", "--exclude-standard", "-z").split(
          "\0",
        ),
      ]),
    ].filter(Boolean);
    const excluded = changed.filter((name) => secret(name, p.inputs.sensitive) ||
      (!p.inputs.extra.includes(name) && !["package.json", ".vine/project.json", ...p.authority].includes(name) &&
       p.inputs.exclude.some((pattern) => matches(name, pattern))));
    const omitted = changed.filter((name) => !excluded.includes(name) &&
      !["package.json", ".vine/project.json", ...p.authority, ...p.inputs.extra].includes(name) &&
      !p.inputs.include.some((pattern) => matches(name, pattern)));
    if (omitted.length)
      throw Error(`Changed paths omitted from verification inputs: ${JSON.stringify(omitted)}`);
    const docsOnly =
      changed.length > 0 &&
      changed.every(
        (name) => name.endsWith(".md") && !p.authority.includes(name) &&
          !/(^|\/)(AGENTS|SKILL|CLAUDE)\.md$/.test(name) &&
          !/^(agents|\.agents|\.codex|\.claude)\//.test(name) &&
          (p.documentationPaths ?? []).some((pattern) => matches(name, pattern)),
      );
    const matchedRules = p.routing.filter((rule) =>
      changed.some((name) =>
        rule.patterns.some((pattern) => matches(name, pattern)),
      ),
    );
    boundaries = [
      ...new Set([
        ...boundaries,
        ...matchedRules.flatMap((rule) => rule.boundaries),
      ]),
    ];
    scope = docsOnly ? "documentation" : "routine";
    applicability = {
      base: revision,
      mergeBase,
      changedPaths: changed,
      rules: matchedRules.map((rule) => rule.id),
      documentationOnly: docsOnly,
      exclusions: excluded,
      unmatchedBehavioralChanges: docsOnly ? [] : changed.filter((name) =>
        !p.routing.some((rule) => rule.patterns.some((pattern) => matches(name, pattern)))),
      boundaryReview:
        "Maintainer reviews routing completeness; agent may add checks but cannot waive them.",
    };
  }
  if (!Object.hasOwn(p.scopes, scope) || scope === "targeted")
    throw Error(
      "Choose documentation, routine or full; targeted results do not establish completion",
    );
  if (boundaries.some((b) => !Object.hasOwn(p.boundaries, b)))
    throw Error("Unknown applicability boundary");
  const required = [
    ...new Set([
      ...p.scopes[scope],
      ...boundaries.flatMap((b) => p.boundaries[b]),
    ]),
  ];
  const attempts = [],
    directory = safe(root, p.evidenceDir);
  if (fs.existsSync(directory))
    for (const name of fs.readdirSync(directory).sort()) {
      const dir = safe(directory, name),
        file = safe(dir, "attempt.json");
      if (!fs.existsSync(file)) continue;
      try {
        const a = schema("attempt", readJSON(file));
        if (a.lifecycle === "started" && reconcile) {
          let running = true;
          try {
            process.kill(a.pid, 0);
          } catch (e) {
            running = e.code !== "ESRCH";
          }
          if (!running) {
            a.lifecycle = "orphaned";
            a.endedAt = new Date().toISOString();
            a.limitations.push(
              "Reconciled unresolved attempt after wrapper process disappeared",
            );
            atomic(file, a);
          }
        }
        attempts.push({
          id: name,
          suite: a.suite,
          problems: inspectAttempt(root, p, current, dir, a),
        });
      } catch (e) {
        attempts.push({
          id: name,
          suite: null,
          problems: [`Invalid attempt: ${e.message}`],
        });
      }
    }
  const satisfied = required.filter((id) =>
    attempts.some((a) => a.suite === id && !a.problems.length),
  );
  return {
    completion: "diagnostic-only; approved baseline required by completion CLI",
    scope,
    applicability,
    boundaries,
    required,
    satisfied,
    missing: required.filter((id) => !satisfied.includes(id)),
    inputDigest: current.digest,
    attempts,
    trust: "local diagnostic; candidate-authored evidence is not attestation",
    acceptance: "not evaluated",
  };
}
export function verifyCase(root, caseFile, base = null) {
  const c = schema("case", readJSON(caseFile)),
    p = policy(root);
  const fixtureEntries = c.fixturePaths
    .map((name) => {
      if (/[*?\[\]{}]/.test(name))
        throw Error("Case fixture paths must be exact files");
      return { path: name, digest: sha(fs.readFileSync(safe(root, name))) };
    })
    .sort((a, b) => a.path.localeCompare(b.path));
  if (sha(JSON.stringify(fixtureEntries)) !== c.testFixtureDigest)
    throw Error("Case final test/fixture digest changed");
  const load = (id) =>
    schema(
      "attempt",
      readJSON(safe(root, `${p.evidenceDir}/${id}/attempt.json`)),
    );
  const red = load(c.redAttempt),
    green = load(c.greenAttempt);
  if (red.case !== c.id || green.case !== c.id || red.id === green.id || red.suite !== green.suite)
    throw Error("Case attempt association mismatch");
  if (
    red.evaluatedRevision !== c.defectiveRevision ||
    green.evaluatedRevision !== c.fixedRevision
  )
    throw Error("Case revision association mismatch");
  const sourceEntries = (a) => a.pre.entries.filter((e) =>
    ![...c.fixturePaths, ".vine/project.json", ...p.authority].includes(e.path));
  if (JSON.stringify(sourceEntries(red)) === JSON.stringify(sourceEntries(green)))
    throw Error("No distinct implementation input state; red/green is inconclusive");
  if (c.chronology === "unconfirmed")
    throw Error("Case chronology unconfirmed");
  for (const a of [red, green])
    for (const f of fixtureEntries)
      if (a.pre.entries.find((e) => e.path === f.path)?.digest !== f.digest)
        throw Error(
          "Final reproducer differs between red and green; replay required",
        );
  if (
    !Number.isInteger(red.exitCode) ||
    red.exitCode === 0 ||
    red.signal !== null ||
    red.lifecycle !== "completed" ||
    !c.setupValidated ||
    !c.assertion ||
    c.tests.some((id) => !red.reports.some((r) =>
      r.status === "valid" && r.observation?.failed.includes(id) &&
      !r.observation.expectedFailure.includes(id)))
  )
    throw Error("Red assertion/setup unconfirmed");
  if (
    red.pre.digest !== red.post?.digest ||
    sha(JSON.stringify(red.pre.entries)) !== red.pre.digest ||
    sha(JSON.stringify(red.post?.entries)) !== red.post?.digest ||
    red.project !== root ||
    red.cwd !== root ||
    red.id !== c.redAttempt ||
    !red.logs.length ||
    !Number.isFinite(Date.parse(red.startedAt)) ||
    !Number.isFinite(Date.parse(red.endedAt)) ||
    Date.parse(red.endedAt) < Date.parse(red.startedAt)
  )
    throw Error("Red inputs changed or manifest invalid");
  const redDir = safe(root, `${p.evidenceDir}/${red.id}`);
  const historicalBytes = fs.readFileSync(safe(redDir, "policy.json"));
  const historical = schema("project", JSON.parse(historicalBytes));
  const redSuite = historical.suites[red.suite];
  const historicalPackage = fs.readFileSync(safe(redDir, "package.json"));
  if (red.pre.entries.find((e) => e.path === "package.json")?.digest !== sha(historicalPackage) ||
      !JSON.parse(historicalPackage).scripts?.[redSuite?.script])
    throw Error("Red historical package script identity mismatch");
  if (sha(historicalBytes) !== red.policyDigest || !redSuite ||
      red.pre.entries.find((e) => e.path === ".vine/project.json")?.digest !== red.policyDigest ||
      red.helperDigest !== helperIdentity() ||
      red.environment.node !== historical.runtime.node || red.environment.bun !== historical.runtime.bun)
    throw Error("Red historical policy/helper/toolchain identity mismatch; replay required");
  const redArgs = ["run", redSuite.script, ...redSuite.args.map((arg) => arg === "{artifact}" ? (red.artifact?.path ?? "") : arg), ...red.selection];
  if (redSuite.reports.some((r) => r.adapter === "vitest"))
    redArgs.push("--reporter=json", `--outputFile=${safe(path.join(redDir, "native"), redSuite.reports.find((r) => r.adapter === "vitest").path)}`);
  if (JSON.stringify(red.argv) !== JSON.stringify(redArgs) || red.reports.length !== redSuite.reports.length ||
      red.selection.some((arg) => !redSuite.selection.some((pattern) => new RegExp(pattern).test(arg))))
    throw Error("Red executed arguments or report inventory differ from historical contract");
  for (const report of red.reports) {
    const spec = redSuite.reports.find(
      (r) => r.path === report.path && r.adapter === report.adapter,
    );
    if (
      !spec ||
      JSON.stringify(parseReport(safe(redDir, "native"), spec)) !==
        JSON.stringify(report)
    )
      throw Error("Red native report changed or incompatible");
  }
  for (const log of red.logs)
    if (sha(fs.readFileSync(safe(redDir, log.path))) !== log.digest)
      throw Error("Red log changed");
  const checks = verify(root, "task", [], false, null, base ?? c.defectiveRevision);
  const greenProblems = inspectAttempt(
    root,
    p,
    manifest(root, p),
    safe(root, `${p.evidenceDir}/${green.id}`),
    green,
    true,
  );
  if (
    greenProblems.length ||
    checks.missing.length ||
    c.tests.some(
      (id) =>
        !green.reports.some(
          (r) =>
            r.status === "valid" &&
            r.observation?.executed.includes(id) &&
            !r.observation.failed.includes(id) &&
            !r.observation.expectedFailure.includes(id),
        ),
    ) ||
    c.surroundingSuites.some(
      (id) =>
        !checks.satisfied.includes(id) &&
        !checks.attempts.some((a) => a.suite === id && !a.problems.length),
    )
  )
    throw Error("Green or surrounding obligations incomplete");
  if (
    c.chronology === "red-before-fix" &&
    Date.parse(red.endedAt) > Date.parse(green.startedAt)
  )
    throw Error("Chronology inconsistent");
  return {
    case: c.id,
    association: "mechanically consistent",
    trust:
      "Oracle, setup and chronology declarations require independent review",
  };
}
if (isMain(import.meta.url))
  main(() => {
    const a = args();
    options(a, [
      "root",
      "scope",
      "boundaries",
      "case",
      "reconcile",
      "trusted-policy",
      "trusted-policy-sha256",
      "diagnostic",
      "base",
      "trusted-base",
    ]);
    const root = rootAt(a.root);
    if (a.diagnostic !== "true") {
      if (!a["trusted-policy"] || !/^[a-f0-9]{64}$/.test(a["trusted-policy-sha256"] ?? ""))
        throw Error("Completion requires --trusted-policy and independently supplied --trusted-policy-sha256; use --diagnostic true for local inspection");
      if (sha(fs.readFileSync(a["trusted-policy"])) !== a["trusted-policy-sha256"] ||
          sha(fs.readFileSync(safe(root, ".vine/project.json"))) !== a["trusted-policy-sha256"])
        throw Error("Candidate or baseline differs from approved policy digest");
    }
    if (a.diagnostic !== "true") {
      if (!/^[a-f0-9]{40,64}$/.test(a["trusted-base"] ?? ""))
        throw Error("Completion requires independently supplied --trusted-base full commit identity");
      if (a.base && git(root, "rev-parse", "--verify", `${a.base}^{commit}`).trim() !== a["trusted-base"])
        throw Error("--base differs from trusted change baseline");
      if (!a.case && a.scope && a.scope !== "task")
        throw Error("Completion requires task scope; direct scopes are diagnostic only");
    }
    if (a.case) {
      const result = verifyCase(root, a.case, a["trusted-base"] ?? a.base ?? null);
      result.baselineDigest = a["trusted-policy-sha256"] ?? null;
      result.trustedBase = a["trusted-base"] ?? null;
      result.completion = a.diagnostic === "true" ? "diagnostic-only" : "approved-policy case evaluated";
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    const result = verify(
      root,
      a.scope ?? (a.diagnostic === "true" ? "routine" : "task"),
      a.boundaries?.split(",").filter(Boolean) ?? [],
      a.reconcile === "true",
      a["trusted-policy"] ?? null,
      a["trusted-base"] ?? a.base ?? null,
    );
    result.completion = a.diagnostic === "true" ? "diagnostic-only" : "approved-policy obligations evaluated";
    result.baselineDigest = a["trusted-policy-sha256"] ?? null;
    result.trustedBase = a["trusted-base"] ?? null;
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.missing.length ? 1 : 0;
  });
