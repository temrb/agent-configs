# Grading rubric

Keep this rubric, `evals.json`, `verification.json`, original fixtures, and configuration labels outside the execution agent's context.

## Evidence sources

- Use `verify_case.py` for input preservation, deliverable presence, symlink rejection, forbidden artifacts, and mutation scope.
- Use sandboxed fixture commands for executable behavior only after the controller has inspected and allowlisted the command.
- Use transcripts and command logs for ordering, baseline identity, diagnosis-before-editing, safety choices, and claims that a challenge ran.
- Use output files for final implementation and test semantics.
- Use human review for materially ambiguous oracle mapping, subjective quality, risk acceptance, or a claim whose decisive evidence cannot be reproduced.

Do not pass a process expectation from `report.md` alone. Do not pass a semantic expectation merely because the implementation contains a likely-looking branch. Do not infer that an omitted command passed.

## Atomic grading

Grade every expectation independently as `passed: true` or `passed: false`, with concrete evidence. When evidence is unavailable, set `passed: false` and state `inconclusive` in the evidence; do not award partial credit inside a binary item. Preserve the exact fields required by the evaluation viewer:

```json
{
  "text": "expectation text",
  "passed": false,
  "evidence": "inconclusive: the transcript omits the baseline file hashes"
}
```

For numeric results, reproduce the calculation. For byte-preservation and scope claims, cite the controller verifier. For a red-phase claim, cite transcript events showing the new check and baseline identity before the first implementation mutation. For an independent-challenge claim, identify the challenge's source, author or origin, implementation exposure, result, and limit.

## Semantic decisions

- A designated contract can independently establish expected behavior even when an execution agent writes the test.
- A generated test is not independent merely because it ran in a separate process.
- An existing test is not authoritative merely because it predates the change.
- A held-out input is useful only if it was not selected after inspecting the candidate implementation's behavior.
- A mocked component check does not prove a browser, network, persistence, process, or service boundary that it bypasses.
- A release gate can fail without proving an implementation defect.
- `implementation-green, validation-provisional` is the correct bounded outcome when implementation checks pass but no decisive boundary-crossing challenge is available.

## Grader calibration and blinding

Before scoring a benchmark iteration, test the grader against:

1. a known-good transcript and output;
2. a persuasive report that claims red-to-green ordering but edits implementation first;
3. a solution that passes visible examples by special-casing them;
4. a solution that weakens or deletes a failing test;
5. a partial run described as global green;
6. a generated oracle with no governing contract or independent challenge.

The grader should reject cases 2 through 6 on the affected expectations. Blind graders and human reviewers to `current`, `prior`, and `without-skill` labels until grades are locked. Randomize presentation order. Record grader model, prompt revision, temperature or sampling configuration, and calibration outcome.

## Acceptance analysis

Report expectation-level pass rates, paired configuration deltas, mean, standard deviation, range, runtime, and tokens. Flag expectations that pass equally without the skill, cases with high variance, and gains explained by longer reports rather than stronger evidence. Keep development, held-out, and trigger conclusions separate.
