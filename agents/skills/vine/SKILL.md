---
name: vine
description: Reproduce consequential behavioral defects, select meaningful regression coverage in the owning suite, and verify the final change with fresh evidence. Use for behavioral feature or bug work and consequential failures discovered during a task.
---

# Verified Invariants & No-regression Engineering

Evidence helpers are optional and currently support the Foundation-compatible
Node 24.19.0 / Bun 1.4.2 profile. Use existing project checks directly unless the
project adopts the helper policy. Project commands and acceptance remain
project-owned.

Establish the requirement and owning boundary before choosing an oracle. Read
project instructions and verification policy; these own commands, applicability
and acceptance. Reassess if consequential unexpected behavior emerges mid-task.

For a bug, reuse an existing reproducer where possible. Confirm that defective
code reaches the intended behavioral assertion with valid setup before fixing
when feasible. For a feature, establish externally meaningful expected behavior
and useful positive, negative and boundary cases before implementation when
feasible. A spike with an unresolved contract is exploratory work.

Choose coverage by consequence, reproducibility, recurrence, existing protection
and cost. A useful test rejects a plausible incorrect behavior. No new test is
needed when existing coverage is sufficient. Probe/helper tests cannot prove
route wiring or built-artifact behavior. Mock only boundaries irrelevant to the
invariant. Keep scope aligned with the authorized task.

Use [triage](references/regression-triage.md) for baseline failures, flakes,
blocked reproductions and incidental discoveries; [oracles](references/test-oracles.md)
for discrimination and replay; [ownership](references/test-ownership.md) for
coverage edits and retirement; [evidence](references/verification-evidence.md)
when capturing commands or reporting completion.

After fixing, verify the final reproducer and required surrounding checks.
Recheck evidence after relevant source, test, fixture, dependency, config or
policy edits. State selection, failures, unexecuted checks and acceptance limits.
Report chronology honestly; replay does not establish historical test-first work.
The helpers validate mechanical evidence, never semantic correctness or merge
permission. Follow the project's existing acceptance authority.
