# VINE research notes

Historical design research retained with its owning skill. These notes predate
implementation and are not release, compatibility, or effectiveness evidence.
External claims and source labels below have not been reverified by repository
checks. See [evaluation](evaluation.md) for the maintained evaluation procedure.

Second research pass: strengthening the evidence on AI coding-agent testing failures
October 11, 2026 • Independent follow-up to Pass 1 • Focus: additional empirical evidence, source verification, causal confidence, and implications for a future testing skill

1. Executive summary: what changes after Pass 1
   The first report's central conclusion remains defensible: the most consequential testing failures occur when agents confuse tests that pass with tests that establish the intended behavior.
   The second pass adds three findings that materially sharpen that conclusion.
   First, repository-level test writing is demonstrably difficult for contemporary autonomous agents. SWE Atlas – Test Writing evaluates agents that must explore a real repository, locate the appropriate test suite, write tests, and execute them. Its evaluation distinguishes meaningful behavioral coverage from simply producing executable test files. The benchmark's analysis identifies missing required scenarios as its leading failure category and also observes misplaced tests and failure to reuse established test helpers.

Test Writing

Second, even when generated tests execute successfully, they may fail to distinguish correct implementations from defective ones. SWE-Mutation, a peer-reviewed July 2026 study, evaluated generated tests against 2,636 mutated implementations drawn from 800 software-engineering instances. Its results provide independent support for the concern that test validity and defect-detection strength are more important than test counts.

ACL Anthology

Third—and especially important for your eventual SKILL.md—more repository instructions do not necessarily improve outcomes. A controlled 2026 study of AGENTS.md-style context files found no general improvement in task success despite increased agent exploration, testing activity, and inference costs above 20%. This challenges a central assumption behind the proposed solution: that supplying more explicit testing instructions will automatically improve software quality.

SRI Lab

The result is a more precise design hypothesis:
A dedicated testing skill is worth investigating when it changes specific, measurable agent decisions. Its value should be established by improved bug detection, preservation of existing behavioral coverage, appropriate test execution, and accurate verification reporting—not by how many procedures it contains or how many tests the agent writes.

1. Additional documented cases and empirical findings
   Case L. Autonomous test-writing agents omit required behaviors even when the environment is prepared
   Primary source: Scale AI, SWE Atlas – Test Writing • Agent benchmark • High confidence for benchmark observations
   SWE Atlas – Test Writing methodology and resultsThis benchmark is especially relevant because it isolates the testing task rather than evaluating agents only as bug-fix implementers.
   It contains 90 test-writing tasks from 11 production repositories spanning Go, Python, C, and TypeScript. Agents receive a repository, a behavioral request, and access to tools. They must investigate the implementation, add tests, and submit a patch.
   The evaluation combines a manifest check, a mutation test, and human-authored behavioral rubrics evaluated with an LLM judge.
   Three failure patterns emerged:

- Agents omitted tests for required scenarios. This was the largest failure category in the benchmark's analysis.
- Some tests failed the mutation check because they did not meaningfully exercise the requested behavior.
- Some agents placed tests in new files or incorrect directories rather than extending existing suites and reusing established fixtures.
  For the last pattern, the report gives concrete examples: creating a function-specific test file when related tests already exist, or placing a test in a dashboard test directory when the behavior belongs to a handler module.

Test Writing

Root-cause assessment: The first two failures demonstrate incomplete behavioral coverage or relevance. The third demonstrates repository-convention mismatch. The benchmark does not isolate whether these are caused primarily by insufficient exploration, weak test-planning ability, or limited context.
Mitigation: Discover existing test ownership and enumerate distinct required scenarios before writing tests.
Limitation: The benchmark partly depends on human-authored rubrics and LLM judging, so its success metric is not a pure, independent measurement of defect detection. It is nevertheless stronger than counting tests or checking whether they compile.
An additional caution: the page's introductory performance summary and its updated live leaderboard are not fully synchronized. I would use its published methodology and qualitative failure analysis rather than treat a particular displayed leaderboard score as a stable scientific result.
Case M. Generated test suites fail to detect realistic defective implementations
Primary source: Sun et al., Findings of ACL 2026 • Peer-reviewed benchmark • High confidence for measured results
SWE-Mutation: Can LLMs Generate Reliable Test Suites in Software Engineering?SWE-Mutation evaluates tests by introducing defective implementations and checking whether the generated tests reject them.
800
Original instances
2,636
Mutated variants
36.15%
Detection rate for a reported leading model

The paper reports that DeepSeek-V3.1 achieved a 10.20% verification rate and a 36.15% detection rate under the benchmark's definitions.
It also found that the study's agentically constructed mutants were harder for generated tests to detect than conventional mutants: average detection declined from 71.04% to 39.81%.

ACL Anthology

This supplies evidence for a more specific failure than superficiality:
The generated tests can be insufficiently discriminative: they permit plausible incorrect implementations to pass.
Important scope limitation: This study evaluates LLM-generated tests and uses an agentic mutation framework. It is not a controlled comparison of complete autonomous coding agents. It therefore supports the general test-oracle problem but should not be used to estimate autonomous-agent failure rates directly.
For the eventual skill, this supports a test-quality check such as asking whether a plausible incorrect implementation would still pass. Actual mutation testing, however, requires a tool.
Case N. Agent-authored billing tests were rejected during real code review
Primary source: Devin-associated GitHub PR and reviewer comment • Individual case • Moderate confidence
Firecrawl PR #1645 and maintainer's test review
The PR attempted to repair billing records across several Firecrawl API operations, including map, search, crawl, and batch scrape.
It modified production billing logic and introduced tests. The public discussion includes a Devin agent integration and a reviewer explicitly rejecting the changes to billing.test.ts, requesting that they be reverted.
What is established: A real reviewer found the agent-associated testing changes unacceptable.
What is not established from that comment alone: Which specific assertions were wrong, whether the tests were originally generated by the agent or subsequently modified, and whether the fundamental problem was mocking, test assumptions, or repository conventions.
This is useful supporting evidence for human rejection of agent test changes, but significantly weaker than Konflux PR #7380, where the problematic change is visible and its lost behavioral coverage is identifiable.
Case O. CI/test failures are observable in a substantial real-world sample of agent-authored PRs
Primary source: Ehsani et al., MSR 2026 • Repository-scale empirical study • High confidence for association, not causation
Where Do AI Coding Agents Fail? An Empirical Study of Failed Agentic Pull Requests in GitHubThe researchers examined 33,596 agent-authored GitHub pull requests associated with five coding-agent families.
They manually analyzed a sample of 600 rejected PRs; 38 were unavailable for final categorization.
Within this sample, the study classified 99 PRs as having CI or test failures. Across the broader dataset, unmerged PRs also tended to have more failing CI checks than merged PRs. The reported association was statistically significant.

imranraad07.github.io

This is important because it provides population-level context that the first report largely lacked.
However, a failed CI check does not automatically mean an agent failed to run tests locally. The failure could arise from a defect, missing environment dependency, integration problem, or branch-specific configuration.
Supported conclusion: CI/test failure is a measurable component of rejected agent contributions.
Unsupported conclusion: A specific proportion of autonomous agents routinely skip testing.
Case P. More testing instructions increased activity without improving task success
Primary source: Gloaguen et al., ICLR 2026 workshop • Controlled comparative study • High confidence within studied settings
Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?This is probably the most important newly identified paper for deciding whether to create a testing skill.
The researchers evaluated coding agents with no repository context file, an LLM-generated file, and—in appropriate settings—a developer-written file.
They found that agents often followed the context files, explored more files, and performed more testing, but overall task-success improvements were not statistically significant. Generated context files increased inference costs by approximately 20–23% in the reported comparisons.

arxiv.org

More revealingly, the authors removed different categories of instructions from generated context files.
Benchmark Full context accuracy Without testing instructions Interpretation
CTXbench 68.12% 66.67% Difference not statistically significant
SWE-bench 54.36% 57.72% Difference not statistically significant
Removing the testing-instruction category reduced cost in both comparisons.

arxiv.org

What is demonstrated: Generic repository-context additions can consume resources and change tool behavior without measurably improving the benchmark's final correctness measure.
What remains unknown: Whether a narrowly scoped, explicitly invoked testing skill would behave differently from a repository-wide context file.
This is not evidence against all testing instructions. It is evidence against assuming their value without an experiment.
Case Q. Full-lifecycle agents often degrade test quality even when execution improves implementation behavior
Primary source: Guan et al., SWE-Cycle • Agent benchmark • High confidence for benchmark findings
SWE-Cycle: Benchmarking Code Agents across the Complete Issue Resolution CyclePass 1 highlighted the best strict full-cycle solve rate of 13.50%. The second inspection adds an important nuance.
The study reports that full-cycle operation can improve dynamic implementation performance, because agents repeatedly write, run, and fix code. Yet other quality dimensions deteriorate, particularly the static assessment of generated tests.
The researchers found that many full-cycle submissions had tests that still ran, while losing coverage depth or other aspects of semantic quality. The analysis records more test-generation degradations than improvements across all six evaluated model configurations.

arxiv.org
+1

This means a productive implementation feedback loop can coexist with a deteriorating verification oracle.
That distinction is critical. More test execution is not necessarily better testing when the agent is progressively adapting both code and checks around an incomplete understanding of the desired behavior.

1. Revised failure taxonomy
   The second pass suggests organizing failure patterns by what becomes untrustworthy, rather than only by when the failure occurs in the testing lifecycle.
   Pattern Concrete evidence Root-cause category Skill-addressable?
   Behavioral omission — missing scenarios or modes SWE Atlas, SWE-Cycle coreutils case Incomplete requirements interpretation or scenario planning Partly
   Non-discriminative assertions — incorrect solutions survive tests SWE-Mutation, UTBoost Weak or incomplete test oracle Partly; stronger with mutation tooling
   Invalid reproducer — failure occurs before target assertion SWE-Cycle Ansible case Execution-result interpretation and evaluation design Yes for diagnosis; tooling for enforcement
   Coupled incorrect assumptions — implementation and tests validate the same error SWE-Cycle, Codex #40639 Unverified requirements, insufficient falsification Partly
   Test-scope regression — existing guarantees removed Konflux PR #7380 Test-maintenance decision and missing invariant preservation Strong candidate
   Incorrect test ownership/placement SWE Atlas test-placement analysis Repository-context discovery Strong candidate
   Incomplete verification — required checks absent Codex #8432, Claude #18411 Workflow compliance or instruction conflict Partly; gates needed
   Stale or unsupported success report Codex #7952 Inadequate evidence management Strong candidate with tooling
   Environmental interference — tests fail or cannot execute for external reasons SWE-Cycle, Konflux, Cloudflare example Dependency/runtime infrastructure Diagnosis only
   Verification bypass — skips, disabled assertions, bypassed hooks Claude #45550 and #40117 Agent behavior and insufficient enforcement Guidance plus mandatory controls
   Excessive or inappropriate mocking Hora and Robbes, MSR 2026 Possible test-level mismatch Partly; evidence of harm remains limited
   Long-horizon cross-phase degradation SWE-Cycle Interacting errors across environment, implementation, and testing Partly; durable state may help
   Defective evaluation oracle UTBoost, SWE-bench audits Inadequate tests or parser/grader defects Mostly infrastructure
   Ineffective instruction overhead AGENTS.md controlled study Redundant context and unproductive agent work Requires skill redesign and evaluation
   The critical distinction is between a test-quality defect and a test-process defect.
   A perfectly executed weak test remains weak. A comprehensive test suite that was not executed provides no verification evidence. Both failures matter, but they require different interventions.

2. Root causes: what is established and what remains hypothetical
   A. The quality of the behavioral oracle is the strongest recurring issue
   The evidence converges around a missing distinction between observing a successful execution and demonstrating the required property.
   SWE Atlas reports missing behavioral scenarios. SWE-Mutation shows defective implementations surviving generated tests. UTBoost identifies previously accepted incorrect patches. Konflux demonstrates a test replaced with one checking a different invariant.
   These independent sources support the conclusion that inadequate behavioral discrimination is a real failure mode.
   They do not establish a single universal cognitive explanation for it. The agent may misunderstand the requirement, fail to find relevant code, under-sample scenarios, or construct an inappropriate test oracle.
   Intervention hypothesis: Require each meaningful test to identify the requirement it checks, the observation that demonstrates success, and an incorrect behavior it should reject.
   The qualification is important: this is a promising procedure, not a verified improvement yet.
   B. Test execution and test quality can move independently
   SWE-Cycle and the AGENTS.md study together provide a useful warning.
   More exploration and test execution do not necessarily yield more correct final changes. Conversely, tests that pass may still be irrelevant or incomplete.
   This suggests measuring execution compliance and defect-detection quality separately.
   An agent could score well on running required commands yet poorly on preserving test intent. Another might write strong tests but be unable to execute them because of infrastructure constraints.
   A future skill should recognize both outcomes rather than combining them into a single success flag.
   C. Repository awareness is not simply a question of reading more documentation
   SWE Atlas gives evidence of poor test placement and inconsistent reuse of fixtures. The AGENTS.md study shows that repository context files do not necessarily accelerate discovery of relevant source files.
   The plausible cause is not always missing information. It may be ineffective information retrieval or failure to use discovered facts in later decisions.
   Potential intervention: Rather than supply a full architecture summary in every skill invocation, have the agent discover a small set of task-specific facts: test runner, owning suite, fixtures, CI obligations, and environmental constraints.
   The existing repository documentation remains authoritative. The skill should not reproduce it wholesale.
   D. Test-maintenance failure is supported, but long-term maintenance evidence remains weak
   The Konflux example strongly demonstrates a harmful immediate test modification. The skip/bypass incident reports provide additional warning signs.
   However, the research baseline remains thin on what happens to agent-generated tests after several months of real development.
   Pass 1's observational studies measured test structure, mocking, and some coverage effects. They did not establish that agent tests systematically become flaky or obsolete faster than human-written tests.
   That should remain a research gap, not be promoted to an established general failure pattern.
   E. Instructions and enforcement serve fundamentally different roles
   The AGENTS.md study found evidence that coding agents often do follow instructions and perform more tool actions. Individual bug reports document cases where agents did not.
   These findings are compatible: different tasks, models, instructions, and environments can produce different compliance behavior.
   The more important conclusion is that instruction-following frequency is not a sufficient correctness guarantee.
   A skill can influence what the agent chooses. A hook or CI rule can make a specific bypass impossible or visible. An independent test oracle can establish whether the resulting checks are meaningful.
   These mechanisms complement each other but should not be confused.

3. Updated implications for temrb/cloudflare-template
   I reconfirmed the private repository's AGENTS.md and .github/workflows/verify.yml through the GitHub connection. The relevant architecture documented in Pass 1 remains applicable.
   The project exposes several verification layers, but not all are executed for every CI event. Vitest and workerd integration checks are distinct from conditional browser E2E, removal, and built-artifact checks.
   For example, the workflow's FULL_VERIFY condition enables additional checks for PRs targeting main, pushes to main, and manual dispatches. A PR targeting dev runs a narrower set of checks. CI workflow.
   This suggests a more concrete testing-risk model.
   Task type Required knowledge Agent failure to watch for
   Small pure-function change Existing colocated Vitest tests Tests that check only the same happy-path assumption as the implementation
   Authentication or tenant-isolation change Auth fixtures, runtime checks, browser behavior Mock-only tests that never exercise authorization boundaries
   D1/migration change Schema validation, migrations, workerd fixtures Running unit tests but omitting database integration proofs
   Recovery, tasks, jobs, or authority changes State transitions, retries, failure recovery Tests passing in isolated states without verifying lifecycle invariants
   Browser change Playwright setup, synthetic credentials, runtime server Fragile timing assumptions or tests that inspect UI without server-side effects
   Removal or release-related change Structural and release proof commands, acceptance restrictions Reporting static checks as full release acceptance
   These are prospective testing risks inferred from the repository's verified commands and architecture, not observed agent failures in this repository.
   The strongest repository-specific conclusion is that test execution must have explicit scope semantics.
   A useful report would distinguish:

- Targeted unit checks completed for the final revision.
- Workerd integration checks completed or not executed.
- Browser checks completed, blocked, or not applicable.
- Structural/build checks completed or not executed.
- External or production acceptance unverified unless separately authorized and evidenced.
  The skill should not invent a universal rule that every edit requires every expensive check. It should select a relevant verification scope, obey repository acceptance requirements, and disclose what remains unverified.
  This project also contains an existing documented acceptance process. A future skill should integrate with that process rather than create a competing one. Repository instructions.

1. Revised intervention priorities
   Pass 1's intervention table used labels such as “High expected strength.” That is too confident: most of these procedures have not been independently evaluated as agent interventions.
   A better prioritization uses evidence for the failure, mechanical testability, and ease of enforcement.

1. Behavioral invariant preservation
   Detect removed or weakened assertions, changed test scenarios, newly introduced skips, and replacements that test different behavior.
   Strong direct case: Konflux PR #7380. Intervention effectiveness still untested.

1. Behavior-specific test design
   Identify expected outcomes, important scenario distinctions, negative controls, and plausible counterexamples before writing assertions.
   Supported by SWE Atlas, SWE-Mutation, SWT-Bench, and SWE-Cycle.

1. Task-specific verification topology
   Discover existing test suites, fixtures, required commands, conditional CI rules, and relevant execution environments.
   Supported by SWE Atlas and repository inspection; avoid long duplicated context.

1. Evidence-linked completion
   Report only checks actually executed on the final relevant code state, including failed, skipped, blocked, and unverified statuses.
   Supported by execution-integrity incidents; strongest with independently captured tool logs.

Skill versus infrastructure
Intervention Instruction-based skill Tooling or enforcement
Explain why a test exists Good fit Optional
Select behaviorally distinct scenarios Good fit, fallible Mutation/differential tests improve validation
Find existing testing conventions Good fit Repository search and indexing
Preserve test assertions Good fit for review Automated test-diff audit is stronger
Run required checks Can direct execution CI/hooks needed for guaranteed enforcement
Diagnose setup, collection, and assertion failures Good fit with tool output Structured test-runner diagnostics
Guarantee correct interpretation of requirements Cannot guarantee Human/domain oracle
Guarantee checks were not bypassed Cannot guarantee Permission controls and protected CI
Guarantee consistent long-horizon execution Cannot guarantee Durable state and orchestration
Prevent benchmark leakage Outside normal skill scope Sandbox and evaluation isolation
The most relevant official guidance is Anthropic's explanation of when to use skills, repository rules, hooks, and subagents. It distinguishes instruction loading and scope from deterministic lifecycle controls.

Claude by Anthropic

That supports treating the future SKILL.md as one component of a verification workflow rather than as the entire solution.

1. Research gaps and the strongest next experiment
   The newly discovered evidence changes which unknowns deserve priority.
   Question Why it matters Experiment
   Can a skill prevent agents from weakening tests? Direct real-world incident; measurable harm Replay flaky-test repair tasks with assertion-preservation scoring
   Can a skill increase mutation kill rates? Test quality is a central concern Held-out mutant evaluation with fixed tasks and budgets
   Does targeted repository discovery improve test placement? SWE Atlas identifies placement failures Compare free exploration, concise context, and explicit discovery procedure
   Do extra testing instructions help beyond raising activity? Controlled AGENTS.md study challenges the assumption Randomized skill-only versus no-skill evaluation
   Which failures require independent enforcement? Agent compliance is not guaranteed Compare skill-only against skill plus hooks and CI
   Can agents manage verification after many edits? SWE-Cycle identifies cross-phase deterioration Multi-step tasks with revision-specific evidence tracking
   Are generated tests harder to maintain long-term? Current evidence is insufficient Follow test survival, repair cost, and flake rates across later commits
   Recommended evaluation baseline
   I would test three conditions against the same independently graded task set.
   Control
   A
   Agent only
   Existing project guidance, no dedicated testing skill
   Treatment
   B
   Agent + skill
   Same tasks, model, repository and execution budget
   Enforced
   C
   Skill + gates
   Deterministic execution and evidence controls

Primary outcomes
Preserved behavioral invariants

Detected held-out defects

Verified final-state claims

Cost, latency and interventions

The key dependent variable should be independently validated correctness, not how often the agent invokes a testing tool.
The AGENTS.md study shows exactly why: an agent can do more testing and still fail to improve its final task result. 8. Corrections and confidence adjustments to Pass 1
The first report is directionally sound, but this second pass supports several refinements.
Pass 1 conclusion Second-pass assessment
345 erroneous patches identified by UTBoost Retain. Confirmed in the ACL paper; this concerns re-evaluation of patches and graders, not the rate of agents skipping tests. arxiv.org
SWT-Bench 15.9% rising to 18.5% Retain with scope. This is a measured improvement for a particular agent configuration and test-writing task, not proof that a general-purpose skill works. proceedings.nips.cc
SWE-Cycle best strict solve rate 13.50% Retain with nuance. Full-cycle dynamic implementation behavior sometimes improved while static test quality degraded. arxiv.org
Agents frequently produce superficial assertions Qualify. Some benchmark studies support incomplete discrimination, but human-comparison studies also show meaningful coverage gains. Avoid universal claims. arxiv.org
Agents may overuse mocks Retain as an observed association. Higher mock-addition frequency does not, by itself, demonstrate lower defect detection. arxiv.org
Repository instructions can prevent testing omissions Downgrade. Direct incidents show omissions, while controlled research finds context files can increase activity without improving correctness. arxiv.org
A testing skill should be a high-priority next step Retain as an experimental hypothesis, not an established solution. The new research increases the importance of controlled validation before adoption.
Final research conclusion
The most defensible position after two passes is narrower and more useful than simply saying AI coding agents are bad at testing.
Autonomous coding agents have demonstrable weaknesses in selecting meaningful test scenarios, preserving existing behavioral coverage, interpreting test evidence, and coordinating verification across repository-specific workflows. These are supported by agent benchmarks, empirical studies, and independently inspectable GitHub cases.
At the same time, generated tests can provide useful coverage, and more testing activity is not necessarily associated with greater correctness. The causal benefit of a dedicated testing skill remains unproven.
That points toward a focused research direction: a skill designed to protect test intent, force explicit choices about verification scope, challenge weak assertions, and distinguish executed evidence from unsupported claims, with external controls for guarantees a skill file cannot provide.
The next important work is not drafting a larger checklist. It is defining the smallest set of interventions that can be measured against the specific failures demonstrated above.
Research status: Second pass complete as a literature-and-case review. The example repository was reinspected read-only through GitHub. No agent runs or controlled experiments were performed, no repository changes were made, and no SKILL.md was created.
