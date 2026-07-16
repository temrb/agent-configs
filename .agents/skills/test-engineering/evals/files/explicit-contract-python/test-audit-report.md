# Refund test audit

Scope: `src/refunds.py` and `tests/test_refunds.py`.

Finding R-1: existing tests cover divisible totals and invalid arguments, but do not exercise remainder allocation. The current implementation uses floor division for every share and can drop cents when `total_cents` is not divisible by `recipient_count`.

Recommended candidate verification:

- a non-divisible total with a stable expected remainder order;
- a total smaller than the recipient count;
- zero cents;
- general conservation and balance assertions over representative inputs.

This audit identifies a coverage and implementation risk. The product- and finance-designated decision record remains the governing authority for expected semantics.
