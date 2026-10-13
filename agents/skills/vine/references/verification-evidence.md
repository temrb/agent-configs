# Execution and final-state evidence

With valid `.vine/project.json`, invoke the installed helper by absolute path:

```sh
node /path/to/vine/scripts/run-check.mjs --root /project --suite unit --task task-id
node /path/to/vine/scripts/verify-evidence.mjs --root /project --scope task --trusted-base APPROVED_BASE_COMMIT --trusted-policy /trusted/project.json --trusted-policy-sha256 APPROVED_SHA256
node /path/to/vine/scripts/audit-test-diff.mjs --root /project --base BASE_REVISION
```

Suite IDs come from project metadata; package.json retains command ownership.
Extra selection arguments follow `--` and are allowed only by policy. Targeted
passes never discharge unfiltered obligations. Each attempt receives a unique
report directory. Missing/malformed required native reports leave evidence
incomplete even when the subprocess exits zero; the wrapper exits nonzero and
retains the subprocess exit code in the attempt. Failed commands retain logs and process status;
behavioral classification requires an identified assertion and validated setup.
Unknown observation remains unknown.

Verification identities cover relevant tracked, dirty and nonignored untracked
inputs, modes and symlink targets, independently of release fingerprints. Built-in
sensitive filenames and `inputs.sensitive` globs are never read or hashed. Filename
heuristics are incomplete: the owner must declare custom sensitive paths. Use
`inputs.exclude` for dependencies, generated outputs and runtime/evidence state. Runtime
setup still needs separate evidence. Pre/post equality cannot detect edits
restored during a local run: local evidence is diagnostic, not isolated proof.

Before completion, validate attempts against final inputs and applicable scope.
Completion always derives task applicability from `--trusted-base`, a full commit
identity supplied independently by the maintainer or protected CI. Optional `--base`
must resolve to that same identity. Direct scopes are diagnostic only. Additional
boundaries may add checks. Renames contribute both paths. Changed paths outside
include/extra/mandatory inputs fail unless explicitly excluded; exclusions are
listed for owner review. This detects change-set omissions, not missing unchanged
transitive dependencies: input policy completeness still needs review. Unknown
behavioral paths are listed individually and require boundary review even when
other paths match routing. Required obligations
cannot be waived by the agent. Operational acceptance remains project/operator
owned. Local JSON, including valid case records, is not independently trusted.

The approved policy and digest must come from maintainer-controlled configuration,
independently of the candidate. A new policy needs explicit baseline approval.
For local diagnostics, use `--diagnostic true`; its exit status grants no approval.
Policies must declare nonempty `inputs.relevant` source/test globs. Package scripts,
policy and authority are mandatory inputs. Only explicit `documentationPaths`
select passive documentation; agent instructions remain behavioral. Built suites
require exact `expectedBoundaries` coverage and a complete sealed file inventory.

Each suite declares `category: "command"` or `"behavioral"`. Command checks may
use process success or `json-status`; behavioral suites require scenario reports
(workerd, Vitest, Playwright, built, or removal). Categorization is part of the
independently approved policy, not inferred from a suite name. A case's `tests`
list contains discriminators that each actually failed red and passed green,
not every test merely executed. Red and green use the same owning suite and
must differ in fingerprinted inputs outside fixture, policy and authority files.
Same-HEAD dirty-worktree fixes are supported. Distinct inputs alone cannot prove
a causal fix; oracle/setup review must exclude unrelated changes and flakes.
Case completion applies surrounding checks from the independently supplied task
base, which may predate `defectiveRevision`.
