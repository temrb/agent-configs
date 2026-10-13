# Architecture audit after VINE

Audit date: 2026-10-11. Baseline: `37759d0`. Scope: maintained assets,
generated packages, build/validation code, documentation, tests, and committed
CI. Local client installations and external branch-protection settings are
outside this evidence. Recommendations below distinguish demonstrated defects
from optional simplifications.

## Fit and distribution

VINE fits the [repository purpose](../README.md): reusable agent assets and
their distribution tooling. Its [entrypoint](../agents/skills/vine/SKILL.md)
is a short instruction workflow with conditional references. Its scripts,
schemas, tests and development docs are colocated under the canonical skill,
as [AGENTS.md](../AGENTS.md) requires. A skill may have executable resources;
size alone is not a reason to remove it.

The distribution paths have different owners:

| Asset | Canonical input | Distribution and ownership |
| --- | --- | --- |
| Prefine skill/plugin | `agents/skills/prefine/`, plugin metadata and recipe | [Recipe](../agents/plugins/prefine/build.json) copies `SKILL.md` and renders the Codex manifest. [Inventory](../agents/plugins/prefine/.generated.json) owns exactly those output roots. |
| VINE standalone skill | `agents/skills/vine/` | [Installer](../agents/skills/vine/scripts/install.mjs) copies 14 explicit runtime files into a consumer's `.agents/skills/vine/`; `.vine/install.json` records ownership, commit, bytes and modes. Docs/tests/research stay in source. |
| Native client configs | `agents/configs/<platform>/` | Platform validators check native syntax and bounded path/runtime rules; installation remains an explicit client-owned copy/merge. |

[repo-build.json](../repo-build.json) registers only the plugin collection.
There is no VINE plugin, generated VINE bundle, repository `.vine/project.json`,
hook registration, or VINE completion gate. The root Python engine neither
imports VINE code nor requires Node/Bun. Its VINE-related CI job tests an asset,
not the correctness of every repository task.

Two ownership implementations are justified here. Repository synchronization
owns committed recipe outputs, while VINE installation owns files in another
project and preserves local edits, evidence and rollback state. Replacing both
with one installer would couple unrelated lifecycles and runtime dependencies.
The existing pure renderer / shared synchronization split is useful: safety,
adoption, retirement and rollback are centralized and have failure-path tests.

VINE's complexity is concentrated in optional executable evidence capture, not
its instruction entrypoint. The baseline has 1,642 helper-script lines, 768 schema
lines and 944 lifecycle-test lines. These implement process/report identity,
final-input freshness, filtering, red/green association, artifact sealing and
installation ownership. They impose real review and compatibility costs. The
36 public lifecycle tests establish mechanics, not improved agent effectiveness.
The [evaluation guide](../agents/skills/vine/docs/evaluation.md) correctly leaves
held-out effectiveness and fresh client discovery unverified.

The helper profile is application-specific: `run-check.mjs` invokes Bun scripts,
uses `FOUNDATION_EVIDENCE_DIR`, and understands Cloudflare release paths;
`reports.mjs` includes fixed Foundation removal identities. These are concrete
portability limits, already acknowledged in its compatibility record, rather
than proof that the instruction workflow is irrelevant. The entrypoint now
explicitly makes helpers optional and identifies this profile.

## CI count, requirements and overlap (historical baseline)

The topology below describes the audit baseline, not the current workflow. The
current [workflow](../.github/workflows/validate.yml) has one `check` job using
Python 3.11, Node 24.19.0 and Bun 1.4.2. It runs `scripts/check.py`, which executes
documentation links, Python tests, asset validation, generated drift and discovered
skill JavaScript suites. Pushes to `main` and pull requests trigger it; direct
`dev` pushes do not. Branch policy was not changed by the VINE audit.

At the historical baseline, the workflow defined two jobs:
`check` on Python **3.11 and 3.14**, and `vine` on Node **24.19.0** with Bun
**1.4.2**, all on `ubuntu-latest`, for pushes and pull requests. Node/Bun setup
actions are commit-pinned; checkout and Python setup use major-version tags.

There are **five distinct check commands, nine command executions and three job
runs**, not six independent CI checks. The `check` job has six *steps*:

| Step in `check` | Actual requirement | Overlap / VINE specificity |
| --- | --- | --- |
| `actions/checkout@v4` | Supplies the checkout being checked. | Setup, not a validation check; applies to all assets. |
| `actions/setup-python@v5` | Selects each declared supported Python version. | Setup, not a validation check; VINE helpers do not use Python. |
| `scripts/check_docs.py` | Existing local Markdown paths and heading anchors throughout README, docs and agent trees. | Asset validation also checks skill links and now plugin package links, but does not replace repository-wide documentation discovery. |
| `unittest discover -s tests` | Tests tooling behavior, including rejected inputs, ownership, rollback, portability and config rules; now also dispatches skill-owned Python suites. | Uses synthetic failures that a valid real checkout cannot exercise. Mostly predates VINE; no Node/Bun dependency. |
| `scripts/repo.py validate` | Checks actual canonical skills, plugins, bundled skills/manifests and native configs against supported contracts. | Tests validate the validators; this command validates the current assets. Shares manifest checks with rendering and link checks with documentation. |
| `scripts/repo.py sync --check` | Re-renders recipes, checks inventories, ownership and exact output bytes/types/modes without writing. | A valid but stale generated instruction/manifest can pass asset validation and fail here. Does not validate every canonical config or skill. |

The separate `vine` job has checkout, Node setup, Bun setup and one test command:
`node --test agents/skills/vine/tests/*.test.mjs`. It protects the shipped helper
lifecycle using isolated temporary consumers, including installed execution,
stale/filtered/malformed evidence, signals, immutable installation and competing
installers. Python asset validation checks its `SKILL.md` contract and links;
neither Python validation nor build drift tests these executable behaviors.

History confirms the four Python commands and matrix existed at `4850ea1`,
before VINE's addition at `cfd2f28`. VINE added one runtime job. None of the
five commands is an irrelevant duplicate. Repeating links/drift on two Python
versions has small potential redundancy, but retaining one straightforward
matrix is proportionate at this size. No branch rules or remote run history
were inspected, so the number of externally required status checks is unknown.

## Confirmed problems and implemented fixes

1. **High: package validation accepted checkout-only links.** Shared validation
   bounded bundled skill links to the repository; README/nested plugin links
   were checked only by the repository-wide checker. A plugin could pass both
   while depending on canonical files absent from the distributed package.
   [Validation](../scripts/validation.py) now bounds bundled skills and all plugin
   Markdown to the package. Regression cases first failed for README, bundled
   `SKILL.md`, and nested docs, then passed after the fix. Tradeoff: intentional
   references outside a package must use external URLs or include the resource.

2. **High: local installations polluted generated ownership discovery.**
   `prepare()` recursively found `.generated.json` beneath ignored root
   `.codex/`, contradicting the explicit maintained/installed boundary.
   [Inventory discovery](../scripts/repo.py) now prunes that local tree while
   still rejecting forgotten inventories elsewhere. The regression demonstrated
   rejection before the fix and preservation after it. Canonical nested Codex
   configuration remains in validation scope.

3. **Medium: shared validation owned Prefine-specific evaluator data.**
   `skill()` constructed `tests/fixtures/prefine-behavior.json` for every skill.
   Its schema helper and feature-specific assertions now live in
   [Prefine's suite](../agents/skills/prefine/tests/test_behavior.py), preserving
   positive/negative coverage. A small [shared dispatcher](../tests/test_skills.py)
   runs canonical Python skill suites in separate processes through the existing
   root test command. Tradeoff: `validate` checks portable asset contracts;
   evaluator data checks require the test command, which CI already runs.

4. **Medium: documentation ownership and scope drift.** Root `docs/research.md`
   held VINE-specific historical research despite the colocation policy. It is
   now [skill-owned research](../agents/skills/vine/docs/research.md), linked from
   evaluation and labeled as historical material rather than verified evidence.
   VINE's compatibility record no longer describes its committed addition as
   uncommitted. Contributor/build guides now include the lifecycle command,
   dependency boundary and actual CI count. The CI comment now acknowledges
   separate runtime suites; commands, versions, matrix and job IDs are preserved.

## Proportionate follow-up opportunities

1. **Before claiming broader support:** use an actual second consumer to define
   a new adapter and compatibility tests. Generalizing artifact layouts,
   removal identities, package runners and exact runtime pins now would add
   abstractions without a demonstrated consumer. Keeping the limited profile
   costs portability but avoids a speculative orchestration framework.
2. **Before promoting effectiveness:** complete the documented independent
   evaluation and client smoke runs. The current evidence supports shipping an
   experimental optional workflow, not a universal acceptance mechanism.
3. **Optional later cleanup:** split the large VINE test file by lifecycle area,
   deduplicate runtime pins behind one skill-owned compatibility source, or
   reduce repeated Python-matrix work if measured maintenance/CI cost warrants
   it. None fixes an observed correctness failure today. Do not introduce a
   registry, dependency graph or shared installation framework just for two
   skills and one generated plugin.

No plugin's shipped files changed: Prefine's recipe consumers were reviewed,
and synchronization leaves its bundle, manifest and inventory identical.
Consequently no plugin version bump is needed. VINE remains a standalone skill
whose next committed revision identifies its changed instructions.

## Validation and limits

Baseline: 58 Python tests and 36 VINE tests passed; asset validation,
documentation links and generated drift passed. The ordinary sandbox denied
Node/Bun child execution; the unmodified VINE suite passed with that permission
enabled. Two new boundary regressions failed against the original code.

Final results are recorded in [compatibility evidence](compatibility.md).
Python 3.11 is unavailable locally, so that matrix leg remains for CI. No client
session, protected-merge configuration, real Foundation consumer, or held-out
model evaluation was exercised. Historical research claims were not reverified.
