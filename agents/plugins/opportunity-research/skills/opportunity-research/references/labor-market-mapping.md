# Labor market mapping

Turn occupation data into a shortlist of recurring buyer workflows by industry. Use the [source guide](./source-guide.md) for O\*NET task files and buyer evidence. Store optional source copies in `ref/` in the researched project.

## Build the map

- Use O\*NET task data to find similar work across roles. Use BLS Occupational Employment and Wage Statistics (OEWS) to locate employment and wage concentration by industry. Use Anthropic's observed exposure measure to generate hypotheses about which tasks might be automated. [BLS industry tables](https://www.bls.gov/oes/2025/may/oessrci.htm) · [Anthropic methodology](https://www.anthropic.com/research/labor-market-impacts) · [Published exposure data](https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main/labor_market_impacts)
- Record source releases, geography, industry and ownership scope, coverage gaps, join rules, and unmatched codes. Use the official O\*NET-to-SOC crosswalk for the relevant taxonomy versions. Count each OEWS estimate once within a consistent industry, geography, and ownership scope, even when several O\*NET codes match the same row. Choose nonoverlapping occupation and industry levels so parent totals and their child rows are never summed together. [O\*NET crosswalk](https://www.onetcenter.org/crosswalks.html)
- Record missing exposure as unknown. A reported zero reflects the study's usage threshold. Where exposure is missing, record the gap and continue with the available task, employment, wage, and buyer evidence.

## Screen workflows

Look for administrative tasks embedded in physical and regulated occupations. Group equivalent tasks across roles by buyer workflow and industry, using the recurring trigger and outcome to identify equivalent work. Honor explicit brief constraints. Keep embedded workflows eligible for discovery when the only exclusion signal is the occupation code, job title, or government employment share. Apply the [launch-risk rubric](./decision-rubric.md#launch-risk) once the buyer, inputs, intended use, and plausible consequences are clear.

## Prioritize and size

Use a weighted score, if helpful, to choose what to investigate. Record the criteria, weights, proxies, missing inputs, and their effect on the ranking. Task counts and frequency ratings alone cannot establish time spent, workflow spending, or an upper bound. Estimate workflow cost from observed volume, handling time, and labor cost, or from actual outsourced spend. Use the [commercial viability rubric](./decision-rubric.md#commercial-viability) to assess pricing and reachable paid demand.

## Scope the offer

Record the recurring outcome, payer with purchase authority, smallest sellable deliverable, verification method, and exception owner. For example, a distributor could pay for draft orders prepared from emailed purchase orders. Its order team checks drafts against the source and resolves ambiguous SKUs or quantities before release. Assess plausible harm from draft errors, including across a batch, under the launch-risk rubric. Treat intake through ERP handoff as a separate expansion with its own buyer commitment, access, controls, and delivery economics.

## Save for resume

Record which workflow and industry pairs were carried forward, the evidence behind each choice, and material coverage gaps in `phases/phase-NN/notes/workflow-map.md`. Link the map from the coverage item in the phase's `notes/status.md` and record the next check for any gap that could change the shortlist.
