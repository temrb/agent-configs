import pytest

from src.refunds import allocate_refund


def test_allocates_divisible_total_evenly():
    assert allocate_refund(900, 3) == [300, 300, 300]


@pytest.mark.parametrize(
    ("total_cents", "recipient_count", "message"),
    [
        (-1, 2, "total_cents must be non-negative"),
        (100, 0, "recipient_count must be positive"),
    ],
)
def test_rejects_invalid_arguments(total_cents, recipient_count, message):
    with pytest.raises(ValueError, match=f"^{message}$"):
        allocate_refund(total_cents, recipient_count)
