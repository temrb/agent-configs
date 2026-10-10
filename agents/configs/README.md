# Configuration collection

Keep each platform's configuration in `agents/configs/<platform>/`, using its
native directory and file layout. Codex lives in [codex/](codex/README.md), with
one canonical `.codex/` tree. Installation scope does not create another copy
inside this collection.

Configurations are maintained independently of plugin recipes and require no
build. Keep companion hooks, scripts, and rules at their native relative paths.
Do not import credentials, runtime history, logs, or caches.

Validation rejects known Codex runtime asset names while permitting optional native
configuration assets. It does not scan legitimate configuration for embedded
credentials; review all imported content before committing.
