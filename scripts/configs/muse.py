"""Validate the supplied Muse settings without claiming schema conformance."""
from configs.native_json import json_configs


def muse_configs(root, safe):
    json_configs(root, safe, "muse", "settings.json")
