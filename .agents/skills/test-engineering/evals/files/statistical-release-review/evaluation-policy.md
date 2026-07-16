# Candidate release-evaluation policy

Status: designated as governing release policy for this exercise by the model-risk owner.

Evaluate the supplied labeled rows exactly once as a held-out release set. A candidate may advance only when all of these gates pass:

- every row has a unique non-empty `id`, a region, and binary `label` and `prediction` values;
- each region has at least 10 labeled rows;
- overall positive-class precision is at least 0.85;
- positive-class recall is at least 0.75 in every region;
- every false negative has a recorded decision from the safety reviewer.

Calculate metrics from the CSV rather than from rounded values in prose. Do not tune a threshold or remove rows after seeing the release result. A failed or unevaluable gate means `do not advance`; it does not by itself identify an implementation defect. The policy owner must authorize any changed threshold or exception.
