# Skill collection

Each immediate entry `agents/skills/<name>/` contains the canonical `SKILL.md` and optional resources. The directory listing is the index; `SKILL.md` is the authoritative instruction contract. Skills follow the [Agent Skills specification](https://agentskills.io/specification).

Frontmatter needs a matching lowercase hyphenated `name` (1–64 characters), a nonempty `description` (up to 1024 characters), and a body. The current standard-library validator intentionally supports a **single-line frontmatter subset**, not arbitrary YAML mappings or block scalars; `compatibility` is capped at 500 characters. Markdown resource links must resolve. See [standards](../../docs/standards.md) for the distinction between this supported subset and full upstream conformance.

Plugins may bundle committed copies of these sources through declarative generation recipes. Edit only the canonical skill and run `python3 scripts/repo.py sync`, then `sync --check` and `validate` before committing; generated bundles install without a repository build step.

Standalone skills use a Git commit as their release identity; generated plugin bundles use the consuming plugin's version/tag. Client installation paths and discovery behavior are documented with the relevant plugin or client, rather than assumed to be universal.
