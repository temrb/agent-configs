#!/usr/bin/env python3
"""Create an answer-key-free, isolated workspace for one evaluation run."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-id", type=int, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    skill_group = parser.add_mutually_exclusive_group()
    skill_group.add_argument(
        "--skill-source",
        type=Path,
        help="Skill version to copy without its evals directory; defaults to the current package.",
    )
    skill_group.add_argument(
        "--without-skill",
        action="store_true",
        help="Stage a true without-skill baseline and omit the skill directory.",
    )
    return parser.parse_args()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def reject_overlap(destination: Path, protected_roots: list[Path]) -> None:
    for root in protected_roots:
        if is_within(destination, root) or is_within(root, destination):
            raise SystemExit(
                f"destination overlaps protected source tree: {destination} <-> {root}"
            )


def reject_symlinks(root: Path, *, ignored_top_level: set[str] | None = None) -> None:
    ignored = ignored_top_level or set()
    if root.is_symlink():
        raise SystemExit(f"symlink sources are not allowed: {root}")
    if not root.is_dir():
        return
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root)
        if relative.parts and relative.parts[0] in ignored:
            continue
        if candidate.is_symlink():
            raise SystemExit(f"nested symlink is not allowed: {candidate}")


def resolve_eval_input(package_root: Path, eval_root: Path, relative_name: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"invalid eval input path: {relative_name}")

    unresolved = package_root / relative
    if unresolved.is_symlink():
        raise SystemExit(f"symlink eval input is not allowed: {relative_name}")
    try:
        source = unresolved.resolve(strict=True)
    except FileNotFoundError as error:
        raise SystemExit(f"missing eval input: {relative_name}") from error
    if not is_within(source, eval_root):
        raise SystemExit(f"eval input escapes evals directory: {relative_name}")
    reject_symlinks(source)
    return source


def main() -> None:
    args = parse_args()
    eval_root = Path(__file__).resolve().parent
    package_root = eval_root.parent.resolve()
    destination = args.destination.resolve()

    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")

    skill_source: Path | None = None
    protected_roots = [package_root, eval_root]
    if not args.without_skill:
        supplied_skill = args.skill_source or package_root
        if supplied_skill.is_symlink():
            raise SystemExit(f"symlink skill source is not allowed: {supplied_skill}")
        skill_source = supplied_skill.resolve(strict=True)
        if not (skill_source / "SKILL.md").is_file():
            raise SystemExit(f"not a skill directory: {skill_source}")
        reject_symlinks(skill_source, ignored_top_level={"evals"})
        protected_roots.append(skill_source)

    reject_overlap(destination, protected_roots)

    data = json.loads((eval_root / "evals.json").read_text(encoding="utf-8"))
    try:
        case = next(item for item in data["evals"] if item["id"] == args.eval_id)
    except StopIteration as error:
        raise SystemExit(f"unknown eval id: {args.eval_id}") from error

    input_sources = [
        resolve_eval_input(package_root, eval_root, relative_name)
        for relative_name in case.get("files", [])
    ]

    destination.mkdir(parents=True)
    if skill_source is not None:
        shutil.copytree(
            skill_source,
            destination / "skill",
            ignore=shutil.ignore_patterns(
                "evals", ".git", ".DS_Store", "__pycache__", "*.pyc"
            ),
        )

    input_root = destination / "input"
    input_root.mkdir()
    (destination / "output").mkdir()
    copied_inputs: list[str] = []
    for source in input_sources:
        target = input_root / source.name
        if target.exists():
            raise SystemExit(f"duplicate staged input name: {source.name}")
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        copied_inputs.append(str(target.relative_to(destination)))

    task = {
        "eval_id": case["id"],
        "eval_name": case.get("name", f"eval-{case['id']}"),
        "prompt": case["prompt"],
        "inputs": copied_inputs,
        "deliverables": {
            "worktree": "output/worktree",
            "report": "output/report.md",
        },
    }
    (destination / "task.json").write_text(
        json.dumps(task, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
