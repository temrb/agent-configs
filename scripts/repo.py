#!/usr/bin/env python3
"""Discover declarative recipes, render all entries, then check or install outputs."""
import argparse
import fcntl
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import subprocess
import tempfile

sys.dont_write_bytecode = True
from generators import GENERATORS
from agent_paths import reserved_manifests

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ".generated.json"


def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def safe(path, boundary):
    path = Path(os.path.abspath(path))
    boundary = Path(os.path.abspath(boundary))
    if not path.is_relative_to(boundary) or path == boundary:
        raise ValueError(f"path must stay inside {boundary}: {path}")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"symlink: {current}")
        if current != path and current.is_file():
            raise ValueError(f"parent is not a directory: {current}")
        if current.exists() and not (current.is_dir() or current.is_file()):
            raise ValueError(f"special file: {current}")
    return path


def scan(path):
    safe(path, ROOT)
    if not path.exists():
        return {}
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        return {"": (path.read_bytes(), (0o755 if mode & 0o111 else 0o644))}
    if not stat.S_ISDIR(mode):
        raise ValueError(f"unsupported file: {path}")
    result = {"": None}
    for child in sorted(path.iterdir()):
        for relative, data in scan(child).items():
            result[child.name + ("/" + relative if relative else "")] = data
    return result


def config(path):
    safe(path, ROOT)
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or type(value.get("version")) is not int or value["version"] != 1:
        raise ValueError(f"unsupported configuration version: {path}")
    return value


def overlaps(a, b):
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def paths(value, key, path):
    items = value.get(key)
    if not isinstance(items, list):
        raise ValueError(f"{path}: {key} must be a list")
    return items


def validate_tree(tree):
    if not isinstance(tree, dict) or (tree and "" not in tree):
        raise ValueError("renderer must return a tree with a root")
    for rel, data in tree.items():
        if not isinstance(rel, str) or (rel and (Path(rel).is_absolute() or Path(rel).as_posix() != rel or any(p in (".", "..") for p in rel.split("/")))):
            raise ValueError(f"invalid renderer path: {rel!r}")
        if data is not None and (not isinstance(data, tuple) or len(data) != 2 or not isinstance(data[0], bytes) or type(data[1]) is not int or data[1] not in (0o644, 0o755)):
            raise ValueError(f"invalid renderer file: {rel}")
        if rel:
            for parent in Path(rel).parents:
                key = "" if str(parent) == "." else parent.as_posix()
                if key not in tree or tree[key] is not None:
                    raise ValueError(f"missing or conflicting renderer parent: {rel}")
        if data is None and not any(k != rel and (not rel or k.startswith(rel + "/")) and v is not None for k, v in tree.items()):
            raise ValueError(f"empty generated directory requires a placeholder: {rel}")
    return tree


@contextmanager
def sync_lock():
    # Lock the repository directory itself: no lock file to race with unlinking.
    lock = os.open(ROOT, os.O_RDONLY)
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another synchronization process is running")
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    finally:
        os.close(lock)


def prepare(adopt=False):
    pending = sorted(ROOT.glob(".repo-stage-*"))
    if pending:
        raise ValueError(f"unfinished synchronization; inspect recovery files before retrying: {pending}")
    root_config = config(ROOT / "repo-build.json")
    entries = []
    collections = []
    for name in paths(root_config, "collections", ROOT / "repo-build.json"):
        if not isinstance(name, str):
            raise ValueError("collection must be a path string")
        collection = safe(ROOT / name, ROOT)
        if any(overlaps(collection, other) for other in collections):
            raise ValueError(f"overlapping collections: {collection}")
        collections.append(collection)
        if not collection.is_dir():
            raise ValueError(f"missing collection: {collection}")
        for entry in sorted(collection.iterdir()):
            safe(entry, ROOT)
            if entry.is_dir() and any(p.exists() or p.is_symlink() for p in (entry / "build.json", entry / INVENTORY)):
                entries.append(entry)
    if (ROOT / ".git").exists():
        tracked = subprocess.run(["git", "ls-files", "-z", "--", "**/.generated.json"], cwd=ROOT, capture_output=True, check=True).stdout
        for name in tracked.decode().split("\0"):
            if not name:
                continue
            marker = safe(ROOT / name, ROOT)
            if not marker.exists():
                # A fully removed entry is retired. Leftover files require its ledger.
                if marker.parent.exists() and any(marker.parent.iterdir()):
                    raise ValueError(f"removed ownership inventory with remaining entry files: {marker}")
    for marker in ROOT.rglob(INVENTORY):
        if any(part in (".git",) or part.startswith(".repo-stage-") for part in marker.relative_to(ROOT).parts):
            continue
        if marker.parent not in entries:
            raise ValueError(f"inventory outside registered entries: {marker}")
    for marker in reserved_manifests(ROOT):
        if not (marker.parent / INVENTORY).exists():
            raise ValueError(f"generated manifest without ownership inventory: {marker}")
    jobs, sources, owned = [], [], []
    for entry in entries:
        recipe_path = safe(entry / "build.json", ROOT)
        safe(entry / INVENTORY, ROOT)
        steps = paths(config(recipe_path), "steps", recipe_path) if recipe_path.exists() else []
        old = []
        inventory = entry / INVENTORY
        if inventory.exists():
            old = paths(config(inventory), "outputs", inventory)
        old_paths = []
        for name in old:
            if not isinstance(name, str):
                raise ValueError(f"invalid inventory path: {inventory}")
            output = safe(entry / name, entry)
            if name != output.relative_to(entry).as_posix():
                raise ValueError(f"noncanonical inventory path: {name}")
            old_paths.append(output)
        new = {}
        for step in steps:
            if not isinstance(step, dict) or set(step) != {"generator", "source", "output"}:
                raise ValueError(f"invalid step: {recipe_path}")
            if not isinstance(step["generator"], str) or step["generator"] not in GENERATORS:
                raise ValueError(f"unknown generator: {step['generator']}")
            if not all(isinstance(step[key], str) and step[key] for key in ("source", "output")):
                raise ValueError(f"invalid step paths: {recipe_path}")
            source = safe(entry / step["source"], ROOT)
            if source.name == INVENTORY:
                raise ValueError(f"generated control file cannot be an input: {source}")
            output = safe(entry / step["output"], entry)
            if any(overlaps(output, other) for other in new):
                raise ValueError(f"overlapping outputs: {output}")
            if not source.exists():
                raise ValueError(f"missing source: {source}")
            sources.append(source)
            new[output] = validate_tree(GENERATORS[step["generator"]](source, scan))
        for group in (old_paths, list(new)):
            for index, output in enumerate(group):
                if any(overlaps(output, other) for other in group[:index]):
                    raise ValueError(f"overlapping outputs: {output}")
                if any(overlaps(output, entry / name) for name in ("build.json", INVENTORY)):
                    raise ValueError(f"output overlaps control file: {output}")
        roots = sorted(set(old_paths) | set(new))
        # Old roots may become ancestors of new roots (or vice versa).
        minimal = [p for p in roots if not any(p != q and p.is_relative_to(q) for q in roots)]
        desired = {}
        for base in minimal:
            tree = {}
            for output, content in new.items():
                if output.is_relative_to(base):
                    prefix = output.relative_to(base)
                    for rel, data in content.items():
                        target = prefix / rel
                        tree[target.as_posix() if target.as_posix() != "." else ""] = data
                        for parent in target.parents:
                            if parent.as_posix() == ".":
                                if output != base:
                                    tree.setdefault("", None)
                                break
                            tree.setdefault(parent.as_posix(), None)
            desired[base] = tree
            actual = scan(base)
            conflicts = []
            for rel, data in actual.items():
                target = base / rel
                if any(target == old or target.is_relative_to(old) for old in old_paths):
                    continue
                # Structural ancestors of owned roots contain no personal data themselves.
                if data is None and any(old.is_relative_to(target) and old != target for old in old_paths):
                    continue
                if rel not in tree or data != tree[rel]:
                    conflicts.append(target.relative_to(ROOT).as_posix())
            if conflicts:
                print("adoption replaces/removes:\n" + "\n".join(conflicts))
                if not adopt:
                    raise ValueError("unowned content conflicts; preview with sync --check --adopt, then explicitly sync --adopt")
        owned.extend(minimal)
        desired[inventory] = {"": (encoded({"version": 1, "outputs": sorted(p.relative_to(entry).as_posix() for p in new)}), 0o644)}
        jobs.extend(desired.items())
    for directory in reserved_manifests(ROOT):
        for rel, data in scan(directory).items():
            target = directory / rel
            if any(target == output or target.is_relative_to(output) for output in owned):
                continue
            if data is None and any(output.is_relative_to(target) for output in owned):
                continue
            raise ValueError(f"unexpected generated content without ownership: {target}")
    for output in owned + [entry / INVENTORY for entry in entries]:
        if any(overlaps(output, source) for source in sources):
            raise ValueError(f"source/output overlap: {output}")
    return jobs


def differences(jobs):
    drift = False
    for root, desired in jobs:
        actual = scan(root)
        for rel in sorted(set(actual) | set(desired)):
            label = None
            if rel not in desired:
                label = "obsolete" if not desired else "extra"
            elif rel not in actual:
                label = "missing"
            elif actual[rel] != desired[rel]:
                label = "changed"
            if label:
                drift = True
                print(f"{label}: {(root / rel).relative_to(ROOT)}")
    return drift


def install(jobs):
    # Stage on the same filesystem. Backups permit rollback on installation errors.
    stage = Path(tempfile.mkdtemp(prefix=".repo-stage-", dir=ROOT))
    retain = False
    try:
        replacements = []
        for index, (destination, content) in enumerate(jobs):
            staged = stage / str(index)
            for rel, data in sorted(content.items(), key=lambda item: (item[0].count('/'), item[0])):
                target = staged / rel
                if data is None:
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data[0])
                    target.chmod(data[1])
            replacements.append((destination, staged, stage / f"backup-{index}"))
        (stage / "recovery.json").write_bytes(encoded({"replacements": [
            {"destination": str(destination), "staged": str(staged), "backup": str(backup)}
            for destination, staged, backup in replacements
        ]}))
        completed, parents = [], []
        try:
            for destination, staged, backup in replacements:
                parent = destination.parent
                missing = []
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for parent in reversed(missing):
                    parent.mkdir()
                    parents.append(parent)
                if destination.exists():
                    destination.rename(backup)
                completed.append((destination, backup))
                if staged.exists():
                    staged.rename(destination)
        except BaseException:
            retain = True
            recovery_errors = []
            for destination, backup in reversed(completed):
                try:
                    if destination.is_dir():
                        shutil.rmtree(destination)
                    elif destination.exists():
                        destination.unlink()
                    if backup.exists():
                        backup.rename(destination)
                except OSError as error:
                    recovery_errors.append(str(error))
            for parent in reversed(parents):
                try:
                    parent.rmdir()
                except OSError:
                    pass
            if recovery_errors:
                print(f"recovery incomplete; backups retained at {stage}: {recovery_errors}", file=sys.stderr)
            else:
                retain = False
            raise

    finally:
        if not retain:
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sync", "validate"])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--adopt", action="store_true", help="explicitly adopt conflicting content (use --check to preview)")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            from validation import validate_assets
            validate_assets(ROOT, safe)
            print("Assets are valid.")
            return 0
        with sync_lock():
            return synchronize(args)
    except (OSError, ValueError, TypeError, AttributeError, shutil.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def synchronize(args):
    try:
        jobs = prepare(adopt=args.adopt)
        drift = differences(jobs)
        if args.check:
            if not drift:
                print("Generated content is in sync.")
            return int(drift)
        if drift:
            install(jobs)
        print("Generated content synchronized.")
        return 0
    except (OSError, ValueError, TypeError, AttributeError, shutil.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
