import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
export const VERSION = "1.0.0";
export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const sha = (data) => createHash("sha256").update(data).digest("hex");
export const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
export function atomic(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const temp = `${p}.${randomUUID()}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(value, null, 2) + "\n", {
    mode: 0o600,
  });
  fs.renameSync(temp, p);
}
export function validate(value, schema, at = "$") {
  if (schema.const !== undefined && value !== schema.const)
    throw Error(`${at}: unsupported value`);
  if (schema.enum && !schema.enum.includes(value))
    throw Error(`${at}: invalid enum`);
  const type = Array.isArray(value)
    ? "array"
    : value === null
      ? "null"
      : typeof value;
  if (
    schema.type &&
    !(Array.isArray(schema.type) ? schema.type : [schema.type]).includes(type)
  )
    throw Error(`${at}: expected ${schema.type}`);
  if (type === "object") {
    for (const key of schema.required ?? [])
      if (!Object.hasOwn(value, key)) throw Error(`${at}: missing ${key}`);
    for (const [key, child] of Object.entries(value)) {
      const rule =
        schema.properties && Object.hasOwn(schema.properties, key)
          ? schema.properties[key]
          : schema.additionalProperties;
      if (rule === false || rule === undefined)
        throw Error(`${at}: unknown ${key}`);
      if (rule !== true) validate(child, rule, `${at}.${key}`);
    }
  }
  if (type === "array") {
    if (schema.minItems && value.length < schema.minItems)
      throw Error(`${at}: too few items`);
    if (
      schema.uniqueItems &&
      new Set(value.map((v) => JSON.stringify(v))).size !== value.length
    )
      throw Error(`${at}: duplicate items`);
    value.forEach((v, i) => validate(v, schema.items, `${at}[${i}]`));
  }
  if (type === "string") {
    if (schema.minLength && value.length < schema.minLength)
      throw Error(`${at}: empty string`);
    if (schema.pattern && !new RegExp(schema.pattern).test(value))
      throw Error(`${at}: invalid format`);
  }
}
export function schema(name, value) {
  validate(
    value,
    readJSON(path.join(HERE, "../schemas", `${name}.schema.json`)),
  );
  return value;
}
export function args(argv = process.argv.slice(2)) {
  const out = { extra: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--") {
      out.extra = argv.slice(i + 1);
      break;
    }
    if (
      !argv[i].startsWith("--") ||
      !argv[i + 1] ||
      argv[i + 1].startsWith("--")
    )
      throw Error(`Expected --option value: ${argv[i]}`);
    const key = argv[i].slice(2);
    if (key in out) throw Error(`Duplicate option ${key}`);
    out[key] = argv[++i];
  }
  return out;
}
export function options(a, allowed) {
  for (const key of Object.keys(a))
    if (!["extra", ...allowed].includes(key))
      throw Error(`Unknown option --${key}`);
}
export function git(root, ...argv) {
  return execFileSync("git", ["-C", root, ...argv], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    maxBuffer: 32 * 1024 * 1024,
  });
}
export function rootAt(explicit) {
  if (explicit) return fs.realpathSync(explicit);
  let dir = process.cwd();
  while (!fs.existsSync(path.join(dir, ".vine/project.json"))) {
    const parent = path.dirname(dir);
    if (parent === dir)
      throw Error("No .vine/project.json; pass --root PROJECT");
    dir = parent;
  }
  return fs.realpathSync(dir);
}
export function safe(root, relative) {
  if (
    path.isAbsolute(relative) ||
    /^[A-Za-z]:/.test(relative) ||
    relative.includes("\0") ||
    relative.split(/[\\/]/).includes("..")
  )
    throw Error(`Unsafe relative path: ${relative}`);
  const dest = path.resolve(root, relative);
  const containment = path.relative(root, dest);
  if (containment === ".." || containment.startsWith(`..${path.sep}`) || path.isAbsolute(containment))
    throw Error(`Outside project root: ${relative}`);
  let cursor = dest;
  while (cursor !== root) {
    if (fs.lstatSync(cursor, { throwIfNoEntry: false })?.isSymbolicLink())
      throw Error(`Symlink path: ${relative}`);
    const parent = path.dirname(cursor);
    if (parent === cursor) throw Error(`Outside project root: ${relative}`);
    cursor = parent;
  }
  return dest;
}
export function policy(root, trustedFile = null) {
  if (process.versions.node !== "24.19.0")
    throw Error("VINE requires tested Node 24.19.0");
  const p = schema(
    "project",
    readJSON(trustedFile ?? safe(root, ".vine/project.json")),
  );
  const pkg = readJSON(safe(root, "package.json"));
  for (const [id, suite] of Object.entries(p.suites)) {
    if (!pkg.scripts?.[suite.script])
      throw Error(`Suite ${id}: missing package script ${suite.script}`);
    const reportPaths = suite.reports.map((report) => safe(root, report.path));
    if (new Set(reportPaths).size !== reportPaths.length)
      throw Error(`Suite ${id}: duplicate report destination`);
    if (suite.category === "behavioral" && !suite.reports.some((r) => r.adapter !== "json-status"))
      throw Error(`Suite ${id}: behavioral checks require scenario reports`);
    if (suite.reports.filter((r) => r.adapter === "vitest").length > 1)
      throw Error(`Suite ${id}: ambiguous Vitest output destinations`);
    if (suite.reports.some((r) => r.adapter === "built") &&
        (suite.artifact === "none" || !suite.expectedBoundaries?.length))
      throw Error(`Suite ${id}: built reports require artifact and expectedBoundaries`);
    for (const expression of suite.selection) new RegExp(expression);
  }
  for (const [scope, ids] of Object.entries(p.scopes))
    for (const id of ids)
      if (!p.suites[id]) throw Error(`${scope}: unknown suite ${id}`);
  for (const [boundary, ids] of Object.entries(p.boundaries))
    for (const id of ids)
      if (!p.suites[id]) throw Error(`${boundary}: unknown suite ${id}`);
  for (const rule of p.routing)
    for (const boundary of rule.boundaries)
      if (!p.boundaries[boundary])
        throw Error(`Routing ${rule.id}: unknown boundary ${boundary}`);
  for (const doc of ["package.json", ".vine/project.json", ...p.authority])
    if (secret(doc, p.inputs.sensitive)) throw Error(`Secret cannot be authority: ${doc}`);
    else if (!fs.existsSync(safe(root, doc)))
      throw Error(`Missing authority ${doc}`);
  for (const input of p.inputs.extra)
    if (secret(input, p.inputs.sensitive))
      throw Error(`Secret cannot be a declared verification input: ${input}`);
    else if (!fs.existsSync(safe(root, input)))
      throw Error(`Missing declared input ${input}`);
  if (p.evidenceDir !== ".cloudflare/vine-evidence")
    throw Error("Unsupported evidence directory");
  return p;
}
// Conservative path globs: wildcards include dotfiles, which own CI and policy.
// Supported syntax is *, ** and ?; other characters are literal.
export function matches(name, pattern) {
  let regex = "^";
  for (let i = 0; i < pattern.length; i++) {
    if (pattern[i] === "*" && pattern[i + 1] === "*") {
      i++;
      if (pattern[i + 1] === "/") {
        i++;
        regex += "(?:.*/)?";
      } else regex += ".*";
    } else if (pattern[i] === "*") regex += "[^/]*";
    else if (pattern[i] === "?") regex += "[^/]";
    else regex += pattern[i].replace(/[|\\{}()[\]^$+?.]/g, "\\$&");
  }
  return new RegExp(regex + "$", "s").test(name);
}
export function secret(name, patterns = []) {
  if (patterns.some((pattern) => matches(name, pattern))) return true;
  const base = path.posix.basename(name);
  if (
    [
      ".npmrc",
      ".pypirc",
      ".netrc",
      ".git-credentials",
      "credentials.json",
      "service-account.json",
      "secrets.yaml",
      "secrets.yml",
      "api-token.txt",
    ].includes(base) ||
    /(^|\/)\.codex\/auth\.json$/.test(name)
  )
    return true;
  return (
    (/^(\.env(?:\.|$)|\.dev\.vars|credentials$|id_(rsa|ed25519)|.*\.(pem|key)$)/i.test(
      base,
    ) &&
      !/\.example$/.test(base)) ||
    /(^|\/)(\.aws|\.ssh)(\/|$)/.test(name)
  );
}
export function manifest(root, p) {
  const names = new Set(
    git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
      .split("\0")
      .filter(Boolean),
  );
  const mandatory = new Set(["package.json", ".vine/project.json", ...p.authority]);
  for (const input of [...p.inputs.extra, ...mandatory]) names.add(input);
  for (const pattern of p.inputs.relevant) {
    if (![...names].some((name) => !mandatory.has(name) && !secret(name, p.inputs.sensitive) &&
        matches(name, pattern) &&
        (p.inputs.extra.includes(name) || !p.inputs.exclude.some((excluded) => matches(name, excluded))) &&
        (p.inputs.extra.includes(name) || p.inputs.include.some((included) => matches(name, included)))))
      throw Error(`Relevant source/test coverage missing: ${pattern}`);
  }
  const entries = [];
  for (const name of [...names].sort()) {
    const declared = p.inputs.extra.includes(name) || mandatory.has(name);
    if (
      secret(name, p.inputs.sensitive) ||
      (!declared && p.inputs.exclude.some((pattern) => matches(name, pattern)))
    )
      continue;
    if (
      !declared &&
      !p.inputs.include.some((pattern) => matches(name, pattern))
    )
      continue;
    const target = path.join(root, name);
    let st;
    try {
      st = fs.lstatSync(target);
    } catch (e) {
      if (e.code === "ENOENT") {
        entries.push({ path: name, kind: "deleted" });
        continue;
      }
      throw e;
    }
    if (st.isSymbolicLink())
      entries.push({
        path: name,
        kind: "symlink",
        target: fs.readlinkSync(target),
        mode: st.mode & 0o111,
      });
    else if (st.isFile()) {
      // Refuse a symlink parent instead of reading outside the project.
      safe(root, name);
      entries.push({
        path: name,
        kind: "file",
        digest: sha(fs.readFileSync(target)),
        mode: st.mode & 0o111,
      });
    } else throw Error(`Non-file verification input ${name}`);
  }
  return { digest: sha(JSON.stringify(entries)), entries };
}
export function helperIdentity() {
  const entries = [
    ["SKILL.md", sha(fs.readFileSync(path.join(HERE, "../SKILL.md")))],
  ];
  for (const dir of ["scripts", "schemas", "references"])
    for (const name of fs.readdirSync(path.join(HERE, "..", dir)).sort()) {
      const f = path.join(HERE, "..", dir, name);
      if (fs.statSync(f).isFile())
        entries.push([`${dir}/${name}`, sha(fs.readFileSync(f))]);
    }
  return sha(JSON.stringify(entries));
}
export function executable(name) {
  for (const dir of (process.env.PATH ?? "").split(path.delimiter)) {
    const candidate = path.join(dir, name);
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      return fs.realpathSync(candidate);
    } catch {}
  }
  throw Error(`Missing executable ${name}`);
}
export function main(fn) {
  Promise.resolve()
    .then(fn)
    .catch((e) => {
      console.error(`VINE: ${e.message}`);
      process.exitCode = 1;
    });
}

export function isMain(url) {
  return (
    Boolean(process.argv[1]) &&
    fileURLToPath(url) === path.resolve(process.argv[1])
  );
}
