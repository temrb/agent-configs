# skills

Each subdirectory is one standalone canonical skill. Expected shape:
`<name>/SKILL.md`. `SKILL.md` is the doc; the directory listing is the index.

Plugins bundle committed copies of canonical skills through declarative recipes.
Edit canonical files and synchronize before committing. See the
[repository generation workflow](../../README.md#repository-generation).
Installation of a generated plugin requires no build step.

Validation requires a directory-matching name and nonempty description in
single-line frontmatter, an instruction body, and resolving local Markdown links.
Run `python3 scripts/repo.py validate`. Installable standalone copies are identified
by Git commit; generated plugin copies are identified by their plugin release.
See each plugin README for client installation and update procedures.
