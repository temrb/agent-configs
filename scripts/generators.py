"""Pure renderers: desired relative paths mapped to (bytes, mode) files or None directories."""
import json
from validation import manifest as validate_manifest


def copy_tree(source, scan):
    if not source.is_dir():
        raise ValueError(f"copy-tree source must be a directory: {source}")
    return scan(source)


def copy_skill(source, scan):
    """Bundle only the skill contract; development resources stay canonical."""
    if not source.is_dir():
        raise ValueError(f"copy-skill source must be a directory: {source}")
    contract = source / "SKILL.md"
    content = scan(contract)
    if not contract.is_file():
        raise ValueError(f"copy-skill requires SKILL.md: {source}")
    return {"": None, "SKILL.md": content[""]}


def codex_manifest(source, scan):
    if not source.is_file():
        raise ValueError(f"codex-manifest source must be a file: {source}")
    manifest = validate_manifest(json.loads(source.read_text()))
    result = {}
    interface = manifest.get("extensions", {}).get("com.openai", {}).get("interface")
    if interface is not None:
        result["interface"] = interface
    for field in ("name", "version", "description", "author"):
        if field in manifest:
            result[field] = manifest[field]
    result["keywords"] = manifest.get("keywords", [])
    result["skills"] = manifest.get("skills", "./skills")
    validate_manifest(result, codex=True)
    return {"": ((json.dumps(result, indent=2) + "\n").encode(), 0o644)}


GENERATORS = {"copy-skill": copy_skill, "copy-tree": copy_tree, "codex-manifest": codex_manifest}
