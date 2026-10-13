"""Repository-relative locations of the agent content collections."""
from pathlib import Path

PLUGIN_COLLECTION = Path("agents/plugins")
CANONICAL_SKILLS = Path("agents/skills")
CONFIG_COLLECTION = Path("agents/configs")


def reserved_manifests(root):
    return (root / PLUGIN_COLLECTION).glob("*/.codex-plugin")
