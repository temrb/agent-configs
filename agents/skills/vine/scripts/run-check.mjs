import fs from "node:fs";
import path from "node:path";
import { spawn, execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import {
  isMain,
  args,
  options,
  rootAt,
  policy,
  manifest,
  helperIdentity,
  executable,
  git,
  sha,
  atomic,
  safe,
  VERSION,
  main,
  schema,
} from "./common.mjs";
import { parseReport } from "./reports.mjs";

export function artifact(root, suite) {
  if (suite.artifact === "none") return null;
  const prefix = suite.artifact === "authority" ? "authority/" : "";
  const id = fs
    .readFileSync(safe(root, `${prefix}.cloudflare/build-id`), "utf8")
    .trim();
  if (!/^[A-Za-z0-9_-]+$/.test(id)) throw Error("Invalid build identity");
  const relative = `.cloudflare/releases/${prefix}${id}`;
  const bytes = fs.readFileSync(safe(root, `${relative}/manifest.json`));
  const sealed = JSON.parse(bytes);
  if (
    sealed.version !== 1 ||
    sealed.buildId !== id ||
    !sealed.files ||
    !Object.keys(sealed.files).length
  )
    throw Error("Invalid sealed artifact manifest");
  const inventory = (prefix = "") => fs.readdirSync(safe(root, `${relative}/${prefix}`)).flatMap((name) => {
    const file = prefix ? `${prefix}/${name}` : name;
    const location = safe(root, `${relative}/${file}`);
    const stat = fs.lstatSync(location);
    if (stat.isDirectory()) return inventory(file);
    if (!stat.isFile()) throw Error(`Non-file sealed artifact: ${file}`);
    return file === "manifest.json" ? [] : [file];
  });
  if (JSON.stringify(inventory().sort()) !== JSON.stringify(Object.keys(sealed.files).sort()))
    throw Error("Sealed artifact inventory incomplete");
  const actual = [];
  for (const name of Object.keys(sealed.files).sort()) {
    const digest = sha(fs.readFileSync(safe(root, `${relative}/${name}`)));
    if (digest !== sealed.files[name])
      throw Error(`Sealed artifact changed: ${name}`);
    actual.push([name, digest]);
  }
  return {
    path: relative,
    digest: sha(bytes),
    buildId: id,
    filesDigest: sha(JSON.stringify(actual)),
  };
}
export async function run(a) {
  options(a, ["root", "suite", "task", "case", "baseline", "setup"]);
  const root = rootAt(a.root),
    p = policy(root),
    suite = p.suites[a.suite];
  if (!Object.hasOwn(p.suites, a.suite) || !a.task)
    throw Error("Specify approved --suite and --task");
  if (
    a.extra.some(
      (arg) =>
        !suite.selection.some((pattern) => new RegExp(pattern).test(arg)),
    )
  )
    throw Error("Selection argument prohibited by project policy");
  const exe = executable("bun");
  const bun = execFileSync(exe, ["--version"], { encoding: "utf8" }).trim();
  if (bun !== p.runtime.bun)
    throw Error(`Requires Bun ${p.runtime.bun}; found ${bun}`);
  const pre = manifest(root, p),
    id = randomUUID();
  const dir = safe(root, `${p.evidenceDir}/${id}`);
  fs.mkdirSync(dir, { recursive: true });
  const reportsDir = path.join(dir, "native");
  fs.mkdirSync(reportsDir);
  for (const spec of suite.reports) fs.mkdirSync(path.dirname(safe(reportsDir, spec.path)), { recursive: true });
  fs.copyFileSync(safe(root, ".vine/project.json"), path.join(dir, "policy.json"));
  fs.copyFileSync(safe(root, "package.json"), path.join(dir, "package.json"));
  const built = artifact(root, suite);
  const suiteArgs = suite.args.map((arg) =>
    arg === "{artifact}" ? (built?.path ?? "") : arg,
  );
  const argv = ["run", suite.script, ...suiteArgs, ...a.extra];
  if (suite.reports.some((r) => r.adapter === "vitest"))
    argv.push(
      "--reporter=json",
      `--outputFile=${safe(reportsDir, suite.reports.find((r) => r.adapter === "vitest").path)}`,
    );
  const environment = { node: process.versions.node, bun };
  for (const key of suite.filterEnv)
    if (process.env[key]) environment[key] = process.env[key];
  const now = () => new Date().toISOString();
  const attempt = {
    schemaVersion: 1,
    helperVersion: VERSION,
    helperDigest: helperIdentity(),
    adapterVersion: 1,
    id,
    pid: process.pid,
    task: a.task,
    case: a.case ?? null,
    trust: {
      source: "local",
      ciRun: process.env.GITHUB_RUN_ID
        ? `${process.env.GITHUB_RUN_ID}/${process.env.GITHUB_RUN_ATTEMPT ?? "unknown"}`
        : null,
    },
    project: root,
    baselineRevision: a.baseline
      ? git(root, "rev-parse", "--verify", `${a.baseline}^{commit}`).trim()
      : git(root, "rev-parse", "HEAD").trim(),
    evaluatedRevision: git(root, "rev-parse", "HEAD").trim(),
    startedAt: now(),
    endedAt: null,
    executable: exe,
    argv,
    cwd: root,
    suite: a.suite,
    selection: a.extra,
    environment,
    setup: a.setup ?? null,
    pre,
    post: null,
    policyDigest: sha(fs.readFileSync(path.join(root, ".vine/project.json"))),
    lifecycle: "started",
    exitCode: null,
    signal: null,
    failureClassification: "unknown",
    reports: [],
    logs: [],
    artifact: built,
    limitations: [
      "Local pre/post equality cannot exclude edit-and-restore races; evidence is not independent CI attestation.",
      "Environment setup is declared, not independently validated.",
    ],
  };
  const output = path.join(dir, "attempt.json");
  atomic(output, schema("attempt", attempt));
  console.log(`VINE attempt ${id}: ${output}`);
  const logFile = path.join(dir, "command.log"),
    fd = fs.openSync(logFile, "wx", 0o600);
  const max = 8 * 1024 * 1024;
  let bytes = 0,
    truncated = false,
    interrupted = null;
  const child = spawn(exe, argv, {
    cwd: root,
    detached: process.platform !== "win32",
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, FOUNDATION_EVIDENCE_DIR: reportsDir },
  });
  const handlers = new Map();
  for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) {
    const handler = () => {
      interrupted = signal;
      try {
        if (process.platform !== "win32") process.kill(-child.pid, signal);
        else child.kill(signal);
      } catch {}
    };
    handlers.set(signal, handler);
    process.on(signal, handler);
  }
  function consume(chunk, stream) {
    stream.write(chunk);
    const part = chunk.subarray(0, Math.max(0, max - bytes));
    fs.writeSync(fd, part);
    bytes += part.length;
    if (part.length < chunk.length) truncated = true;
  }
  child.stdout.on("data", (c) => consume(c, process.stdout));
  child.stderr.on("data", (c) => consume(c, process.stderr));
  const result = await new Promise((resolve) => {
    child.on("error", (error) => resolve({ code: null, signal: null, error }));
    child.on("close", (code, signal) => resolve({ code, signal }));
  });
  for (const [signal, handler] of handlers) process.off(signal, handler);
  fs.closeSync(fd);
  attempt.endedAt = now();
  attempt.lifecycle =
    interrupted || result.signal ? "interrupted" : "completed";
  attempt.exitCode = result.code;
  attempt.signal = result.signal ?? interrupted;
  attempt.logs = [
    { path: "command.log", digest: sha(fs.readFileSync(logFile)), truncated },
  ];
  if (result.error) {
    attempt.failureClassification = "environment";
    attempt.limitations.push(result.error.message);
  }
  attempt.reports = suite.reports.map((spec) => parseReport(reportsDir, spec));
  try {
    attempt.post = manifest(root, p);
  } catch (e) {
    attempt.limitations.push(`Post identity unavailable: ${e.message}`);
  }
  // An assertion-shaped failure is insufficient to validate its requirement or setup.
  if (truncated)
    attempt.limitations.push(
      "Captured log exceeded 8 MiB; inspect runner-native evidence",
    );
  atomic(output, schema("attempt", attempt));
  console.log(
    `VINE ${id}: ${attempt.lifecycle}, exit ${result.code}, report states ${attempt.reports.map((r) => r.status).join(",") || "not required"}`,
  );
  const evidenceComplete = attempt.post?.digest === attempt.pre.digest &&
    attempt.reports.every((r) => r.status === "valid" &&
      !r.observation?.failed.length &&
      !r.limitations.includes("Native suite reports unsuccessful completion") &&
      !r.limitations.includes("Playwright global errors present") &&
      (r.adapter === "json-status" || (r.observation?.executed.length && r.observation.discovery === "observed")));
  console.log(`VINE evidence capture: ${evidenceComplete ? "complete" : "incomplete"}; completion still requires verification`);
  return result.code === 0 && !interrupted && !result.signal && evidenceComplete ? 0 : 1;
}
if (isMain(import.meta.url))
  main(async () => {
    process.exitCode = await run(args());
  });
