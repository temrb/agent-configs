# Concurrent counter contract

Status: designated as governing behavior for this exercise by the telemetry product owner.

`counter.Counter` starts at zero. Each completed call to `Increment` adds exactly one. `Increment` and `Value` may be called concurrently from multiple goroutines and must be race-free. Once all incrementing goroutines have completed, `Value` must equal the number of completed increments.

The exported type and method signatures are compatibility requirements. Operations must not sleep, perform I/O, start background goroutines, or add dependencies.
