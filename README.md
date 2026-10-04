# agent-configs

Personal agent configs — plugins, skills, snippets, etc.

## Contents

| Path | Description |
| ---- | ----------- |
| `plugins/prefine` | A prompt compiler and enhancer that turns rough requests into lean, effective prompts without executing the underlying task. |

## Layout

```text
agent-configs/
  plugins/prefine/
```

`skills/`, `snippets/`, etc. will follow the same layout as the repo grows.

## Usage

Load a plugin or skill directly from this repo by path:

- Plugin: point your agent client at `plugins/<name>` (e.g. `plugins/prefine`).
- Skill: point your agent client at the skill directory (e.g. `plugins/prefine/skills/prefine`).

See `plugins/prefine/skills/prefine/SKILL.md` for the skill definition, and `plugins/prefine/plugin.json` for plugin metadata.

## Adding new configs

Copy the `plugins/prefine` structure for a new plugin:

```text
plugins/<name>/
  plugin.json
  skills/<name>/SKILL.md
```

No per-directory READMEs — document everything here.
