# Configuration collection

Each client maintains one canonical native tree under `agents/configs/<platform>/`. Keep native filenames and relative asset paths intact; installation at user or project scope does not create another canonical source here.

Currently supported: [Codex](codex/README.md), whose source is `agents/configs/codex/.codex/`. Other clients can add sibling entries with their own README and validator without altering common plugin or skill recipes.

Native configurations are independent of plugin generation and are not synchronized by `scripts/repo.py sync` unless a future recipe explicitly declares that behavior. Installation/export is client-specific and must document destination scope, merge/retirement, and precedence. Never import credentials, runtime history, logs, or caches; path validation does not detect secrets hidden in otherwise legitimate configuration files.

See [shared ownership and compatibility policy](../../docs/standards.md).
