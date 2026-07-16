# Evaluation protocol

These evaluations measure whether the skill improves test-engineering behavior across stacks and evidence types. They are not part of the execution agent's context.

## Isolation and staging

The answer key, verifier policy, trigger set, prior outputs, configuration labels, and grading must not be visible to the execution agent. Do not run an agent from this directory or give it the installed package path.

For every configuration and repetition:

1. Create a fresh destination outside the skill package, source fixture, and evaluation tree.
2. Run `prepare_case.py` from a controller process. Use the default for the current skill, `--skill-source` for a preserved prior version, or `--without-skill` for a true no-skill baseline.
3. Mount or expose only the staged `input/`, optional `skill/`, `task.json`, an empty `output/`, an isolated temporary directory, and the minimum pinned toolchain required by the fixture.
4. Make the staged `input/` read-only. Give the agent write access only to `output/` and isolated temporary storage.
5. Disable network access and external credentials unless a case explicitly requires them. No current case does.
6. Do not mount this package, the original fixture, another skill version, baseline output, or controller home into the agent sandbox.
7. Save transcripts, timing, outputs, and grades outside the agent-visible workspace. Archive or remove the isolated run before reusing its path.

`prepare_case.py` rejects overlapping destinations and symlinks so staging cannot recurse into the package or dereference a fixture path outside the evaluation tree. Filesystem staging is not a sandbox by itself; the controller must enforce the mounts and network policy above.

The execution contract is always `output/worktree` plus `output/report.md`. The preparation script intentionally omits expected outputs, expectations, splits, dimensions, verifier policies, and configuration labels from `task.json`.

## Configurations, splits, and repetitions

Use these configurations where meaningful:

- **current skill** — the package being evaluated;
- **prior version** — a preserved pre-change snapshot for regression comparison;
- **without skill** — the same task with no skill directory or skill instructions.

Use development cases for iteration and reserve held-out cases for acceptance decisions. Do not revise the skill using held-out transcripts and then continue calling those cases held out; rotate them into development and add replacements.

Normally run at least three paired repetitions per case and configuration when affordable. Use the same model, tools, sandbox image, fixture bytes, resource limits, and starting state within a pair. Randomize or counterbalance configuration order. Record model identifier, tool versions, operating system or image digest, locale, timezone, environment variables that affect behavior, start time, duration, token usage, and controller revision.

For intermittent or statistical cases, predeclare the sample or repetition count and the success threshold in controller-visible grading policy. Do not accept a convenient random outcome as decisive evidence. The replica case requires at least 20 focused observations and both allowed selections before its local nondeterminism claim can pass.

Report per-expectation results, paired deltas, mean, standard deviation, range, and failures by configuration. A single run is a smoke check, not evidence of skill lift.

## Grading

1. Run `verify_case.py` from the controller for deterministic filesystem and mutation-scope checks. It never establishes semantic correctness.
2. Run any fixture command only inside the sandbox, only after inspecting its definition and prerequisites, and only when the command is allowlisted by the controller. Record unavailable prerequisites as environment outcomes rather than agent failures.
3. Grade process claims from the transcript and command log, not from `report.md` alone. A report that merely says a red phase, review, or challenge happened does not pass without evidence.
4. Grade each natural-language expectation atomically. Do not give partial credit inside a binary expectation. Use `inconclusive` in the evidence field when the artifact cannot decide it, then route material semantic questions to human review.
5. Blind graders and human reviewers to configuration labels. Randomize output order and reveal labels only after individual grades are locked.
6. Calibrate the grader against at least one known-good output and subtly wrong outputs, including a persuasive report with an invalid oracle, a visible-example overfit, an implementation edit before diagnosis, and an unsupported global-green claim.

Keep programmatic results, semantic grades, human review, and acceptance status separate. Programmatic file checks cannot validate product intent; an LLM grader cannot replace deterministic checks; a human reviewer does not retroactively create product authority.

## Trigger evaluation

`trigger-evals.json` is a separate realistic should-trigger/should-not-trigger set. Run each query at least three times against the published metadata, keep a held-out portion, and report false-positive and false-negative rates. Close negative examples matter more than obviously unrelated prompts. Trigger tests do not execute the behavioral fixtures.

## Environment and dependencies

The controller owns a pinned evaluation image or equivalent reproducible toolchain. Fixture manifests declare their local runner requirements where applicable. Preflight every case before comparison; if a required runtime or dependency is absent, skip the pair or mark both sides as environment-blocked. The execution agent must not install dependencies.

Do not compare configurations that received different dependency caches, services, permissions, or network access. Never interpret a missing runner as a test-engineering failure.

## Results and acceptance

Store all run artifacts outside this skill directory. A candidate revision is acceptable only when:

- required development cases show no material regression;
- held-out and trigger results meet predeclared thresholds;
- observed lift is not explained by prompt leakage, environment differences, or a broken grader;
- variance and cost are reported rather than hidden;
- at least one reviewer examines qualitative transcripts for correlated-oracle failures.

If those conditions have not been measured, describe the package as structurally validated but behaviorally unbenchmarked.
