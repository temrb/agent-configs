import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import {
  isMain,
  args,
  options,
  sha,
  readJSON,
  atomic,
  safe,
  git,
  VERSION,
  main,
} from "./common.mjs";
export const RUNTIME = [
  "SKILL.md",
  "references/regression-triage.md",
  "references/test-oracles.md",
  "references/test-ownership.md",
  "references/verification-evidence.md",
  "schemas/project.schema.json",
  "schemas/attempt.schema.json",
  "schemas/case.schema.json",
  "scripts/common.mjs",
  "scripts/reports.mjs",
  "scripts/run-check.mjs",
  "scripts/verify-evidence.mjs",
  "scripts/audit-test-diff.mjs",
  "scripts/install.mjs",
];
const sourceDefault = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
function files(root, prefix = "") {
  const out = [];
  for (const name of fs.readdirSync(safe(root, prefix))) {
    const relative = prefix ? `${prefix}/${name}` : name,
      location = safe(root, relative);
    const st = fs.lstatSync(location);
    if (st.isDirectory()) out.push(...files(root, relative));
    else if (st.isFile()) out.push(relative);
    else throw Error(`Non-file package input ${relative}`);
  }
  return out.sort();
}
function duplicates(root, destination) {
  const found = [];
  for (const dir of [
    ".agents/skills",
    ".codex/skills",
    ".claude/skills",
    ".agents/plugins",
    ".codex/plugins",
    ".claude/plugins",
  ]) {
    const location = safe(root, dir);
    if (!fs.existsSync(location)) continue;
    for (const file of files(location))
      if (path.basename(file) === "SKILL.md") {
        const absolute = path.join(location, file);
        if (
          absolute !== path.join(destination, "SKILL.md") &&
          /^name:\s*["']?vine["']?\s*$/m.test(fs.readFileSync(absolute, "utf8"))
        )
          found.push(absolute);
      }
  }
  if (found.length)
    throw Error(`Duplicate VINE discovery: ${found.join(", ")}`);
}
function unchanged(dest, record) {
  if (!fs.existsSync(dest))
    throw Error(
      "Installed runtime missing; preserve inventory for manual repair",
    );
  const names = files(dest);
  if (
    JSON.stringify(names) !== JSON.stringify(Object.keys(record.files).sort())
  )
    throw Error(
      "Uninventoried or missing installed files; preserve for review",
    );
  for (const [name, value] of Object.entries(record.files)) {
    const file = safe(dest, name),
      st = fs.statSync(file);
    if (
      sha(fs.readFileSync(file)) !== value.digest ||
      (st.mode & 0o111) !== value.mode
    )
      throw Error(`Locally edited runtime ${name}; preserve for review`);
  }
}
export function install(
  root,
  source = sourceDefault,
  development = false,
  remove = false,
) {
  if (process.versions.node !== "24.19.0")
    throw Error("VINE installer requires Node 24.19.0");
  root = fs.realpathSync(root);
  source = fs.realpathSync(source);
  const dest = safe(root, ".agents/skills/vine"),
    recordFile = safe(root, ".vine/install.json");
  const lock = safe(root, ".cloudflare/vine-install/lock");
  fs.mkdirSync(path.dirname(lock), { recursive: true });
  try { fs.mkdirSync(lock); } catch (e) {
    if (e.code === "EEXIST") throw Error("Installation locked; inspect lock/owner.json and transaction recovery before manually removing a stale lock");
    throw e;
  }
  try {
    atomic(path.join(lock, "owner.json"), { pid: process.pid, startedAt: new Date().toISOString() });
    const previous = fs.existsSync(recordFile) ? readJSON(recordFile) : null;
    if (
      previous &&
      (previous.helperVersion !== VERSION || previous.schemaVersion !== 1)
    )
      throw Error(
        "Unsupported installation inventory; use previous installer for removal",
      );
    if (previous) unchanged(dest, previous);
    else if (fs.existsSync(dest))
      throw Error("Unowned VINE installation; preserve for review");
    duplicates(root, dest);
    // V1 never registers hooks. A future owned registration needs its own versioned lifecycle.
    if (previous?.hooks?.length)
      throw Error(
        "Disable owned hooks using the owning adapter before removal/update",
      );
    if (remove && !previous) throw Error("No owned VINE installation");
    let record;
    if (!remove) {
      let commit = null,
        repo = null,
        prefix = null;
      try {
        repo = git(source, "rev-parse", "--show-toplevel").trim();
        commit = git(source, "rev-parse", "HEAD").trim();
        prefix = path.relative(repo, source).replaceAll("\\", "/");
      } catch {}
      const inventory = {};
      for (const name of RUNTIME) {
        const file = safe(source, name),
          bytes = fs.readFileSync(file),
          st = fs.statSync(file);
        if (!st.isFile()) throw Error(`Missing runtime ${name}`);
        inventory[name] = { digest: sha(bytes), mode: st.mode & 0o111 };
        if (!development) {
          if (!commit)
            throw Error("Release installation requires a pinned Git source");
          const sourcePath = prefix ? `${prefix}/${name}` : name;
          let original;
          try {
            original = git(repo, "show", `${commit}:${sourcePath}`);
          } catch {
            throw Error(
              `Uncommitted runtime ${name}; use --development true for an explicitly provisional install`,
            );
          }
          const mode = git(repo, "ls-tree", commit, "--", sourcePath).split(
            " ",
          )[0];
          if ((Number.parseInt(mode, 8) & 0o111) !== inventory[name].mode)
            throw Error(`Runtime mode differs from pinned commit: ${name}`);
          if (sha(original) !== inventory[name].digest)
            throw Error(`Runtime differs from pinned commit: ${name}`);
        }
      }
      record = {
        schemaVersion: 1,
        helperVersion: VERSION,
        node: "24.19.0",
        sourceCommit: commit,
        provisional: development,
        files: inventory,
        hooks: [],
        installedAt: new Date().toISOString(),
      };
    }
    const transaction = safe(
      root,
      `.cloudflare/vine-install/transactions/${randomUUID()}`,
    );
    fs.mkdirSync(transaction, { recursive: true });
    const staged = path.join(transaction, "new"),
      backup = path.join(transaction, "previous");
    if (!remove) {
      fs.mkdirSync(staged);
      for (const name of RUNTIME) {
        const target = safe(staged, name);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.copyFileSync(safe(source, name), target);
        fs.chmodSync(target, record.files[name].mode ? 0o755 : 0o644);
        if (sha(fs.readFileSync(target)) !== record.files[name].digest)
          throw Error("Staging digest mismatch");
      }
    }
    atomic(path.join(transaction, "recovery.json"), {
      destination: dest,
      recordFile,
      previous,
      next: record ?? null,
    });
    let movedOld = false,
      movedNew = false;
    try {
      if (previous) {
        fs.renameSync(dest, backup);
        movedOld = true;
      }
      if (!remove) {
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.renameSync(staged, dest);
        movedNew = true;
        atomic(recordFile, record);
      } else fs.unlinkSync(recordFile);
    } catch (e) {
      if (movedNew) fs.renameSync(dest, staged);
      if (movedOld) fs.renameSync(backup, dest);
      if (previous) atomic(recordFile, previous);
      else if (fs.existsSync(recordFile)) fs.unlinkSync(recordFile);
      throw e;
    }
    return {
      action: remove ? "removed" : previous ? "updated" : "installed",
      record: record ?? null,
      rollback: transaction,
      evidence: "preserved",
    };
  } finally { fs.rmSync(lock, { recursive: true }); }
}
if (isMain(import.meta.url))
  main(() => {
    const a = args();
    options(a, ["root", "source", "development", "remove"]);
    if (!a.root) throw Error("Pass --root CONSUMER");
    console.log(
      JSON.stringify(
        install(
          a.root,
          a.source,
          a.development === "true",
          a.remove === "true",
        ),
        null,
        2,
      ),
    );
  });
