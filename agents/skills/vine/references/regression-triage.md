# Triage and transitions

Identify expected and observed behavior, requirement authority, consequence and
owning boundary. Reuse existing failures; strengthen only an identified gap.
Separate pre-existing baseline failures from task regressions. Collection,
compilation, missing bindings and unrelated failures are not behavioral red.

If reproduction is impossible or unsafe, record attempts, prerequisite limits
and alternative evidence; leave red unconfirmed. If the fix predates the test,
report that chronology. Optional baseline replay establishes discrimination only.

For flakes, identify the invariant and instability cause, retaining protection
while diagnosing. Quarantine needs reviewed replacement/repair, owner and expiry.
A behavior change names the retired guarantee, requirement authority and
replacement coverage or intentional absence; rationale is not maintainer review.

For unrelated valuable discoveries, save location, expected/observed behavior,
consequence, evidence and reproduction status in the project's deferral record
or local task notes. Continue the original scope. Do not automatically file
external issues or add tests for incidental low-value observations.
