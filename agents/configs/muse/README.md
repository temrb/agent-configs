# Meta Muse Code configuration

The canonical source is [settings.json](.config/muse/settings.json) in
`agents/configs/muse/.config/muse/`. It preserves the supplied `specs/context/settings.json`
preferences: model and reasoning, approval profile, agent capacity, delegation,
telemetry, and endpoint transport. `specs/context` is ignored local context,
not a second maintained source. No Codex keys have been translated into Muse keys.

## Compatibility and installation scope

The public [Muse Code developer documentation](https://meta-models.github.io/muse-code-sdk/next/guides/extend/)
places user settings at `$XDG_CONFIG_HOME/muse/settings.json`, defaulting to
`~/.config/muse/settings.json`. This tree mirrors that standard user layout
relative to home; it is not automatically loaded from this repository.

Project assets have separate native locations: hooks in `.muse/hooks.json`,
MCP servers in root `.mcp.json`, and skills in `.agents/skills/`. The developer
documentation does not establish `.muse/settings.json` as a project settings
layer. Do not install this user settings file there.

The [configuration reference](https://ai.developer.meta.com/docs/muse-code/configuration)
still requires login. The supplied settings keys, model availability, and full
runtime compatibility remain unverified; validation checks syntax and paths.

## Install or export

From the repository root, use the standard user destination below, or set
`muse_destination` to an export staging directory:

```bash
muse_destination="${XDG_CONFIG_HOME:-$HOME/.config}/muse"
mkdir -p "$muse_destination"
if [ -e "$muse_destination/settings.json" ]; then
  cp -a "$muse_destination/settings.json" "$muse_destination/settings.json.backup-$(date +%Y%m%d-%H%M%S)"
fi
cp agents/configs/muse/.config/muse/settings.json "$muse_destination/settings.json"
```

Review and merge existing settings manually before replacing them. This copies
only settings; it does not install credentials or synchronize a live client.
Project settings equivalence is not assumed.

## Import and maintenance

Import only the reviewed settings file from a confirmed installation:

```bash
muse_source="${XDG_CONFIG_HOME:-$HOME/.config}/muse"
cp "$muse_source/settings.json" agents/configs/muse/.config/muse/settings.json
git diff -- agents/configs/muse/
git status --short
python3 scripts/repo.py validate
```

Review for embedded credentials and machine-specific endpoints before committing.
Never import an entire live directory. Keep authentication, sessions, history,
logs, caches, and databases outside the source. Edit this canonical entry first,
then export explicitly. Record the installed source revision, review its diff
before updates, and retire only previously installed assets; preserve unrelated
files. Companion assets should be added only after their native layout is verified.

## Validation

Python 3.11+ is required. `python3 scripts/repo.py validate` requires
`settings.json`, parses JSON assets, requires a top-level object in settings,
checks repository path safety, and rejects known runtime artifacts at any depth.
It does not verify Muse keys, models, precedence, or runtime behavior and is not
a secret scanner. Plugin `sync` neither installs nor generates this configuration.

See [collection policy](../README.md) and [standards](../../../docs/standards.md).
