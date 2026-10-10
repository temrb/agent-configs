# Build and maintenance

This document describes the repository's shared generation engine, not a client runtime. The [root README](../README.md) is the contributor entry point; [standards](standards.md) define compatibility boundaries.

## Repository generation

Canonical skills live in `agents/skills/<name>/`. Plugin metadata stays canonical in
`agents/plugins/<name>/plugin.json`. Generated skill trees and Codex manifests are
committed, so each plugin installs independently without a build step.
Repository validation requires Python 3.11+ for native TOML parsing.
Edit canonical inputs, then run:

```bash
python3 scripts/repo.py sync
python3 scripts/repo.py sync --check
python3 scripts/repo.py validate
python3 -B -m unittest discover -s tests
```

The CLI resolves the repository from its own location; an absolute script path
works from another directory. Check mode never writes and reports missing,
changed, extra, and obsolete content. Invalid configuration or drift fails the
check. The shared validation workflow runs tooling tests, asset validation, and the
generated-content check as separate checks.

`repo-build.json` registers `agents/plugins`; collection paths are relative to
the repository root. `scripts/agent_paths.py` defines shared collection roots
for asset and reserved manifest discovery. Native configuration layouts belong
with their platform-specific validators, rather than in the shared path module.
Each collection's immediate
entry directories may contain a version-1 `build.json` recipe. Prefine declares:

```json
{
  "version": 1,
  "steps": [
    {
      "generator": "copy-tree",
      "source": "../../skills/prefine",
      "output": "skills/prefine"
    },
    {
      "generator": "codex-manifest",
      "source": "plugin.json",
      "output": ".codex-plugin/plugin.json"
    }
  ]
}
```

Paths are relative to the recipe directory. Sources must stay inside the
repository; outputs must stay inside their entry. `copy-tree` copies all files,
nested resources and Git-compatible regular/executable modes (0644/0755).
Meaningful empty directories require a committed placeholder such as `.gitkeep`;
empty source directories are rejected. Other permission bits are ignored for
comparison. Use an explicit package format if richer metadata is ever needed. `codex-manifest`
copies the canonical name, version, description, author, and OpenAI interface;
keywords default to `[]` and skills to `./skills`. Required metadata and types
are checked before rendering.

The engine owns each declared output root, including all descendants. Its
committed `.generated.json` inventory records those roots. Removing a step
(or its recipe) removes previously owned output while preserving unrelated
entry files and sibling skills. Commit inventory changes with generated output;
do not edit inventories manually. Do not place handwritten files inside an
owned output root. First ownership and ownership expansion reject conflicting
unowned content. Existing identical content can be adopted without replacement.
For intentional replacement, first run `sync --check --adopt` and review the
listed files, then run `sync --adopt`. The flag authorizes the listed deletion
or replacement; save personal content outside the output before adopting.

All recipes, sources, inventories, and destinations are validated and rendered
before writing. Symlinks, special files, overlapping outputs, source/output
overlap, and outputs that cover control files are rejected. Replacements are
staged on the repository filesystem before installation; installation failures
and Python interruptions trigger rollback using backups. Failed restoration
retains the stage directory and prints its location; `recovery.json` maps each
backup to its destination. Inspect and restore those backups before removing
the retained stage directory and retrying. Concurrent sync/check processes are
rejected using a POSIX advisory lock on the repository directory. SIGKILL,
power loss, and filesystem failure do not guarantee automatic rollback; retained
stage directories block subsequent synchronization for manual recovery.
Filesystem errors produce a nonzero status.

Add a generated plugin by creating its canonical inputs, README, and recipe;
shared code and CI need no edits. Add a collection by listing its directory in
`repo-build.json`. Add a transformation by registering one renderer in
`scripts/generators.py`: it accepts a source path and tree scanner and returns
relative paths mapped to `(bytes, permission_mode)` for files or `None` for
directories (the empty path represents the output root). Renderers do not mutate
the filesystem; the engine handles ownership, comparisons, staging, and writes.
Steps are independent; chained generated inputs are not supported. Add fixture
coverage for a new renderer to the shared standard-library test suite.

## Extending the repository



Introduce a new asset type with a collection README defining canonical location,
entry shape, validation, and consumption. Plain snippets may remain plain files.
Recipes are optional; extend asset validation when the type arrives. No catalog
or dependency graph is required for the current collections.

Registering a collection enables build recipe discovery, not automatic asset validation. Each new asset type needs its own validator or an explicit decision that it is unvalidated. Client-native layouts and parsing belong in platform modules (for example `scripts/configs/codex.py`), not in the shared renderer interface.

## Asset validation and retirement

`python3 scripts/repo.py validate` also checks native Codex TOML/JSON and Muse/OpenCode
JSON independently of recipes (see [configuration entries](../agents/configs/README.md)).
Client modules under `scripts/configs/` require canonical files and check path
safety and known runtime artifacts. Muse and OpenCode share bounded JSON tree
checks; Muse schema and installation details remain unverified because its
official documentation requires login. These trees are never generated or
installed by plugin synchronization; `repo-build.json` is unchanged.
It inspects every canonical skill and plugin,
including entries without recipes, plus bundled skills and existing Codex
manifests. The local contract requires plugin README, name, semantic version,
description, author name, typed optional interface/keywords, and existing skill
and declared resource paths. Skill frontmatter uses unique single-line fields
between `---` delimiters, with a directory-matching name, nonempty description,
and instruction body; relative Markdown resource links must resolve. This
standard-library validator enforces the repository's supported subset; a
`$schema` URL is metadata, not a claim of complete upstream schema validation.
New manifest features need corresponding validation before use.

Build discovery uses registered immediate entry directories. Inventory discovery
also checks outside registered collections, and reserved Codex output directories
require inventories. In Git working trees, deleting a tracked inventory while
entry files remain is diagnosed. Arbitrary copies with all ownership evidence
removed cannot be identified reliably as generated; never erase the evidence
before retiring outputs.

To retire an entry, remove its recipe steps, synchronize to remove owned outputs,
and commit the empty inventory with those deletions. Then remove the entire entry
(or retain its empty inventory if canonical entry files remain), and finally
remove unused collection registration. Do not remove both control files while
leaving generated files behind.

## Releases

Changes to shipped instructions, resources, or manifest behavior require reviewing
all recipes consuming the changed canonical source and bumping each affected
plugin's semantic version. Synchronization does not infer or enforce version
bumps. Standalone skills use the repository Git commit as their release identity.
Before releasing, run tests, `validate`, and `sync --check`; commit canonical
inputs, generated bundles, Codex manifests, and inventories together. Tag that
commit as `<plugin-name>/v<version>` (for example `prefine/v0.1.1`). Do not reuse
release tags. Independent skill version manifests can wait until needed.
