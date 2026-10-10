# Configuration collection

Each client maintains one canonical native tree under `agents/configs/<platform>/`. Keep native filenames and relative asset paths intact; installation at user or project scope does not create another canonical source here.

| Client | Canonical source | Status |
| --- | --- | --- |
| [Codex](codex/README.md) | `agents/configs/codex/.codex/` | Native TOML/JSON validation |
| [Meta Muse Code](muse/README.md) | `agents/configs/muse/settings.json` | Context-derived JSON; official documentation requires login, native paths and precedence unverified |
| [OpenCode](opencode/README.md) | `agents/configs/opencode/opencode.json` | Native V2 JSON; user and project installation |

Each entry documents installation, export/import, maintenance, precedence, and
validation limits. Add sibling entries with their own README and validator
without altering common plugin or skill recipes.

Native configurations are independent of plugin generation and are not synchronized by `scripts/repo.py sync` unless a future recipe explicitly declares that behavior. Installation/export is client-specific and must document destination scope, merge/retirement, and precedence. Never import credentials, runtime history, logs, or caches; path validation does not detect secrets hidden in otherwise legitimate configuration files.

See [shared ownership and compatibility policy](../../docs/standards.md).
