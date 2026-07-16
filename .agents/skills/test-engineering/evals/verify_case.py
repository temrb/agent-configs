#!/usr/bin/env python3
"""Verify deterministic evaluation deliverables without executing agent-authored code."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-id", type=int, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def tree_state(root: Path) -> tuple[dict[str, str], list[str]]:
    files: dict[str, str] = {}
    symlinks: list[str] = []
    if not root.is_dir():
        return files, symlinks
    for candidate in sorted(root.rglob("*")):
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            symlinks.append(relative)
        elif candidate.is_file():
            files[relative] = digest(candidate)
    return files, symlinks


def changes(
    original: dict[str, str], candidate: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    changed = sorted(
        path for path in original.keys() & candidate.keys() if original[path] != candidate[path]
    )
    added = sorted(candidate.keys() - original.keys())
    removed = sorted(original.keys() - candidate.keys())
    return changed, added, removed


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, evidence: str) -> None:
    checks.append({"name": name, "passed": passed, "evidence": evidence})


def main() -> int:
    args = parse_args()
    eval_root = Path(__file__).resolve().parent
    run_directory = args.run_directory.resolve()
    policy = json.loads((eval_root / "verification.json").read_text(encoding="utf-8"))
    try:
        case = policy["cases"][str(args.eval_id)]
    except KeyError as error:
        raise SystemExit(f"no verification policy for eval {args.eval_id}") from error

    fixture = (eval_root / case["fixture"]).resolve(strict=True)
    try:
        fixture.relative_to(eval_root)
    except ValueError as error:
        raise SystemExit(f"verification fixture escapes eval root: {fixture}") from error

    staged_input = run_directory / "input" / fixture.name
    worktree = run_directory / "output" / "worktree"
    report = run_directory / "output" / "report.md"
    checks: list[dict[str, Any]] = []

    original_files, original_links = tree_state(fixture)
    input_files, input_links = tree_state(staged_input)
    output_files, output_links = tree_state(worktree)

    add_check(checks, "fixture_has_no_symlinks", not original_links, repr(original_links))
    add_check(checks, "staged_input_exists", staged_input.is_dir(), str(staged_input))
    add_check(checks, "staged_input_has_no_symlinks", not input_links, repr(input_links))
    add_check(
        checks,
        "staged_input_unchanged",
        input_files == original_files,
        repr(changes(original_files, input_files)),
    )
    add_check(checks, "output_worktree_exists", worktree.is_dir(), str(worktree))
    add_check(checks, "output_worktree_has_no_symlinks", not output_links, repr(output_links))
    add_check(
        checks,
        "report_exists",
        report.is_file() and not report.is_symlink(),
        str(report),
    )
    report_nonempty = report.is_file() and report.stat().st_size > 0
    add_check(checks, "report_nonempty", report_nonempty, str(report))

    forbidden_components = set(policy.get("forbidden_components", []))
    forbidden_paths = sorted(
        path
        for path in output_files
        if any(component in forbidden_components for component in Path(path).parts)
    )
    add_check(checks, "no_forbidden_output_artifacts", not forbidden_paths, repr(forbidden_paths))

    changed, added, removed = changes(original_files, output_files)
    all_changes = sorted(set(changed + added + removed))
    mutation_policy = case["mutation_policy"]
    if mutation_policy == "unchanged":
        add_check(
            checks,
            "output_worktree_unchanged",
            not all_changes,
            repr({"changed": changed, "added": added, "removed": removed}),
        )
    elif mutation_policy == "allowlist":
        patterns = case.get("allowed_changes", [])
        outside = [path for path in all_changes if not matches_any(path, patterns)]
        add_check(checks, "changes_within_allowlist", not outside, repr(outside))
        if case.get("required_change"):
            add_check(checks, "required_change_present", bool(all_changes), repr(all_changes))
    else:
        raise SystemExit(f"unknown mutation policy: {mutation_policy}")

    passed = sum(1 for check in checks if check["passed"])
    result = {
        "eval_id": args.eval_id,
        "checks": checks,
        "changes": {"changed": changed, "added": added, "removed": removed},
        "summary": {
            "passed": passed,
            "failed": len(checks) - passed,
            "total": len(checks),
            "pass_rate": passed / len(checks) if checks else 0.0,
        },
        "semantic_validation": "not performed",
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_output:
        args.json_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
