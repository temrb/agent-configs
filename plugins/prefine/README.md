# prefine

A prompt compiler and enhancer that turns rough requests into lean, effective prompts without executing the underlying task.

## Contents

- `plugin.json` — plugin metadata (machine source of truth for name, version, description).
- `skills/prefine/SKILL.md` — the skill definition.

## Usage

Point your agent client at `plugins/prefine` for the plugin, or at `skills/prefine` inside it for the skill alone. See `skills/prefine/SKILL.md` for behavior and output contract.

## Canonical source

`skills/prefine` here is a generated copy of the canonical `skills/prefine/` at the repository root. Do not edit this copy directly. Edit the canonical source, then synchronize before committing:

- Sync: `python3 scripts/sync-prefine.py`
- Check: `python3 scripts/sync-prefine.py --check`
