# Repository Guidelines

## Project Structure & Module Organization

This repository maintains reusable agent assets and their distribution tooling.
Canonical skills live in `agents/skills/<name>/`, plugins in
`agents/plugins/<name>/`, and client configurations in `agents/configs/<platform>/`.
Python maintenance tools live in `scripts/`, with platform validators in
`scripts/configs/`. Root `tests/` covers shared tooling; skill-specific tests,
fixtures, and documentation belong beside the skill. Root `docs/` contains shared
policies and build documentation. `repo-build.json` registers generated collections.

## Build, Test, and Development Commands

Use Python 3.11+ and run these commands from the repository root:

- `python3 -B scripts/check.py`: run all checks; requires Node 24.19.0 and Bun 1.4.2 alongside Python. The script resolves repository paths from its location.
- `python3 scripts/repo.py sync`: regenerate declared plugin outputs.
- `python3 scripts/repo.py sync --check`: detect generated-content drift without writing.
- `python3 scripts/repo.py validate`: validate canonical assets, bundles, and native configurations.
- `python3 -B -m unittest discover -s tests`: run shared tooling and skill-owned Python tests.
- `python3 -B scripts/check_docs.py`: check local documentation links.
- `node --test agents/skills/vine/tests/*.test.mjs`: run VINE lifecycle tests; CI uses Node 24.19.0 and Bun 1.4.2.

## Coding Style & Naming Conventions

Follow existing file conventions: four-space indentation for Python and two spaces
for JavaScript and JSON. Use `snake_case` for Python functions and modules.
Skill directory names use lowercase letters, digits, and internal hyphens;
manifest names must match their directories. Use relative Markdown links.
No repository-wide formatter or linter is configured.

Edit canonical sources, then synchronize. Never edit generated output roots or
`.generated.json` inventories manually. Keep feature documentation with its owner.

## Testing Guidelines

Shared tests use standard-library `unittest`: name files `test_*.py` and methods
`test_*`. JavaScript suites use `agents/skills/*/tests/*.test.mjs`; the complete check discovers them automatically and runs sorted files together per skill. Skill Python suites in `agents/skills/*/tests/test_*.py` are discovered once through the root suite. Add positive and negative
cases when changing validation or generation contracts, including failure paths
and ownership behavior. Run the applicable tests and all repository checks before
submitting. No numeric coverage threshold is configured.

## Commit & Pull Request Guidelines

History uses concise imperative summaries and occasional scoped prefixes such as
`docs(prefine):`; follow that pattern without assuming strict Conventional Commits.
Pull requests should explain the behavior changed, affected assets, and validation
performed, and link relevant issues. Commit canonical changes, generated outputs,
and inventories together. Shipped plugin changes require reviewing consumers and
bumping affected semantic versions; release tags use `<plugin-name>/v<version>`.

## Security & Configuration

Never commit credentials or runtime state. Treat root `.codex/` as an ignored
local installation; maintained Codex sources belong under `agents/configs/codex/`.
