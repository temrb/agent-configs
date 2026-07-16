# Legacy label-parser compatibility

Status: designated by the migration owner for this exercise.

The duplicate implementations of `parseTags(value)` and `parseLabels(value)` may be refactored into shared internal structure. Their exported names and one-string-argument interfaces must remain. Existing externally observed behavior for string inputs is compatibility behavior for this refactor, including whitespace handling, empty segments, ordering, and duplicates.

No new parsing policy or non-string behavior is authorized. The refactor must not add dependencies, I/O, logging, or asynchronous behavior.
