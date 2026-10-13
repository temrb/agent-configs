# Skill collection

Each immediate entry `agents/skills/<name>/` contains the canonical `SKILL.md` and optional resources. The directory listing is the index; `SKILL.md` is the authoritative instruction contract. Skills follow the [Agent Skills specification](https://agentskills.io/specification).

Frontmatter needs a matching lowercase hyphenated `name` (1–64 characters), a nonempty `description` (up to 1024 characters), and a body. The current standard-library validator intentionally supports a **single-line frontmatter subset**, not arbitrary YAML mappings or block scalars; `compatibility` is capped at 500 characters. Markdown resource links must resolve. See [standards](../../docs/standards.md) for the distinction between this supported subset and full upstream conformance.

Optional `docs/` holds skill-specific guides; `tests/` holds feature-specific
tests, evaluation fixtures, and supporting test resources. These resources are
maintained beside the canonical `SKILL.md`. Shared tooling and cross-feature
integration tests belong in root `tests/`.

Root tests discover skill-owned `tests/test_*.py` suites and run each in an
isolated Python process. Other runtimes use explicit CI jobs with requirements
documented beside the skill. These mechanics checks do not establish model
effectiveness. Standalone skills with runtime resources should provide a
skill-local installation guide and keep installer ownership separate from
repository-generated plugin ownership; see VINE's
[installation guide](vine/docs/installation.md) for that lifecycle.

Plugins may bundle committed copies of these sources through declarative
generation recipes. Edit only the canonical skill and run
`python3 scripts/repo.py sync`, then `sync --check` and `validate` before committing;
generated bundles install without a repository build step. Use `copy-skill` as
the standard skill recipe: it creates the skill directory containing only
`SKILL.md`. Development docs, tests, and fixtures stay in the canonical source.
Required runtime resources must be explicitly included through additional recipe
steps, with links resolving inside the distributed package.

Standalone skills use a Git commit as their release identity; generated plugin bundles use the consuming plugin's version/tag. Client installation paths and discovery behavior are documented with the relevant plugin or client, rather than assumed to be universal.

`skills add` sources must be scoped to `agents/skills`, never the bare repository, to avoid the generated Prefine duplicate. See Prefine [installation](prefine/docs/installation.md) and VINE [installation](vine/docs/installation.md); VINE supports only its custom installer, not `skills add`.
