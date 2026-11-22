---
name: opportunity-research
description: Run, resume, or revise a software opportunity research phase. Investigate buyer outcomes, spending, and practical substitutes, then decide what warrants further discovery, paid validation, or a production build.
---

# Opportunity research

Use the user's request and any invocation arguments as the brief. A brief can start a new phase, resume `phase-NN`, or revise `phase-NN` with specified changes.

Complete the requested desk research and save a verified `report.md` with supporting notes. A decision to validate zero offers can complete a phase. If live research is unavailable, deliver a research plan based on what you can verify locally.

## Start or resume

Use the repository root of the project being researched for `phases/` and optional local source copies in `ref/`. For a new attempt, use the next numbered phase. For a resume or revision, use the requested phase and inspect its checkpoint, report, and relevant notes first. Resolve an ambiguous phase reference before writing. Reconstruct a missing checkpoint from existing artifacts. Preserve completed work. Reopen checks affected by the brief, new evidence, or restored access and set the state to `in progress`. If the verified report already satisfies the request and coverage needs no further work, return it.

Create or update `notes/status.md` with the [status template](./references/status-template.md). Use it as the work checklist. Save evidence and update the checklist as checks resolve, before a context reset, and before yielding control. After an interruption, pick up from the first unfinished check and its cited notes.

Continue after progress updates and milestones. If a source or lead is blocked, record the limit and proceed with independent checks. End the run when the report is verified or when an unresolved dependency prevents further authorized work. Carry out local checks with permissible inputs. Field plans propose outreach, purchases, or live pilots for the user to authorize.

## 1. Discover outcomes and spending

Read the [source guide](./references/source-guide.md). Synthesize the starting sources and consult relevant earlier phases to generate and challenge hypotheses. Reuse applicable synthesis on resume or revision. Look beyond the customer and source mix already covered, within the brief. For open discovery, sweep consumer, business, and intermediary-led settings across industries.

Start from buyer behavior such as a purchase, costly workaround, failed switch, or abandoned attempt. Include outcomes buyers cannot access or afford. Trace what they spend, lose, or give up, who controls the budget, how often the problem occurs in a reachable segment, and what changed that might make a better outcome possible. Log searches and the evidence behind the strongest leads and early eliminations.

If the first sweep yields mostly seller claims, thin economics, or few reachable buyers, run a targeted second pass using different buyer sources and workflow terms. Record the result or why a second pass was unnecessary. If live research is unavailable across available routes, document which checks are blocked and proceed to the research-plan format. Individual source failures are evidence limits for the affected claims.

## 2. Screen scoped offers

Read the [decision rubric](./references/decision-rubric.md). Work backward to the smallest sellable offer. Define the user, payer with purchase authority, launch geography, channel, inputs, intended use, and measurable improvement. Screen launch risk and commercial viability before deeper work. Consider a narrower scope if it could clear a failed or unresolved gate.

A serious lead is a scoped offer with a plausible material gain and a credible enough route to buyers to warrant testing. Record a decisive early elimination with its evidence and which remaining checks it made unnecessary. For other serious leads, trace a real attempt from trigger to outcome or abandonment, including handoffs and exceptions. Where expertise matters, identify what can be transferred into repeatable procedures and where judgment or specialist review is still needed.

## 3. Challenge survivors

Search for the outcome under alternate names and adjacent categories. Compare the buyer's current behavior, the best accessible tools and bundled features, services, DIY, and doing without. Check the strongest substitute against a concrete case's inputs, exceptions, systems, and access constraints. Compare total cost, including setup, switching, review, and upkeep. Date and scope the gap claim. A substitute-based rejection needs evidence that the buyer can obtain and use the substitute on the decisive case. Apply the same checks to both sides of an intermediary offer and to any expansion needed for viability.

Finish the risk cases and commercial arithmetic for surviving serious leads. Test the assumption most likely to reverse the decision. Run a lightweight comparison when representative, permissible inputs are available. Exhaust public checks likely to change the disposition before deferring to fieldwork. Stop searching when coverage and decisive checks are accounted for and remaining unknowns have a specific dependency or test.

## 4. Decide, write, and verify

Use the rubric to record gate outcomes and dispositions. Rank offers eligible for validation and state separately which meet the production bar. Use the [report template](./references/report-template.md) to write `report.md`, including its research-plan format if live research was unavailable. Link to `notes/` for source synthesis, searches, risk cases, funnel arithmetic, and substitute comparisons.

Before marking the phase complete, check the report against the notes and rubric. Verify decision-critical claims, arithmetic, pilot and build eligibility, and relative links. Confirm the checkpoint accounts for coverage and each watchlist lead has a next check with a decision threshold. Record the verification in `notes/status.md` and return the report path and main decision.
