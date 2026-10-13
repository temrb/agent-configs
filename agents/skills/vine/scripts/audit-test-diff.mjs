import fs from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import {
  matches,
  isMain,
  args,
  options,
  rootAt,
  policy,
  git,
  sha,
  safe,
  main,
  readJSON,
  validate,
  secret,
} from "./common.mjs";

export function audit(root, base) {
  const p = policy(root);
  if (!base)
    throw Error(
      "Pass --base appropriate target revision; no latest-commit fallback",
    );
  const targetHead = git(
    root,
    "rev-parse",
    "--verify",
    `${base}^{commit}`,
  ).trim();
  const testedHead = git(root, "rev-parse", "HEAD").trim();
  const mergeBase = git(root, "merge-base", targetHead, testedHead).trim();
  // Compare base tree to entire working proposal, including index and unstaged edits.
  const tracked = git(
    root,
    "diff",
    "--name-only",
    "-z",
    "--no-renames",
    mergeBase,
    "--",
  )
    .split("\0")
    .filter(Boolean);
  const untracked = git(
    root,
    "ls-files",
    "-z",
    "--others",
    "--exclude-standard",
  )
    .split("\0")
    .filter(Boolean);
  const names = [...new Set([...tracked, ...untracked])].sort();
  const changes = [],
    patchEntries = [];
  for (const name of names) {
    if (secret(name, p.inputs.sensitive)) {
      patchEntries.push([name, "secret-excluded"]);
      continue;
    }
    let beforeBytes = null;
    try {
      beforeBytes = execFileSync(
        "git",
        ["-C", root, "show", `${mergeBase}:${name}`],
        { stdio: ["ignore", "pipe", "pipe"] },
      );
    } catch {}
    const beforeMode =
      git(root, "ls-tree", mergeBase, "--", `:(literal)${name}`).split(
        " ",
      )[0] || null;
    safe(root, path.dirname(name));
    const location = path.join(root, name);
    let st = null;
    try {
      st = fs.lstatSync(location);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
    }
    const afterBytes = st?.isSymbolicLink()
      ? Buffer.from(fs.readlinkSync(location))
      : st?.isFile()
        ? fs.readFileSync(location)
        : null;
    const before = beforeBytes?.toString("utf8") ?? null;
    const after = afterBytes?.toString("utf8") ?? null;
    patchEntries.push([
      name,
      beforeMode,
      beforeBytes === null ? null : sha(beforeBytes),
      st
        ? {
            kind: st.isSymbolicLink()
              ? "symlink"
              : st.isFile()
                ? "file"
                : "directory",
            mode: st.mode & 0o111,
          }
        : null,
      afterBytes === null ? null : sha(afterBytes),
    ]);
    if (
      !p.authority.includes(name) &&
      !p.protected.some((pattern) => matches(name, pattern))
    )
      continue;
    const findings = [];
    if (after === null) findings.push("Protected input deleted");
    if (before === null)
      findings.push("Protected input added; review discovery/ownership");
    const count = (text, re) => [...(text ?? "").matchAll(re)].length;
    if (
      count(
        after,
        /\b(?:it|test|describe)\.skip\b|\b(?:xit|xtest|xdescribe)\s*\(/g,
      ) >
      count(
        before,
        /\b(?:it|test|describe)\.skip\b|\b(?:xit|xtest|xdescribe)\s*\(/g,
      )
    )
      findings.push("Skip/quarantine syntax increased");
    if (
      count(after, /\b(?:it|test)\.fails\b/g) !==
      count(before, /\b(?:it|test)\.fails\b/g)
    )
      findings.push("Expected-failure declarations changed (not skips)");
    if (
      count(after, /\b(?:assert|expect)\s*[.(]/g) <
      count(before, /\b(?:assert|expect)\s*[.(]/g)
    )
      findings.push("Assertion syntax removed; semantic review required");
    if (
      /workerd|runner|harness|vitest|playwright|workflow|package\.json|\.vine|\/scripts\//.test(
        name,
      )
    )
      findings.push("Execution, dispatch or policy input changed");
    if (!findings.length)
      findings.push(
        "Protected expectations/fixtures changed; review retained guarantees",
      );
    changes.push({ path: name, findings });
  }
  return {
    mode: p.mode,
    targetHead,
    mergeBase,
    testedHead,
    patchDigest: sha(JSON.stringify(patchEntries)),
    patchIdentityComplete: !names.some((name) => secret(name, p.inputs.sensitive)),
    excludedSensitivePaths: names.filter((name) => secret(name, p.inputs.sensitive)),
    changedPaths: names,
    protectedChanges: changes,
    limitations: [
      "Advisory syntax inventory cannot prove semantic preservation or scenario reachability.",
      "Renames are represented as deletion/addition to preserve complete comparison.",
      "Maintainer approval must be independently verified and bound to patchDigest.",
    ],
  };
}
export function exceptionRequest(result, filename) {
  if (!result.patchIdentityComplete) throw Error("Patch identity incomplete: sensitive changes require independent review and protected binding");
  const value = readJSON(filename);
  const text = { type: "string", minLength: 1 };
  validate(value, {
    type: "object",
    additionalProperties: false,
    required: [
      "invariant",
      "reason",
      "replacementEvidence",
      "scope",
      "owner",
      "expiry",
      "retirementRationale",
      "patchDigest",
      "approvalReference",
    ],
    properties: Object.fromEntries(
      [
        "invariant",
        "reason",
        "replacementEvidence",
        "scope",
        "owner",
        "expiry",
        "retirementRationale",
        "patchDigest",
        "approvalReference",
      ].map((key) => [key, text]),
    ),
  });
  if (value.patchDigest !== result.patchDigest)
    throw Error("Exception is bound to another patch");
  if (
    value.expiry !== "permanent" &&
    (!Number.isFinite(Date.parse(value.expiry)) ||
      Date.parse(value.expiry) <= Date.now())
  )
    throw Error("Exception expired or expiry invalid");
  return {
    ...value,
    approval:
      "unverified; maintainer must independently authenticate approvalReference and patch binding",
  };
}
if (isMain(import.meta.url))
  main(() => {
    const a = args();
    options(a, ["root", "base", "exception"]);
    const result = audit(rootAt(a.root), a.base);
    if (a.exception) result.exception = exceptionRequest(result, a.exception);
    console.log(JSON.stringify(result, null, 2));
  });
