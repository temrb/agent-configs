def active_order_ids(orders: list[dict]) -> list[str]:
    """Return IDs for active orders in their input order."""
    return [order["id"] for order in orders if order.get("status") == "active"]
