#!/usr/bin/env python3
"""Run the repository's complete, read-only validation suite."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    suites = {}
    for path in sorted((ROOT / "agents/skills").glob("*/tests/*.test.mjs")):
        suites.setdefault(path.parent.parent.name, []).append(str(path))
    if suites:
        missing = [runtime for runtime in ("node", "bun") if not shutil.which(runtime)]
        if missing:
            print("Missing runtime prerequisites: " + ", ".join(missing)
                  + ". JavaScript suites require Node 24.19.0 and Bun 1.4.2.",
                  file=sys.stderr, flush=True)
            return 1

    checks = [
        ("Documentation links", [sys.executable, "-B", str(ROOT / "scripts/check_docs.py")]),
        ("Python tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"]),
        ("Asset validation", [sys.executable, "-B", str(ROOT / "scripts/repo.py"), "validate"]),
        ("Generated-content drift", [sys.executable, "-B", str(ROOT / "scripts/repo.py"), "sync", "--check"]),
    ]
    checks.extend((f"JavaScript tests: {skill}", ["node", "--test", *paths])
                  for skill, paths in suites.items())
    for name, command in checks:
        print(f"==> {name}", flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT)
        except OSError as error:
            print(f"{name} could not run: {error}", file=sys.stderr, flush=True)
            return 1
        if result.returncode:
            print(f"{name} failed (exit {result.returncode}).", file=sys.stderr, flush=True)
            return result.returncode if result.returncode > 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
