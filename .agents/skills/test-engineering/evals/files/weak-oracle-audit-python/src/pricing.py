def discounted_subtotal(subtotal_cents: int, discount_basis_points: int) -> int:
    """Return the subtotal after applying a basis-point discount."""
    return max(0, subtotal_cents - discount_basis_points)
