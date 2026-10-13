# Plugin collection

Each entry in `agents/plugins/<name>/` is a distributable plugin package. Directory names serve as the index; do not maintain a separate catalog. The canonical `plugin.json` targets [Agent Plugins v1.0.0](https://agent-plugins.org/specification). Bundled skills under `skills/` and an MCP configuration at `mcp.json` are **optional** component types; clients may support different subsets.

The repository adds release requirements (semantic `version`, `description`, `author.name`), documented in [standards](../../docs/standards.md). Each entry must have a README describing its contents, supported clients, installation, and updates. The README and packaged files travel together.

Entries using generated outputs declare `build.json` and commit a `.generated.json` ownership inventory. Generated outputs must not be hand-edited. For example [Prefine](prefine/README.md) copies the canonical [Prefine skill](../skills/prefine/SKILL.md) and generates an optional Codex compatibility manifest. No other plugin is required to emit a Codex manifest.

Follow [build and maintenance](../../docs/build-system.md) for recipes, drift checks, and retirement. Always run `python3 scripts/repo.py validate`, even if an entry has no recipe; run `sync --check` and tests before releases. Plugin releases bump the version and use `<name>/v<version>` tags. Install instructions are entry/client-specific; an independently copyable package is not a guarantee of automatic discovery.
