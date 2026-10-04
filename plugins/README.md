# plugins

Each subdirectory is one self-contained plugin.

Expected shape: `<name>/README.md` + `plugin.json` + `skills/<name>/SKILL.md`. See each plugin's `README.md` for docs; the directory listing is the index.

`plugins/prefine/skills/prefine/` is a generated copy of the canonical `skills/prefine/` source. Edit the canonical files only, then run `python3 scripts/sync-prefine.py` before committing (`--check` verifies without writing).
