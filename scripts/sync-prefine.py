#!/usr/bin/env python3
"""Synchronize the canonical Prefine skill to its generated plugin copy.

Canonical source: ``skills/prefine/``
Generated copy: ``plugins/prefine/skills/prefine/``

Edit canonical files only, then run this script before committing::

    python3 scripts/sync-prefine.py
    python3 scripts/sync-prefine.py --check

The sync replaces only ``plugins/prefine/skills/prefine/`` and preserves
sibling plugin skills. Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "skills" / "prefine"
DST_DIR = REPO_ROOT / "plugins" / "prefine" / "skills" / "prefine"


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_files(root: Path) -> dict[str, Path]:
    """Map relative POSIX paths to absolute paths for regular files under root.

    Raises SystemExit with an error message if root is missing or if any
    symlink is found in the tree (including root itself).
    """
    if root.is_symlink():
        print(f"error: symlink found: {root}", file=sys.stderr)
        raise SystemExit(1)
    if not root.is_dir():
        print(f"error: missing directory: {root}", file=sys.stderr)
        raise SystemExit(1)

    files: dict[str, Path] = {}
    symlinks: list[str] = []
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as it:
            entries = sorted(it, key=lambda e: e.name)
            for entry in entries:
                entry_path = Path(entry.path)
                # Check symlink first so symlinked dirs/files are rejected
                # without being followed.
                if entry.is_symlink():
                    symlinks.append(_relative_posix(entry_path, root))
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry_path)
                elif entry.is_file(follow_symlinks=False):
                    rel = _relative_posix(entry_path, root)
                    files[rel] = entry_path
                else:
                    # Skip sockets, FIFOs, devices, etc. but treat them as
                    # errors since the skill copy must be plain files.
                    print(
                        f"error: unsupported file type: {entry_path}",
                        file=sys.stderr,
                    )
                    raise SystemExit(1)

    if symlinks:
        for rel in symlinks:
            print(f"error: symlink found: {rel}", file=sys.stderr)
        raise SystemExit(1)
    return files


def _read_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def check() -> int:
    """Compare canonical and plugin trees without writing. Return exit code."""
    try:
        src_files = collect_files(SRC_DIR)
    except SystemExit as e:
        return int(e.code or 1)
    if DST_DIR.is_symlink():
        print(f"error: symlink found at destination root: {DST_DIR}", file=sys.stderr)
        return 1
    if not DST_DIR.is_dir():
        print(f"error: destination directory missing: {DST_DIR}", file=sys.stderr)
        print(f"missing: all {len(src_files)} file(s) from canonical skill", file=sys.stderr)
        return 1
    try:
        dst_files = collect_files(DST_DIR)
    except SystemExit as e:
        return int(e.code or 1)

    src_names = set(src_files)
    dst_names = set(dst_files)
    missing = sorted(src_names - dst_names)
    extra = sorted(dst_names - src_names)
    changed = sorted(
        name
        for name in sorted(src_names & dst_names)
        if _read_bytes(src_files[name]) != _read_bytes(dst_files[name])
    )

    if not missing and not extra and not changed:
        print("prefine skill in sync: canonical and plugin copies match")
        return 0

    for name in missing:
        print(f"missing in plugin copy: {name}")
    for name in extra:
        print(f"extra in plugin copy: {name}")
    for name in changed:
        print(f"changed in plugin copy: {name}")
    return 1


def sync() -> int:
    """Replace the plugin copy with the canonical tree. Return exit code."""
    try:
        src_files = collect_files(SRC_DIR)
    except SystemExit as e:
        return int(e.code or 1)
    if DST_DIR.is_symlink():
        print(f"error: symlink found at destination root: {DST_DIR}", file=sys.stderr)
        return 1
    if DST_DIR.exists():
        # Reject symlinks in the destination tree before deleting anything.
        try:
            collect_files(DST_DIR)
        except SystemExit as e:
            return int(e.code or 1)
        # Limit writes to the Prefine destination directory; sibling plugin
        # skills under plugins/prefine/skills/ are left untouched.
        shutil.rmtree(DST_DIR)
    DST_DIR.mkdir(parents=True, exist_ok=True)

    for rel in sorted(src_files):
        src_path = src_files[rel]
        dst_path = DST_DIR / Path(rel)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

    print(f"synced {len(src_files)} file(s) to {DST_DIR.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync skills/prefine/ to plugins/prefine/skills/prefine/."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare trees without writing; exit nonzero on any difference",
    )
    args = parser.parse_args(argv)
    return check() if args.check else sync()


if __name__ == "__main__":
    raise SystemExit(main())
