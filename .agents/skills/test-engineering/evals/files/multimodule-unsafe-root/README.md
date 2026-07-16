# Catalog workspace

This workspace contains a browser-independent web formatter and a Go catalog service. The root test command was written for a private CI environment that resets a shared database before dispatching module tests. Product title behavior is governed by `web/title-contract.md`.

The web and catalog modules can be inspected and validated independently. No behavior contract has been supplied for the database-reset script.
