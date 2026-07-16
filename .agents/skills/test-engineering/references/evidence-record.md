# Test-engineering evidence record

Use only the sections needed by the selected intent mode. Keep this record in the task response or a user-requested artifact unless repository persistence was explicitly authorized. Replace blanks with observed evidence or `unknown`; never fill gaps by inference.

## Scope and task authority

| Requested or possible action | Authorizing source | Scope | Status or limit |
|---|---|---|---|
| Inspect files or state |  |  | authorized / not authorized / unknown |
| Run local commands or validators |  |  | authorized / unsafe / unavailable / unknown |
| Change tests or validators |  |  | authorized / not authorized / conditional |
| Change implementation or system artifacts |  |  | authorized / not authorized / conditional |
| Install, contact, deploy, destroy, or spend |  |  | authorized / not authorized / conditional |

- Intent mode: audit / diagnosis / characterization / behavior change or TDD / discovery / regression / refactor
- Evidence boundary: static / unit or component / integration or contract / system or E2E / nontraditional
- Relevant module, workspace, or system boundary:
- Working-state evidence and user changes to preserve:
- Commands or actions withheld for safety, scope, cost, or missing authority:

Task authority controls what the agent may do. It does not by itself define what the product should do.

## Behavioral authority and evidence sources

| ID | Source or path | Role | Owner or designation | Scope | Status |
|---|---|---|---|---|---|
|  |  | governing behavioral authority / candidate authority |  |  | current / stale / conflicting / absent |
|  |  | current-behavior or compatibility evidence |  |  | inspected / partial / unknown |
|  |  | audit evidence |  |  | read / missing / partial |
|  | command, revision, environment | execution evidence |  | exact observation only | passed / failed / inconclusive |

A user statement, report, hypothesis, or preference is governing behavior only when explicitly presented or designated as such within the source's authority. Record supersession and conflicts rather than choosing silently. Repository behavior, existing tests, and review do not grant behavioral authority by themselves.

For each material audit finding:

| Finding | Report evidence | Repository or execution evidence | Disposition | Next action |
|---|---|---|---|---|
|  | section or supplied text | file, line, or command | confirmed / contradicted / inconclusive / not assessed |  |

`Confirmed` requires repository or execution evidence, not repetition of the report. If the named report is missing, do not recreate findings from memory or implication.

## Contract, observation, and oracle map

| ID | Verification purpose | Governing rule, observed behavior, or hypothesis | Candidate evidence | Gating status or open decision |
|---|---|---|---|---|
|  | conformance | authoritative required / invariant / prohibited behavior |  | gating / unresolved |
|  | characterization | explicitly observed current behavior |  | non-normative / adopted |
|  | exploratory | hypothesis / candidate invariant / divergence |  | non-gating / confirmed and adopted |

For each candidate test or validator:

- Map ID and observable behavior:
- Evidence boundary and why it faithfully observes the behavior:
- Oracle, metric, threshold, or review criterion:
- Positive, negative, boundary, and prohibited cases that matter:
- Plausible subtly incorrect implementation rejected:
- Fixtures, mocks, datasets, sampling, environment, or statistical assumptions:
- Compatibility behavior explicitly designated for preservation:

Execution establishes mechanics and observed discrimination, not semantic correctness by itself. Do not count implementation-derived assertions, unreviewed snapshots, or post hoc thresholds as strong semantic evidence.

## Decisive-evidence provenance

| Evidence or oracle | Contract source or owner | Author or origin | Author saw implementation? | Semantic reviewer | Challenge source | Result and limit |
|---|---|---|---|---|---|---|
|  |  |  | yes / no / unknown |  |  |  |

- Decisive acceptance source or challenge outside the sole implementation loop:
- Why it is independent enough for the actual risk:
- Acceptance status: validated / implementation-green, validation-provisional / inconclusive
- Material human review or risk acceptance still required:

Validated completion requires at least one decisive acceptance source or challenge that was not both authored and adjudicated solely inside the implementation loop. If none is available or proportionate, use a provisional or inconclusive status.

## Meaningful red and diagnosis record

- Independently identifiable unchanged baseline:
- Exact focused command, selector, and relevant environment:
- Command definition, hooks, and prerequisites inspected:
- Observed failure:
- Intended contract gap demonstrated:
- Incidental harness, fixture, data, dependency, permission, timing, and environment checks:
- If compile/import/linkage/missing-symbol red: why it directly and uniquely expresses the authorized gap:
- Concrete contract-conforming behavior that can pass:
- Failure class: implementation / test or oracle / specification / fixture or data / environment or harness / downstream / inconclusive
- Supporting evidence, alternatives, and next discriminating check:

If current behavior conforms, label the evidence characterization or regression protection; do not fabricate a red phase.

### Intermittent or statistical evidence

- Predeclared repetition count, sample, threshold, and uncertainty method:
- Observed count, distribution, failure rate, or confidence interval:
- Isolated versus suite, staged, or production-like result:
- Ordering, seed, time, timezone, locale, parallelism, process, and shared-state evidence:
- Product nondeterminism versus test or measurement nondeterminism:
- Proposed retry, timeout, quarantine, threshold change, or excluded sample and detection power lost, if authorized:

## Proactive discovery record

| Observation | Reproduction or invariant evidence | Behavioral-authority status | Label | Confirmation needed |
|---|---|---|---|---|
|  |  | governing / absent / ambiguous | candidate anomaly / suspicious divergence / observed invariant violation / confirmed defect |  |

Do not promote an anomaly to a confirmed defect without applicable behavioral authority.

## Change and verification record

- Authorized semantic scope:
- Minimum coherent change and why it generalizes:
- Test or validator semantic changes and independent justification, if any:
- Behavior explicitly designated for compatibility:
- Out-of-scope behavior preserved:
- Focused evidence: exact command and result
- Impacted regressions: exact command and result
- Broader or external gate: exact command and result
- Static, build, policy, data-quality, or structural checks: exact command and result
- Independent challenge: provenance, command or method, result, and implementation exposure
- Unrun, unsafe, unauthorized, unavailable, or disproportionate checks:
- Residual risk and acceptance status:

Use `passed`, `failed`, `not run`, `blocked`, `inconclusive`, `implementation-green`, `validation-provisional`, or `validated`. A partial run is not a full-suite result, and green checks are not proof of total correctness.

## Refactor proposal and baseline gate

- Known functional and regression baseline:
- Pre-existing failures or unavailable suites:
- Affected-scope checks and why they are sufficient for the bounded claim:
- Design objective and non-goals:
- Intended structure:
- Affected interfaces, callers, and compatibility constraints:
- Atomic steps and regression check after each:
- Structural completion checks:
- No-new-attributable-regression evidence:
- Rollback or reversibility:
- Human approval boundary:

Keep functional changes out of this phase. Search after each step for missed callers, stale references, obsolete definitions, compatibility shims, dead imports, and incomplete migrations. Never describe baseline parity or a partial run as global green.
