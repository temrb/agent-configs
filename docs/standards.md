# Standards and compatibility

## Source of truth

Each asset has exactly one canonical location. The repository distinguishes:

- **Canonical source:** manually maintained input to a plugin, skill, or native configuration.
- **Generated output:** files under an output root declared in `build.json` and owned by `.generated.json`. Never edit directly.
- **Installed configuration:** a client-native copy in a user or project destination. The root `.codex/`, if present locally, is an ignored installation, not a maintained repository source.
- **Compatibility artifact:** a client-specific format rendered from a portable source, such as `.codex-plugin/plugin.json`.

Do not infer compatibility with an agent client merely from a portable package layout. Each client entry documents installation scope, runtime precedence, and support status.

## External specifications and local policies

| Asset | Upstream reference | Repository contract |
| --- | --- | --- |
| Portable plugin | [Agent Plugins v1.0.0](https://agent-plugins.org/specification) | The portable `plugin.json` uses the canonical v1.0.0 `$schema` when declared (required for this repository's published plugin). This repository additionally requires `version` (semantic version), `description`, and `author.name` for releases. Core manifest fields cannot be replaced by client-specific ones. |
| Skill | [Agent Skills](https://agentskills.io/specification) | `SKILL.md` requires matching name, description, and body. The standard-library validator currently accepts a documented **single-line YAML frontmatter subset**, not arbitrary YAML; name and description length limits are enforced. |
| Codex configuration | [Codex config reference](https://developers.openai.com/codex/config-reference) | Native TOML/JSON syntax and repository path safety are checked, not full Codex runtime or schema compatibility. |

Client-specific settings and extensions stay in their platform namespaces; they must not be generalized into the root asset contract. This repository validates the supported local subset and cannot claim exhaustive upstream schema coverage without an explicit conformance test suite.

## Naming and metadata

- Collection entry names are the directory names; portable plugin names and skills must match their entry directories.
- Portable plugin names follow Agent Plugins v1.0.0, including valid periods; skill names follow Agent Skills (lowercase alphanumeric and internal hyphens).
- Package version bumps are required for user-visible behavior or metadata changes. A Git tag (`<plugin-name>/v<version>`) identifies an immutable plugin release. A standalone skill's Git commit identifies its release.
- User-facing defaults belong in the canonical skill contract; examples and client metadata must agree with it. Avoid independently maintaining a model catalog or copying the same default into multiple documents.
- Extension-specific metadata may be validated locally, but unknown extensions are not assumed to have a portable meaning.

## Documentation responsibilities

| Document | Owns |
| --- | --- |
| [Root README](../README.md) | Purpose, shared principles, collection navigation, quick commands |
| [Build and maintenance](build-system.md) | Recipe format, generated ownership, recovery, and release mechanics |
| Collection README | Canonical input and entry structure for one asset type |
| Entry README | Concrete installation, consumption, and supported-client behavior |
| This document | Cross-cutting terminology, policy, and upstream compatibility boundaries |

Use relative repository links. Document command prerequisites and destructive behavior. When changing a contract, update the canonical documentation, the relevant validator, and positive/negative tests together. CI checks local links and build drift, but does not substitute for manual client smoke tests.
