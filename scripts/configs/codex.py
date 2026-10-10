"""Validation for the native Codex configuration tree."""
import json
import tomllib

from agent_paths import CONFIG_COLLECTION

CONFIG_DIR = CONFIG_COLLECTION / "codex/.codex"

# Runtime data has no place in a distributable configuration tree. This is a
# bounded guard, not a secret scanner or an allowlist of native assets.
RUNTIME_NAMES = frozenset({
    "auth.json", "history.jsonl", "sessions", "archived_sessions",
    "session_index.jsonl", "log", "logs", "cache", "caches", ".cache",
    "sqlite", "shell_snapshots", "tmp", "terminal_snapshots",
})


def runtime_asset(name):
    return (name in RUNTIME_NAMES or name.endswith((".log", ".sqlite", ".sqlite-wal",
            ".sqlite-shm", ".sqlite-journal")))


def codex_configs(root, safe):
    """Check native syntax without imposing an upstream schema or asset list."""
    directory = safe(root / CONFIG_DIR, root)
    config = safe(directory / "config.toml", root)
    if not config.is_file():
        raise ValueError(f"missing canonical Codex configuration: {config}")
    for path in sorted(directory.rglob("*")):
        safe(path, root)
        if runtime_asset(path.name):
            raise ValueError(f"private runtime asset is not configuration: {path}")
        if not path.is_file():
            continue
        try:
            if path.suffix == ".toml":
                tomllib.loads(path.read_text())
            elif path.suffix == ".json":
                json.loads(path.read_text())
        except (ValueError, UnicodeError) as error:
            raise ValueError(f"invalid configuration syntax: {path}: {error}") from error
