"""Validate the canonical OpenCode JSON tree independently of plugin recipes."""
from configs.native_json import json_configs


def opencode_configs(root, safe):
    json_configs(root, safe, "opencode", "opencode.json")
