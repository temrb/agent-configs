---
name: test-engineering
description: >-
  Create, improve, audit, diagnose, and validate software tests and other
  verification evidence across any language, runtime, framework, test level, or
  domain, including conventional software and AI/ML systems. Use for unit,
  component, integration, contract, system, or E2E testing; characterization,
  TDD, flaky tests, test-related CI, proactive discovery, regression and refactor
  validation; and performance, security, concurrency, data-quality, statistical,
  ML, or human evaluation. Do not use merely for non-test lint, build, packaging,
  deployment, or infrastructure failures.
---

# Test engineering

Use tests and other validators as executable evidence about behavior established independently of the implementation loop. AI-generated tests, diagnoses, expected values, and challenge cases are proposals, not self-certifying specifications. Passing checks never prove total correctness, security, compatibility, performance, or product intent.

Do not let one implementation loop define expected behavior, author the decisive checks, implement the change, and judge success without an independent acceptance source or challenge. Independence is about evidence provenance, not mechanically requiring a second agent for every task.

## Load only relevant context

- Read applicable repository instructions, then inspect focused implementation, tests or validators, fixtures, callers, dependency and version sources, configuration, CI, and architecture or impact information. Do not ingest the repository indiscriminately.
- Read an attached or pasted audit before using its findings. When the user names an exact report or path, locate that report if a focused lookup can do so; never substitute a related report or infer missing findings. If it remains unavailable, say so and continue only with available evidence.
- Read [references/evidence-record.md](references/evidence-record.md) only when a durable authority map, provenance record, audit disposition, red/green record, diagnosis, discovery record, or refactor proposal will materially help. Use only the relevant sections.

Keep process evidence in the task record or a user-requested report by default. Do not add repository bookkeeping files merely to record this workflow.

## Separate authority, behavior, and evidence

Maintain two distinct authority records:

1. **Task authority** controls what may be inspected, executed, changed, installed, contacted, deployed, or otherwise affected. The current user controls agent scope within their authority.
2. **Behavioral authority** establishes what the system is supposed to do. Use requirements or artifacts explicitly presented or designated as governing by an authorized product, domain, or standards owner, within their stated scope.

A user statement, report, bug label, hypothesis, or preference becomes governing behavior only when it is explicitly presented or designated as such within the speaker's authority. Human authorship, review, repository presence, or confident wording alone does not grant behavioral authority. Record explicit supersession; otherwise report conflicts and identify dependent assertions or mutations instead of silently choosing.

Treat repository code, tests, schemas, documentation, callers, and conventions as current-behavior and compatibility evidence, not unquestionable intent. Treat a supplied audit as scoped audit evidence and confirm material findings against repository or execution evidence before calling them confirmed. Treat tool output as evidence only for the command, environment, revision, and scope observed.

Classify candidate verification by purpose:

- **Conformance test or validator** — maps its oracle to a governing behavioral contract item.
- **Characterization test** — maps to explicitly observed current behavior and remains non-normative unless an authority adopts it.
- **Exploratory probe** — maps to a hypothesis, candidate invariant, anomaly, or divergence and remains non-gating unless confirmed and adopted.

Require both observed behavior and applicable behavioral authority for semantic conformance, confirmed-defect, and semantic-success claims. Use evidence appropriate to the claim for test-quality findings, measurements, collection failures, and candidate anomalies; do not invent a product contract for them.

For decisive checks, record provenance when material: contract source or owner, oracle author or origin, whether the author saw the implementation, semantic reviewer, challenge source, and acceptance status. Never invent repository facts, frameworks, commands, dependencies, versions, findings, executions, or results. Label missing, stale, contradictory, or inconclusive evidence and narrow claims accordingly.

## Select intent and evidence boundary

State the authorized scope and select one or more **intent modes**:

- **Audit or review** — assess coverage, oracle strength, maintainability, and risk. No red phase or edit is required.
- **Failure diagnosis** — reproduce and classify a deterministic or intermittent failure. Stop after a supported diagnosis unless changes were also authorized.
- **Characterization** — capture important observed behavior for protection or migration without silently making it intended behavior.
- **Behavior change or TDD** — use contract → meaningful red → diagnosis → coherent change → regression gate for an authorized fix or feature.
- **Proactive discovery** — search for anomalies or invariant violations. Use candidate labels until authoritative intent supports a defect claim.
- **Regression validation** — test whether an authorized change preserved applicable behavior and gates without assuming a new red phase.
- **Refactor validation** — freeze authorized behavior, validate structural progress separately, and keep new functional behavior out of the refactor.

Separately select the **evidence boundary** that can observe the behavior: static analysis; unit or component; integration or contract; system or E2E; or a nontraditional validator. Integration and E2E are boundaries, not intent modes. Use the lowest-cost boundary that faithfully observes the contract, and add a boundary-crossing check when isolation or mocks would bypass decisive behavior.

Do not force conventional unit-test-first TDD when the primary oracle is statistical, nondeterministic, data-quality, subjective UX, security, concurrency, or performance evidence. Apply the same independence rules through representative datasets, predeclared thresholds, uncertainty analysis, model or formal checking, load tests, security analysis, staged validation, telemetry, or human evaluation as appropriate.

Determine whether analysis, test changes, implementation, refactoring, or a combination is authorized. Do not turn analysis into code changes. Do not install dependencies, add a framework, regenerate broad artifacts, contact external services, deploy, or take destructive, costly, or materially broader action without authority.

Calibrate autonomy by specification clarity, oracle strength, regression coverage, blast radius, security or data risk, reversibility, and architectural scope. Require direct human judgment for materially unresolved intent or oracle questions, material untested behavior, high-impact semantic or architectural decisions, and risk acceptance. Authentication, authorization, money, destructive operations, sensitive data, concurrency, distributed protocols, difficult migrations, public APIs, and architectural refactors normally need explicit review.

## 1. Inspect the test system safely

Establish with file or command evidence, recording `absent` or `unknown` rather than forcing a conventional answer:

- relevant modules and workspaces; languages; runtimes and toolchains; build or package systems; version sources; available dependencies; generated-code steps; test or validation mechanisms; discovery rules; and standard commands;
- nearby assertions, fixtures, factories, mocks, snapshots, helpers, datasets, thresholds, and naming conventions;
- system-under-test artifacts, public interfaces, callers, dependencies, side effects, error paths, gates, and architectural constraints;
- version-control or other working-state evidence where present, including user changes to preserve.

Inspect a discovered command's definition and relevant hooks before running it. Test scripts may invoke migrations, services, networks, containers, deployment, or destructive cleanup. Confirm prerequisites and request authority before unsafe or externally mutating execution.

Preserve user changes. Record status, focused diffs, or affected-file hashes when useful; never reset or overwrite unrelated work to manufacture a clean baseline. Record what was inspected and what remains unknown.

## 2. Establish the contract and oracle

Before writing an affected conformance assertion, record the applicable required behavior, examples, invariants, prohibited behavior, compatibility, errors, retries, partial failure, side effects, ordering, idempotency, persistence, security, privacy, performance, exclusions, and open decisions.

Map conformance checks to contract items, characterization checks to observed behavior, and exploratory probes to hypotheses or candidate invariants. An ambiguity is material when plausible interpretations change an assertion, observable behavior, compatibility, risk, or architecture. Resolve material ambiguity through an authorized source before encoding a gating conformance oracle. If no decision is available, document alternatives, leave only the dependent assertion or mutation unwritten, and continue safe evidence-bounded work.

Preserve important decisions in executable checks, machine-checkable constraints, persistent specifications, or explicit review criteria. Conversation memory is not regression protection.

## 3. Plan diagnosable, discriminating evidence

For each authorized behavioral increment, use:

`contract rule → meaningful red condition → diagnosis → coherent behavior change → regression gate`

State the expected observable failure and a proportionate, safe, authorized verification ladder before editing. Keep unrelated features, fixes, migrations, and refactors in separate loops.

Require an oracle that rejects at least one plausible subtly incorrect implementation. Cover the relevant positive, negative, prohibited, boundary, empty, malformed, transition, error, side-effect, invariant, compatibility, security, concurrency, and performance cases. Avoid tautologies, implementation-derived expected values, mocks that bypass the behavior, fixture-only checks, overspecified internals, and large snapshots without reviewed semantic meaning. More checks do not imply stronger verification.

## 4. Establish meaningful red evidence and diagnose

For an authorized behavior change or TDD loop, run each new-behavior or bug-reproduction check against an independently identifiable unchanged baseline before editing implementation artifacts, when the command is available, safe, authorized, and scoped. Capture:

1. the exact focused command and selector, relevant environment, and baseline revision, preserved copy, or file hashes;
2. the observed failure and why it expresses the intended contract gap;
3. evidence distinguishing that failure from incidental harness, fixture, dependency, permission, timing, or environment failure;
4. why a contract-conforming implementation can satisfy the oracle.

A compilation, import, linkage, missing-symbol, absent-endpoint, type, or generated-interface failure is meaningful red when it directly and uniquely expresses the authorized contract gap. Unrelated configuration, collection, or dependency failures are not. When a trusted reference is available, safe, authorized, and scoped, run it; otherwise record it as not run and state concrete valid behavior that would pass. If current behavior already conforms, label the new check as characterization or regression protection rather than fabricating red evidence.

Classify each failure before editing:

- **implementation** — observed behavior violates the governing contract;
- **test or oracle** — assertion, metric, threshold, or setup does not represent the contract;
- **specification** — intent is absent, ambiguous, or contradictory;
- **fixture or data** — test data, mocks, factories, datasets, or state are invalid;
- **environment or harness** — dependencies, services, versions, permissions, timing, collection, or configuration prevent a valid run;
- **downstream** — another defect or earlier failure causes the visible symptom;
- **inconclusive** — available evidence cannot distinguish the cause.

State the hypothesis, supporting evidence, alternatives, and next discriminating check. A red check alone does not authorize an implementation edit.

For intermittent failures, reproduce repeatedly and in isolation when safe, then vary or record ordering, seed, time, timezone, locale, parallelism, process boundaries, and shared state as relevant. Predeclare a repetition or evidence threshold where practical. Distinguish product nondeterminism from test nondeterminism. Do not add sleeps, retries, widened timeouts, or quarantine merely to obtain green; document the detection power lost and obtain authority for any such tradeoff.

## 5. Make only the authorized coherent change

Make the smallest change that satisfies the contract and its invariant across equivalent inputs, not the smallest textual patch that satisfies visible examples. Check affected callers and adjacent behavior, avoid input special-casing, and explain why the change generalizes.

Do not weaken, delete, skip, loosen, or rewrite checks solely to make an implementation pass. Change a check's semantics only when independent behavioral authority justifies it, and record that justification. Preserve behavior explicitly designated for compatibility and behavior outside the authorized semantic scope. Treat other observed behavior as evidence to assess, not an automatic contract.

## 6. Run proportionate verification and an independent challenge

When available, safe, authorized, and scoped, use the strongest applicable sequence:

1. new focused evidence;
2. impacted existing checks;
3. broader regression suite or external gate;
4. applicable types, lint, static analysis, build, data-quality, or policy checks;
5. an independent challenge selected for the actual risk.

Possible challenges include implementation-blind pre-existing acceptance tests, independently calculated expected values, held-out inputs, mutation testing, properties, fuzzing, metamorphic relations, model or formal checks, security probes, representative performance trials, schema or migration checks, structural searches, separate-context review, staged validation, and human evaluation. Use differential testing only when the reference behavior is independently designated for preservation; a previous implementation may contain the defect under repair.

Before claiming **validated completion**, identify at least one decisive acceptance source or challenge that was not both authored and adjudicated solely inside the implementation loop. Record its provenance, implementation exposure, result, and limits. If none is available or proportionate, report **implementation-green, validation-provisional** or **inconclusive** rather than self-certifying the change. Do not run challenge techniques mechanically; report what was applicable, run, unavailable, unsafe, unauthorized, or disproportionate and state residual risk.

## 7. Refactor separately

Establish a known functional and regression baseline before refactoring. Prefer global green, but do not erase legacy reality: record pre-existing failures and unavailable suites, require no new attributable regression, and never call a partial run global green. Baseline parity plus strong affected-scope evidence may support a bounded result when omissions are explicit.

Propose the design objective, non-goals, intended structure, affected interfaces and callers, compatibility plan, atomic steps, checks after each step, structural completion criteria, and rollback. Obtain review for broad or architectural scope. Freeze behavioral expectations, apply one structural step at a time, and rerun regression and structural checks. Search for missed callers, stale references, obsolete definitions, temporary compatibility layers, dead imports, and incomplete migrations.

## Report proportionately

Use only the sections the selected mode needs:

1. **Scope and authority** — intent mode, evidence boundary, task authority, repository state, behavioral authority, and audit status.
2. **Contract and decisions** — requirements, observations or hypotheses, invariants, prohibited behavior, and unresolved ambiguity.
3. **Evidence and diagnosis** — inspected context, provenance, baseline, exact commands, outcomes, and classification.
4. **Change** — files, semantic scope, approvals, and why it generalizes.
5. **Verification and limits** — exact checks, independent challenge, omissions, acceptance status, residual risk, and decisions still needed.

Distinguish `passed`, `failed`, `not run`, `blocked`, `inconclusive`, `implementation-green`, `validation-provisional`, and `validated`. Never present a partial run as full-suite success or passing checks as proof of total correctness.

## Complete or pause precisely

Complete audits, diagnoses, characterization, discovery, and bounded regression reports when the authorized evidence-bounded work is done, even if some dispositions are `inconclusive`.

For behavior changes, complete implementation work only when affected intent is clear, oracles discriminate, meaningful baseline evidence failed for the intended reason, diagnosis preceded implementation, the change is coherent, and relevant gates ran or omissions are explicit. Claim validated completion only when the independent-source-or-challenge gate is satisfied. Otherwise use the provisional or inconclusive acceptance status while still reporting completed implementation work accurately.

Pause only assertions and mutations whose correctness depends on unresolved ambiguity, conflicting authority, unavailable decisive evidence, unacceptable risk, or an external, destructive, costly, or broader action. Request the specific decision or authority needed while still reporting all safe conclusions already established.
