# Oracles and discrimination

Derive expected behavior from a requirement, established invariant or independent
correct behavior, rather than copying the implementation's output. Identify a
concrete incorrect implementation the test rejects. Prefer boundary assertions
to assertion counts and snapshots without a behavioral discriminator.

Confirm setup and that the failing assertion expresses the defect. For a valid
red/green association use the same final test and fixture digest. If either
changes, replay the final reproducer on a disposable defective state, applying
only compatible test/fixture setup; never transplant the fix. Incompatible setup
is inconclusive. Record red, green, source states, oracle and surrounding checks
in the case schema. High-risk security, ownership, billing, persistence, recovery
and state transitions deserve particular care.

Mutation experiments exclude equivalent mutants, invalid builds and environment
failures from eligible detection counts. Detection already provided by the old
suite is reuse, not marginal coverage. Public fixtures cannot substitute for
external held-out grading.
