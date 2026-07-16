# Checkout discount decision record

Status: designated as the governing contract for this exercise by the checkout product owner.

`discounted_subtotal(subtotal_cents, discount_basis_points)` must:

- accept integer `subtotal_cents >= 0` and integer basis points from 0 through 10,000;
- compute the discount as a percentage where 10,000 basis points is 100%;
- round the discount to the nearest cent, with an exact half cent rounded upward;
- return the subtotal minus that rounded discount;
- remain deterministic and side-effect free;
- preserve its public name and two-argument interface.

Invalid-input behavior is outside this exercise and has not been designated.
