# agent-configs

Maintainable, reusable agent assets for supported clients. The filesystem is the index: browse `agents/` to discover the current entries.

## Principles

- **One canonical source:** edit an asset in its canonical collection rather than a bundled or installed copy.
- **Explicit distribution:** generated plugin assets are reproducible and committed so packages can be used independently.
- **Client-neutral core:** common skill, plugin, and build policies apply across clients; Codex-specific configuration and adapters belong in Codex-specific locations.
- **Documented compatibility:** a portable file layout is not a promise that every agent client installs or executes it identically.
- **Safe maintenance:** validate sources, generated artifacts, and ownership before release; never commit runtime credentials or state.

## Collections

| Collection | Purpose | Canonical location |
| --- | --- | --- |
| [Skills](agents/skills/README.md) | Reusable Agent Skills | `agents/skills/<name>/` |
| [Plugins](agents/plugins/README.md) | Distributable plugin packages with optional bundled components | `agents/plugins/<name>/` |
| [Configurations](agents/configs/README.md) | Client-native configuration and companion assets | `agents/configs/<platform>/` |

Each collection README defines its asset contract, installation or consumption boundary, and extension procedure. Client-specific instructions, such as [Codex configuration](agents/configs/codex/README.md) and [Prefine installation](agents/plugins/prefine/README.md), live with their entries.

## Maintain

Python 3.11+ is required. From the repository root:

```bash
python3 scripts/repo.py sync
python3 scripts/repo.py sync --check
python3 scripts/repo.py validate
python3 -B -m unittest discover -s tests
python3 -B scripts/check_docs.py
```

Edit canonical sources first. `sync` rebuilds declared generated outputs; `sync --check` detects drift without writing; `validate` checks supported asset contracts. The tests exercise rendering, ownership, and validation. Generated contents and their `.generated.json` inventories are committed together.

See [Build and maintenance](docs/build-system.md) for recipes, ownership, recovery, adoption, and retirement; see [Standards and compatibility](docs/standards.md) for terminology, external specifications, and repository-specific policy.

## Adding entries

Add a skill, plugin, or native configuration beneath its collection using that collection's README. No manually maintained root catalog is needed. New *generated* collections are registered in `repo-build.json`; new asset types or validators also require explicit code and test coverage. See [extension boundaries](docs/build-system.md#extending-the-repository).

## Releases

Review each consumer of changed canonical inputs, synchronize, validate, run the tests, and commit generated outputs and ownership inventories. Plugins use semantic versions and immutable tags; standalone skills use Git commits as release identities. See [release policy](docs/build-system.md#releases).
