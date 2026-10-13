# Compatibility evidence

Deterministic CI runs the complete repository check on Python 3.11. These checks do
not establish client runtime compatibility or model behavior.

Architecture-audit remediation checks on 2026-10-11 used Python 3.14.4:
all 60 root tests (including the delegated Prefine fixture suite), documentation
links, asset validation, synchronization and generated-content checking passed.
VINE's 36 lifecycle tests passed on Node 24.19.0 and Bun 1.4.2 with child-process
execution enabled; the ordinary sandbox denied those subprocesses. VINE skill
metadata validation and `git diff --check` also passed. Python 3.11 was unavailable
locally; its result awaits the CI matrix. See the [architecture audit](architecture-audit.md)
for findings, priorities and the distinction between these checks and runtime
or behavioral evidence.

## Client smoke runs

No client sessions were launched for the audit remediation. No tested client
version or successful behavioral run is claimed. Run the installation and smoke
procedures in each client README before relying on a new client release.

Record each run here with date, client name and exact version, operating system,
repository commit, installed scope, discovery result, smoke prompt, outcome, and
any limitations. Keep account identifiers, tokens, and private traces out of Git.

### Skills CLI verification (pending publication)

No Skills CLI compatibility testing has succeeded yet; status remains unverified. The source is unpublished, so the following post-publication checks have not been run:

1. Run `--list` against the scoped `agents/skills` source; confirm discovery of only `prefine` and `vine`.
2. Perform a negative test using the bare repository source; record the duplicate-discovery behavior or failure to confirm why scoping is required.
3. Verify project-local Prefine installation, client discovery, and a smoke test using `Write a greeting`. Confirm Prefine returns a refined prompt without executing the greeting task.
4. Verify global Codex installation with `-g -a codex`, followed by list, update, and remove operations.

For each completed verification run, record test date, client and CLI versions, operating system, repository commit, source scope, discovery results, and test outcome.

## Prefine behavioral runs

No live model evaluation was performed for this remediation. Use the bundled
evaluation guide and case matrix. Record date, host/version, model identifier,
repository commit, case IDs, controlled retrieval setup, observed pass/fail
results, and sanitized trace evidence separately from deterministic CI results.
