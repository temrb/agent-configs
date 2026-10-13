# Evaluation and maintenance

Helper fixtures are public development mechanics checks. They are not an
independent behavioral evaluation. Run them with:

```sh
node --test agents/skills/vine/tests/*.test.mjs
```

Use the Node/Bun versions in [compatibility](compatibility.md). Historical
[research notes](research.md) explain the design hypothesis without establishing
the skill's effectiveness.

Freeze external evaluator ownership, inaccessible held-out storage, repository
revisions, client/model version, prompts/tools, budgets, rubric, sample design,
randomization and reset protocol before graded agent runs. A sibling workspace
or a second agent with the same filesystem does not provide hidden isolation.
Keep defect patches, graders and credentials out of both checkout and package.

Compare A (existing instructions) and B (skill) first; later C (mechanical gates)
and D (combined). Shared external instrumentation must be identical. Hooks and
reviewer stay disabled. Record explicit/implicit/mid-task activation and adjacent
negative controls separately. Reset each run's checkout, dependencies, local
DB/Worker state, evidence, processes, locks and ports. Use no remote mutations.

Report original-suite detection and marginal detection among original misses;
retained guarantees; valid red/setup; final correctness; accurate verification
claims; reuse/no-new-test decisions; owning boundary and scope; time/tokens,
command/CI cost, review effort, flakes, false positives and maintenance burden.
Exclude equivalent defects, invalid builds and environment failures from eligible
detection denominators, reporting exclusions. Blind reviewers when possible and
report sample counts and uncertainty. Small demonstrations establish feasibility.

Proposed promotion rule, to be frozen by maintainer/evaluator before grading:
+10 percentage points marginal detection, no critical guarantee loss, no increase
in false completion claims, median time/token overhead at most 25%. Alternative
correctness/claim improvements are scored separately where marginal coverage is
inapplicable. Insufficient sample size is inconclusive. Do not tune against the
final held-out set. Promotion, release, adapters and second-project adoption
remain pending until required evidence exists.

Review unknown failures, flakes, audit false positives, costs and compatibility
periodically. Retire low-value rules with maintainer review and reevaluate on
fresh held-out material after substantial changes. Preserve CI artifacts under
existing retention; concise acceptance conclusions belong in the project record.
