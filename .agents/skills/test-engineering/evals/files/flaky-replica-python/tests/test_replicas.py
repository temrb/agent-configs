from src.replicas import choose_replica


def test_primary_replica_is_selected():
    assert choose_replica(["primary", "secondary"]) == "primary"
