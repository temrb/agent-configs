# agent-configs

Maintainable, reusable agent assets for supported clients. The filesystem is the index: browse `agents/` to discover the current entries.

## Principles

- **One canonical source:** edit an asset in its canonical collection rather than a bundled or installed copy.
- **Explicit distribution:** generated plugin assets are reproducible and committed so packages can be used independently.
- **Client-neutral core:** common skill, plugin, and build policies apply across clients; client-specific configuration and adapters belong in client-specific locations.
- **Documented compatibility:** a portable file layout is not a promise that every agent client installs or executes it identically.
- **Safe maintenance:** validate sources, generated artifacts, and ownership before release; never commit runtime credentials or state.

## Collections

| Collection | Purpose | Canonical location |
| --- | --- | --- |
| [Skills](agents/skills/README.md) | Reusable Agent Skills | `agents/skills/<name>/` |
| [Plugins](agents/plugins/README.md) | Distributable plugin packages with optional bundled components | `agents/plugins/<name>/` |
| [Configurations](agents/configs/README.md) | Client-native configuration and companion assets | `agents/configs/<platform>/` |

Each collection README defines its asset contract, installation or consumption boundary, and extension procedure. Client-specific instructions, including [Codex](agents/configs/codex/README.md), [Meta Muse Code](agents/configs/muse/README.md), [OpenCode](agents/configs/opencode/README.md), and [Prefine installation](agents/plugins/prefine/README.md), live with their entries.

Feature documentation lives beside its canonical skill, plugin, or platform
configuration; root `docs/` holds only shared repository documentation. See the
[documentation ownership policy](docs/standards.md#documentation-responsibilities).

## Maintain

Python 3.11+, Node 24.19.0, and Bun 1.4.2 are required for the complete check.
From the repository root:

```bash
python3 -B scripts/check.py
python3 scripts/repo.py sync
python3 scripts/repo.py sync --check
python3 scripts/repo.py validate
python3 -B -m unittest discover -s tests
python3 -B scripts/check_docs.py
node --test agents/skills/vine/tests/*.test.mjs
```

`scripts/check.py` runs all validation and tests without installing dependencies or regenerating content. It resolves the repository from its script location, so an absolute script path works from any directory. Python suites in `agents/skills/*/tests/test_*.py` run through the root test suite once; JavaScript files in `agents/skills/*/tests/*.test.mjs` run together per skill in sorted order.

Edit canonical sources first. `sync` rebuilds declared generated outputs; `sync --check` detects drift without writing; `validate` checks supported asset contracts. The Python suite exercises rendering, ownership, validation, and skill-owned Python tests. VINE's lifecycle suite additionally requires Node 24.19.0 and Bun 1.4.2; these runtimes are not needed for shared tooling. Generated contents and their `.generated.json` inventories are committed together.

See [Build and maintenance](docs/build-system.md) for recipes, ownership, recovery, adoption, and retirement; see [Standards and compatibility](docs/standards.md) for terminology, external specifications, and repository-specific policy.

## Adding entries

Add a skill, plugin, or native configuration beneath its collection using that collection's README. No manually maintained root catalog is needed. New *generated* collections are registered in `repo-build.json`; new asset types or validators also require explicit code and test coverage. See [extension boundaries](docs/build-system.md#extending-the-repository).

## Releases

Review each consumer of changed canonical inputs, synchronize, validate, run the tests, and commit generated outputs and ownership inventories. Plugins use semantic versions and immutable tags; standalone skills use Git commits as release identities. See [release policy](docs/build-system.md#releases).

Client and behavioral run evidence is tracked in [compatibility evidence](docs/compatibility.md).
