# Prefine Skills CLI installation

This guide is the sole authoritative documentation for installing Prefine with the Skills CLI. The [skill contract](../SKILL.md) remains the authoritative behavior contract.

## Source and discovery

Scope the source to the skill collection, not the bare repository, so discovery avoids the generated plugin duplicate:

```sh
npx skills add temrb/agent-configs/agents/skills --skill prefine
npx skills add temrb/agent-configs/agents/skills --skill prefine --list
```

`--list` only discovers available skills without installing them.

## Installation options

- Project-local installation is the default; add `-g` for a global installation.
- Target an agent with `-a codex` or `-a <agent>`.
- Use `-y` for non-interactive installation.
- Installations link by default; use `--copy` to copy files explicitly.
- The CLI requires Node.js `>=22.20.0`, per its engines declaration.

## Reproducibility

`skills add` follows `main`/HEAD and does not provide reliable commit-SHA pinning. For reproducible, pinned bytes, copy `agents/skills/prefine/` from a selected repository commit following the manual-copy [usage](../../../plugins/prefine/README.md#usage).

## Installed contents and lifecycle

A canonical installation includes `docs/` and `tests/` alongside [SKILL.md](../SKILL.md). Those support files are inert installation noise; only `SKILL.md` defines the runtime contract.

Inspect installed skills with `npx skills list`, refresh them with `npx skills update`, and remove them with `npx skills remove`. Restart the client session after installation or changes.
