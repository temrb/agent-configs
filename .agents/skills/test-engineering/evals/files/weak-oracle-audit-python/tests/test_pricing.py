from src.pricing import discounted_subtotal


def test_discount_never_increases_subtotal():
    result = discounted_subtotal(10_00, 2_500)
    assert 0 <= result <= 10_00
