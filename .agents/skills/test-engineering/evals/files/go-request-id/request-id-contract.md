# Request-ID response contract

Status: designated as governing behavior for this exercise by the API product owner.

`api.NewHandler(nextID)` returns an HTTP handler. Every response produced by that handler, including method and malformed-body errors, must include a non-empty `X-Request-ID` response header whose value came from `nextID`. The header must be observable by a real `net/http` client before the response status and body are committed.

For a `POST` request with malformed JSON, the handler must return status 400 and body `invalid request\n`. The public constructor signature is a compatibility requirement. The handler must not perform network I/O or add dependencies.
