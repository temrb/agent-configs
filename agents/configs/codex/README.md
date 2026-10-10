# Codex configuration

The source of truth is `agents/configs/codex/.codex/config.toml`. Native assets
such as `hooks.json`, `hooks/`, and `rules/` belong alongside it. This repository
storage path is not automatically loaded by Codex.

The checkout's root `.codex/` is a local installation, excluded from canonical
validation and synchronization. Update it explicitly when needed; maintain
shared changes in `agents/configs/codex/.codex/`.

## Install or export

Run these commands from the repository root. Choose a user destination
(`${CODEX_HOME:-$HOME/.codex}`) or a project's `.codex/` directory. Project
configuration loads only for trusted projects; user and project layers have
runtime precedence independent of this repository's storage layout. See the
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
for scope restrictions and supported keys. Provider, notification, and telemetry
settings ignored at project scope should be documented as user-only additions
if needed later.

```bash
# User installation. For project installation, set codex_destination=/path/to/project/.codex
codex_destination="${CODEX_HOME:-$HOME/.codex}"
# Back up the destination before merging the canonical tree into it.
if [ -e "$codex_destination" ]; then
  cp -a "$codex_destination" "${codex_destination}.backup-$(date +%Y%m%d-%H%M%S)"
fi
mkdir -p "$codex_destination"
cp -a agents/configs/codex/.codex/. "$codex_destination/"
```

This is a manual merge, not an inventory-managed installation. Before an update,
compare the previous installed source revision with the current canonical tree
(for example, `git diff --name-status <previous-revision> HEAD -- agents/configs/codex/.codex`).
Review any uncommitted source changes too. Preview retired paths and remove only
files you previously installed from this collection after reviewing the backup;
preserve unrelated destination files. The copy command leaves destination-only
files in place, so removed hooks and rules remain active until retired manually.
Keep the source revision or a copy of the installed source tree for that comparison.

Both destinations receive the same source assets. Identical effective runtime
behavior is not guaranteed across user and project scopes.

Review existing destination files before copying; merge `config.toml` manually
if you need to retain destination preferences. `cp -a` preserves relative paths
and executable script permissions. If hooks are added, verify their command
paths at the destination and complete Codex's hook-trust review before use.

## Import selected assets

Import only configuration assets you intend to maintain. For example:

```bash
codex_source="${CODEX_HOME:-$HOME/.codex}"
cp -a "$codex_source/config.toml" agents/configs/codex/.codex/config.toml
# If intentionally maintained, copy hooks.json, hooks/, or rules/ individually.
git diff -- agents/configs/
python3 scripts/repo.py validate
```

Never copy an entire live `CODEX_HOME` into the repository: it may contain
`auth.json`, history, logs, caches, and other private runtime data. Review new
untracked assets with `git status` as well as the diff.

## Settings reconciliation

The local root configuration was moved without changing its contents. It
already includes all settings from the previous remote user/project split:

| Group | Preserved settings and values |
| --- | --- |
| Reasoning | `model_reasoning_effort = "low"`, `model_reasoning_summary = "concise"`, `plan_mode_reasoning_effort = "high"` |
| Personality and output | `personality = "pragmatic"`, `tool_output_token_limit = 8000` |
| Approval and sandbox | `approval_policy = "on-request"`, `sandbox_mode = "workspace-write"`, `sandbox_workspace_write.network_access = false` |
| Search | top-level `web_search = "live"`, `tools.web_search.context_size = "medium"` |
| Agents and skills | `agents.max_concurrent_threads_per_session = 3`, `skills.max_context_tokens = 8000` |

The local customization also preserves fields omitted from that split:

| Group | Preserved settings and values |
| --- | --- |
| Model | `model = "gpt-6.1-sol"` |
| Context | `model_context_window = 1050000`, `model_auto_compact_token_limit = 700000`, `model_auto_compact_token_limit_scope = "total"` |
| Reviewer | `approvals_reviewer = "auto_review"` |
| Subagents | `agents.enabled = true`, `agents.default_subagent_model = "gpt-6-luna"`, `agents.default_subagent_reasoning_effort = "max"` |
| TUI | `model`, `reasoning`, `five-hour-limit`, `weekly-limit`, `context-remaining`, `task-progress`, `fast-mode` in `tui.status_line` |

These configuration keys are documented in the official reference. Model access,
context limits, reviewer availability, and status item support depend on the
installed Codex version and account; this collection preserves explicit local
preferences rather than selecting replacement defaults. No separate uploaded
reference file was available in this checkout for an independent comparison.

`web_search` deliberately remains top-level. Placing it after
`[sandbox_workspace_write]` without opening another table would nest it inside
that table and change its meaning. Shell network access remains disabled.

## Validation

Python 3.11+ is required. Validation requires the canonical `config.toml` and
parses native TOML and JSON assets, including optional `hooks.json`, independently
of plugin recipes. It checks syntax and repository path safety, not the complete
upstream schema or runtime compatibility. No Codex version is pinned and no
runtime compatibility guarantee is made. Other native files retain their paths.
Known private runtime names (including authentication, history, sessions, logs,
caches, and SQLite state) are rejected at any depth. This guard cannot detect
credentials embedded in otherwise legitimate configuration or arbitrarily named
files; review imported content before committing it.

```bash
python3 scripts/repo.py sync --check
python3 scripts/repo.py validate
python3 -B -m unittest discover -s tests
```
