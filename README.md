# agent-configs

Personal agent configs — plugins, skills, snippets, etc. The filesystem is the index: browse directories for the current list.

## Layout

```text
agent-configs/
  plugins/<name>/README.md + plugin.json + skills/<name>/SKILL.md
  skills/<name>/SKILL.md
```

See `plugins/README.md` and `skills/README.md` for what belongs in each collection.

## Usage

- Plugin: point your agent client at `plugins/<name>`. Details live in that plugin's `README.md`.
- Skill: point your agent client at the skill directory (`plugins/<name>/skills/<skill-name>` or `skills/<name>`). The colocated `SKILL.md` is the definition and the doc.

## Adding

Copy an existing entry as a template and write colocated docs — no root edits:

- New plugin: copy the `plugins/<name>/` shape, fill in `plugin.json` plus that plugin's `README.md` and `skills/<name>/SKILL.md`.
- New standalone skill: add `skills/<name>/SKILL.md`.
