import random


def choose_replica(replicas: list[str]) -> str:
    """Choose one available replica."""
    return random.choice(replicas)
