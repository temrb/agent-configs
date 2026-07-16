# Post-login redirect contract

Status: designated as governing behavior for this exercise by the application-security owner and account product owner.

`RedirectPolicy.safe_path(value)` returns the input only when it is an absolute-path reference on the current origin. It must reject scheme-relative values such as `//evil.example`, backslash-prefixed variants, strings containing control characters, and any value with a URI scheme or host. Rejected or missing values return `/account`.

The method must preserve query strings and fragments on accepted same-origin paths. Its module name, method name, one-argument interface, and fallback value are compatibility requirements. It must not perform I/O or add a dependency.
