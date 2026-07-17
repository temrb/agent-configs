---
name: skill-manager
description: Creates, inspects, validates, revises, organizes, and maintains agent skills across Open Agent Skills-compatible systems, OpenAI Codex and ChatGPT skills, and Anthropic Claude skills. Use when creating a new skill, reviewing or updating an existing skill, checking skill structure or metadata, organizing skill files, or reconciling platform-specific skill requirements.
compatibility: Designed for filesystem-based Agent Skills workflows. Local inspection and validation require filesystem read access; implementation requires scoped file write access. External publishing, uploads, installations, or current-doc verification depend on host tools and permissions.
metadata:
  skill_manager_version: '1.0.1'
---

# Skill Manager

Manage the full lifecycle of agent skills: create, inspect, validate, revise, organize, and maintain them without erasing platform-specific requirements.

## Core operating rules

1. Infer the requested operation from the user's language and current context.
2. Inspect existing skill files before recommending or making changes to an existing skill.
3. Treat the target skill's actual files as primary source material. Do not recreate existing metadata, instructions, dependencies, scripts, or directory structure from memory.
4. Separate analysis from implementation:
   - For review, inspection, or recommendation requests, do not modify files.
   - For create, fix, revise, update, organize, or implement requests, make safe in-scope changes directly when the target is accessible.
5. Ask only for missing information that materially changes correctness. Otherwise proceed with a stated assumption.
6. Preserve platform-specific files and fields. Do not translate one platform's configuration into another platform's schema unless the user explicitly requests a migration.
7. Report unsupported, missing, ambiguous, or conflicting requirements explicitly. Never invent a schema, dependency, tool name, install path, or deployment behavior.
8. Validate proportionately after implementation. Prefer local, read-only or non-destructive checks first.
9. Require confirmation before destructive, external-side-effecting, costly, or scope-expanding actions.

Read `references/platform-requirements.md` when platform identification or compatibility matters. Read `references/validation-criteria.md` when performing a formal review, validation, migration, or release-readiness check.

## Determine the operation

Map the request to one or more lifecycle operations:

- **Create**: make a new skill from requirements, examples, existing project artifacts, or a demonstrated workflow.
- **Inspect**: inventory and explain an existing skill without changing it.
- **Validate**: check structural, internal, platform, dependency, and workflow consistency.
- **Revise**: modify an existing skill while preserving its source files and intended behavior.
- **Organize**: improve layout, progressive disclosure, naming, references, or maintainability.
- **Manage**: handle discovery, placement, enablement guidance, packaging, versioning plans, or coordinated maintenance across multiple skills.

If multiple operations are implied, use this order unless context requires otherwise:

1. inspect
2. identify platform and constraints
3. validate current state
4. revise or organize
5. validate resulting state
6. report changes and remaining risks

## Resolve the target and platform

Use the request, filesystem layout, and existing files to infer the target.

Strong signals include:

- `.agents/skills/`, `$HOME/.agents/skills/`, `/etc/codex/skills/`, or `agents/openai.yaml`: OpenAI/Codex-oriented.
- `.claude/skills/` or Claude Code-only frontmatter such as `disable-model-invocation`, `when_to_use`, `paths`, `context`, `agent`, or `shell`: Claude Code-oriented.
- A skill archive or API workflow involving skill IDs and versions: Anthropic Claude API-oriented.
- A plain directory with `SKILL.md` and no platform-specific additions: treat as Open Agent Skills-compatible.
- A request for portability across platforms: use the strict portable baseline in `references/platform-requirements.md`.

When the platform is still uncertain:

- For inspection, validate against the open format baseline and list platform-specific observations separately.
- For creation, default to the portable baseline unless the requested capability depends on a platform extension.
- For implementation, ask one concise question only when choosing the wrong platform would materially change files, metadata, invocation behavior, or deployment.

## Existing-skill inspection procedure

Before changing an existing skill:

1. Locate the skill root and confirm `SKILL.md` if present.
2. Inventory files and directories within the skill root.
3. Read `SKILL.md` completely.
4. Parse and preserve all frontmatter fields, including unknown or platform-specific fields.
5. Identify files referenced by `SKILL.md` and inspect those relevant to the requested change.
6. Inspect platform files when present, including `agents/openai.yaml`.
7. Inspect relevant scripts before changing instructions that invoke them.
8. Identify dependency declarations, environment assumptions, external calls, generated artifacts, and install or publish instructions.
9. Note inconsistencies before editing: broken paths, mismatched names, stale references, conflicting instructions, unsupported fields, or undeclared dependencies.

Do not delete or rewrite content merely because it is unfamiliar. Preserve unknown fields and files unless they are proven invalid for the declared target or the user explicitly asks to remove them.

## Creation procedure

For a new skill:

1. Gather source context already available in the request, project, examples, runbooks, schemas, code, or prior workflow traces.
2. Derive a focused skill purpose and activation boundary.
3. Choose a valid kebab-case name. For portable or Anthropic-compatible targets, avoid reserved Anthropic product/company words in the `name`.
4. Write a discovery-oriented `description` that says both what the skill does and when to use it.
5. Start with only `SKILL.md` unless supporting files add clear value.
6. Move detailed, conditional, or bulky material into focused `references/` files and tell the agent exactly when to read each one.
7. Add scripts only when deterministic reusable logic is more reliable than instructions alone.
8. Make scripts non-interactive, document inputs and outputs, handle errors clearly, and avoid undeclared runtime dependencies.
9. Add platform-specific files only for a declared platform need. Do not add `agents/openai.yaml` or Claude-specific frontmatter merely for symmetry.
10. Keep the main instructions procedural and reusable rather than encoding one task instance.
11. Add validation or verification steps for fragile operations.
12. Validate the result before reporting completion.

If no destination is specified for an implementation request, prefer an existing project skill root that matches the detected platform. If none exists, create a standalone `./<skill-name>/` directory rather than writing into a user-global or system-global location. State that assumption.

## Revision procedure

When updating an existing skill:

1. Define the smallest change that satisfies the request.
2. Preserve the current public name, root directory, metadata, platform configuration, and unrelated files by default.
3. Patch existing files rather than replacing them wholesale unless a full rewrite is explicitly requested or the file is irreparably inconsistent.
4. Preserve comments, examples, custom metadata, and formatting where practical.
5. Update all affected internal references when moving or renaming files inside the skill.
6. Do not silently change invocation policy, pre-approved tools, external dependencies, distribution model, or runtime assumptions.
7. Re-read changed files and validate after editing.

A requested reorganization may move internal supporting files when the change is contained within the skill and all local references can be updated safely. Renaming the skill root, changing its public `name`, deleting files, or changing externally referenced paths requires confirmation unless the user explicitly requested that exact action.

## Managing a collection of skills

When the request covers multiple skills:

1. Inventory each skill root, `name`, `description`, detected platform, platform-specific files, and validation status.
2. Treat same-named skills as separate artifacts until the target client's discovery behavior is verified. Do not merge them by assumption.
3. Flag overlapping descriptions, ambiguous activation boundaries, duplicate public names, broken shared references, and inconsistent platform conventions.
4. Preserve platform-specific variants when they express behavior that cannot be represented portably.
5. Apply batch changes only within the user's stated scope. Validate each changed skill independently before reporting the collection as healthy.
6. Prefer reversible organization: add indexes or improve descriptions before renaming roots, changing public names, or deleting duplicates.
7. Require confirmation for collection-wide renames, moves, deletions, publishing, enablement changes, or migrations that can affect discovery outside the edited directories.

## Organizing for maintainability

Prefer this portable structure when it matches the content:

```text
skill-name/
├── SKILL.md
├── scripts/              # Optional executable helpers
├── references/           # Optional detailed documentation
├── assets/               # Optional templates and static resources
└── agents/
    └── openai.yaml       # Optional OpenAI-specific metadata
```

Apply progressive disclosure:

- Keep activation-critical rules, workflow order, safety gates, and common gotchas in `SKILL.md`.
- Move large specifications, platform matrices, long examples, schemas, and rare edge cases into `references/`.
- Keep references focused and directly linked from `SKILL.md` with a clear read condition.
- Prefer shallow relative paths and forward slashes.
- Avoid chains where one reference file merely points to another unless necessary.

## Platform-specific handling

Use `references/platform-requirements.md` as the working matrix. Key rules:

- The portable baseline follows the open Agent Skills structure and its strict naming rules.
- OpenAI-specific UI, invocation policy, and tool dependency declarations belong in `agents/openai.yaml`; preserve that file when it already exists.
- Anthropic Claude custom Skills add naming restrictions and API packaging/runtime constraints.
- Claude Code supports additional invocation and execution frontmatter that is not a universal Agent Skills standard.
- `allowed-tools` is not safely portable as a single semantic contract across all clients. Preserve existing usage and validate it against the intended platform instead of assuming equivalent behavior.
- Do not map OpenAI MCP dependency declarations to Claude runtime packages, or Claude Code invocation fields to OpenAI policy fields, without an explicit migration request.

When requirements conflict, report the conflict and choose one of these paths:

1. preserve the existing platform contract;
2. use the strict portable intersection when portability is the stated goal; or
3. maintain platform-specific variants/files when one common representation cannot preserve behavior.

Do not claim a false common standard.

## Validation workflow

For local validation, run the bundled validator when Python 3 is available:

```bash
python3 scripts/validate_skill.py /path/to/target-skill --platform auto
```

Use an explicit profile when known:

```bash
python3 scripts/validate_skill.py /path/to/target-skill --platform portable
python3 scripts/validate_skill.py /path/to/target-skill --platform agentskills
python3 scripts/validate_skill.py /path/to/target-skill --platform openai
python3 scripts/validate_skill.py /path/to/target-skill --platform claude-platform
python3 scripts/validate_skill.py /path/to/target-skill --platform claude-code
```

If the host environment provides the official/reference `skills-ref` validator, run it for open-format validation as an additional check rather than replacing source inspection.

Validation should cover, as applicable:

- required files and parseable frontmatter;
- valid and consistent name/directory relationships;
- description quality and activation scope;
- platform-specific metadata and unsupported fields;
- broken relative file references;
- missing scripts, assets, references, or declared dependencies;
- SKILL.md size and progressive-disclosure issues;
- obvious runtime incompatibilities with the intended platform;
- non-destructive smoke checks for bundled scripts when safe and meaningful.

Do not run scripts merely because they exist. Inspect them first. Avoid tests that mutate external state, incur cost, require secrets, publish artifacts, or modify files outside a disposable/test scope without confirmation.

## Confirmation gates

Proceed without extra confirmation for safe, requested, in-scope work such as:

- reading skill files;
- creating a new skill in the agreed or safely inferred local destination;
- editing files inside the target skill;
- adding missing local references or validation helpers;
- running read-only static validation;
- running clearly non-destructive local checks.

Require confirmation before:

- deleting a skill, file, remote version, or unrelated content;
- renaming or moving a skill root or changing its public invocation name unless explicitly requested;
- uploading, publishing, installing, deploying, or sending skill contents to an external service;
- creating remote versions or changing remote workspace state;
- installing packages or system dependencies;
- invoking paid services or actions likely to incur material cost;
- granting broader tool permissions or changing security/invocation policy beyond the request;
- modifying files outside the target skill or agreed scope;
- performing a migration that drops unsupported platform behavior.

When confirmation is needed, explain the exact action, scope, and reason in one concise request.

## Reporting contract

For inspection or review, report:

1. detected operation and platform profile;
2. files inspected;
3. findings separated into errors, risks, and recommendations;
4. unsupported or conflicting requirements;
5. no-change statement when no files were modified.

For implementation, report:

1. assumptions used;
2. files created, changed, moved, or deliberately left untouched;
3. validation performed and its result;
4. warnings or checks that could not be completed;
5. any external, destructive, costly, or scope-expanding next action still awaiting confirmation.

Never claim compatibility, successful deployment, or runtime correctness beyond what was actually validated.

## Maintenance behavior

When repeated failures, corrections, or false triggers are available, use them as source material for targeted revisions. Prefer evidence from actual skill files, execution results, project artifacts, and user corrections over generic best-practice prose.

When current platform behavior is material and the bundled platform reference may be stale, verify against current official documentation if the host permits read-only external research. If current verification is unavailable, say which requirement could not be confirmed and avoid guessing.
