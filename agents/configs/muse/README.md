# Meta Muse Code configuration

The canonical source is [settings.json](settings.json) in
`agents/configs/muse/`. It preserves the supplied `specs/context/settings.json`
preferences: model and reasoning, approval profile, agent capacity, delegation,
telemetry, and endpoint transport. `specs/context` is ignored local context,
not a second maintained source. No Codex keys have been translated into Muse keys.

## Compatibility and installation scope

The [official configuration documentation](https://ai.developer.meta.com/docs/muse-code/configuration)
returned “Not Logged In” during implementation. The supplied keys, model availability,
native user/project directory names, scope restrictions, and precedence could not
be independently verified. This entry is a maintained context-derived configuration,
with syntax validation, pending native compatibility verification. It makes no
claim that Muse automatically loads this repository directory or that its approval
profile provides Codex sandbox behavior. Do not rely on these settings as a verified
security boundary.

Before activation, consult the documentation with authenticated access and confirm
the supported keys, destination, and precedence for your installed Muse release.
No user or project destination is guessed here.

## Install or export

From the repository root, set `muse_destination` to the **confirmed directory**
for the intended user or project scope, or an export staging directory:

```bash
: "${muse_destination:?Set a confirmed destination or export staging directory}"
mkdir -p "$muse_destination"
if [ -e "$muse_destination/settings.json" ]; then
  cp -a "$muse_destination/settings.json" "$muse_destination/settings.json.backup-$(date +%Y%m%d-%H%M%S)"
fi
cp agents/configs/muse/settings.json "$muse_destination/settings.json"
```

Review and merge existing settings manually before replacing them. This copies
only settings; it does not install credentials or synchronize a live client.
User/project equivalence and precedence remain unverified.

## Import and maintenance

Import only the reviewed settings file from a confirmed installation:

```bash
: "${muse_source:?Set the confirmed source directory}"
cp "$muse_source/settings.json" agents/configs/muse/settings.json
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
