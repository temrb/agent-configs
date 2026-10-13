# Compatibility record

| Contract                 | Implemented / tested scope                                                     |
| ------------------------ | ------------------------------------------------------------------------------ |
| Helper/schema            | Helper 1.0.0; schema v1; unknown policy fields/versions rejected               |
| Runtime                  | Node 24.19.0, Bun 1.4.2                                                        |
| Source release           | Standalone Git commit identity; development installs explicitly provisional    |
| Project policy           | `.vine/project.json`, application-owned commands and authority                 |
| Evidence                 | Local diagnostics; CI run IDs are metadata, never authenticated trust          |
| Operating mode           | Advisory/manual review; protected merge unverified                             |
| Codex discovery          | Not yet tested in a fresh pinned client session                                |
| Hooks / reviewer         | Omitted; no automatic execution or continuation                                |
| Effectiveness evaluation | External held-out evaluation pending                                           |

Helpers use dependency-free ESM and the documented JSON Schema subset encoded
by their schemas: types, enums, constants, required/properties, additional
properties, arrays, string patterns and minimum lengths. Unsupported schema
major versions fail; no claim of general JSON Schema implementation is made.
Paths resolve relative to modules or explicit/ancestor project policy. Installed
execution from a different cwd and roots containing spaces is covered by tests.
Local symlink file identity is captured without following targets; symlink parent
paths and unsafe runtime/report destinations fail closed.

Recheck this record after runner, schema, toolchain, CI, discovery or adapter
changes. No client/runtime migration may silently treat incompatible evidence
as passing. An updated schema contract requires versioning and migration docs.

Verification path globs support `*`, `**` and `?`, including dotfiles and newline
filenames; other characters are literal. Hidden policy and CI inputs are covered
by regression fixtures.

Historical development provenance: reusable baseline
`d5dfeba5ed495ab2087714c87083f17d0bbe09d3`, application baseline
`b4ba3c317e255b2400ab0ace866e6339fd08e6ca`. VINE was added in repository commit
`cfd2f28`; use the reviewed source checkout's full Git commit for an installation,
with actual runtime file digests in each consumer's inventory and attempts.
Local mechanics validation date: 2026-10-11. Last
independent effectiveness evaluation: none. The initial implementation supports
the Bun/Node tuple and Foundation report formats above; broader project/runtime
compatibility requires its own policy and compatibility proof before adoption.

The instruction workflow can be used without these helpers. The optional helper
profile uses Bun package scripts, `FOUNDATION_EVIDENCE_DIR`, Cloudflare artifact
paths and Foundation removal-report identities. It is not a general runner for
every repository. Node/Bun pins belong to this profile and its CI tests; shared
repository generation and validation require only Python.

Available local CLI: `codex-cli 0.162.1` (`--version` only). This identifies an
installed executable; it does not establish discovery, activation, hooks or
permission enforcement in the active client.

## Audit corrections and policy migration

The optional helper supports the Foundation-compatible profile on Linux with the
pinned runtime above. Windows runtime compatibility, fresh client discovery,
real consumer integration, and effectiveness remain unverified.

Existing v1 policies must add `inputs.relevant`: nonempty source/test globs
reviewed by the application owner. Every glob must match an included, nonsecret
input outside the mandatory controls. Tracked deletions remain fingerprinted.
`package.json`, `.vine/project.json`, and all authority files are always captured,
even when include/exclude rules omit them. Routine and full scopes must be
nonempty. Existing attempts without the mandatory controls or historical policy
snapshot require replay. This tightens the experimental v1 contract before release.

Completion CLI calls require both `--trusted-policy FILE` and
`--trusted-policy-sha256 SHA256`. The maintainer or trusted CI configuration must
supply the digest from an independently reviewed immutable policy revision,
outside candidate-controlled scripts and evidence. A candidate-authored file or
digest does not establish approval. Any policy change requires an explicit new
approved digest. The CLI records that baseline identity; provenance remains the
caller's trust responsibility. Use `--diagnostic true` for local inspection;
the exported `verify()` and `verifyCase()` functions provide diagnostics only,
never independent acceptance. Diagnostic exit success is not completion approval.

`documentationPaths` explicitly permits passive documentation globs; absent or
unknown paths select routine checks. Agent instruction filenames and agent
configuration trees always select routine checks even if a broad glob matches.
Each built suite must declare nonempty `expectedBoundaries` and an artifact.
These are smoke execution identities, separate from applicability `boundaries`,
which select suites. Reports must contain exactly the expected identities;
additional, missing, duplicate, and empty identities fail. Sealed artifacts must
inventory all release files except the root manifest itself.

Vitest supports one configured JSON destination per suite, including nested
paths. Red attempts capture `policy.json` alongside native evidence and validate
commands, report inventory, policy digest, helper identity and runtime against
that historical contract. The final fixture paths and digest in the case record
identify the reproducer overlay; both attempts must include that exact overlay.
Independent review must approve the overlay and its setup. A different historical
helper requires replay with the current helper; arbitrary old helper versions are
not supported. Historical report paths may differ from green report paths.

Sensitive patch paths are listed without reading or hashing their contents.
`patchIdentityComplete: false` means `patchDigest` cannot bind the entire proposal;
exception requests then fail and require independent protected review/binding.

### Local audit tightening (2026-10-11)

The experimental v1 policy now requires a `category` on each suite: `command`
for static/process checks or `behavioral` for scenario evidence. Existing policies
must add this field and receive a new independently approved digest; prior
attempts require replay because helper and policy identities change. No shipped
VINE plugin or generated consumer exists in this repository.

Completion additionally requires an independently supplied `--trusted-base` full
commit identity and always derives task routing. Direct scopes remain available
with `--diagnostic true`. Custom sensitive paths use optional `inputs.sensitive`
globs. Changed unclassified input omissions fail task verification; explicit
exclusions remain visible. See the canonical [execution contract](../references/verification-evidence.md)
for routing, evidence categories, wrapper exit behavior and case constraints.

The local lifecycle tests use real Git and Bun processes with synthetic native
reports. They verify installed execution from another cwd, not genuine Vitest,
Playwright or Foundation consumer interoperability. No network dependencies
were installed during this audit; those integration claims remain unverified.
