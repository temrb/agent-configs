# Refund-allocation decision record

Status: designated as the governing contract for this exercise by the product owner and finance domain owner.

`allocate_refund(total_cents, recipient_count)` must:

- accept integer `total_cents >= 0` and integer `recipient_count > 0`;
- return exactly `recipient_count` integer, non-negative shares;
- conserve the total exactly: `sum(shares) == total_cents`;
- keep shares within one cent of each other;
- assign any remainder cents to earlier recipient positions, in stable order;
- return all-zero shares when `total_cents == 0`;
- raise `ValueError("total_cents must be non-negative")` for a negative total;
- raise `ValueError("recipient_count must be positive")` for a non-positive count.

The function must remain deterministic and side-effect free. Its public name, two-argument interface, exception type, and exact error messages are compatibility requirements. No new dependency, I/O, logging, or network behavior is authorized. Performance must remain linear in the number of returned shares.
