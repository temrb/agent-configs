"""Bounded native JSON tree checks; no upstream schema or runtime claims."""
import json

from agent_paths import CONFIG_COLLECTION

RUNTIME_NAMES = frozenset({
    "auth.json", "credentials.json", "credentials", "history.jsonl", "history",
    "sessions", "archived_sessions", "session_index.jsonl", "log", "logs",
    "cache", "caches", ".cache", "sqlite", "tmp", "node_modules",
    ".env", ".DS_Store",
})


def runtime_asset(name):
    return (name in RUNTIME_NAMES or name.startswith(".env.") or
            name.endswith((".log", ".sqlite", ".sqlite-wal", ".sqlite-shm",
                           ".sqlite-journal", ".db", ".db-wal", ".db-shm")))


def json_configs(root, safe, client, filename):
    directory = safe(root / CONFIG_COLLECTION / client, root)
    config = safe(directory / filename, root)
    if not config.is_file():
        raise ValueError(f"missing canonical {client} configuration: {config}")
    for path in sorted(directory.rglob("*")):
        safe(path, root)
        if runtime_asset(path.name):
            raise ValueError(f"private runtime asset is not configuration: {path}")
        if path.is_file() and path.suffix == ".json":
            try:
                value = json.loads(path.read_text())
                if path == config and not isinstance(value, dict):
                    raise ValueError("native configuration must be an object")
            except (ValueError, UnicodeError) as error:
                raise ValueError(f"invalid configuration syntax: {path}: {error}") from error
