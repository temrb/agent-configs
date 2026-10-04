# skills

Each subdirectory is one standalone skill.

Expected shape: `<name>/SKILL.md`. `SKILL.md` is the doc — no extra `README.md`. The directory listing is the index.

`skills/prefine/` is the canonical Prefine source; `plugins/prefine/skills/prefine/` is a generated copy. Edit the canonical files only, then run `python3 scripts/sync-prefine.py` before committing (`--check` verifies without writing).
