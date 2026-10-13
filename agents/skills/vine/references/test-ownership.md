# Owning coverage and retained guarantees

Find the existing owner: unit/tool logic, real binding/persistence harness,
application HTTP/browser, or generated artifact. A probe Worker using production
helpers still does not prove application cookies, routing or serialization.
An output-only defect needs evidence on the actual packaged output.

Review the complete base-to-proposal diff, including staged, unstaged, renamed,
deleted and nonignored untracked files. Check test expectations, fixtures, skips,
mocks, discovery/dispatch, dependencies, runner configuration and CI. Removing a
scenario's registration can weaken protection while leaving its assertions.

Use audit-test-diff.mjs as an advisory inventory. Syntax findings cannot prove
semantic preservation. Expected-failure tests execute inverted expectations;
`test.fails` is distinct from skips/quarantines. Requirement retirement and
protected policy reductions require independent maintainer review bound to the
patch. Record check/invariant, reason, replacement, scope, owner and expiry or
permanent retirement rationale; agent-authored rationale is a request.

To check an exception request, pass `--exception REQUEST.json` to the diff auditor.
The strict request fields are `invariant`, `reason`, `replacementEvidence`,
`scope`, `owner`, `expiry` (future timestamp or `permanent`),
`retirementRationale`, `patchDigest` and `approvalReference`. Every field is a
nonempty string. A request for a different patch or expired scope is rejected.
The helper cannot authenticate approvalReference; maintainer approval remains
unverified until checked independently. No request waives an obligation.
