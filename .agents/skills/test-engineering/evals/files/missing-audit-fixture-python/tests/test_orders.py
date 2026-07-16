import json
from pathlib import Path

from src.orders import active_order_ids


def test_reads_active_orders_from_reviewed_fixture():
    fixture_path = Path(__file__).parent / "data" / "orders.json"
    orders = json.loads(fixture_path.read_text())

    assert active_order_ids(orders) == ["order-1", "order-3"]
