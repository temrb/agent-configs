def allocate_refund(total_cents: int, recipient_count: int) -> list[int]:
    if total_cents < 0:
        raise ValueError("total_cents must be non-negative")
    if recipient_count <= 0:
        raise ValueError("recipient_count must be positive")

    share = total_cents // recipient_count
    return [share] * recipient_count
