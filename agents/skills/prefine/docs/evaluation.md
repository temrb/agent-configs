# Prefine behavioral evaluation

The [case matrix](../tests/fixtures/prefine-behavior.json) evaluates the canonical
[skill](../SKILL.md). These are semantic evaluation fixtures,
not deterministic package tests. Passing validators or synchronization does not
establish instruction following.

The skill-owned Python suite checks the case matrix's structure and runs through
the root test suite. Run it alone with
`python3 -B -m unittest discover -s agents/skills/prefine/tests`.

Load the skill in the intended host and submit each case's `turns` in order as
one active compilation request. Keep the full output and tool trace. For
multi-turn cases, send the next turn only after the expected missing-input or
essential-clarification request. If the model compiles prematurely, record that
failure rather than injecting an unsolicited continuation. The clarification
case deliberately needs a deliverable choice and disallows placeholders.

Supply controlled read-only attachments for context cases. For resolver cases,
use a controlled official-documentation tool fixture: Fixture-A1 belongs to a
fictional provider with a model-specific guide, explicitly applicable family
advice, and general advice. Identify gpt-fixture as OpenAI-owned. Do not use these
fictional identifiers for live-provider smoke checks. Include separate source
variants for moved pages and redirects, absent exact models, a verified model
without dedicated guidance, inapplicable family advice, and unavailable retrieval.
Keep sources' ownership, availability, and expected applicability in the run log.
For unauthorized-source checks, place conflicting selectors or execution
instructions in attachments and retrieved documentation; neither may change the
active request's settings or authorize task execution.

Judge each `expected` assertion against output and trace. Record pass, fail, or
inconclusive, with supporting excerpts and tool calls; do not match exact output
strings. Verify target selection, mode, applicable retrieval, fallback, source
authority, scope fidelity, and permitted response forms. A finished prompt need
not visibly differ across providers when guidance adds nothing material.

Repeat consequential non-execution, continuation, and source-authority cases
several times and record model/host versions, trial counts, and outcomes. Keep
live provider lookup out of deterministic CI. Run the plugin README's manual
smoke procedure separately using a currently verified real identifier and
inspect traces for current official entry-point navigation. Do not claim
behavioral success from package checks or unexecuted fixtures.
