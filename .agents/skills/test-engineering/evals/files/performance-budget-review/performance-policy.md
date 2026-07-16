# Search-latency release policy

Status: designated as governing release policy for this exercise by the search product owner and site-reliability owner.

The supplied measurements contain 30 post-warmup paired trials from the same pinned environment. Use all rows. Calculate the median as the average of the two central sorted values and p95 with the nearest-rank method.

A candidate may advance only when:

- every row is complete, numeric, and from one matching environment identifier;
- candidate p95 is no greater than 120 milliseconds;
- candidate median is no more than 10% above baseline median.

Do not remove outliers, change the percentile method, or rerun only unfavorable trials after seeing the result. A failed release gate establishes a performance-policy violation for this candidate; it does not identify the responsible code change. The policy owners must authorize exceptions or changed budgets.
