# Validation criteria

Use this checklist to decide whether a created or modified skill is structurally complete, internally consistent, and compatible with its intended platform.

Validation is layered. Do not equate a structural pass with runtime correctness.

## A. Structural completeness

A structurally complete portable skill should satisfy all applicable checks:

- The skill root exists and is the intended directory.
- `SKILL.md` exists at the root.
- YAML frontmatter opens and closes correctly and parses as complete YAML when a YAML parser is available.
- If complete YAML parsing is unavailable, reduced validation confidence is reported as a warning rather than an unconditional pass.
- Required fields for the target profile are present.
- `name` satisfies target naming rules.
- Directory/name relationships satisfy the intended platform.
- `description` satisfies length and content requirements.
- Referenced local files exist.
- Platform-specific files are in their documented locations.
- Optional directories contain files appropriate to their purpose.

## B. Internal consistency

Check that:

- `name`, directory name, examples, invocation instructions, and platform metadata do not contradict each other.
- The description matches the actual workflow and activation boundary.
- Every script named in instructions exists at the referenced path.
- Every referenced template, asset, schema, or guide exists.
- Renamed or moved files have no stale local references.
- Dependencies mentioned in instructions agree with scripts and platform configuration.
- Instructions do not call tools or commands that the target environment cannot provide without stating the requirement.
- Output formats and examples agree with the procedural instructions.
- Safety and confirmation gates do not conflict with implementation steps.

## C. Platform compatibility

### Portable/Open Agent Skills

Validate:

- strict portable name syntax;
- exact parent-directory/name match;
- required `name` and `description`;
- optional frontmatter uses documented open-format fields or clearly namespaced metadata;
- `metadata`, when present, is a string-to-string mapping;
- `allowed-tools` is treated as experimental rather than universally supported;
- progressive disclosure and relative references are sensible.

### OpenAI

Additionally validate:

- `agents/openai.yaml` only when present or intentionally added;
- local icon paths in that file resolve from the skill root and exist when configured;
- `allow_implicit_invocation` is a boolean when present;
- tool dependency declarations are not invented and match the actual intended integration;
- OpenAI-specific configuration is not presented as portable frontmatter.

### Anthropic Claude Platform/API

Additionally validate:

- reserved words are absent from the skill name;
- no XML tags occur in `name` or `description`;
- archive/root structure is compatible with upload requirements when packaging is requested;
- total size is within the applicable upload limit when API upload is the target;
- runtime scripts do not depend on network access or runtime package installation when they are expected to execute in the Claude API container;
- remote versioning/deletion actions are separated from local file editing.

### Claude Code

Additionally validate:

- Claude Code-specific frontmatter is preserved and syntactically coherent, including current fields such as `when_to_use`, `argument-hint`, `model`, `effort`, `hooks`, `paths`, and `shell`;
- invocation fields match the intended user/model invocation behavior;
- permission fields are reviewed as security-sensitive behavior, not merely metadata;
- directory renames are treated as possible invocation-name changes;
- Claude Code-only fields are not claimed to be portable.

## D. Instruction quality

A maintainable skill should generally have:

- a focused job with clear boundaries;
- a description that includes concrete trigger terms;
- imperative, reusable workflow steps;
- defaults rather than a large menu of equivalent choices;
- explicit fragile-operation sequences where order matters;
- validation loops for quality-critical work;
- common non-obvious gotchas near the core workflow;
- detailed material moved to references when it would bloat `SKILL.md`;
- scripts used for deterministic logic rather than as a substitute for clear instructions.

Warnings rather than hard failures are appropriate for judgment-based quality criteria.

## E. Script and dependency checks

Before running a bundled script:

1. Read it.
2. Identify its inputs, outputs, filesystem writes, network calls, subprocesses, dependencies, secrets, and external side effects.
3. Confirm the intended platform can provide its runtime and packages.
4. Prefer `--help`, dry-run, check, lint, or validation modes when available.
5. Run only non-destructive checks automatically.
6. Require confirmation before installation, network side effects, paid calls, external mutation, or destructive behavior.

A script is not validated merely because its syntax parses. For important scripts, use a safe representative input or documented smoke test when available.

## F. Change-scope checks

For revisions, verify:

- the implementation stayed within the requested skill and scope;
- unrelated metadata and files were preserved;
- no public name, root path, invocation policy, permission grant, or dependency contract changed silently;
- deletions and external changes were either explicitly requested or confirmed;
- the final report lists what changed and what was not validated.

## G. Validation levels

Use the highest safe level justified by the request:

### Level 1: Static local validation

- inspect tree and source files;
- validate frontmatter and names;
- check local references;
- inspect platform-specific metadata;
- perform syntax checks that do not execute the workflow.

### Level 2: Reference/tool validation

When available and appropriate:

- run `skills-ref validate` for the open-format structure;
- run platform-provided validators or linters that are local and non-destructive.

### Level 3: Non-destructive smoke validation

- exercise a script with safe test input;
- verify expected output shape;
- confirm no unintended writes or external calls.

### Level 4: Integration or deployment validation

Includes uploads, remote versions, publishing, installation, or external-system execution. This level requires explicit user intent and any confirmation required by the action's cost, external effects, or scope.

## H. Pass criteria

Report **pass** only when:

- no blocking structural or platform errors remain for the declared target;
- internal references required by the workflow resolve;
- known dependencies and environment requirements are represented accurately;
- all implementation changes were re-read after writing;
- the validation level actually performed is stated.

Report **pass with warnings** when structural compatibility is intact but non-blocking quality, portability, or untested-runtime concerns remain.

Report **fail** when a required file/field is missing, naming or packaging is invalid for the target, required references are broken, or the workflow depends on a capability known to be unavailable on the declared platform.

Never convert an unverified assumption into a passing claim.
