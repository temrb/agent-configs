# Replica selection contract

Status: designated as the governing behavior for this exercise by the availability product owner.

`choose_replica(replicas)` must return one member of a supplied non-empty sequence. Selection among healthy replicas is intentionally nondeterministic; no specific member or stable ordering is promised. Empty-input behavior is outside this exercise.
