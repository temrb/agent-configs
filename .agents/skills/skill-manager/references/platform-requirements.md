# Platform requirements and differences

Use this reference when identifying a target platform, validating compatibility, or deciding whether a field or file is portable.

This is a platform-aware matrix, not a claim that every client implements one identical standard. Existing target files and current official platform documentation take precedence when they conflict with this reference.

## 1. Portable Agent Skills baseline

Use this baseline for new cross-platform skills unless a platform-specific feature is required.

### Required structure

```text
skill-name/
└── SKILL.md
```

Optional conventional directories:

```text
scripts/
references/
assets/
```

Additional files and directories may exist when a client supports or ignores them safely.

### SKILL.md

`SKILL.md` contains YAML frontmatter followed by Markdown instructions.

Required portable fields:

- `name`
- `description`

Portable `name` constraints:

- 1 to 64 characters.
- Lowercase ASCII letters, digits, and hyphens only.
- Must not start or end with a hyphen.
- Must not contain consecutive hyphens.
- Must match the parent directory name.

Portable `description` constraints:

- 1 to 1024 characters.
- Describe both what the skill does and when an agent should use it.
- Include concrete trigger terms where useful.

Open-format optional frontmatter fields include:

- `license`
- `compatibility` with a maximum of 500 characters when present
- `metadata` as a string-to-string mapping
- `allowed-tools`, which is experimental and may not have consistent client support

### Content organization

- Keep `SKILL.md` focused on instructions needed whenever the skill activates.
- Keep the body under about 500 lines as a practical quality target.
- Move detailed or conditional material into focused supporting files.
- Use relative paths from the skill root and forward slashes.
- Prefer shallow references such as `references/guide.md` rather than deep chains.
- Scripts should be self-contained or clearly document dependencies, fail with useful messages, and handle expected edge cases.

### Reference validation

When available, the open-format reference validator can be used as an additional structural check:

```bash
skills-ref validate ./skill-name
```

Do not treat a passing structural validator as proof that the workflow is correct, safe, or runnable on every platform.

## 2. OpenAI Codex and ChatGPT skill additions

OpenAI's skill format builds on the Agent Skills model: a skill directory with `SKILL.md`, optional scripts/references/assets, and progressive loading.

### Discovery locations

Codex can discover skills from locations including:

- repository-scoped `.agents/skills/` directories from the current working directory toward the repository root;
- `$HOME/.agents/skills` for user skills;
- `/etc/codex/skills` for admin-provided skills;
- system-bundled skills.

Do not move or install a skill into a user or system location without an implementation request and appropriate scope.

### OpenAI-specific metadata

`agents/openai.yaml` is optional and OpenAI-specific. It can hold:

- `interface` metadata such as `display_name`, `short_description`, icon paths, `brand_color`, and `default_prompt`;
- `policy.allow_implicit_invocation` where `false` disables implicit activation while retaining explicit invocation;
- `dependencies.tools` declarations, including MCP tool dependencies.

Rules for managing this file:

- Preserve it when it exists.
- Do not create fictional dependency entries.
- Do not treat OpenAI dependency declarations as generic Agent Skills metadata.
- Validate referenced local icon paths when present.
- Do not assume another platform will interpret this file.

### Distribution and enablement are separate concerns

Local skill authoring/discovery and reusable plugin distribution are different workflows. Do not package, publish, install, or modify external configuration merely because a skill was edited.

Disabling a local Codex skill may be represented outside the skill directory in Codex configuration. Changing that configuration is outside a normal in-skill edit and should be treated as a separate scoped action.

## 3. Anthropic Claude custom Skill requirements

Anthropic's custom Skills use the same core `SKILL.md` concept but add platform constraints.

### Name and description constraints

For Anthropic custom Skills:

- `name` is at most 64 characters and uses lowercase letters, digits, and hyphens.
- The `name` must not contain the reserved words `anthropic` or `claude`.
- `name` and `description` must not contain XML tags.
- `description` is non-empty and at most 1024 characters.
- The description should say what the skill does and when it should be used.

For a portable skill intended to work with Anthropic as well as the open format, apply the stricter intersection: use the open-format directory/name rules plus Anthropic's reserved-word and XML restrictions.

### Claude API packaging and versioning

For custom Skill upload through the Claude API:

- Uploads may use a zip archive or file objects.
- A zip archive must contain the skill directory as its single top-level entry.
- The upload must include `SKILL.md` at the skill root.
- The top-level directory must correspond to the frontmatter name under Anthropic's documented matching rule.
- Total upload size must remain under the platform limit.
- Updates create new custom-skill versions rather than mutating an existing version in place.
- Remote deletion requires deleting versions before deleting the skill.

Creating versions, uploading archives, or deleting remote objects changes external workspace state and therefore requires confirmation unless the user explicitly requested that exact remote action.

### Claude API runtime constraints

Skills executed in the Claude API code-execution container have important constraints:

- no network access;
- no runtime package installation;
- isolated container execution;
- only available/pre-installed packages can be assumed.

Do not call a skill Claude-API-compatible when its runtime requires network calls or on-demand package installation unless the workflow explicitly runs elsewhere.

## 4. Claude Code differences

Claude Code supports filesystem-based skills in locations such as:

- `~/.claude/skills/`
- `.claude/skills/`

Claude Code also supports frontmatter fields and invocation behavior beyond the portable baseline. Current documented fields include:

- `when_to_use`
- `argument-hint`
- `arguments`
- `disable-model-invocation`
- `user-invocable`
- `allowed-tools`
- `disallowed-tools`
- `model`
- `effort`
- `context`
- `agent`
- `hooks`
- `paths`
- `shell`

Most of these are Claude Code extensions rather than universal Agent Skills fields. `allowed-tools` also exists experimentally in the open Agent Skills specification, but Claude Code gives it platform-specific permission semantics.

Important handling rules:

- Preserve Claude Code-specific fields when editing a Claude Code skill.
- Do not copy them into a portable skill solely to mimic behavior on another platform.
- `allowed-tools` in Claude Code has permission semantics for invocation turns; do not assume the experimental open-format field or another platform has identical semantics.
- The skill directory name can affect the command used to invoke a Claude Code skill, so renaming the directory can be a public behavior change.

Claude Code's own frontmatter requirements are more permissive than the strict portable/open-format requirements. When a skill must work across clients, validate against the stricter portable profile instead of relying on Claude Code permissiveness.

## 5. Cross-platform decision rules

### New portable skill

Use:

- a directory whose name exactly matches `name`;
- a name satisfying the open-format regex and Anthropic reserved-word restriction;
- a description satisfying the shared 1024-character limit and containing activation guidance;
- `SKILL.md` plus only necessary portable supporting directories;
- no platform-specific invocation or dependency fields unless placed in a platform-specific file and explicitly needed.

### Existing platform-specific skill

Preserve its native contract first. Do not remove supported platform extensions just to make the tree look portable.

### Migration request

1. Inspect the complete source skill.
2. Identify source-only and target-only features.
3. Classify each feature as directly portable, transformable, or unsupported.
4. Report unsupported behavior before implementation.
5. Preserve source files unless the requested migration explicitly replaces them.
6. Never silently weaken tool permissions, invocation controls, dependencies, or runtime assumptions.

### Conflicting targets

If one file cannot express both platform behaviors correctly, prefer explicit platform-specific files or variants over inventing a fake shared schema.

## 6. Source documentation used to establish this baseline

The manager should verify current official documentation when a task depends on behavior that may have changed.

```text
https://learn.chatgpt.com/docs/build-skills
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
https://agentskills.io/home
https://agentskills.io/specification
https://code.claude.com/docs/en/skills
```
