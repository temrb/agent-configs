# plugins

Each subdirectory is one self-contained plugin. The directory listing is the index.

Entries contain a README, canonical `plugin.json`, and any bundled skills.
Generated entries declare their outputs in `build.json` and commit the resulting
files and `.generated.json` inventory. Add an entry without changing shared code
or CI. See the [repository generation workflow](../../README.md#repository-generation).

Prefine bundles a generated copy of canonical `agents/skills/prefine/` and a derived
Codex manifest. Edit canonical inputs and run the shared sync command before
committing. Plugins can be copied and installed independently.

Run `python3 scripts/repo.py validate` even for plugins without recipes. Entries
require README, complete metadata, and valid bundled skills and resource paths.
Release behavior changes with a plugin version bump and a `<name>/v<version>`
Git tag; commit generated outputs and ownership inventories with the release.
