# Standalone installation and lifecycle

The runtime inventory is the explicit `RUNTIME` list in
[the installer](../scripts/install.mjs). It contains only the skill, runtime
references, schemas and ESM helpers. Tests, development docs and evaluator data
are excluded. Python 3.11+ remains required for source repository validation.
No plugin or hook registration is required.

From a reviewed pinned source checkout, using Node 24.19.0:

```sh
node /source/agents/skills/vine/scripts/install.mjs --root /consumer
```

The installer compares runtime bytes to its source Git commit, preserving modes.
Uncommitted source is rejected for release installation. For local development
only, add `--development true`; the resulting inventory is explicitly provisional.
The source commit, digests and compatibility are recorded at `.vine/install.json`
outside skill discovery. The installer does not claim actual client discovery.

Updates use the same command. A complete staged inventory replaces owned paths,
removing retired files. Edited, missing, unowned or duplicate files cause a
non-destructive stop for review. Unrelated client configuration is preserved.
The previous runtime and recovery mapping remain under `.cloudflare/vine-install/transactions/`.
On synchronous failure the installer restores the old runtime and inventory.
SIGKILL/power-loss recovery needs manual review of `recovery.json` and backups.
Do not delete a transaction while recovery is unresolved.

Uninstall using the canonical installer or installed copy:

```sh
node /source/agents/skills/vine/scripts/install.mjs --root /consumer --remove true
```

Task evidence and unrelated configuration remain. V1 owns no hooks; an inventory
claiming owned hooks is refused until the owning adapter disables them. Duplicate
standalone/plugin copies are checked in project `.agents`, `.codex` and `.claude`
discovery trees. User/global and client-specific effective discovery still need
client inspection; filesystem checks alone cannot establish a single active
identity across every client layer.

Rollback: preserve task evidence, restore the previous reviewed runtime and its
inventory from the printed transaction, restore the corresponding approved
project policy, then validate compatibility and rerun required checks. Keep
existing application CI intact. No remote release/tag/publication is performed
by this installer.

Install, update, and remove share an exclusive per-consumer lock at
`.cloudflare/vine-install/lock`, acquired before reading ownership and held through
commit or rollback. Contenders fail without touching inventory. The lock records
PID and start time and is released in `finally`. After a crash, inspect
`lock/owner.json`, confirm no installer is running, and review the transaction's
`recovery.json` and destination/inventory state before manually removing the lock.
Locks are never automatically stolen based on age or PID alone.

`npx skills add` is unsupported for VINE because it bypasses the RUNTIME inventory, commit verification, locking, and transactional installation; use the canonical `node .../install.mjs --root` command in this document instead.
