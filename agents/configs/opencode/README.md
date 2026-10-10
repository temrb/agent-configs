# OpenCode configuration

The canonical source is [opencode.json](opencode.json) in
`agents/configs/opencode/`. It adopts the supplied `specs/context/opencode.json`
intent using the [OpenCode V2 configuration format](https://opencode.ai/v2/docs/config/).
The ignored context draft is not a second maintained source. This storage directory
is not an automatically installed configuration.

## Settings and compatibility

The configuration starts in plan mode, enables snapshots, requests update
notifications, defines ordered permissions, and adds a reviewer subagent and
review/verify commands. No provider or model is pinned; configure authentication
outside this repository. Review command references to architecture documents and
package.json are project conventions, not files supplied by this entry; adapt
them to each project.

This targets **V2**, whose plural `permissions`, `agents`, and `commands` differ
from V1. Do not install it unchanged into V1. No runtime version is pinned.
The [permission documentation](https://opencode.ai/v2/docs/permissions/) specifies
last-match-wins rules, with agent rules following global rules. Example environment
files are allowed after broader read denials. The reviewer denies edits and shell
execution except selected Git inspection. Shell permissions do not provide an OS
sandbox; the listed command patterns are not exhaustive protection against every
possible command. No Codex sandbox, reasoning, or agent-capacity settings are copied.

## Installation and precedence

The documented global destination is `~/.config/opencode/opencode.json`.
Project settings can be `<project>/opencode.json` or
`<project>/.opencode/opencode.json`. JSONC is also supported by the client;
this repository deliberately maintains strict JSON.

Global configuration loads before project configuration. OpenCode searches from
the current directory to the filesystem root, merges direct files from farthest
to closest, then `.opencode` files in the same order. Every discovered `.opencode`
configuration therefore overrides direct files. Nonconflicting values are retained;
use one project layout consistently. `update` is global-only; project values are
ignored. Permission arrays have their own ordered rule semantics.

From the repository root, select the destination explicitly:

```bash
# For project scope, use /path/to/project or /path/to/project/.opencode instead.
opencode_destination="$HOME/.config/opencode"
mkdir -p "$opencode_destination"
if [ -e "$opencode_destination/opencode.json" ]; then
  cp -a "$opencode_destination/opencode.json" "$opencode_destination/opencode.json.backup-$(date +%Y%m%d-%H%M%S)"
fi
cp agents/configs/opencode/opencode.json "$opencode_destination/opencode.json"
```

Review and merge destination preferences manually before replacement. Check for
an existing `opencode.jsonc` and consolidate it deliberately rather than depending
on precedence between JSON and JSONC. Export uses the same copy to a staging
directory. Installation is explicit; no repository command updates live settings.

## Import and maintenance

Copy only reviewed configuration, never the entire live config or data directory:

```bash
opencode_source="$HOME/.config/opencode"
cp "$opencode_source/opencode.json" agents/configs/opencode/opencode.json
git diff -- agents/configs/opencode/
git status --short
python3 scripts/repo.py validate
```

Convert JSONC to strict JSON before importing. Review for embedded secrets and
machine-specific paths. Keep credentials, sessions, logs, caches, dependencies,
and databases outside tracked sources. Edit the canonical entry first, record the
installed revision, and compare revisions before updates. Retire only previously
installed assets after reviewing a backup; preserve unrelated destination files.
Future file-based assets must retain their documented native relative layout.

## Validation

Python 3.11+ is required. `python3 scripts/repo.py validate` requires
`opencode.json`, parses JSON assets, requires a top-level configuration object,
checks repository path safety, and rejects known runtime artifacts at any depth.
It does not fetch or fully validate the upstream schema, resolve embedded paths,
verify provider availability, or execute the client. The `$schema` enables editor
validation; it does not make local validation exhaustive. Runtime-name checks
are bounded guards, not secret scanning. JSONC companion files are not parsed by
the local validator; maintain JSON assets here.

Plugin `sync` neither generates nor installs this tree. See
[collection policy](../README.md) and [standards](../../../docs/standards.md).
