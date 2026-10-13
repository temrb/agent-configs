import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  policy,
  manifest,
  atomic,
  readJSON,
  schema,
  sha,
  safe,
  validate,
} from "../scripts/common.mjs";
import { run } from "../scripts/run-check.mjs";
import { verify, inspectAttempt } from "../scripts/verify-evidence.mjs";
import { parseReport } from "../scripts/reports.mjs";
import { audit } from "../scripts/audit-test-diff.mjs";
import { install, RUNTIME } from "../scripts/install.mjs";
const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const git = (root, ...argv) =>
  execFileSync("git", ["-C", root, ...argv], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
function fixture(t, reports = [], command = "node proof.mjs") {
  const root = fs.mkdtempSync(
    path.join(os.tmpdir(), "vine consumer # with spaces "),
  );
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, ".vine"));
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({ scripts: { test: command } }),
  );
  fs.writeFileSync(path.join(root, "proof.mjs"), 'console.log("proof");\n');
  fs.writeFileSync(
    path.join(root, ".gitignore"),
    ".cloudflare/\n.vine/transactions/\n.vine/install.json\n",
  );
  const p = {
    schemaVersion: 1,
    helperVersion: "1.0.0",
    runtime: { node: "24.19.0", bun: "1.4.2" },
    evidenceDir: ".cloudflare/vine-evidence",
    inputs: {
      relevant: ["proof.mjs"],
      include: ["**"],
      exclude: [
        ".cloudflare/**",
        ".vine/transactions/**",
        ".vine/install.json",
        ".agents/**",
      ],
      extra: [],
    },
    authority: [],
    suites: {
      unit: {
        category: "command",
        script: "test",
        args: [],
        selection: ["^--selected$"],
        filterEnv: ["VINE_TEST_FILTER"],
        reports,
        artifact: "none",
      },
    },
    scopes: {
      targeted: [],
      documentation: ["unit"],
      routine: ["unit"],
      full: ["unit"],
    },
    boundaries: { logic: [] },
    routing: [],
    protected: ["**"],
    mode: "advisory/manual-review",
  };
  atomic(path.join(root, ".vine/project.json"), p);
  git(root, "init", "-q");
  git(root, "add", ".");
  git(
    root,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "baseline",
  );
  return root;
}
const invoke = (root, extra = []) =>
  run({ root, suite: "unit", task: "fixture", extra });
const attempt = (root) => {
  const dir = path.join(root, ".cloudflare/vine-evidence");
  const ids = fs
    .readdirSync(dir)
    .sort(
      (a, b) =>
        fs.statSync(path.join(dir, b)).mtimeMs -
        fs.statSync(path.join(dir, a)).mtimeMs,
    );
  return {
    dir: path.join(dir, ids[0]),
    a: readJSON(path.join(dir, ids[0], "attempt.json")),
  };
};
test("fresh success, changed final inputs and edits during execution", async (t) => {
  const root = fixture(t);
  assert.equal(await invoke(root), 0);
  assert.deepEqual(verify(root, "routine").missing, []);
  fs.writeFileSync(path.join(root, "new test.ts"), "untracked change");
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  fs.unlinkSync(path.join(root, "new test.ts"));
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    'import fs from "node:fs"; fs.writeFileSync("changed.ts", "during execution");',
  );
  await invoke(root);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
});
test("filters, missing reports and malformed reports never satisfy full obligations", async (t) => {
  const root = fixture(t, [{ path: "proof.json", adapter: "json-status" }]);
  await invoke(root);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    'import fs from "node:fs"; fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+"/proof.json", "{bad");',
  );
  await invoke(root);
  assert.equal(attempt(root).a.reports[0].status, "malformed");
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    'import fs from "node:fs"; fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+"/proof.json", JSON.stringify({status:"passed"}));',
  );
  await invoke(root, ["--selected"]);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  process.env.VINE_TEST_FILTER = "subset";
  try {
    await invoke(root);
  } finally {
    delete process.env.VINE_TEST_FILTER;
  }
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  await invoke(root);
  assert.deepEqual(verify(root, "routine").missing, []);
  assert.equal(
    fs.readdirSync(path.join(root, ".cloudflare/vine-evidence")).length,
    5,
  );
});
test("reused native reports, altered logs and policy weakening are detected", async (t) => {
  const root = fixture(t, [{ path: "proof.json", adapter: "json-status" }]);
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    'import fs from "node:fs"; fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+"/proof.json", JSON.stringify({status:"passed"}));',
  );
  await invoke(root);
  const first = attempt(root);
  fs.appendFileSync(path.join(first.dir, "command.log"), "tampered");
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  fs.writeFileSync(path.join(root, "proof.mjs"), "process.exit(0)");
  await invoke(root);
  assert.equal(attempt(root).a.reports[0].status, "missing");
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.suites.unit.reports = [];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
});
test("schema, helper version and prohibited selections fail closed", async (t) => {
  const root = fixture(t);
  await assert.rejects(() => invoke(root, ["--unapproved"]), /prohibited/);
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.helperVersion = "9.0.0";
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /unsupported/);
  p.helperVersion = "1.0.0";
  p.unknown = true;
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /unknown/);
});
test("verification identity includes dirty/untracked, deletion, modes and symlink targets, excludes secrets", (t) => {
  const root = fixture(t),
    p = policy(root),
    original = manifest(root, p).digest;
  fs.writeFileSync(path.join(root, ".dev.vars"), "SECRET=never-ingest");
  fs.writeFileSync(path.join(root, ".env"), "SECRET=never-ingest");
  assert.equal(manifest(root, p).digest, original);
  fs.chmodSync(path.join(root, "proof.mjs"), 0o755);
  assert.notEqual(manifest(root, p).digest, original);
  fs.chmodSync(path.join(root, "proof.mjs"), 0o644);
  fs.symlinkSync("proof.mjs", path.join(root, "link"));
  const one = manifest(root, p).digest;
  fs.unlinkSync(path.join(root, "link"));
  fs.symlinkSync("other", path.join(root, "link"));
  assert.notEqual(manifest(root, p).digest, one);
  fs.unlinkSync(path.join(root, "link"));
  fs.unlinkSync(path.join(root, "proof.mjs"));
  assert.ok(
    manifest(root, p).entries.some(
      (e) => e.path === "proof.mjs" && e.kind === "deleted",
    ),
  );
});
test("native adapters distinguish skipped, failed and expected failure", (t) => {
  const root = fixture(t),
    dir = path.join(root, "reports");
  fs.mkdirSync(dir);
  atomic(path.join(dir, "w.json"), {
    schemaVersion: 1,
    status: "failed",
    results: [
      { name: "pass", status: "passed" },
      { name: "skip", status: "skipped" },
      { name: "assertion", status: "failed" },
    ],
  });
  const r = parseReport(dir, { path: "w.json", adapter: "workerd" });
  assert.equal(r.status, "valid");
  assert.deepEqual(r.observation.failed, ["assertion"]);
  assert.deepEqual(r.observation.skipped, ["skip"]);
  atomic(path.join(dir, "p.json"), {
    stats: { expected: 1, unexpected: 0, flaky: 0, skipped: 0 },
    errors: [],
    suites: [
      {
        title: "suite",
        specs: [
          {
            title: "inverted",
            tests: [
              {
                expectedStatus: "failed",
                status: "expected",
                results: [{ status: "failed" }],
              },
            ],
          },
        ],
      },
    ],
  });
  const p = parseReport(dir, { path: "p.json", adapter: "playwright" });
  assert.equal(p.observation.expectedFailure.length, 1);
  assert.equal(p.observation.skipped.length, 0);
  assert.equal(p.observation.failed.length, 0);
});
test("failed setup and collection retain process outcome without invented behavioral red", async (t) => {
  const root = fixture(t, [], "node missing-file.mjs");
  assert.equal(await invoke(root), 1);
  assert.equal(attempt(root).a.failureClassification, "unknown");
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
});
test("interruption forwards termination and unresolved dead wrappers reconcile as orphaned", async (t) => {
  const root = fixture(t, [], "node proof.mjs");
  fs.writeFileSync(path.join(root, "proof.mjs"), "setInterval(()=>{},100);");
  const child = spawn(
    process.execPath,
    [
      path.join(source, "scripts/run-check.mjs"),
      "--root",
      root,
      "--suite",
      "unit",
      "--task",
      "signal",
    ],
    { stdio: "ignore" },
  );
  const exited = new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", resolve);
  });
  await new Promise((resolve) => setTimeout(resolve, 400));
  child.kill("SIGTERM");
  await exited;
  const { a, dir } = attempt(root);
  assert.equal(a.lifecycle, "interrupted");
  a.lifecycle = "started";
  a.pid = 2147483647;
  a.endedAt = null;
  atomic(path.join(dir, "attempt.json"), a);
  verify(root, "routine", [], true);
  assert.equal(readJSON(path.join(dir, "attempt.json")).lifecycle, "orphaned");
});
test("complete diff includes staged/unstaged/untracked renamed/deleted files and safe expected failures", (t) => {
  const root = fixture(t);
  fs.renameSync(
    path.join(root, "proof.mjs"),
    path.join(root, "renamed with space.mjs"),
  );
  git(root, "add", "-A");
  fs.writeFileSync(
    path.join(root, "new\ncase.test.ts"),
    'test.fails("case",()=>expect(false).toBe(true));',
  );
  fs.appendFileSync(path.join(root, "renamed with space.mjs"), "// unstaged");
  const result = audit(root, "HEAD");
  assert.ok(result.changedPaths.includes("proof.mjs"));
  assert.ok(result.changedPaths.includes("new\ncase.test.ts"));
  const changes = result.protectedChanges.find(
    (c) => c.path === "new\ncase.test.ts",
  ).findings;
  assert.ok(changes.some((s) => s.includes("Expected-failure")));
  assert.ok(!changes.some((s) => s.includes("Skip/quarantine")));
});
test("standalone install, foreign cwd, upgrade retirement, edited-file preservation, duplicate detection and removal", async (t) => {
  const root = fixture(t);
  const first = install(root, source, true);
  assert.equal(first.action, "installed");
  const dest = path.join(root, ".agents/skills/vine");
  assert.deepEqual(fs.readdirSync(dest).sort(), [
    "SKILL.md",
    "references",
    "schemas",
    "scripts",
  ]);
  assert.equal(fs.existsSync(path.join(dest, "tests")), false);
  const installedScript = path.join(dest, "scripts/run-check.mjs");
  execFileSync(
    process.execPath,
    [installedScript, "--root", root, "--suite", "unit", "--task", "installed"],
    { cwd: os.tmpdir(), stdio: "pipe" },
  );
  const recordFile = path.join(root, ".vine/install.json"),
    record = readJSON(recordFile);
  fs.writeFileSync(path.join(dest, "retired.mjs"), "old");
  record.files["retired.mjs"] = { digest: sha("old"), mode: 0 };
  atomic(recordFile, record);
  assert.equal(install(root, source, true).action, "updated");
  assert.equal(fs.existsSync(path.join(dest, "retired.mjs")), false);
  fs.appendFileSync(path.join(dest, "SKILL.md"), "local edit");
  assert.throws(() => install(root, source, true), /Locally edited/);
  fs.copyFileSync(path.join(source, "SKILL.md"), path.join(dest, "SKILL.md"));
  const duplicate = path.join(root, ".codex/skills/other");
  fs.mkdirSync(duplicate, { recursive: true });
  fs.copyFileSync(
    path.join(source, "SKILL.md"),
    path.join(duplicate, "SKILL.md"),
  );
  assert.throws(() => install(root, source, true), /Duplicate/);
  fs.rmSync(duplicate, { recursive: true });
  assert.equal(install(root, source, true, true).action, "removed");
  assert.equal(fs.existsSync(dest), false);
  assert.ok(fs.existsSync(path.join(root, ".cloudflare/vine-evidence")));
});

test("trusted policy changes and exceptions bound to another patch are rejected", async (t) => {
  const root = fixture(t);
  await invoke(root);
  const trusted = path.join(os.tmpdir(), `vine-trusted-${Date.now()}.json`);
  fs.copyFileSync(path.join(root, ".vine/project.json"), trusted);
  t.after(() => fs.rmSync(trusted, { force: true }));
  assert.deepEqual(verify(root, "routine", [], false, trusted).missing, []);
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.scopes.routine = [];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(
    () => verify(root, "routine", [], false, trusted),
    /differs from trusted/,
  );
  fs.copyFileSync(trusted, path.join(root, ".vine/project.json"));
  const { exceptionRequest } = await import("../scripts/audit-test-diff.mjs");
  const request = path.join(root, "exception.json");
  atomic(request, {
    invariant: "coverage",
    reason: "retirement",
    replacementEvidence: "review",
    scope: "task",
    owner: "maintainer",
    expiry: "permanent",
    retirementRationale: "removed feature",
    patchDigest: "wrong",
    approvalReference: "external-review",
  });
  assert.throws(
    () => exceptionRequest(audit(root, "HEAD"), request),
    /another patch/,
  );
});
test("applicability defaults to routine and adds owning boundary obligations", (t) => {
  const root = fixture(t),
    p = readJSON(path.join(root, ".vine/project.json"));
  p.routing = [{ id: "app", patterns: ["routes/**"], boundaries: ["logic"] }];
  atomic(path.join(root, ".vine/project.json"), p);
  fs.mkdirSync(path.join(root, "routes"));
  fs.writeFileSync(path.join(root, "routes/index.ts"), "// behavior");
  const r = verify(root, "task", [], false, null, "HEAD");
  assert.equal(r.scope, "routine");
  assert.ok(r.applicability.rules.includes("app"));
  assert.throws(() => verify(root, "task"), /requires --base/);
});
test("skipped, unreachable/empty, filtered and failed native suites cannot establish completion", async (t) => {
  const root = fixture(t, [{ path: "w.json", adapter: "workerd" }]);
  for (const value of [
    {
      status: "passed",
      discovery: "completed-dispatch",
      results: [{ name: "skip", status: "skipped" }],
    },
    { status: "passed", discovery: "completed-dispatch", results: [] },
    {
      status: "filtered",
      discovery: "completed-dispatch",
      filter: "one",
      results: [{ name: "one", status: "passed" }],
    },
    {
      status: "passed",
      discovery: "partial-dispatch",
      results: [{ name: "one", status: "passed" }],
    },
    {
      status: "failed",
      discovery: "partial-dispatch",
      results: [{ name: "assertion", status: "failed" }],
    },
  ]) {
    fs.writeFileSync(
      path.join(root, "proof.mjs"),
      `import fs from 'node:fs';fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/w.json',JSON.stringify(${JSON.stringify({ schemaVersion: 1, ...value })}));`,
    );
    await invoke(root);
    assert.deepEqual(verify(root, "routine").missing, ["unit"]);
  }
});

test("red/green case association uses final reproducer and rejects changed fixtures", async (t) => {
  const { verifyCase } = await import("../scripts/verify-evidence.mjs");
  const root = fixture(t, [{ path: "unit.json", adapter: "vitest" }]);
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.suites.surrounding = { ...p.suites.unit, reports: [] };
  p.scopes.routine.push("surrounding");
  atomic(path.join(root, ".vine/project.json"), p);
  fs.writeFileSync(path.join(root, "value.mjs"), "export default false;");
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    `import value from './value.mjs';import fs from 'node:fs';
    const passed=value===true;fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/unit.json',JSON.stringify({success:passed,testResults:[{name:'proof',assertionResults:[{fullName:'behavior',status:passed?'passed':'failed'},{fullName:'surrounding behavior',status:'passed'}]}]}));process.exitCode=passed?0:1;`,
  );
  git(root, "add", ".");
  git(
    root,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "defective fixture",
  );
  const defective = git(root, "rev-parse", "HEAD");
  assert.equal(
    await run({ root, suite: "unit", task: "case", case: "case-1", extra: [] }),
    1,
  );
  const red = attempt(root).a;
  fs.writeFileSync(path.join(root, "value.mjs"), "export default true;");
  git(root, "add", ".");
  git(
    root,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "correct fixture",
  );
  assert.equal(
    await run({
      root,
      suite: "unit",
      task: "case",
      case: "case-1",
      extra: ["--selected"],
    }),
    0,
  );
  const green = attempt(root).a;
  const fixtureDigest = sha(fs.readFileSync(path.join(root, "proof.mjs"))),
    caseFile = path.join(root, ".cloudflare/case.json");
  atomic(caseFile, {
    schemaVersion: 1,
    id: "case-1",
    requirement: "Value must be true",
    oracle: "Independent true expectation",
    tests: ["proof/behavior"],
    fixturePaths: ["proof.mjs"],
    testFixtureDigest: sha(
      JSON.stringify([{ path: "proof.mjs", digest: fixtureDigest }]),
    ),
    defectiveRevision: defective,
    fixedRevision: git(root, "rev-parse", "HEAD"),
    redAttempt: red.id,
    greenAttempt: green.id,
    surroundingSuites: ["unit"],
    assertion: "value===true",
    setupValidated: true,
    chronology: "red-before-fix",
    approval: null,
  });
  assert.throws(() => verifyCase(root, caseFile), /obligations incomplete/);
  await run({ root, suite: "unit", task: "surrounding", extra: [] });
  await run({ root, suite: "surrounding", task: "case", extra: [] });
  assert.equal(
    verifyCase(root, caseFile).association,
    "mechanically consistent",
  );
  const caseRecord = readJSON(caseFile);
  atomic(caseFile, { ...caseRecord, tests: [...caseRecord.tests, "proof/surrounding behavior"] });
  assert.throws(() => verifyCase(root, caseFile), /Red assertion/);
  atomic(caseFile, caseRecord);
  const unchangedFile = path.join(root, p.evidenceDir, red.id, "attempt.json");
  const beforeUnchanged = readJSON(unchangedFile);
  const unchanged = structuredClone(beforeUnchanged);
  unchanged.pre = structuredClone(green.pre);
  unchanged.post = structuredClone(green.pre);
  atomic(unchangedFile, unchanged);
  assert.throws(() => verifyCase(root, caseFile), /distinct implementation/);
  atomic(unchangedFile, beforeUnchanged);
  const redFile = path.join(root, p.evidenceDir, red.id, "attempt.json");
  const originalRed = readJSON(redFile);
  atomic(redFile, { ...originalRed, argv: ["run", "unrelated"] });
  assert.throws(() => verifyCase(root, caseFile), /Red executed arguments/);
  atomic(redFile, { ...originalRed, policyDigest: "wrong" });
  assert.throws(() => verifyCase(root, caseFile), /historical policy/);
  atomic(redFile, originalRed);
  const greenDir = path.join(root, p.evidenceDir, green.id);
  const reportFile = path.join(greenDir, "native/unit.json");
  const original = readJSON(reportFile);
  const unrelated = structuredClone(original);
  unrelated.testResults[0].assertionResults[0].fullName = "unrelated test";
  atomic(reportFile, unrelated);
  green.reports = [
    parseReport(path.join(greenDir, "native"), p.suites.unit.reports[0]),
  ];
  atomic(path.join(greenDir, "attempt.json"), green);
  assert.throws(() => verifyCase(root, caseFile), /obligations incomplete/);
  atomic(reportFile, original);
  green.reports = [
    parseReport(path.join(greenDir, "native"), p.suites.unit.reports[0]),
  ];
  atomic(path.join(greenDir, "attempt.json"), green);
  assert.equal(
    verifyCase(root, caseFile).association,
    "mechanically consistent",
  );
  const redDir = path.join(root, p.evidenceDir, red.id);
  red.exitCode = null;
  atomic(path.join(redDir, "attempt.json"), red);
  assert.throws(() => verifyCase(root, caseFile), /Red assertion/);
  red.exitCode = 1;
  atomic(path.join(redDir, "attempt.json"), red);
  fs.appendFileSync(path.join(root, "proof.mjs"), "// changed fixture");
  assert.throws(() => verifyCase(root, caseFile), /digest changed/);
});

test("verification input globs include hidden policy, CI and nested dotfiles", (t) => {
  const root = fixture(t),
    p = policy(root),
    original = manifest(root, p);
  assert.ok(original.entries.some((e) => e.path === ".vine/project.json"));
  fs.mkdirSync(path.join(root, ".github/workflows"), { recursive: true });
  fs.writeFileSync(
    path.join(root, ".github/workflows/verify.yml"),
    "changed CI",
  );
  assert.notEqual(manifest(root, p).digest, original.digest);
  fs.mkdirSync(path.join(root, "src"));
  fs.writeFileSync(
    path.join(root, "src/.instructions"),
    "changed instructions",
  );
  assert.ok(
    manifest(root, p).entries.some((e) => e.path === "src/.instructions"),
  );
});

test("patch identity includes executable modes and symlink targets without following them", (t) => {
  const root = fixture(t);
  fs.appendFileSync(path.join(root, "proof.mjs"), "// changed");
  const before = audit(root, "HEAD").patchDigest;
  fs.chmodSync(path.join(root, "proof.mjs"), 0o755);
  assert.notEqual(audit(root, "HEAD").patchDigest, before);
  fs.symlinkSync("/nonexistent/private-target", path.join(root, "test-link"));
  const one = audit(root, "HEAD").patchDigest;
  fs.unlinkSync(path.join(root, "test-link"));
  fs.symlinkSync("/different/private-target", path.join(root, "test-link"));
  assert.notEqual(audit(root, "HEAD").patchDigest, one);
});

test("zero process status cannot override unsuccessful native suite completion", async (t) => {
  const root = fixture(t, [{ path: "unit.json", adapter: "vitest" }]);
  fs.writeFileSync(
    path.join(root, "proof.mjs"),
    `import fs from 'node:fs';fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/unit.json',JSON.stringify({success:false,testResults:[{name:'suite',assertionResults:[{fullName:'one',status:'passed'}]}]}));`,
  );
  assert.equal(await invoke(root), 1);
  assert.equal(attempt(root).a.exitCode, 0);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
});

test("release installation verifies immutable source bytes and rejects uncommitted edits", (t) => {
  const root = fixture(t),
    repo = fs.mkdtempSync(path.join(os.tmpdir(), "vine pinned source "));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  const canonical = path.join(repo, "agents/skills/vine");
  for (const name of RUNTIME) {
    const target = path.join(canonical, name);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(source, name), target);
  }
  git(repo, "init", "-q");
  git(repo, "add", ".");
  git(
    repo,
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "immutable source",
  );
  const result = install(root, canonical);
  assert.equal(result.record.provisional, false);
  assert.equal(result.record.sourceCommit, git(repo, "rev-parse", "HEAD"));
  fs.appendFileSync(path.join(canonical, "SKILL.md"), "changed source");
  assert.throws(() => install(root, canonical), /differs from pinned commit/);
});

test("artifact identity rejects altered sealed bytes even when manifest is unchanged", (t) => {
  const root = fixture(t);
  const output = path.join(root, ".cloudflare/releases/build");
  fs.mkdirSync(output, { recursive: true });
  fs.writeFileSync(path.join(root, ".cloudflare/build-id"), "build");
  fs.writeFileSync(path.join(output, "worker.mjs"), "sealed bytes");
  atomic(path.join(output, "manifest.json"), {
    version: 1,
    buildId: "build",
    files: { "worker.mjs": sha("sealed bytes") },
  });
  return import("../scripts/run-check.mjs").then(({ artifact }) => {
    assert.equal(artifact(root, { artifact: "application" }).buildId, "build");
    fs.writeFileSync(path.join(output, "worker.mjs"), "changed bytes");
    assert.throws(
      () => artifact(root, { artifact: "application" }),
      /Sealed artifact changed/,
    );
  });
});

test("credential stores are never ingested into input manifests", (t) => {
  const root = fixture(t),
    p = policy(root),
    digest = manifest(root, p).digest;
  for (const file of [
    ".npmrc",
    ".pypirc",
    ".netrc",
    ".git-credentials",
    "credentials.json",
    ".codex/auth.json",
  ]) {
    const target = path.join(root, file);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, "synthetic-private-value");
  }
  assert.equal(manifest(root, p).digest, digest);
});

test("malformed completion timestamps cannot satisfy an obligation", async (t) => {
  const root = fixture(t);
  await invoke(root);
  const { a, dir } = attempt(root);
  a.endedAt = "invalid-time";
  atomic(path.join(dir, "attempt.json"), a);
  assert.deepEqual(verify(root, "routine").missing, ["unit"]);
});

test("safe destinations reject dangling symlinks before file creation", (t) => {
  const root = fixture(t);
  fs.symlinkSync("absent-target", path.join(root, "dangling"));
  assert.throws(() => safe(root, "dangling"), /Symlink/);
  assert.throws(() => safe(root, "dangling/report.json"), /Symlink/);
  assert.equal(
    parseReport(root, { path: "dangling", adapter: "vitest" }).status,
    "malformed",
  );
  assert.equal(fs.existsSync(path.join(root, "absent-target")), false);
});

test("malformed Playwright outcomes and failed Vitest files cannot appear green", (t) => {
  const root = fixture(t);
  const report = {
    stats: { expected: 1, unexpected: 0, flaky: 0, skipped: 0 },
    errors: [],
    suites: [
      {
        title: "suite",
        specs: [
          {
            title: "behavior",
            tests: [
              {
                expectedStatus: "passed",
                status: "expected",
                results: [{ status: "failed" }],
              },
            ],
          },
        ],
      },
    ],
  };
  const file = path.join(root, ".cloudflare/report.json");
  atomic(file, report);
  const spec = { path: ".cloudflare/report.json", adapter: "playwright" };
  assert.equal(parseReport(root, spec).observation.failed.length, 1);
  delete report.suites[0].specs[0].tests[0].status;
  atomic(file, report);
  assert.equal(parseReport(root, spec).status, "malformed");
  atomic(file, {
    success: true,
    testResults: [
      {
        name: "file",
        status: "failed",
        assertionResults: [{ title: "test", status: "passed" }],
      },
    ],
  });
  assert.ok(
    parseReport(root, { ...spec, adapter: "vitest" }).limitations.includes(
      "Native suite reports unsuccessful completion",
    ),
  );
});

test("inherited object properties cannot satisfy required schema fields", () => {
  assert.throws(
    () =>
      validate(Object.create({ toString: "inherited" }), {
        type: "object",
        required: ["toString"],
        properties: { toString: { type: "string" } },
        additionalProperties: false,
      }),
    /missing toString/,
  );
  assert.throws(
    () =>
      validate(
        { toString: "unknown" },
        {
          type: "object",
          properties: {},
          additionalProperties: false,
        },
      ),
    /unknown toString/,
  );
});

test("explicit ignored nonsecret inputs override broad exclusions", (t) => {
  const root = fixture(t);
  fs.mkdirSync(path.join(root, ".cloudflare"));
  const input = ".cloudflare/required-fixture.json";
  fs.writeFileSync(path.join(root, input), "first");
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.inputs.extra = [input];
  atomic(path.join(root, ".vine/project.json"), p);
  p.inputs.relevant = [input];
  atomic(path.join(root, ".vine/project.json"), p);
  const before = manifest(root, policy(root));
  assert.ok(before.entries.some((e) => e.path === input));
  fs.writeFileSync(path.join(root, input), "changed");
  assert.notEqual(manifest(root, policy(root)).digest, before.digest);
  p.inputs.extra = [".env"];
  fs.writeFileSync(path.join(root, ".env"), "synthetic private content");
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /Secret cannot/);
});

test("application authority is protected even outside protected globs", (t) => {
  const root = fixture(t);
  fs.writeFileSync(path.join(root, "authority.md"), "acceptance requirements");
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.authority = ["authority.md"];
  p.protected = ["tests/**"];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.ok(
    audit(root, "HEAD").protectedChanges.some((c) => c.path === "authority.md"),
  );
});

test("empty coverage is rejected and mandatory controls bypass exclusions", (t) => {
  const root = fixture(t), p = policy(root);
  p.inputs.include = [];
  assert.throws(() => manifest(root, p), /coverage missing/);
  p.inputs.include = ["proof.mjs"];
  p.inputs.exclude = ["package.json", ".vine/**"];
  const original = manifest(root, p).digest;
  fs.writeFileSync(path.join(root, "package.json"), '{"scripts":{"test":"unrelated"}}');
  assert.notEqual(manifest(root, p).digest, original);
  p.scopes.full = [];
  assert.throws(() => schema("project", p), /too few items/);
});

test("instruction Markdown never uses documentation routing", (t) => {
  const root = fixture(t), p = policy(root);
  p.documentationPaths = ["**/*.md"];
  atomic(path.join(root, ".vine/project.json"), p);
  git(root, "add", ".");
  git(root, "-c", "user.name=Fixture", "-c", "user.email=f@example.invalid", "commit", "-qm", "routing");
  for (const name of ["AGENTS.md", "agents/skills/demo/SKILL.md", "unknown.md"]) {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), "instructions");
    if (name !== "unknown.md") assert.equal(verify(root, "task", [], false, null, "HEAD").applicability.documentationOnly, false);
    fs.unlinkSync(path.join(root, name));
  }
  fs.mkdirSync(path.join(root, "docs"));
  fs.writeFileSync(path.join(root, "docs/guide.md"), "guide");
  assert.equal(verify(root, "task", [], false, null, "HEAD").applicability.documentationOnly, true);
});

test("built reports require nonempty unique execution and declared suite identities", (t) => {
  const root = fixture(t), dir = path.join(root, "native");
  fs.mkdirSync(dir);
  for (const boundaries of [[], ["one", "one"], [123]]) {
    atomic(path.join(dir, "built.json"), { status: "passed", buildId: "id", manifestSHA256: "hash", boundaries });
    assert.equal(parseReport(dir, { path: "built.json", adapter: "built" }).status, "malformed");
  }
  const p = policy(root);
  p.suites.unit.reports = [{ path: "built.json", adapter: "built" }];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /expectedBoundaries/);
});

test("Vitest configured nested report output is executed and verified", async (t) => {
  const root = fixture(t, [{ path: "custom/results.json", adapter: "vitest" }]);
  fs.writeFileSync(path.join(root, "proof.mjs"), `import fs from 'node:fs';
    const output = process.argv.find((arg) => arg.startsWith('--outputFile=')).slice('--outputFile='.length);
    fs.writeFileSync(output, JSON.stringify({success:true,testResults:[{name:'suite',assertionResults:[{fullName:'behavior',status:'passed'}]}]}));`);
  assert.equal(await invoke(root), 0);
  assert.deepEqual(verify(root, "routine").missing, []);
  const p = policy(root);
  p.suites.unit.reports.push({ path: "second.json", adapter: "vitest" });
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /ambiguous/);
});

test("sensitive patch exclusions prevent exception binding", async (t) => {
  const root = fixture(t);
  fs.writeFileSync(path.join(root, ".npmrc"), "private value");
  const result = audit(root, "HEAD");
  assert.equal(result.patchIdentityComplete, false);
  const { exceptionRequest } = await import("../scripts/audit-test-diff.mjs");
  assert.throws(() => exceptionRequest(result, "unused.json"), /identity incomplete/);
});

test("installer lock excludes competing process and preserves winner inventory", (t) => {
  const root = fixture(t);
  install(root, source, true);
  const record = fs.readFileSync(path.join(root, ".vine/install.json"));
  // Hold the same exclusion boundary as an active transaction, then invoke a second process.
  const lock = path.join(root, ".cloudflare/vine-install/lock");
  fs.mkdirSync(lock);
  assert.throws(() => execFileSync(process.execPath, [path.join(source, "scripts/install.mjs"), "--root", root, "--development", "true"], { stdio: "pipe" }), /Command failed/);
  assert.deepEqual(fs.readFileSync(path.join(root, ".vine/install.json")), record);
  fs.rmSync(lock, { recursive: true });
  assert.equal(install(root, source, true).action, "updated");
  assert.equal(fs.existsSync(lock), false);
});

test("completion CLI binds policy, task scope and independently supplied base", async (t) => {
  const root = fixture(t), cli = path.join(source, "scripts/verify-evidence.mjs");
  const baseline = path.join(os.tmpdir(), `vine-policy-${path.basename(root)}.json`);
  t.after(() => fs.rmSync(baseline, { force: true }));
  fs.copyFileSync(path.join(root, ".vine/project.json"), baseline);
  const digest = sha(fs.readFileSync(baseline)), base = git(root, "rev-parse", "HEAD");
  const call = (extra) => execFileSync(process.execPath, [cli, "--root", root, ...extra], { stdio: "pipe" });
  const approved = ["--trusted-policy", baseline, "--trusted-policy-sha256", digest, "--trusted-base", base];
  assert.throws(() => call([]), /Command failed/);
  await invoke(root);
  assert.equal(JSON.parse(call(approved)).baselineDigest, digest);
  assert.throws(() => call([...approved, "--scope", "documentation"]), /Command failed/);
  const wrongDigest = [...approved]; wrongDigest[3] = "0".repeat(64);
  assert.throws(() => call(wrongDigest), /Command failed/);
  git(root, "-c", "user.name=Fixture", "-c", "user.email=f@example.invalid", "commit", "--allow-empty", "-qm", "next");
  assert.throws(() => call([...approved, "--base", "HEAD"]), /Command failed/);
});

test("safe rejects Windows drive-relative paths on every platform", (t) => {
  const root = fixture(t);
  assert.throws(() => safe(root, "D:escape.txt"), /Unsafe/);
});

test("competing installer at destination commit cannot remove winner ownership", async (t) => {
  const root = fixture(t), release = path.join(root, ".cloudflare/release-installer");
  const child = spawn(process.execPath, ["--input-type=module", "-e", `
    import fs from 'node:fs';
    import { install } from ${JSON.stringify(new URL('../scripts/install.mjs', import.meta.url).href)};
    const rename = fs.renameSync;
    fs.renameSync = function(from, to) {
      if (to.endsWith('/.agents/skills/vine')) {
        process.stdout.write('at-commit\\n');
        const deadline = Date.now() + 10000;
        while (!fs.existsSync(${JSON.stringify(release)})) {
          if (Date.now() > deadline) throw Error('coordination timeout');
          Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 10);
        }
      }
      return rename(from, to);
    };
    install(${JSON.stringify(root)}, ${JSON.stringify(source)}, true);
  `], { stdio: ["ignore", "pipe", "pipe"] });
  t.after(() => child.kill());
  const completion = new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", (code) => code === 0 ? resolve() : reject(Error(`installer exited ${code}`)));
  });
  await new Promise((resolve, reject) => {
    child.stdout.once("data", resolve);
    child.once("error", reject);
    child.once("exit", (code) => { if (code !== 0) reject(Error(`installer exited ${code}`)); });
  });
  assert.throws(() => install(root, source, true), /locked/);
  assert.equal(fs.existsSync(path.join(root, ".vine/install.json")), false);
  fs.writeFileSync(release, "continue");
  await completion;
  const record = readJSON(path.join(root, ".vine/install.json"));
  assert.equal(record.files["SKILL.md"].digest, sha(fs.readFileSync(path.join(root, ".agents/skills/vine/SKILL.md"))));
  assert.equal(install(root, source, true, true).action, "removed");
});

test("built suite rejects partial and additional identities and accepts exact coverage", async (t) => {
  const root = fixture(t, [{ path: "built.json", adapter: "built" }]);
  const p = readJSON(path.join(root, ".vine/project.json"));
  p.suites.unit.artifact = "application";
  p.suites.unit.expectedBoundaries = ["worker", "static"];
  atomic(path.join(root, ".vine/project.json"), p);
  const output = path.join(root, ".cloudflare/releases/build");
  fs.mkdirSync(output, { recursive: true });
  fs.writeFileSync(path.join(root, ".cloudflare/build-id"), "build");
  fs.writeFileSync(path.join(output, "worker.mjs"), "sealed");
  atomic(path.join(output, "manifest.json"), {version:1,buildId:"build",files:{"worker.mjs":sha("sealed")}});
  for (const boundaries of [[], ["worker"], ["worker", "static", "extra"], ["static", "worker"]]) {
    fs.writeFileSync(path.join(root, "proof.mjs"), `import fs from 'node:fs';import {createHash} from 'node:crypto';
      const manifest = fs.readFileSync('.cloudflare/releases/build/manifest.json');
      fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/built.json',JSON.stringify({status:'passed',buildId:'build',manifestSHA256:createHash('sha256').update(manifest).digest('hex'),boundaries:${JSON.stringify(boundaries)}}));`);
    await invoke(root);
    assert.deepEqual(verify(root, "routine").missing, boundaries.length === 2 ? [] : ["unit"]);
  }
  fs.writeFileSync(path.join(output, "unlisted.mjs"), "runtime");
  const { artifact } = await import("../scripts/run-check.mjs");
  assert.throws(() => artifact(root, p.suites.unit), /inventory incomplete/);
});

test("task routing preserves both sides of renames and all unmatched paths", (t) => {
  const root = fixture(t), p = policy(root);
  p.routing = [{ id: "original", patterns: ["proof.mjs"], boundaries: ["logic"] }];
  atomic(path.join(root, ".vine/project.json"), p);
  fs.renameSync(path.join(root, "proof.mjs"), path.join(root, "renamed.mjs"));
  p.inputs.relevant = ["*.mjs"];
  atomic(path.join(root, ".vine/project.json"), p);
  git(root, "add", "-A");
  const result = verify(root, "task", [], false, null, "HEAD");
  assert.ok(result.applicability.changedPaths.includes("proof.mjs"));
  assert.ok(result.applicability.changedPaths.includes("renamed.mjs"));
  assert.deepEqual(result.applicability.rules, ["original"]);
  assert.ok(result.applicability.unmatchedBehavioralChanges.includes("renamed.mjs"));
});

test("task input completeness rejects unclassified new and tracked files, lists explicit exclusions", async (t) => {
  const root = fixture(t), p = policy(root);
  fs.writeFileSync(path.join(root, "feature.mjs"), "original");
  git(root, "add", ".");
  git(root, "-c", "user.name=Fixture", "-c", "user.email=f@example.invalid", "commit", "-qm", "feature");
  p.inputs.include = ["proof.mjs"];
  atomic(path.join(root, ".vine/project.json"), p);
  await invoke(root);
  fs.writeFileSync(path.join(root, "feature.mjs"), "changed");
  assert.throws(() => verify(root, "task", [], false, null, "HEAD"), /omitted.*feature.mjs/);
  p.inputs.exclude.push("feature.mjs");
  atomic(path.join(root, ".vine/project.json"), p);
  assert.ok(verify(root, "task", [], false, null, "HEAD").applicability.exclusions.includes("feature.mjs"));
  fs.writeFileSync(path.join(root, "new.mjs"), "new");
  assert.throws(() => verify(root, "task", [], false, null, "HEAD"), /omitted.*new.mjs/);
});

test("behavioral suites require scenario reports and report destinations are unique", (t) => {
  const root = fixture(t), p = policy(root);
  p.suites.unit.category = "behavioral";
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /scenario reports/);
  p.suites.unit.reports = [{ path: "status.json", adapter: "json-status" }];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /scenario reports/);
  p.suites.unit.reports = [{ path: "unit.json", adapter: "vitest" }];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.equal(policy(root).suites.unit.category, "behavioral");
  p.suites.unit.reports.push({ path: "./unit.json", adapter: "workerd" });
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /duplicate report/);
});

test("blank native identities and unknown adapters are malformed", (t) => {
  const root = fixture(t);
  atomic(path.join(root, "report.json"), { schemaVersion: 1, status: "passed", discovery: "completed-dispatch", results: [{ name: "  ", status: "passed" }] });
  assert.equal(parseReport(root, { path: "report.json", adapter: "workerd" }).status, "malformed");
  atomic(path.join(root, "report.json"), { status: "passed" });
  assert.equal(parseReport(root, { path: "report.json", adapter: "unknown" }).status, "malformed");
  atomic(path.join(root, "report.json"), { success: true, testResults: [{ name: "file", assertionResults: [{ fullName: "", status: "passed" }] }] });
  assert.equal(parseReport(root, { path: "report.json", adapter: "vitest" }).status, "malformed");
});

test("required report failures affect wrapper exit while preserving process exit", async (t) => {
  const root = fixture(t, [{ path: "proof.json", adapter: "json-status" }]);
  assert.equal(await invoke(root), 1);
  assert.equal(attempt(root).a.exitCode, 0);
  assert.equal(attempt(root).a.reports[0].status, "missing");
  fs.writeFileSync(path.join(root, "proof.mjs"), `import fs from 'node:fs';fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/proof.json', '{bad');`);
  assert.equal(await invoke(root), 1);
  assert.equal(attempt(root).a.exitCode, 0);
  assert.equal(attempt(root).a.reports[0].status, "malformed");
});

test("explicit sensitive paths are never ingested and block patch exception binding", (t) => {
  const root = fixture(t), p = policy(root);
  p.inputs.sensitive = ["private/**"];
  atomic(path.join(root, ".vine/project.json"), p);
  const original = manifest(root, p).digest;
  for (const file of ["private/custom.json", "service-account.json", "secrets.yaml", "api-token.txt"]) {
    fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
    fs.writeFileSync(path.join(root, file), "synthetic private bytes");
  }
  assert.equal(manifest(root, p).digest, original);
  assert.equal(audit(root, "HEAD").patchIdentityComplete, false);
  p.inputs.sensitive.push("package.json");
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /Secret cannot/);
  p.inputs.sensitive.pop();
  p.authority = ["private/custom.json"];
  atomic(path.join(root, ".vine/project.json"), p);
  assert.throws(() => policy(root), /Secret cannot/);
});

test("installer detects Claude plugin duplicate discovery", (t) => {
  const root = fixture(t), duplicate = path.join(root, ".claude/plugins/demo/skills/vine");
  fs.mkdirSync(duplicate, { recursive: true });
  fs.copyFileSync(path.join(source, "SKILL.md"), path.join(duplicate, "SKILL.md"));
  assert.throws(() => install(root, source, true), /Duplicate VINE/);
  assert.equal(fs.existsSync(path.join(root, ".vine/install.json")), false);
});

test("authority Markdown remains behavioral despite passive documentation globs", (t) => {
  const root = fixture(t), p = policy(root);
  fs.writeFileSync(path.join(root, "requirements.md"), "requirements");
  p.authority = ["requirements.md"];
  p.documentationPaths = ["**/*.md"];
  atomic(path.join(root, ".vine/project.json"), p);
  git(root, "add", ".");
  git(root, "-c", "user.name=Fixture", "-c", "user.email=f@example.invalid", "commit", "-qm", "authority");
  fs.appendFileSync(path.join(root, "requirements.md"), " changed guarantee");
  assert.equal(verify(root, "task", [], false, null, "HEAD").applicability.documentationOnly, false);
});

test("same-HEAD implementation fix establishes red/green with the final reproducer", async (t) => {
  const { verifyCase } = await import("../scripts/verify-evidence.mjs");
  const root = fixture(t, [{ path: "w.json", adapter: "workerd" }]);
  fs.writeFileSync(path.join(root, "value.mjs"), "export default false;");
  fs.writeFileSync(path.join(root, "proof.mjs"), `import value from './value.mjs';import fs from 'node:fs';
    fs.writeFileSync(process.env.FOUNDATION_EVIDENCE_DIR+'/w.json', JSON.stringify({schemaVersion:1,status:value?'passed':'failed',discovery:'completed-dispatch',results:[{name:'behavior',status:value?'passed':'failed'}]}));process.exitCode=value?0:1;`);
  const call = () => run({ root, suite: "unit", task: "case", case: "dirty-fix", extra: [] });
  assert.equal(await call(), 1);
  const red = attempt(root).a;
  fs.writeFileSync(path.join(root, "value.mjs"), "export default true;");
  assert.equal(await call(), 0);
  const green = attempt(root).a;
  assert.equal(red.evaluatedRevision, green.evaluatedRevision);
  const caseFile = path.join(root, ".cloudflare/case.json");
  atomic(caseFile, {
    schemaVersion:1,id:"dirty-fix",requirement:"true value",oracle:"true expectation",tests:["behavior"],fixturePaths:["proof.mjs"],
    testFixtureDigest:sha(JSON.stringify([{path:"proof.mjs",digest:sha(fs.readFileSync(path.join(root,"proof.mjs")))}])),
    defectiveRevision:red.evaluatedRevision,fixedRevision:green.evaluatedRevision,redAttempt:red.id,greenAttempt:green.id,
    surroundingSuites:["unit"],assertion:"value is true",setupValidated:true,chronology:"red-before-fix",approval:null,
  });
  assert.equal(verifyCase(root, caseFile).association, "mechanically consistent");
});
